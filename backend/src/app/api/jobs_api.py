import logging
import uuid
import os
import tempfile
import shutil
import re

from flask import Blueprint, request, jsonify
from pydantic import BaseModel, ValidationError, Field, HttpUrl

# Use relative import for flattened config object
from ..config import config
# from src.core.git_utils import clone_repo # Keep commented out for now if not used
from src.exceptions import CloningError, TaskEnqueueError, HistoryUpdateError # Import custom exceptions
# Need to import the task object directly
from src.tasks.documentation_task import run_adk_documentation_task
# Import constants for status
from ..constants import JobStatus

# DI Imports (Container needed for manual resolution)
from dependency_injector.wiring import inject, Provide # Keep Provide if other routes use it
from src.app.container import Container
from src.persistence.repository import JobHistoryRepository

logger = logging.getLogger(__name__)

jobs_bp = Blueprint('jobs_api', __name__, url_prefix='/api/v1') # Using a versioned prefix

# --- Pydantic Models ---
class DocumentRequest(BaseModel):
    # Allow generic string for now, could add stricter git URL validation if needed
    repoUrl: str = Field(..., examples=["https://github.com/google/generative-ai-docs.git"])
    obsidianFormat: bool = False

# Basic regex, could be more sophisticated
# GIT_URL_REGEX = re.compile(r"^(?:git|ssh|https|http)://|^git@|^[^/]+@[^:]+:")

@jobs_bp.route('/jobs', methods=['POST'])
# @inject 
def submit_job(): # Removed repo param
    """Submit a new documentation generation job."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON request body"}), 400

    try:
        request_data = DocumentRequest(**data)
    except ValidationError as e:
        logger.warning(f"Job submission validation failed: {e.errors()}")
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400

    # Use validated data
    repo_url = request_data.repoUrl
    use_obsidian = request_data.obsidianFormat

    # TODO: Add stricter validation for repo_url format if needed using regex or library

    job_id = str(uuid.uuid4())

    # Construct paths using flattened config
    clone_dir = config.CLONE_BASE_DIR / job_id
    output_dir_job = config.OUTPUT_BASE_DIR / job_id

    # Manually resolve dependencies needed for this endpoint/task
    # This assumes the main app context has the container configured,
    # but we instantiate locally for clarity/isolation here.
    # Consider attaching container to app context (`g`) if reused across requests.
    container = Container()
    # Note: Calling factory provider creates *new* instance, correct for repo.
    repo: JobHistoryRepository = container.job_history_repo()
    # Note: Calling singleton provider gets the *shared* instance.
    runner: Runner = container.adk_runner()

    db_record_id = None # Store ID for potential cleanup
    try:
        # 1. Create Initial History Record via Repository (using manually resolved repo)
        logger.info(f"Job {job_id}: Attempting to create initial history record for repo {repo_url}.")
        history_entry = repo.add_initial(job_id=job_id, repo_url=repo_url)
        
        # Retrieve ID immediately after creation, while session is active in repo
        if history_entry and history_entry.id:
            db_record_id = history_entry.id 
            logger.info(f"Job {job_id}: Initial history record created with ID {db_record_id}.")
        else:
             logger.error(f"Job {job_id}: repo.add_initial did not return a valid history entry with an ID.")
             raise HistoryUpdateError(f"Failed to get valid history entry ID for job {job_id}.")

        # 2. Enqueue Celery Task, passing only serializable data via kwargs
        logger.info(f"Job {job_id}: Attempting to enqueue Celery task.")
        run_adk_documentation_task.apply_async(
            # Pass ONLY serializable data that matches the task signature
            kwargs={
                # REMOVED: 'job_id': job_id, 
                # REMOVED: 'repo_url': repo_url, 
                'repo_clone_path': str(clone_dir),
                'output_dir_job': str(output_dir_job),
                'use_obsidian': use_obsidian
            },
            task_id=job_id
        )
        logger.info(f"Job {job_id}: Celery task successfully enqueued.")

        return jsonify({
            "job_id": job_id,
            "status": JobStatus.PENDING.value, # Use enum value
            "message": "Documentation job submitted successfully.",
            "clone_dir": str(clone_dir),
            "output_dir": str(output_dir_job)
        }), 202 # Accepted

    except HistoryUpdateError as e:
        logger.error(f"Job {job_id}: Failed to create history record: {e}", exc_info=True)
        return jsonify({"error": f"Failed to initialize job history: {e}"}), 500

    except Exception as e: # Catch other errors (e.g., Celery connection)
        logger.error(f"Job {job_id}: Failed to enqueue Celery task or other error: {e}", exc_info=True)
        if db_record_id:
            logger.warning(f"Job {job_id}: Attempting to delete history record ID {db_record_id} due to task enqueue failure.")
            try:
                # Use job_id for deletion as repo method expects it
                # We still need a repo instance here for cleanup.
                # Re-resolve a new one (it's cheap - factory pattern)
                cleanup_repo: JobHistoryRepository = container.job_history_repo()
                deleted = cleanup_repo.delete_by_job_id(job_id)
                logger.info(f"Job {job_id}: Cleanup deletion status for history record (Job ID {job_id}): {deleted}")
            except Exception as cleanup_err:
                logger.error(f"Job {job_id}: Error during history record cleanup (Job ID {job_id}): {cleanup_err}", exc_info=True)
        else:
            logger.warning(f"Job {job_id}: No history record ID available for cleanup after task enqueue failure.")
        return jsonify({"error": f"Failed to submit job to processing queue: {e}"}), 500 
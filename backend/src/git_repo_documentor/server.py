import asyncio
import threading
import uuid
import os
import logging
import tempfile
import shutil
import re # For basic Git URL check
import git # For cloning
from datetime import datetime, timezone # Added timezone
import json # Added for storing error info
from pathlib import Path # Added

from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from celery.result import AsyncResult

from google.adk.sessions import InMemorySessionService, BaseSessionService as SessionService
from google.adk.artifacts import InMemoryArtifactService, BaseArtifactService as ArtifactService
from google.adk.memory import InMemoryMemoryService, BaseMemoryService as MemoryService
# Use the correct relative import for the local service
from .services.memory_service import get_memory_service

# --- Import Celery app and task ---
from ..celery_app import celery_app
from .tasks import run_adk_documentation_task

# --- Import DB instance and Model from models.py ---
from .models import db, JobHistory

# --- Configuration ---
# Use pathlib for cleaner path construction
SERVER_DIR = Path(__file__).parent
INSTANCE_FOLDER_PATH = SERVER_DIR.parent / 'instance'
SQLITE_DB_PATH = INSTANCE_FOLDER_PATH / 'history.db'
SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH.resolve()}'

# Base directory for clones (configurable via environment variable)
CLONE_BASE_DIR = os.environ.get('CLONE_BASE_DIR', os.path.join(tempfile.gettempdir(), 'gitdocu_clones'))
# Base directory for output (configurable via environment variable)
OUTPUT_BASE_DIR = os.environ.get('OUTPUT_BASE_DIR', os.path.abspath("gitdocu_output"))

# Ensure base directories exist
os.makedirs(CLONE_BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True) # Ensure instance folder exists for DB

# --- Flask App Setup ---
app = Flask(__name__, instance_path=INSTANCE_FOLDER_PATH)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recommended

# Initialize SQLAlchemy with the app
db.init_app(app)

CORS(app) # Allow requests from the frontend development server
logging.basicConfig(level=logging.INFO) # Basic logging setup

# Check if DB URI is configured
if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    logging.error("FATAL: SQLALCHEMY_DATABASE_URI is not configured. History feature will not work.")
    # Optionally exit or raise an error if DB is critical for startup
    # sys.exit(1)

# --- Create Database Tables ---
with app.app_context():
    db.create_all()

# --- ADK Service Factory (Moved to services/factory.py) ---
# def create_service_factory() -> tuple[SessionService, ArtifactService, MemoryService]:
#     ...


# --- Pydantic Models for Request Validation ---
class DocumentRequest(BaseModel):
    repoUrl: str # Keep as string for now, validate format separately
    obsidianFormat: bool = False

# Basic Git URL validation (can be improved)
GIT_URL_REGEX = re.compile(r"^(?:git|ssh|https|http)://|^git@|^[^/]+@[^:]+:")

# --- API Endpoints ---

@app.route('/document', methods=['POST'])
def start_documentation():
    """
    Starts the documentation process by cloning a Git repository,
    creating a job history record, and enqueuing a Celery task.
    """
    try:
        data = DocumentRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400
    except Exception as e: # Catch potential JSON decoding errors
         return jsonify({"error": f"Failed to parse request body: {e}"}), 400

    repo_url = data.repoUrl

    # --- Basic Git URL Format Check ---
    # This is a basic check, not foolproof (e.g., doesn't guarantee reachability)
    if not GIT_URL_REGEX.match(repo_url):
        logging.warning(f"Received potentially invalid Git URL format: {repo_url}")
        # Decide whether to reject or attempt cloning anyway
        # return jsonify({"error": "Invalid Git repository URL format"}), 400
        # For now, let's allow it and let git clone fail if it's truly invalid.

    # --- Prepare Directories ---
    job_id = str(uuid.uuid4()) # Use Celery task ID later if preferred, but UUID is fine
    output_dir_job = os.path.join(OUTPUT_BASE_DIR, job_id)
    clone_dir = None # Initialize

    try:
        os.makedirs(output_dir_job, exist_ok=True)
        # Create a secure temporary directory for cloning
        # This context manager handles cleanup if the script crashes here,
        # but the task needs to clean it up upon completion/failure.
        # We create it *before* the task so we can pass the path.
        temp_dir_for_clone = tempfile.mkdtemp(prefix=f"{job_id}_", dir=CLONE_BASE_DIR)
        clone_dir = temp_dir_for_clone # Path to pass to the task
        logging.info(f"Job {job_id}: Created temporary clone directory: {clone_dir}")

    except Exception as e:
         logging.error(f"Job {job_id}: Failed to create directories: {e}", exc_info=True)
         # Attempt cleanup if clone_dir was partially created
         if clone_dir and os.path.exists(clone_dir):
             shutil.rmtree(clone_dir, ignore_errors=True)
         return jsonify({"error": f"Server error setting up job directories: {e}"}), 500

    # --- Clone Repository ---
    try:
        logging.info(f"Job {job_id}: Cloning {repo_url} into {clone_dir}")
        # Use GitPython or subprocess
        git.Repo.clone_from(repo_url, clone_dir, depth=1) # Shallow clone for speed
        logging.info(f"Job {job_id}: Cloning successful.")
    except git.GitCommandError as e:
        logging.error(f"Job {job_id}: Git clone failed for {repo_url}. Error: {e}", exc_info=True)
        # Clean up directories before returning error
        shutil.rmtree(clone_dir, ignore_errors=True)
        shutil.rmtree(output_dir_job, ignore_errors=True)
        return jsonify({
            "error": "Failed to clone repository",
            "details": str(e.stderr) # Provide Git's error message
        }), 400
    except Exception as e: # Catch other potential errors during clone setup
        logging.error(f"Job {job_id}: Error during git clone setup for {repo_url}: {e}", exc_info=True)
        shutil.rmtree(clone_dir, ignore_errors=True)
        shutil.rmtree(output_dir_job, ignore_errors=True)
        return jsonify({"error": f"Server error during repository cloning: {e}"}), 500

    # --- Create Initial History Record ---
    try:
        history_entry = JobHistory(
            job_id=job_id,
            repo_url=repo_url,
            status='PENDING'
            # request_time is default
        )
        db.session.add(history_entry)
        db.session.commit()
        logging.info(f"Job {job_id}: Created initial history record.")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Job {job_id}: Failed to create history record: {e}", exc_info=True)
        # Clean up directories since we can't track the job
        shutil.rmtree(clone_dir, ignore_errors=True)
        shutil.rmtree(output_dir_job, ignore_errors=True)
        return jsonify({"error": f"Server error saving job history: {e}"}), 500

    # --- Enqueue Celery Task ---
    try:
        task = run_adk_documentation_task.apply_async(
            args=[clone_dir, output_dir_job, data.obsidianFormat],
            task_id=job_id # Use the same ID for Celery task and history
        )
        logging.info(f"Job {job_id}: Submitted task for processing repo {repo_url}. Celery Task ID: {task.id}")
        return jsonify({
            "job_id": task.id,
            "status": "PENDING", # Initial status is PENDING
            "message": "Documentation task enqueued."
        }), 202
    except Exception as e:
        # Handle errors during task submission (e.g., broker connection error)
        logging.error(f"Job {job_id}: Failed to enqueue Celery task: {e}", exc_info=True)
        # Attempt to remove the history record we just added
        try:
            entry_to_delete = JobHistory.query.filter_by(job_id=job_id).first()
            if entry_to_delete:
                db.session.delete(entry_to_delete)
                db.session.commit()
                logging.info(f"Job {job_id}: Removed history record due to Celery submission failure.")
        except Exception as db_err:
            db.session.rollback()
            logging.error(f"Job {job_id}: Failed to remove history record after Celery error: {db_err}", exc_info=True)
        # Clean up directories since the task wasn't submitted
        shutil.rmtree(clone_dir, ignore_errors=True)
        shutil.rmtree(output_dir_job, ignore_errors=True)
        return jsonify({"error": f"Failed to submit documentation task: {e}"}), 500


@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Returns the status of a specific documentation job using Celery backend."""
    task_result = AsyncResult(job_id, app=celery_app)

    response = {
        "job_id": job_id,
        "status": task_result.status, # PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
        "details": None,
        "result": None,
        "error_info": None
    }

    if task_result.ready(): # Task finished (SUCCESS or FAILURE)
        if task_result.successful():
            result_data = task_result.get() # Get the return value from the task
            response["details"] = result_data.get("details", "Task completed.")
            response["result"] = result_data # Include full task result if needed
        else: # Task failed
            try:
                # Accessing result of a failed task raises the exception.
                # Access state info instead.
                response["details"] = "Task failed during execution."
                # Try to get metadata stored when state was updated to FAILURE
                if isinstance(task_result.info, dict):
                    response["error_info"] = {
                        "type": task_result.info.get("error_type", "Unknown"),
                        "message": task_result.info.get("details", str(task_result.info)), # Use 'details' from our FAILURE meta
                        # Optionally include traceback if stored and desired
                        # "traceback": task_result.info.get("traceback")
                    }
                elif isinstance(task_result.info, Exception):
                     response["error_info"] = {
                         "type": type(task_result.info).__name__,
                         "message": str(task_result.info)
                     }
                else: # Fallback if info is not an exception or dict
                     response["error_info"] = {
                         "type": "Unknown Error",
                         "message": str(task_result.info)
                     }

            except Exception as e:
                logging.error(f"Error retrieving failure info for job {job_id}: {e}", exc_info=True)
                response["details"] = f"Task failed, but error details could not be retrieved: {e}"
                response["error_info"] = {"type": "Retrieval Error", "message": str(e)}
    elif task_result.state == 'STARTED':
         # Try to get intermediate status from metadata if set via update_state
         meta = task_result.info or {}
         response["details"] = meta.get("status", "Task is running...")
    elif task_result.state == 'PENDING':
        response["details"] = "Task is waiting to be processed."
    else: # RETRY, REVOKED, or custom states
        response["details"] = f"Task is in state: {task_result.state}"

    return jsonify(response)


@app.route('/history', methods=['GET'])
def get_history():
    """Returns the history of documentation jobs from the database."""
    try:
        jobs = JobHistory.query.order_by(JobHistory.request_time.desc()).all()
        history_list = [job.to_dict() for job in jobs]
    return jsonify(history_list)
    except Exception as e:
        logging.error(f"Failed to retrieve job history from database: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve job history"}), 500


def run_server():
     # Set environment variable for Gemini API Key if needed by ADK
     # Ensure you have GOOGLE_API_KEY set in your environment where the server runs
     # if 'GOOGLE_API_KEY' not in os.environ:
     #    print("Warning: GOOGLE_API_KEY environment variable not set. ADK might fail.")

     # Determine host and port from environment variables
     host = os.environ.get('FLASK_HOST', '127.0.0.1')
     port = int(os.environ.get('FLASK_PORT', 5001))

     logging.info(f"Starting Flask server on http://{host}:{port}")
     logging.info(f"Database located at: {SQLALCHEMY_DATABASE_URI}")
     # Use a production-ready WSGI server (like gunicorn or waitress) instead of app.run in production
     # For development:
     app.run(host=host, port=port, debug=False) # Keep debug=False for stability, especially with Celery


if __name__ == '__main__':
    # This allows running the server directly with `python -m backend.src.git_repo_documentor.server`
    # Make sure PYTHONPATH includes the project root or adjust imports accordingly.
     # Remember to also run Celery workers:
     # celery -A backend.src.celery_app worker --loglevel=info
     run_server()

# To run from project root: poetry run python -m backend.src.git_repo_documentor.server
# And in another terminal: poetry run celery -A backend.src.celery_app worker --loglevel=info
# Ensure Redis server is running.
# Ensure required environment variables (e.g., for ADK services, broker URLs) are set.

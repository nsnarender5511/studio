import logging
import json
from flask import Blueprint, jsonify
from celery.result import AsyncResult
from datetime import datetime

# Use relative imports within the 'app' package
# Removed db import as it's accessed via repository
# from ..models import db, JobHistory
from ..celery_app import celery_app
# Import the constants
from ..constants import JobStatus

# DI Imports
from dependency_injector.wiring import inject, Provide
from src.app.container import Container
from src.persistence.repository import JobHistoryRepository

logger = logging.getLogger(__name__)

history_bp = Blueprint('history_api', __name__, url_prefix='/api/v1') # Using a versioned prefix

@history_bp.route('/status/<job_id>', methods=['GET'])
@inject # Apply decorator
def get_job_status(job_id: str, repo: JobHistoryRepository = Provide[Container.job_history_repo]): # Inject repository
    """Get the status of a specific job."""
    # Check Celery task state first
    task_result = AsyncResult(job_id, app=celery_app)
    celery_state = task_result.state

    # Query database record via repository
    job_record = repo.get_by_job_id(job_id)

    if not job_record:
        # If no DB record, rely on Celery state if available, otherwise 404
        # Use Enum values for comparison
        if celery_state == JobStatus.PENDING.value:
            return jsonify({"job_id": job_id, "status": JobStatus.PENDING.value, "details": "Task is waiting in queue."}), 200
        elif celery_state == JobStatus.STARTED.value:
            return jsonify({"job_id": job_id, "status": JobStatus.STARTED.value, "details": "Task has started processing."}), 200
        else:
            logger.warning(f"Status requested for unknown job_id: {job_id}")
            return jsonify({"error": "Job not found"}), 404

    # Combine DB info with Celery state
    response = {
        "job_id": job_record.job_id,
        "repo_url": job_record.repo_url,
        # Use status directly from DB record (should be the string value)
        "status": job_record.status,
        "request_time": job_record.request_time.isoformat() if job_record.request_time else None,
        "end_time": job_record.end_time.isoformat() if job_record.end_time else None,
        "details": job_record.details
    }

    # Refine status based on Celery if DB is still PENDING/STARTED
    # Compare DB status (which is the enum value string) with Enum values
    if job_record.status in [JobStatus.PENDING.value, JobStatus.STARTED.value]:
        if celery_state == JobStatus.PROGRESS.value:
            response['status'] = JobStatus.PROGRESS.value
            response['details'] = task_result.info.get('status', 'Processing...') if isinstance(task_result.info, dict) else 'Processing...'
        elif celery_state == 'SUCCESS' and job_record.status != JobStatus.COMPLETED.value:
            response['status'] = JobStatus.COMPLETED.value # Assume success means Completed
            response['details'] = "Task completed (DB update may be slightly delayed)."
        elif celery_state == 'FAILURE' and job_record.status != JobStatus.FAILED.value:
            response['status'] = JobStatus.FAILED.value
            response['details'] = "Task failed (DB update may be slightly delayed)."
            # Try to get error info from Celery result if DB hasn't updated yet
            if isinstance(task_result.info, dict):
                 response["error_info"] = task_result.info # Or extract relevant parts
            elif isinstance(task_result.info, Exception):
                 response["error_info"] = {"error_type": type(task_result.info).__name__, "message": str(task_result.info)}

    # Add error info if job failed (from DB record)
    elif job_record.status == JobStatus.FAILED.value and job_record.error_info_json:
        try:
             response["error_info"] = json.loads(job_record.error_info_json)
        except json.JSONDecodeError:
             logger.warning(f"Failed to parse error_info_json for job {job_id}")
             response["error_info"] = {"raw": job_record.error_info_json}

    return jsonify(response), 200

@history_bp.route('/history', methods=['GET'])
@inject # Apply decorator
def get_job_history(repo: JobHistoryRepository = Provide[Container.job_history_repo]): # Inject repository
    """Get a list of recent job history."""
    # Get jobs via repository
    # TODO: Implement pagination using request args (e.g., page, per_page)
    jobs = repo.get_all_history() # Add limit/pagination later if needed

    history_list = [
        {
            "job_id": job.job_id,
            "repo_url": job.repo_url,
            "status": job.status, # Assumes this is already the string value stored
            "request_time": job.request_time.isoformat() if job.request_time else None,
            "end_time": job.end_time.isoformat() if job.end_time else None,
            "details": job.details
        }
        for job in jobs
    ]

    return jsonify(history_list), 200 
import logging
import shutil
import asyncio
import os
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone

# Import Celery app instance
from src.app.celery_app import celery_app

# DI Imports
from dependency_injector.wiring import inject, Provide
from src.app.container import Container
from google.adk.runners import Runner
from src.persistence.repository import JobHistoryRepository

from src.exceptions import TaskEnqueueError, HistoryUpdateError, AdkOrchestrationError
from src.app.constants import JobStatus, AdkStages
from src.app.config import config # Import config for user_id

logger = logging.getLogger(__name__)

# --- Wiring removed - Handled centrally in celery_app.py ---
# try:
#     # Ensure container instance is available
#     container_instance = Container()
#     # Wire *only* this module
#     container_instance.wire(modules=[__name__])
#     logger.debug(f"Container wired for module: {__name__}")
# except Exception as e:
#     logger.error(f"Failed to wire container for {__name__}: {e}", exc_info=True)
#     # Decide how to handle: raise error? Log and continue (DI might fail)?
#     # For now, just log.
# --- End Wiring --- 

async def _execute_adk_flow(
    job_id: str,
    repo_clone_path: str,
    output_dir_job: str,
    use_obsidian: bool,
    runner: Runner,
    repo: JobHistoryRepository,
    update_progress_callback: Optional[callable] = None # Optional callback for progress
) -> Dict[str, Any]:
    """Core async logic for executing the ADK documentation flow."""
    
    final_status = JobStatus.FAILED
    final_state_summary = None
    error_info = None
    original_exception = None
    current_stage = "ADK Flow Start"

    try:
        logger.info(f"Job {job_id}: Starting ADK flow logic.")
        
        current_stage = AdkStages.INITIAL_STATE_CREATION.value
        initial_state_data = {
            "repo_path": repo_clone_path,
            "output_dir": output_dir_job,
            "use_obsidian_format": use_obsidian,
            "verbose_logging": True
        }

        current_stage = AdkStages.ADK_RUNNER_EXECUTION.value
        logger.info(f"Job {job_id}: Starting ADK runner execution.")

        user_id = config.ADK_USER_ID if hasattr(config, 'ADK_USER_ID') else "gitdocu_user_default"
        session_id = job_id

        last_event = None
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=initial_state_data
        ):
            logger.debug(f"Job {job_id}: Received ADK event: ID={event.id}, Author={event.author}, Actions={event.actions}")
            last_event = event
            current_adk_stage = event.actions.state_delta.get("current_stage", current_stage)
            
            if update_progress_callback:
                # Provide progress updates via callback
                try:
                    update_progress_callback(state=JobStatus.PROGRESS.value, meta={'status': f'Processing ADK event {event.id}...', 'current_stage': current_adk_stage})
                except Exception as cb_err:
                     logger.warning(f"Job {job_id}: Progress callback failed: {cb_err}")

            current_stage = current_adk_stage

        if last_event is None:
            logger.warning(f"Job {job_id}: ADK runner finished without yielding any events.")
            raise AdkOrchestrationError("ADK runner did not produce any events.", stage=current_stage)

        final_event = last_event
        final_state_delta = final_event.actions.state_delta if final_event and final_event.actions else {}
        logger.info(f"Job {job_id}: ADK runner execution finished. Final event ID: {final_event.id}.")
        logger.debug(f"Job {job_id}: Final event state delta: {final_state_delta}")

        current_stage = AdkStages.RESULT_PROCESSING.value
        orchestration_status_str = final_state_delta.get('orchestration_status', 'Unknown')

        if orchestration_status_str == JobStatus.COMPLETED.value:
            final_status = JobStatus.COMPLETED
            final_state_summary = {
                 "message": "ADK flow completed successfully.",
                 "documentation_plan_results": final_state_delta.get('documentation_plan_results', [])
            }
            logger.info(f"Job {job_id}: Orchestration reported completion.")
        else:
            final_status = JobStatus.FAILED
            details = final_state_delta.get("error_details", f"Orchestration status: {orchestration_status_str}")
            error_stage = final_state_delta.get("error_stage", current_stage)
            error_info = {
                'status': JobStatus.FAILED.value,
                'details': details,
                'stage': error_stage,
                'error_type': final_state_delta.get("error_type", "OrchestrationError"),
            }
            logger.warning(f"Job {job_id}: Orchestration did not report completion. Status: {orchestration_status_str}, Details: {details}, Stage: {error_stage}")
            if not original_exception:
                original_exception = AdkOrchestrationError(details, stage=error_stage)

    except Exception as e:
        original_exception = e
        logger.error(f"Job {job_id}: Error during ADK flow execution at stage '{current_stage}': {e}", exc_info=True)
        final_status = JobStatus.FAILED
        error_info = {
            'status': JobStatus.FAILED.value,
            'details': f"Unexpected task error at stage '{current_stage}': {str(e)}",
            'stage': current_stage,
            'error_type': type(e).__name__
        }
    
    finally:
        logger.info(f"Job {job_id}: ADK flow finished. Final Status: {final_status.value}. Attempting DB update.")
        details_for_db = None
        if final_status == JobStatus.FAILED and error_info:
            details_for_db = error_info.get('details', "Unknown error")
        elif final_status == JobStatus.COMPLETED and final_state_summary:
            details_for_db = final_state_summary.get('message', "Completed successfully")

        try:
            repo.update_final_status(
                job_id=job_id,
                status=final_status,
                end_time=datetime.now(timezone.utc),
                details=details_for_db,
                error_info=error_info
            )
            logger.info(f"Job {job_id}: Successfully updated final history record status to '{final_status.value}'.")
        except Exception as db_err:
            logger.critical(f"Job {job_id}: FAILED TO UPDATE FINAL DB STATUS to '{final_status.value}': {db_err}", exc_info=True)

        # Cleanup is handled outside this core function now

    # Return result dictionary
    return {
        "final_status": final_status.value,
        "details": details_for_db,
        "error_info": error_info # Pass the whole dict
    }


@celery_app.task(bind=True)
def run_adk_documentation_task(
    self,
    repo_clone_path: str,
    output_dir_job: str,
    use_obsidian: bool
):
    """Celery task wrapper for ADK documentation flow."""
    job_id = self.request.id
    if not job_id:
        logger.error("Celery task started without a job_id in request context.")
        # Cannot proceed without job_id for DB updates and ADK session
        return { "final_status": JobStatus.FAILED.value, "details": "Missing job_id in task context", "error_info": {"error_type": "ConfigurationError"} }

    logger.info(f"Job {job_id}: Celery worker received task for repo path {repo_clone_path}")
    self.update_state(state=JobStatus.STARTED.value, meta={'status': 'Resolving dependencies...'})

    container = Container()
    runner: Optional[Runner] = None
    repo: Optional[JobHistoryRepository] = None
    
    try:
        runner = container.adk_runner()
        repo = container.job_history_repo()
        logger.info(f"Job {job_id}: Runner and Repository resolved from container.")
    except Exception as e:
        logger.critical(f"Job {job_id}: Failed to resolve critical dependencies (Runner/Repo): {e}", exc_info=True)
        # Attempt to update DB to FAILED even if DI fails
        try:
            # Try resolving repo again just for cleanup
            repo_for_cleanup = container.job_history_repo()
            error_info = {
                'status': JobStatus.FAILED.value,
                'details': f"Dependency Injection failed: {str(e)}",
                'stage': 'Dependency Resolution',
                'error_type': type(e).__name__
            }
            repo_for_cleanup.update_final_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                end_time=datetime.now(timezone.utc),
                details=error_info['details'],
                error_info=error_info
            )
        except Exception as cleanup_err:
             logger.critical(f"Job {job_id}: FAILED TO UPDATE DB STATUS after DI failure: {cleanup_err}", exc_info=True)
        # Return failure to Celery
        return { "final_status": JobStatus.FAILED.value, "details": f"Dependency Injection failed: {str(e)}", "error_info": {"error_type": type(e).__name__} }

    # --- Define Progress Callback for Celery --- 
    def update_celery_progress(state: str, meta: dict):
        self.update_state(state=state, meta=meta)

    # --- Execute Core Logic --- 
    try:
        # Run the core async logic
        result_dict = asyncio.run(_execute_adk_flow(
            job_id=job_id,
            repo_clone_path=repo_clone_path,
            output_dir_job=output_dir_job,
            use_obsidian=use_obsidian,
            runner=runner,
            repo=repo,
            update_progress_callback=update_celery_progress # Pass the callback
        ))
        # The core function handles the final DB update
        logger.info(f"Job {job_id}: Core ADK flow finished. Result: {result_dict}")
        return result_dict # Return result to Celery
    
    except Exception as task_exec_err:
        logger.error(f"Job {job_id}: Unexpected error during core logic execution: {task_exec_err}", exc_info=True)
        # Final DB update is attempted within _execute_adk_flow's finally block
        # We still need to return a failure state to Celery
        return {
            "final_status": JobStatus.FAILED.value,
            "details": f"Core task execution failed: {str(task_exec_err)}",
            "error_info": {"error_type": type(task_exec_err).__name__, "stage": "Core Logic Execution"}
        }
    finally:
         # --- Cleanup Cloned Repo (Moved here from core logic) ---
         if repo_clone_path and os.path.exists(repo_clone_path):
             try:
                 shutil.rmtree(repo_clone_path)
                 logger.info(f"Job {job_id}: Successfully cleaned up clone directory: {repo_clone_path}")
             except OSError as e:
                 logger.error(f"Job {job_id}: Error cleaning up clone directory {repo_clone_path}: {e}", exc_info=True)
         else:
             logger.warning(f"Job {job_id}: Clone directory {repo_clone_path} not found or not specified, skipping cleanup.")


# --- Wiring removal and other comments omitted for brevity --- 
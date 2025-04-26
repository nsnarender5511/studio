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

from src.exceptions import TaskEnqueueError, HistoryUpdateError, AdkOrchestrationError # Keep exception imports
# Import constants
from src.app.constants import JobStatus, AdkStages

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

@celery_app.task(bind=True)
# @inject # Keep inject commented if wiring is central
def run_adk_documentation_task(
    self,
    repo_clone_path: str,
    output_dir_job: str,
    use_obsidian: bool
):
    """The main Celery task to run the ADK documentation flow.
    
    This synchronous task wraps the core async logic using asyncio.run().
    """
    job_id = self.request.id # Get job_id from task context
    logger.info(f"Job {job_id}: Worker received task for repo path {repo_clone_path}")
    # Use Enum for state reporting
    self.update_state(state=JobStatus.STARTED.value, meta={'status': 'Starting ADK documentation flow...'})

    # Define a nested async function to contain the original logic
    async def _run_async_logic():
        # --- Resolve Dependencies using Container --- 
        container = Container()
        try:
            runner: Runner = container.adk_runner()
            repo: JobHistoryRepository = container.job_history_repo()
            logger.info(f"Job {job_id}: Runner and Repository resolved from container.")
        except Exception as e:
            logger.critical(f"Job {job_id}: Failed to resolve critical dependencies (Runner/Repo) from container: {e}", exc_info=True)
            # If DI fails, the exception will be caught by the outer try/except
            raise TaskEnqueueError(f"Dependency Injection failed for job {job_id}: {e}") from e
        # --- End Dependency Resolution --- 

        final_status = JobStatus.FAILED # Default to Enum
        final_state_summary = None
        error_info = None
        original_exception = None
        current_stage = "Task Execution Start"

        try:
            # --- Start of ADK Logic using resolved runner --- 
            logger.info(f"Job {job_id}: Starting ADK flow logic inside async wrapper.")

            # Service/Agent/Tool setup is handled by the container providers for the Runner
            current_stage = AdkStages.INITIAL_STATE_CREATION.value
            initial_state_data = {
                "repo_path": repo_clone_path,
                "output_dir": output_dir_job,
                "use_obsidian_format": use_obsidian,
                "verbose_logging": True
            }

            current_stage = AdkStages.ADK_RUNNER_EXECUTION.value
            logger.info(f"Job {job_id}: Starting ADK runner execution.")

            # Use config object directly for ADK_USER_ID
            user_id = config.ADK_USER_ID if hasattr(config, 'ADK_USER_ID') else "gitdocu_user_default" 
            session_id = job_id # Use Celery task ID as session ID

            last_event = None
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=initial_state_data
            ):
                logger.debug(f"Job {job_id}: Received ADK event: ID={event.id}, Author={event.author}, Actions={event.actions}")
                last_event = event
                current_adk_stage = event.actions.state_delta.get("current_stage", current_stage) # Get stage from event if available
                # Update Celery progress state (Note: self.update_state is sync)
                self.update_state(state=JobStatus.PROGRESS.value, meta={'status': f'Processing ADK event {event.id}...', 'current_stage': current_adk_stage})
                current_stage = current_adk_stage # Update local stage tracker

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

            # --- End of ADK Logic --- 

        except Exception as e:
            original_exception = e
            logger.error(f"Job {job_id}: Error during async task execution at stage '{current_stage}': {e}", exc_info=True)
            final_status = JobStatus.FAILED
            error_info = {
                'status': JobStatus.FAILED.value,
                'details': f"Unexpected task error at stage '{current_stage}': {str(e)}",
                'stage': current_stage,
                'error_type': type(e).__name__
            }
        
        finally:
            # --- Update DB using Repository --- 
            logger.info(f"Job {job_id}: Async logic finished. Final Status: {final_status.value}. Attempting DB update.")
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

            # --- Cleanup Cloned Repo --- 
            if repo_clone_path and os.path.exists(repo_clone_path):
                try:
                    shutil.rmtree(repo_clone_path)
                    logger.info(f"Job {job_id}: Successfully cleaned up clone directory: {repo_clone_path}")
                except OSError as e:
                    logger.error(f"Job {job_id}: Error cleaning up clone directory {repo_clone_path}: {e}", exc_info=True)
            else:
                 logger.warning(f"Job {job_id}: Clone directory {repo_clone_path} not found or not specified, skipping cleanup.")

        # Return the final result dictionary from the async logic block
        return {
            "final_status": final_status.value,
            "details": details_for_db,
            "error_type": error_info.get('error_type') if error_info else None 
        } 

    # --- Execute the nested async function using asyncio.run() --- 
    try:
         # This runs the async logic and returns the final dictionary
         result_dict = asyncio.run(_run_async_logic())
         return result_dict # Return the serializable dict to Celery
    except Exception as task_exec_err:
         # Catch potential errors from asyncio.run or DI failure
         logger.error(f"Job {job_id}: Top-level task execution error: {task_exec_err}", exc_info=True)
         # Attempt to update DB status to FAILED even if main logic failed
         try:
             container = Container() # Resolve container again for cleanup
             repo: JobHistoryRepository = container.job_history_repo()
             error_info = {
                'status': JobStatus.FAILED.value,
                'details': f"Task execution failed before DB update: {str(task_exec_err)}",
                'stage': 'Task Initialization/Async Run',
                'error_type': type(task_exec_err).__name__
             }
             repo.update_final_status(
                 job_id=job_id,
                 status=JobStatus.FAILED,
                 end_time=datetime.now(timezone.utc),
                 details=error_info['details'],
                 error_info=error_info
             )
             logger.info(f"Job {job_id}: Successfully updated final history record status to FAILED after top-level error.")
         except Exception as cleanup_db_err:
             logger.critical(f"Job {job_id}: FAILED TO UPDATE DB STATUS after top-level task error: {cleanup_db_err}", exc_info=True)
         
         # Return a failure dictionary directly to Celery
         return {
              "final_status": JobStatus.FAILED.value,
              "details": f"Task execution failed: {str(task_exec_err)}",
              "error_type": type(task_exec_err).__name__
         } 
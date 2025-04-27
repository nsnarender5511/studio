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
from google.adk.runners import Runner, RunConfig, InvocationContext, Event
from google.adk.events import EventActions
from src.persistence.repository import JobHistoryRepository

from src.exceptions import TaskEnqueueError, HistoryUpdateError, AdkOrchestrationError
from src.app.constants import JobStatus, AdkStages, AgentKeys
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

# Define the async helper function containing the core logic
async def _run_adk_orchestration_logic(
    job_id: str,
    repo_clone_path: str,
    output_dir_job: str,
    use_obsidian: bool,
    runner: Runner,
    repo: JobHistoryRepository,
    update_progress_callback: callable # Re-introduce callback
):
    """Core async logic for ADK orchestration, callable by task and test."""
    final_status = JobStatus.FAILED # Default to failed
    final_result_details = "Orchestration did not complete as expected."
    error_info = None
    final_event_data = {}
    current_stage = AdkStages.ORCHESTRATION_START.value # Ensure defined
    
    try:
        # Initial progress update
        update_progress_callback(state=JobStatus.PROGRESS.value, meta={'status': 'Starting ADK Flow...', 'current_stage': current_stage})
        
        user_id = config.ADK_USER_ID if hasattr(config, 'ADK_USER_ID') else "gitdocu_user_default"
        session_id = job_id # Use job_id as session_id

        # Prepare initial state (verified in Phase 0)
        initial_state_data = {
            "repo_path": repo_clone_path,
            "output_dir": output_dir_job,
            "use_obsidian_format": use_obsidian,
            "verbose_logging": True # Or derive from config
        }

        logger.info(f"Job {job_id}: Starting ADK runner execution.")
        current_stage = AdkStages.ADK_RUNNER_EXECUTION.value # Update stage
        update_progress_callback(state=JobStatus.PROGRESS.value, meta={'status': 'ADK Runner executing...', 'current_stage': current_stage})

        # --- ADK Runner Invocation --- 
        # Define an async function to wrap the async generator
        async def _run_adk_runner_async():
            nonlocal current_stage # Tell python to use current_stage from the outer scope
            _last_event = None
            _final_state_delta = {}
            # Revert new_message back to empty dict
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=dict(), # Revert back to empty dict
                run_config=RunConfig()
            ):
                logger.debug(f"Job {job_id}: Received ADK event: ID={event.id}, Author={event.author}, Actions={event.actions}")
                _last_event = event
                # Get stage and detail from the event's state delta
                if event.actions and event.actions.state_delta:
                     current_adk_stage = event.actions.state_delta.get("current_stage", current_stage)
                     status_detail = event.actions.state_delta.get("status_detail", f'Processing ADK event {event.id}...')
                     # Update Celery progress from within async loop
                     update_progress_callback(state=JobStatus.PROGRESS.value, meta={'status': status_detail, 'current_stage': current_adk_stage})
                     current_stage = current_adk_stage # Update overall stage tracker
                else:
                     # Fallback if no state delta in event
                     update_progress_callback(state=JobStatus.PROGRESS.value, meta={'status': f'Processing ADK event {event.id}...', 'current_stage': current_stage})
                _final_state_delta = event.actions.state_delta if event and event.actions else {}
            return _last_event, _final_state_delta

        # --- Process Final ADK Event --- 
        # REMOVED initial_state_data argument from call
        last_event, final_state_delta = await _run_adk_runner_async()
        if last_event is None:
            logger.warning(f"Job {job_id}: ADK runner finished without yielding any events.")
            raise AdkOrchestrationError("ADK runner did not produce any events.", stage=current_stage)

        final_event_data = final_state_delta
        logger.info(f"Job {job_id}: ADK runner execution finished. Final event ID: {last_event.id}.")
        logger.debug(f"Job {job_id}: Final event state delta: {final_event_data}")

        current_stage = AdkStages.RESULT_PROCESSING.value # Update stage
        orchestration_status_str = final_event_data.get('orchestration_status', JobStatus.FAILED.value)

        if orchestration_status_str == JobStatus.COMPLETED.value:
            final_status = JobStatus.COMPLETED
            final_result_details = final_event_data.get("message", "ADK flow completed successfully.")
            logger.info(f"Job {job_id}: Orchestration reported completion.")
        else:
            final_status = JobStatus.FAILED
            details = final_event_data.get("error_details", f"Orchestration failed with status: {orchestration_status_str}")
            error_stage = final_event_data.get("error_stage", current_stage)
            error_type = final_event_data.get("error_type", "OrchestrationError")
            final_result_details = details
            error_info = {
                'status': JobStatus.FAILED.value,
                'details': details,
                'stage': error_stage,
                'error_type': error_type,
            }
            logger.warning(f"Job {job_id}: Orchestration did not report completion. Status: {orchestration_status_str}, Details: {details}, Stage: {error_stage}")
            
    except Exception as task_exec_err:
        logger.error(f"Job {job_id}: Unexpected error during ADK orchestration: {task_exec_err}", exc_info=True)
        final_status = JobStatus.FAILED
        final_result_details = f"Core task execution failed: {str(task_exec_err)}"
        if not error_info: # Capture error info if not already set by ADK failure
             error_info = {
                 'status': JobStatus.FAILED.value,
                 'details': final_result_details,
                 'stage': current_stage, # Stage where the exception occurred
                 'error_type': type(task_exec_err).__name__
             }
             
    # Return results for the caller (Celery task or test script)
    return {
        "final_status": final_status,
        "final_result_details": final_result_details, 
        "error_info": error_info,
        "final_event_data": final_event_data # Include final state delta for inspection
    }


@celery_app.task(bind=True)
def run_adk_documentation_task(
    self,
    repo_clone_path: str,
    output_dir_job: str,
    use_obsidian: bool,
):
    """Celery task wrapper that executes the ADK documentation flow."""
    job_id = self.request.id
    if not job_id:
        logger.error("Celery task started without a job_id in request context.")
        return { "final_status": JobStatus.FAILED.value, "details": "Missing job_id in task context", "error_info": {"error_type": "ConfigurationError"} }

    logger.info(f"Job {job_id}: Celery worker received task for repo path {repo_clone_path}")
    self.update_state(state=JobStatus.STARTED.value, meta={'status': 'Resolving dependencies...'})

    # --- Resolve Dependencies (Manual or DI) ---
    container = Container() # Manual resolution for now
    runner: Optional[Runner] = None
    repo: Optional[JobHistoryRepository] = None
    try:
        runner = container.adk_runner()
        repo = container.job_history_repo()
        logger.info(f"Job {job_id}: Runner and Repository resolved manually from container.")
    except Exception as e:
        logger.critical(f"Job {job_id}: Failed to resolve critical dependencies (Runner/Repo): {e}", exc_info=True)
        # Attempt to update DB status even if DI/resolution fails
        # ... (DB update logic omitted for brevity, assume it attempts update) ...
        return { "final_status": JobStatus.FAILED.value, "details": f"Dependency Resolution failed: {str(e)}", "error_info": {"error_type": type(e).__name__} }

    # --- Define Progress Callback for Celery --- 
    def update_celery_progress(state: str, meta: dict):
        # Update Celery task state
        try: 
            self.update_state(state=state, meta=meta)
            logger.debug(f"Job {job_id}: Updated Celery state to {state}, Meta: {meta}")
        except Exception as prog_err:
             logger.warning(f"Job {job_id}: Failed to update Celery progress state: {prog_err}")

    # --- Execute Core Async Logic --- 
    final_status = JobStatus.FAILED # Default status
    final_result_details = "Task did not run core logic."
    error_info = None
    
    try:
        # Run the extracted async logic using asyncio.run()
        result = asyncio.run(_run_adk_orchestration_logic(
             job_id=job_id,
             repo_clone_path=repo_clone_path,
             output_dir_job=output_dir_job,
             use_obsidian=use_obsidian,
             runner=runner,
             repo=repo, # Pass repo for potential use inside logic if needed
             update_progress_callback=update_celery_progress
        ))
        # Extract results
        final_status = result.get("final_status", JobStatus.FAILED)
        final_result_details = result.get("final_result_details", "Core logic finished without details.")
        error_info = result.get("error_info")
        
    except Exception as task_exec_err:
        logger.error(f"Job {job_id}: Error running core ADK logic from task: {task_exec_err}", exc_info=True)
        final_status = JobStatus.FAILED
        final_result_details = f"Celery task wrapper failed: {str(task_exec_err)}"
        if not error_info: # Capture error if not already set by core logic failure
             error_info = {
                 'status': JobStatus.FAILED.value,
                 'details': final_result_details,
                 'stage': 'Celery Task Execution', 
                 'error_type': type(task_exec_err).__name__
             }
    
    finally:
        # --- Update Final DB Status --- 
        logger.info(f"Job {job_id}: Attempting final DB update. Status: {final_status.value}. Details: {final_result_details}")
        try:
            repo.update_final_status(
                job_id=job_id,
                status=final_status,
                end_time=datetime.now(timezone.utc),
                details=final_result_details,
                error_info=error_info # Pass the whole dict if available
            )
            logger.info(f"Job {job_id}: Successfully updated final history record status to '{final_status.value}'.")
        except Exception as db_err:
            logger.critical(f"Job {job_id}: FAILED TO UPDATE FINAL DB STATUS to '{final_status.value}': {db_err}", exc_info=True)

        # --- Cleanup Cloned Repo --- 
        if repo_clone_path and os.path.exists(repo_clone_path):
             try:
                 # Keep cleanup synchronous within the sync Celery task
                 shutil.rmtree(repo_clone_path)
                 logger.info(f"Job {job_id}: Successfully cleaned up clone directory: {repo_clone_path}")
             except OSError as e:
                 logger.error(f"Job {job_id}: Error cleaning up clone directory {repo_clone_path}: {e}", exc_info=True)
        else:
             logger.warning(f"Job {job_id}: Clone directory {repo_clone_path} not found or not specified, skipping cleanup.")

    # --- Return result dictionary to Celery --- 
    logger.info(f"Job {job_id}: Celery task finished with status: {final_status.value}")
    return {
        "final_status": final_status.value,
        "details": final_result_details, 
        "error_info": error_info
    }


# --- REMOVED _execute_adk_flow function as it's integrated above --- 

# --- REMOVED enqueue_documentation_job - Belongs in API layer (e.g., app/api/jobs_api.py) --- 

# --- Wiring removal and other comments omitted for brevity --- 
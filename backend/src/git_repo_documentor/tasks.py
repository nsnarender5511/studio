import asyncio
import os
import shutil
import tempfile
import logging
import traceback
from datetime import datetime, timezone
import json
from contextlib import contextmanager

from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, State, BaseSessionService as SessionService
from google.adk.artifacts import InMemoryArtifactService, BaseArtifactService as ArtifactService
from google.adk.memory import BaseMemoryService as MemoryService

from ..celery_app import celery_app # Import the Celery app instance
# Import model definition from new location
from .models import JobHistory
from .services.factory import create_service_factory

from .agents.orchestrator import OrchestratorAgent # Adjust imports based on actual structure
from .agents.orchestrator import (
    file_identification_agent, structure_designer_agent, code_parser_agent,
    code_interpreter_agent, dependency_analyzer_agent, testing_analyzer_agent,
    feature_extractor_agent, content_generator_agent, verifier_agent,
    visualizer_agent, md_formatter_agent, obsidian_writer_agent, summarizer_agent,
    fact_checker_agent, self_reflection_agent, code_execution_verifier_agent
)
from .tools import (
    read_directory_tool, read_file_tool, write_file_tool, ensure_directory_exists_tool,
    code_parser_tool, dependency_analyzer_tool, web_search_tool, visualization_tool,
    format_obsidian_links_tool, knowledge_graph_tool, memory_interaction_tool,
    fact_verification_tool, code_executor_tool
)
from .services.memory_service import get_memory_service

logger = logging.getLogger(__name__)

# --- Standalone DB Session Helper ---
@contextmanager
def get_db_session():
    """Provides a transactional scope around a series of operations."""
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        logger.warning("SQLALCHEMY_DATABASE_URI environment variable not set. Cannot get DB session.")
        yield None # Yield None if DB is not configured
        return

    engine = None
    session = None
    try:
        engine = create_engine(db_uri)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.commit() # Commit if context block completes without error
    except Exception:
        if session: session.rollback() # Rollback on error
        logger.error("Database session error", exc_info=True)
        raise # Re-raise the exception after rollback
    finally:
        if session: session.close()
        # Dispose engine if needed, depends on connection pooling strategy
        # if engine: engine.dispose()

def update_job_history(job_id: str, status: str, details: str = None, final_state_summary: dict = None, error_info: dict = None):
    """Helper function to update the JobHistory record in the database."""
    with get_db_session() as session:
        if not session:
            logger.warning(f"Job {job_id}: Skipping history update because database session could not be created.")
            return

        try:
            job_record = session.query(JobHistory).filter(JobHistory.job_id == job_id).first()
            if job_record:
                job_record.status = status
                job_record.end_time = datetime.now(timezone.utc)
                job_record.details = details

                if error_info:
                    # Exclude traceback before storing
                    error_info_to_store = {k: v for k, v in error_info.items() if k != 'traceback'}
                    job_record.error_info_json = json.dumps(error_info_to_store)
                else:
                    job_record.error_info_json = None # Clear error info on success

                # No explicit commit here, handled by context manager
                logger.info(f"Job {job_id}: History record update prepared for status '{status}'.")
            else:
                logger.warning(f"Job {job_id}: Could not find history record to update.")
        except Exception as e:
            # Log error, rollback is handled by context manager
            logger.error(f"Job {job_id}: Error preparing history record update: {e}", exc_info=True)
            # Re-raise might be needed if we want the task update to fail
            # raise

@celery_app.task(bind=True)
def run_adk_documentation_task(self, repo_clone_path: str, output_dir_job: str, use_obsidian: bool):
    """Celery task to run the ADK documentation process."""
    job_id = self.request.id
    logger.info(f"Job {job_id}: Starting ADK task for {repo_clone_path}")
    self.update_state(state='STARTED', meta={'status': 'Running ADK process...'})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    final_state_summary = None
    status_details = ""
    task_status = "FAILURE" # Default to failure
    error_info = None
    original_exception = None # Store original exception

    try:
        session_service, artifact_service, memory_service = create_service_factory()

        sub_agents = {
            "file_identification": file_identification_agent,
            "structure_designer": structure_designer_agent,
            "code_parser": code_parser_agent,
            "code_interpreter": code_interpreter_agent,
            "dependency_analyzer": dependency_analyzer_agent,
            "testing_analyzer": testing_analyzer_agent,
            "feature_extractor": feature_extractor_agent,
            "content_generator": content_generator_agent,
            "verifier": verifier_agent,
            "visualizer": visualizer_agent,
            "md_formatter": md_formatter_agent,
            "obsidian_writer": obsidian_writer_agent,
            "summarizer": summarizer_agent,
            "fact_checker": fact_checker_agent,
            "self_reflection": self_reflection_agent,
            "code_execution_verifier": code_execution_verifier_agent,
        }
        tools = [
            read_directory_tool, read_file_tool, write_file_tool, ensure_directory_exists_tool,
            code_parser_tool, dependency_analyzer_tool, web_search_tool, visualization_tool,
            format_obsidian_links_tool, knowledge_graph_tool, memory_interaction_tool,
            fact_verification_tool, code_executor_tool
        ]

        orchestrator = OrchestratorAgent(sub_agents=sub_agents, tools=tools)
        runner = Runner(
            agent=orchestrator,
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
            app_name="GitDocuRunnerTask",
        )

        initial_state = State({
            "repo_path": repo_clone_path,
            "output_dir": output_dir_job,
            "use_obsidian_format": use_obsidian,
            "verbose_logging": True
        })

        # Run the ADK process
        final_event = loop.run_until_complete(runner.run(initial_state=initial_state))
        final_state = final_event.state if hasattr(final_event, 'state') else State({})

        # Extract summary from final state
        plan = final_state.get('documentation_plan', [])
        summary_status = final_state.get('summary_status', 'Not run or status unavailable')
        success_count = sum(1 for item in plan if item.get('status') == 'done')
        fail_count = sum(1 for item in plan if item.get('status') == 'failed')

        status_details = f"Processed {len(plan)} files. {success_count} succeeded, {fail_count} failed. Summary: {summary_status}"
        final_state_summary = {
             "documentation_plan": plan, # Note: Plan might be large
             "summary_status": summary_status
        }
        logger.info(f"Job {job_id}: ADK process completed successfully.")
        task_status = "SUCCESS"

    except Exception as e:
        original_exception = e # Store exception
        logger.error(f"Job {job_id}: ADK process failed: {e}", exc_info=True)
        status_details = f"Error during ADK process: {str(e)}"
        task_status = "FAILURE"
        error_info = {
            'status': 'Failed',
            'details': status_details,
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }

    finally:
        # Update Job History Record using the new context manager approach
        db_status = "Completed" if task_status == "SUCCESS" else "Failed"
        try:
            update_job_history(
                job_id=job_id,
                status=db_status,
                details=status_details,
                final_state_summary=final_state_summary if task_status == "SUCCESS" else None,
                error_info=error_info # Pass full error_info, traceback removal happens inside
            )
        except Exception as db_update_err:
             # Log failure to update history, but don't let it prevent cleanup/final task state
             logger.error(f"Job {job_id}: CRITICAL - Failed to update job history in finally block: {db_update_err}", exc_info=True)

        # Clean up the cloned repository directory
        try:
            if repo_clone_path and os.path.isdir(repo_clone_path):
                 logger.info(f"Job {job_id}: Cleaning up temporary directory {repo_clone_path}")
                 shutil.rmtree(repo_clone_path)
        except Exception as cleanup_err:
            logger.error(f"Job {job_id}: Failed to cleanup temporary directory {repo_clone_path}: {cleanup_err}", exc_info=True)

        # Close the event loop
        loop.close()

        # Return Result for Celery (if SUCCESS) or Raise (if FAILURE)
        if task_status == "SUCCESS":
             return {
                 'status': 'Completed',
                 'details': status_details,
                 'final_state_summary': final_state_summary
             }
        else:
             # Raise the original exception to mark Celery task as failed
             if original_exception:
                 raise original_exception
             else:
                 # Should not happen if task_status is FAILURE, but as fallback:
                 raise RuntimeError(f"Task {job_id} failed with status '{db_status}' but original exception context was lost.") 
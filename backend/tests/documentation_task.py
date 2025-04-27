import logging
import os
import pathlib
import uuid
import tempfile
import shutil
import asyncio
import git # Requires GitPython
from typing import Any, Dict, Optional

# Setup Python path for imports if running script directly from backend/
import sys
# Add project root and src directory to path
project_root = pathlib.Path(__file__).resolve().parent.parent 
sys.path.insert(0, str(project_root)) 
sys.path.insert(0, str(project_root / 'src'))

# Import necessary application components AFTER adjusting path
try:
    # from src.tasks.documentation_task import run_adk_documentation_task # KEEP COMMENTED
    from src.app.container import Container # Container might be needed indirectly or for setup
    from src.app.config import config # Load configuration (reads .env)
    from src.app.logging_setup import setup_logging
    from src.app.constants import JobStatus
    # We need these for type hints and resolving
    from google.adk.runners import Runner 
    from src.persistence.repository import JobHistoryRepository
    # Import the CORE logic function, not the celery task
    from src.tasks.documentation_task import _execute_adk_flow # <-- UNCOMMENT THIS
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print("Ensure you are running this script from the 'backend' directory or have the project structure setup correctly.")
    sys.exit(1)

# --- REMOVED Mock Celery Task --- 

# --- Main Test Execution ---
async def main(): # Added async def main()
    # --- Configuration ---
    TEST_REPO_URL = "https://github.com/google/generative-ai-docs.git" # Example repo
    USE_OBSIDIAN = False
    LOG_LEVEL = logging.INFO

    # --- Setup ---
    # NOTE: setup_logging is called outside main now, in the if __name__ block
    logger = logging.getLogger(__name__)
    
    # Verify GOOGLE_API_KEY is set (crucial for ADK)
    if not config.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not set in environment or .env file. ADK runner will fail.")
        # Cannot sys.exit(1) from async func directly without more complex handling
        # Return a failure status instead
        return {"final_status": JobStatus.FAILED.value, "details": "Missing GOOGLE_API_KEY", "error_info": {"error_type": "ConfigurationError"}}
    else:
        # Mask the key in logs if needed, but confirm it's loaded
        logger.info("GOOGLE_API_KEY loaded successfully.")

    # Create a base temporary directory for this test run
    base_temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="gitdocu_test_"))
    clone_dir = base_temp_dir / "repo_clone"
    output_dir = base_temp_dir / "output"
    output_dir.mkdir()

    job_id = str(uuid.uuid4())
    result = None

    logger.info(f"Starting test for job_id: {job_id}")
    logger.info(f"Temporary directories created:")
    logger.info(f"  Base: {base_temp_dir}")
    logger.info(f"  Clone: {clone_dir}")
    logger.info(f"  Output: {output_dir}")

    container = None
    runner: Optional[Runner] = None
    repo: Optional[JobHistoryRepository] = None
    session_service: Optional[Any] = None # Explicitly define session_service

    try:
        # 1. Resolve Dependencies from Container
        logger.info("Resolving dependencies from container...")
        container = Container()
        runner = container.adk_runner()
        repo = container.job_history_repo()
        session_service = container.session_service() # Resolve session service
        logger.info("Dependencies resolved.")

        # 2. Create ADK Session (Added Step)
        user_id = config.ADK_USER_ID if hasattr(config, 'ADK_USER_ID') else "gitdocu_user_default"
        logger.info(f"Creating ADK session {job_id} for user {user_id}...")
        try:
            # create_session is likely async based on previous error
            # Pass app_name from the resolved runner instance
            session_service.create_session(user_id=user_id, session_id=job_id, app_name=runner.app_name)
            logger.info(f"ADK session {job_id} created.")
        except AttributeError:
             logger.error("session_service does not have create_session method or it's not async, or runner is missing app_name.")
             raise # Re-raise critical error
        except Exception as session_err:
            logger.error(f"Failed to create ADK session: {session_err}", exc_info=True)
            raise # Re-raise to stop the test

        # 3. Create Initial DB Record (optional but good practice for testing repo)
        try:
            logger.info("Creating initial DB record for test...")
            repo.add_initial(job_id=job_id, repo_url=TEST_REPO_URL)
            logger.info("Initial DB record created.")
        except Exception as db_init_err:
             logger.warning(f"Could not create initial DB record (continuing test): {db_init_err}")

        # 4. Clone the repository
        logger.info(f"Cloning repository {TEST_REPO_URL} into {clone_dir}...")
        git.Repo.clone_from(TEST_REPO_URL, str(clone_dir), depth=1)
        logger.info("Repository cloned successfully.")

        # 5. Execute the CORE async function directly
        logger.info("Executing _execute_adk_flow...")
        
        # Define a simple progress printer (optional)
        def print_progress(state: str, meta: dict):
             print(f"[Test Progress] State: {state}, Meta: {meta}")

        # Use await directly now since we are in an async function
        # No need for asyncio.run() here
        result = await _execute_adk_flow( # Changed asyncio.run to await
            job_id=job_id,
            repo_clone_path=str(clone_dir),
            output_dir_job=str(output_dir),
            use_obsidian=USE_OBSIDIAN,
            runner=runner, # Pass resolved runner
            repo=repo,     # Pass resolved repo
            update_progress_callback=print_progress # Pass optional progress printer
        )
        logger.info("Core function execution finished.")
        print("\n--- Core Function Result ---")
        print(result)
        print("-----------------------------")

    except Exception as e:
        logger.error(f"An error occurred during the test: {e}", exc_info=True)
        if result is None:
             result = {"final_status": JobStatus.FAILED.value, "details": f"Test script error: {str(e)}", "error_info": {"error_type": type(e).__name__}}

    finally:
        # 6. Cleanup temporary directories
        logger.info(f"Cleaning up temporary directory: {base_temp_dir}")
        try:
            # Use run_in_executor for blocking I/O in async context if needed
            # For simplicity here, we call it directly, but beware if it blocks significantly
            shutil.rmtree(base_temp_dir)
            logger.info("Cleanup successful.")
        except OSError as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Return the result dict for exit code handling
    return result

if __name__ == "__main__":
    # Setup logging once before running main async function
    setup_logging(log_level=logging.INFO)
    
    # Run the async main function
    final_result = asyncio.run(main()) 

    # Exit with appropriate code based on task outcome
    # Logger won't be configured here if main fails early, so use print
    if final_result and final_result.get("final_status") == JobStatus.COMPLETED.value:
        print("INFO: Test completed successfully.")
        sys.exit(0)
    else:
        print(f"ERROR: Test failed. Result: {final_result}")
        sys.exit(1) 
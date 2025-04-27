# Backend Refactoring Implementation Plan

**Goal:** Restructure the `backend/src/` directory for improved modularity, clarity, separation of concerns, and extensibility, based on the revised architecture plan.

**Branch:** `refactor/backend-improvements` (already created and checked out)

---

## Phase 0: Prerequisites

1.  **Dependencies:** Ensure necessary dependencies for planned features are added (some might already be present):
    *   `pydantic[dotenv]` (for configuration)
    *   `python-json-logger` (for structured logging)
    *   `pytest`, `pytest-mock`, `requests` (for testing - can be added later in Phase 5)
    *   **Action:** Check `backend/pyproject.toml`; add if missing and run `poetry lock --no-update && poetry install`.

---

## Phase 1: Create New Directory Structure

Create the target directory layout within `backend/src/`.

*   **Action:** Execute the following commands from the `backend/src/` directory:
    ```bash
    mkdir app
    mkdir app/api
    mkdir adk
    mkdir adk/agents
    mkdir adk/agents/orchestrators
    mkdir adk/agents/sub_agents
    mkdir adk/tools
    mkdir adk/services
    mkdir adk/prompts
    mkdir tasks
    mkdir core
    touch app/__init__.py
    touch app/api/__init__.py
    touch adk/__init__.py
    touch adk/agents/__init__.py
    touch adk/agents/orchestrators/__init__.py
    touch adk/agents/sub_agents/__init__.py
    touch adk/tools/__init__.py
    touch adk/services/__init__.py
    touch adk/prompts/__init__.py
    touch tasks/__init__.py
    touch core/__init__.py
    ```

---

## Phase 2: Move Existing Files

Move current files into their new locations according to the target architecture.

*   **Action:** Execute the following commands from the `backend/src/` directory:
    ```bash
    # Move Celery App definition
    mv celery_app.py app/celery_app.py

    # Move Models
    mv git_repo_documentor/models.py app/models.py

    # Move ADK Services
    # Ensure adk/services exists first if mv doesn't create parent
    mv git_repo_documentor/services/* adk/services/
    rmdir git_repo_documentor/services

    # Move ADK Agents (will be further refined later)
    # Ensure adk/agents exists first
    mv git_repo_documentor/agents/* adk/agents/
    rmdir git_repo_documentor/agents

    # Move ADK Tools (will be further refined later)
    # Ensure adk/tools exists first
    mv git_repo_documentor/tools/* adk/tools/
    rmdir git_repo_documentor/tools

    # Move ADK Prompts
    # Ensure adk/prompts exists first
    mv git_repo_documentor/prompts/* adk/prompts/
    rmdir git_repo_documentor/prompts

    # Move Server logic (temporarily place in app/ for splitting)
    mv git_repo_documentor/server.py app/server_temp.py # Rename temporarily

    # Move Task logic (temporarily place for splitting)
    mv git_repo_documentor/tasks.py tasks/tasks_temp.py # Rename temporarily

    # Remove old main package directory and any leftover helpers inside it
    rm -rf git_repo_documentor
    ```

---

## Phase 3: Create New Files & Extract Logic

Create the remaining new files and populate them by extracting logic from the moved `app/server_temp.py` and `tasks/tasks_temp.py` files.

1.  **Configuration (`app/config.py`)**
    *   **Action:** Create `app/config.py`. Define the Pydantic `Settings(BaseSettings)` class as planned, loading from `.env` and environment variables. Include fields for `SQLALCHEMY_DATABASE_URI`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CLONE_BASE_DIR`, `OUTPUT_BASE_DIR`, `GOOGLE_API_KEY` (and potentially others like ADK service types, GCP project/location).
2.  **Logging (`app/logging_setup.py`)**
    *   **Action:** Create `app/logging_setup.py`. Define a function `setup_logging()` that configures the root logger to use `python_json_logger.JsonFormatter`.
3.  **Exceptions (`exceptions.py`)**
    *   **Action:** Create `src/exceptions.py`. Define initial custom exception classes (e.g., `ConfigurationError(Exception)`, `CloningError(Exception)`, `AdkOrchestrationError(Exception)`, `HistoryUpdateError(Exception)`).
4.  **Core Git Utils (`core/git_utils.py`)**
    *   **Action:** Create `core/git_utils.py`. Move the Git cloning logic (using the `gitpython` library) from `app/server_temp.py` into a function `clone_repo(repo_url: str, target_dir: str) -> None`. This function should raise `CloningError` on failure.
5.  **API Blueprints (`app/api/`)**
    *   **Action:** Create `app/api/history_api.py` and `app/api/jobs_api.py`.
    *   Define Flask Blueprints in each (`history_bp = Blueprint(...)`, `jobs_bp = Blueprint(...)`).
    *   Move the route definitions (`@app.route(...)`) for `/history` and `/status` from `app/server_temp.py` to `history_api.py`, adapting them to use the blueprint (`@history_bp.route(...)`). Import necessary functions/models (like `JobHistory`, `AsyncResult`).
    *   Move the route definition for `/document` from `app/server_temp.py` to `jobs_api.py`, adapting it (`@jobs_bp.route(...)`). Update it to:
        *   Import `clone_repo` from `src.core.git_utils`.
        *   Import an enqueue function (to be created in `tasks`) like `enqueue_documentation_job` from `src.tasks.documentation_task`.
        *   Call `clone_repo`.
        *   Call `enqueue_documentation_job`.
        *   Remove the direct Git cloning and Celery `apply_async` logic.
6.  **App Initialization (`app/__init__.py`)**
    *   **Action:** Create the actual `app/__init__.py`.
    *   Add code to:
        *   Import `Flask`.
        *   Import `settings` from `.config`.
        *   Import `db` from `.models`.
        *   Import `setup_logging` from `.logging_setup`.
        *   Import blueprints (`history_bp`, `jobs_bp`) from `.api`.
        *   Create the Flask `app = Flask(...)`.
        *   Load configuration: `app.config.from_object(settings)`.
        *   Setup logging: `setup_logging()`.
        *   Initialize DB: `db.init_app(app)`.
        *   Register blueprints: `app.register_blueprint(history_bp)`, `app.register_blueprint(jobs_bp)`.
        *   Include the `with app.app_context(): db.create_all()` logic.
7.  **ADK Orchestration Logic (`adk/agents/orchestrators/git_documentation.py`)**
    *   **Action:** Create `adk/agents/orchestrators/git_documentation.py`.
    *   Define a function `run_git_documentation_flow(repo_clone_path: str, output_dir_job: str, use_obsidian: bool, settings: Settings) -> Tuple[str, Optional[dict], Optional[dict]]`.
    *   Move the core ADK logic (service factory setup, agent/tool definitions *within the run*, runner setup, `runner.run` call, result processing) from `tasks/tasks_temp.py` into this function.
    *   This function should handle internal errors using custom exceptions (`AdkOrchestrationError`).
    *   Return values indicating success/failure status, details string, final state summary (on success), and error info dict (on failure).
8.  **Task DB Update Logic (`tasks/db_update.py`)**
    *   **Action:** Create `tasks/db_update.py`.
    *   Move the `get_db_session` context manager and `update_job_history` function from `tasks/tasks_temp.py` into this file. Ensure it imports necessary modules (`os`, `logging`, `json`, `datetime`, `SQLAlchemy`, `src.app.models.JobHistory`, `src.app.config`).
9.  **Celery Task Definition (`tasks/documentation_task.py`)**
    *   **Action:** Create `tasks/documentation_task.py`.
    *   Define the Celery task `@celery_app.task(bind=True) def run_adk_documentation_task(...)`.
    *   Import `settings` from `src.app.config`.
    *   Import `run_git_documentation_flow` from `src.adk.agents.orchestrators.git_documentation`.
    *   Import `update_job_history` from `.db_update`.
    *   Import `clone_repo`'s cleanup logic or refactor cleanup (e.g., `shutil.rmtree`).
    *   The task's main logic should now:
        *   Call `run_git_documentation_flow`, passing necessary arguments.
        *   Use a `try...except...finally` block around the call.
        *   In `finally`, call `update_job_history` with the status/details/error info returned by `run_git_documentation_flow`.
        *   In `finally`, perform cleanup (e.g., removing `repo_clone_path`).
        *   Return the success result or re-raise the exception caught from `run_git_documentation_flow`.
    *   Define the helper function `enqueue_documentation_job(job_id: str, repo_url: str, clone_dir: str, output_dir_job: str, obsidianFormat: bool)`:
        *   Imports `db`, `JobHistory` from `src.app.models`.
        *   Imports `celery_app` from `src.app.celery_app`.
        *   Imports `run_adk_documentation_task` task object.
        *   Creates the initial `JobHistory` record in the DB.
        *   Calls `run_adk_documentation_task.apply_async(...)`.
        *   Handles potential DB/Celery submission errors.
10. **Refine ADK Components (`adk/`)**
    *   **Action:** Create `adk/agents/definitions.py` and `adk/tools/definitions.py`.
    *   Move agent *class definitions* from `adk/agents/orchestrator.py` (and any sub-agent files created) to `adk/agents/definitions.py`.
    *   Move tool *function/class definitions* from `adk/tools/__init__.py` to `adk/tools/definitions.py`.
    *   Update `adk/tools/__init__.py` to import definitions from `.definitions` and perform the actual tool *instantiation* (e.g., `read_directory_tool = FunctionTool(...)`). Export instances.
    *   Update `adk/agents/__init__.py` to import/export agent definitions.
11. **Cleanup Temporary Files**
    *   **Action:** Delete `app/server_temp.py` and `tasks/tasks_temp.py`.

---

## Phase 4: Update Imports

This is a critical phase overlapping with Phase 3.

*   **Action:** Go through every `.py` file in `src/app/`, `src/adk/`, `src/tasks/`, `src/core/`, `src/exceptions.py`.
*   Review all `import` statements.
*   Update them according to the new file locations:
    *   Use relative imports (`.`, `..`) for imports *within* the same top-level package (`app`, `adk`, `tasks`, `core`). Example: `from .models import db` inside `app/api/history_api.py`.
    *   Use absolute imports starting from `src` for imports *between* the top-level packages. Example: `from src.app.config import settings` inside `tasks/documentation_task.py`, or `from src.core.git_utils import clone_repo` inside `app/api/jobs_api.py`.
*   **Verification:** Use a tool or manually check for `ImportError` or `NameError`. Python's `-m` execution might require careful handling of the `PYTHONPATH` or running from the `backend` directory.

---

## Phase 5: Integration & Verification

1.  **Initial Checks:** Attempt basic imports in a Python interpreter or run simple scripts to catch immediate `ImportError`.
2.  **Run Flask Server:** Execute `poetry run python -m src.app` (or adjust command based on how `app.py` is structured, possibly need a `run.py` or use `flask run`). Fix any import or runtime errors.
3.  **Run Celery Worker:** Execute `poetry run celery -A src.app.celery_app worker --loglevel=info` (adjust `-A` path). Fix any errors.
4.  **Basic Test:** Use `curl` or a simple client to POST to `/document`, then check `/status` and `/history`. Verify the basic flow works and logs appear correctly formatted.

--- 
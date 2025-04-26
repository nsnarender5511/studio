# Backend Refactoring & Architectural Improvement Plan (Post Initial Refactor)

**Date:** 2025-04-27

**Goal:** Address architectural weaknesses and code quality issues identified after the initial backend restructuring, focusing on improving decoupling, configuration management, ADK structure, and overall maintainability based on Roaster feedback.

**Context:** This plan follows the completion of `backend_refactor_plan.md`. The backend services (Flask, Celery) are assumed to be running with placeholder ADK agents, and the basic API flow is functional but reveals underlying structural issues.

**Legend:**
*   `[ ]` - Checklist item

---

## Phase 1: Foundational Cleanup & ADK Restructuring

**Goal:** Clean up the ADK module structure as originally intended (Plan 3.10) and eliminate magic strings for better maintainability.

### Step 1.1: Refactor ADK Structure (Implement Original Plan Item 3.10)
   - **Goal:** Centralize ADK agent/tool definitions, separate definition from instantiation, improve ADK module organization.
   - **Actions:**
      1.  `[x]` **Create Definition Files:**
          *   Create `backend/src/adk/agents/definitions.py`.
          *   Create `backend/src/adk/tools/definitions.py`.
      2.  `[x]` **Move Agent Class Definitions:**
          *   Move `PlaceholderAgent` class definition from `backend/src/adk/agents/orchestrator.py` to `backend/src/adk/agents/definitions.py`.
          *   Move `OrchestratorAgent` class definition from `backend/src/adk/agents/orchestrator.py` to `backend/src/adk/agents/definitions.py` (or its own file like `backend/src/adk/agents/orchestrator_agent.py` if preferred).
      3.  `[x]` **List Existing Tool Files:** (To ensure all are moved)
          *   Run: `ls backend/src/adk/tools` (Identify files like `file_system.py`, `code_parser.py`, etc., excluding `__init__.py`, `definitions.py`, `__pycache__/`).
      4.  `[x]` **Move Tool Function/Class Definitions:**
          *   For *each* tool file identified above (e.g., `file_system.py`), move the core Python function(s) or class(es) it defines into `backend/src/adk/tools/definitions.py`.
          *   Example (Conceptual for `file_system.py`):
              ```python
              # backend/src/adk/tools/definitions.py
              import os
              import logging # Add if needed by tool funcs
              # ... other tool function imports ...

              logger = logging.getLogger(__name__) # Add logger if needed

              # --- File System Tool Functions ---
              def read_directory(path: str) -> str:
                  # ... implementation from file_system.py ...

              def read_file(path: str) -> str:
                  # ... implementation from file_system.py ...

              # ... other tool functions ...
              ```
      5.  `[x]` **Update Tool Instantiation (`adk/tools/__init__.py`):**
          *   Modify `backend/src/adk/tools/__init__.py` to:
              *   Import the tool *functions* from `.definitions`.
              *   Perform the `FunctionTool` instantiation for each tool.
              *   Export *only* the instantiated tool objects (e.g., `read_directory_tool`).
          *   Example Snippet (`backend/src/adk/tools/__init__.py`):
              ```python
              from google.adk.tools import FunctionTool
              import logging # If needed
              # Import functions from the new definitions file
              from .definitions import read_directory, read_file # ... import others

              # Instantiate tools
              read_directory_tool = FunctionTool(fn=read_directory, description="Reads directory contents.")
              read_file_tool = FunctionTool(fn=read_file, description="Reads file content.")
              # ... instantiate other tools ...

              # Export only the instances
              __all__ = [
                  "read_directory_tool",
                  "read_file_tool",
                  # ... export other tool instances ...
              ]
              ```
      6.  `[x]` **Delete Old Tool Definition Files:**
          *   After confirming functions are moved and tools instantiated correctly, delete the original tool definition files (e.g., `rm backend/src/adk/tools/file_system.py`, `rm backend/src/adk/tools/code_parser.py`, etc.).
      7.  `[x]` **Update Agent Instantiation (`adk/agents/__init__.py`):**
          *   Modify `backend/src/adk/agents/__init__.py` to:
              *   Import agent *classes* (e.g., `PlaceholderAgent`) from `.definitions`.
              *   Instantiate the placeholder agents here (or potentially in a factory).
              *   Export the agent *instances* (e.g., `file_identification_agent`).
          *   Example Snippet (`backend/src/adk/agents/__init__.py`):
              ```python
              # Import agent classes
              from .definitions import PlaceholderAgent # , OrchestratorAgent, etc.

              # Instantiate placeholder agents
              file_identification_agent = PlaceholderAgent(name="FileIdentificationAgent")
              structure_designer_agent = PlaceholderAgent(name="StructureDesignerAgent")
              # ... instantiate all others ...

              # Export instances
              __all__ = [
                  "file_identification_agent",
                  "structure_designer_agent",
                  # ... export others ...
                  # Optionally export classes too if needed elsewhere: "PlaceholderAgent", "OrchestratorAgent"
              ]
              ```
      8.  `[x]` **Update Orchestrator Imports (`git_documentation.py`):**
          *   Modify `backend/src/adk/agents/orchestrators/git_documentation.py`:
              *   Change agent imports from `from ..orchestrator import ...` to `from src.adk.agents import file_identification_agent, ...` (importing instances from the package init).
              *   Ensure `OrchestratorAgent` class is imported correctly (e.g., `from src.adk.agents.definitions import OrchestratorAgent`).
              *   Ensure tool imports are correct: `from src.adk.tools import read_directory_tool, ...`.
      9.  `[x]` **Cleanup `adk/agents/orchestrator.py`:**
          *   Remove the placeholder agent instantiations and the `__all__` export list from this file. If only the `OrchestratorAgent` definition remains, consider moving it (Step 1.1.2) and deleting this file.
   - **Verification:** Run `make run-backend` and `make run-celery`. Submit a test job. Check for import errors or runtime errors related to agent/tool instantiation or usage. Ensure the placeholder flow still completes.

### Step 1.2: Eliminate Magic Strings
   - **Goal:** Replace hardcoded strings for statuses, stages, keys, etc., with constants or Enums.
   - **Actions:**
      1.  `[x]` **Create Constants File:**
          *   Create `backend/src/app/constants.py`.
      2.  `[x]` **Define Constants/Enums:**
          *   Add definitions for common strings. Start with critical ones.
          *   Example (`backend/src/app/constants.py`):
              ```python
              from enum import Enum

              class JobStatus(str, Enum):
                  PENDING = "PENDING"
                  STARTED = "STARTED"
                  PROGRESS = "PROGRESS"
                  COMPLETED = "Completed" # Note: Check consistency, API used 'Completed', maybe use SUCCESS internally?
                  FAILED = "Failed"
                  # Add other statuses if used

              class AdkStages(str, Enum):
                  SERVICE_CREATION = "service_creation"
                  AGENT_TOOL_SETUP = "agent_tool_setup"
                  RUNNER_CREATION = "runner_creation"
                  INITIAL_STATE_CREATION = "initial_state_creation"
                  ADK_RUNNER_EXECUTION = "adk_runner_execution"
                  RESULT_PROCESSING = "result_processing"
                  # Add other stages

              class AgentKeys(str, Enum):
                  FILE_IDENTIFICATION = "file_identification"
                  STRUCTURE_DESIGNER = "structure_designer"
                  CODE_PARSER = "code_parser"
                  CODE_INTERPRETER = "code_interpreter"
                  DEPENDENCY_ANALYZER = "dependency_analyzer"
                  TESTING_ANALYZER = "testing_analyzer"
                  FEATURE_EXTRACTOR = "feature_extractor"
                  CONTENT_GENERATOR = "content_generator"
                  VERIFIER = "verifier"
                  VISUALIZER = "visualizer"
                  MD_FORMATTER = "md_formatter"
                  OBSIDIAN_WRITER = "obsidian_writer"
                  SUMMARIZER = "summarizer"
                  FACT_CHECKER = "fact_checker"
                  SELF_REFLECTION = "self_reflection"
                  CODE_EXECUTION_VERIFIER = "code_execution_verifier"
                  # Add keys for all agents used
              ```
      3.  `[x]` **Update Usage (Example Files):**
          *   Modify `backend/src/tasks/db_update.py`: Import `JobStatus` and use e.g., `job_record.status = JobStatus.FAILED`.
          *   Modify `backend/src/app/api/history_api.py`: Import `JobStatus` and use e.g., `if job_record.status == JobStatus.FAILED:`. Check comparisons `job_record.status in ['PENDING', 'STARTED']`.
          *   Modify `backend/src/adk/agents/orchestrators/git_documentation.py`: Import `AdkStages`, `AgentKeys`, `JobStatus`. Use e.g., `current_stage = AdkStages.AGENT_TOOL_SETUP`, `AgentKeys.FILE_IDENTIFICATION: file_id_agent_instance`, `status = JobStatus.COMPLETED`, check status in `error_info`.
          *   Modify `backend/src/tasks/documentation_task.py`: Import `JobStatus`. Use e.g., `history_entry = JobHistory(..., status=JobStatus.PENDING)`. Check `db_status` assignment.
      4.  `[x]` **Review Other Files:** Check other files in `app`, `tasks`, `adk` for hardcoded strings that should be constants.
   - **Verification:** Run `make run-backend` / `make run-celery`. Submit job. Check status reporting, logs, and ensure no errors due to incorrect constant usage. Code review for consistency.

---

## Phase 2: Consolidate ADK Execution Logic

### Step 2.1: Simplify Celery Task Execution
   - **Goal:** Reduce indirection by moving the core ADK orchestration logic directly into the Celery task.
   - **Actions:**
      1.  `[x]` **Copy Logic:** Copy the *entire body* of the `async def run_git_documentation_flow(...)` function from `backend/src/adk/agents/orchestrators/git_documentation.py`.
      2.  `[x]` **Paste into Celery Task:** Paste this copied logic into the `run_adk_documentation_task(...)` function in `backend/src/tasks/documentation_task.py`, replacing the existing `try...except...finally` block that *calls* `run_git_documentation_flow`.
      3.  `[x]` **Adapt Logic:**
          *   Ensure necessary imports (ADK Runner, State, services, agents, tools, settings, exceptions, constants, asyncio, logging, etc.) are present at the top of `documentation_task.py`. Use absolute paths (`src.adk.agents`, `src.adk.tools`, `src.app.config`, `src.app.constants` etc.).
          *   Remove the `loop.run_until_complete(...)` call, as Celery tasks can directly `await` async functions/methods.
          *   The `job_id` is available as `self.request.id`. Use this variable directly where `job_id` parameter was used.
          *   Ensure the `try...except...finally` block structure for error handling and history/cleanup updates is preserved correctly around the core ADK logic copied from `run_git_documentation_flow`.
          *   Make sure the final return value or exception propagation aligns with Celery task requirements.
      4.  `[x]` **Remove Original Function:** Delete the `async def run_git_documentation_flow(...)` function from `backend/src/adk/agents/orchestrators/git_documentation.py` (or the whole file if empty).
      5.  `[x]` **Remove Import:** Delete the import for `run_git_documentation_flow` from `backend/src/tasks/documentation_task.py`.
   - **Verification:** Run `make run-celery`. Submit a test job. Check Celery logs for correct execution trace (service creation, agent setup, runner execution, results processing all happening within the task). Check final job status via API.

---

## Phase 3: Architectural Refinements (Consideration & Potential Implementation)

**Goal:** Improve decoupling and configuration management for better long-term scalability.

### Step 3.1: Refine Configuration Structure (Optional but Recommended)
   - **Goal:** Make configuration more modular.
   - **Actions:**
      1.  `[x]` **Define Nested Settings:** In `backend/src/app/config.py`:
          *   Define classes like `DatabaseSettings(BaseModel)`, `CelerySettings(BaseModel)`, `AdkSettings(BaseModel)`, etc., containing relevant fields.
          *   Modify the main `Settings(BaseSettings)` class to compose these: e.g., `db: DatabaseSettings = DatabaseSettings()`, `celery: CelerySettings = CelerySettings()`.
      2.  `[x]` **Update Settings Access:** Modify code currently accessing `settings.SOME_VAR` to use the nested structure, e.g., `settings.celery.CELERY_BROKER_URL` in `celery_app.py`, `settings.adk.GCP_PROJECT_ID` in `memory_service.py`.
   - **Verification:** Run `make run-backend` / `make run-celery`. Check logs for successful configuration loading. Test job submission.

### Step 3.2: Introduce Dependency Injection (Detailed Consideration)
   - **Goal:** Reduce direct imports between layers (`tasks` importing `adk` logic/services, `adk` importing `app.config`) to improve testability and reduce coupling.
   - **Why DI?** Direct imports create tight coupling. If `adk.agents` changes its structure, `tasks` might break. If `app.config` changes, `adk` might break. Testing becomes harder as components cannot be easily replaced with mocks.
   - **Strategy Options:**
      1.  **Manual Injection (Constructor/Method Injection):**
          *   **How:** Instantiate core services (like ADK `Runner`, configuration objects, DB session factories/managers) near the application entry points (e.g., `app/__init__.py` for Flask context, potentially a setup phase for Celery workers).
          *   Pass these instances explicitly to the objects/functions that need them.
          *   **Example (Celery Task):** Modify `tasks.documentation_task.run_adk_documentation_task` to *accept* pre-configured `runner` and `settings` (or `adk_settings`) objects as arguments, instead of importing `settings` and creating the `runner` inside the task. The Celery `apply_async` call in `app/api/jobs_api.py` would need to pass these (potentially serialized or retrieved via a shared context if simple passing isn't feasible).
          *   **Example (ADK Services):** Modify `adk.services.factory.create_service_factory` and `adk.services.memory_service.get_memory_service` to accept the relevant configuration (`AdkSettings` if Step 3.1 is done) as an argument instead of importing `src.app.config.settings`.
          *   **Pros:** Explicit dependencies, no extra libraries.
          *   **Cons:** Can lead to verbose constructors/function calls ("prop drilling"); manual wiring can be tedious.
      2.  **DI Framework (`python-dependency-injector`):**
          *   **How:** Define a DI container (e.g., in `app/container.py` or similar). Declare providers for configuration (`Settings`, `DatabaseSettings`, `AdkSettings`), ADK services (`Runner`, specific service instances), DB session managers, etc. Use `@inject` decorators or container lookups within classes/functions (e.g., API endpoints, Celery tasks) to get dependencies.
          *   **Example (Celery Task):**
              ```python
              # app/container.py
              from dependency_injector import containers, providers
              from .config import Settings
              from src.adk.runners import Runner # Assuming Runner is defined
              # ... other imports

              class Container(containers.DeclarativeContainer):
                  config = providers.Singleton(Settings)
                  # Provider for ADK Runner (example, needs details)
                  adk_runner = providers.Factory(
                      Runner,
                      agent=..., # Agent provider/instance
                      session_service=..., # Service providers
                      artifact_service=...,
                      memory_service=...,
                      app_name="GitDocuRunnerFlow"
                  )
                  # ... other providers ...

              # tasks/documentation_task.py
              from dependency_injector.wiring import inject, Provide
              from src.app.container import Container

              @celery_app.task(bind=True)
              @inject
              def run_adk_documentation_task(self, repo_clone_path: str, ..., runner: Runner = Provide[Container.adk_runner], config: Settings = Provide[Container.config]):
                  job_id = self.request.id
                  # Use injected runner and config directly
                  # No need to import settings or create runner inside
                  # ... rest of task logic using runner and config.adk ...
              ```
          *   **Pros:** Centralized dependency management, cleaner code using injection, facilitates testing via provider overrides.
          *   **Cons:** Adds a library dependency, learning curve for the framework.
   - **Decision Path:** Evaluate the team's familiarity with DI and the anticipated complexity. For moderate complexity, manual injection might suffice initially. For larger or evolving systems, a framework offers better long-term management.
   - **Action (If Proceeding):**
      1.  `[x]` Choose Strategy (Manual or Framework).
      2.  `[x]` Implement container/manual wiring for key services (Config, ADK Runner/Services, DB Session Manager/Repository).
      3.  `[x]` Refactor consumers (Celery tasks, ADK services, API endpoints) to receive dependencies via injection/arguments instead of direct imports.
   - **Verification:** Code review focusing on reduced imports between layers. Unit/Integration tests demonstrating successful injection and component interaction. Assess improvement in test setup complexity (easier mocking).

### Step 3.3: Re-evaluate DB Session Management (Post DI / Consolidation)
   - **Goal:** Ensure DB session management is efficient, safe, and aligns with the chosen architecture (DI or consolidated task logic).
   - **Context:** Currently uses `tasks/db_update.py` with a `get_db_session` context manager for operations outside Flask request context (in Celery tasks, API endpoint task enqueue pre-commit).
   - **Potential Simplification:**
      *   **If Task Logic Consolidated (Step 2.1):** The `update_job_history` function could potentially move directly into `documentation_task.py` if not used elsewhere. The `get_db_session` might still be needed within the task if multiple DB interactions occur that aren't part of the main Flask app context.
      *   **If DI Introduced (Step 3.2):**
          *   **Session Scope Management:** A DI framework might offer better ways to manage session scope, potentially replacing `get_db_session`. For example, injecting a session factory or a request-scoped/task-scoped session provider.
          *   **Repository Pattern:** Introduce a Repository pattern (e.g., `JobHistoryRepository`) responsible for all `JobHistory` CRUD operations. Inject this repository into tasks/API endpoints instead of directly using `db.session` or `get_db_session`. The repository itself would handle session management internally (potentially obtaining the session via DI).
   - **Action:**
      1.  `[x]` After completing Phase 2 (Task Consolidation) and deciding on/implementing Phase 3.2 (DI), review `tasks/db_update.py` and its callers (`documentation_task.py`, `jobs_api.py`).
      2.  `[x]` If using DI, investigate framework capabilities for session management or implement a Repository pattern for `JobHistory`.
      3.  `[x]` Refactor DB interaction points to use the new session management approach or Repository.
      4.  `[x]` Potentially remove `tasks/db_update.py` if its functionality is fully absorbed elsewhere.
   - **Verification:** Code review for simplified DB interactions. Unit tests for Repositories (if used). Integration tests confirming DB updates still occur correctly during job lifecycle.

---

## Diagrams (Textual)

**Current Coupling (Simplified - Roaster's View):**

```
+----------+      Imports      +-----------+      Imports      +---------+
|  app/api |------------------>| tasks/    |------------------>| adk/    |
| (Flask)  |<------------------| (Celery)  |<------------------| (Agents)|
+----------+      Config       +-----------+      Config       +---------+
     |              Imports?         ^               | Imports?
     |                               |               v
     +-----------> app/config <------+-----------> core/
     |              Imports?         |
     +-----------> app/models <-------+
```

**Target Coupling (Simplified - With DI/Refactoring):**

```
+----------+   (HTTP)   +-----------+   (Broker)   +---------+
|  Frontend| ---------> |  app/api  | -----------> | tasks/  |
+----------+            +-----------+              +---------+
                          |       ^                  |       ^
  Config Subset Inject -->|       | DB Models        |       | ADK Service/Runner Inject
                          v       |                  v       | Config Subset Inject
+----------+         + app/      |             + adk/       |
| app/config| ------> | (App Ctx) | ----------> | (Services) |
+----------+         +-----------+             +------------+
  |  ^                  |       ^                  |      ^
  |  | DB Config        |       | Core Utils Inject|      | Core Utils Inject
  |  +----------------> db      |------------------+      |
  |                                                        |
  +-------------------------------------------------------> core/
```
*(Note: DI = Dependency Injection)*

--- 
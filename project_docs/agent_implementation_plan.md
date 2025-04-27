# GitDocu ADK Agent Implementation Plan

**Version:** 1.0
**Date:** 2025-04-27

**Goal:** To implement the full suite of ADK agents defined in `project_docs/blueprint.md` for the GitDocu project in a phased, incremental manner. The core orchestration logic resides within the `run_adk_documentation_task` Celery task in `backend/src/tasks/documentation_task.py`.

**Assumptions:**
*   The backend refactoring plan (`backend_refactor_plan.md`) has been largely completed, establishing the project structure (`src/app`, `src/adk`, `src/tasks`, `src/core`).
*   ADK agents and tools structure follows Plan 3.10 from `refactoring_improvement_plan.md` (definitions separated from instantiation).
*   Placeholder agents (like `PlaceholderAgent`) are currently used in `src/adk/agents/__init__.py` and called by the logic in `src/tasks/documentation_task.py`.
*   Constants for agent keys, stages, and statuses are defined in `src/app/constants.py`.
*   The ADK `Runner` is correctly configured and invoked within `run_adk_documentation_task`.
*   The mechanism for passing initial parameters (`repo_clone_path`, `output_dir_job`, `use_obsidian`) into the `InvocationContext` state for the orchestration flow is functional (this might require adjusting the previous fix in `documentation_task.py` that passed `new_message=dict()`).

---

## Phase 0: Setup & Baseline Verification

**Objective:** Ensure the foundation is stable, constants are defined, initial state is passed correctly, and the current placeholder flow runs without fundamental errors (like the previous `NotImplementedError`).

**Tasks:**
1.  **Verify Constants:** Ensure `src/app/constants.py` contains `Enum` definitions for `JobStatus`, `AdkStages` (including all stages planned below), and `AgentKeys` (listing all agents from the blueprint).
2.  **Verify Placeholders:** Confirm that `src/adk/agents/__init__.py` instantiates and exports `PlaceholderAgent` instances for *all* agents listed in `AgentKeys`.
3.  **Verify Initial State:**
    *   **Action:** Modify the `runner.run_async(...)` call within `src/tasks/documentation_task.py`. Instead of `new_message=dict()`, pass the required initial state.
    *   **Example:**
        ```python
        # Inside run_adk_documentation_task in documentation_task.py
        initial_state_data = {
            "repo_path": repo_clone_path,
            "output_dir": output_dir_job,
            "use_obsidian_format": use_obsidian,
            "verbose_logging": True # Or based on config
        }
        # ... inside the try block ...
        async for event in runner.run_async(
            user_id=user_id,
            session_id=job_id,
            # Pass initial state here, maybe as structured message part or directly if runner supports it
            # Option 1 (If Runner/Agent expects structured message):
            # new_message=[{'role': 'user', 'parts': [initial_state_data]}],
            # Option 2 (If Runner/Agent expects simple dict):
            new_message=initial_state_data,
            run_config=RunConfig() # Potentially add config here too
        ):
            # ... rest of loop ...
        ```
    *   **Confirmation:** Check if the `OrchestratorAgent` logic (or the initial steps in `documentation_task.py`) can access these values from `ctx.state`. Adjust the `run_async` call signature/parameters as needed based on ADK documentation for passing initial state.
4.  **Run Baseline Test:** Execute `poetry run python tests/documentation_task.py | cat`.
    *   **Expected Outcome:** The test should complete (likely 'FAILED' functionally, as placeholders do nothing useful) but *without* structural errors like `NotImplementedError` or errors related to finding placeholder agents/tools. Logs should show the orchestration logic attempting to call the placeholder agents.

---

## Phase 1: Implement MVP Agents (Core Documentation Flow)

**Objective:** Replace the core placeholder agents with basic `LlmAgent` implementations to achieve an end-to-end flow generating a simple Markdown document for each planned file.

**Key Agents/Tools:**
*   Agents: `FileIdentificationAgent`, `StructureDesignerAgent`, `CodeParserAgent`, `CodeInterpreterAgent`, `DocContentAgent`, `MarkdownFormatterAgent`.
*   Tools: `read_directory_tool`, `read_file_tool`, `code_parser_tool`, `write_file_tool`, `ensure_directory_exists_tool`.

**Implementation Steps:**
1.  **Tool Verification:** Ensure the required tools (`read_directory`, `read_file`, `write_file`, `ensure_directory`, `parse_code`) are defined in `adk/tools/definitions.py` and instantiated in `adk/tools/__init__.py`.
2.  **Define MVP Agents:**
    *   In `adk/agents/definitions.py`, create basic `LlmAgent` classes for the 6 agents listed above.
    *   Use `google.adk.models.Gemini` (e.g., `gemini-1.5-flash` for speed/cost or `gemini-1.5-pro` for capability).
    *   Write initial prompts (`instruction`) based on the descriptions in `blueprint.md`.
    *   Assign the necessary tools (`tools=[...]`) to each agent.
    *   Define the expected `output_key` for each agent (e.g., `"identified_files"`, `"documentation_plan"`).
3.  **Instantiate MVP Agents:** In `adk/agents/__init__.py`, replace the `PlaceholderAgent` instantiations for these 6 agents with instantiations of the new `LlmAgent` classes.
4.  **Update Orchestration Logic (`documentation_task.py`):**
    *   Ensure the main orchestration flow within `run_adk_documentation_task` correctly calls these agents in sequence using `ctx.find_sub_agent(AgentKeys.AGENT_NAME.value)`.
    *   Implement the loop to iterate through the `documentation_plan`.
    *   Pass state correctly between agents via `ctx.actions.state_delta`.
    *   Handle basic success/failure status checking from sub-agents (expecting them to put `"status": JobStatus.COMPLETED.value` or `"status": JobStatus.FAILED.value` in their state delta).
    *   Call `MarkdownFormatterAgent` at the end of the loop for each file.

**Verification:**
*   Run `poetry run python tests/documentation_task.py | cat`.
*   **Expected Outcome:** The test should complete with `final_status: COMPLETED`. Simple Markdown files should be generated in the temporary output directory, corresponding to the `documentation_plan`. Content will be basic, based on initial prompts. Check logs for agent execution flow.

---

## Phase 2: Enhance Analysis & Content

**Objective:** Implement the remaining analysis agents to gather more context about the code, and update the content generation agent to use this richer information.

**Key Agents/Tools:**
*   Agents: `DependencyAnalyzerAgent`, `TestingAnalyzerAgent`, `FeatureExtractorAgent`. (Implement these as `LlmAgent`s). Update `DocContentAgent`.
*   Tools: `dependency_analyzer_tool`, `web_search_tool` (if needed by Dependency Analyzer). Ensure these tools are implemented/instantiated.

**Implementation Steps:**
1.  **Tool Verification:** Ensure `dependency_analyzer_tool` and `web_search_tool` are implemented and available.
2.  **Define Analysis Agents:** In `adk/agents/definitions.py`, create `LlmAgent` classes for `DependencyAnalyzerAgent`, `TestingAnalyzerAgent`, `FeatureExtractorAgent` with appropriate prompts, tools, and output keys (`"dependency_analysis"`, `"testing_analysis"`, `"feature_analysis"`).
3.  **Instantiate Analysis Agents:** In `adk/agents/__init__.py`, replace placeholders with new `LlmAgent` instances.
4.  **Update Orchestration Logic (`documentation_task.py`):**
    *   Inside the file processing loop, *after* `CodeInterpreterAgent` and *before* `DocContentAgent`, add calls to the new analysis agents (`DependencyAnalyzerAgent`, `TestingAnalyzerAgent`, `FeatureExtractorAgent`).
    *   Accumulate their results (`dependency_analysis`, `testing_analysis`, `feature_analysis`) in the `ctx.actions.state_delta`.
5.  **Update `DocContentAgent`:**
    *   Modify the `DocContentAgent` class in `adk/agents/definitions.py`.
    *   Update its `instruction` (prompt) to explicitly request incorporating the information from `dependency_analysis`, `testing_analysis`, and `feature_analysis` alongside `code_interpretation` when generating the `draft_content`.

**Verification:**
*   Run `poetry run python tests/documentation_task.py | cat`.
*   **Expected Outcome:** Test completes successfully. Generated Markdown files should be more detailed, referencing dependencies, tests, and key features identified by the new analysis agents. Compare output with Phase 1.

---

## Phase 3: Add Verification & Refinement (Optional but Recommended)

**Objective:** Introduce a verification step to check the generated content against the source code and analysis, potentially enabling a refinement loop.

**Key Agents/Tools:**
*   Agents: `VerifierAgent`.
*   Tools: Relies primarily on `read_file_tool` and potentially access to previous analysis state.

**Implementation Steps:**
1.  **Define `VerifierAgent`:** In `adk/agents/definitions.py`, create `VerifierAgent(LlmAgent)`.
    *   `instruction`: Prompt it to compare `draft_content` with `parsed_code`, `code_interpretation`, etc., checking for accuracy, consistency, and completeness. Instruct it to output a JSON like `{"verification_status": "passed|failed", "reason": "...", "suggestions": "..."}`.
    *   `output_key`: `"verification_result"`.
2.  **Instantiate `VerifierAgent`:** In `adk/agents/__init__.py`, replace placeholder.
3.  **Update Orchestration Logic (`documentation_task.py`):**
    *   Inside the file processing loop, *after* `DocContentAgent`, call `VerifierAgent`.
    *   Check the `"verification_status"` from the `verification_result`.
    *   **Option A (Simple Fail):** If status is 'failed', raise an exception for that file or log a warning.
    *   **Option B (Refinement Loop - More Complex):** If status is 'failed', potentially call `DocContentAgent` *again*, passing the `verification_result["suggestions"]` as additional input to refine the content. Add a loop limit (e.g., max 2 attempts per file). This requires more complex state management. *Start with Option A*.

**Verification:**
*   Run `poetry run python tests/documentation_task.py | cat`.
*   **Expected Outcome:** Test completes. Logs should show the `VerifierAgent` running. If verification fails (Option A), the overall job might fail or logs should indicate per-file verification failures. If Option B is implemented, logs should show refinement attempts.

---

## Phase 4: Add Visualization & Summarization

**Objective:** Generate visual diagrams and a repository-level summary document.

**Key Agents/Tools:**
*   Agents: `VisualizationAgent`, `SummarizerAgent`.
*   Tools: `visualization_tool`, `ensure_directory_exists_tool`, `write_file_tool`, `read_file_tool`.

**Implementation Steps:**
1.  **Tool Verification:** Ensure `visualization_tool` is implemented (using `graphviz` or similar) and available.
2.  **Define Agents:** In `adk/agents/definitions.py`, create `VisualizationAgent(LlmAgent)` and `SummarizerAgent(LlmAgent)`.
    *   `VisualizationAgent`: Prompt it to generate diagrams (based on accumulated analysis like dependencies) and use the `visualization_tool` to save them. Needs `ensure_directory_exists_tool`. Output key: `"visualization_result"`.
    *   `SummarizerAgent`: Prompt it to read *all* successfully generated Markdown files (requires paths from the `documentation_plan` state), synthesize a summary, create a TOC, and write an `SUMMARY.md` or `README.md` file. Needs `read_file_tool`, `write_file_tool`. Output key: `"summary_status"`.
3.  **Instantiate Agents:** In `adk/agents/__init__.py`, replace placeholders.
4.  **Update Orchestration Logic (`documentation_task.py`):**
    *   **Visualization:** Inside the file processing loop (or perhaps after certain analysis steps like dependency analysis), conditionally call `VisualizationAgent`. Store paths to generated visualizations.
    *   **Summarization:** *After* the main file processing loop completes successfully, call `SummarizerAgent`. Pass the final state of the `documentation_plan` (so it knows which files were generated successfully).

**Verification:**
*   Run `poetry run python tests/documentation_task.py | cat`.
*   **Expected Outcome:** Test completes successfully. Check the output directory for image files (visualizations) and a summary Markdown file.

---

## Phase 5: Implement Obsidian Output

**Objective:** Add support for generating documentation specifically formatted for Obsidian, including wikilinks.

**Key Agents/Tools:**
*   Agents: `ObsidianWriterAgent`.
*   Tools: `format_obsidian_links_tool`.

**Implementation Steps:**
1.  **Tool Implementation:** Implement the `format_obsidian_links_tool` function in `adk/tools/definitions.py` (using regex or similar to convert potential links based on filenames in the plan) and instantiate it in `adk/tools/__init__.py`.
2.  **Define `ObsidianWriterAgent`:** In `adk/agents/definitions.py`, create `ObsidianWriterAgent(LlmAgent)`.
    *   `instruction`: Prompt it to format `draft_content` for Obsidian, explicitly mentioning the use of `format_obsidian_links_tool`.
    *   `tools`: [`ensure_directory_exists_tool`, `write_file_tool`, `format_obsidian_links_tool`].
    *   `output_key`: `"obsidian_writing_status"`.
3.  **Instantiate `ObsidianWriterAgent`:** In `adk/agents/__init__.py`, replace placeholder.
4.  **Update Orchestration Logic (`documentation_task.py`):**
    *   In the "Formatting & Writing" step (3d) of the file processing loop, add conditional logic:
        ```python
        if use_obsidian:
            formatter_agent_key = AgentKeys.OBSIDIAN_WRITER.value
        else:
            formatter_agent_key = AgentKeys.MD_FORMATTER.value
        formatter_agent = ctx.find_sub_agent(formatter_agent_key)
        # ... rest of the call ...
        ```

**Verification:**
*   Modify `tests/documentation_task.py` to set `USE_OBSIDIAN = True`.
*   Run `poetry run python tests/documentation_task.py | cat`.
*   **Expected Outcome:** Test completes successfully. Generated files should be in the output directory. Inspect the content for Obsidian-style wikilinks (`[[Link]]`) where appropriate.

---

## Phase 6: Advanced Features (Optional - Beyond Core Scope)

**Objective:** Implement remaining specialized agents from the blueprint if project scope expands.

**Key Agents/Tools:**
*   Agents: `FactCheckerAgent`, `SelfReflectionAgent`, `CodeExecutionVerifierAgent`, `KnowledgeGraphManagerAgent`, `MemoryManagerAgent`.
*   Tools: Corresponding tools (`fact_verification.py`, `knowledge_graph.py`, `memory_tools.py`, `code_executor.py`).

**Implementation Steps:**
*   Define and implement these agents and tools based on their descriptions in `blueprint.md`.
*   Integrate them into the orchestration flow within `documentation_task.py` at appropriate points (e.g., fact checking after content generation, memory updates throughout). This will likely require significant additions to the orchestration logic and state management.

**Verification:** Requires specific test cases designed for these advanced features.

---

## Phase 7: Comprehensive Testing & Optimization

**Objective:** Ensure robustness, reliability, and acceptable performance.

**Tasks:**
1.  **Unit Testing:** Write `pytest` unit tests for individual tool functions and potentially for agent prompt generation logic. Mock external dependencies (LLM calls, file system).
2.  **Integration Testing:** Expand `tests/documentation_task.py` or create new integration tests using different repositories (smaller, larger, different languages) and edge cases (empty repos, repos with non-code files).
3.  **Error Handling Review:** Test failure scenarios (e.g., invalid repo URL, LLM API errors, file system errors) and ensure graceful failure reporting.
4.  **Performance Analysis:** Identify bottlenecks (e.g., slow LLM calls, inefficient file processing). Consider parallelizing file processing steps (using `asyncio.gather` or ADK's `ParallelAgent` if refactoring orchestration). Optimize prompts for efficiency. Add caching where appropriate (e.g., for web search results).
5.  **Dependency Review:** Ensure all necessary external libraries (like `GitPython`, `astroid`, `graphviz`, language parsers) are correctly listed in `pyproject.toml`.

--- 
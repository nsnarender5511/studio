# ADK Agent Class Definitions
import logging
from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent # Added SequentialAgent
from google.adk.sessions import State
from google.adk.tools import BaseTool, FunctionTool # Added FunctionTool
from pydantic import Field, BaseModel # Removed BaseModel import if only used for schema
from typing import Dict, List, Any, Optional # Added imports
from google.adk.models import Gemini
from src.app.constants import AgentKeys, JobStatus, AdkStages # Import constants
from google.adk.runners import InvocationContext # Event removed, imported below
from google.adk.events import Event, EventActions # Import Event and EventActions
import time # Import time for timestamps

logger = logging.getLogger(__name__) 

# --- Common Model Definition (Example) ---
# Use Flash for potentially faster/cheaper MVP, Pro for complex tasks later
# common_model = Gemini(model="gemini-1.5-flash-latest") 
common_model = Gemini(model="gemini-1.5-pro-latest")

# --- Placeholder Agent Definition ---
class PlaceholderAgent(BaseAgent):
    """A generic placeholder agent."""
    name: str = "PlaceholderAgent"
    description: str = "A generic placeholder agent."

    async def run(self, state: State, artifact_service):
        logger.info(f"Running PlaceholderAgent: {self.name}")
        state.update({f"{self.name}_run": True})
        return state

    async def _run_async_impl(self, ctx: InvocationContext):
        agent_name = ctx.agent_name or self.name
        logger.info(f"PlaceholderAgent '{agent_name}' executing...")
        # Simulate some work and return a standard completion status
        yield ctx.new_event(state_delta={
            "status": JobStatus.COMPLETED.value,
            f"{agent_name}_result": "placeholder output"
        })

# --- Orchestrator Agent Definition ---
class OrchestratorAgent(BaseAgent):
    """Manages the overall documentation workflow."""
    name: str = "Orchestrator"
    description: str = "Manages the overall documentation workflow."

    # Sub-agents and tools are expected to be passed during instantiation
    sub_agents: Dict[str, BaseAgent] = Field(...)
    tools: List[BaseTool] = Field(default_factory=list)

    # Override model_post_init to handle sub_agent dictionary correctly
    def model_post_init(self, __context: Any) -> None:
        # 1. REMOVED: Explicit setting of parent_agent.
        # We will let the superclass method handle it now, hoping it iterates the list correctly.
        # if isinstance(self.sub_agents, dict):
        #     for sub_agent in self.sub_agents.values():
        #         ...
        
        # 2. Temporarily replace self.sub_agents with its values for the super call
        original_sub_agents = self.sub_agents
        temp_sub_agents_list = []
        if isinstance(original_sub_agents, dict):
             temp_sub_agents_list = list(original_sub_agents.values())
        elif isinstance(original_sub_agents, list): # Handle list case just in case
             temp_sub_agents_list = original_sub_agents
        
        try:
            self.sub_agents = temp_sub_agents_list # Temporarily assign list
            # 3. Call super().model_post_init - it should now iterate over the list and set parent_agent
            super().model_post_init(__context)
        finally:
            # 4. Restore the original sub_agents dictionary (important for later use)
            self.sub_agents = original_sub_agents

    async def _run_async_impl(self, ctx: InvocationContext):
        job_id = ctx.session.id 
        current_stage = AdkStages.ORCHESTRATION_START.value 
        logger.info(f"Job {job_id}: OrchestratorAgent starting execution.")
        
        # Construct and yield initial stage event
        initial_actions = EventActions(state_delta={"current_stage": current_stage})
        initial_event = Event(
            id=Event.new_id(),
            invocation_id=ctx.invocation_id,
            author=self.name,
            timestamp=time.time(),
            actions=initial_actions
        )
        yield initial_event

        # Accumulate state changes locally before yielding
        current_state_delta = {}

        try:
            # --- Retrieve Initial State --- 
            # Use placeholders as initial state passing is still unresolved
            repo_path_placeholder = "/path/to/placeholder/repo" 
            output_dir_placeholder = "/path/to/placeholder/output"
            use_obsidian = False 
            logger.warning(f"Job {job_id}: Using placeholder paths due to state passing issue.")

            # Store placeholders in state delta for sub-agents
            current_state_delta.update({
                "repo_path": repo_path_placeholder, 
                "output_dir": output_dir_placeholder, 
                "use_obsidian_format": use_obsidian, 
                "verbose_logging": True
            })
            # Yield state update event
            update_actions = EventActions(state_delta=current_state_delta.copy())
            update_event = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=update_actions
            )
            yield update_event

            # --- Stage 1: File Identification --- 
            current_stage = AdkStages.FILE_IDENTIFICATION.value 
            logger.info(f"Job {job_id}: Entering stage: {current_stage}")
            current_state_delta["current_stage"] = current_stage
            current_state_delta["status_detail"] = f"Identifying files..."
            # Yield stage start event
            stage_start_actions = EventActions(state_delta=current_state_delta.copy())
            stage_start_event = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=stage_start_actions
            )
            yield stage_start_event

            file_id_agent = ctx.find_sub_agent(AgentKeys.FILE_IDENTIFICATION.value)
            if not file_id_agent: raise RuntimeError(f"Sub-agent not found: {AgentKeys.FILE_IDENTIFICATION.value}")

            file_id_results = {} 
            async for event in file_id_agent.run_async(ctx):
                 if event.actions and event.actions.state_delta:
                      file_id_results.update(event.actions.state_delta)
            
            current_state_delta.update(file_id_results) # Update local delta tracker

            if file_id_results.get("status") != JobStatus.COMPLETED.value:
                 raise Exception(f"{AgentKeys.FILE_IDENTIFICATION.value} failed: {file_id_results.get('error_details', 'Unknown error')}")

            identified_files = file_id_results.get("identified_files") 
            if not identified_files:
                 raise Exception(f"{AgentKeys.FILE_IDENTIFICATION.value} found no files.")
            logger.info(f"Job {job_id}: Identified {len(identified_files)} files.")
            # Yield stage completion with accumulated state
            stage_complete_actions = EventActions(state_delta=current_state_delta.copy())
            stage_complete_event = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=stage_complete_actions
            )
            yield stage_complete_event

            # --- Stage 2: Structure Design --- 
            current_stage = AdkStages.STRUCTURE_DESIGN.value 
            logger.info(f"Job {job_id}: Entering stage: {current_stage}")
            current_state_delta["current_stage"] = current_stage
            current_state_delta["status_detail"] = f"Designing structure..."
            # Yield stage start event
            stage_start_actions_2 = EventActions(state_delta=current_state_delta.copy())
            stage_start_event_2 = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=stage_start_actions_2
            )
            yield stage_start_event_2
            
            designer_agent = ctx.find_sub_agent(AgentKeys.STRUCTURE_DESIGNER.value)
            if not designer_agent: raise RuntimeError(f"Sub-agent not found: {AgentKeys.STRUCTURE_DESIGNER.value}")

            designer_results = {} 
            async for event in designer_agent.run_async(ctx):
                 if event.actions and event.actions.state_delta:
                      designer_results.update(event.actions.state_delta)
            
            current_state_delta.update(designer_results)

            if designer_results.get("status") != JobStatus.COMPLETED.value:
                 raise Exception(f"{AgentKeys.STRUCTURE_DESIGNER.value} failed: {designer_results.get('error_details', 'Unknown error')}")

            documentation_plan = designer_results.get("documentation_plan")
            if not documentation_plan:
                raise Exception(f"{AgentKeys.STRUCTURE_DESIGNER.value} created an empty plan.")
            logger.info(f"Job {job_id}: Documentation plan created with {len(documentation_plan)} items.")
            # Yield stage completion with accumulated state
            stage_complete_actions_2 = EventActions(state_delta=current_state_delta.copy())
            stage_complete_event_2 = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=stage_complete_actions_2
            )
            yield stage_complete_event_2

            # --- Stage 3: Iterative Processing --- 
            processed_files_count = 0
            total_files = len(documentation_plan)
            current_plan_state = list(documentation_plan) # Mutable copy for status updates

            for idx, plan_item in enumerate(current_plan_state):
                source_file = plan_item.get("source_file")
                output_file = plan_item.get("output_file")
                if not source_file or not output_file:
                     logger.warning(f"Job {job_id}: Skipping invalid plan item {idx}: {plan_item}")
                     plan_item["status"] = "skipped" 
                     continue

                file_stage_prefix = f"Processing file {idx+1}/{total_files} ({source_file})"
                logger.info(f"Job {job_id}: {file_stage_prefix}")

                # Update state delta for this file iteration
                current_state_delta.update({
                    "current_file_path": source_file,
                    "current_output_path": output_file,
                    "parsed_code": None,
                    "code_interpretation": None,
                    "draft_content": None
                })
                # Yield file iteration start event
                file_iter_actions = EventActions(state_delta=current_state_delta.copy())
                file_iter_event = Event(
                    id=Event.new_id(),
                    invocation_id=ctx.invocation_id,
                    author=self.name,
                    timestamp=time.time(),
                    actions=file_iter_actions
                )
                yield file_iter_event

                try:
                    # --- 3a: Code Parsing --- 
                    current_stage = AdkStages.CODE_PARSING.value 
                    logger.debug(f"Job {job_id}: Stage: {current_stage} for {source_file}")
                    current_state_delta["current_stage"] = current_stage
                    current_state_delta["status_detail"] = f"{file_stage_prefix} - Parsing..."
                    # Yield sub-stage start event
                    sub_stage_actions_parse = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_event_parse = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_actions_parse
                    )
                    yield sub_stage_event_parse
                    
                    parser_agent = ctx.find_sub_agent(AgentKeys.CODE_PARSER.value)
                    if not parser_agent: raise RuntimeError(f"Sub-agent not found: {AgentKeys.CODE_PARSER.value}")
                    parser_results = {} 
                    async for event in parser_agent.run_async(ctx):
                        if event.actions and event.actions.state_delta:
                             parser_results.update(event.actions.state_delta)
                    current_state_delta.update(parser_results)
                    if parser_results.get("status") != JobStatus.COMPLETED.value:
                         raise Exception(f"{AgentKeys.CODE_PARSER.value} failed: {parser_results.get('error_details', 'Unknown error')}")
                    # Yield sub-stage completion event
                    sub_stage_complete_actions_parse = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_complete_event_parse = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_complete_actions_parse
                    )
                    yield sub_stage_complete_event_parse

                    # --- 3b: Code Interpretation --- 
                    current_stage = AdkStages.CODE_INTERPRETATION.value 
                    logger.debug(f"Job {job_id}: Stage: {current_stage} for {source_file}")
                    current_state_delta["current_stage"] = current_stage
                    current_state_delta["status_detail"] = f"{file_stage_prefix} - Interpreting..."
                    # Yield sub-stage start event
                    sub_stage_actions_interpret = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_event_interpret = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_actions_interpret
                    )
                    yield sub_stage_event_interpret
                    
                    interpreter_agent = ctx.find_sub_agent(AgentKeys.CODE_INTERPRETER.value)
                    if not interpreter_agent: raise RuntimeError(f"Sub-agent not found: {AgentKeys.CODE_INTERPRETER.value}")
                    interpreter_results = {} 
                    async for event in interpreter_agent.run_async(ctx):
                        if event.actions and event.actions.state_delta:
                             interpreter_results.update(event.actions.state_delta)
                    current_state_delta.update(interpreter_results)
                    if interpreter_results.get("status") != JobStatus.COMPLETED.value:
                         raise Exception(f"{AgentKeys.CODE_INTERPRETER.value} failed: {interpreter_results.get('error_details', 'Unknown error')}")
                    # Yield sub-stage completion event
                    sub_stage_complete_actions_interpret = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_complete_event_interpret = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_complete_actions_interpret
                    )
                    yield sub_stage_complete_event_interpret

                    # --- 3c: Content Generation --- 
                    current_stage = AdkStages.CONTENT_GENERATION.value 
                    logger.debug(f"Job {job_id}: Stage: {current_stage} for {source_file}")
                    current_state_delta["current_stage"] = current_stage
                    current_state_delta["status_detail"] = f"{file_stage_prefix} - Generating content..."
                    # Yield sub-stage start event
                    sub_stage_actions_content = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_event_content = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_actions_content
                    )
                    yield sub_stage_event_content
                    
                    content_agent = ctx.find_sub_agent(AgentKeys.CONTENT_GENERATOR.value)
                    if not content_agent: raise RuntimeError(f"Sub-agent not found: {AgentKeys.CONTENT_GENERATOR.value}")
                    content_results = {} 
                    async for event in content_agent.run_async(ctx):
                        if event.actions and event.actions.state_delta:
                             content_results.update(event.actions.state_delta)
                    current_state_delta.update(content_results)
                    if content_results.get("status") != JobStatus.COMPLETED.value:
                         raise Exception(f"{AgentKeys.CONTENT_GENERATOR.value} failed: {content_results.get('error_details', 'Unknown error')}")
                    # Yield sub-stage completion event
                    sub_stage_complete_actions_content = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_complete_event_content = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_complete_actions_content
                    )
                    yield sub_stage_complete_event_content

                    # --- 3d: Formatting & Writing --- 
                    current_stage = AdkStages.OUTPUT_FORMATTING.value 
                    logger.debug(f"Job {job_id}: Stage: {current_stage} for {source_file}")
                    current_state_delta["current_stage"] = current_stage
                    current_state_delta["status_detail"] = f"{file_stage_prefix} - Formatting/Writing..."
                    # Yield sub-stage start event
                    sub_stage_actions_format = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_event_format = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_actions_format
                    )
                    yield sub_stage_event_format
                    
                    formatter_agent_key = AgentKeys.OBSIDIAN_WRITER.value if use_obsidian else AgentKeys.MD_FORMATTER.value
                    formatter_agent = ctx.find_sub_agent(formatter_agent_key)
                    if not formatter_agent: raise RuntimeError(f"Sub-agent not found: {formatter_agent_key}")
                    
                    formatter_results = {} 
                    async for event in formatter_agent.run_async(ctx):
                        if event.actions and event.actions.state_delta:
                             formatter_results.update(event.actions.state_delta)
                    current_state_delta.update(formatter_results)
                    if formatter_results.get("status") != JobStatus.COMPLETED.value:
                         raise Exception(f"{formatter_agent_key} failed: {formatter_results.get('error_details', 'Unknown error')}")
                    # Yield sub-stage completion event
                    sub_stage_complete_actions_format = EventActions(state_delta=current_state_delta.copy())
                    sub_stage_complete_event_format = Event(
                        id=Event.new_id(),
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        timestamp=time.time(),
                        actions=sub_stage_complete_actions_format
                    )
                    yield sub_stage_complete_event_format
                    
                    # File processed successfully within the try block
                    plan_item["status"] = "completed"
                    processed_files_count += 1
                    logger.info(f"Job {job_id}: Successfully processed file {idx+1}/{total_files}: {source_file}")

                except Exception as file_proc_err:
                    # Log the error and mark the file as failed in the plan
                    error_detail = f"Error processing file {source_file}: {str(file_proc_err)}"
                    logger.error(f"Job {job_id}: {error_detail}", exc_info=True) # Include traceback
                    plan_item["status"] = "failed"
                    plan_item["error"] = error_detail
                    # Update overall state with the error detail for this specific file (optional but helpful)
                    current_state_delta.update({
                        f"error_file_{idx}": error_detail,
                        "status_detail": f"Error processing {source_file}. Continuing...",
                        "has_processing_errors": True # Flag that at least one error occurred
                    })
                    # Yield an event indicating the file error
                    file_error_actions = EventActions(state_delta=current_state_delta.copy())
                    file_error_event = Event(
                         id=Event.new_id(),
                         invocation_id=ctx.invocation_id,
                         author=self.name,
                         timestamp=time.time(),
                         message=f"Failed processing {source_file}",
                         actions=file_error_actions
                    )
                    yield file_error_event
                    # Continue to the next file in the loop
                    continue
                # END OF TRY...EXCEPT FOR SINGLE FILE
            # --- END OF FILE PROCESSING LOOP ---

            # --- Stage 4: Finalization ---
            # Check if any errors occurred during file processing
            if current_state_delta.get("has_processing_errors"):
                final_status = JobStatus.FAILED
                final_message = "Orchestration completed with errors during file processing."
                logger.warning(f"Job {job_id}: {final_message}")
                current_state_delta.update({
                    "orchestration_status": final_status.value,
                    "current_stage": AdkStages.ORCHESTRATION_COMPLETE.value, # Still technically complete
                    "status_detail": final_message,
                    "documentation_plan_results": current_plan_state # Final plan state with errors
                })
            else:
                final_status = JobStatus.COMPLETED
                final_message = f"Orchestration completed successfully. Processed {processed_files_count} files."
                logger.info(f"Job {job_id}: {final_message}")
                current_state_delta.update({
                    "orchestration_status": final_status.value,
                    "current_stage": AdkStages.ORCHESTRATION_COMPLETE.value,
                    "status_detail": final_message,
                    "documentation_plan_results": current_plan_state # Final plan state
                })

            # Yield final completion event (success or with errors)
            final_complete_actions = EventActions(state_delta=current_state_delta.copy())
            final_complete_event = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=final_complete_actions
            )
            yield final_complete_event

        except Exception as orch_err:
            # Catch any other unexpected errors during orchestration stages
            logger.error(f"Job {job_id}: Orchestration failed at stage {current_stage}: {orch_err}", exc_info=True)
            final_plan_state = current_state_delta.get("documentation_plan", []) # Get potentially partial plan
            # Ensure final state delta reflects the failure
            current_state_delta.update({
                "orchestration_status": JobStatus.FAILED.value,
                "current_stage": current_stage,
                "status_detail": f"Failed at stage {current_stage}: {orch_err}",
                "error_details": str(orch_err),
                "error_stage": current_stage,
                "error_type": type(orch_err).__name__,
                "documentation_plan": final_plan_state
            })
            # Yield final failure event
            final_fail_actions = EventActions(state_delta=current_state_delta.copy())
            final_fail_event = Event(
                id=Event.new_id(),
                invocation_id=ctx.invocation_id,
                author=self.name,
                timestamp=time.time(),
                actions=final_fail_actions
            )
            yield final_fail_event
        finally:
            logger.info(f"Job {job_id}: OrchestratorAgent finished execution.")

# ================================================
# Phase 1: MVP Agent Definitions
# ================================================

class FileIdentificationAgent(LlmAgent):
    """Identifies relevant source code files in a repository for documentation."""
    name: str = AgentKeys.FILE_IDENTIFICATION.value
    model: Gemini = common_model
    instruction: str = ( # Basic initial prompt
        "Analyze the repository structure provided via the 'read_directory' tool. "
        "Identify the primary source code files (e.g., .py, .js, .ts, .java, .go, .rb) suitable for documentation. "
        "Exclude common test directories (tests/, test/, __tests__), configuration files (.*rc, .config/, *.config, *.toml, *.yaml), build artifacts (dist/, build/, target/), "
        "dependency folders (node_modules/, venv/), and documentation files (.md, .rst) unless it's the root README.md. "
        "List the relative paths of the identified files from the repository root."
    )
    tools: list = ["read_directory"] # Tool instances imported in tools/__init__.py
    output_key: str = "identified_files" # Expected output structure: {"identified_files": ["path/to/file1.py", ...]}

class StructureDesignerAgent(LlmAgent):
    """Creates a plan for organizing the documentation based on identified files."""
    name: str = AgentKeys.STRUCTURE_DESIGNER.value
    model: Gemini = common_model
    instruction: str = (
        "Given a list of identified source files in the 'identified_files' state variable, "
        "create a structured documentation plan. For each source file, determine a logical output path "
        "for its corresponding Markdown documentation file within the 'output_dir' state variable. "
        "Mirror the source directory structure within the output directory. "
        "Output a JSON list where each item is an object with keys: 'source_file' (original relative path), "
        "'output_file' (new relative path for the .md file), and 'status' (set to 'pending')."
    )
    # No tools needed if identified_files and output_dir are in state
    output_key: str = "documentation_plan" # Expected output: {"documentation_plan": [{"source_file": ..., "output_file": ..., "status": "pending"}, ...]}

class CodeParserAgent(LlmAgent):
    """Parses a single code file to extract its structure."""
    name: str = AgentKeys.CODE_PARSER.value
    model: Gemini = common_model
    instruction: str = (
        "Parse the code file located at the path specified in the 'current_file_path' state variable. "
        "Use the 'parse_code' tool to perform the parsing. "
        "Return the structured data obtained from the tool."
    )
    tools: list = ["parse_code", "read_file_content"] # read_file might be needed by parse_code internally
    output_key: str = "parsed_code" # Expected output: {"parsed_code": {... structured data from tool ...}}

class CodeInterpreterAgent(LlmAgent):
    """Analyzes parsed code structure to generate a summary."""
    name: str = AgentKeys.CODE_INTERPRETER.value
    model: Gemini = common_model
    instruction: str = (
        "Analyze the parsed code structure provided in the 'parsed_code' state variable for the file path in 'current_file_path'. "
        "Provide a concise summary (1-3 sentences) of the file's primary purpose. "
        "Identify its main components (e.g., classes, functions, key logic blocks) and briefly describe their roles. "
        "Focus on the high-level functionality and design intent."
        # "You can use the 'read_file_content' tool if the parsed structure lacks necessary context."
    )
    # tools: list = ["read_file_content"] # Optional, enable if needed
    output_key: str = "code_interpretation" # Expected output: {"code_interpretation": "Summary text..."}

class DocContentAgent(LlmAgent):
    """Generates Markdown documentation content based on code analysis."""
    name: str = AgentKeys.CONTENT_GENERATOR.value
    model: Gemini = common_model
    # Phase 1: Basic prompt using only interpretation
    instruction: str = (
        "Generate Markdown documentation content for the file 'current_file_path'. "
        "Use the summary provided in the 'code_interpretation' state variable as the primary input. "
        "Expand on the summary, creating clear sections using Markdown headings. "
        "Include:\n"
        "- A brief overview section based on the interpretation.\n"
        "- Sections describing key functions or classes identified in the interpretation (if any), explaining their purpose.\n"
        "- Use Markdown formatting for readability (code blocks for names, lists, etc.)."
        # Phase 2 Enhancement: "Incorporate details from 'dependency_analysis', 'testing_analysis', and 'feature_analysis' state variables if available."
    )
    # No tools needed if analysis is in state
    output_key: str = "draft_content" # Expected output: {"draft_content": "Markdown content..."}

class MarkdownFormatterAgent(LlmAgent):
    """Formats and writes documentation content to a Markdown file."""
    name: str = AgentKeys.MD_FORMATTER.value
    model: Gemini = common_model # Might not need LLM if logic is simple, could be BaseAgent
    instruction: str = (
        "Take the Markdown content from the 'draft_content' state variable. "
        "Ensure basic Markdown formatting is correct (e.g., headings, lists, code blocks). "
        "Use the 'ensure_directory_exists' tool for the directory part of the 'current_output_path' state variable. "
        "Then, use the 'write_file_content' tool to save the final Markdown content to the full 'current_output_path'."
    )
    tools: list = ["ensure_directory_exists", "write_file_content"]
    # Output key might not be strictly needed if it just performs actions
    # Outputting status might be useful: {"formatting_status": "success"}
    output_key: str = "formatting_status"

# ================================================
# Phase 2+ Agent Definitions (Placeholders for now)
# ================================================

# Add definitions for DependencyAnalyzerAgent, TestingAnalyzerAgent, etc.
# when implementing those phases, replacing PlaceholderAgent instances. 
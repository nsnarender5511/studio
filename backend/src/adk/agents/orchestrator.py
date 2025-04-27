import logging
from google.adk.sessions import State
from google.adk.tools import BaseTool
from typing import Dict, List, Optional, Any

# --- Import Agent Classes from definitions ---
from .definitions import PlaceholderAgent, OrchestratorAgent

logger = logging.getLogger(__name__)

def create_orchestrator(config: Optional[Dict[str, Any]] = None) -> OrchestratorAgent:
    """Creates and configures the OrchestratorAgent, instantiating placeholders internally."""
    logger.info("Creating Orchestrator Agent")
    config = config or {}

    # --- Instantiate placeholder agents inside the creator function ---
    # This avoids the circular import with agents/__init__.py
    logger.debug("Creating placeholder agent instances in create_orchestrator")
    file_identification_agent = PlaceholderAgent(name="FileIdentificationAgent")
    structure_designer_agent = PlaceholderAgent(name="StructureDesignerAgent")
    code_parser_agent = PlaceholderAgent(name="CodeParserAgent")
    code_interpreter_agent = PlaceholderAgent(name="CodeInterpreterAgent")
    dependency_analyzer_agent = PlaceholderAgent(name="DependencyAnalyzerAgent")
    testing_analyzer_agent = PlaceholderAgent(name="TestingAnalyzerAgent")
    feature_extractor_agent = PlaceholderAgent(name="FeatureExtractorAgent")
    content_generator_agent = PlaceholderAgent(name="DocContentAgent")
    verifier_agent = PlaceholderAgent(name="VerifierAgent")
    visualizer_agent = PlaceholderAgent(name="VisualizationAgent")
    md_formatter_agent = PlaceholderAgent(name="MarkdownFormatterAgent")
    obsidian_writer_agent = PlaceholderAgent(name="ObsidianWriterAgent")
    summarizer_agent = PlaceholderAgent(name="SummarizerAgent")
    fact_checker_agent = PlaceholderAgent(name="FactCheckingAgent")
    self_reflection_agent = PlaceholderAgent(name="SelfReflectionAgent")
    code_execution_verifier_agent = PlaceholderAgent(name="CodeExecutionVerifierAgent")

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
        # TODO: Allow overriding/adding agents via config?
    }

    # TODO: Load tools based on config or requirements
    tools: List[BaseTool] = [] # Assuming tools are managed separately for now

    orchestrator = OrchestratorAgent(sub_agents=sub_agents, tools=tools)
    logger.info("Orchestrator Agent created with internally defined instances.")
    return orchestrator

# Optionally, add the run_orchestration function if needed,
# which might use create_orchestrator
async def run_orchestration(config: Dict[str, Any], initial_state: Optional[State] = None) -> State:
    """Creates an orchestrator and runs it with the given config and initial state."""
    logger.info("Running orchestration...")
    orchestrator = create_orchestrator(config)
    initial_state = initial_state or State({})
    initial_state.update(config.get("initial_state", {})) # Merge config state

    # Assuming artifact_service needs to be handled or passed
    # This might come from a higher-level context
    artifact_service = None # Placeholder for artifact service instance

    final_state = await orchestrator.run(initial_state, artifact_service)
    logger.info("Orchestration finished.")
    return final_state

__all__ = [
    "create_orchestrator",
    "run_orchestration",
    "OrchestratorAgent", # Re-exporting from definitions
    "PlaceholderAgent"  # Re-exporting from definitions
]

# Export agent definitions and potentially pre-configured instances
import logging

# --- Import Agent Classes from definitions --- 
from .definitions import (
    PlaceholderAgent, OrchestratorAgent, # Base/Placeholder
    FileIdentificationAgent, StructureDesignerAgent, CodeParserAgent, # MVP Agents Phase 1
    CodeInterpreterAgent, DocContentAgent, MarkdownFormatterAgent, # MVP Agents Phase 1
    # Add imports for Phase 2+ agents here when defined
    # DependencyAnalyzerAgent, TestingAnalyzerAgent, FeatureExtractorAgent, 
    # VerifierAgent, VisualizationAgent, SummarizerAgent, ObsidianWriterAgent 
)
from src.app.constants import AgentKeys # Import the keys

# --- Import Orchestration functions --- 
# Commenting out old orchestrator functions as logic moves to task/OrchestratorAgent
# from .orchestrator import create_orchestrator, run_orchestration 

logger = logging.getLogger(__name__)

# --- Instantiate Agents ---

# --- Phase 1 MVP Agents ---
file_identification_agent = FileIdentificationAgent() # Use default name from class
structure_designer_agent = StructureDesignerAgent()
code_parser_agent = CodeParserAgent()
code_interpreter_agent = CodeInterpreterAgent()
doc_content_agent = DocContentAgent()
markdown_formatter_agent = MarkdownFormatterAgent()

# --- Phase 2+ Agents (using Placeholders for now) ---
dependency_analyzer_agent = PlaceholderAgent(name=AgentKeys.DEPENDENCY_ANALYZER.value)
testing_analyzer_agent = PlaceholderAgent(name=AgentKeys.TESTING_ANALYZER.value)
feature_extractor_agent = PlaceholderAgent(name=AgentKeys.FEATURE_EXTRACTOR.value)
verifier_agent = PlaceholderAgent(name=AgentKeys.VERIFIER.value)
fact_checker_agent = PlaceholderAgent(name=AgentKeys.FACT_CHECKER.value)
self_reflection_agent = PlaceholderAgent(name=AgentKeys.SELF_REFLECTION.value)
code_execution_verifier_agent = PlaceholderAgent(name=AgentKeys.CODE_EXECUTION_VERIFIER.value)
visualizer_agent = PlaceholderAgent(name=AgentKeys.VISUALIZER.value)
obsidian_writer_agent = PlaceholderAgent(name=AgentKeys.OBSIDIAN_WRITER.value) # Keep placeholder until Phase 5
summarizer_agent = PlaceholderAgent(name=AgentKeys.SUMMARIZER.value) # Keep placeholder until Phase 4

# TODO: Instantiate KnowledgeGraphManagerAgent, MemoryManagerAgent when defined


# Control what `from src.adk.agents import *` imports
__all__ = [
    # Agent Classes (Exporting for potential direct use elsewhere)
    "PlaceholderAgent",
    "OrchestratorAgent",
    "FileIdentificationAgent", 
    "StructureDesignerAgent", 
    "CodeParserAgent",
    "CodeInterpreterAgent", 
    "DocContentAgent", 
    "MarkdownFormatterAgent",
    # Add Phase 2+ classes here when defined

    # Agent Instances (Exporting for use in orchestration logic via find_sub_agent)
    "file_identification_agent",
    "structure_designer_agent",
    "code_parser_agent",
    "code_interpreter_agent",
    "dependency_analyzer_agent", # Placeholder instance
    "testing_analyzer_agent",    # Placeholder instance
    "feature_extractor_agent",   # Placeholder instance
    "content_generator_agent",   # Renamed from doc_content_agent
    "verifier_agent",            # Placeholder instance
    "fact_checker_agent",        # Placeholder instance
    "self_reflection_agent",     # Placeholder instance
    "code_execution_verifier_agent", # Placeholder instance
    "visualizer_agent",          # Placeholder instance
    "md_formatter_agent",        # Renamed from markdown_formatter_agent
    "obsidian_writer_agent",     # Placeholder instance
    "summarizer_agent",          # Placeholder instance
    # Add KG/Memory agents here when instantiated
]

# Rename instances to match export list expectations if needed
content_generator_agent = doc_content_agent
md_formatter_agent = markdown_formatter_agent

# Deprecated Orchestration Functions - Commented out import above
# __all__.extend([
#     "create_orchestrator",
#     "run_orchestration",
# ])

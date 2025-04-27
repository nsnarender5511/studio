import logging
from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone
import json

# Import flattened config object and class
from .config import config, Config
# Import constants for agent keys
from .constants import AgentKeys
from src.adk.services.memory_service import get_memory_service # Import factory func
# Import ADK base types and implementations needed for providers
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.adk.artifacts import BaseArtifactService, InMemoryArtifactService
from google.adk.memory import BaseMemoryService
from google.adk.runners import Runner
# Fix: Import only BaseAgent from google.adk.agents
from google.adk.agents import BaseAgent # Removed OrchestratorAgent, PlaceholderAgent
from google.adk.tools import BaseTool # For tool list type hint

# Import specific tools and agents (or their factories if complex)
# This already imports our local definitions including OrchestratorAgent and PlaceholderAgent
from src.adk.agents import definitions as agent_defs # Keep definitions separate
# Import modules containing instances/lists
from src.adk import agents as agent_module
from src.adk import tools as tool_module

# Import Repository
from src.persistence.repository import JobHistoryRepository

logger = logging.getLogger(__name__)

# --- Factory function for Sub-Agents --- 
def get_sub_agents() -> dict[str, BaseAgent]:
    """Creates the dictionary of sub-agents using instances from agent_module."""
    logger.debug("Factory: Creating sub-agent dictionary from agent_module instances")
    # Use the agent instances directly imported/defined in agent_module
    # Ensure agent_module.__all__ correctly lists the instance variable names
    # Map AgentKeys.ENUM.value to the corresponding instance
    return {
        # Phase 1 MVP Agents
        AgentKeys.FILE_IDENTIFICATION.value: agent_module.file_identification_agent,
        AgentKeys.STRUCTURE_DESIGNER.value: agent_module.structure_designer_agent,
        AgentKeys.CODE_PARSER.value: agent_module.code_parser_agent,
        AgentKeys.CODE_INTERPRETER.value: agent_module.code_interpreter_agent,
        AgentKeys.CONTENT_GENERATOR.value: agent_module.content_generator_agent, # Using renamed instance
        AgentKeys.MD_FORMATTER.value: agent_module.md_formatter_agent,          # Using renamed instance

        # Phase 2+ Agents (using placeholders instantiated in agent_module)
        AgentKeys.DEPENDENCY_ANALYZER.value: agent_module.dependency_analyzer_agent,
        AgentKeys.TESTING_ANALYZER.value: agent_module.testing_analyzer_agent,
        AgentKeys.FEATURE_EXTRACTOR.value: agent_module.feature_extractor_agent,
        AgentKeys.VERIFIER.value: agent_module.verifier_agent,
        AgentKeys.VISUALIZER.value: agent_module.visualizer_agent,
        AgentKeys.OBSIDIAN_WRITER.value: agent_module.obsidian_writer_agent,
        AgentKeys.SUMMARIZER.value: agent_module.summarizer_agent,
        AgentKeys.FACT_CHECKER.value: agent_module.fact_checker_agent, # Placeholder
        AgentKeys.SELF_REFLECTION.value: agent_module.self_reflection_agent, # Placeholder
        AgentKeys.CODE_EXECUTION_VERIFIER.value: agent_module.code_execution_verifier_agent, # Placeholder
        
        # TODO: Add KG/Memory Manager Agents when implemented
    }

class Container(containers.DeclarativeContainer):
    # --- Configuration Provider --- 
    config: providers.Provider[Config] = providers.Object(config)

    # --- Database Providers --- 
    db_engine = providers.Singleton(create_engine, config.provided.SQLALCHEMY_DATABASE_URI)
    db_session_factory = providers.Singleton(sessionmaker, bind=db_engine, autocommit=False, autoflush=False)
    # Use ContextLocalSingleton for appropriate session scoping in web/task contexts
    db_session: providers.Provider[Session] = providers.ContextLocalSingleton(db_session_factory)
    # Repository for JobHistory access, depends on the session factory
    job_history_repo: providers.Provider[JobHistoryRepository] = providers.Factory(
        JobHistoryRepository, session_factory=db_session_factory # Pass factory
    )

    # --- ADK Service Providers --- 
    # Session Service Provider
    session_service: providers.Provider[BaseSessionService] = providers.Singleton(
        # Fix: Check config value, default to memory if not specified or unsupported
        lambda cfg: InMemorySessionService() if cfg.SESSION_SERVICE_TYPE.lower() != 'database' else InMemorySessionService(), # Placeholder: Add DB service if needed
        cfg=config # Pass whole config
    )
    # Artifact Service Provider
    artifact_service: providers.Provider[BaseArtifactService] = providers.Singleton(
        # Fix: Check config value, default to memory if not specified or unsupported
        lambda cfg: InMemoryArtifactService() if cfg.ARTIFACT_SERVICE_TYPE.lower() != 'database' else InMemoryArtifactService(), # Placeholder: Add DB service if needed
        cfg=config # Pass whole config
    )
    # Memory Service Provider
    memory_service: providers.Provider[BaseMemoryService] = providers.Singleton(
        get_memory_service,
        service_type=config.provided.MEMORY_SERVICE_TYPE,
        config_obj=config # Pass the whole flattened config object
    )

    # --- ADK Tool Providers --- 
    # Assumes tool_module.__all__ correctly lists the instantiated tool objects
    adk_tools: providers.Provider[list[BaseTool]] = providers.List(
         *[providers.Object(getattr(tool_module, tool_name)) for tool_name in tool_module.__all__] 
    )

    # --- ADK Agent Providers --- 
    # Dictionary of sub-agents provided by factory function
    sub_agents_dict = providers.Factory(get_sub_agents)

    # Orchestrator Agent Provider
    orchestrator_agent: providers.Provider[agent_defs.OrchestratorAgent] = providers.Factory(
        agent_defs.OrchestratorAgent,
        sub_agents=sub_agents_dict, # Reverted: Pass the dictionary provider again
        tools=adk_tools
    )

    # --- ADK Runner Provider --- 
    adk_runner: providers.Provider[Runner] = providers.Factory(
        Runner,
        agent=orchestrator_agent,
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=memory_service,
        app_name="GitDocuRunnerFlow_DI"
    ) 
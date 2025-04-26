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
    """Creates the dictionary of sub-agents required by the orchestrator."""
    logger.debug("Factory: Creating sub-agent dictionary")
    # Return a dictionary mapping agent names to instances
    return {
        "FileIdentificationAgent": agent_defs.PlaceholderAgent(name="FileIdentificationAgent"),
        "StructureDesignerAgent": agent_defs.PlaceholderAgent(name="StructureDesignerAgent"),
        "CodeParserAgent": agent_defs.PlaceholderAgent(name="CodeParserAgent"),
        "CodeInterpreterAgent": agent_defs.PlaceholderAgent(name="CodeInterpreterAgent"),
        "DependencyAnalyzerAgent": agent_defs.PlaceholderAgent(name="DependencyAnalyzerAgent"),
        "TestingAnalyzerAgent": agent_defs.PlaceholderAgent(name="TestingAnalyzerAgent"),
        "FeatureExtractorAgent": agent_defs.PlaceholderAgent(name="FeatureExtractorAgent"),
        "DocContentAgent": agent_defs.PlaceholderAgent(name="DocContentAgent"),
        "VerifierAgent": agent_defs.PlaceholderAgent(name="VerifierAgent"),
        "VisualizationAgent": agent_defs.PlaceholderAgent(name="VisualizationAgent"),
        "MarkdownFormatterAgent": agent_defs.PlaceholderAgent(name="MarkdownFormatterAgent"),
        "ObsidianWriterAgent": agent_defs.PlaceholderAgent(name="ObsidianWriterAgent"),
        "SummarizerAgent": agent_defs.PlaceholderAgent(name="SummarizerAgent"),
        "FactCheckingAgent": agent_defs.PlaceholderAgent(name="FactCheckingAgent"),
        "SelfReflectionAgent": agent_defs.PlaceholderAgent(name="SelfReflectionAgent"),
        "CodeExecutionVerifierAgent": agent_defs.PlaceholderAgent(name="CodeExecutionVerifierAgent"),
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
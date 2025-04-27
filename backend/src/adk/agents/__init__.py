# Export agent definitions and potentially pre-configured instances
import logging

# --- Import Agent Classes from definitions --- 
from .definitions import PlaceholderAgent, OrchestratorAgent

# --- Import Orchestration functions --- 
from .orchestrator import create_orchestrator, run_orchestration

logger = logging.getLogger(__name__)


# Control what `from .agents import *` does
__all__ = [
    # Agent Classes
    "PlaceholderAgent",
    "OrchestratorAgent",

    # Orchestration Functions
    "create_orchestrator",
    "run_orchestration",

]

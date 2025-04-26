import os
import logging

from google.adk.sessions import InMemorySessionService, BaseSessionService as SessionService
from google.adk.artifacts import InMemoryArtifactService, BaseArtifactService as ArtifactService
from google.adk.memory import InMemoryMemoryService, BaseMemoryService as MemoryService

# Import the memory service factory
from .memory_service import get_memory_service

logger = logging.getLogger(__name__)

def create_service_factory() -> tuple[SessionService, ArtifactService, MemoryService]:
    """Create appropriate ADK services based on environment configuration."""
    session_type = os.environ.get('SESSION_SERVICE_TYPE', 'memory').lower()
    artifact_type = os.environ.get('ARTIFACT_SERVICE_TYPE', 'memory').lower()
    memory_type = os.environ.get('MEMORY_SERVICE_TYPE', 'memory').lower()

    logger.info(f"Using ADK Services: Session='{session_type}', Artifact='{artifact_type}', Memory='{memory_type}'")

    # --- Session Service ---
    if session_type == 'memory':
        session_service = InMemorySessionService()
    # Add elif for other types (e.g., 'database') if implemented
    # elif session_type == 'database':
    #     session_service = DatabaseSessionService(...)
    else:
        logger.warning(f"Unsupported SESSION_SERVICE_TYPE '{session_type}', defaulting to 'memory'.")
        session_service = InMemorySessionService()

    # --- Artifact Service ---
    if artifact_type == 'memory':
        artifact_service = InMemoryArtifactService()
    # Add elif for other types (e.g., 'filesystem', 'gcs') if implemented
    # elif artifact_type == 'filesystem':
    #     artifact_service = FileSystemArtifactService(base_path=...)
    else:
        logger.warning(f"Unsupported ARTIFACT_SERVICE_TYPE '{artifact_type}', defaulting to 'memory'.")
        artifact_service = InMemoryArtifactService()

    # --- Memory Service (delegated to factory) ---
    try:
        memory_service = get_memory_service(service_type=memory_type)
    except Exception as e:
        # Log the error from the factory and re-raise to prevent server startup with bad config
        logger.error(f"Failed to initialize Memory Service via factory: {e}", exc_info=True)
        raise RuntimeError(f"Memory Service initialization failed: {e}") from e

    return session_service, artifact_service, memory_service 
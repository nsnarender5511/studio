# Placeholder for Memory Service configuration and potentially custom implementations

# TODO: Configure the ADK MemoryService based on requirements.
# - Choose the backend (InMemoryMemoryService, VertexAiRagMemoryService, etc.).
# - Set up necessary credentials and configurations if using cloud services.
# - Potentially implement custom memory storage or retrieval logic if needed,
#   though usually interaction happens via Memory Tools and Agents.

# from google.adk.memory import InMemoryMemoryService, VertexAiRagMemoryService
# import os

import os
import logging
from google.adk.memory import BaseMemoryService, InMemoryMemoryService, VertexAiRagMemoryService
# Import flattened config TYPE for type hinting
from src.app.config import Config

logger = logging.getLogger(__name__)

def get_memory_service(
    service_type: str,
    config_obj: Config # Accept injected flattened config object
) -> BaseMemoryService:
    """Factory function to get a configured memory service instance based on service_type."""
    service_type = service_type.lower()
    logger.info(f"Attempting to initialize MemoryService of type: '{service_type}'")

    if service_type == "vertex":
        # Use injected Config object
        project_id = config_obj.GCP_PROJECT_ID
        location = config_obj.GCP_LOCATION
        if not project_id:
            logger.error("GCP_PROJECT_ID is required for Vertex AI Memory Service (set in config or env).")
            raise ValueError("GCP_PROJECT_ID is required for Vertex AI Memory Service.")

        logger.info(f"Using Vertex AI RAG Memory Service (Project: {project_id}, Location: {location})")
        try:
            # Assuming VertexAiRagMemoryService is part of the installed google-adk package
            # and handles authentication via Application Default Credentials (ADC)
            return VertexAiRagMemoryService(project_id=project_id, location=location)
        except Exception as e:
            logger.error(f"Failed to initialize VertexAiRagMemoryService: {e}", exc_info=True)
            raise # Re-raise the exception to indicate failure

    elif service_type == "memory":
        logger.info("Using In-Memory Memory Service")
        return InMemoryMemoryService()

    else:
        logger.warning(f"Unsupported MEMORY_SERVICE_TYPE '{service_type}', defaulting to 'memory'.")
        return InMemoryMemoryService()

# # Example instantiation (usually done in main.py)
# # memory_service_instance = get_memory_service(service_type="memory")

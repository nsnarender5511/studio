import logging
from celery import Celery
# Import flattened config object
from src.app.config import config
# Import container and settings instance
from .container import Container
# Import logging setup function
from src.app.logging_setup import setup_logging

logger = logging.getLogger(__name__)

# Initialize container instance
container = Container()
container.config.override(config)

# Initialize Celery using flattened config
celery_app = Celery(__name__, broker=str(config.CELERY_BROKER_URL),
                    backend=str(config.CELERY_RESULT_BACKEND))

# --- Centralized Wiring for Celery Tasks ---
# Ensure this happens after Celery app init but before worker starts consuming tasks
# List all modules where @inject is used within Celery tasks
celery_wiring_modules = [
    "src.tasks.documentation_task",
    # Add other task modules here if they use @inject
    # "src.adk.services.memory_service", # If memory service used directly by a task with @inject
]
try:
    container.wire(modules=celery_wiring_modules)
    logger.info(f"Dependency Injector container wired centrally for Celery modules: {celery_wiring_modules}")
except Exception as e:
    logger.error(f"Central Celery wiring failed: {e}", exc_info=True)
    # Consider raising the error to prevent worker start if wiring is critical
# --- End Centralized Wiring ---

# Use config directly (no need for CELERY namespace if flattened)
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    # Add other Celery settings directly from config if defined
    # broker_connection_retry_on_startup=config.BROKER_RETRY_STARTUP, # Example
)

# Configure logging for Celery workers
setup_logging()

# Discover tasks in the specified module
celery_app.autodiscover_tasks(['src.tasks'])

logger.info(f"Celery app configured. Broker: {config.CELERY_BROKER_URL}, Backend: {config.CELERY_RESULT_BACKEND}")

if __name__ == '__main__':
    # This allows running the worker directly, e.g., for debugging
    # Command: celery -A src.app.celery_app worker --loglevel=info
    celery_app.start() 
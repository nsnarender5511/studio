import os
from celery import Celery

# Default to Redis, but allow override via environment variables
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

celery_app = Celery(
    'git_repo_documentor',
    broker=broker_url,
    backend=result_backend,
    include=['src.git_repo_documentor.tasks'] # Adjusted path relative to app location
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ensure JSON serialization
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Add task time limits if desired
    # task_time_limit=30 * 60, # e.g., 30 minutes
    # task_soft_time_limit=25 * 60,
)

if __name__ == '__main__':
    # This allows running the worker directly, e.g., for debugging
    # Command: celery -A backend.src.celery_app worker --loglevel=info
    celery_app.start() 
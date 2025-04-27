"""Custom exception classes for the application."""

class BaseApplicationError(Exception):
    """Base class for application-specific errors."""
    pass

class ConfigurationError(BaseApplicationError):
    """Error related to application configuration."""
    pass

class CloningError(BaseApplicationError):
    """Error occurred during Git repository cloning."""
    pass

class AdkOrchestrationError(BaseApplicationError):
    """Error occurred during the ADK orchestration flow."""
    def __init__(self, message, stage=None, original_exception=None):
        super().__init__(message)
        self.stage = stage
        self.original_exception = original_exception

    def __str__(self):
        base = super().__str__()
        stage_info = f" [Stage: {self.stage}]" if self.stage else ""
        return f"{base}{stage_info}"

class HistoryUpdateError(BaseApplicationError):
    """Error occurred while updating the job history database."""
    pass

class TaskEnqueueError(BaseApplicationError):
    """Error occurred while trying to enqueue a Celery task."""
    pass 
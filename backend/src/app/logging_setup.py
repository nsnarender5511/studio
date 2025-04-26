import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(log_level=logging.INFO):
    """Configures the root logger for structured JSON logging."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers if any (important for Flask app reloading)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)

    # Use a custom format including standard log record attributes
    # plus specific ones relevant to the application (e.g., job_id if added via adapter)
    log_format = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s"
    # Add other fields you might want consistently
    # format_str = '%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] %(message)s'

    formatter = jsonlogger.JsonFormatter(
        log_format,
        rename_fields={ "levelname": "level", "asctime": "timestamp" }
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Optional: Silence overly verbose libraries
    # logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.info("Structured JSON logging configured.")

# Example usage (usually called once at app startup):
# if __name__ == '__main__':
#     setup_logging()
#     logging.info("This is an info message")
#     logging.warning("This is a warning")
#     try:
#         1 / 0
#     except ZeroDivisionError:
#         logging.error("Division by zero error", exc_info=True) 
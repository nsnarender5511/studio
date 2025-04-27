import logging
import sys
from pythonjsonlogger import jsonlogger
from src.app.config import config
import coloredlogs

def setup_logging(log_level=logging.INFO):
    """Configures the root logger for structured JSON logging."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers if any (important for Flask app reloading)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)

    # Determine log format based on environment variable
    log_format_type = getattr(config, 'LOG_FORMAT', 'string').lower()

    if log_format_type == 'json':
        # Use JSON formatter for production
        log_format = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s"
        formatter = jsonlogger.JsonFormatter(
            log_format,
            rename_fields={"levelname": "level", "asctime": "timestamp"}
        )
        # Log configuration message inside the conditional block
        logging.info("Structured JSON logging configured.")
        # Ensure the handler is added for JSON format as well
        logger.addHandler(handler)
    else:
        # Default to colored string format for development
        log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s" # Example format
        level_styles = { # Example styles
            'debug': {'color': 'blue'},
            'info': {'color': 'green'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'color': 'red', 'bold': True}
        }
        # Use ColoredFormatter for development logs
        formatter = coloredlogs.ColoredFormatter(fmt=log_format, level_styles=level_styles)
        # Log configuration message updated
        logging.info("Colored string logging configured for development.")
        # Add the handler here for non-JSON format
        logger.addHandler(handler)

    # Set the chosen formatter on the handler
    handler.setFormatter(formatter)
    # Note: logger.addHandler(handler) is now called inside the conditional blocks

    # Optional: Silence overly verbose libraries
    # logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Example usage (usually called once at app startup):
# if __name__ == '__main__':
#     setup_logging()
#     # Test messages would now depend on LOG_FORMAT env var
#     logging.info("This is an info message")
#     logging.warning("This is a warning")
#     logging.debug("This is a debug message")
#     try:
#         1 / 0
#     except ZeroDivisionError:
#         logging.error("Division by zero error", exc_info=True) 
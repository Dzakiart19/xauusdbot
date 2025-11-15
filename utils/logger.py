"""
Logging Configuration & Setup
Centralized logging with file rotation and Telegram alerts for critical events
"""

import logging
import logging.handlers
from pathlib import Path
from config.settings import LOG_LEVEL, LOG_FILE, LOG_ROTATE_SIZE_MB, LOG_BACKUP_COUNT

# Create logger
logger = logging.getLogger("xauusdbot")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Ensure log directory exists
log_path = Path(LOG_FILE)
log_path.parent.mkdir(parents=True, exist_ok=True)

# File Handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=LOG_ROTATE_SIZE_MB * 1024 * 1024,
    backupCount=LOG_BACKUP_COUNT
)
file_handler.setLevel(logging.WARNING)  # File gets WARNING and above
file_format = logging.Formatter(
    "[%(asctime)s UTC] [%(levelname)s] [%(module)s:%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_format)

# Console Handler (for real-time viewing)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
console_handler.setFormatter(console_format)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_logger():
    """Get configured logger instance"""
    return logger

def log_critical(message: str, extra_info: dict = None):
    """Log critical errors with extra context"""
    if extra_info:
        message = f"{message} | {extra_info}"
    logger.critical(message)

def log_error(message: str, exception: Exception = None):
    """Log errors with optional exception traceback"""
    if exception:
        logger.error(message, exc_info=True)
    else:
        logger.error(message)

def log_warning(message: str):
    """Log warnings"""
    logger.warning(message)

def log_info(message: str):
    """Log info messages"""
    logger.info(message)

def log_debug(message: str):
    """Log debug messages"""
    logger.debug(message)

if __name__ == "__main__":
    get_logger().info("Logging system initialized")

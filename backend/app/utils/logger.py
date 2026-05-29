import logging
import sys
from typing import Any

# Configure structured logging
def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with consistent formatting."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

def log_error(logger: logging.Logger, error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log an error with context."""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"{type(error).__name__}: {str(error)}{context_str}", exc_info=True)

# Made with Bob
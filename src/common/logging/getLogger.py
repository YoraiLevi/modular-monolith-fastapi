from contextvars import ContextVar
from typing import Optional
import logging

# Create a context variable to store the current service name
current_logger_ctx: ContextVar[Optional[str]] = ContextVar("current_logger", default=None)


def getContextualLogger() -> logging.Logger:
    """Get the logger for the current context."""
    try:
        return logging.getLogger(current_logger_ctx.get())
    except Exception as e:
        logging.error("Failed to get logger for context", extra={"error": e})
        return logging.getLogger()

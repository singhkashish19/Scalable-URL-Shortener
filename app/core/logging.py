"""
Structured logging configuration for production environments.

Features:
- JSON formatted logs for aggregation (ELK, CloudWatch, etc.)
- Contextual information (request_id, user_id, etc.)
- Color-coded console output for development
- File rotating handler for production
"""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Provides:
    - Structured output for log aggregation systems
    - Exception information
    - Custom context fields (request_id, user_id)
    - Timestamp in ISO format
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for aggregation systems."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            log_obj["exception_type"] = record.exc_info[0].__name__

        # Add custom context fields
        for key in ["user_id", "request_id", "ip_address", "short_code"]:
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development console output.
    
    Makes logs more readable during development.
    """

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for terminal output."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message with color
        msg = f"{color}[{timestamp}] [{levelname}]{self.RESET} {record.getMessage()}"
        
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        
        return msg


def setup_logging() -> logging.Logger:
    """
    Configure application logging with production-grade settings.
    
    Returns:
        logger: Configured logger instance
    """
    logger = logging.getLogger("urlshortener")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Prevent duplicate handlers
    logger.handlers.clear()

    # Console handler (development-friendly or JSON based on environment)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    if settings.ENVIRONMENT == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    
    logger.addHandler(console_handler)
    
    # File handler (for production environments)
    if settings.ENVIRONMENT == "production":
        try:
            file_handler = RotatingFileHandler(
                "logs/app.log",
                maxBytes=10485760,  # 10MB
                backupCount=10
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(JSONFormatter())
            logger.addHandler(file_handler)
        except (IOError, OSError):
            pass  # Fail gracefully if logs directory doesn't exist

    return logger


logger = setup_logging()

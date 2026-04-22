"""
Structured logging utility for the application
Supports both human-readable and JSON formats based on environment
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON string representation of log record
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        # Add context if present
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context

        # Add trace_id and span_id if present
        if hasattr(record, "trace_id") and record.trace_id:
            log_data["trace_id"] = record.trace_id

        if hasattr(record, "span_id") and record.span_id:
            log_data["span_id"] = record.span_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "context",
                "trace_id",
                "span_id",
            ]:
                if not key.startswith("_"):
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as human-readable string

        Args:
            record: Log record to format

        Returns:
            Human-readable string representation of log record
        """
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        module = record.module.ljust(20)
        function = record.funcName.ljust(20)
        message = record.getMessage()

        log_line = f"{timestamp} | {level} | {module} | {function} | {message}"

        # Add context if present
        if hasattr(record, "context") and record.context:
            log_line += f" | Context: {json.dumps(record.context, ensure_ascii=False, default=str)}"

        # Add trace_id and span_id if present
        if hasattr(record, "trace_id") and record.trace_id:
            log_line += f" | trace_id: {record.trace_id}"

        if hasattr(record, "span_id") and record.span_id:
            log_line += f" | span_id: {record.span_id}"

        # Add exception info if present
        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


class StructuredLogger:
    """
    Structured logger that provides consistent logging format
    with module, function, and context information.
    Uses JSON format in production, human-readable in development.
    """

    def __init__(self, name: str):
        """
        Initialize structured logger

        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
        self._setup_handler()
        self._trace_id: str | None = None
        self._span_id: str | None = None

    def _setup_handler(self):
        """Setup logging handler if not already configured"""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)

            # Use JSON formatter in production, human-readable in development
            if settings.ENVIRONMENT.lower() in ["production", "prod"]:
                formatter = JSONFormatter()
            else:
                formatter = HumanReadableFormatter()

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def set_trace_context(self, trace_id: str | None = None, span_id: str | None = None):
        """
        Set trace context for distributed tracing

        Args:
            trace_id: Trace ID for distributed tracing
            span_id: Span ID for current operation
        """
        self._trace_id = trace_id
        self._span_id = span_id

    def _get_extra(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Get extra fields for log record

        Args:
            context: Additional context dictionary

        Returns:
            Dictionary with extra fields for log record
        """
        extra: dict[str, Any] = {}

        if context:
            extra["context"] = context

        if self._trace_id:
            extra["trace_id"] = self._trace_id

        if self._span_id:
            extra["span_id"] = self._span_id

        return extra

    def info(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """
        Log info message with optional context

        Args:
            message: Log message
            extra: Additional context dictionary
            **kwargs: Additional context as keyword arguments
        """
        context = {**(extra or {}), **kwargs}
        log_extra = self._get_extra(context if context else None)
        self.logger.info(message, extra=log_extra)

    def error(
        self, message: str, extra: dict[str, Any] | None = None, exc_info: bool = False, **kwargs
    ):
        """
        Log error message with optional context and exception info

        Args:
            message: Log message
            extra: Additional context dictionary
            exc_info: Whether to include exception traceback
            **kwargs: Additional context as keyword arguments
        """
        context = {**(extra or {}), **kwargs}
        log_extra = self._get_extra(context if context else None)
        self.logger.error(message, extra=log_extra, exc_info=exc_info)

    def warning(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """
        Log warning message with optional context

        Args:
            message: Log message
            extra: Additional context dictionary
            **kwargs: Additional context as keyword arguments
        """
        context = {**(extra or {}), **kwargs}
        log_extra = self._get_extra(context if context else None)
        self.logger.warning(message, extra=log_extra)

    def debug(self, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """
        Log debug message with optional context

        Args:
            message: Log message
            extra: Additional context dictionary
            **kwargs: Additional context as keyword arguments
        """
        context = {**(extra or {}), **kwargs}
        log_extra = self._get_extra(context if context else None)
        self.logger.debug(message, extra=log_extra)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)

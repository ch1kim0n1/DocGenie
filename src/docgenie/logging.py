"""Structured logging configuration for DocGenie."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler
from structlog.types import Processor


def configure_logging(verbose: bool = False, json_output: bool = False) -> None:
    """
    Configure structured logging for DocGenie.

    Args:
        verbose: Enable DEBUG level logging
        json_output: Output logs as JSON instead of console format
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    processors: list[Processor]
    if json_output:
        # JSON output for CI/production
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=log_level,
        )
    else:
        # Rich console output for humans
        console = Console(stderr=True)
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        logging.basicConfig(
            format="%(message)s",
            handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
            level=log_level,
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding structured context to logs."""

    def __init__(self, **context: Any) -> None:
        self.context = context
        self.token: Any | None = None

    def __enter__(self) -> LogContext:
        for key, value in self.context.items():
            structlog.contextvars.bind_contextvars(**{key: value})
        return self

    def __exit__(self, *args: Any) -> None:
        for key in self.context:
            structlog.contextvars.unbind_contextvars(key)


def log_file_operation(operation: str, path: Path, **extra: Any) -> None:
    """Log a file operation with structured context."""
    logger = get_logger(__name__)
    logger.info(
        operation,
        path=str(path),
        **extra,
    )


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log an error with full context."""
    logger = get_logger(__name__)
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **(context or {}),
        exc_info=True,
    )

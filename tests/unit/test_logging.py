"""Tests for docgenie.logging — structured logging helpers."""

from __future__ import annotations

from pathlib import Path

import structlog

from docgenie.logging import (
    LogContext,
    configure_logging,
    get_logger,
    log_error,
    log_file_operation,
)


def test_configure_logging_info_level() -> None:
    """configure_logging should not raise for normal info-level setup."""
    configure_logging(verbose=False, json_output=False)


def test_configure_logging_verbose_debug() -> None:
    """configure_logging in verbose mode should not raise."""
    configure_logging(verbose=True, json_output=False)


def test_configure_logging_json_output() -> None:
    """configure_logging with JSON output should not raise."""
    configure_logging(verbose=False, json_output=True)


def test_get_logger_returns_bound_logger() -> None:
    configure_logging(verbose=False)
    logger = get_logger("test.module")
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warning")


def test_log_context_manager_binds_context() -> None:
    configure_logging(verbose=False)
    with LogContext(request_id="abc-123"):
        ctx = structlog.contextvars.get_contextvars()
        assert "request_id" in ctx
        assert ctx["request_id"] == "abc-123"


def test_log_context_manager_unbinds_on_exit() -> None:
    configure_logging(verbose=False)
    structlog.contextvars.clear_contextvars()
    with LogContext(session="xyz"):
        pass
    ctx = structlog.contextvars.get_contextvars()
    assert "session" not in ctx


def test_log_file_operation_does_not_raise() -> None:
    configure_logging(verbose=False)
    log_file_operation("write", Path("/tmp/test.txt"), size=100)


def test_log_error_does_not_raise() -> None:
    configure_logging(verbose=False)
    err = ValueError("something went wrong")
    log_error(err, context={"component": "test"})


def test_log_error_no_context_does_not_raise() -> None:
    configure_logging(verbose=False)
    err = RuntimeError("boom")
    log_error(err)

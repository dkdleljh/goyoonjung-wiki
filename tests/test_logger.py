#!/usr/bin/env python3
"""Tests for logger module."""
from __future__ import annotations

import logging

import scripts.logger as lg


def test_setup_logger_returns_logger():
    """Test setup_logger returns a logger instance."""
    logger = lg.setup_logger("test-logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test-logger"


def test_setup_logger_creates_console_handler():
    """Test setup_logger creates console handler."""
    logger = lg.setup_logger("test-console")
    assert len(logger.handlers) > 0


def test_setup_logger_creates_file_handler(tmp_path):
    """Test setup_logger creates file handler when path provided."""
    log_file = tmp_path / "test.log"
    logger = lg.setup_logger("test-file", log_file=log_file)
    assert len(logger.handlers) == 2  # console + file

    logger.info("test message")
    assert log_file.exists()
    assert "test message" in log_file.read_text()


def test_get_logger_returns_existing():
    """Test get_logger returns existing logger."""
    logger1 = lg.get_logger("test-get")
    logger2 = lg.get_logger("test-get")
    assert logger1 is logger2


def test_log_context_changes_level():
    """Test LogContext temporarily changes log level."""
    logger = lg.get_logger("test-context")
    original_level = logger.level

    with lg.LogContext(logger, logging.DEBUG):
        assert logger.level == logging.DEBUG

    assert logger.level == original_level


def test_log_exception_logs_traceback(caplog):
    """Test log_exception includes traceback."""
    logger = lg.get_logger("test-exception")
    try:
        raise ValueError("test error")
    except ValueError as e:
        lg.log_exception(logger, "Test context", e)

    assert "test error" in caplog.text
    assert "Traceback" in caplog.text

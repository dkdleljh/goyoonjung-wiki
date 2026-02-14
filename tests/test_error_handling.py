#!/usr/bin/env python3
"""Tests for error_handling module."""
from __future__ import annotations

import pytest

import scripts.error_handling as eh


def test_wiki_error_base_exception():
    """Test WikiError can be raised and caught."""
    with pytest.raises(eh.WikiError):
        raise eh.WikiError("test error")


def test_validation_error():
    """Test ValidationError works correctly."""
    with pytest.raises(eh.ValidationError):
        raise eh.ValidationError("invalid input")


def test_validate_url_accepts_valid_url():
    """Test validate_url accepts valid URLs."""
    assert eh.validate_url("https://example.com") is True
    assert eh.validate_url("http://example.com") is True
    assert eh.validate_url("ftp://files.example.com") is True


def test_validate_url_rejects_empty():
    """Test validate_url rejects empty strings."""
    with pytest.raises(eh.ValidationError):
        eh.validate_url("")
    
    with pytest.raises(eh.ValidationError):
        eh.validate_url(None)  # type: ignore


def test_validate_url_rejects_invalid_scheme():
    """Test validate_url rejects invalid URL schemes."""
    with pytest.raises(eh.ValidationError):
        eh.validate_url("javascript:alert(1)")
    
    with pytest.raises(eh.ValidationError):
        eh.validate_url("not-a-url")


def test_validate_path_accepts_valid_path():
    """Test validate_path accepts valid paths."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        assert eh.validate_path(tmpdir, must_exist=True) is True


def test_validate_path_rejects_empty():
    """Test validate_path rejects empty paths."""
    with pytest.raises(eh.ValidationError):
        eh.validate_path("")
    
    with pytest.raises(eh.ValidationError):
        eh.validate_path(None)  # type: ignore


def test_handle_errors_returns_default():
    """Test handle_errors decorator returns default on error."""
    @eh.handle_errors(default_return="error")
    def failing_func():
        raise ValueError("test")
    
    result = failing_func()
    assert result == "error"


def test_handle_errors_reraises_when_requested():
    """Test handle_errors can reraise exceptions."""
    @eh.handle_errors(reraise=True)
    def failing_func():
        raise ValueError("test")
    
    with pytest.raises(ValueError):
        failing_func()


def test_safe_execute_returns_success():
    """Test safe_execute returns success tuple."""
    def successful_func():
        return "success"
    
    success, result, error = eh.safe_execute(successful_func)
    assert success is True
    assert result == "success"
    assert error is None


def test_safe_execute_returns_failure():
    """Test safe_execute returns failure tuple."""
    def failing_func():
        raise ValueError("test error")
    
    success, result, error = eh.safe_execute(failing_func)
    assert success is False
    assert result is None
    assert "ValueError" in error
    assert "test error" in error

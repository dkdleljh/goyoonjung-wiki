#!/usr/bin/env python3
"""Error handling utilities for goyoonjung-wiki.

This module provides standardized error handling decorators and utilities.
"""
from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Type variable for return type preservation
T = TypeVar("T")


class WikiError(Exception):
    """Base exception for wiki-related errors."""
    pass


class CollectionError(WikiError):
    """Error during data collection."""
    pass


class ProcessingError(WikiError):
    """Error during data processing."""
    pass


class ValidationError(WikiError):
    """Error during input validation."""
    pass


class NetworkError(WikiError):
    """Error during network operations."""
    pass


def handle_errors(
    default_return: Any = None,
    exceptions: tuple[type[Exception], ...] | None = None,
    log_level: int = logging.ERROR,
    reraise: bool = False,
) -> Callable:
    """Decorator for standardized error handling.

    Args:
        default_return: Value to return on error
        exceptions: Tuple of exceptions to catch (default: all)
        log_level: Logging level for error messages
        reraise: Whether to reraise the exception after logging

    Returns:
        Decorated function
    """
    if exceptions is None:
        exceptions = (Exception,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.log(
                    log_level,
                    f"Error in {func.__name__}: {type(e).__name__}: {e}",
                    exc_info=log_level >= logging.ERROR,
                )
                if reraise:
                    raise
                return default_return
        return wrapper  # type: ignore[return-value]
    return decorator


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    if not isinstance(url, str):
        raise ValidationError(f"URL must be string, got {type(url).__name__}")

    # Basic URL validation
    if not url.startswith(("http://", "https://", "ftp://")):
        raise ValidationError(f"Invalid URL scheme: {url}")

    return True


def validate_path(path: str, must_exist: bool = False) -> bool:
    """Validate file/directory path.

    Args:
        path: Path to validate
        must_exist: Whether path must exist

    Returns:
        True if valid

    Raises:
        ValidationError: If path is invalid
    """
    if not path:
        raise ValidationError("Path cannot be empty")

    if not isinstance(path, str):
        raise ValidationError(f"Path must be string, got {type(path).__name__}")

    from pathlib import Path

    p = Path(path)
    if must_exist and not p.exists():
        raise ValidationError(f"Path does not exist: {path}")

    return True


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable:
    """Decorator to retry function on error.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to retry on

    Returns:
        Decorated function
    """
    if exceptions is None:
        exceptions = (Exception,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts in {func.__name__}: {e}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed in {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    import time
                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry decorator")

        return wrapper  # type: ignore[return-value]
    return decorator


def safe_execute[T](func: Callable[..., T], *args: Any, **kwargs: Any) -> tuple[bool, T | None, str | None]:
    """Safely execute a function and return success/failure.

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Tuple of (success, result, error_message)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, f"{type(e).__name__}: {e}"

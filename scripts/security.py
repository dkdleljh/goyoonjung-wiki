#!/usr/bin/env python3
"""Input validation and sanitization module for security enhancements."""
from __future__ import annotations

import html
import re
import urllib.parse

import validators


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL."""
    if not url or not isinstance(url, str):
        return False
    try:
        result = validators.url(url)
        if result is True:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme in ('http', 'https')
        return False
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Validate if a string is a valid email address."""
    if not email or not isinstance(email, str):
        return False
    try:
        return bool(validators.email(email))
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    if not filename:
        return ""

    filename = filename.replace("..", "")
    filename = re.sub(r"[/\\]", "", filename)
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    return filename.strip()


def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML tags."""
    try:
        import bleach
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + ['br', 'p', 'strong', 'em']
        allowed_attrs = {**bleach.sanitizer.ALLOWED_ATTRIBUTES, 'a': ['href', 'title']}
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs)
    except ImportError:
        return escape_html(text)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)


def sanitize_url(url: str) -> str:
    """Sanitize and validate URL parameters."""
    if not url:
        return ""

    try:
        parsed = urllib.parse.urlparse(url)

        if parsed.scheme and parsed.scheme not in ('http', 'https'):
            return ""

        if parsed.netloc:
            if parsed.netloc.startswith('javascript:'):
                return ""
            if parsed.netloc.startswith('data:'):
                return ""

        return url
    except Exception:
        return ""


def validate_path(path: str, base_dir: str) -> bool:
    """Validate that a path is within the base directory (prevent path traversal)."""
    import os
    try:
        abs_base = os.path.abspath(base_dir)
        abs_path = os.path.abspath(os.path.join(base_dir, path))
        return abs_path.startswith(abs_base)
    except Exception:
        return False


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """Sanitize general user input."""
    if not text:
        return ""

    text = text[:max_length]

    text = escape_html(text)

    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
    ]
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    return text.strip()


def validate_date_string(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD or similar)."""
    if not date_str:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}'
    if not re.match(pattern, date_str):
        return False
    try:
        year, month, day = map(int, date_str.split('-'))
        return 1 <= month <= 12 and 1 <= day <= 31
    except (ValueError, AttributeError):
        return False


def validate_year(year_str: str) -> bool:
    """Validate year string."""
    if not year_str:
        return False
    try:
        year = int(year_str)
        return 1900 <= year <= 2100
    except (ValueError, TypeError):
        return False


def sanitize_search_query(query: str, max_length: int = 200) -> str:
    """Sanitize search query input."""
    if not query:
        return ""

    query = query[:max_length]

    query = re.sub(r'[^\w\s가-힣a-zA-Z0-9\-]', '', query)

    return query.strip()

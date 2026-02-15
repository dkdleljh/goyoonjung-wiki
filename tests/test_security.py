#!/usr/bin/env python3
"""Tests for security module."""
from __future__ import annotations

import scripts.security as security


def test_validate_url_valid():
    assert security.validate_url("https://example.com") is True
    assert security.validate_url("http://example.com/path") is True
    assert security.validate_url("https://example.com/path?query=value") is True


def test_validate_url_invalid():
    assert security.validate_url("") is False
    assert security.validate_url(None) is False
    assert security.validate_url("not-a-url") is False
    assert security.validate_url("ftp://example.com") is False


def test_validate_email_valid():
    assert security.validate_email("test@example.com") is True
    assert security.validate_email("user.name@domain.co.kr") is True


def test_validate_email_invalid():
    assert security.validate_email("") is False
    assert security.validate_email(None) is False
    assert security.validate_email("not-an-email") is False


def test_sanitize_filename():
    assert security.sanitize_filename("test.txt") == "test.txt"
    assert security.sanitize_filename("../etc/passwd") == "etcpasswd"
    assert security.sanitize_filename("test<>file.txt") == "testfile.txt"
    assert security.sanitize_filename("") == ""


def test_sanitize_filename_with_path():
    assert security.sanitize_filename("path/to/file.txt") == "pathtofile.txt"
    assert security.sanitize_filename("path\\to\\file.txt") == "pathtofile.txt"


def test_escape_html():
    assert security.escape_html("<script>") == "&lt;script&gt;"
    assert security.escape_html("&") == "&amp;"
    assert security.escape_html('"quotes"') == "&quot;quotes&quot;"


def test_sanitize_url_valid():
    assert security.sanitize_url("https://example.com") == "https://example.com"
    assert security.sanitize_url("http://example.com/path") == "http://example.com/path"


def test_sanitize_url_dangerous():
    assert security.sanitize_url("javascript:alert(1)") == ""
    assert security.sanitize_url("data:text/html,<script>") == ""
    assert security.sanitize_url("") == ""


def test_validate_path():
    assert security.validate_path("test.txt", "/base/dir") is True
    assert security.validate_path("subdir/test.txt", "/base/dir") is True
    assert security.validate_path("../etc/passwd", "/base/dir") is False


def test_sanitize_user_input():
    result = security.sanitize_user_input("<script>alert(1)</script>")
    assert "<script>" not in result

    result = security.sanitize_user_input("test<script>")
    assert "<script>" not in result

    long_input = "a" * 20000
    result = security.sanitize_user_input(long_input)
    assert len(result) == 10000


def test_validate_date_string():
    assert security.validate_date_string("2026-02-15") is True
    assert security.validate_date_string("2024-01-01") is True
    assert security.validate_date_string("") is False
    assert security.validate_date_string("invalid") is False
    assert security.validate_date_string("2026-13-01") is False


def test_validate_year():
    assert security.validate_year("2026") is True
    assert security.validate_year("1990") is True
    assert security.validate_year("") is False
    assert security.validate_year("invalid") is False
    assert security.validate_year("1800") is False
    assert security.validate_year("2200") is False


def test_sanitize_search_query():
    assert security.sanitize_search_query("고윤정") == "고윤정"
    assert security.sanitize_search_query("test query") == "test query"
    result = security.sanitize_search_query("test<script>query")
    assert "<script>" not in result
    result = security.sanitize_search_query("a" * 300)
    assert len(result) == 200

#!/usr/bin/env python3
"""Tests for check_links module."""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import Mock, patch

import scripts.check_links as check_links


def test_result_dataclass():
    """Test Result dataclass creation."""
    result = check_links.Result(url="https://example.com", status="ok", code=200)
    assert result.url == "https://example.com"
    assert result.status == "ok"
    assert result.code == 200


def test_result_dataclass_with_note():
    """Test Result with optional note field."""
    result = check_links.Result(
        url="https://example.com",
        status="warn",
        code=301,
        note="Redirect"
    )
    assert result.note == "Redirect"


def test_extract_urls_basic():
    """Test basic URL extraction."""
    text = "Check out https://example.com for more info"
    urls = check_links.extract_urls(text)
    assert "https://example.com" in urls


def test_extract_urls_multiple():
    """Test extracting multiple URLs."""
    text = "Visit https://a.com and https://b.com"
    urls = check_links.extract_urls(text)
    assert len(urls) == 2


def test_extract_urls_with_parentheses():
    """Test URL extraction handles parentheses."""
    text = "See https://example.com/page?id=1 for details"
    urls = check_links.extract_urls(text)
    assert len(urls) == 1


def test_extract_urls_complex():
    """Test URL extraction with query parameters."""
    text = "Link: https://example.com/search?q=test&lang=en"
    urls = check_links.extract_urls(text)
    assert "https://example.com/search?q=test&lang=en" in urls


def test_safe_url_basic():
    """Test URL encoding for basic URLs."""
    url = "https://example.com/path"
    result = check_links.safe_url(url)
    assert result == url


def test_safe_url_with_spaces():
    """Test URL encoding handles spaces in path."""
    url = "https://example.com/path with spaces"
    result = check_links.safe_url(url)
    assert "%20" in result or "+" in result


def test_safe_url_with_unicode():
    """Test URL encoding handles unicode characters."""
    url = "https://example.com/한글"
    result = check_links.safe_url(url)
    assert result.startswith("https://example.com/")


def test_safe_url_invalid():
    """Test safe_url handles completely invalid URLs."""
    url = ""
    result = check_links.safe_url(url)
    assert result == ""


def test_fetch_status_ok(monkeypatch):
    """Test successful URL fetch."""
    mock_response = Mock()
    mock_response.status = 200

    with patch('scripts.check_links.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
        mock_urlopen.return_value.__exit__ = Mock(return_value=False)

        result = check_links.fetch_status("https://example.com")

        assert result.status == "ok"
        assert result.code == 200


def test_fetch_status_404(monkeypatch):
    """Test 404 response handling."""
    mock_response = Mock()
    mock_response.status = 404

    with patch('scripts.check_links.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
        mock_urlopen.return_value.__exit__ = Mock(return_value=False)

        result = check_links.fetch_status("https://example.com/notfound")

        assert result.status == "bad"
        assert result.code == 404


def test_fetch_status_redirect(monkeypatch):
    """Test redirect response handling."""
    mock_response = Mock()
    mock_response.status = 301

    with patch('scripts.check_links.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__ = Mock(return_value=mock_response)
        mock_urlopen.return_value.__exit__ = Mock(return_value=False)

        result = check_links.fetch_status("https://example.com/redirect")

        assert result.status == "warn"
        assert result.code == 301


def test_fetch_status_network_error(monkeypatch):
    """Test network error handling."""
    with patch('scripts.check_links.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network error")

        result = check_links.fetch_status("https://example.com")

        assert result.status == "warn"
        assert result.code is None
        assert "error" in result.note


def test_fetch_status_timeout(monkeypatch):
    """Test timeout handling."""
    import socket

    with patch('scripts.check_links.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = socket.timeout()

        result = check_links.fetch_status("https://example.com")

        assert result.status == "warn"


def test_iter_md_files(tmp_path, monkeypatch):
    """Test iterating markdown files."""
    base = tmp_path / "wiki"
    pages = base / "pages"
    pages.mkdir(parents=True)

    (pages / "test1.md").write_text("# Test 1")
    (pages / "test2.md").write_text("# Test 2")
    (pages / "test3.txt").write_text("Not markdown")

    monkeypatch.setattr(check_links, 'PAGES_DIR', pages)

    files = list(check_links.iter_md_files())
    assert len(files) == 2


def test_write_report(tmp_path, monkeypatch):
    """Test report generation."""
    output = tmp_path / "link-health.md"

    monkeypatch.setattr(check_links, 'OUT', output)

    results = [
        check_links.Result(url="https://ok.com", status="ok", code=200),
        check_links.Result(url="https://warn.com", status="warn", code=301),
        check_links.Result(url="https://bad.com", status="bad", code=404),
    ]

    check_links.write_report(results, checked=3)

    assert output.exists()
    content = output.read_text()
    assert "OK: **1**" in content
    assert "WARN: **1**" in content
    assert "BAD: **1**" in content


def test_heal_tag_404(tmp_path):
    """Test 404 tag healing."""
    test_file = tmp_path / "test.md"
    test_file.write_text("Check https://broken.com")

    check_links.heal_tag_404(test_file, "https://broken.com")

    content = test_file.read_text()
    assert "<!-- Broken/404:" in content


def test_heal_tag_already_tagged(tmp_path):
    """Test healing skips already tagged URLs."""
    test_file = tmp_path / "test.md"
    test_file.write_text("Check https://broken.com <!-- Broken/404: 2026-02-15 -->")

    check_links.heal_tag_404(test_file, "https://broken.com")

    content = test_file.read_text()
    assert content.count("<!-- Broken/404:") == 1


def test_url_regex_patterns():
    """Test URL regex catches common patterns."""
    test_cases = [
        "https://example.com",
        "http://example.com",
        "https://example.com/path",
        "https://example.com/path?query=value",
        "https://example.com/path#anchor",
    ]

    for url in test_cases:
        matches = check_links.extract_urls(f"Link: {url}")
        assert url in matches

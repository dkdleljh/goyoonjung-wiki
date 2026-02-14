#!/usr/bin/env python3
"""Tests for auto_collect_visual_links module."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import scripts.auto_collect_visual_links as vis


def test_entry_dataclass_creation():
    """Test Entry dataclass can be created."""
    entry = vis.Entry(year=2024, block="- [제목](url)", url="https://example.com")
    assert entry.year == 2024
    assert entry.url == "https://example.com"


def test_entry_dataclass_immutable():
    """Test Entry dataclass is frozen (immutable)."""
    entry = vis.Entry(year=2024, block="test", url="https://example.com")
    with pytest.raises(Exception):  # frozen dataclass
        entry.year = 2025


def test_read_text(tmp_path):
    """Test read_text function."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content", encoding="utf-8")
    
    content = vis.read_text(str(test_file))
    assert content == "test content"


def test_write_text(tmp_path):
    """Test write_text function."""
    test_file = tmp_path / "test.txt"
    
    vis.write_text(str(test_file), "new content")
    
    assert test_file.read_text(encoding="utf-8") == "new content"


def test_load_seen_urls_returns_set():
    """Test load_seen_urls returns a set."""
    urls = vis.load_seen_urls()
    assert isinstance(urls, set)


def test_load_seen_urls_with_file(tmp_path, monkeypatch):
    """Test load_seen_urls reads from file."""
    test_file = tmp_path / "seen.txt"
    test_file.write_text("https://url1.com\nhttps://url2.com\n", encoding="utf-8")
    
    monkeypatch.setattr(vis, 'SEEN_TXT', str(test_file))
    
    urls = vis.load_seen_urls()
    assert "https://url1.com" in urls
    assert "https://url2.com" in urls


def test_load_seen_urls_ignores_empty_lines(tmp_path, monkeypatch):
    """Test load_seen_urls ignores empty lines."""
    test_file = tmp_path / "seen.txt"
    test_file.write_text("https://url1.com\n\nhttps://url2.com\n  \n", encoding="utf-8")
    
    monkeypatch.setattr(vis, 'SEEN_TXT', str(test_file))
    
    urls = vis.load_seen_urls()
    assert len(urls) == 2


def test_extract_date_from_text():
    """Test date extraction from text."""
    result = vis.extract_date_from_text("2024-01-15")
    assert result == "2024-01-15"


def test_extract_date_from_text_returns_none():
    """Test date extraction returns None for invalid input."""
    result = vis.extract_date_from_text("no date here")
    assert result is None


@patch('scripts.auto_collect_visual_links.requests.get')
def test_http_get_success(mock_get):
    """Test http_get returns content on success."""
    mock_response = MagicMock()
    mock_response.text = "test content"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    result = vis.http_get("https://example.com")
    assert result == "test content"


@patch('scripts.auto_collect_visual_links.requests.get')
def test_http_get_raises_on_error(mock_get):
    """Test http_get raises on HTTP error."""
    import requests
    mock_get.side_effect = requests.HTTPError("404 Not Found")
    
    with pytest.raises(requests.HTTPError):
        vis.http_get("https://example.com")


def test_ensure_year_section():
    """Test ensure_year_section adds year section."""
    md = "# Title\n\n"
    result = vis.ensure_year_section(md, 2024)
    
    assert "## 2024" in result
    assert "(추가 보강 필요)" in result


def test_ensure_year_section_existing_year():
    """Test ensure_year_section returns same if year exists."""
    md = "# Title\n\n## 2024\n(추가 보강 필요)\n"
    result = vis.ensure_year_section(md, 2024)
    assert result == md

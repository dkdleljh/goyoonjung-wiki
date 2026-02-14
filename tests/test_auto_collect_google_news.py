#!/usr/bin/env python3
"""Tests for auto_collect_google_news module."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import scripts.auto_collect_google_news as gnews


def test_normalize_rss_url_ascii():
    """Test normalize_rss_url with ASCII URL."""
    url = "https://example.com/search?q=test"
    result = gnews.normalize_rss_url(url)
    assert result == url


def test_normalize_rss_url_unicode():
    """Test normalize_rss_url with Unicode URL."""
    url = "https://example.com/search?q=고윤정"
    result = gnews.normalize_rss_url(url)
    assert "%EA%B3%A0%EC%9C%A4%EC%A0%95" in result


def test_get_today_news_path():
    """Test get_today_news_path returns correct path."""
    result = gnews.get_today_news_path()
    assert "news/" in result
    assert result.endswith(".md")


def test_clean_title():
    """Test clean_title removes HTML tags."""
    title = "<b>고윤정</b> Interview &quot;Test&quot;"
    result = gnews.clean_title(title)
    assert "<b>" not in result
    assert "</b>" not in result
    assert "&quot;" not in result


def test_classify_interview():
    """Test classify returns Interview for interview titles."""
    result = gnews.classify("고윤정 인터뷰")
    assert result == "Interview"


def test_classify_work():
    """Test classify returns Work for drama/movie titles."""
    result = gnews.classify("고윤정 무빙 드라마")
    assert result == "Work"
    
    result = gnews.classify("고윤정 환혼")
    assert result == "Work"


def test_classify_pictorial():
    """Test classify returns Pictorial for magazine titles."""
    result = gnews.classify("고윤정 화보")
    assert result == "Pictorial"
    
    result = gnews.classify("고윤정 보그")
    assert result == "Pictorial"


def test_classify_general():
    """Test classify returns General for other titles."""
    result = gnews.classify("고윤정 최신 뉴스")
    assert result == "General"


@patch('scripts.auto_collect_google_news.urlopen')
def test_fetch_rss_success(mock_urlopen):
    """Test fetch_rss returns XML data."""
    mock_response = MagicMock()
    mock_response.read.return_value = b"<rss><channel><item><title>Test</title></item></channel></rss>"
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response
    
    result = gnews.fetch_rss()
    assert isinstance(result, bytes)


@patch('scripts.auto_collect_google_news.urlopen')
def test_fetch_rss_failure(mock_urlopen):
    """Test fetch_rss raises on failure."""
    from urllib.error import URLError
    mock_urlopen.side_effect = URLError("Connection failed")
    
    with pytest.raises(URLError):
        gnews.fetch_rss()


def test_decode_google_news_url():
    """Test decode_google_news_url handles URLs."""
    result = gnews.decode_google_news_url("https://news.google.com/rss/articles/abc123")
    assert isinstance(result, str)

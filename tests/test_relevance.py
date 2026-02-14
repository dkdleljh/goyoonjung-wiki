#!/usr/bin/env python3
"""Tests for relevance module."""
from __future__ import annotations

import scripts.relevance as rel


def test_is_relevant_accepts_name_in_title():
    """Test that title with name is accepted."""
    result = rel.is_relevant(
        title="고윤정 최근 드라마 참여",
        url="https://example.com/article",
        source="KBS",
        description="description"
    )
    assert result is True


def test_is_relevant_rejects_without_name():
    """Test that title without name is rejected."""
    result = rel.is_relevant(
        title="최근 드라마 인기",
        url="https://example.com/article",
        source="KBS",
        description="description"
    )
    assert result is False


def test_is_relevant_accepts_name_in_description():
    """Test that name in description is accepted."""
    result = rel.is_relevant(
        title="드라마 리뷰",
        url="https://example.com/article",
        source="KBS",
        description="고윤정님이 참여하는 드라마"
    )
    assert result is True


def test_is_relevant_rejects_finance_keywords():
    """Test that finance-related titles are rejected."""
    result = rel.is_relevant(
        title="고윤정 주가 전망",
        url="https://example.com/stock",
        source="증권사",
        description="주식 분석"
    )
    assert result is False


def test_is_relevant_accepts_finance_with_entertainment_context():
    """Test that finance + entertainment context is accepted."""
    result = rel.is_relevant(
        title="고윤정 드라마 촬영 중",
        url="https://example.com",
        source="보그",
        description="부동산 투자"
    )
    assert result is True


def test_is_relevant_scores_trusted_sources():
    """Test that trusted sources get bonus points."""
    result = rel.is_relevant(
        title="고윤정 인터뷰",
        url="https://vogue.kr",
        source="Vogue",
        description=""
    )
    assert result is True


def test_is_relevant_scores_context_tokens():
    """Test that context tokens give bonus points."""
    result = rel.is_relevant(
        title="고윤정 드라마 캐스팅",
        url="https://example.com",
        source="뉴스",
        description=""
    )
    assert result is True


def test_is_relevant_url_with_name():
    """Test that URL containing name alone is not enough (needs score >= 3)."""
    result = rel.is_relevant(
        title="Article",
        url="https://goyoun-jung.com/article",
        source="News",
        description=""
    )
    # URL with name gives +1, but needs >=3, so this returns False
    assert result is False


def test_is_relevant_url_with_name_and_context():
    """Test that URL containing name with context passes."""
    result = rel.is_relevant(
        title="고윤정 인터뷰",
        url="https://goyoun-jung.com/article",
        source="News",
        description=""
    )
    # NAME in title (+3) + URL contains goyoun (+1) = 4 >= 3
    assert result is True


def test_is_relevant_returns_false_for_low_score():
    """Test that items with low score are rejected."""
    # Name not in title or description, low context
    result = rel.is_relevant(
        title="Article Title",
        url="https://example.com",
        source="Unknown",
        description=""
    )
    assert result is False


def test_load_blacklist_returns_set():
    """Test that load_blacklist returns a set."""
    blacklist = rel.load_blacklist()
    assert isinstance(blacklist, set)
    assert len(blacklist) > 0


def test_load_blacklist_includes_defaults():
    """Test that default blacklist items are included."""
    blacklist = rel.load_blacklist()
    assert "주가" in blacklist
    assert "부동산" in blacklist

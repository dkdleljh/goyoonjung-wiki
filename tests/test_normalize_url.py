#!/usr/bin/env python3
"""Tests for URL normalization."""

from __future__ import annotations

import scripts.normalize_url as nu


def test_strips_tracking_params():
    url = "https://example.com/a?utm_source=x&fbclid=y&id=1"
    assert nu.norm(url) == "https://example.com/a?id=1"


def test_mobile_and_amp_host_normalized():
    url = "https://m.example.com/amp/article/123/amp?utm_medium=social"
    assert nu.norm(url) == "https://example.com/article/123"


def test_youtube_watch_canonicalized():
    url = "https://youtu.be/abc123?t=10&utm_source=x"
    assert nu.norm(url) == "https://www.youtube.com/watch?v=abc123"


def test_youtube_shorts_canonicalized():
    url = "https://m.youtube.com/shorts/xyz789?feature=share"
    assert nu.norm(url) == "https://www.youtube.com/watch?v=xyz789"


#!/usr/bin/env python3
"""Tests for rebuild_timeline_narrative module."""
from __future__ import annotations


def test_timeline_module():
    import scripts.rebuild_timeline_narrative as timeline
    assert timeline is not None


def test_timeline_has_main():
    import scripts.rebuild_timeline_narrative as timeline
    assert hasattr(timeline, 'main')


def test_timeline_base():
    import scripts.rebuild_timeline_narrative as timeline
    assert hasattr(timeline, 'BASE')

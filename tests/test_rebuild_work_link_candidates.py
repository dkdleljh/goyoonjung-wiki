#!/usr/bin/env python3
"""Tests for rebuild_work_link_candidates module."""
from __future__ import annotations


def test_rebuild_module_imports():
    import scripts.rebuild_work_link_candidates as rebuild
    assert rebuild is not None


def test_rebuild_has_main():
    import scripts.rebuild_work_link_candidates as rebuild
    assert hasattr(rebuild, 'main')


def test_rebuild_constants():
    import scripts.rebuild_work_link_candidates as rebuild
    assert hasattr(rebuild, 'BASE')

#!/usr/bin/env python3
"""Tests for auto_collect_schedule module."""
from __future__ import annotations


def test_schedule_module_imports():
    import scripts.auto_collect_schedule as schedule
    assert schedule is not None


def test_schedule_has_main():
    import scripts.auto_collect_schedule as schedule
    assert hasattr(schedule, 'main')


def test_schedule_constants():
    import scripts.auto_collect_schedule as schedule
    assert hasattr(schedule, 'BASE')

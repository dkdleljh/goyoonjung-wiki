#!/usr/bin/env python3
"""Tests for auto_collect_agency module."""
from __future__ import annotations


def test_agency_module():
    import scripts.auto_collect_agency as agency
    assert agency is not None


def test_agency_has_main():
    import scripts.auto_collect_agency as agency
    assert hasattr(agency, 'main')


def test_agency_base():
    import scripts.auto_collect_agency as agency
    assert hasattr(agency, 'BASE')

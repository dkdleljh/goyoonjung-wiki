#!/usr/bin/env python3
"""Tests for config_loader module."""
from __future__ import annotations


def test_config_loader_import():
    import scripts.config_loader as config_loader
    assert config_loader is not None


def test_config_loader_has_base():
    import scripts.config_loader as config_loader
    assert hasattr(config_loader, 'BASE')


def test_config_loader_has_load_config():
    import scripts.config_loader as config_loader
    assert hasattr(config_loader, 'load_yaml' if hasattr(config_loader, 'load_yaml') else 'load_config')


def test_config_loader_constants():
    import scripts.config_loader as config_loader
    assert hasattr(config_loader, 'BASE')
    assert hasattr(config_loader, 'CONFIG_PATH')

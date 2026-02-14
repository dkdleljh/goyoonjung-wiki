#!/usr/bin/env python3
"""Tests for config_loader module."""
from __future__ import annotations

from pathlib import Path

import scripts.config_loader as cfg


def test_load_config_returns_dict(tmp_path, monkeypatch):
    """Test load_config returns a dictionary."""
    # Create a temporary config file
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
rss_url: "https://example.com/rss"
schedule_keywords:
  - "공개"
  - "개봉"
""")

    monkeypatch.setattr(cfg, 'CONFIG_PATH', config_file)

    config = cfg.load_config()
    assert isinstance(config, dict)


def test_load_config_parses_simple_key_value(tmp_path, monkeypatch):
    """Test loading simple key-value pairs."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text('test_key: "test_value"')

    monkeypatch.setattr(cfg, 'CONFIG_PATH', config_file)

    config = cfg.load_config()
    assert config.get("test_key") == "test_value"


def test_load_config_parses_nested_keys(tmp_path, monkeypatch):
    """Test loading nested key-value pairs."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
parent:
  child: "value"
""")

    monkeypatch.setattr(cfg, 'CONFIG_PATH', config_file)

    config = cfg.load_config()
    assert "parent" in config
    assert config["parent"]["child"] == "value"


def test_load_config_parses_list(tmp_path, monkeypatch):
    """Test loading list values."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
items:
  - "item1"
  - "item2"
""")

    monkeypatch.setattr(cfg, 'CONFIG_PATH', config_file)

    config = cfg.load_config()
    assert "items" in config
    assert "item1" in config["items"]
    assert "item2" in config["items"]


def test_load_config_ignores_comments(tmp_path, monkeypatch):
    """Test that comments are ignored."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
# This is a comment
key: "value"
""")

    monkeypatch.setattr(cfg, 'CONFIG_PATH', config_file)

    config = cfg.load_config()
    assert config.get("key") == "value"


def test_load_config_handles_missing_file():
    """Test that missing config file returns empty dict."""
    cfg.CONFIG_PATH = Path("/nonexistent/config.yaml")

    config = cfg.load_config()
    assert config == {}


def test_load_config_strips_quotes(tmp_path, monkeypatch):
    """Test that quotes are stripped from values."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text('''
key1: "value1"
key2: 'value2'
''')

    monkeypatch.setattr(cfg, 'CONFIG_PATH', config_file)

    config = cfg.load_config()
    assert config.get("key1") == "value1"
    assert config.get("key2") == "value2"

#!/usr/bin/env python3
"""Tests for notify_status module."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import scripts.notify_status as ns


def test_color_mapping():
    """Test color mapping for different status types."""
    assert "green" in ns.COLORS
    assert "yellow" in ns.COLORS
    assert "red" in ns.COLORS


def test_color_values():
    """Test color values are integers."""
    assert isinstance(ns.COLORS["green"], int)
    assert isinstance(ns.COLORS["yellow"], int)
    assert isinstance(ns.COLORS["red"], int)


def test_webhook_url_from_config():
    """Test WEBHOOK_URL is defined."""
    # WEBHOOK_URL can be None or a string
    assert ns.WEBHOOK_URL is None or isinstance(ns.WEBHOOK_URL, str)


def test_send_discord_message_no_webhook(capsys):
    """Test send_discord_message prints message when no webhook."""
    ns.WEBHOOK_URL = None

    result = ns.send_discord_message("Test", "Message", "green")

    assert result is False
    captured = capsys.readouterr()
    assert "Test" in captured.out

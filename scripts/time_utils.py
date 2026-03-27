#!/usr/bin/env python3
"""Shared timezone helpers for Seoul-based automation."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

SEOUL_TZ = ZoneInfo("Asia/Seoul")


def seoul_now() -> datetime:
    return datetime.now(SEOUL_TZ)


def seoul_today_str() -> str:
    return seoul_now().strftime("%Y-%m-%d")


def seoul_timestamp_str() -> str:
    return seoul_now().strftime("%Y-%m-%d %H:%M")


def seoul_timestamp_seconds_str() -> str:
    return seoul_now().strftime("%Y-%m-%d %H:%M:%S")

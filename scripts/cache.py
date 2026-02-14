#!/usr/bin/env python3
"""Performance optimization module for wiki automation.

This module provides caching and performance optimization utilities.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE / ".cache"


class Cache:
    """Simple file-based cache with TTL support."""

    def __init__(self, name: str, ttl_seconds: int = 3600):
        self.name = name
        self.ttl = ttl_seconds
        self.cache_dir = CACHE_DIR / name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Any | None:
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            if time.time() - data.get("_cached_at", 0) > self.ttl:
                path.unlink()
                return None

            return data.get("value")
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any) -> bool:
        path = self._get_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"value": value, "_cached_at": time.time()}, f)
            return True
        except OSError as e:
            logger.warning(f"Cache write failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            count += 1
        return count


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self) -> None:
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


def get_cache(name: str, ttl: int = 3600) -> Cache:
    return Cache(name, ttl)


def clear_all_caches() -> int:
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for cache_dir in CACHE_DIR.iterdir():
        if cache_dir.is_dir():
            for f in cache_dir.glob("*.json"):
                f.unlink()
                count += 1
    return count

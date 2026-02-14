#!/usr/bin/env python3
"""Tests for cache module."""
from __future__ import annotations

import time

import pytest

import scripts.cache as cache


def test_cache_init():
    c = cache.Cache("test-cache", ttl_seconds=60)
    assert c.name == "test-cache"
    assert c.ttl == 60


def test_cache_set_get(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, 'CACHE_DIR', tmp_path / ".cache")
    
    c = cache.Cache("test")
    assert c.get("key") is None
    
    c.set("key", "value")
    assert c.get("key") == "value"


def test_cache_expiry(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, 'CACHE_DIR', tmp_path / ".cache")
    
    c = cache.Cache("test", ttl_seconds=1)
    c.set("key", "value")
    
    time.sleep(1.1)
    assert c.get("key") is None


def test_cache_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, 'CACHE_DIR', tmp_path / ".cache")
    
    c = cache.Cache("test")
    c.set("key", "value")
    assert c.get("key") == "value"
    
    c.delete("key")
    assert c.get("key") is None


def test_cache_clear(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, 'CACHE_DIR', tmp_path / ".cache")
    
    c = cache.Cache("test")
    c.set("key1", "value1")
    c.set("key2", "value2")
    
    count = c.clear()
    assert count >= 2


def test_rate_limiter():
    limiter = cache.RateLimiter(calls_per_second=10)
    
    start = time.time()
    for _ in range(3):
        limiter.wait()
    elapsed = time.time() - start
    
    assert elapsed >= 0.2


def test_get_cache():
    c = cache.get_cache("test", ttl=60)
    assert isinstance(c, cache.Cache)
    assert c.name == "test"
    assert c.ttl == 60


def test_clear_all_caches(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, 'CACHE_DIR', tmp_path / ".cache")
    
    c1 = cache.Cache("cache1")
    c2 = cache.Cache("cache2")
    c1.set("key", "value")
    c2.set("key", "value")
    
    count = cache.clear_all_caches()
    assert count >= 2

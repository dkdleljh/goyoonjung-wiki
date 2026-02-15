#!/usr/bin/env python3
"""Tests for performance_optimizer module."""
from __future__ import annotations

import time

import scripts.performance_optimizer as performance_optimizer


def test_task_result_dataclass():
    result = performance_optimizer.TaskResult(
        task_name="test",
        success=True,
        duration=1.0,
        output="output"
    )
    assert result.task_name == "test"
    assert result.success is True


def test_performance_metrics_dataclass():
    metrics = performance_optimizer.PerformanceMetrics(
        task_count=10,
        total_duration=5.0,
        parallel_duration=2.0,
        speedup_factor=2.5,
        cache_hit_rate=0.8
    )
    assert metrics.task_count == 10
    assert metrics.speedup_factor == 2.5


def test_simple_cache_init():
    cache = performance_optimizer.SimpleCache(ttl_seconds=60)
    assert cache.ttl == 60
    assert cache.cache == {}


def test_simple_cache_set_get():
    cache = performance_optimizer.SimpleCache(ttl_seconds=60)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_simple_cache_expiry():
    cache = performance_optimizer.SimpleCache(ttl_seconds=1)
    cache.set("key1", "value1")
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_simple_cache_clear():
    cache = performance_optimizer.SimpleCache(ttl_seconds=60)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_simple_cache_hit_rate():
    cache = performance_optimizer.SimpleCache(ttl_seconds=60)
    rate = cache.get_hit_rate()
    assert isinstance(rate, float)


def test_async_runner_init():
    runner = performance_optimizer.AsyncRunner(max_workers=4, cache_ttl=3600)
    assert runner.max_workers == 4
    assert runner.cache.ttl == 3600


def test_async_runner_cache_key():
    runner = performance_optimizer.AsyncRunner()
    key1 = runner._get_cache_key("https://example.com", "GET")
    key2 = runner._get_cache_key("https://example.com", "GET")
    key3 = runner._get_cache_key("https://example.com", "POST")
    assert key1 == key2
    assert key1 != key3


def test_async_runner_cache_usage():
    runner = performance_optimizer.AsyncRunner(cache_ttl=60)
    cache_key = runner._get_cache_key("https://example.com", "GET")
    runner.cache.set(cache_key, "cached_content")
    result = runner.cache.get(cache_key)
    assert result == "cached_content"


def test_parallel_script_runner_init():
    runner = performance_optimizer.ParallelScriptRunner(max_workers=3)
    assert runner.max_workers == 3


def test_parallel_script_runner_result():
    result = performance_optimizer.TaskResult(
        task_name="test_script",
        success=True,
        duration=1.5,
        output="test output"
    )
    assert result.success is True
    assert result.duration == 1.5


def test_task_result_with_error():
    result = performance_optimizer.TaskResult(
        task_name="test",
        success=False,
        duration=1.0,
        output=None,
        error="Test error"
    )
    assert result.success is False
    assert result.error == "Test error"


def test_performance_metrics_all_fields():
    metrics = performance_optimizer.PerformanceMetrics(
        task_count=100,
        total_duration=10.0,
        parallel_duration=3.0,
        speedup_factor=3.33,
        cache_hit_rate=0.75
    )
    assert metrics.task_count == 100
    assert metrics.total_duration == 10.0
    assert metrics.parallel_duration == 3.0
    assert metrics.speedup_factor == 3.33
    assert metrics.cache_hit_rate == 0.75


def test_cache_multiple_keys():
    cache = performance_optimizer.SimpleCache(ttl_seconds=60)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_cache_nonexistent_key():
    cache = performance_optimizer.SimpleCache(ttl_seconds=60)
    result = cache.get("nonexistent")
    assert result is None


def test_async_runner_session():
    runner = performance_optimizer.AsyncRunner()
    assert runner.session is None


def test_cache_key_uniqueness():
    runner = performance_optimizer.AsyncRunner()
    key1 = runner._get_cache_key("https://a.com", "GET")
    key2 = runner._get_cache_key("https://b.com", "GET")
    key3 = runner._get_cache_key("https://a.com", "POST")
    assert key1 != key2
    assert key1 != key3

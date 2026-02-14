#!/usr/bin/env python3
"""Tests for lock_manager module."""
from __future__ import annotations

import time

import pytest

import scripts.lock_manager as lm


@pytest.fixture
def temp_lock_dir(tmp_path):
    """Create a temporary lock directory."""
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()
    return lock_dir


def test_atomic_lock_acquire_release(temp_lock_dir):
    """Test basic lock acquire and release."""
    lock = lm.AtomicLock("test-lock", str(temp_lock_dir), timeout=10)

    assert lock.acquire() is True
    assert lock.acquired is True

    lock.release()
    assert lock.acquired is False


def test_atomic_lock_prevents_duplicate(temp_lock_dir):
    """Test that lock prevents duplicate acquisition."""
    lock1 = lm.AtomicLock("test-lock2", str(temp_lock_dir), timeout=10)
    lock2 = lm.AtomicLock("test-lock2", str(temp_lock_dir), timeout=10)

    assert lock1.acquire() is True
    assert lock2.acquire(block=False) is False

    lock1.release()


def test_atomic_lock_context_manager(temp_lock_dir):
    """Test lock as context manager."""
    with lm.AtomicLock("test-lock3", str(temp_lock_dir), timeout=10) as lock:
        assert lock.acquired is True
    assert lock.acquired is False


def test_lock_manager_get_lock(temp_lock_dir):
    """Test LockManager.get_lock returns AtomicLock."""
    manager = lm.LockManager(str(temp_lock_dir))
    lock = manager.get_lock("test-lock", timeout=10)

    assert isinstance(lock, lm.AtomicLock)
    assert lock.lock_name == "test-lock"


def test_lock_manager_cleanup_stale_locks(temp_lock_dir):
    """Test cleanup of stale locks."""
    # Create a stale lock by force
    stale_lock_dir = temp_lock_dir / "stale-lock"
    stale_lock_dir.mkdir()
    (stale_lock_dir / "lock_info.json").write_text('{"pid": 99999, "start_time": "2020-01-01T00:00:00"}')

    manager = lm.LockManager(str(temp_lock_dir))
    manager.cleanup_stale_locks()

    assert not stale_lock_dir.exists()


def test_lock_manager_get_lock_status(temp_lock_dir):
    """Test getting lock status."""
    manager = lm.LockManager(str(temp_lock_dir))

    with manager.get_lock("test-lock-status", timeout=10):
        status = manager.get_lock_status()
        assert "test-lock-status" in status
        assert status["test-lock-status"]["status"] == "active"


def test_lock_timeout_handling(temp_lock_dir):
    """Test that lock times out correctly."""
    lock = lm.AtomicLock("timeout-lock", str(temp_lock_dir), timeout=1)

    # Acquire and release immediately
    lock.acquire()
    time.sleep(0.1)
    lock.release()

    # Should be able to acquire again
    lock2 = lm.AtomicLock("timeout-lock", str(temp_lock_dir), timeout=1)
    assert lock2.acquire() is True
    lock2.release()


def test_with_lock_decorator(temp_lock_dir, monkeypatch):
    """Test the with_lock decorator."""
    monkeypatch.chdir(temp_lock_dir.parent)

    call_count = 0

    @lm.with_lock("decorator-test-lock", timeout=10)
    def test_func():
        nonlocal call_count
        call_count += 1
        return "executed"

    result = test_func()
    assert result == "executed"
    assert call_count == 1


def test_force_release_handles_missing_info(temp_lock_dir):
    """Test force release when info file is missing."""
    lock_dir = temp_lock_dir / "no-info-lock"
    lock_dir.mkdir()

    lock = lm.AtomicLock("no-info-lock", str(temp_lock_dir), timeout=10)
    lock._force_release()  # Should not raise

    assert not lock_dir.exists()

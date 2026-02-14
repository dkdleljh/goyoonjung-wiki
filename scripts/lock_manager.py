#!/usr/bin/env python3
"""
Atomic Lock Manager for goyoonjung-wiki automation
Implements directory-based atomic locking with deadlock prevention
"""

import os
import sys
import time
import errno
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, ContextManager
import fcntl
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AtomicLock:
    """Directory-based atomic lock with timeout and deadlock detection"""
    
    def __init__(self, lock_name: str, lock_dir: str = ".locks", timeout: int = 1800):
        self.lock_name = lock_name
        self.lock_dir = Path(lock_dir)
        self.lock_path = self.lock_dir / lock_name
        self.timeout = timeout
        self.info_file = self.lock_path / "lock_info.json"
        self.acquired = False
        
        # Ensure lock directory exists
        self.lock_dir.mkdir(exist_ok=True)
    
    def acquire(self, block: bool = True) -> bool:
        """Acquire atomic lock using mkdir"""
        start_time = time.time()
        
        while True:
            try:
                # Atomic directory creation
                self.lock_path.mkdir(exist_ok=False)
                self.acquired = True
                
                # Write lock information
                lock_info = {
                    "pid": os.getpid(),
                    "start_time": datetime.now().isoformat(),
                    "lock_name": self.lock_name,
                    "hostname": os.uname().nodename
                }
                
                with open(self.info_file, 'w') as f:
                    json.dump(lock_info, f, indent=2)
                
                logger.info(f"Lock acquired: {self.lock_name} (PID: {os.getpid()})")
                return True
                
            except FileExistsError:
                # Check for stale lock
                if self._is_stale_lock():
                    logger.warning(f"Stale lock detected: {self.lock_name}, removing...")
                    self._force_release()
                    continue
                
                if not block:
                    return False
                    
                # Check timeout
                if time.time() - start_time > self.timeout:
                    logger.error(f"Lock timeout: {self.lock_name}")
                    return False
                
                # Wait before retry
                time.sleep(1)
    
    def release(self):
        """Release the lock"""
        if self.acquired:
            try:
                if self.info_file.exists():
                    self.info_file.unlink()
                self.lock_path.rmdir()
                self.acquired = False
                logger.info(f"Lock released: {self.lock_name}")
            except OSError as e:
                logger.error(f"Error releasing lock {self.lock_name}: {e}")
    
    def _is_stale_lock(self) -> bool:
        """Check if lock is stale (older than timeout)"""
        if not self.info_file.exists():
            # Fallback: check directory modification time
            try:
                mtime = self.lock_path.stat().st_mtime
                age = time.time() - mtime
                return age > self.timeout
            except OSError:
                return True
        
        try:
            with open(self.info_file, 'r') as f:
                lock_info = json.load(f)
            
            start_time = datetime.fromisoformat(lock_info["start_time"])
            age = (datetime.now() - start_time).total_seconds()
            
            # Check if process still exists
            try:
                os.kill(lock_info["pid"], 0)
                return age > self.timeout
            except OSError:
                # Process doesn't exist
                return True
                
        except (json.JSONDecodeError, KeyError, OSError, ValueError):
            return True
    
    def _force_release(self):
        """Force release a stale lock"""
        try:
            if self.info_file.exists():
                self.info_file.unlink()
            self.lock_path.rmdir()
        except OSError:
            pass
    
    def __enter__(self):
        if self.acquire():
            return self
        raise TimeoutError(f"Could not acquire lock: {self.lock_name}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    
    def __del__(self):
        if self.acquired:
            self.release()

class LockManager:
    """Manages multiple locks with deadlock detection"""
    
    def __init__(self, lock_dir: str = ".locks"):
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True)
        self.acquired_locks = []
        
    def get_lock(self, lock_name: str, timeout: int = 1800) -> AtomicLock:
        """Get a lock instance"""
        return AtomicLock(lock_name, self.lock_dir, timeout)
    
    def acquire_multiple(self, lock_names: list, timeout: int = 1800) -> bool:
        """Acquire multiple locks with deadlock prevention"""
        # Sort lock names to prevent deadlock
        sorted_locks = sorted(lock_names)
        
        acquired_locks = []
        try:
            for lock_name in sorted_locks:
                lock = self.get_lock(lock_name, timeout)
                if not lock.acquire(block=False):
                    # Release already acquired locks
                    for acquired_lock in acquired_locks:
                        acquired_lock.release()
                    return False
                acquired_locks.append(lock)
            
            self.acquired_locks.extend(acquired_locks)
            return True
            
        except Exception:
            # Release any acquired locks
            for lock in acquired_locks:
                lock.release()
            return False
    
    def cleanup_stale_locks(self):
        """Clean up all stale locks"""
        for lock_path in self.lock_dir.iterdir():
            if lock_path.is_dir():
                lock = AtomicLock(lock_path.name, self.lock_dir)
                if lock._is_stale_lock():
                    logger.info(f"Cleaning up stale lock: {lock_path.name}")
                    lock._force_release()
    
    def get_lock_status(self) -> dict:
        """Get status of all locks"""
        status = {}
        for lock_path in self.lock_dir.iterdir():
            if lock_path.is_dir():
                info_file = lock_path / "lock_info.json"
                if info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            lock_info = json.load(f)
                        status[lock_path.name] = {
                            "status": "active",
                            "info": lock_info
                        }
                    except (json.JSONDecodeError, IOError, OSError):
                        status[lock_path.name] = {"status": "unknown"}
                else:
                    status[lock_path.name] = {"status": "no_info"}
        
        return status
    
    def release_all(self):
        """Release all acquired locks"""
        for lock in self.acquired_locks:
            lock.release()
        self.acquired_locks.clear()

# Global lock manager instance
lock_manager = LockManager()

def with_lock(lock_name: str, timeout: int = 1800):
    """Decorator for functions that need locking"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with lock_manager.get_lock(lock_name, timeout):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle signals for graceful shutdown"""
    logger.info("Received signal, releasing locks...")
    lock_manager.release_all()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Lock Manager')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup stale locks')
    parser.add_argument('--status', action='store_true', help='Show lock status')
    parser.add_argument('--test', action='store_true', help='Test lock functionality')
    parser.add_argument('--lock-name', type=str, help='Test specific lock')
    
    args = parser.parse_args()
    
    if args.cleanup:
        lock_manager.cleanup_stale_locks()
    
    elif args.status:
        status = lock_manager.get_lock_status()
        print("Lock Status:")
        for lock_name, info in status.items():
            print(f"  {lock_name}: {info['status']}")
            if 'info' in info:
                lock_info = info['info']
                print(f"    PID: {lock_info.get('pid', 'unknown')}")
                print(f"    Started: {lock_info.get('start_time', 'unknown')}")
    
    elif args.test:
        lock_name = args.lock_name or "test-lock"
        logger.info(f"Testing lock: {lock_name}")
        
        with lock_manager.get_lock(lock_name, 10):
            logger.info("Lock acquired for 5 seconds...")
            time.sleep(5)
        
        logger.info("Lock test completed")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
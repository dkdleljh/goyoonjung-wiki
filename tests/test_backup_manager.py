#!/usr/bin/env python3
"""Tests for backup_manager module."""
from __future__ import annotations

import os
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

import scripts.backup_manager as backup_manager


def test_backup_manager_init(tmp_path):
    """Test BackupManager initialization with default and custom parameters."""
    # Test default parameters
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))
    assert manager.backup_dir == tmp_path
    assert manager.max_size_bytes == 500 * 1024 * 1024
    assert manager.max_files == 30

    # Test custom parameters
    manager2 = backup_manager.BackupManager(
        backup_dir=str(tmp_path),
        max_size_mb=100,
        max_files=10
    )
    assert manager2.max_size_bytes == 100 * 1024 * 1024
    assert manager2.max_files == 10


def test_calculate_file_hash(tmp_path):
    """Test SHA256 hash calculation."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Calculate hash
    file_hash = manager.calculate_file_hash(test_file)

    # Verify hash is a valid SHA256 string (64 characters)
    assert len(file_hash) == 64
    assert file_hash.isalnum()  # SHA256 hex is alphanumeric


def test_calculate_file_hash_consistency(tmp_path):
    """Test that hash calculation is consistent for same content."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    test_file = tmp_path / "test.txt"
    test_file.write_text("Consistent content")

    hash1 = manager.calculate_file_hash(test_file)
    hash2 = manager.calculate_file_hash(test_file)

    assert hash1 == hash2


def test_calculate_file_hash_different_content(tmp_path):
    """Test that different content produces different hashes."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    file1 = tmp_path / "test1.txt"
    file2 = tmp_path / "test2.txt"

    file1.write_text("Content A")
    file2.write_text("Content B")

    hash1 = manager.calculate_file_hash(file1)
    hash2 = manager.calculate_file_hash(file2)

    assert hash1 != hash2


def test_find_duplicate_files_empty(tmp_path):
    """Test finding duplicates in empty directory."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))
    duplicates = manager.find_duplicate_files()
    assert duplicates == []


def test_find_duplicate_files_no_duplicates(tmp_path):
    """Test finding duplicates when no duplicates exist."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create unique files
    (tmp_path / "backup1_2026-02-15_1000.tar.gz").write_bytes(b"content1")
    (tmp_path / "backup2_2026-02-15_1100.tar.gz").write_bytes(b"content2")

    duplicates = manager.find_duplicate_files()
    assert duplicates == []


def test_find_duplicate_files_with_duplicates(tmp_path):
    """Test finding actual duplicate files."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create duplicate files
    content = b"duplicate content"
    (tmp_path / "backup1_2026-02-15_1000.tar.gz").write_bytes(content)
    (tmp_path / "backup2_2026-02-15_1100.tar.gz").write_bytes(content)

    duplicates = manager.find_duplicate_files()
    assert len(duplicates) == 1


def test_get_backup_info_from_filename(tmp_path):
    """Test extracting datetime from backup filename."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create a test file with proper name
    test_file = tmp_path / "goyoonjung-wiki_2026-02-15_1030.tar.gz"
    test_file.write_bytes(b"test")

    dt = manager.get_backup_info(test_file)
    assert isinstance(dt, datetime)
    assert dt.year == 2026
    assert dt.month == 2
    assert dt.day == 15


def test_get_backup_info_invalid_filename(tmp_path):
    """Test handling of invalid filename format."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create file with invalid name
    test_file = tmp_path / "invalid_name.tar.gz"
    test_file.write_bytes(b"test")

    result = manager.get_backup_info(test_file)
    # Should return mtime (float) on failure
    assert isinstance(result, float)


def test_cleanup_old_backups_nonexistent_dir(tmp_path):
    """Test cleanup when backup directory doesn't exist."""
    nonexistent = tmp_path / "nonexistent"
    manager = backup_manager.BackupManager(backup_dir=str(nonexistent))

    # Should not raise error
    removed, size_freed = manager.cleanup_old_backups()
    assert removed == 0
    assert size_freed == 0


def test_cleanup_old_backups_with_files(tmp_path):
    """Test cleanup with actual backup files."""
    manager = backup_manager.BackupManager(
        backup_dir=str(tmp_path),
        max_files=2,
        max_size_mb=1  # 1MB limit
    )

    # Create backup files with different timestamps
    (tmp_path / "goyoonjung-wiki_2026-02-15_1000.tar.gz").write_bytes(b"a" * 1024)
    (tmp_path / "goyoonjung-wiki_2026-02-14_1000.tar.gz").write_bytes(b"b" * 1024)
    (tmp_path / "goyoonjung-wiki_2026-02-13_1000.tar.gz").write_bytes(b"c" * 1024)

    removed, size_freed = manager.cleanup_old_backups()

    # Should keep only 2 newest files
    remaining = list(tmp_path.glob("*.tar.gz"))
    assert len(remaining) == 2
    # Most recent should be kept (Feb 15)
    filenames = [f.name for f in remaining]
    assert any("2026-02-15" in f for f in filenames)


def test_cleanup_removes_duplicates(tmp_path):
    """Test that cleanup removes duplicate files."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path), max_files=10)

    # Create duplicate content
    content = b"duplicate"
    (tmp_path / "backup1_2026-02-15_1000.tar.gz").write_bytes(content)
    (tmp_path / "backup2_2026-02-15_1100.tar.gz").write_bytes(content)

    manager.cleanup_old_backups()

    # Should keep only one of the duplicates
    remaining = list(tmp_path.glob("*.tar.gz"))
    assert len(remaining) == 1


def test_create_incremental_backup(tmp_path):
    """Test creating incremental backup."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create a test file to backup
    (tmp_path.parent / "pages").mkdir(exist_ok=True)
    (tmp_path.parent / "pages" / "test.md").write_text("# Test")

    backup_path, created = manager.create_incremental_backup()

    assert created is True
    assert backup_path.exists()
    assert backup_path.suffix == ".gz"


def test_create_incremental_backup_already_exists(tmp_path):
    """Test that backup skips if already exists today."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    today = datetime.now().strftime("%Y-%m-%d")

    # Create existing backup
    existing = tmp_path / f"goyoonjung-wiki_{today}_1000.tar.gz"
    existing.write_bytes(b"existing")

    backup_path, created = manager.create_incremental_backup()

    # Should not create new backup
    assert created is False
    assert backup_path.name == existing.name


def test_create_cleanup_report(tmp_path):
    """Test cleanup report generation."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    manager.create_cleanup_report(removed_count=5, size_freed=1024*1024, kept_count=10, kept_size=512*1024)

    report_path = tmp_path / "cleanup_report.md"
    assert report_path.exists()

    content = report_path.read_text()
    assert "Files removed: 5" in content
    assert "Space freed: 1.0 MB" in content
    assert "Files kept: 10" in content


def test_get_directory_size(tmp_path):
    """Test directory size calculation."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))

    # Create test files
    (tmp_path / "file1.txt").write_bytes(b"a" * 100)
    (tmp_path / "file2.txt").write_bytes(b"b" * 200)

    total_size = manager.get_directory_size()
    assert total_size == 300


def test_get_directory_size_empty(tmp_path):
    """Test directory size for empty directory."""
    manager = backup_manager.BackupManager(backup_dir=str(tmp_path))
    total_size = manager.get_directory_size()
    assert total_size == 0


def test_backup_manager_with_custom_backup_dir(tmp_path):
    """Test BackupManager with Path object as backup_dir."""
    custom_dir = tmp_path / "custom_backups"
    custom_dir.mkdir()

    manager = backup_manager.BackupManager(backup_dir=custom_dir)
    assert manager.backup_dir == custom_dir


def test_backup_cleanup_with_size_limit(tmp_path):
    """Test cleanup respects size limit."""
    manager = backup_manager.BackupManager(
        backup_dir=str(tmp_path),
        max_files=10,
        max_size_mb=0  # Very small limit
    )

    # Create files that exceed size limit
    for i in range(5):
        (tmp_path / f"goyoonjung-wiki_2026-02-{15-i:02d}_1000.tar.gz").write_bytes(b"x" * 1024 * 100)

    removed, size_freed = manager.cleanup_old_backups()

    # Should remove some files to respect limit
    remaining = list(tmp_path.glob("*.tar.gz"))
    assert len(remaining) < 5

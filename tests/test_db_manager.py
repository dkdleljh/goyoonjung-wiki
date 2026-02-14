#!/usr/bin/env python3
"""Tests for db_manager module."""
from __future__ import annotations

import scripts.db_manager as db


def test_get_db_connection_creates_dir(tmp_path):
    """Test that get_db_connection creates parent directory if needed."""
    db.DB_PATH = tmp_path / 'test.db'
    db.DB_PATH.parent.mkdir(exist_ok=True)
    db.DB_PATH.parent.rmdir()  # Remove the directory

    conn = db.get_db_connection()
    assert db.DB_PATH.parent.exists()
    conn.close()


def test_init_db_creates_tables(tmp_path):
    """Test that init_db creates the required tables."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()

    conn = db.get_db_connection()
    cursor = conn.cursor()

    # Check seen_urls table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seen_urls'")
    assert cursor.fetchone() is not None

    # Check kv_store table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kv_store'")
    assert cursor.fetchone() is not None

    conn.close()


def test_is_url_seen_returns_false_for_new_url(tmp_path):
    """Test is_url_seen returns False for unseen URLs."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()

    result = db.is_url_seen("https://example.com")
    assert result is False


def test_is_url_seen_returns_true_for_existing_url(tmp_path):
    """Test is_url_seen returns True for seen URLs."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()
    db.add_seen_url("https://example.com", "test")

    result = db.is_url_seen("https://example.com")
    assert result is True


def test_add_seen_url_inserts_new_url(tmp_path):
    """Test add_seen_url inserts new URL correctly."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()

    db.add_seen_url("https://new-url.com", "google_news")

    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT url, source FROM seen_urls WHERE url = ?", ("https://new-url.com",))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "https://new-url.com"
    assert row[1] == "google_news"


def test_add_seen_url_ignores_duplicates(tmp_path):
    """Test add_seen_url does not raise on duplicate."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()

    # Should not raise
    db.add_seen_url("https://dup.com", "test")
    db.add_seen_url("https://dup.com", "test")  # Duplicate


def test_migrate_from_txt_imports_urls(tmp_path):
    """Test migrate_from_txt imports URLs from text file."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()

    txt_file = tmp_path / "urls.txt"
    txt_file.write_text("https://url1.com\nhttps://url2.com\n\nhttps://url3.com\n")

    count = db.migrate_from_txt(str(txt_file))
    assert count == 3

    assert db.is_url_seen("https://url1.com")
    assert db.is_url_seen("https://url2.com")
    assert db.is_url_seen("https://url3.com")


def test_migrate_from_txt_returns_zero_for_missing_file(tmp_path):
    """Test migrate_from_txt returns 0 for non-existent file."""
    db.DB_PATH = tmp_path / 'test.db'

    count = db.migrate_from_txt(str(tmp_path / "nonexistent.txt"))
    assert count == 0


def test_connection_uses_row_factory(tmp_path):
    """Test that connections use sqlite3.Row factory."""
    db.DB_PATH = tmp_path / 'test.db'
    db.init_db()
    db.add_seen_url("https://rowtest.com", "test")

    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seen_urls WHERE url = ?", ("https://rowtest.com",))
    row = cursor.fetchone()
    conn.close()

    # sqlite3.Row supports dict-like access
    assert row["url"] == "https://rowtest.com"
    assert row["source"] == "test"

#!/usr/bin/env python3
"""SQLite Database Manager for Wiki Automation.
- Replaces simple text files (seen-urls.txt) with a structured DB.
- Tables:
  - seen_urls: Tracks collected URLs to prevent duplicates.
  - news_archive (Future): Store full parsed news items.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / 'data' / 'wiki.db'
try:
    from .normalize_url import norm as normalize_url  # type: ignore[attr-defined]
except Exception:
    from normalize_url import norm as normalize_url  # noqa: E402


def get_db_connection() -> sqlite3.Connection:
    """Ensure DB exists and return connection."""
    if not os.path.exists(DB_PATH.parent):
        os.makedirs(DB_PATH.parent)

    # Use a longer SQLite busy timeout to reduce transient "database is locked" issues
    # during cron bursts.
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
    except Exception:
        pass
    return conn


def init_db() -> None:
    """Initialize database with required tables."""
    conn = get_db_connection()
    c = conn.cursor()

    # Table: seen_urls
    c.execute('''
        CREATE TABLE IF NOT EXISTS seen_urls (
            url TEXT PRIMARY KEY,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT
        )
    ''')

    # Table: key_value_store (for generic metadata like 'last_wiki_revision')
    c.execute('''
        CREATE TABLE IF NOT EXISTS kv_store (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS url_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            norm_url TEXT,
            url TEXT,
            grade TEXT,
            decision TEXT,
            source TEXT,
            is_duplicate INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS url_candidates (
            norm_url TEXT PRIMARY KEY,
            url TEXT,
            grade TEXT,
            lane TEXT,
            title TEXT,
            source TEXT,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            seen_count INTEGER DEFAULT 1
        )
    ''')

    # Indexes (critical for daily KPI queries; avoid full table scans)
    c.execute("CREATE INDEX IF NOT EXISTS idx_seen_urls_first_seen_at ON seen_urls(first_seen_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_url_events_created_at ON url_events(created_at)")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_url_events_created_decision_dup_grade "
        "ON url_events(created_at, decision, is_duplicate, grade)"
    )

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

def is_url_seen(url: str) -> bool:
    nurl = normalize_url(url)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM seen_urls WHERE url = ?', (nurl,))
    result = c.fetchone()
    conn.close()
    return result is not None


def add_seen_url(url: str, source: str = 'unknown') -> bool:
    nurl = normalize_url(url)
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO seen_urls (url, source) VALUES (?, ?)', (nurl, source))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error in add_seen_url: {e}")
        return False


def record_url_event(
    url: str,
    grade: str,
    decision: str,
    source: str,
    is_duplicate: bool = False,
) -> bool:
    nurl = normalize_url(url)
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO url_events (norm_url, url, grade, decision, source, is_duplicate)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (nurl, url, grade, decision, source, int(bool(is_duplicate))),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error in record_url_event: {e}")
        return False


def add_or_update_candidate(
    url: str,
    grade: str,
    lane: str,
    title: str,
    source: str,
) -> bool:
    nurl = normalize_url(url)
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO url_candidates (norm_url, url, grade, lane, title, source)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(norm_url) DO UPDATE SET
                url=excluded.url,
                grade=excluded.grade,
                lane=excluded.lane,
                title=excluded.title,
                source=excluded.source,
                last_seen_at=CURRENT_TIMESTAMP,
                seen_count=url_candidates.seen_count + 1
            ''',
            (nurl, url, grade, lane, title, source),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error in add_or_update_candidate: {e}")
        return False


def list_candidates(lane: str | None = None, limit: int = 300) -> list[sqlite3.Row]:
    conn = get_db_connection()
    c = conn.cursor()
    if lane:
        c.execute(
            '''
            SELECT norm_url, url, grade, lane, title, source, first_seen_at, last_seen_at, seen_count
            FROM url_candidates
            WHERE lane = ?
            ORDER BY last_seen_at DESC
            LIMIT ?
            ''',
            (lane, limit),
        )
    else:
        c.execute(
            '''
            SELECT norm_url, url, grade, lane, title, source, first_seen_at, last_seen_at, seen_count
            FROM url_candidates
            ORDER BY last_seen_at DESC
            LIMIT ?
            ''',
            (limit,),
        )
    rows = c.fetchall()
    conn.close()
    return rows


def migrate_from_txt(txt_path: str) -> int:
    if not os.path.exists(txt_path):
        logger.warning(f"Migration file not found: {txt_path}")
        return 0

    count = 0
    with open(txt_path, encoding='utf-8') as f:
        conn = get_db_connection()
        c = conn.cursor()
        for line in f:
            url = line.strip()
            if not url:
                continue
            nurl = normalize_url(url)
            try:
                c.execute('INSERT OR IGNORE INTO seen_urls (url, source) VALUES (?, ?)', (nurl, 'migration'))
                if c.rowcount > 0:
                    count += 1
            except sqlite3.Error as e:
                logger.debug(f"Skipping URL due to error: {url} - {e}")
        conn.commit()
        conn.close()
    logger.info(f"Migrated {count} URLs from {txt_path}")
    return count

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")

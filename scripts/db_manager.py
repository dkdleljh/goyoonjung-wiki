#!/usr/bin/env python3
"""SQLite Database Manager for Wiki Automation.
- Replaces simple text files (seen-urls.txt) with a structured DB.
- Tables:
  - seen_urls: Tracks collected URLs to prevent duplicates.
  - news_archive (Future): Store full parsed news items.
"""

from __future__ import annotations

import logging
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / 'data' / 'wiki.db'


def get_db_connection() -> sqlite3.Connection:
    """Ensure DB exists and return connection."""
    if not os.path.exists(DB_PATH.parent):
        os.makedirs(DB_PATH.parent)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

def is_url_seen(url: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM seen_urls WHERE url = ?', (url,))
    result = c.fetchone()
    conn.close()
    return result is not None


def add_seen_url(url: str, source: str = 'unknown') -> bool:
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO seen_urls (url, source) VALUES (?, ?)', (url, source))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error in add_seen_url: {e}")
        return False


def migrate_from_txt(txt_path: str) -> int:
    if not os.path.exists(txt_path):
        logger.warning(f"Migration file not found: {txt_path}")
        return 0
        
    count = 0
    with open(txt_path, 'r', encoding='utf-8') as f:
        conn = get_db_connection()
        c = conn.cursor()
        for line in f:
            url = line.strip()
            if not url:
                continue
            try:
                c.execute('INSERT OR IGNORE INTO seen_urls (url, source) VALUES (?, ?)', (url, 'migration'))
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

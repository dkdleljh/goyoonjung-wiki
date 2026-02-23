#!/usr/bin/env python3
"""Generate daily KPI report from URL event telemetry."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import db_manager

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "pages" / "kpi-report.md"
DB = BASE / "data" / "wiki.db"


def q1(cur: sqlite3.Cursor, sql: str) -> int:
    cur.execute(sql)
    row = cur.fetchone()
    return int(row[0] if row and row[0] is not None else 0)


def main() -> int:
    db_manager.init_db()
    if not DB.exists():
        return 0
    # Use a longer busy timeout; this script can run concurrently with collectors.
    con = sqlite3.connect(DB, timeout=30)
    con.execute("PRAGMA busy_timeout = 30000")
    cur = con.cursor()

    # IMPORTANT: avoid date(created_at) wrappers; they defeat indexes and can cause
    # full scans as the DB grows.
    day_start = "datetime('now','localtime','start of day')"
    day_end = "datetime('now','localtime','start of day','+1 day')"

    new_urls = q1(
        cur,
        f"SELECT count(*) FROM seen_urls WHERE first_seen_at >= {day_start} AND first_seen_at < {day_end}",
    )
    landed_urls = q1(
        cur,
        f"""
        SELECT count(*) FROM url_events
        WHERE created_at >= {day_start} AND created_at < {day_end}
          AND decision = 'landed'
        """ ,
    )
    total_events = q1(cur, f"SELECT count(*) FROM url_events WHERE created_at >= {day_start} AND created_at < {day_end}")
    duplicate_events = q1(
        cur,
        f"""
        SELECT count(*) FROM url_events
        WHERE created_at >= {day_start} AND created_at < {day_end}
          AND is_duplicate = 1
        """ ,
    )
    duplicate_rate = (duplicate_events / total_events) if total_events else 0.0

    cur.execute(
        f"""
        SELECT grade, count(*)
        FROM url_events
        WHERE created_at >= {day_start} AND created_at < {day_end}
          AND is_duplicate = 0
          AND decision IN ('landed', 'queue', 'pool')
        GROUP BY grade
        ORDER BY CASE grade WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 ELSE 4 END
        """
    )
    by_grade = {str(g): int(c) for g, c in cur.fetchall()}
    con.close()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# KPI Report (auto)",
        "",
        f"> Updated: {now} (Asia/Seoul)",
        "",
        "## Daily Metrics",
        f"- new_urls: {new_urls}",
        f"- landed_urls: {landed_urls}",
        f"- duplicate_rate: {duplicate_rate:.2%} ({duplicate_events}/{total_events})",
        "- verified_urls_by_grade:",
        f"  - S: {by_grade.get('S', 0)}",
        f"  - A: {by_grade.get('A', 0)}",
        f"  - B: {by_grade.get('B', 0)}",
    ]
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(
        "generate_kpi_report: "
        f"new_urls={new_urls} landed_urls={landed_urls} duplicate_rate={duplicate_rate:.2%}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


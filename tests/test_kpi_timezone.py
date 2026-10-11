import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scripts import generate_kpi_report as report


def test_daily_metrics_use_korean_day_for_utc_database(tmp_path, monkeypatch):
    database = tmp_path / 'wiki.db'
    output = tmp_path / 'report.md'
    monkeypatch.setattr(report, 'DB', database)
    monkeypatch.setattr(report, 'OUT', output)
    monkeypatch.setattr(report.db_manager, 'init_db', lambda: None)
    midnight = datetime.now(ZoneInfo('Asia/Seoul')).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    con = sqlite3.connect(database)
    con.executescript('CREATE TABLE seen_urls(first_seen_at TEXT); CREATE TABLE url_events(created_at TEXT, decision TEXT, is_duplicate INTEGER, grade TEXT);')
    for instant in (midnight - timedelta(seconds=1), midnight + timedelta(seconds=1)):
        stamp = instant.strftime('%Y-%m-%d %H:%M:%S')
        con.execute('INSERT INTO seen_urls VALUES (?)', (stamp,))
        con.execute("INSERT INTO url_events VALUES (?, 'landed', 0, 'S')", (stamp,))
    con.commit()
    con.close()
    assert report.main() == 0
    assert '- new_urls: 1' in output.read_text()
    assert '- landed_urls: 1' in output.read_text()

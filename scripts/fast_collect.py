"""Frequent ingestion with independently scheduled enrichment and durable metrics."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from official_evidence import load
from run_telemetry import record, report
from source_transport import atomic_write

BASE = Path(__file__).resolve().parents[1]
# Seconds between attempts. Failed tasks retry on the next fast tick.
TASKS = [
    ('auto_collect_google_news.py', 300, 100),
    ('auto_collect_youtube_feeds.py', 300, 170),
    ('auto_collect_google_news_sites.py', 900, 120),
    ('auto_collect_google_news_queries.py', 900, 120),
    ('auto_collect_google_news_queries_i18n.py', 1800, 120),
    ('auto_collect_magazine_rss.py', 1800, 170),
    ('official_evidence.py', 600, 180),
    ('review_candidates.py', 900, 150),
    ('archive_backfill.py', 3600, 180),
    ('youtube_archive.py', 3600, 180),
    ('check_links.py', 21600, 300),
]
ENRICH = ['sync_media_watch_sources.py', 'reconcile_evidence.py', 'extract_facts_from_markdown.py',
          'auto_detect_future_works.py', 'audit_fact_conflicts.py', 'rebuild_work_link_candidates.py',
          'render_pages_from_facts.py', 'rebuild_works_year_index.py']


def due_tasks(started: float, state: dict) -> list:
    # Use start times and 30 seconds of timer jitter allowance, not completion times.
    return [(name, interval, timeout) for name, interval, timeout in TASKS
            if started - state.get(name, {}).get('last_attempt', 0) >=
            (300 if state.get(name, {}).get('returncode', 0) else interval) - 30]


def main() -> int:
    started = time.time()
    state_path = BASE/'data/reports/fast-task-state.json'
    state = load(state_path, {})
    steps = []
    env = {**os.environ, 'TZ': 'Asia/Seoul', 'COLLECT_ONLY': '1', 'MAX_SITES': '4',
           'MAX_QUERIES': '4', 'MAX_QUERIES_I18N': '2', 'MAX_URLS': '100'}
    # Schedule from attempt start, so a 30-second run does not turn a 5-minute timer
    # into a 10-minute poll. Allow timer jitter; failed tasks retry next tick.
    due = due_tasks(started, state)
    essentials = [task for task in due if task[0] in {TASKS[0][0], TASKS[1][0], 'official_evidence.py'}]
    extras = sorted([task for task in due if task not in essentials],
                    key=lambda task: state.get(task[0], {}).get('last_attempt', 0))[:2]
    for name, _interval, timeout in essentials + extras:
        stamp = time.time()
        log = BASE/'.locks'/f'fast-{name}.log'
        log.parent.mkdir(exist_ok=True)
        try:
            with log.open('w') as output:
                rc = subprocess.run([sys.executable, str(BASE/'scripts'/name)], cwd=BASE, env=env,
                                    stdout=output, stderr=subprocess.STDOUT, timeout=timeout, check=False).returncode
        except subprocess.TimeoutExpired:
            rc = 124
        state[name] = {**state.get(name, {}), 'last_attempt': stamp, 'returncode': rc}
        if rc == 0:
            state[name]['last_success'] = time.time()
        atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2)+'\n')
        steps.append({'name': name, 'returncode': rc, 'duration_seconds': round(time.time()-stamp, 2)})
        print(json.dumps(steps[-1]), flush=True)
    for name in ENRICH:
        try:
            rc = subprocess.run([sys.executable, str(BASE/'scripts'/name)], cwd=BASE, env=env,
                                timeout=45, check=False).returncode
        except subprocess.TimeoutExpired:
            rc = 124
        steps.append({'name': name, 'returncode': rc})
    core = [step for step in steps if step['name'] in {TASKS[0][0], TASKS[1][0], 'official_evidence.py'}]
    broken_transform = any(step['returncode'] for step in steps if step['name'] in ENRICH)
    rc = 2 if broken_transform or (core and all(step['returncode'] for step in core)) else int(any(step['returncode'] for step in steps))
    record('fast', started, rc, steps)
    report()
    return rc


if __name__ == '__main__':
    raise SystemExit(main())

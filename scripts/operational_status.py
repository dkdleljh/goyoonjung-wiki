#!/usr/bin/env python3
"""Read-only automation health. Report generation never refreshes collection age."""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent.parent
SEOUL = ZoneInfo("Asia/Seoul")
CORE_COLLECTORS = {'auto_collect_google_news.py', 'auto_collect_youtube_feeds.py'}
# Exit 1 is a documented partial collection result. Crashes/timeouts and unknown
# steps still require attention; this does not turn arbitrary failures green.
OPTIONAL_COLLECTORS = {'official_evidence.py', 'archive_backfill.py', 'youtube_archive.py',
                       'review_candidates.py', 'check_links.py', 'auto_collect_google_news_sites.py',
                       'auto_collect_google_news_queries.py', 'auto_collect_google_news_queries_i18n.py',
                       'auto_collect_magazine_rss.py'}


def alert_status(base: Path = BASE, now: datetime | None = None) -> dict:
    """Separate service outages from recorded, noncritical source warnings."""
    now = now or datetime.now(SEOUL)
    errors, warnings = [], []
    try:
        heartbeat = json.loads((base / 'data/reports/heartbeat.json').read_text())
        age = (now - datetime.fromisoformat(heartbeat['timestamp'])).total_seconds()
        if not -300 <= age <= 1800:
            errors.append(f'Collector heartbeat is stale or in the future: {age:.0f}s')
        if heartbeat['status'] not in {'success', 'partial'}:
            errors.append(f'Collector outcome: {heartbeat["status"]}')
        steps = {step['name']: step for step in heartbeat['steps']}
        state = json.loads((base / 'data/reports/fast-task-state.json').read_text())
        for name in sorted(CORE_COLLECTORS):
            task = state.get(name, {})
            last_success = task.get('last_success')
            if last_success is None or not -300 <= now.timestamp() - last_success <= 1800:
                errors.append(f'No recent successful core collection: {name}')
            if steps.get(name, task).get('returncode', 1) != 0:
                errors.append(f'Core collector failed: {name}')
        for name, step in steps.items():
            rc = step['returncode']
            if rc:
                message = f'{name} exited {rc}'
                if name in OPTIONAL_COLLECTORS and rc == 1 and not step.get('crashed'):
                    warnings.append(message)
                elif name not in CORE_COLLECTORS:
                    errors.append(message)
        if heartbeat['status'] == 'partial' and not (warnings or errors):
            errors.append('Partial collection has no diagnostic steps')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'Invalid collection telemetry: {exc}')
    return {'status': 'failure' if errors else 'partial' if warnings else 'success',
            'errors': errors, 'warnings': warnings}


def news_runs(base: Path = BASE) -> list[dict]:
    runs = []
    for path in sorted((base / "news").glob("????-??-??.md")):
        text = path.read_text(encoding="utf-8")
        stamp = re.search(r"^- 실행:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)", text, re.M)
        result = re.search(r"^- 결과:\s*(.+)$", text, re.M)
        note = re.search(r"^- 메모:\s*(.+)$", text, re.M)
        if not stamp or not result:
            continue
        try:
            at = datetime.fromisoformat(stamp[1]).replace(tzinfo=SEOUL)
        except ValueError:
            continue
        state = {"성공": "success", "실패": "failure", "부분성공": "partial", "진행중": "running"}.get(result[1].strip(), "unknown")
        message = note[1].strip() if note else ""
        # Legacy pipelines sometimes stamped success despite failed/skipped collectors.
        if state == "success" and re.search(r":(?:FAIL|TIMEOUT|SKIP|NOTE)\b", message):
            state = "partial"
        runs.append({"timestamp": at.isoformat(), "status": state, "message": message,
                     "source": path.relative_to(base).as_posix(), "duration_seconds": None})
    heartbeat = base / 'data/reports/heartbeat.json'
    try:
        fast = json.loads(heartbeat.read_text())
        datetime.fromisoformat(fast['timestamp'])
        runs.append({'timestamp':fast['timestamp'], 'status':fast['status'],
                     'message':'frequent collector: '+', '.join(step['name']+(' OK' if step['returncode'] == 0 else ' FAIL') for step in fast.get('steps', [])),
                     'source':'data/reports/heartbeat.json', 'duration_seconds':fast['duration_seconds']})
    except (OSError, ValueError, KeyError):
        pass
    return sorted(runs, key=lambda x: datetime.fromisoformat(x['timestamp']))


def health(base: Path = BASE, now: datetime | None = None, max_age_hours: float = 8) -> dict:
    now = now or datetime.now(SEOUL)
    runs = news_runs(base)
    if not runs:
        return {"status": "unknown", "last_run": None, "age_hours": None, "reason": "no recorded pipeline run"}
    latest = runs[-1]
    at = datetime.fromisoformat(latest["timestamp"])
    age = (now - at).total_seconds() / 3600
    state = latest["status"]
    if age < -5 / 60:
        state = "invalid_timestamp"
    elif age > max_age_hours:
        state = "stale"
    elif state == "running" and now - at > timedelta(minutes=40):
        state = "stalled"
    return {"status": state, "last_run": latest["timestamp"], "age_hours": round(age, 2),
            "source": latest["source"], "recorded_result": latest["status"],
            "reason": latest["message"], "max_age_hours": max_age_hours}


def collectors(base: Path = BASE) -> list[dict]:
    runs = news_runs(base)
    names = {"collect", "gnews", "gnews-sites", "gnews-queries", "mag-rss", "portal-news", "sched", "agency", "ency"}
    output = []
    freshness = health(base)["status"]
    for name in sorted(names):
        observations = []
        for run in runs:
            match = re.search(r"(?:^|[, (])" + re.escape(name) + r":(OK|FAIL|SKIP|TIMEOUT|NOTE)\b", run["message"])
            if match:
                observations.append((run, match[1]))
        last = observations[-1] if observations else None
        output.append({"name": name, "status": ("success" if last[1] == "OK" else "failure") if last else "unknown",
                       "freshness": freshness, "last_run": last[0]["timestamp"] if last else None,
                       "last_duration": None,
                       "success_rate": round(100 * sum(s == "OK" for _, s in observations) / len(observations), 2) if observations else None,
                       "error_count": sum(s in {"FAIL", "TIMEOUT"} for _, s in observations) if observations else None})
    return output


def metrics(base: Path = BASE) -> dict:
    runs = news_runs(base)
    completed = [r for r in runs if r["status"] in {"success", "failure", "partial"}]
    successful = [r for r in completed if r["status"] == "success"]
    today = datetime.now(SEOUL).date().isoformat()
    history_path = base / 'data/reports/run-history.json'
    if history_path.exists():
        try:
            measured = json.loads(history_path.read_text())
        except ValueError:
            measured = []
        if measured:
            from statistics import mean
            return {"avg_execution_time": round(mean(r['duration_seconds'] for r in measured), 2),
                    "uptime_percentage": None,
                    "success_rate": round(100 * sum(r['status'] == 'success' for r in measured)/len(measured), 2),
                    "total_runs_today": sum(datetime.fromisoformat(r['timestamp']).astimezone(SEOUL).date().isoformat() == today for r in measured),
                    "sample_count": len(measured), "sample_basis": "measured individual runs",
                    "last_successful_run": next((r['timestamp'] for r in reversed(measured) if r['status'] == 'success'), None)}
    return {"avg_execution_time": None, "uptime_percentage": None,
            "success_rate": round(100 * len(successful) / len(completed), 2) if completed else None,
            "total_runs_today": sum(r["timestamp"].startswith(today) for r in runs),
            "last_successful_run": successful[-1]["timestamp"] if successful else None,
            "sample_count": len(completed), "sample_basis": "latest recorded run per news day"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--alerts', action='store_true', help='Fail on service outages; retain noncritical source warnings')
    args = parser.parse_args()
    if args.alerts:
        result = alert_status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            for level, messages in [('error', result['errors']), ('warning', result['warnings'])]:
                for message in messages:
                    escaped = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
                    print(f'::{level}::{escaped}')
        return int(bool(result['errors']))
    result = health()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

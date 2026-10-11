#!/usr/bin/env python3
"""Recover missed/failed collections and retry publication without human input."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from operational_status import health

BASE = Path(__file__).resolve().parent.parent


def collection_due(state: dict, last_attempt: float, now: float) -> bool:
    # A partial source outage retries hourly; a crash/missing run retries next tick.
    status = state.get("recorded_result", state["status"])
    interval = {"success": 21600, "partial": 3600}.get(status, 900)
    stamp = state.get("last_run")
    completed = datetime.fromisoformat(stamp).timestamp() if stamp else 0
    # A future/corrupt clock must not suppress collection indefinitely.
    previous = max(t for t in (0, last_attempt, completed) if t <= now)
    return now - previous >= interval


def tick() -> int:
    target = BASE / ".locks/automation-tick.json"
    target.parent.mkdir(exist_ok=True)
    try:
        prior = json.loads(target.read_text())
    except (OSError, ValueError):
        prior = {}
    now = time.time()
    state = health(BASE)
    due = collection_due(state, prior.get("collection_attempt", 0), now)
    command = ["bash", "scripts/collect_and_sync_website.sh"] if due else [sys.executable, "scripts/publish_website_content.py"]
    report = {"started_at": now, "stage": "collection_and_publication" if due else "publication",
              "collection_attempt": now if due else prior.get("collection_attempt", 0), "status": "running"}

    def save() -> None:
        temp = target.with_suffix('.tmp')
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temp.replace(target)
    save()
    print(f"Automation tick: {report['stage']}", flush=True)
    result = subprocess.run(command, cwd=BASE, env={**os.environ, "COLLECT_ONLY": "1"}, check=False)
    if result.returncode == 75:
        report["collection_attempt"] = prior.get("collection_attempt", 0)
    report.update(status="completed" if result.returncode == 0 else "busy" if result.returncode == 75 else "partial_or_failed", returncode=result.returncode,
                  finished_at=time.time(), collection=health(BASE))
    save()
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(tick())

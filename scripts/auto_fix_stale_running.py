#!/usr/bin/env python3
"""Auto-fix stale '진행중' status in today's news log.

Problem:
- SIGKILL can abort runs without reaching mark_news_status.sh 실패.
- That leaves news/YYYY-MM-DD.md stuck at 결과: 진행중.

This script checks:
- If summary result is 진행중 and the run timestamp is older than STALE_SECONDS
- AND no active lock directory exists (.locks/lock)
Then it marks the status as 실패 with a short note.

Best-effort; never fails the pipeline.
"""

from __future__ import annotations

import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LOCK_PATH = BASE / ".locks" / "lock"
NEWS = BASE / "news" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
MARK = BASE / "scripts" / "mark_news_status.sh"

STALE_SECONDS = 45 * 60
TZ = "Asia/Seoul"


def parse_run_epoch(text: str) -> int:
    # expects line: - 실행: YYYY-MM-DD HH:MM (Asia/Seoul)
    for ln in text.splitlines():
        if ln.startswith("- 실행:"):
            raw = ln.split(":", 1)[1].strip()
            # strip (TZ)
            raw = raw.split("(", 1)[0].strip()
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
                return int(dt.timestamp())
            except Exception:
                return 0
    return 0


def parse_result(text: str) -> str:
    for ln in text.splitlines():
        if ln.startswith("- 결과:"):
            return ln.split(":", 1)[1].strip()
    return ""


def main() -> int:
    try:
        if not NEWS.exists() or not MARK.exists():
            return 0
        txt = NEWS.read_text(encoding="utf-8", errors="ignore")
        result = parse_result(txt)
        if result != "진행중":
            return 0

        run_epoch = parse_run_epoch(txt)
        if run_epoch <= 0:
            return 0

        age = int(time.time()) - run_epoch
        if age <= STALE_SECONDS:
            return 0

        # if lock exists, treat as still running
        if LOCK_PATH.exists():
            return 0

        note = f"auto-fix: stale running detected (age={age}s)"
        subprocess.run([str(MARK), "실패", note], cwd=str(BASE), check=False)
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

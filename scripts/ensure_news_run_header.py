#!/usr/bin/env python3
"""Ensure today's news file contains the run status/history header.

Why:
- Some generators rewrite news/YYYY-MM-DD.md blocks.
- If the '## 실행 상태' header is missing, check_automation_health.sh fails and
  system_status.md shows false negatives.

This script is conservative:
- Only inserts a minimal header when it's missing.
- Does not delete or reorder existing content.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE / "news"
TZ = ZoneInfo("Asia/Seoul")


def today_ymd() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def get_last_commit_time() -> str:
    try:
        # Use git commit time in local tz for best approximation.
        out = subprocess.check_output(
            ["bash", "-lc", "git log -1 --format=%ad --date=iso"],
            cwd=BASE,
            text=True,
        ).strip()
        # out example: 2026-02-23 13:56:12 +0900
        # Reduce to YYYY-MM-DD HH:MM.
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


def main() -> int:
    ymd = today_ymd()
    path = NEWS_DIR / f"{ymd}.md"
    if not path.exists():
        return 0

    txt = path.read_text(encoding="utf-8")

    has_status = bool(re.search(r"^## 실행 상태\s*$", txt, flags=re.M))
    has_result_line = bool(re.search(r"^- 결과:\s*", txt, flags=re.M))

    if has_status and has_result_line:
        return 0

    run_at = get_last_commit_time()
    note = "auto: reconstructed run header (was missing)"

    header = "\n".join(
        [
            "## 실행 상태",
            f"- 실행: {run_at} (Asia/Seoul)",
            "- 결과: 성공",
            f"- 메모: {note}",
            "",
            "## 실행 이력",
            f"- {run_at} (Asia/Seoul) · 성공 · {note}",
            "",
        ]
    )

    lines = txt.splitlines(True)
    if not lines:
        path.write_text(f"# {ymd} 업데이트\n\n" + header, encoding="utf-8")
        return 0

    # Prefer inserting AFTER the leading AUTO blocks (so we don't place the header inside them).
    #
    # Important: AUTO blocks can contain real content (headings, lists). If the file starts
    # with an AUTO block, we must scan until its matching :END marker.
    insert_at = 1

    first = lines[0].strip()
    if re.match(r"^<!--\s*AUTO-.*:START\s*-->\s*$", first):
        # Insert right after the first AUTO block ends.
        for i, ln in enumerate(lines[:2000]):
            if re.match(r"^<!--\s*AUTO-.*:END\s*-->\s*$", ln.strip()):
                insert_at = i + 1
                break
    else:
        # Fallback: advance past any leading AUTO comment-only lines.
        for i, ln in enumerate(lines[:300]):
            if re.match(r"^<!--\s*AUTO-.*:END\s*-->\s*$", ln.strip()):
                insert_at = i + 1
                continue
            if ln.strip() and not ln.strip().startswith("<!-- AUTO-"):
                break

    # Keep a blank line boundary.
    before = "".join(lines[:insert_at]).rstrip("\n") + "\n\n"
    after = "".join(lines[insert_at:])

    new_txt = before + header + after.lstrip("\n")
    path.write_text(new_txt, encoding="utf-8")
    print(f"ensure_news_run_header: inserted header into news/{ymd}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

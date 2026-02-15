#!/usr/bin/env python3
"""Send a daily summary to Discord via webhook (link/copyright-safe).

This script is designed to be run by automation (cron) without requiring OpenClaw's
Discord channel plugin. It posts directly to a Discord webhook.

Inputs
- Webhook URL via env: DISCORD_WEBHOOK_URL
  (preferred for secrets)

Behavior
- Summarizes commits since local midnight (Asia/Seoul)
- Lists top changed files (by frequency in git log names)
- Includes today's news execution status snippet if available

Exit codes
- 0: sent
- 2: not sent (missing webhook or request failure)
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def sh(cmd: list[str]) -> str:
    p = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, check=False)
    return (p.stdout or "").strip()


def today_kst() -> str:
    # Avoid tz dependency: rely on system TZ env in cron, but fallback is acceptable.
    # If TZ is set to Asia/Seoul by runner, this will match.
    return datetime.now().strftime("%Y-%m-%d")


def read_news_status(today: str) -> str | None:
    p = BASE / "news" / f"{today}.md"
    if not p.exists():
        return None

    txt = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Extract '## 실행 상태' block up to '## 실행 이력'
    out: list[str] = []
    in_block = False
    for ln in txt:
        if ln.strip() == "## 실행 상태":
            in_block = True
            continue
        if in_block and ln.strip() == "## 실행 이력":
            break
        if in_block:
            out.append(ln)
    snip = "\n".join(out).strip()
    if not snip:
        return None

    # Keep it short
    lines = [ln for ln in snip.splitlines() if ln.strip()]
    return "\n".join(lines[:6])


def commit_summaries(today: str) -> list[str]:
    # Commits since local midnight.
    out = sh(["git", "log", "--since", f"{today} 00:00", "--pretty=format:%h %s"])  # noqa: S603
    if not out:
        return []
    return out.splitlines()[:3]


def top_changed_files(today: str) -> list[str]:
    names = sh(
        [
            "bash",
            "-lc",
            "git log --since '" + today + " 00:00' --name-only --pretty=format: | sed '/^$/d' | sort | uniq -c | sort -nr | head -n 8",
        ]
    )
    if not names:
        return []
    # Convert to: path (count)
    out: list[str] = []
    for ln in names.splitlines():
        parts = ln.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        cnt, path = parts
        out.append(f"{path} ({cnt})")
    return out


def build_message(today: str) -> str:
    commits = commit_summaries(today)
    files = top_changed_files(today)
    status = read_news_status(today)

    lines: list[str] = []
    lines.append(f"[고윤정 위키 일일 요약 | {today}]")

    if commits:
        total_commits = len(sh(["git", "log", "--since", f"{today} 00:00", "--pretty=oneline"]).splitlines())
        lines.append(f"- 커밋: {total_commits}개")
        lines.append("  - 상위 3개: " + " | ".join(commits))
    else:
        lines.append("- 커밋: 0개(오늘 변경 없음)")

    if files:
        lines.append("- 주요 변경 파일: " + ", ".join(files[:8]))

    if status:
        # compact one-liner-ish
        status_one = status.replace("\n", " | ")
        lines.append(f"- 자동화 상태: {status_one}")

    return "\n".join(lines)


def main() -> int:
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        print("DISCORD_WEBHOOK_URL is not set")
        return 2

    today = today_kst()
    msg = build_message(today)

    # Use existing notifier implementation (direct webhook post)
    import sys

    sys.path.append(str((BASE / "scripts").resolve()))
    import notify_status  # type: ignore

    # Override global webhook for this run
    notify_status.WEBHOOK_URL = webhook

    ok = notify_status.send_discord_message(
        title=f"고윤정 위키 일일 요약 ({today})",
        message=msg,
        color_name="green",
        force=True,
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

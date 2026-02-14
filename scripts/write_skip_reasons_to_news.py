#!/usr/bin/env python3
"""Write a concise 'why some steps skipped' block into today's news.

Input JSON (created by run_daily_update.sh):
- .locks/last-run-reasons.json

This is for unmanned mode: no user action required; just status transparency.
"""

from __future__ import annotations

import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCKS = os.path.join(BASE, ".locks")
REASONS_PATH = os.path.join(LOCKS, "last-run-reasons.json")
NEWS_DIR = os.path.join(BASE, "news")
TZ = "Asia/Seoul"

MARK_START = "<!-- AUTO-SKIP-REASONS:START -->"
MARK_END = "<!-- AUTO-SKIP-REASONS:END -->"


def today() -> str:
    return os.environ.get("WIKI_TODAY") or os.popen(f"TZ={TZ} date +%Y-%m-%d").read().strip()


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def upsert_block(news: str, block: str) -> str:
    if MARK_START in news and MARK_END in news:
        pre = news.split(MARK_START)[0]
        post = news.split(MARK_END, 1)[1]
        return pre.rstrip() + "\n\n" + block + "\n\n" + post.lstrip()

    # Insert before 실행 이력 if possible
    if "## 실행 이력" in news:
        a, b = news.split("## 실행 이력", 1)
        return a.rstrip() + "\n\n" + block + "\n\n## 실행 이력" + b

    return news.rstrip() + "\n\n" + block + "\n"


def main() -> int:
    if not os.path.exists(REASONS_PATH):
        return 0

    try:
        data = json.loads(read(REASONS_PATH))
    except Exception:
        return 0

    ts = data.get("timestamp") or ""
    steps = data.get("steps") or []

    lines = [
        MARK_START,
        "## 자동화 스킵/실패 사유(무인 로그)",
        "> 목적: 무인 자동화에서 일부 항목이 채워지지 않는 ‘이유’를 기록합니다. (조치 필요 없음)",
    ]
    if ts:
        lines.append(f"> 갱신: {ts} ({TZ})")
    lines.append("")

    if not steps:
        lines += ["- (특이사항 없음)", "", MARK_END]
    else:
        for s in steps:
            name = s.get("name", "step")
            rc = s.get("rc")
            reason = s.get("reason") or ""
            note = s.get("note") or ""
            msg = f"- {name}: rc={rc}"
            if reason:
                msg += f" · {reason}"
            if note:
                msg += f" · {note}"
            lines.append(msg)
        lines += ["", MARK_END]

    block = "\n".join(lines)

    day = today()
    news_path = os.path.join(NEWS_DIR, f"{day}.md")
    if os.path.exists(news_path):
        news = read(news_path)
    else:
        news = f"# {day} 업데이트\n\n## 실행 상태\n\n## 실행 이력\n"

    out = upsert_block(news, block)
    if out != news:
        write(news_path, out)

    print("write_skip_reasons_to_news: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Write daily 'encyclopedia promotion' suggestions into news/YYYY-MM-DD.md.

We can't reliably auto-promote every item to official confirmation (S/A sources)
without brittle scraping and manual judgment. Instead, this script:
- Scans key pages for common TODO markers
- Produces a short, actionable list of suggestions
- Writes them into today's news file between AUTO markers

Markers recognized (Korean):
- 교차검증 필요
- 참고(2차)
- 요약 보강 필요
- (페이지 내 표기 확인 필요)

This keeps the project moving daily with minimal risk.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = "Asia/Seoul"

TARGET_FILES = [
    "pages/profile.md",
    "pages/filmography.md",
    "pages/timeline.md",
    "pages/awards.md",
    "pages/interviews.md",
    "pages/appearances.md",
    "pages/pictorials/events.md",
    "pages/pictorials/stills-posters.md",
    "pages/pictorials/cover.md",
    "pages/pictorials/editorial.md",
    "pages/pictorials/campaign.md",
]

TODO_PATTERNS = [
    r"교차검증 필요",
    r"참고\(2차\)",
    r"요약\(3~5줄\):\s*\n\s*- \(요약 보강 필요\)",
    r"요약 보강 필요",
    r"\(페이지 내 표기 확인 필요\)",
]
TODO_RE = re.compile("|".join(f"(?:{p})" for p in TODO_PATTERNS))

NEWS_DIR = os.path.join(BASE, "news")


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def today_ymd() -> str:
    # Avoid external deps; respect system TZ by relying on env in runner.
    return datetime.now().strftime("%Y-%m-%d")


def scan_file(rel_path: str, max_hits: int = 8) -> list[str]:
    path = os.path.join(BASE, rel_path)
    if not os.path.exists(path):
        return []
    lines = read_text(path).splitlines()
    hits = []
    for i, ln in enumerate(lines, start=1):
        if TODO_RE.search(ln):
            # keep it short
            snippet = ln.strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            hits.append(f"- {rel_path}:{i} · {snippet}")
            if len(hits) >= max_hits:
                break
    return hits


def build_suggestions() -> list[str]:
    out: list[str] = []
    for rel in TARGET_FILES:
        out.extend(scan_file(rel))
        if len(out) >= 20:
            break
    return out[:20]


def upsert_news_block(news_path: str, suggestions: list[str]) -> None:
    md = read_text(news_path)
    start = "<!-- AUTO-ENCYCLOPEDIA-PROMOTE:START -->"
    end = "<!-- AUTO-ENCYCLOPEDIA-PROMOTE:END -->"

    block_lines = [
        start,
        "## 백과사전 승격 제안(자동)",
        "> 목표: 오늘 ‘참고(2차)/보강 필요’ 항목 중 최소 1개를 S/A급(공식/원문) 근거로 승격.",
        "",
    ]
    if suggestions:
        block_lines.append("### 후보(자동 스캔)")
        block_lines.extend(suggestions)
    else:
        block_lines.append("- (현재 자동 스캔으로 잡힌 보강 후보가 없습니다.)")
    block_lines += ["", end]
    block = "\n".join(block_lines) + "\n"

    if start in md and end in md:
        md2 = re.sub(
            re.escape(start) + r"[\s\S]*?" + re.escape(end) + r"\n?",
            block,
            md,
            count=1,
        )
    else:
        # Insert after '## 실행 상태' section if possible, else top.
        m = re.search(r"^## 실행 상태\s*$", md, flags=re.M)
        if m:
            # insert after the status header block (after first blank line following it)
            insert_at = m.end()
            md2 = md[:insert_at] + "\n\n" + block + md[insert_at:]
        else:
            md2 = block + "\n" + md
    write_text(news_path, md2)


def main() -> int:
    ymd = today_ymd()
    news_path = os.path.join(NEWS_DIR, f"{ymd}.md")
    if not os.path.exists(news_path):
        # nothing to do
        return 0
    suggestions = build_suggestions()
    upsert_news_block(news_path, suggestions)
    print(f"suggest_encyclopedia_promotions: {len(suggestions)} suggestions")
    return 0


if __name__ == "__main__":
    sys.exit(main())

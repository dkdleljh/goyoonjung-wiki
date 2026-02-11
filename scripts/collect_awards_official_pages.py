#!/usr/bin/env python3
"""Collect official award site URLs into a dedicated reference list.

This doesn't claim winners; it just keeps official pages handy for manual cross-check.
Output: sources/awards-official.md
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "sources" / "awards-official.md"

SITES = [
    ("백상예술대상", "https://www.baeksangawards.co.kr/"),
    ("청룡시리즈어워즈", "https://bsa.blueaward.co.kr/"),
    ("청룡영화상", "http://www.blueaward.co.kr/"),
    ("대종상영화제", "https://daejong.or.kr/"),
]


def main() -> int:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        "# 🏆 시상식 공식 페이지(참조)",
        "",
        f"> 갱신: {now} (Asia/Seoul)",
        "",
        "- 원칙: 공식 사이트 링크만 모아둡니다(원문 복사 없음).",
        "- 사용: `pages/awards.md` 교차검증 시 근거 링크로 활용.",
        "",
    ]
    for name, url in SITES:
        lines.append(f"- {name}: {url}")
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding='utf-8')
    print(f"collect_awards_official_pages: wrote {OUT}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

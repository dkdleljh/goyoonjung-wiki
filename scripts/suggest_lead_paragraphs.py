#!/usr/bin/env python3
"""Suggest lead paragraphs (NOT auto-apply) for encyclopedia-style pages.

Writes to today's news/YYYY-MM-DD.md between AUTO markers.
- Korean lead suggestion for pages/profile.md and index.md
- English lead suggestion for index.en.md

This script is intentionally conservative: it does not claim facts beyond
what's already in the wiki and linked official anchors (MAA / official pages).
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NEWS_DIR = os.path.join(BASE, "news")


def read_text(rel: str) -> str:
    with open(os.path.join(BASE, rel), "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def today_ymd() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def extract_notable_works(filmography_md: str, limit: int = 6) -> list[str]:
    """Extract works from the first markdown table under '## 드라마/시리즈'.

    This avoids accidental matches in other paragraphs containing pipes.
    """
    works: list[str] = []
    lines = filmography_md.splitlines()

    in_table = False
    for ln in lines:
        if ln.strip() == "## 드라마/시리즈":
            in_table = False
            continue
        if ln.startswith("## ") and "드라마/시리즈" not in ln:
            # stop when next section begins
            if works:
                break
        if ln.startswith("|") and "연도" in ln and "작품" in ln:
            in_table = True
            continue
        if in_table:
            if not ln.startswith("|"):
                # end of table
                if works:
                    break
                continue
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            # expected columns: 연도 | 플랫폼/방송사 | 작품 | 역할 | 비고 | 근거
            if len(cols) >= 3 and cols[2] and cols[2] != "작품":
                w = cols[2]
                if w != "---" and not set(w) <= {"-"}:
                    if w not in works:
                        works.append(w)
            if len(works) >= limit:
                break

    return works


def build() -> str:
    film = read_text("pages/filmography.md")
    works = extract_notable_works(film)
    works_kr = ", ".join(f"*{w}*" for w in works) if works else "(대표작 보강 필요)"

    ko = (
        "### 한국어 리드문(초안)\n"
        "- (index/profile 공용)\n\n"
        "고윤정(Go Youn-jung, 1996년 4월 22일~)은 대한민국의 배우이다. "
        f"주요 출연작으로 {works_kr} 등이 있다. "
        "이 위키는 작품·화보·광고·인터뷰·출연/행사 기록을 링크 중심(저작권 안전)으로 수집·정리한다.\n"
    )

    en = (
        "### English lead (draft)\n"
        "Go Youn-jung (born April 22, 1996) is a South Korean actress. "
        "This wiki is a link-first (copyright-safe) archive of her works, pictorials, endorsements, interviews, and appearances/events, with a focus on official and primary sources.\n"
    )

    return ko + "\n" + en


def upsert(news_path: str, content: str) -> None:
    md = read_text(os.path.relpath(news_path, BASE))
    start = "<!-- AUTO-LEAD-DRAFT:START -->"
    end = "<!-- AUTO-LEAD-DRAFT:END -->"
    block = "\n".join([
        start,
        "## 리드 문단(초안) 제안(자동)",
        "> 목적: 위키백과 느낌의 ‘소개 문단’을 만들기 위한 초안 후보입니다. (자동 적용하지 않음)",
        "",
        content.strip(),
        "",
        end,
        "",
    ])

    if start in md and end in md:
        md2 = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end) + r"\n?", block, md, count=1)
    else:
        # place after encyclopedia promote block if present, else near top
        insert_at = 0
        m = re.search(r"<!-- AUTO-ENCYCLOPEDIA-PROMOTE:END -->\n", md)
        if m:
            insert_at = m.end()
        md2 = md[:insert_at] + "\n" + block + md[insert_at:]

    write_text(news_path, md2)


def main() -> int:
    ymd = today_ymd()
    news_path = os.path.join(NEWS_DIR, f"{ymd}.md")
    if not os.path.exists(news_path):
        return 0
    upsert(news_path, build())
    print("suggest_lead_paragraphs: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

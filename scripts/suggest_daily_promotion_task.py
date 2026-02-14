#!/usr/bin/env python3
"""Suggest one small, high-impact promotion task per day (unmanned mode).

Writes into news/YYYY-MM-DD.md under a marker block.
No web fetching.

This does NOT ask the user to provide URLs.
Instead it summarizes what the automation will attempt next and why something may remain unfilled
(e.g., site blocked / official page not discoverable).
"""

from __future__ import annotations

import os
import re
import sys
from urllib.parse import quote

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = "Asia/Seoul"
NEWS_DIR = os.path.join(BASE, "news")
PROFILE = os.path.join(BASE, "pages", "profile.md")
AWARDS = os.path.join(BASE, "pages", "awards.md")
ENDO_FILES = [
    os.path.join(BASE, "pages", "endorsements", "beauty.md"),
    os.path.join(BASE, "pages", "endorsements", "fashion.md"),
    os.path.join(BASE, "pages", "endorsements", "lifestyle.md"),
]

MARK_START = "<!-- AUTO-DAILY-PROMOTION-TASK:START -->"
MARK_END = "<!-- AUTO-DAILY-PROMOTION-TASK:END -->"


def today() -> str:
    return os.environ.get("WIKI_TODAY") or os.popen(f"TZ={TZ} date +%Y-%m-%d").read().strip()


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def google(q: str) -> str:
    return "https://www.google.com/search?q=" + quote(q)


def find_first_award_needing_proof(md: str) -> tuple[str, str, str] | None:
    # returns (year, award, category)
    for ln in md.splitlines():
        if not ln.startswith("|"):
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 8:
            continue
        year, award, category, *_rest = cols
        proof = cols[6] if len(cols) > 6 else ""
        if re.fullmatch(r"20\d{2}", year) and not proof:
            return year, award, category
    return None


def find_first_endo_needing_announce(md: str) -> tuple[str, str] | None:
    # returns (brand, campaign_url)
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("- 브랜드/회사명:"):
            brand = lines[i].split(":", 1)[1].strip()
            j = i + 1
            end = j
            while end < len(lines) and not lines[end].startswith("- 브랜드/회사명:") and not lines[end].startswith("## "):
                end += 1
            block = "\n".join(lines[i:end])
            if "링크(공식 발표): (확인 필요)" in block:
                camp = ""
                for ln in block.splitlines():
                    if "링크(공식 영상/캠페인):" in ln:
                        camp = ln.split(":", 1)[1].strip()
                        break
                return brand, camp
            i = end
        else:
            i += 1
    return None


def build_block() -> str:
    lines: list[str] = [
        MARK_START,
        "## 오늘의 ‘자동 승격’ 미션(무인)",
        "> 목표: 매일 1개 이상 ‘(확인 필요)/(교차검증 필요)’를 자동으로 줄이도록 시도합니다.",
        "> 원칙: 사람(주인님) 입력 없이 가능한 범위에서만 자동 보강하며, 불가능한 경우는 ‘이유’를 기록하고 스킵합니다.",
        "",
    ]

    # Unmanned mode: we do NOT ask the user to find URLs.
    # Instead we describe what the automation will attempt next.

    lines += [
        "### 자동 처리 우선순위(무인)",
        "- 1) endorsements: 공식 사이트 접근 가능 시 ‘공식 발표’ 링크 자동 확정, 불가 시 ‘공식 채널 게시물(유튜브/인스타)’로 자동 대체",
        "- 2) awards: 공식 도메인/본문 검증 통과 시에만 근거(공식) 자동 채움(검색/접근 불가 시 스킵)",
        "- 3) profile(출생지/학력): 공식/원문 페이지에서 명시가 확인되는 경우에만 자동 반영(대부분 스킵될 수 있음)",
        "",
        "### 오늘의 예상 결과",
        "- 사이트 차단/타임아웃/검색 제한이 있으면 일부 항목은 ‘(확인 필요)’로 남을 수 있습니다.",
        "- 대신 파이프라인은 멈추지 않고 다음 실행에서 계속 재시도합니다.",
        "",
        MARK_END,
    ]
    return "\n".join(lines)

    lines += ["- (현재 자동으로 뽑을 미션이 없습니다)", "", MARK_END]
    return "\n".join(lines)


def upsert(news: str, block: str) -> str:
    if MARK_START in news and MARK_END in news:
        pre = news.split(MARK_START)[0]
        post = news.split(MARK_END, 1)[1]
        return pre.rstrip() + "\n\n" + block + "\n\n" + post.lstrip()
    if "## 실행 이력" in news:
        a, b = news.split("## 실행 이력", 1)
        return a.rstrip() + "\n\n" + block + "\n\n## 실행 이력" + b
    return news.rstrip() + "\n\n" + block + "\n"


def main() -> int:
    t = today()
    news_path = os.path.join(NEWS_DIR, f"{t}.md")
    if os.path.exists(news_path):
        news = read(news_path)
    else:
        news = f"# {t} 업데이트\n\n## 실행 상태\n\n## 실행 이력\n"
    block = build_block()
    out = upsert(news, block)
    if out != news:
        write(news_path, out)
    print("suggest_daily_promotion_task: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

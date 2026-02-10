#!/usr/bin/env python3
"""Suggest one small, high-impact promotion task per day (approval-based).

Writes into news/YYYY-MM-DD.md under a marker block.
No web fetching.

The task focuses on reducing placeholders like:
- 교차검증 필요 (profile)
- (확인 필요) for endorsements official announcement links
- awards proof empty

It also documents a lightweight approval syntax the user can paste into the news file.
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
    with open(path, "r", encoding="utf-8") as f:
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
        "## 오늘의 ‘1개 승격’ 미션(자동)",
        "> 목표: 매일 1개만이라도 ‘(확인 필요)/(교차검증 필요)’를 공식/원문 근거로 승격해서 품질 리포트 숫자를 줄입니다.",
        "",
        "### 승인 입력 규칙(주인님이 직접 붙여넣기)",
        "- 프로필: `APPROVE_PROFILE|출생지|<근거URL>` 또는 `APPROVE_PROFILE|학력|<근거URL>`",
        "- 광고/엠버서더: `APPROVE_ENDO|<브랜드/회사명 그대로>|<공식발표URL>`",
        "- 수상: `APPROVE_AWARD|<연도>|<시상식>|<공식근거URL>`",
        "",
    ]

    # Choose priority (pragmatic for high success rate):
    # endorsements -> awards -> profile
    # Rationale: profile birthplace/education often isn't present on official pages.

    # endorsements
    for f in ENDO_FILES:
        if not os.path.exists(f):
            continue
        e = find_first_endo_needing_announce(read(f))
        if e:
            brand, camp = e
            lines += [
                "### 1순위: endorsements ‘공식 발표’ 링크 1개 확정",
                f"- 대상: {brand}",
                f"- 빠른 검색: {google(f'{brand} 고윤정 모델 공식 발표')}",
            ]
            if camp:
                lines.append(f"- 참고(캠페인/영상): {camp}")
            lines += [
                "- 찾으면 아래 형태로 한 줄 추가:",
                f"  - `APPROVE_ENDO|{brand}|https://...`",
                "",
                MARK_END,
            ]
            return "\n".join(lines)

    aw = read(AWARDS) if os.path.exists(AWARDS) else ""
    first = find_first_award_needing_proof(aw)
    if first:
        y, award, cat = first
        lines += [
            "### 2순위: awards 근거(공식) 1개 채우기",
            f"- 대상: {y} / {award} / {cat}",
            f"- 빠른 검색: {google(f'{award} {y} 고윤정 {cat} 공식')}",
            "- 찾으면 아래 형태로 한 줄 추가:",
            f"  - `APPROVE_AWARD|{y}|{award}|https://...`",
            "",
            MARK_END,
        ]
        return "\n".join(lines)

    prof = read(PROFILE) if os.path.exists(PROFILE) else ""
    if "교차검증 필요" in prof:
        lines += [
            "### 3순위: 프로필(출생지/학력) 교차검증 1개 끝내기",
            "- 추천 액션: 소속사(MAA) 또는 방송사/매체 원문에서 해당 정보가 명시된 페이지 1개를 찾기",
            f"- 빠른 검색: {google('site:maa.co.kr 고윤정 출생 학력')}",
            "- 찾으면 아래 형태로 한 줄 추가(예시):",
            "  - `APPROVE_PROFILE|출생지|https://...`",
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

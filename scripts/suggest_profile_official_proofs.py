#!/usr/bin/env python3
"""Suggest official/primary source candidates to verify profile fields.

Writes into news/YYYY-MM-DD.md under a marker block.
No web fetching (deterministic): only generates search links.

Targets currently flagged fields in pages/profile.md:
- 출생지
- 학력

Policy:
- Avoid rumors; only suggest queries that can lead to official/primary sources
  (agency profile, major broadcasters/magazines interviews).
"""

from __future__ import annotations

import os
import re
import sys
from urllib.parse import quote

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = "Asia/Seoul"

PROFILE = os.path.join(BASE, "pages", "profile.md")
NEWS_DIR = os.path.join(BASE, "news")

MARK_START = "<!-- AUTO-PROFILE-PROOF-SUGGEST:START -->"
MARK_END = "<!-- AUTO-PROFILE-PROOF-SUGGEST:END -->"


def today() -> str:
    # Avoid importing datetime tz libs; rely on system TZ via date cmd in shell scripts normally.
    # Here we keep deterministic by reading from env if provided.
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


def build_block(profile_md: str) -> str:
    needs_birth = "출생지: (교차검증 필요)" in profile_md
    needs_edu = "## 학력" in profile_md and "(교차검증 필요)" in profile_md.split("## 학력", 1)[1]

    lines = [
        MARK_START,
        "## 프로필(출생지/학력) 근거 링크 후보(자동)",
        "> 목표: `pages/profile.md`의 ‘교차검증 필요’ 항목을 공식/원문 근거로 승격하기 위한 검색 링크 후보입니다.",
        "> 주의: 자동 적용하지 않습니다. 링크를 열어 본문에 해당 정보가 명시돼 있는지 확인 후 반영하세요.",
        "",
    ]

    if not (needs_birth or needs_edu):
        lines += ["- (현재 제안할 항목이 없습니다)", "", MARK_END]
        return "\n".join(lines)

    if needs_birth:
        lines += [
            "### 출생지(교차검증)",
            "- 소속사(MAA) 프로필 내 표기 확인:",
            f"  - {google('site:maa.co.kr 고윤정 출생')}",
            "- 주요 1차/원문 인터뷰 기반 확인(방송사/매체):",
            f"  - {google('site:kbs.co.kr 고윤정 출생')}",
            f"  - {google('site:jtbc.co.kr 고윤정 출생')}",
            f"  - {google('site:tvn.cjenm.com 고윤정 출생')}",
            f"  - {google('site:vogue.co.kr 고윤정 출생')}",
            "- 일반 검색(공식 페이지가 나오는지 확인):",
            f"  - {google('고윤정 출생지 공식')}",
            "",
        ]

    if needs_edu:
        lines += [
            "### 학력(교차검증)",
            "- 소속사(MAA) 프로필 내 표기 확인:",
            f"  - {google('site:maa.co.kr 고윤정 학력')}",
            "- 원문 인터뷰/프로필 기사 기반 확인:",
            f"  - {google('site:kbs.co.kr 고윤정 학력')}",
            f"  - {google('site:naver.com 고윤정 학력 인터뷰')}",
            f"  - {google('site:marieclairekorea.com 고윤정 인터뷰 학력')}",
            f"  - {google('site:allurekorea.com 고윤정 인터뷰')}",
            "- 일반 검색:",
            f"  - {google('고윤정 학력 인터뷰 원문')}",
            "",
        ]

    lines.append(MARK_END)
    return "\n".join(lines)


def upsert_block(news_md: str, block: str) -> str:
    if MARK_START in news_md and MARK_END in news_md:
        pre = news_md.split(MARK_START)[0]
        post = news_md.split(MARK_END, 1)[1]
        # keep surrounding newlines tidy
        return pre.rstrip() + "\n\n" + block + "\n\n" + post.lstrip()

    # Insert after '## 실행 상태' block if present
    if "## 실행 상태" in news_md:
        parts = news_md.split("## 실행 상태", 1)
        head = parts[0] + "## 실행 상태" + parts[1]
        # append block near top, before first '## 실행 이력' if exists
        if "## 실행 이력" in head:
            a, b = head.split("## 실행 이력", 1)
            return a.rstrip() + "\n\n" + block + "\n\n## 실행 이력" + b
        return head.rstrip() + "\n\n" + block + "\n"

    return news_md.rstrip() + "\n\n" + block + "\n"


def main() -> int:
    if not os.path.exists(PROFILE):
        return 0
    prof = read(PROFILE)
    block = build_block(prof)

    t = today()
    news_path = os.path.join(NEWS_DIR, f"{t}.md")
    if os.path.exists(news_path):
        news = read(news_path)
    else:
        news = f"# {t} 업데이트\n\n## 실행 상태\n\n## 실행 이력\n"

    out = upsert_block(news, block)
    if out != news:
        write(news_path, out)

    print("suggest_profile_official_proofs: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

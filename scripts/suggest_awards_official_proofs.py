#!/usr/bin/env python3
"""Suggest official proof links for awards entries (NO auto-apply).

Writes a suggestion block into today's news file.

Rationale:
- Award sites are often dynamic and brittle to scrape.
- Instead, provide deterministic, low-risk candidate links:
  - official site home
  - official site search (if known)
  - Google site: search queries for (award + year + 고윤정)

This keeps the workflow fully automated while preserving correctness.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = ZoneInfo("Asia/Seoul")

AWARDS_MD = os.path.join(BASE, "pages", "awards.md")
NEWS_DIR = os.path.join(BASE, "news")


def today_ymd() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def google_site_query(site: str, q: str) -> str:
    from urllib.parse import quote

    return f"https://www.google.com/search?q={quote('site:' + site + ' ' + q)}"


def parse_awards_rows(md: str) -> list[dict]:
    rows = []
    for ln in md.splitlines():
        if not ln.startswith("|"):
            continue
        if "연도" in ln and "시상식" in ln:
            continue
        # table row
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 8:
            continue
        year, award, category, work, result, status, proof, note = cols[:8]
        if not re.fullmatch(r"20\d{2}", year):
            continue
        if proof:
            continue
        rows.append(
            {
                "year": year,
                "award": award,
                "category": category,
                "work": work,
                "result": result,
                "status": status,
            }
        )
    return rows


def build_block(rows: list[dict]) -> str:
    start = "<!-- AUTO-AWARDS-PROOF-SUGGEST:START -->"
    end = "<!-- AUTO-AWARDS-PROOF-SUGGEST:END -->"

    anchors = {
        "백상예술대상": "www.baeksangawards.co.kr",
        "청룡시리즈어워즈": "bsa.blueaward.co.kr",
        "청룡영화상": "www.blueaward.co.kr",
        "대종상": "daejong.or.kr",
        "부일영화상": "www.builfilmawards.com",
        "춘사국제영화제": "www.chunsa.kr",
        "코리아 드라마 어워즈": "koreadramaawards.com",
        "아시아콘텐츠어워즈": "asiacontentsawards.com",
        "씨네21": "www.cine21.com",
        "대한민국 대중문화예술상": "www.mcst.go.kr",
    }

    lines = [
        start,
        "## 수상/노미네이트 근거 링크 후보(자동)",
        "> 목표: `pages/awards.md`의 빈 `근거(공식)` 칸을 채우기 위한 ‘공식 링크 후보’를 자동으로 제안합니다. (자동 적용하지 않음)",
        "",
    ]

    if not rows:
        lines.append("- (근거 링크가 비어있는 항목이 없습니다.)")
        lines += ["", end, ""]
        return "\n".join(lines)

    lines.append("### 검색 링크(빠른 승격용)")

    for r in rows[:20]:
        award = r["award"]
        year = r["year"]
        q = f"{award} {year} 고윤정"
        site = anchors.get(award)
        if site:
            lines.append(f"- {year} {award} / {r['category']} ({r['result']})")
            lines.append(f"  - Google site search: {google_site_query(site, q)}")
        else:
            lines.append(f"- {year} {award} / {r['category']} ({r['result']})")
            lines.append(f"  - Google search: https://www.google.com/search?q={q.replace(' ', '+')}")

    lines += ["", end, ""]
    return "\n".join(lines)


def upsert_news(news_path: str, block: str) -> None:
    md = read(news_path)
    start = "<!-- AUTO-AWARDS-PROOF-SUGGEST:START -->"
    end = "<!-- AUTO-AWARDS-PROOF-SUGGEST:END -->"

    if start in md and end in md:
        md2 = re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end) + r"\n?", block, md, count=1)
    else:
        # Insert after lead draft block if exists, else near top
        insert_at = 0
        m = re.search(r"<!-- AUTO-LEAD-DRAFT:END -->\n", md)
        if m:
            insert_at = m.end()
        md2 = md[:insert_at] + "\n" + block + md[insert_at:]

    write(news_path, md2)


def main() -> int:
    if not os.path.exists(AWARDS_MD):
        return 0
    ymd = today_ymd()
    news_path = os.path.join(NEWS_DIR, f"{ymd}.md")
    if not os.path.exists(news_path):
        return 0

    rows = parse_awards_rows(read(AWARDS_MD))
    block = build_block(rows)
    upsert_news(news_path, block)
    print(f"suggest_awards_official_proofs: rows_missing_proof={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

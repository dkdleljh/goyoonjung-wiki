#!/usr/bin/env python3
"""Promote official TV/OTT article candidates from today's news into pages/appearances.md.

Conservative rules:
- Only allow domains in config/allowlist-domains.txt
- Title must contain '고윤정'
- Append as '보도(1차)' (since it's official broadcaster/OTT domain), otherwise skip.

This does not copy any article text.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import domain_policy

BASE = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE / "news"
APPR = BASE / "pages" / "appearances.md"

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")

OFFICIAL_HOST_HINTS = (
    "news.kbs.co.kr",
    "imnews.imbc.com",
    "news.sbs.co.kr",
    "news.jtbc.co.kr",
    "tvn.cjenm.com",
    "about.netflix.com",
    "www.disneypluskr.com",
)


def today_news() -> Path:
    return NEWS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"


def ensure_year_section(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    return md.rstrip() + f"\n\n{hdr}\n(추가 보강 필요)\n"


def insert_under_year(md: str, year: int, block: str, url: str) -> str:
    if url in md:
        return md
    md = ensure_year_section(md, year)
    hdr = f"## {year}"
    lines = md.splitlines(True)
    start = next((i for i,l in enumerate(lines) if l.strip()==hdr), None)
    if start is None:
        return md + "\n" + block.rstrip() + "\n"
    end = len(lines)
    for j in range(start+1, len(lines)):
        if lines[j].startswith('## ') and lines[j].strip()!=hdr:
            end = j
            break
    section = "".join(lines[start:end]).rstrip() + "\n\n" + block.rstrip() + "\n"
    return "".join(lines[:start]) + section + "".join(lines[end:])


def main() -> int:
    if not APPR.exists():
        return 0
    policy = domain_policy.load_policy()
    news = today_news()
    if not news.exists():
        return 0

    year = datetime.now().year
    md = APPR.read_text(encoding="utf-8")
    changed = 0

    for ln in news.read_text(encoding="utf-8").splitlines():
        m = MD_LINK_RE.search(ln)
        if not m:
            continue
        title, url = m.group(1), m.group(2)
        if "고윤정" not in title:
            continue
        if policy.grade_for_url(url) != "S":
            continue
        host = urlsplit(url).netloc.lower().split(':',1)[0]
        # only promote if official-ish host
        if not any(host.endswith(h) or host==h for h in OFFICIAL_HOST_HINTS):
            continue

        block = "\n".join(
            [
                "- 날짜: (페이지 내 표기 확인 필요)",
                "- 구분: 출연/행사(공식 기사 후보)",
                f"- 제목: {title}",
                f"- 링크(원문): {url}",
                "- 상태: 보도(1차)",
                f"- id: {url}",
                "- 메모: (자동 후보) 방송사/OTT 공식 도메인 기반",
            ]
        )
        new_md = insert_under_year(md, year, block, url)
        if new_md != md:
            md = new_md
            changed += 1

    if changed:
        APPR.write_text(md, encoding="utf-8")

    print(f"promote_official_tv_ott_candidates: changed={changed}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

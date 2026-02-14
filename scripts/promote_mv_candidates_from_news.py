#!/usr/bin/env python3
"""Promote MV candidates from today's news log into pages/videos/mv.md.

This is *candidate* promotion only (no auto 'official confirmation').
Rules:
- Only consider lines that contain a YouTube URL.
- Title must contain both '고윤정' and '뮤직비디오' (strict, to keep precision).
- Append as '확인 필요' into the current year section.

No downloading, no scraping.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE / "news"
OUT = BASE / "pages" / "videos" / "mv.md"

YT_RE = re.compile(r"https?://(?:www\.)?(?:youtu\.be/|youtube\.com/watch\?v=)[^\s)]+")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def get_today_news() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return NEWS_DIR / f"{today}.md"


def ensure_year(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    # append at end
    return md.rstrip() + f"\n\n{hdr}\n(아직 추가된 항목이 없습니다.)\n"


def insert_under_year(md: str, year: int, block: str, url: str) -> str:
    if url in md:
        return md
    md = ensure_year(md, year)
    hdr = f"## {year}"
    lines = md.splitlines(True)
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == hdr:
            start = i
            break
    if start is None:
        return md + "\n" + block.rstrip() + "\n"
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ") and lines[j].strip() != hdr:
            end = j
            break
    section = "".join(lines[start:end])
    # remove placeholder line if present
    section_lines = section.splitlines(True)
    if any("(아직 추가된 항목이 없습니다.)" in x for x in section_lines):
        section = "".join([x for x in section_lines if "(아직 추가된 항목이 없습니다.)" not in x]).rstrip() + "\n"
    new_section = section.rstrip() + "\n\n" + block.rstrip() + "\n"
    return "".join(lines[:start]) + new_section + "".join(lines[end:])


def main() -> int:
    news = get_today_news()
    if not news.exists() or not OUT.exists():
        return 0

    year = datetime.now().year
    news_lines = news.read_text(encoding="utf-8").splitlines()
    out_md = OUT.read_text(encoding="utf-8")

    changed = 0
    for ln in news_lines:
        m = MD_LINK_RE.search(ln)
        if not m:
            continue
        title = m.group(1)
        url = m.group(2)
        if not YT_RE.search(url):
            continue
        if "고윤정" not in title:
            continue
        if "뮤직비디오" not in title and "MV" not in title:
            continue

        block = "\n".join(
            [
                "- 날짜: (확인 필요)",
                "- 아티스트/곡: (확인 필요)",
                "- 구분: 뮤직비디오 출연",
                f"- 제목: {title}",
                f"- 링크(공식 MV): {url}",
                "- 상태: 확인 필요",
                f"- id: {url}",
                "- 메모: (자동 후보) 공식 MV 여부/출연 여부 확인 후 '공식확정'으로 승격",
            ]
        )
        new_md = insert_under_year(out_md, year, block, url)
        if new_md != out_md:
            out_md = new_md
            changed += 1

    if changed:
        OUT.write_text(out_md, encoding="utf-8")

    print(f"promote_mv_candidates_from_news: changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

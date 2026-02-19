#!/usr/bin/env python3
"""Promote works/casting items from today's news log into pages/filmography.md (extra record section).

Conservative rules:
- Require name (고윤정) in title
- Require tokens: 캐스팅/출연/차기작/드라마/영화/합류/확정/제작발표회

Link-first; best-effort.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import domain_policy

BASE = Path(__file__).resolve().parent.parent
NEWS = BASE / "news" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
OUT = BASE / "pages" / "filmography.md"

NAME = "고윤정"
TOKENS = ["캐스팅", "출연", "차기작", "확정", "합류", "드라마", "영화", "제작발표회", "티저"]
MD_LINK_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)]+)\)")


@dataclass(frozen=True)
class Item:
    title: str
    url: str


def parse_items(text: str) -> list[Item]:
    out: list[Item] = []
    for ln in text.splitlines():
        m = MD_LINK_RE.search(ln)
        if not m:
            continue
        title = " ".join(m.group("title").split())
        url = m.group("url").strip()
        if title and url:
            out.append(Item(title=title, url=url))
    return out


def main() -> int:
    try:
        policy = domain_policy.load_policy()
        if not NEWS.exists() or not OUT.exists():
            return 0
        news = NEWS.read_text(encoding="utf-8", errors="ignore")
        items = parse_items(news)
        cands = [
            it
            for it in items
            if (
                NAME in it.title
                and any(t in it.title for t in TOKENS)
                and policy.grade_for_url(it.url) == "S"
            )
        ]
        if not cands:
            print("promote_works_from_news: promoted=0")
            return 0

        md = OUT.read_text(encoding="utf-8", errors="ignore")
        if "## 추가 기록" not in md:
            # fallback: append a section
            md = md.rstrip() + "\n\n## 추가 기록(2차 참고 — 공식 교차검증 필요)\n"

        promoted = 0
        for it in cands:
            if it.url in md:
                continue
            block = "\n".join(
                [
                    "",
                    f"- 날짜: {datetime.now().strftime('%Y-%m-%d')}",
                    "- 구분: 작품/캐스팅(뉴스 자동 반영)",
                    f"- 제목: {it.title}",
                    f"- 링크(원문): {it.url}",
                    "- 상태: 보도(2차)",
                    f"- id: {it.url}",
                ]
            )
            md += block
            promoted += 1

        if promoted:
            OUT.write_text(md, encoding="utf-8")
        print(f"promote_works_from_news: promoted={promoted}")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

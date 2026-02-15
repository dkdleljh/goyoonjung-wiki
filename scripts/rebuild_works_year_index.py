#!/usr/bin/env python3
"""Rebuild works year index.

Output:
- pages/works/by-year.md

Sources:
- pages/filmography.md (primary list)
- pages/works/*.md (optional: link to existing work pages by title)

No web access.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILM = os.path.join(BASE, "pages", "filmography.md")
WORKS_DIR = os.path.join(BASE, "pages", "works")
OUT = os.path.join(WORKS_DIR, "by-year.md")

TABLE_ROW_RE = re.compile(r"^\|\s*(20\d{2})\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*$")
TITLE_H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def load_work_pages() -> dict[str, str]:
    """Map work title -> relative md path."""
    m: dict[str, str] = {}
    if not os.path.isdir(WORKS_DIR):
        return m
    for fn in os.listdir(WORKS_DIR):
        if not fn.endswith(".md"):
            continue
        if fn in {"index.md", "by-year.md"}:
            continue
        path = os.path.join(WORKS_DIR, fn)
        try:
            first = open(path, encoding="utf-8").read().splitlines()[:20]
        except Exception:
            continue
        title = None
        for ln in first:
            mh = TITLE_H1_RE.match(ln.strip())
            if mh:
                title = mh.group(1).strip()
                break
        if not title:
            continue
        m[title] = f"works/{fn}"
    return m


def parse_filmography() -> list[tuple[str, str, str, str, str, str]]:
    if not os.path.exists(FILM):
        return []
    out = []
    for ln in open(FILM, encoding="utf-8").read().splitlines():
        if not ln.startswith("|"):
            continue
        if "| 연도 |" in ln:
            continue
        if ln.strip().startswith("|---"):
            continue
        m = TABLE_ROW_RE.match(ln.strip())
        if not m:
            continue
        year, platform, title, role, note, proof = [x.strip() for x in m.groups()]
        out.append((year, platform, title, role, note, proof))
    return out


def main() -> int:
    rows = parse_filmography()
    work_pages = load_work_pages()

    by_year: dict[int, list[tuple[str, str, str, str, str]]] = defaultdict(list)
    for year, platform, title, role, note, proof in rows:
        by_year[int(year)].append((platform, title, role, note, proof))

    out = [
        "# 작품 — 연도별 인덱스",
        "",
        "> 목적: 필모그래피(드라마/시리즈/영화)를 연도별로 빠르게 탐색합니다.",
        "> 출처: `pages/filmography.md` (1차 근거 중심)",
        "",
        "---",
        "",
    ]

    for y in sorted(by_year.keys(), reverse=True):
        out.append(f"## {y}")
        for platform, title, role, note, proof in by_year[y]:
            link = work_pages.get(title)
            if link:
                title_md = f"[{title}](../{link})"
            else:
                title_md = title
            bits = [f"{title_md}", f"({platform})", f"— {role}"]
            if note:
                bits.append(f"· {note}")
            if proof:
                bits.append(f"· 근거: {proof}")
            out.append("- " + " ".join(bits))
        out.append("")

    out += [
        "---",
        "※ 이 페이지는 자동 생성됩니다.",
        "",
        "## 공식 링크",
        "- (S) 소속사(MAA) 프로필(기준): https://maa.co.kr/artists/go-younjung",
        "",
        "## 출처",
        "- pages/filmography.md",
        "- pages/works/*.md",
        "",
    ]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("rebuild_works_year_index: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Rebuild year-based index pages for encyclopedia-style navigation.

Creates/overwrites:
- pages/pictorials/by-year.md
- pages/appearances/by-year.md

Inputs:
- pictorials: cover/editorial/campaign/making/events
- appearances: pages/appearances.md

This is link-first and deterministic. It does not fetch the web.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PICTORIAL_FILES = [
    "pages/pictorials/cover.md",
    "pages/pictorials/editorial.md",
    "pages/pictorials/campaign.md",
    "pages/pictorials/making.md",
    "pages/pictorials/events.md",
]

APPEARANCES_FILE = "pages/appearances.md"

OUT_PICT_BY_YEAR = "pages/pictorials/by-year.md"
OUT_APP_BY_YEAR = "pages/appearances/by-year.md"

DATE_RE = re.compile(r"^\s*-\s*날짜:\s*(.+?)\s*$")
URL_RE = re.compile(r"https?://[^\s)]+")


@dataclass
class Item:
    date: str
    title: str
    url: str
    source: str


def read_text(rel: str) -> str:
    path = os.path.join(BASE, rel)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(rel: str, content: str) -> None:
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def year_from_date(date: str) -> int | None:
    m = re.search(r"(20\d{2})", date)
    if not m:
        return None
    return int(m.group(1))


def parse_items(md: str, source: str) -> list[Item]:
    lines = md.splitlines()
    items: list[Item] = []

    i = 0
    while i < len(lines):
        m = DATE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        date = m.group(1).strip()
        # scan forward within this entry block until next '- 날짜:' or '## '
        j = i + 1
        title = None
        url = None
        while j < len(lines) and not DATE_RE.match(lines[j]) and not lines[j].startswith("## "):
            ln = lines[j].strip()
            if title is None and (ln.startswith("- 제목:") or ln.startswith("- 행사명:") or ln.startswith("- 프로그램/행사명:")):
                title = ln.split(":", 1)[1].strip() if ":" in ln else None
            if url is None and ("링크" in ln or ln.startswith("- 링크:") or ln.startswith("- 링크(원문):") or ln.startswith("- 링크(공식") ):
                um = URL_RE.search(ln)
                if um:
                    url = um.group(0)
            if url is None:
                um = URL_RE.search(ln)
                if um:
                    # fallback: first url in block
                    url = um.group(0)
            j += 1

        if url and not title:
            # fallback: use source + url
            title = "(제목 보강 필요)"

        if title and url:
            items.append(Item(date=date, title=title, url=url, source=source))

        i = j

    # de-dupe by url
    uniq = {}
    for it in items:
        uniq[it.url] = it
    return list(uniq.values())


def build_year_index(title: str, items: Iterable[Item], intro: str) -> str:
    by_year: dict[int, list[Item]] = defaultdict(list)
    for it in items:
        y = year_from_date(it.date)
        if y is None:
            continue
        by_year[y].append(it)

    years = sorted(by_year.keys(), reverse=True)
    out = [f"# {title}", "", intro.strip(), "", "---", ""]

    for y in years:
        out.append(f"## {y}")
        # sort by date desc (lexicographic works for YYYY-MM-DD)
        for it in sorted(by_year[y], key=lambda x: x.date, reverse=True):
            out.append(f"- {it.date} · [{it.title}]({it.url})")
        out.append("")

    out.append("---")
    out.append("※ 이 페이지는 자동 생성됩니다. 원문은 각 카테고리 페이지를 수정하세요.")
    out.append("")
    return "\n".join(out)


def main() -> int:
    pict_items: list[Item] = []
    for rel in PICTORIAL_FILES:
        try:
            md = read_text(rel)
        except FileNotFoundError:
            continue
        pict_items.extend(parse_items(md, source=rel))

    # global de-dupe (same URL can appear in multiple pictorial categories)
    pict_by_url = {it.url: it for it in pict_items}
    pict_items = list(pict_by_url.values())

    app_items: list[Item] = []
    try:
        md = read_text(APPEARANCES_FILE)
        app_items = parse_items(md, source=APPEARANCES_FILE)
    except FileNotFoundError:
        pass

    app_by_url = {it.url: it for it in app_items}
    app_items = list(app_by_url.values())

    pict_md = build_year_index(
        title="사진/화보/행사 — 연도별 인덱스",
        items=pict_items,
        intro=(
            "> 목적: 화보/커버/캠페인/메이킹/행사(포토월) 링크를 연도별로 빠르게 찾기 위한 인덱스입니다.\n"
            "> 원칙: 링크 중심(이미지 저장/재배포 금지)."
        ),
    )
    write_text(OUT_PICT_BY_YEAR, pict_md)

    app_md = build_year_index(
        title="출연/행사 — 연도별 인덱스",
        items=app_items,
        intro=(
            "> 목적: 예능/유튜브/제작발표회/행사 등 출연 기록을 연도별로 빠르게 찾기 위한 인덱스입니다.\n"
            "> 원문/근거는 `pages/appearances.md`에 누적됩니다."
        ),
    )
    write_text(OUT_APP_BY_YEAR, app_md)

    print("rebuild_year_indexes: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

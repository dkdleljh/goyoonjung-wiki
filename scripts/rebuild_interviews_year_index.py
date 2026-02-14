#!/usr/bin/env python3
"""Rebuild interviews year index.

Output:
- pages/interviews/by-year.md

Input:
- pages/interviews.md

Deterministic; no web fetch.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IN_FILE = os.path.join(BASE, "pages", "interviews.md")
OUT_FILE = os.path.join(BASE, "pages", "interviews", "by-year.md")

DATE_RE = re.compile(r"^\s*-\s*날짜:\s*(.+?)\s*$")
TITLE_RE = re.compile(r"^\s*-\s*제목:\s*(.+?)\s*$")
LINK_RE = re.compile(r"https?://[^\s)]+")


def year_from_date(d: str) -> str | None:
    m = re.search(r"(20\d{2})", d)
    return m.group(1) if m else None


def main() -> int:
    if not os.path.exists(IN_FILE):
        return 0
    lines = open(IN_FILE, encoding="utf-8").read().splitlines()

    items = []
    i = 0
    while i < len(lines):
        m = DATE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        date = m.group(1).strip()
        y = year_from_date(date)
        title = None
        url = None
        j = i + 1
        while j < len(lines) and not DATE_RE.match(lines[j]) and not lines[j].startswith("## "):
            mt = TITLE_RE.match(lines[j])
            if mt and not title:
                title = mt.group(1).strip()
            if not url:
                mu = LINK_RE.search(lines[j])
                if mu:
                    url = mu.group(0)
            j += 1
        if y and title and url:
            items.append((y, date, title, url))
        i = j

    by_year = defaultdict(list)
    for y, date, title, url in items:
        by_year[int(y)].append((date, title, url))

    out = [
        "# 인터뷰/기사 — 연도별 인덱스",
        "",
        "> 목적: 인터뷰/기사 항목을 연도별로 빠르게 찾기 위한 인덱스입니다.",
        "> 원문은 `pages/interviews.md`에 누적됩니다.",
        "",
        "---",
        "",
    ]

    for y in sorted(by_year.keys(), reverse=True):
        out.append(f"## {y}")
        for date, title, url in sorted(by_year[y], key=lambda x: x[0], reverse=True):
            out.append(f"- {date} · [{title}]({url})")
        out.append("")

    out += ["---", "※ 이 페이지는 자동 생성됩니다.", ""]

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("rebuild_interviews_year_index: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

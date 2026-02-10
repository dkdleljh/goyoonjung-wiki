#!/usr/bin/env python3
"""Rebuild endorsements year index.

Output:
- pages/endorsements/by-year.md

Inputs:
- pages/endorsements/beauty.md
- pages/endorsements/fashion.md
- pages/endorsements/lifestyle.md

Parses each brand block and tries to extract a year from:
- '발표일/시작일:' line (YYYY or YYYY-MM-DD)
If missing, it is skipped (keeps the index clean).
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

IN_FILES = [
    "pages/endorsements/beauty.md",
    "pages/endorsements/fashion.md",
    "pages/endorsements/lifestyle.md",
]

OUT_FILE = "pages/endorsements/by-year.md"

YEAR_RE = re.compile(r"(20\d{2})")
URL_RE = re.compile(r"https?://[^\s)]+")


@dataclass
class Item:
    year: int
    brand: str
    role: str
    url: str


def read_text(rel: str) -> str:
    with open(os.path.join(BASE, rel), "r", encoding="utf-8") as f:
        return f.read()


def write_text(rel: str, content: str) -> None:
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def parse(md: str) -> list[Item]:
    lines = md.splitlines()
    items: list[Item] = []

    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if ln.startswith("- 브랜드/회사명:"):
            brand = ln.split(":", 1)[1].strip()
            role = ""
            date = ""
            url = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("- 브랜드/회사명:") and not lines[j].startswith("## "):
                s = lines[j].strip()
                if s.startswith("- 역할:"):
                    role = s.split(":", 1)[1].strip()
                if s.startswith("- 발표일/시작일:"):
                    date = s.split(":", 1)[1].strip()
                if ("링크" in s) and not url:
                    m = URL_RE.search(s)
                    if m:
                        url = m.group(0)
                j += 1

            ym = YEAR_RE.search(date)
            if ym and url:
                items.append(Item(year=int(ym.group(1)), brand=brand, role=role, url=url))

            i = j
        else:
            i += 1

    # de-dupe by url
    uniq = {it.url: it for it in items}
    return list(uniq.values())


def main() -> int:
    all_items: list[Item] = []
    for rel in IN_FILES:
        if os.path.exists(os.path.join(BASE, rel)):
            all_items.extend(parse(read_text(rel)))

    by_year = defaultdict(list)
    for it in all_items:
        by_year[it.year].append(it)

    years = sorted(by_year.keys(), reverse=True)
    out = [
        "# 광고/엠버서더 — 연도별 인덱스",
        "",
        "> 목적: 브랜드/광고/엠버서더 기록을 연도별로 빠르게 찾기 위한 인덱스입니다.",
        "> 메모: ‘발표일/시작일’이 확인된 항목만 자동으로 포함됩니다.",
        "",
        "---",
        "",
    ]

    for y in years:
        out.append(f"## {y}")
        for it in sorted(by_year[y], key=lambda x: (x.brand.lower(), x.url)):
            role = f" — {it.role}" if it.role else ""
            out.append(f"- [{it.brand}]({it.url}){role}")
        out.append("")

    out.append("---")
    out.append("※ 이 페이지는 자동 생성됩니다. 원문은 각 카테고리 파일을 수정하세요.")
    out.append("")

    write_text(OUT_FILE, "\n".join(out))
    print("rebuild_endorsements_year_index: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

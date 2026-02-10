#!/usr/bin/env python3
"""Auto-fill '(페이지 내 표기 확인 필요)' dates using page metadata.

Targets:
- pages/interviews.md
- pages/pictorials/cover.md
- pages/pictorials/editorial.md
- pages/pictorials/campaign.md

If an entry contains '- 날짜: (페이지 내 표기 확인 필요)' (or '(확인 필요)') and has a URL,
fetch the page and try to extract a publish date via:
- JSON-LD: datePublished
- meta: property=article:published_time / og:published_time

Limits:
- Max updates per run: 3
- Strict timeouts.

Safety:
- Only fills date when an ISO-like YYYY-MM-DD can be parsed.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = [
    os.path.join(BASE, "pages", "interviews.md"),
    os.path.join(BASE, "pages", "pictorials", "cover.md"),
    os.path.join(BASE, "pages", "pictorials", "editorial.md"),
    os.path.join(BASE, "pages", "pictorials", "campaign.md"),
]

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
TIMEOUT = 12

DATE_LINE_RE = re.compile(r"^\s*-\s*날짜:\s*\((페이지 내 표기 확인 필요|확인 필요)\)\s*$")
URL_RE = re.compile(r"https?://[^\s)]+")

ISO_DATE_RE = re.compile(r"(20\d{2})[-\./](\d{1,2})[-\./](\d{1,2})")


def fetch(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def parse_iso_date(s: str) -> str | None:
    m = ISO_DATE_RE.search(s)
    if not m:
        return None
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{y}-{mo:02d}-{d:02d}"


def extract_date_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    # JSON-LD
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.get_text(strip=True) or "")
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for obj in objs:
            if isinstance(obj, dict):
                for k in ["datePublished", "dateCreated", "dateModified"]:
                    v = obj.get(k)
                    if isinstance(v, str):
                        dt = parse_iso_date(v)
                        if dt:
                            return dt

    # meta properties
    for prop in ["article:published_time", "og:published_time", "article:modified_time", "og:updated_time"]:
        m = soup.find("meta", attrs={"property": prop})
        if m and m.get("content"):
            dt = parse_iso_date(m["content"])
            if dt:
                return dt

    # meta name
    for name in ["pubdate", "publish-date", "date"]:
        m = soup.find("meta", attrs={"name": name})
        if m and m.get("content"):
            dt = parse_iso_date(m["content"])
            if dt:
                return dt

    return None


def update_file(path: str, max_updates: int, budget: list[int]) -> int:
    if not os.path.exists(path):
        return 0

    lines = open(path, "r", encoding="utf-8").read().splitlines(True)
    updated = 0

    i = 0
    while i < len(lines) and budget[0] < max_updates:
        if DATE_LINE_RE.match(lines[i]):
            # search nearby for a URL within next ~12 lines
            url = None
            for j in range(i, min(i + 15, len(lines))):
                m = URL_RE.search(lines[j])
                if m:
                    url = m.group(0)
                    break
            if not url:
                i += 1
                continue
            try:
                html = fetch(url)
                dt = extract_date_from_html(html)
            except Exception:
                dt = None
            if dt:
                lines[i] = re.sub(r"\(페이지 내 표기 확인 필요\)|\(확인 필요\)", dt, lines[i])
                updated += 1
                budget[0] += 1
            time.sleep(0.25)
        i += 1

    if updated:
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(lines))

    return updated


def main() -> int:
    total = 0
    budget = [0]
    for f in FILES:
        total += update_file(f, max_updates=3, budget=budget)
        if budget[0] >= 3:
            break
    print(f"promote_dates_from_meta: updated={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

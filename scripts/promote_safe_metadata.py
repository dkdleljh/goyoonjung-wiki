#!/usr/bin/env python3
"""Safely promote encyclopedia quality by filling *objective metadata*.

This script only performs low-risk, deterministic enrichments:
1) For KBS연예 articles (kstar.kbs.co.kr/list_view.html?idx=...), fetch page and extract:
   - date (YYYY-MM-DD) from page text
   - title from <title> or og:title
   Then update markdown entries that already contain the URL by replacing placeholder dates
   like '(페이지 내 표기 확인 필요)' or 'YYYY-??-??' in the same entry block.

2) For Vogue Korea post URLs with /YYYY/MM/DD/ in the path, infer date from URL and
   replace placeholder '(페이지 내 표기 확인 필요)' date lines in pictorials.

No content interpretation, no new links, no image downloads.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
TIMEOUT = 25

TARGET_FILES = [
    "pages/interviews.md",
    "pages/appearances.md",
    "pages/pictorials/events.md",
    "pages/pictorials/editorial.md",
    "pages/pictorials/cover.md",
    "pages/pictorials/campaign.md",
]

KBS_RE = re.compile(r"https?://kstar\.kbs\.co\.kr/list_view\.html\?idx=(\d+)")
VOGUE_DATE_RE = re.compile(r"https?://www\.vogue\.co\.kr/(20\d{2})/(\d{2})/(\d{2})/")

DATE_ANY_RE = re.compile(r"(20\d{2})[\.-](\d{2})[\.-](\d{2})")


@dataclass
class Meta:
    url: str
    date: str | None = None
    title: str | None = None


def http_get(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def fetch_kbs_meta(url: str) -> Meta:
    html = http_get(url)
    soup = BeautifulSoup(html, "html.parser")

    title = None
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = " ".join(og["content"].split())
    elif soup.title and soup.title.string:
        title = " ".join(soup.title.string.split())

    text = soup.get_text("\n")
    m = DATE_ANY_RE.search(text)
    date = None
    if m:
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    return Meta(url=url, date=date, title=title)


def infer_vogue_date(url: str) -> str | None:
    m = VOGUE_DATE_RE.search(url)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def read_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines(True)


def write_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def update_entry_block(lines: list[str], start: int, end: int, meta: Meta) -> bool:
    """Update date/title inside lines[start:end] if safe placeholders exist."""
    changed = False

    # date line patterns
    for i in range(start, end):
        ln = lines[i]
        if ln.lstrip().startswith("- 날짜:"):
            # Replace placeholders only
            if "(페이지 내 표기 확인 필요)" in ln or "??" in ln:
                if meta.date:
                    indent = re.match(r"^\s*", ln).group(0)
                    lines[i] = f"{indent}- 날짜: {meta.date}\n"
                    changed = True
            break

    # title/행사명 line patterns (only if the existing line is obviously a placeholder)
    if meta.title:
        for key in ("- 제목:", "- 행사명:", "- 프로그램/행사명:"):
            for i in range(start, end):
                ln = lines[i]
                if ln.lstrip().startswith(key):
                    # Do not overwrite if it already has meaningful text
                    if "(인터뷰" in ln or "관련" in ln and len(ln.strip()) < 30:
                        indent = re.match(r"^\s*", ln).group(0)
                        lines[i] = f"{indent}{key} {meta.title}\n"
                        changed = True
                    break
            if changed:
                break

    return changed


def promote_file(rel_path: str, kbs_cache: dict[str, Meta]) -> int:
    path = os.path.join(BASE, rel_path)
    if not os.path.exists(path):
        return 0
    lines = read_lines(path)
    changed = 0

    # find entry blocks starting with '- 날짜:' and ending before next blank line + '- 날짜:' or section header
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("- 날짜:"):
            start = i
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("- 날짜:") and not lines[j].startswith("## "):
                j += 1
            end = j

            block_text = "".join(lines[start:end])

            # KBS url
            m = KBS_RE.search(block_text)
            if m:
                url = m.group(0)
                meta = kbs_cache.get(url)
                if meta is None:
                    try:
                        meta = fetch_kbs_meta(url)
                    except Exception:
                        meta = Meta(url=url)
                    kbs_cache[url] = meta
                    time.sleep(0.2)
                if meta.date or meta.title:
                    if update_entry_block(lines, start, end, meta):
                        changed += 1

            # Vogue date inference (only for pictorials files typically)
            for vm in VOGUE_DATE_RE.finditer(block_text):
                vurl = vm.group(0)
                vdate = infer_vogue_date(vurl)
                if vdate:
                    meta2 = Meta(url=vurl, date=vdate)
                    if update_entry_block(lines, start, end, meta2):
                        changed += 1
                        break

            i = end
        else:
            i += 1

    if changed:
        write_lines(path, lines)
    return changed


def main() -> int:
    kbs_cache: dict[str, Meta] = {}
    total = 0
    for rel in TARGET_FILES:
        total += promote_file(rel, kbs_cache)
    print(f"promote_safe_metadata: updated_blocks={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

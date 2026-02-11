#!/usr/bin/env python3
"""Auto-collect *news article links* for Go Youn-jung from search portals.

Unmanned + copyright-safe principles:
- Link-first only (no article text copying).
- Best-effort: never crash the whole pipeline; return 0 even if sources block.
- De-dupe via sources/seen-urls.txt AND existing markdown contains URL.

Targets (server-rendered search pages):
- Naver news search
- Daum news search

Landing:
- pages/interviews.md (as 기사/보도 링크)

Notes:
- These portals change HTML frequently; parsing is conservative and may skip.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(__file__)
sys.path.append(SCRIPT_DIR)
import relevance

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEEN_TXT = os.path.join(BASE, "sources", "seen-urls.txt")
INTERVIEWS_MD = os.path.join(BASE, "pages", "interviews.md")

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}
TIMEOUT = 20

QUERY = "고윤정"
NAVER_NEWS = f"https://search.naver.com/search.naver?where=news&query={quote_plus(QUERY)}&sort=1"
DAUM_NEWS = f"https://search.daum.net/search?w=news&q={quote_plus(QUERY)}&sort=recency"


@dataclass(frozen=True)
class Entry:
    year: int
    block: str
    url: str


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_seen_urls() -> set[str]:
    if not os.path.exists(SEEN_TXT):
        return set()
    out: set[str] = set()
    with open(SEEN_TXT, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                out.add(s)
    return out


def http_get(url: str) -> str | None:
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def norm_url(u: str) -> str:
    # minimal normalization
    return u.split("#")[0]


def extract_date_from_url(u: str) -> str | None:
    # common date patterns in Korean magazine/news URLs
    m = re.search(r"/(20\d{2})[./-](\d{2})[./-](\d{2})", u)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", u)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def og_title(url: str) -> str | None:
    html = http_get(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return " ".join(og["content"].split())
    if soup.title and soup.title.string:
        return " ".join(soup.title.string.split())
    return None


def ensure_year_section(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    years = sorted({int(y) for y in re.findall(r"^## (\d{4})\s*$", md, flags=re.M)}, reverse=True)
    if not years:
        return md + f"\n\n{hdr}\n(추가 보강 필요)\n"
    for y in years:
        if year > y:
            m = re.search(rf"^## {y}\s*$", md, flags=re.M)
            if m:
                return md[: m.start()] + f"{hdr}\n(추가 보강 필요)\n\n" + md[m.start() :]
    return md + f"\n\n{hdr}\n(추가 보강 필요)\n"


def insert_entry_under_year(md: str, year: int, block: str, url: str) -> str:
    if url in md:
        return md
    md = ensure_year_section(md, year)
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
    new_section = section.rstrip() + "\n\n" + block.rstrip() + "\n"
    return "".join(lines[:start]) + new_section + "".join(lines[end:])


def apply_entries(path: str, entries: Iterable[Entry]) -> int:
    md = read_text(path)
    changed = 0
    for e in sorted(entries, key=lambda x: (x.year, x.url)):
        before = md
        md = insert_entry_under_year(md, e.year, e.block, e.url)
        if md != before:
            changed += 1
    if changed:
        write_text(path, md)
    return changed


def naver_collect(limit: int = 8) -> list[str]:
    html = http_get(NAVER_NEWS)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    # Naver search: anchors with class 'news_tit' often contain direct links
    for a in soup.select("a.news_tit"):
        href = a.get("href")
        if not href:
            continue
        href = norm_url(href)
        if href.startswith("/"):
            href = urljoin(NAVER_NEWS, href)
        if href in out:
            continue
        out.append(href)
        if len(out) >= limit:
            break
    return out


def daum_collect(limit: int = 8) -> list[str]:
    html = http_get(DAUM_NEWS)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    # Daum: results often have a.link_tit or a.f_link_b
    for a in soup.select("a.f_link_b, a.link_tit"):
        href = a.get("href")
        if not href:
            continue
        href = norm_url(href)
        if href.startswith("/"):
            href = urljoin(DAUM_NEWS, href)
        if href in out:
            continue
        # skip internal search links
        if "search.daum.net" in href:
            continue
        out.append(href)
        if len(out) >= limit:
            break
    return out


def build_entries(urls: list[str], seen: set[str], source_label: str) -> list[Entry]:
    out: list[Entry] = []
    for u in urls:
        if u in seen:
            continue
        title = og_title(u)
        if not title:
            continue
        # Precision-first relevance gate
        if not relevance.is_relevant(title, u, source_label):
            continue
        date = extract_date_from_url(u) or "(페이지 내 표기 확인 필요)"
        year = int(date[:4]) if date[:4].isdigit() else time.gmtime().tm_year
        block = "\n".join(
            [
                f"- 날짜: {date}",
                f"- 매체: {source_label}(검색)",
                "- 구분: 기사/보도(링크)",
                f"- 제목: {title}",
                f"- 링크: {u}",
                "- 상태: 보도(2차)",
                f"- id: {u}",
                "- 요약(3~5줄):",
                "  - (요약 보강 필요) 원문 기반 요약.",
            ]
        )
        out.append(Entry(year=year, block=block, url=u))
        time.sleep(0.1)
    return out


def main() -> int:
    if not os.path.exists(INTERVIEWS_MD):
        return 0

    seen = load_seen_urls()

    n_urls = naver_collect()
    d_urls = daum_collect()

    entries = []
    entries += build_entries(n_urls, seen, "네이버 뉴스")
    entries += build_entries(d_urls, seen, "다음 뉴스")

    changed = apply_entries(INTERVIEWS_MD, entries)
    print(f"auto_collect_news_links: urls={len(n_urls)+len(d_urls)} entries={len(entries)} changed={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

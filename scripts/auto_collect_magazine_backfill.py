#!/usr/bin/env python3
"""Backfill interviews/pictorial links from magazine site searches (year-targeted).

Purpose
- Increase coverage for earlier years (e.g., 2018-2022) without using web_search.
- Link-first: we only store URL + minimal metadata (title/date/description).

What it does
1) Query a small set of site search endpoints with queries like "고윤정 2019".
2) Extract article URLs matching strict patterns.
3) For new URLs (not in seen-urls), fetch each article page once and extract:
   - title (og:title)
   - description (og:description)
   - published date (article:published_time / time[datetime] / common meta)
4) Classify into:
   - interviews (if title/desc includes "인터뷰")
   - pictorials/cover (if includes "커버" or "표지")
   - pictorials/editorial (if includes "화보" or "룩" etc)
   - otherwise: interviews (article archive)
5) Append deterministic entry blocks to the appropriate page.
6) Record URL in sources/seen-urls via scripts/add_seen_url.sh

Safety
- No copying of article body. Uses metadata only.
- Conservative limits: max_targets, max_new_urls, per-request timeouts.

"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urljoin

import requests

BASE = Path(__file__).resolve().parent.parent

TIMEOUT = (5, 20)
UA = "goyoonjung-wiki/1.0 (+https://github.com)"

YEARS = ["2018", "2019", "2020", "2021", "2022"]
NAME = "고윤정"

SEARCH_TARGETS = [
    ("ELLE Korea", "https://www.elle.co.kr/?s={q}"),
    ("Vogue Korea", "https://www.vogue.co.kr/?s={q}"),
    ("Harper's Bazaar Korea", "https://www.harpersbazaar.co.kr/?s={q}"),
    ("W Korea", "https://www.wkorea.com/?s={q}"),
    ("GQ Korea", "https://www.gqkorea.co.kr/?s={q}"),
    ("Esquire Korea", "https://www.esquirekorea.co.kr/?s={q}"),
    ("Cosmopolitan Korea", "https://www.cosmopolitan.co.kr/search?query={q}"),
    # Marie Claire search is heavier; keep tag/search handled elsewhere.
]

PAGINATION_PAGES = 4  # fetch a few pages per query to reach older content

ARTICLE_PATTERNS = [
    re.compile(r"^https?://www\\.elle\\.co\\.kr/article/\\d+", re.I),
    re.compile(r"^https?://www\\.vogue\\.co\\.kr/\\d{4}/\\d{2}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.harpersbazaar\\.co\\.kr/article/\\d+", re.I),
    re.compile(r"^https?://www\\.wkorea\\.com/\\d{4}/\\d{2}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.gqkorea\\.co\\.kr/\\d{4}/\\d{2}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.esquirekorea\\.co\\.kr/article/\\d+", re.I),
    re.compile(r"^https?://www\\.cosmopolitan\\.co\\.kr/article/\\d+", re.I),
]

HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)

OG_TITLE_RE = re.compile(r'property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', re.I)
OG_DESC_RE = re.compile(r'property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', re.I)
PUBLISHED_RE = re.compile(
    r'(?:property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\'])'
    r'|(?:<time[^>]+datetime=["\']([^"\']+)["\'])'
    r'|(?:name=["\']pubdate["\']\s+content=["\']([^"\']+)["\'])',
    re.I,
)


@dataclass(frozen=True)
class Item:
    url: str
    title: str
    desc: str
    date: str  # YYYY-MM-DD
    media: str


def is_article(url: str) -> bool:
    return any(rx.match(url) for rx in ARTICLE_PATTERNS)


def iter_search_pages(base_url: str) -> list[str]:
    # Try common pagination patterns; harmless if ignored.
    urls = [base_url]
    for n in range(2, PAGINATION_PAGES + 1):
        if "?" in base_url:
            urls.append(base_url + f"&paged={n}")
            urls.append(base_url + f"&page={n}")
        else:
            urls.append(base_url.rstrip("/") + f"/page/{n}/")
    # stable dedupe
    out: list[str] = []
    seen: set[str] = set()
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def extract_links(html: str, base_url: str) -> set[str]:
    out: set[str] = set()
    for href in HREF_RE.findall(html):
        href = href.strip()
        if not href or href.startswith("javascript:"):
            continue
        abs_url = urljoin(base_url, href)
        if abs_url.startswith("http"):
            out.add(abs_url.split("#", 1)[0])
    return out


def extract_meta(html: str) -> tuple[str, str, str | None]:
    title = ""
    desc = ""
    mt = OG_TITLE_RE.search(html)
    if mt:
        title = mt.group(1).strip()
    md = OG_DESC_RE.search(html)
    if md:
        desc = md.group(1).strip()

    pub = None
    mp = PUBLISHED_RE.search(html)
    if mp:
        for g in mp.groups():
            if g:
                pub = g.strip()
                break

    return title, desc, pub


def to_ymd(pub: str | None, fallback_year: str) -> str | None:
    if not pub:
        return None
    m = re.search(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})", pub)
    if m:
        y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
        return f"{y}-{mo:02d}-{d:02d}"
    m = re.search(r"(20\d{2})[-./](\d{1,2})", pub)
    if m and m.group(1) == fallback_year:
        y, mo = m.group(1), int(m.group(2))
        return f"{y}-{mo:02d}-01"
    return None


def classify(item: Item) -> str:
    t = f"{item.title} {item.desc}"
    if "인터뷰" in t:
        return "interview"
    if "커버" in t or "표지" in t:
        return "cover"
    if "화보" in t or "룩" in t or "캠페인" in t or "디지털" in t:
        return "pictorial"
    return "interview"


def append_interview(item: Item) -> None:
    path = BASE / "pages" / "interviews.md"
    txt = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else "# 인터뷰/기사 아카이브\n"

    # Minimal, metadata-only summary (3 lines)
    summary_lines = []
    if item.desc:
        # keep short
        d = re.sub(r"\s+", " ", item.desc).strip()
        summary_lines.append(f"  - (메타) {d[:160]}")
    summary_lines.append("  - (요약) 링크/메타 기반 자동 수집 항목입니다. 원문 확인 후 요약 보강 가능.")
    summary_lines.append("  - (키워드) 인터뷰/기사 아카이브 보강")

    block = (
        f"\n- 날짜: {item.date}\n"
        f"- 매체: {item.media}\n"
        f"- 제목: {item.title}\n"
        f"- 링크: {item.url}\n"
        f"- 상태: 공식확정\n"
        f"- id: {item.url}\n"
        "- 요약(3~5줄):\n"
        + "\n".join(summary_lines)
        + "\n"
        "- 키워드: 인터뷰, 아카이브\n"
    )

    if item.url in txt:
        return

    path.write_text(txt.rstrip() + "\n" + block + "\n", encoding="utf-8")


def ensure_year_heading(path: Path, year: str) -> None:
    txt = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    if f"## {year}" in txt:
        return
    # insert before official links section if exists, else append
    marker = "## 공식 링크"
    if marker in txt:
        txt = txt.replace(marker, f"## {year}\n\n(아직 추가된 항목이 없습니다.)\n\n" + marker, 1)
    else:
        txt = txt.rstrip() + f"\n\n## {year}\n\n(아직 추가된 항목이 없습니다.)\n"
    path.write_text(txt.rstrip() + "\n", encoding="utf-8")


def append_pictorial(item: Item, kind: str) -> None:
    if kind == "cover":
        path = BASE / "pages" / "pictorials" / "cover.md"
        category = "커버"
    else:
        path = BASE / "pages" / "pictorials" / "editorial.md"
        category = "화보/기사(RSS)"

    year = item.date.split("-", 1)[0]
    ensure_year_heading(path, year)

    txt = path.read_text(encoding="utf-8", errors="ignore")
    if item.url in txt:
        return

    block = (
        f"\n- 날짜: {item.date}\n"
        f"- 매체: {item.media}\n"
        f"- 구분: {category}\n"
        f"- 제목: {item.title}\n"
        f"- 링크(원문): {item.url}\n"
        f"- 상태: 공식확정\n"
        f"- id: {item.url}\n"
    )

    # Append at end of file (before official link section if possible)
    marker = "## 공식 링크"
    if marker in txt:
        txt = txt.replace(marker, block + "\n" + marker, 1)
    else:
        txt = txt.rstrip() + "\n" + block

    path.write_text(txt.rstrip() + "\n", encoding="utf-8")


def mark_seen(url: str) -> None:
    subprocess.run(["bash", str(BASE / "scripts" / "add_seen_url.sh"), url], check=False, cwd=BASE)


def main() -> int:
    max_new_urls = int(os.environ.get("BACKFILL_MAX_NEW", "20"))
    items_added = 0
    new_urls: list[tuple[str, str, str]] = []  # (url, media, year)

    for year in YEARS:
        q = quote(f"{NAME} {year}")
        for media, tmpl in SEARCH_TARGETS:
            base = tmpl.format(q=q)
            for url in iter_search_pages(base):
                html = fetch(url)
                if not html:
                    continue
                links = extract_links(html, url)
                for u in links:
                    if not is_article(u):
                        continue
                    new_urls.append((u, media, year))

    # stable de-dupe preserve order
    seen_set: set[str] = set()
    uniq_urls: list[tuple[str, str, str]] = []
    for u, m, y in new_urls:
        if u in seen_set:
            continue
        seen_set.add(u)
        uniq_urls.append((u, m, y))

    # Filter by existing seen-urls using grep (fast) to avoid loading large files
    seen_txt = (BASE / "sources" / "seen-urls.txt")
    seen_blob = seen_txt.read_text(encoding="utf-8", errors="ignore") if seen_txt.exists() else ""

    candidates = [(u, m, y) for (u, m, y) in uniq_urls if u not in seen_blob]

    for u, media, y in candidates[:max_new_urls]:
        html = fetch(u)
        if not html:
            continue
        title, desc, pub = extract_meta(html)
        if not title:
            continue
        date = to_ymd(pub, y)
        if not date:
            continue
        item = Item(url=u, title=title, desc=desc, date=date, media=media)
        k = classify(item)
        if k == "interview":
            append_interview(item)
        elif k == "cover":
            append_pictorial(item, "cover")
        else:
            append_pictorial(item, "pictorial")
        mark_seen(u)
        items_added += 1

    print(f"auto_collect_magazine_backfill: added={items_added} (max_new={max_new_urls})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

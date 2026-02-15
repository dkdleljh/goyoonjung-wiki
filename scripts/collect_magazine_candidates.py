#!/usr/bin/env python3
"""Collect magazine/article candidate URLs from known site-search/tag pages.

This is a lightweight link harvester to increase coverage (quantity) while keeping
quality controls (no content copying). It:
- fetches a small set of watchlist URLs (magazines)
- extracts outbound article links
- normalizes/dedupes
- filters out already-seen URLs using sources/seen-urls.txt
- writes a short candidate list into news/YYYY-MM-DD.md (append)

Design goals:
- Conservative: only adds URLs; does not attempt to parse full article text.
- Robust: timeouts + user-agent; skips on errors.

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

BASE = Path(__file__).resolve().parent.parent
SEEN_TXT = BASE / "sources" / "seen-urls.txt"
NEWS_DIR = BASE / "news"
WATCHLIST = BASE / "sources" / "watchlist.md"

TIMEOUT = (5, 20)
UA = "goyoonjung-wiki/1.0 (+https://github.com)"

# Only harvest from these watchlist lines (keep tight to avoid noise)
WATCH_KEYS = [
    "https://www.elle.co.kr/?s=",
    "https://www.vogue.co.kr/?s=",
    "https://www.harpersbazaar.co.kr/?s=",
    "https://www.marieclairekorea.com/tag/",
    "https://www.wkorea.com/?s=",
    "https://www.gqkorea.co.kr/?s=",
    "https://www.esquirekorea.co.kr/?s=",
    "https://www.cosmopolitan.co.kr/search?query=",
]

ARTICLE_PATTERNS = [
    re.compile(r"^https?://www\\.elle\\.co\\.kr/article/\\d+", re.I),
    re.compile(r"^https?://www\\.vogue\\.co\\.kr/\\d{4}/\\d{2}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.harpersbazaar\\.co\\.kr/article/\\d+", re.I),
    re.compile(r"^https?://www\\.marieclairekorea\\.com/.+?/\\d{4}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.wkorea\\.com/\\d{4}/\\d{2}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.gqkorea\\.co\\.kr/\\d{4}/\\d{2}/\\d{2}/", re.I),
    re.compile(r"^https?://www\\.esquirekorea\\.co\\.kr/article/\\d+", re.I),
    re.compile(r"^https?://www\\.cosmopolitan\\.co\\.kr/article/\\d+", re.I),
]

HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)


@dataclass
class Candidate:
    url: str
    source: str


def load_seen() -> set[str]:
    if not SEEN_TXT.exists():
        return set()
    return {ln.strip() for ln in SEEN_TXT.read_text(encoding="utf-8").splitlines() if ln.strip()}


def is_article(url: str) -> bool:
    for rx in ARTICLE_PATTERNS:
        if rx.match(url):
            return True
    return False


def normalize(url: str) -> str:
    # basic normalization: drop fragment
    try:
        p = urlparse(url)
        return p._replace(fragment="").geturl()
    except Exception:
        return url


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
            out.add(normalize(abs_url))
    return out


def read_watchlist_targets() -> list[str]:
    if not WATCHLIST.exists():
        return []
    targets: list[str] = []
    for ln in WATCHLIST.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln.startswith("-"):
            continue
        m = re.search(r"(https?://\S+)", ln)
        if not m:
            continue
        u = m.group(1)
        if any(u.startswith(k) for k in WATCH_KEYS):
            targets.append(u)
    # dedupe keep order
    seen: set[str] = set()
    out: list[str] = []
    for u in targets:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def append_news(cands: list[Candidate]) -> Path:
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out = NEWS_DIR / f"{today}.md"

    header = f"\n\n## ✅ 자동 수집 후보(매거진/화보/인터뷰) — {today}\n"
    lines = [header, "- 원칙: 링크만 수집(전문 복사 금지) / 확정 반영은 pages에 분류\n"]
    for c in cands[:40]:
        lines.append(f"- {c.url}  _(from: {c.source})_\n")

    if out.exists():
        txt = out.read_text(encoding="utf-8")
    else:
        txt = f"# {today}\n\n"
    out.write_text(txt + "".join(lines), encoding="utf-8")
    return out


def main() -> None:
    seen = load_seen()
    targets = read_watchlist_targets()

    found: list[Candidate] = []

    for t in targets:
        html = fetch(t)
        if not html:
            continue
        links = extract_links(html, t)
        for u in links:
            if not is_article(u):
                continue
            if u in seen:
                continue
            found.append(Candidate(url=u, source=t))

    # stable dedupe
    uniq: dict[str, Candidate] = {}
    for c in found:
        uniq[c.url] = c
    found = list(uniq.values())

    if found:
        out = append_news(found)
        print(f"collect_magazine_candidates: +{len(found)} candidates -> {out}")
    else:
        print("collect_magazine_candidates: no new candidates")


if __name__ == "__main__":
    main()

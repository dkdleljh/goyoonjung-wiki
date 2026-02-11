#!/usr/bin/env python3
"""Sanitize today's news log to reduce junk links.

Rules (conservative):
- Remove lines that contain a URL pointing to news.google.com/rss/articles (unresolved redirect)
- Remove duplicate URLs (keep first)
- Remove URLs whose domain is NOT in config/allowlist-domains.txt (quality gate)

Does NOT attempt semantic relevance ranking.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE / "news"
ALLOWLIST = BASE / "config" / "allowlist-domains.txt"

URL_RE = re.compile(r"https?://[^\s)]+")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
NAME = "고윤정"


def today_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return NEWS_DIR / f"{today}.md"


def load_allowlist() -> set[str]:
    if not ALLOWLIST.exists():
        return set()
    out: set[str] = set()
    for raw in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith('#'):
            continue
        # allow accidental scheme
        ln = ln.replace('https://', '').replace('http://', '')
        out.add(ln.strip('/'))
    return out


def main() -> int:
    path = today_path()
    if not path.exists():
        print("sanitize_news_log: no file")
        return 0

    allow = load_allowlist()

    lines = path.read_text(encoding="utf-8").splitlines(True)
    out: list[str] = []
    seen: set[str] = set()
    removed = 0
    removed_allow = 0
    deduped = 0

    for ln in lines:
        m = URL_RE.search(ln)
        if not m:
            out.append(ln)
            continue
        url = m.group(0)

        # 제목 기반 품질 게이트: 마크다운 링크 텍스트에 '고윤정'이 없으면 제거
        mm = MD_LINK_RE.search(ln)
        if mm:
            title = mm.group(1)
            if NAME not in title:
                removed_allow += 1
                continue

        if "news.google.com/rss/articles" in url:
            removed += 1
            continue

        # quality gate: allowlist domains only (if allowlist is configured)
        if allow:
            host = urlsplit(url).netloc.lower()
            host = host.split(':', 1)[0]
            if host not in allow:
                removed_allow += 1
                continue

        if url in seen:
            deduped += 1
            continue

        seen.add(url)
        out.append(ln)

    if out != lines:
        path.write_text("".join(out), encoding="utf-8")

    print(f"sanitize_news_log: removed_google={removed} removed_other={removed_allow} deduped={deduped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

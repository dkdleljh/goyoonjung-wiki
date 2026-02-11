#!/usr/bin/env python3
"""Sanitize today's news log to reduce junk links.

Rules (conservative):
- Remove lines that contain a URL pointing to news.google.com/rss/articles (unresolved redirect)
- Remove duplicate URLs (keep first)

Does NOT attempt semantic relevance ranking.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE / "news"

URL_RE = re.compile(r"https?://[^\s)]+")


def today_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return NEWS_DIR / f"{today}.md"


def main() -> int:
    path = today_path()
    if not path.exists():
        print("sanitize_news_log: no file")
        return 0

    lines = path.read_text(encoding="utf-8").splitlines(True)
    out: list[str] = []
    seen: set[str] = set()
    removed = 0
    deduped = 0

    for ln in lines:
        m = URL_RE.search(ln)
        if not m:
            out.append(ln)
            continue
        url = m.group(0)

        if "news.google.com/rss/articles" in url:
            removed += 1
            continue

        if url in seen:
            deduped += 1
            continue

        seen.add(url)
        out.append(ln)

    if out != lines:
        path.write_text("".join(out), encoding="utf-8")

    print(f"sanitize_news_log: removed_google={removed} deduped={deduped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

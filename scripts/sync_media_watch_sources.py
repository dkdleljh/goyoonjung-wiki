#!/usr/bin/env python3
"""Sync domains from sources/media-watch.md into config allowlists.

Purpose:
- "무제한 확장"을 안전하게 하기 위해, 사람이 추가한 watchlist(URL 모음)에서
  도메인만 추출해 allowlist에 보강합니다.

Conservative rules:
- Only adds domains (no removals)
- Only http/https URLs
- Skips very generic domains (google.com, youtube.com etc.) unless already present

Outputs:
- config/allowlist-domains.txt (append missing)

This script does NOT change google-news-sites.txt automatically because that file
requires labels/hints; we keep it curated.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent
MEDIA_WATCH = BASE / "sources" / "media-watch.md"
ALLOWLIST = BASE / "config" / "allowlist-domains.txt"

SKIP = {
    "www.google.com",
    "google.com",
    "news.google.com",
    "search.naver.com",
    "search.daum.net",
    "tv.naver.com",
    "www.youtube.com",
    "youtube.com",
    "youtu.be",
}


def extract_domains(text: str) -> set[str]:
    out: set[str] = set()
    for m in re.finditer(r"https?://[^\s)]+", text):
        u = m.group(0).rstrip(".,;")
        host = urlsplit(u).netloc.lower().split(":", 1)[0]
        if not host or host in SKIP:
            continue
        out.add(host)
    return out


def load_allowlist() -> set[str]:
    if not ALLOWLIST.exists():
        return set()
    out: set[str] = set()
    for raw in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        out.add(ln)
    return out


def main() -> int:
    if not MEDIA_WATCH.exists() or not ALLOWLIST.exists():
        return 0

    domains = extract_domains(MEDIA_WATCH.read_text(encoding="utf-8"))
    cur = load_allowlist()

    add = sorted([d for d in domains if d not in cur])
    if not add:
        print("sync_media_watch_sources: added=0")
        return 0

    with ALLOWLIST.open("a", encoding="utf-8") as f:
        f.write("\n# synced from sources/media-watch.md (auto)\n")
        for d in add:
            f.write(d + "\n")

    print(f"sync_media_watch_sources: added={len(add)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

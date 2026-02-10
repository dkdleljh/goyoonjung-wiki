#!/usr/bin/env python3
"""Build a small cache of candidate official URLs for awards proof filling.

Why:
- Official sites can be slow and search can be rate-limited.
- Crawling from a small set of known official seed URLs is more deterministic.

Input:
- config/awards-url-hints.json (award name -> list of seed urls)

Output:
- config/awards-official-cache.json (award name -> list of same-domain urls)

Safety:
- Only same-domain URLs are included.
- Small crawl: at most 2 seeds per award, 60 links per seed.

No content verification here; verification happens in promote_awards_official_proofs.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HINTS = os.path.join(BASE, "config", "awards-url-hints.json")
OUT = os.path.join(BASE, "config", "awards-official-cache.json")

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
TIMEOUT = 12


def domain(u: str) -> str:
    try:
        return urlparse(u).netloc
    except Exception:
        return ""


def fetch(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def extract_links(html: str, base_url: str, want_domain: str, limit: int = 60) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    seen = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        u = urljoin(base_url, href).split("#")[0]
        if domain(u) != want_domain:
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= limit:
            break
    return out


def main() -> int:
    if not os.path.exists(HINTS):
        return 0
    hints = json.loads(open(HINTS, "r", encoding="utf-8").read())

    cache: dict[str, list[str]] = {}

    for award, seeds in hints.items():
        urls: list[str] = []
        seen = set()
        for seed in (seeds or [])[:2]:
            d = domain(seed)
            if not d:
                continue
            try:
                html = fetch(seed)
            except Exception:
                continue
            links = extract_links(html, seed, d, limit=60)
            for u in links:
                if u in seen:
                    continue
                seen.add(u)
                urls.append(u)
            time.sleep(0.2)
        if urls:
            cache[award] = urls

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")

    print(f"rebuild_awards_official_cache: awards={len(cache)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

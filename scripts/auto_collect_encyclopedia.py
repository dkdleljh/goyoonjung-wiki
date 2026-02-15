#!/usr/bin/env python3
"""Auto-collect encyclopedia updates.
- Source 1: Wikipedia (API) - Reliable
- Source 2: Namuwiki - Unreliable (Cloudflare) -> Just check reachability
- Logic:
  - Wiki: Check last revision ID. If changed from stored metadata, log "Wiki Updated".
  - Namu: HEAD request. If 200, log "Namuwiki Reachable". If 403, log "Namuwiki Blocked".
"""

import json
import os
import sys
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# Allow importing sibling modules when running as a script: `python3 scripts/..py`
sys.path.insert(0, os.path.dirname(__file__))
from cache import get_cache  # noqa: E402

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WIKI_API = (
    "https://ko.wikipedia.org/w/api.php"
    "?action=query"
    "&format=json"
    "&formatversion=2"
    "&titles=%EA%B3%A0%EC%9C%A4%EC%A0%95"
    "&prop=revisions"
    "&rvprop=timestamp|user|comment|ids"
    "&rvlimit=1"
)
NAMU_URL = "https://namu.wiki/w/%EA%B3%A0%EC%9C%A4%EC%A0%95"

USER_AGENT = "goyoonjung-wiki/1.0 (local automation; contact: none)"


def check_wikipedia():
    """Check latest revision via MediaWiki API.

    Important: Wikipedia API may return 403 if User-Agent is missing.
    We always send a descriptive UA, plus basic accept headers.
    """
    cache = get_cache("encyclopedia", ttl=60 * 30)
    cache_key = "wikipedia_ko_goyoonjung_latest"

    try:
        cached = cache.get(cache_key)
        if cached:
            return cached

        req = Request(
            WIKI_API,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Accept-Language": "ko,en;q=0.8",
            },
        )

        with urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            msg = "Wikipedia Check Failed: empty response"
            cache.set(cache_key, msg)
            return msg

        page = pages[0]
        revs = page.get("revisions") or []
        if not revs:
            msg = "Wikipedia Check Failed: no revisions in response"
            cache.set(cache_key, msg)
            return msg

        rev = revs[0]
        timestamp = rev.get("timestamp", "")
        user = rev.get("user", "")
        comment = rev.get("comment", "")
        revid = rev.get("revid")

        msg = f"Wikipedia 업데이트 확인: {timestamp} by {user} (revid={revid}) {comment}".strip()
        cache.set(cache_key, msg)
        return msg

    except Exception as e:
        return f"Wikipedia Check Failed: {e}"

def check_namuwiki():
    # Fake user agent to try passing simple checks
    req = Request(NAMU_URL, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    try:
        with urlopen(req, timeout=5) as r:
            return f"Namuwiki 접근 가능 (Code: {r.getcode()})"
    except HTTPError as e:
        if e.code == 403:
            return "Namuwiki 접근 차단됨 (Cloudflare 403) - 수동 확인 필요"
        return f"Namuwiki Error: {e.code}"
    except Exception as e:
        return f"Namuwiki Check Failed: {e}"

def main():
    print("Checking Encyclopedias...")

    wiki_status = check_wikipedia()
    print(wiki_status)

    namu_status = check_namuwiki()
    print(namu_status)

    # Log to Daily
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(BASE, "news", f"{today}.md")

    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# {today} 로그\n\n## 뉴스/업데이트\n")

    with open(log_path, "a", encoding="utf-8") as f:
        # Check if lines exist to avoid spam
        content = ""
        try:
            with open(log_path, encoding="utf-8") as r:
                content = r.read()
        except (OSError, UnicodeDecodeError):
            pass

        if wiki_status not in content:
            f.write(f"- [Encyclopedia] {wiki_status}\n")
        if namu_status not in content:
            f.write(f"- [Encyclopedia] {namu_status}\n")

if __name__ == "__main__":
    main()

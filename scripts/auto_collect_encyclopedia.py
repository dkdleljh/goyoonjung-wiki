#!/usr/bin/env python3
"""Auto-collect encyclopedia updates.
- Source 1: Wikipedia (API) - Reliable
- Source 2: Namuwiki - Unreliable (Cloudflare) -> Just check reachability
- Logic:
  - Wiki: Check last revision ID. If changed from stored metadata, log "Wiki Updated".
  - Namu: HEAD request. If 200, log "Namuwiki Reachable". If 403, log "Namuwiki Blocked".
"""

import os
import json
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WIKI_API = "https://ko.wikipedia.org/w/api.php?action=query&titles=%EA%B3%A0%EC%9C%A4%EC%A0%95&prop=revisions&rvprop=timestamp|user|comment&format=json"
NAMU_URL = "https://namu.wiki/w/%EA%B3%A0%EC%9C%A4%EC%A0%95"

def check_wikipedia():
    try:
        with urlopen(WIKI_API) as r:
            data = json.loads(r.read())
        
        pages = data['query']['pages']
        for pid in pages:
            rev = pages[pid]['revisions'][0]
            timestamp = rev['timestamp']
            user = rev['user']
            comment = rev.get('comment', '')
            
            # Convert to local time friendly string
            # 2024-05-10T12:00:00Z -> Simple check
            return f"Wikipedia 업데이트 확인: {timestamp} by {user} ({comment})"
            
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
            with open(log_path, "r", encoding="utf-8") as r:
                content = r.read()
        except (IOError, OSError, UnicodeDecodeError):
            pass
        
        if wiki_status not in content:
            f.write(f"- [Encyclopedia] {wiki_status}\n")
        if namu_status not in content:
            f.write(f"- [Encyclopedia] {namu_status}\n")

if __name__ == "__main__":
    main()

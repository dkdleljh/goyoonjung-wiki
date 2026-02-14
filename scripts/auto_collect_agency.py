#!/usr/bin/env python3
"""Auto-collect official updates from MAA Agency website.
- Source: https://maa.co.kr/artists/go-younjung
- Logic:
  - Fetch HTML
  - Extract text content regarding "Drama", "Film", "AD"
  - Limitation: The site is SPA (Nuxt). We fetch the initial HTML payload.
    If the data is in JS, we extract it.
  - Generates a summary of current official listing for comparison.
  - If changes detected (logic simplified for now: just log the current snapshot),
    append to news/YYYY-MM-DD.md
"""

import os
import re
from datetime import datetime
from urllib.request import Request, urlopen

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAA_URL = "https://maa.co.kr/artists/go-younjung"

def fetch_html():
    req = Request(MAA_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req) as resp:
        return resp.read().decode('utf-8')

def extract_works(html):
    # The site renders lists. detailed parsing depends on structure.
    # We'll look for keywords "NETFLIX", "tvN", "Disney+" appearing in the text
    # to reconstruct a rough list of what the agency promotes.

    # Simple regex to find "Title" pattern in the HTML or JSON blob
    # Since it's Nuxt, data might be in window.__NUXT__

    works = []

    # Heuristic: split by lines, find lines with known platforms
    # This is a 'monitoring' script.

    # Let's try to extract cleanly if possible is hard without beautifulsoup,
    # but we can try basic string finding.

    platforms = ["NETFLIX", "tvN", "Disney+", "JTBC", "TVING"]

    # Remove HTML tags for text analysis
    text = re.sub('<[^<]+?>', ' ', html)
    lines = [f.strip() for f in text.splitlines() if f.strip()]

    # Find section "Drama" or "Film"
    capture = False
    for line in lines:
        if "Drama" in line or "Film" in line:
            capture = True
        if "Awards" in line:
            capture = False

        if capture:
            if any(p in line for p in platforms):
                # Clean up multiple spaces
                clean = " ".join(line.split())
                if len(clean) > 5:
                    works.append(clean)

    return works

def main():
    print(f"Fetching MAA: {MAA_URL}")
    try:
        html = fetch_html()
    except Exception as e:
        print(f"Failed to fetch MAA: {e}")
        return

    works = extract_works(html)
    if not works:
        print("No works found (parsing fail or empty).")
        return

    print(f"Found {len(works)} official work entries.")

    # Log to daily news as a "Snapshot"
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(BASE, "news", f"{today}.md")

    snapshot_entry = f"- [Agency] MAA 공식 홈페이지 작품 리스트 확인: {len(works)}건 (변동 확인용)"

    # Avoid duplicate lines
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            if snapshot_entry in f.read():
                return

    # Create/Append
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# {today} 로그\n\n## 뉴스/업데이트\n")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{snapshot_entry}\n")
        # Optional: list them in comment or detail?
        # f.write("  <!-- " + " | ".join(works) + " -->\n")

if __name__ == "__main__":
    main()

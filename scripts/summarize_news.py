#!/usr/bin/env python3
"""Smart Summary for News.
- Goals:
  1. Fetch article content from URL.
  2. Generate a 3-line summary.
  3. (Future) Use LLM API.
  4. (Current) Use simple extraction (first 3 sentences or meta description).
"""

import sys
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def fetch_html(url):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

def heuristic_summary(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Try meta description first
    meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if meta and meta.get('content'):
        desc = meta['content'].strip()
        if len(desc) > 30:
            return f"Tip: {desc[:200]}..."

    # Fallback: Extract paragraphs
    paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 50]
    if paragraphs:
        # Return first 2 paragraphs combined
        summary = " ".join(paragraphs[:2])
        return summary[:300] + "..."

    return "요약 실패 (본문 추출 불가)"

def main():
    if len(sys.argv) < 2:
        print("Usage: summarize_news.py <URL>")
        return

    url = sys.argv[1]
    html = fetch_html(url)
    if not html:
        print("Error: Could not fetch URL")
        return

    summary = heuristic_summary(html)
    print(summary)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Auto-collect news from Google News RSS.
- Source: Google News RSS (keyword: "고윤정")
- Logic:
  - Fetch RSS XML using urllib
  - Parse with xml.etree.ElementTree (no external deps)
  - Filter items published within last 24h
  - Deduplicate against seen-urls.txt
  - Classify into: [인터뷰], [작품], [화보], [일반]
  - Append to pages/news/YYYY-MM-DD.md
"""

import logging
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen, Request
from email.utils import parsedate_to_datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))
import db_manager
import config_loader
import relevance

CONF = config_loader.load_config()
RSS_URL = CONF.get('rss_url', "https://news.google.com/rss/search?q=%EA%B3%A0%EC%9C%A4%EC%A0%95+when:1d&hl=ko&gl=KR&ceid=KR:ko")


def normalize_rss_url(url: str) -> str:
    try:
        url.encode('ascii')
        return url
    except UnicodeEncodeError:
        return quote(url, safe=':/?&=+%\'')

BASE = SCRIPT_DIR.parent


def get_today_news_path() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(BASE, "news", f"{today}.md")

# Removed load_seen_urls and add_to_seen, using db_manager directly

def clean_title(title):
    return title.replace("<b>", "").replace("</b>", "").replace("&quot;", "'")

def classify(title):
    if "인터뷰" in title:
        return "Interview"
    if any(k in title for k in ["무빙", "환혼", "이 사랑 통역 되나요", "슬기로울 전공의생활", "전공의생활"]):
        return "Work"
    if any(k in title for k in ["화보", "보그", "엘르", "에스콰이어", "마리끌레르"]):
        return "Pictorial"
    return "General"

def decode_google_news_url(source_url):
    import urllib.request
    try:
        req = urllib.request.Request(source_url, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.geturl()
    except:
        return source_url

def fetch_rss():
    url = normalize_rss_url(RSS_URL)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req) as response:
        return response.read()

def main():
    print(f"Fetching RSS: {RSS_URL}")
    try:
        xml_data = fetch_rss()
    except Exception as e:
        print(f"Failed to fetch RSS: {e}")
        return

    root = ET.fromstring(xml_data)
    channel = root.find("channel")
    if channel is None:
        print("Invalid RSS format")
        return

    new_items = []

    for item in channel.findall("item"):
        title_elem = item.find("title")
        link_elem = item.find("link")
        pubDate_elem = item.find("pubDate")
        source_elem = item.find("source")

        if title_elem is None or link_elem is None:
            continue

        title = clean_title(title_elem.text)
        origin_link = link_elem.text
        
        # Check duplicate title in current batch
        if any(x['title'] == title for x in new_items):
            continue

        real_url = decode_google_news_url(origin_link)
        
        # Check DB
        if db_manager.is_url_seen(real_url):
            continue

        source_text = source_elem.text if source_elem is not None else "Google News"

        desc_el = item.find("description")
        desc = desc_el.text if desc_el is not None and desc_el.text else ""

        # Relevance gate (precision-first)
        if not relevance.is_relevant(title, real_url, source_text, desc):
            continue

        category = classify(title)
        
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        if pubDate_elem is not None:
            try:
                dt = parsedate_to_datetime(pubDate_elem.text)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        new_items.append({
            "title": title,
            "url": real_url,
            "date": date_str,
            "category": category,
            "source": source_text
        })
        
        db_manager.add_seen_url(real_url, source='google_news')

    if not new_items:
        print("No new items found.")
        return

    log_path = get_today_news_path()
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# {datetime.now().strftime('%Y-%m-%d')} 로그\n\n## 뉴스/업데이트\n")

    with open(log_path, "a", encoding="utf-8") as f:
        for item in new_items:
            f.write(f"- [{item['category']}] [{item['title']}]({item['url']}) - {item['source']} ({item['date']})\n")
    
    print(f"Added {len(new_items)} items to {log_path}")

if __name__ == "__main__":
    main()

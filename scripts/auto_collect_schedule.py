#!/usr/bin/env python3
"""Auto-collect schedule from recent news logic.
- Analyzes `news/YYYY-MM-DD.md` (recent logs)
- Looks for keywords: "공개", "첫방", "개봉", "침석", "제작발표회" combined with future dates.
- Heuristic: strict pattern matching for dates in titles.
- Updates `pages/schedule.md` with [Upcoiming] Suggestions.
"""

import os
import re
from datetime import datetime, timedelta

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCHEDULE_MD = os.path.join(BASE, "pages", "schedule.md")
NEWS_DIR = os.path.join(BASE, "news")

PATTERNS = [
    (r"(\d{1,2})월\s*(\d{1,2})일", "MM-DD"),
    (r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", "YYYY-MM-DD"),
    (r"(\d{1,2})\.(\d{1,2})", "MM.DD"),  # 1.16 like patterns
]

KEYWORDS = ["공개", "첫방", "방송", "개봉", "참석", "개최", "발매"]

def scan_recent_news(days=3):
    """Scan last N days of news logs."""
    found = []
    today = datetime.now()
    for i in range(days):
        d = today - timedelta(days=i)
        fname = d.strftime("%Y-%m-%d.md")
        path = os.path.join(NEWS_DIR, fname)
        if not os.path.exists(path):
            continue
        
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("- "): continue
                # Line format: - [Category] [Title](Link) ...
                # Extract Title
                m = re.search(r"\[(.*?)\]\((.*?)\)", line)
                if not m: continue
                title = m.group(1)
                link = m.group(2)
                
                # Check keywords
                if not any(k in title for k in KEYWORDS):
                    continue
                    
                # Extract Potential Date
                future_date = extract_future_date(title, today)
                if future_date:
                    found.append({
                        "date": future_date.strftime("%Y-%m-%d"),
                        "title": title,
                        "link": link
                    })
    return found

def extract_future_date(text, anchor_date):
    """Try to find a date in text that is in the future relative to anchor_date."""
    # Pattern matching
    # 1. MM월 DD일
    m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        try:
            # Assume current year or next year
            d = datetime(anchor_date.year, month, day)
            if d < anchor_date: # If looking back, maybe next year? (e.g. in Dec news says Jan)
                 d = datetime(anchor_date.year + 1, month, day)
            return d
        except (ValueError, OSError):
            pass
        
    return None

def update_schedule(items):
    if not items: return
    
    with open(SCHEDULE_MD, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check duplicates strictly by Link or Title
    new_entries = []
    for item in items:
        if item['link'] in content: continue
        # Format entry
        entry = f"""
- 날짜/시간: {item['date']} (추정)
- 구분: 기타(뉴스기반추정)
- 제목: {item['title']}
- 대상: 고윤정
- 장소/플랫폼: -
- 상태: 보도(1차)
- 링크(공식/원문): {item['link']}
- id: {item['link']}
- 메모: 자동 수집됨. 정확한 시간/장소 확인 필요.
"""
        new_entries.append(entry)
        
    if not new_entries:
        print("No new schedule entries to add.")
        return

    # Insert into Upcoming
    # Finding "## 다가오는 일정 (Upcoming)"
    header = "## 다가오는 일정 (Upcoming)"
    if header not in content:
        print("Cannot find Upcoming section.")
        return
        
    parts = content.split(header)
    # Insert after header
    insertion = "\n".join(new_entries)
    new_content = parts[0] + header + "\n" + insertion + parts[1]
    
    with open(SCHEDULE_MD, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Added {len(new_entries)} schedule suggestions.")

def main():
    print("Scanning news for schedule...")
    items = scan_recent_news()
    if items:
        update_schedule(items)
    else:
        print("No schedule info found in recent news.")

if __name__ == "__main__":
    main()

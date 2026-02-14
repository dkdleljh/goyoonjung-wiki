#!/usr/bin/env python3
"""Context Awareness: Update Profile Status.
- Scans recent news for keywords like "crank in", "filming", "casting confirmed".
- Updates `pages/profile.md` 'Current Status' field.
"""
# noqa: E701

import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROFILE_MD = BASE / 'pages' / 'profile.md'
NEWS_DIR = BASE / 'news'

KEYWORDS = {
    "촬영": "촬영 중",
    "크랭크인": "촬영 중",
    "캐스팅": "차기작 준비/검토",
    "검토": "차기작 검토 중",
    "공개": "홍보 활동 중",
    "종영": "휴식/차기작 검토"
}

def get_recent_keywords(days=7):
    # Scan last N days of news

    # Priority: Filming (3) > Promotion (2) > Casting (1)

    today = datetime.now()
    # Simple scan of latest log
    latest_log = NEWS_DIR / f"{today.strftime('%Y-%m-%d')}.md"
    if not latest_log.exists():
        return None

    content = latest_log.read_text(encoding='utf-8')

    if "촬영" in content or "크랭크인" in content:
        return "촬영 중 (최신 뉴스 기반)"
    if "공개" in content or "제작발표회" in content:
        return "작품 홍보/공개 중"
    if "캐스팅" in content and "확정" in content:
        return "차기작 준비 중"

    return None

def update_profile(new_status):
    if not new_status: return

    content = PROFILE_MD.read_text(encoding='utf-8')

    # Regex find "- 상태: ..."
    # We want to replace it.

    # Pattern: ^- 상태: (.*)$
    pattern = r"(- 상태: )(.*)"

    if re.search(pattern, content, re.MULTILINE):
        # Check if already same
        m = re.search(pattern, content, re.MULTILINE)
        current = m.group(2).strip()

        if current == new_status:
            print(f"Status already up to date: {current}")
            return

        new_content = re.sub(pattern, f"\\1{new_status}", content, count=1)
        PROFILE_MD.write_text(new_content, encoding='utf-8')
        print(f"Updated Profile Status: {current} -> {new_status}")
    else:
        print("Could not find 'Status' field in profile.md")

def main():
    print("Checking for status updates...")
    status = get_recent_keywords()
    if status:
        update_profile(status)
    else:
        print("No status change detected from recent news.")

if __name__ == "__main__":
    main()

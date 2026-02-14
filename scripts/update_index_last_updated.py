#!/usr/bin/env python3
"""Update index.md and index.en.md 'last updated' + today's log link.

Deterministic rule:
- Use Asia/Seoul date (YYYY-MM-DD)
- Point 'today log' to news/YYYY-MM-DD.md

This is safe and does not fetch the web.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = ZoneInfo("Asia/Seoul")

def today_ymd() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def update_index_md(path: str, ymd: str) -> bool:
    s = read(path)
    s2 = s

    # KR
    s2 = re.sub(r"^- 마지막 업데이트:\s*\*\*(\d{4}-\d{2}-\d{2})\*\*\s*$", f"- 마지막 업데이트: **{ymd}**", s2, flags=re.M)

    # Any '- 오늘 로그...' line that links to news/YYYY-MM-DD.md
    s2 = re.sub(
        r"^(-\s*오늘\s*로그[^:]*:\s*\[`news/)(\d{4}-\d{2}-\d{2})(\.md`\]\(news/)\2(\.md\)\s*)$",
        rf"\g<1>{ymd}\g<3>{ymd}\g<4>",
        s2,
        flags=re.M,
    )

    # EN
    s2 = re.sub(r"^- Last updated:\s*\*\*(\d{4}-\d{2}-\d{2})\*\*\s*$", f"- Last updated: **{ymd}**", s2, flags=re.M)

    # Any '- Today’s log...' line that links to news/YYYY-MM-DD.md
    s2 = re.sub(
        r"^(-\s*Today[’']s\s*log[^:]*:\s*\[`news/)(\d{4}-\d{2}-\d{2})(\.md`\]\(news/)\2(\.md\)\s*)$",
        rf"\g<1>{ymd}\g<3>{ymd}\g<4>",
        s2,
        flags=re.M,
    )

    if s2 != s:
        write(path, s2)
        return True
    return False


def main() -> int:
    ymd = today_ymd()
    changed = False
    for fname in ("index.md", "index.en.md"):
        path = os.path.join(BASE, fname)
        if os.path.exists(path):
            changed = update_index_md(path, ymd) or changed
    print(f"update_index_last_updated: {ymd} changed={changed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

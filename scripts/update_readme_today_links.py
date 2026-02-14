#!/usr/bin/env python3
"""Update README.md 'today log' link to the current date (Asia/Seoul).

Why:
- README contains human-friendly quick links.
- We still keep template text (news/YYYY-MM-DD.md) elsewhere, but the Quick Links
  should point to the actual file for today.

Safe:
- No web access.
- Pure string/regex substitution.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = ZoneInfo("Asia/Seoul")


def today_ymd() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def update_readme(path: str, ymd: str) -> bool:
    s = read(path)
    s2 = s

    # Quick Links: make '오늘 로그' point to today's file
    s2 = re.sub(
        r"^(-\s*오늘\s*로그\s*→)\s*`news/YYYY-MM-DD\.md`\s*$",
        rf"\g<1> [`news/{ymd}.md`](news/{ymd}.md)",
        s2,
        flags=re.M,
    )

    # Start-here section: update the example link date
    s2 = re.sub(
        r"\(예:\s*\[`news/(\d{4}-\d{2}-\d{2})\.md`\]\(news/\1\.md\)\)",
        rf"(예: [`news/{ymd}.md`](news/{ymd}.md))",
        s2,
    )

    if s2 != s:
        write(path, s2)
        return True
    return False


def main() -> int:
    ymd = today_ymd()
    path = os.path.join(BASE, "README.md")
    if not os.path.exists(path):
        print("update_readme_today_links: README.md missing")
        return 0
    changed = update_readme(path, ymd)
    print(f"update_readme_today_links: {ymd} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

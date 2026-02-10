#!/usr/bin/env python3
"""Fill endorsements '링크(공식 발표)' without human approval (fallback mode).

Problem:
- Some official brand sites are blocked/timeout in this environment.
- Fully unmanned automation should not depend on the user providing URLs.

Policy (unmanned fallback):
- If '링크(공식 발표)' is '(확인 필요)' but '링크(공식 영상/캠페인)' exists and looks like an official channel post
  (YouTube/Instagram/official-domain), then copy that URL into '링크(공식 발표)'.

This changes the meaning slightly to: "official primary post" (campaign/announcement) rather than strictly a press release.

Safety:
- Only uses links already present in the entry.
- Does not add new claims.

Limits:
- Max fills per run: 2
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from urllib.parse import urlparse

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENDO_FILES = [
    os.path.join(BASE, "pages", "endorsements", "beauty.md"),
    os.path.join(BASE, "pages", "endorsements", "fashion.md"),
    os.path.join(BASE, "pages", "endorsements", "lifestyle.md"),
]

ALLOWED_FALLBACK_DOMAINS = {
    "youtu.be",
    "www.youtube.com",
    "youtube.com",
    "www.instagram.com",
    "instagram.com",
}


@dataclass
class Block:
    file: str
    start: int
    end: int
    brand_line: str


def read_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines(True)


def write_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def main() -> int:
    filled = 0

    for f in ENDO_FILES:
        if not os.path.exists(f):
            continue
        lines = read_lines(f)
        i = 0
        changed = False
        while i < len(lines):
            if not lines[i].startswith("- 브랜드/회사명:"):
                i += 1
                continue
            start = i
            brand_line = lines[i].strip()
            end = i + 1
            while end < len(lines) and not lines[end].startswith("- 브랜드/회사명:") and not lines[end].startswith("## "):
                end += 1

            block = "".join(lines[start:end])
            if "링크(공식 발표): (확인 필요)" not in block:
                i = end
                continue

            m = re.search(r"링크\(공식 영상/캠페인\):\s*(https?://\S+)", block)
            if not m:
                i = end
                continue
            camp = m.group(1).strip()
            if domain(camp) not in ALLOWED_FALLBACK_DOMAINS:
                i = end
                continue

            # replace the announce line within this block
            for k in range(start, end):
                if lines[k].strip() == "- 링크(공식 발표): (확인 필요)":
                    lines[k] = f"  - 링크(공식 발표): {camp} (자동: 공식 채널 게시물로 대체)\n"
                    changed = True
                    filled += 1
                    break

            if filled >= 2:
                break
            i = end

        if changed:
            write_lines(f, lines)

        if filled >= 2:
            break

    print(f"promote_endorsements_announce_fallback: filled={filled}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

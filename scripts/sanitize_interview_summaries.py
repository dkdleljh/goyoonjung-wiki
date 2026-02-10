#!/usr/bin/env python3
"""Sanitize interview summaries in pages/interviews.md.

Problem:
- Some entries accumulated huge duplicated bullet lists under '- 요약(3~5줄):'.

Fix (unmanned, deterministic):
- For each entry block:
  - Find '- 요약(3~5줄):'
  - Collect following indented bullets ('  - ...')
  - De-duplicate bullets (preserve order)
  - Keep at most MAX_BULLETS
  - Remove boilerplate-like bullets (share/nav)

No web access.
"""

from __future__ import annotations

import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILE = os.path.join(BASE, "pages", "interviews.md")

MAX_BULLETS = 5

BAD_SUBSTR = [
    "랭킹뉴스",
    "URL복사",
    "글씨 작게보기",
    "글씨 크게보기",
    "페이스북",
    "트위터",
    "네이버",
    "카카오",
    "공유",
]


def main() -> int:
    if not os.path.exists(FILE):
        return 0

    lines = open(FILE, "r", encoding="utf-8").read().splitlines(True)

    changed = False
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("- 날짜:"):
            start = i
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("- 날짜:") and not lines[j].startswith("## "):
                j += 1
            end = j

            # locate summary header
            k = start
            while k < end:
                if lines[k].strip() == "- 요약(3~5줄):":
                    b0 = k + 1
                    b1 = b0
                    bullets = []
                    while b1 < end and lines[b1].lstrip().startswith("  -"):
                        txt = lines[b1].strip()[3:].strip()
                        bullets.append(txt)
                        b1 += 1

                    if bullets:
                        # sanitize
                        out = []
                        seen = set()
                        for b in bullets:
                            if any(x in b for x in BAD_SUBSTR):
                                continue
                            key = re.sub(r"\s+", "", b)
                            if key in seen:
                                continue
                            seen.add(key)
                            out.append(b)
                            if len(out) >= MAX_BULLETS:
                                break

                        new_lines = [f"  - {b}\n" for b in out]
                        if new_lines != lines[b0:b1]:
                            lines[b0:b1] = new_lines
                            changed = True
                    break
                k += 1

            i = end
        else:
            i += 1

    if changed:
        with open(FILE, "w", encoding="utf-8") as f:
            f.write("".join(lines))

    print(f"sanitize_interview_summaries: changed={int(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

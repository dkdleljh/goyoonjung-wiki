#!/usr/bin/env python3
"""Remove user-facing URL-hunting suggestion blocks from a news file.

Unmanned mode goal: the user should not be asked to find/approve URLs.

Removes blocks:
- AUTO-PROFILE-PROOF-SUGGEST
- AUTO-ENDORSEMENTS-OFFICIAL-ANNOUNCE-SUGGEST
- AUTO-AWARDS-PROOF-SUGGEST
- AUTO-DAILY-PROMOTION-TASK (old approval-based versions may contain instructions)

Keeps the rest of the news log intact.
"""

from __future__ import annotations

import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NEWS = os.path.join(BASE, "news")

BLOCKS = [
    ("<!-- AUTO-PROFILE-PROOF-SUGGEST:START -->", "<!-- AUTO-PROFILE-PROOF-SUGGEST:END -->"),
    ("<!-- AUTO-ENDORSEMENTS-OFFICIAL-ANNOUNCE-SUGGEST:START -->", "<!-- AUTO-ENDORSEMENTS-OFFICIAL-ANNOUNCE-SUGGEST:END -->"),
    ("<!-- AUTO-AWARDS-PROOF-SUGGEST:START -->", "<!-- AUTO-AWARDS-PROOF-SUGGEST:END -->"),
]


def strip(md: str) -> str:
    out = md
    for a, b in BLOCKS:
        if a in out and b in out:
            pre = out.split(a)[0]
            post = out.split(b, 1)[1]
            out = pre.rstrip() + "\n\n" + post.lstrip()
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: strip_url_hunt_blocks.py <YYYY-MM-DD>")
        return 2
    day = sys.argv[1]
    path = os.path.join(NEWS, f"{day}.md")
    if not os.path.exists(path):
        return 0
    s = open(path, "r", encoding="utf-8").read()
    t = strip(s)
    if t != s:
        with open(path, "w", encoding="utf-8") as f:
            f.write(t)
    print("strip_url_hunt_blocks: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

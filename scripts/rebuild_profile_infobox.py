#!/usr/bin/env python3
"""Generate a Wikipedia-like infobox table for pages/profile.md (unmanned).

Writes/updates a block between markers.
No web access.
"""

from __future__ import annotations

import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROFILE = os.path.join(BASE, "pages", "profile.md")

START = "<!-- AUTO-INFOBOX:START -->"
END = "<!-- AUTO-INFOBOX:END -->"


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def extract_line(md: str, prefix: str) -> str | None:
    for ln in md.splitlines():
        if ln.strip().startswith(prefix):
            return ln.split(":", 1)[1].strip()
    return None


def build(md: str) -> str:
    name = extract_line(md, "- 이름") or "고윤정"
    birth = extract_line(md, "- 출생") or "1996-04-22"
    job = extract_line(md, "- 직업") or "배우"
    years = extract_line(md, "- 활동 기간") or "2018년 ~ 현재"
    agency = extract_line(md, "- 소속사") or "MAA"

    rows = [
        START,
        "| 항목 | 내용 |",
        "|---|---|",
        f"| 이름 | {name} |",
        f"| 출생 | {birth} |",
        f"| 직업 | {job} |",
        f"| 활동 | {years} |",
        f"| 소속사 | {agency} |",
        END,
        "",
    ]
    return "\n".join(rows)


def upsert(md: str, block: str) -> str:
    if START in md and END in md:
        pre = md.split(START)[0]
        post = md.split(END, 1)[1]
        return pre.rstrip() + "\n\n" + block + "\n" + post.lstrip()

    # insert after title and intro lines (after first blank following title)
    lines = md.splitlines(True)
    # find first blank line after title
    idx_title = None
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            idx_title = i
            break
    if idx_title is None:
        return block + md
    j = idx_title + 1
    while j < len(lines) and lines[j].strip() != "":
        j += 1
    # include the blank line
    if j < len(lines):
        j += 1
    return "".join(lines[:j]) + block + "\n" + "".join(lines[j:])


def main() -> int:
    if not os.path.exists(PROFILE):
        return 0
    md = read(PROFILE)
    block = build(md)
    out = upsert(md, block)
    if out != md:
        write(PROFILE, out)
        print("rebuild_profile_infobox: updated")
    else:
        print("rebuild_profile_infobox: nochange")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

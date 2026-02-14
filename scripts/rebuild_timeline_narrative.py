#!/usr/bin/env python3
"""Rebuild a narrative timeline block (2~3 sentences per year) from existing data.

Updates pages/timeline.md between markers.
No web access.

Sources:
- pages/filmography.md (works by year)
- pages/awards.md (award years)

Safety:
- Only summarizes already-recorded items.
- No speculation.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TIMELINE = os.path.join(BASE, "pages", "timeline.md")
FILM = os.path.join(BASE, "pages", "filmography.md")
AWARDS = os.path.join(BASE, "pages", "awards.md")

START = "<!-- AUTO-TIMELINE-NARRATIVE:START -->"
END = "<!-- AUTO-TIMELINE-NARRATIVE:END -->"

TABLE_ROW_RE = re.compile(r"^\|\s*(20\d{2})\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*$")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def film_by_year() -> dict[int, list[str]]:
    out: dict[int, list[str]] = defaultdict(list)
    if not os.path.exists(FILM):
        return out
    for ln in read(FILM).splitlines():
        m = TABLE_ROW_RE.match(ln.strip())
        if not m:
            continue
        y, platform, title, role, note, proof = [x.strip() for x in m.groups()]
        out[int(y)].append(f"{title}({platform})")
    return out


def awards_by_year() -> dict[int, list[str]]:
    out: dict[int, list[str]] = defaultdict(list)
    if not os.path.exists(AWARDS):
        return out
    for ln in read(AWARDS).splitlines():
        if not ln.startswith("|"):
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 6:
            continue
        if not re.fullmatch(r"20\d{2}", cols[0]):
            continue
        y = int(cols[0])
        award = cols[1]
        result = cols[4]
        out[y].append(f"{award}({result})")
    return out


def build_block() -> str:
    films = film_by_year()
    awards = awards_by_year()
    years = sorted(set(films.keys()) | set(awards.keys()))

    lines = [
        START,
        "## 🧾 연도별 요약(자동 · 서술형)",
        "> 메모: 위키백과처럼 ‘읽는 타임라인’ 느낌을 만들기 위한 자동 요약입니다. (추측/평가 없음)",
        "",
    ]

    for y in years:
        items = films.get(y, [])
        aw = awards.get(y, [])
        s1 = ""
        if items:
            shown = ", ".join(items[:3])
            s1 = f"- {y}: 드라마/영화 활동: {shown}" + (" 외" if len(items) > 3 else "")
        else:
            s1 = f"- {y}: (기록 보강 중)"
        lines.append(s1)
        if aw:
            shown_aw = ", ".join(aw[:2])
            lines.append(f"  - 수상/노미네이트 기록: {shown_aw}" + (" 외" if len(aw) > 2 else ""))
        lines.append("")

    lines += [END, ""]
    return "\n".join(lines)


def upsert(md: str, block: str) -> str:
    if START in md and END in md:
        pre = md.split(START)[0]
        post = md.split(END, 1)[1]
        return pre.rstrip() + "\n\n" + block + post.lstrip()

    # insert after intro
    lines = md.splitlines(True)
    idx = 0
    if lines and lines[0].startswith("# "):
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "":
            idx += 1
        if idx < len(lines):
            idx += 1
    return "".join(lines[:idx]) + block + "\n" + "".join(lines[idx:])


def main() -> int:
    if not os.path.exists(TIMELINE):
        return 0
    md = read(TIMELINE)
    block = build_block()
    out = upsert(md, block)
    if out != md:
        write(TIMELINE, out)
    print("rebuild_timeline_narrative: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

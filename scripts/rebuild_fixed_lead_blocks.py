#!/usr/bin/env python3
"""Build fixed, always-on lead blocks for index/profile (unmanned).

Creates/updates between markers in:
- index.md (KO)
- index.en.md (EN)
- pages/profile.md (KO)

Data sources:
- pages/filmography.md (notable works)
- pages/awards.md (counts of awards rows)

No web access.
"""

from __future__ import annotations

import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FILES = [
    os.path.join(BASE, "index.md"),
    os.path.join(BASE, "index.en.md"),
    os.path.join(BASE, "pages", "profile.md"),
]
FILM = os.path.join(BASE, "pages", "filmography.md")
AWARDS = os.path.join(BASE, "pages", "awards.md")

START = "<!-- AUTO-FIXED-LEAD:START -->"
END = "<!-- AUTO-FIXED-LEAD:END -->"


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def extract_notable_works(limit: int = 6) -> list[str]:
    if not os.path.exists(FILM):
        return []
    md = read(FILM)
    works = []
    lines = md.splitlines()
    in_table = False
    for ln in lines:
        if ln.strip() == "## 드라마/시리즈":
            in_table = False
            continue
        if ln.startswith("## ") and "드라마/시리즈" not in ln and works:
            break
        if ln.startswith("|") and "연도" in ln and "작품" in ln:
            in_table = True
            continue
        if in_table:
            if not ln.startswith("|"):
                if works:
                    break
                continue
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cols) >= 3 and cols[2] and cols[2] != "작품":
                w = cols[2]
                if w not in works and w != "---":
                    works.append(w)
            if len(works) >= limit:
                break
    return works


def count_awards_rows() -> int:
    if not os.path.exists(AWARDS):
        return 0
    md = read(AWARDS)
    n = 0
    for ln in md.splitlines():
        if ln.startswith("|") and re.search(r"\|\s*20\d{2}\s*\|", ln):
            n += 1
    return n


def block_ko() -> str:
    works = extract_notable_works()
    works_txt = ", ".join(f"*{w}*" for w in works) if works else "(대표작 보강 중)"
    awards_n = count_awards_rows()
    return "\n".join([
        START,
        "## 🧠 리드(확정 포맷 · 자동)",
        "> 메모: 이 블록은 ‘초안’이 아니라 **항상 같은 포맷으로 자동 생성**됩니다. (무인 운영) ",
        "",
        "고윤정(Go Youn-jung, 1996-04-22~)은 대한민국의 배우이다.",
        f"주요 출연작으로 {works_txt} 등이 있다.",
        f"이 위키는 작품·화보·광고·인터뷰·출연/행사 기록을 링크 중심(저작권 안전)으로 누적하며, (수상/노미네이트 표: {awards_n}행) 항목은 공식 근거 확보 시 순차적으로 확정한다.",
        END,
        "",
    ])


def block_en() -> str:
    works = extract_notable_works()
    works_txt = ", ".join(works[:6]) if works else "(notable works in progress)"
    return "\n".join([
        START,
        "## 🧠 Lead (fixed format · auto)",
        "> Note: This block is generated in a fixed format for unmanned operation.",
        "",
        "Go Youn-jung (born 1996-04-22) is a South Korean actress.",
        f"Notable works include {works_txt}.",
        "This wiki is a link-first (copyright-safe) archive of works, pictorials, endorsements, interviews, and appearances/events, with primary-source verification when available.",
        END,
        "",
    ])


def upsert(md: str, block: str) -> str:
    if START in md and END in md:
        pre = md.split(START)[0]
        post = md.split(END, 1)[1]
        return pre.rstrip() + "\n\n" + block + post.lstrip()

    # insert after first '---' or after top summary area; fallback: after title line + blank
    if "---" in md:
        a, b = md.split("---", 1)
        return a.rstrip() + "\n\n---\n\n" + block + b.lstrip()

    lines = md.splitlines(True)
    idx = 0
    if lines and lines[0].startswith("# "):
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "":
            idx += 1
        if idx < len(lines):
            idx += 1
    return "".join(lines[:idx]) + block + "".join(lines[idx:])


def main() -> int:
    for path in FILES:
        if not os.path.exists(path):
            continue
        md = read(path)
        if path.endswith("index.en.md"):
            block = block_en()
        else:
            block = block_ko()
        out = upsert(md, block)
        if out != md:
            write(path, out)
    print("rebuild_fixed_lead_blocks: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

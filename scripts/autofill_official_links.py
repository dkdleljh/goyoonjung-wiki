#!/usr/bin/env python3
"""Autofill '공식 링크' / '출처' sections using existing URLs in each page.

This is conservative: it only reuses URLs that already exist in the markdown.
It does NOT web-fetch or invent facts.

Targets:
- pages/works/*.md

Rules:
- Replace placeholder '- (추가 필요)' under '## 공식 링크' with up to N URLs that look official.
- Replace placeholder under '## 출처' with MAA profile if present in file; otherwise keep placeholder.

Official URL heuristics:
- youtube.com / youtu.be (official trailers/clips)
- netflix.com
- disneyplus.com
- tvn.cjenm.com
- tv.jtbc.co.kr
- program.tving.com / tving.com

"""

from __future__ import annotations

import re
from pathlib import Path

WORKS_DIR = Path("pages/works")

URL_RE = re.compile(r"https?://[^\s)\]>]+")

OFFICIAL_HINTS = [
    "youtube.com",
    "youtu.be",
    "netflix.com",
    "disneyplus.com",
    "tvn.cjenm.com",
    "tv.jtbc.co.kr",
    "tving.com",
    "program.tving.com",
]


def pick_official(urls: list[str], limit: int = 6) -> list[str]:
    seen: set[str] = set()
    picked: list[str] = []

    def add(u: str) -> None:
        if u in seen:
            return
        seen.add(u)
        picked.append(u)

    # Prefer non-search entity pages first
    priority = []
    rest = []
    for u in urls:
        if any(h in u for h in OFFICIAL_HINTS):
            if "/search/" in u or "?s=" in u:
                rest.append(u)
            else:
                priority.append(u)

    for u in priority + rest:
        add(u)
        if len(picked) >= limit:
            break

    return picked


def ensure_section(txt: str, heading: str) -> str:
    if f"\n## {heading}\n" in txt or txt.startswith(f"## {heading}\n"):
        return txt
    return txt + ("\n" if not txt.endswith("\n") else "") + f"\n## {heading}\n- (추가 필요)\n"


def replace_placeholder_block(txt: str, heading: str, lines: list[str]) -> str:
    # Replace the first occurrence of a placeholder list item under the heading.
    # Very simple block replace: find heading line, then next lines until blank line.
    pat = re.compile(rf"(^##\s+{re.escape(heading)}\s*$)([\s\S]*?)(\n\n|\Z)", re.M)
    m = pat.search(txt)
    if not m:
        return txt

    block = m.group(2)
    if "(추가 필요" not in block and "- (추가 필요)" not in block:
        return txt

    new_block = "\n" + "\n".join(lines) + "\n"
    new_txt = txt[: m.start(2)] + new_block + txt[m.end(2) :]
    return new_txt


def main() -> None:
    changed = 0
    scanned = 0

    for p in sorted(WORKS_DIR.glob("*.md")):
        if p.name == "by-year.md":
            continue
        scanned += 1
        txt = p.read_text(encoding="utf-8", errors="ignore")

        urls = URL_RE.findall(txt)
        official = pick_official(urls)

        txt2 = txt
        txt2 = ensure_section(txt2, "공식 링크")
        txt2 = ensure_section(txt2, "출처")

        if official:
            lines = [f"- {u}" for u in official]
            txt2 = replace_placeholder_block(txt2, "공식 링크", lines)

        # 출처: prefer official URLs already present in file; also include MAA profile if present
        source_lines: list[str] = []
        for u in official[:3]:
            source_lines.append(f"- (S) 공식 링크: {u}")

        maa = "https://maa.co.kr/artists/go-younjung"
        if maa in txt2:
            source_lines.append(f"- (S) 소속사(MAA) 아티스트 프로필: {maa}")

        if source_lines:
            txt2 = replace_placeholder_block(txt2, "출처", source_lines)

        if txt2 != txt:
            p.write_text(txt2, encoding="utf-8")
            changed += 1

    print(f"autofill_official_links: scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()

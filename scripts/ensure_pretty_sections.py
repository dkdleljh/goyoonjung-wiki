#!/usr/bin/env python3
"""Ensure a minimal "pretty + detailed" scaffold exists across markdown pages.

Goal
- Make pages consistently readable without inventing facts.
- Add a small, optional overview section that can be filled over time.

What it does
- For markdown files under: pages/, docs/, sources/ (and top-level selected)
- Skips: news/ (automation logs), templates/, auto-generated reports
- If a file has an H1 and is missing a "## 한눈에 보기" section, inserts it after the H1 block.

This is structural only: placeholders are clearly marked as (추가 필요).
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

TARGET_DIRS = [BASE / "pages", BASE / "docs", BASE / "sources"]
TOP_LEVEL_FILES = [BASE / "README.md", BASE / "CONTRIBUTING.md", BASE / "CHANGELOG.md"]

SKIP_FILES = {
    "pages/link-health.md",
    "pages/lint-report.md",
    "pages/quality-report.md",
    "pages/daily-report.md",
    "pages/content-gaps.md",
    "pages/system_status.md",
}

H1_RE = re.compile(r"^#\s+.+")
H2_OVERVIEW = "## 한눈에 보기"

OVERVIEW_BLOCK = (
    "## 한눈에 보기\n\n"
    "- 한 줄 요약: (추가 필요)\n"
    "- 핵심 링크: (추가 필요 — 공식/원문 우선)\n"
    "- 상태: (추가 필요 — 근거 수준 S/A/2차/보강 필요)\n\n"
)


def should_skip(path: Path) -> bool:
    rel = path.relative_to(BASE).as_posix()
    if rel.startswith("news/"):
        return True
    if "/templates/" in rel:
        return True
    if rel in SKIP_FILES:
        return True
    return False


def has_h2(text: str, h2: str) -> bool:
    return f"\n{h2}\n" in text or text.startswith(f"{h2}\n")


def insert_after_h1(text: str, block: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    # Find first H1 line
    h1_idx = None
    for i, ln in enumerate(lines):
        if H1_RE.match(ln.strip()):
            h1_idx = i
            break
    if h1_idx is None:
        return text

    # Insert after the initial H1 section (H1 + following blank lines)
    insert_at = h1_idx + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1

    new_lines = lines[:insert_at] + ["", block.rstrip(), ""] + lines[insert_at:]
    return "\n".join(new_lines).rstrip() + "\n"


def process_file(path: Path) -> bool:
    if should_skip(path):
        return False

    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return False

    if has_h2(text, H2_OVERVIEW):
        return False

    new = insert_after_h1(text, OVERVIEW_BLOCK)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    scanned = 0

    for p in TOP_LEVEL_FILES:
        if p.exists():
            scanned += 1
            if process_file(p):
                changed += 1

    for d in TARGET_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            scanned += 1
            if process_file(p):
                changed += 1

    print(f"ensure_pretty_sections: scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()

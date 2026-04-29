#!/usr/bin/env python3
"""Build verification queue from unresolved placeholders in pages/*.md."""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
OUT = PAGES / "verification-queue.md"

EXCLUDE = {
    "quality-report.md",
    "daily-report.md",
    "content-gaps.md",
    "link-health.md",
    "verification-queue.md",
    "system_status.md",
}
EXCLUDE_DIRS = {
    "checklists",
    "recommendations",
    "templates",
}

PATTERNS = [
    re.compile(r"검증\s*불가"),
    re.compile(r"\(?확인\s*필요\)?"),
    re.compile(r"추가\s*필요"),
    re.compile(r"미확정"),
]


def iter_pages() -> list[Path]:
    out: list[Path] = []
    for p in PAGES.rglob("*.md"):
        if p.name in EXCLUDE:
            continue
        rel_parts = p.relative_to(PAGES).parts
        if rel_parts and rel_parts[0] in EXCLUDE_DIRS:
            continue
        out.append(p)
    return sorted(out)


def detect(line: str) -> bool:
    stripped = line.strip()
    if " | " in stripped and ("공식확정" in stripped or "보도(1차)" in stripped):
        return False
    if stripped.startswith(">") and "상태:" in stripped:
        return False
    if "애매한 건" in stripped:
        return False
    return any(pt.search(line) for pt in PATTERNS)


def main() -> int:
    items: list[str] = []
    for path in iter_pages():
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        rel = path.relative_to(BASE)
        for idx, line in enumerate(lines, start=1):
            if detect(line):
                items.append(f"- [{rel}:{idx}] {line.strip()[:180]}")

    header = [
        "# Verification Queue (auto)",
        "",
        "> 목적: 공식 근거 확인이 필요한 항목을 우선순위로 처리하기 위한 큐",
        "",
        f"- total_items: {len(items)}",
        "",
        "## Items",
    ]

    body = items if items else ["- (없음)"]
    OUT.write_text("\n".join(header + body).rstrip() + "\n", encoding="utf-8")
    print(f"rebuild_verification_queue: {len(items)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Ensure required sections exist in content pages.

Adds the following headings if missing:
- "## 공식 링크"
- "## 출처"

Insertion strategy:
- If file contains "<!-- AUTO-CANDIDATES:START -->", insert blocks immediately before it.
- Else, append at end.

This is a *structure* normalizer: it does not invent facts.
"""

from __future__ import annotations

from pathlib import Path

REQUIRED_BLOCK = (
    "## 공식 링크\n"
    "- (추가 필요)\n\n"
    "## 출처\n"
    "- (추가 필요: 공식/1차 링크)\n\n"
)

CONTENT_DIRS = [
    "pages/brands",
    "pages/magazines",
    "pages/pictorials",
    "pages/endorsements",
    "pages/works",
    "pages/videos",
    "pages/interviews",
]


def has_heading(txt: str, heading: str) -> bool:
    return f"\n## {heading}\n" in txt or txt.startswith(f"## {heading}\n")


def should_skip(path: Path) -> bool:
    # Skip templates and auto-generated reports.
    p = str(path)
    if "/templates/" in p:
        return True
    if path.name in {"link-health.md", "lint-report.md", "quality-report.md", "daily-report.md", "content-gaps.md"}:
        return True
    return False


def main() -> None:
    changed = 0
    scanned = 0

    for d in CONTENT_DIRS:
        base = Path(d)
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.md")):
            if should_skip(p):
                continue
            scanned += 1
            txt = p.read_text(encoding="utf-8", errors="ignore")

            need_official = not has_heading(txt, "공식 링크")
            need_sources = not has_heading(txt, "출처")
            if not (need_official or need_sources):
                continue

            block = ""
            if need_official:
                block += "## 공식 링크\n- (추가 필요)\n\n"
            if need_sources:
                block += "## 출처\n- (추가 필요: 공식/1차 링크)\n\n"

            marker = "<!-- AUTO-CANDIDATES:START -->"
            if marker in txt:
                txt = txt.replace(marker, block + marker, 1)
            else:
                if not txt.endswith("\n"):
                    txt += "\n"
                txt = txt + "\n" + block

            p.write_text(txt, encoding="utf-8")
            changed += 1

    print(f"ensure_required_sections: scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()

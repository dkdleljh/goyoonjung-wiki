#!/usr/bin/env python3
"""Insert/refresh a simple Table of Contents in selected markdown files.

- Uses explicit markers to avoid touching auto-generated blocks.
- Does not change content, only adds/updates a TOC section.

Markers:
  <!-- TOC:START -->
  <!-- TOC:END -->

We generate links for headings (##..######) excluding headings inside code fences.
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

TOC_START = "<!-- TOC:START -->"
TOC_END = "<!-- TOC:END -->"

HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
CODE_FENCE_RE = re.compile(r"^```")


def slugify(title: str) -> str:
    # GitHub-style basic slug for Korean/ASCII mixed.
    # Keep it simple: lower, strip, replace spaces with -, drop non-word except Korean.
    s = title.strip().lower()
    s = re.sub(r"[`*_]", "", s)
    s = re.sub(r"\s+", "-", s)
    # Remove chars that are not alnum, hyphen, or Korean
    s = re.sub(r"[^0-9a-z\-가-힣]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def extract_headings(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    in_code = False
    out: list[tuple[int, str]] = []
    for ln in lines:
        if CODE_FENCE_RE.match(ln.strip()):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING_RE.match(ln)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if title.startswith("(자동"):
            continue
        out.append((level, title))
    return out


def build_toc(headings: list[tuple[int, str]]) -> str:
    if not headings:
        return "- (목차 없음)"

    min_level = min(l for l, _ in headings)
    lines: list[str] = []
    for level, title in headings:
        indent = "  " * (level - min_level)
        slug = slugify(title)
        lines.append(f"{indent}- [{title}](#{slug})")
    return "\n".join(lines)


def upsert_toc(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    headings = extract_headings(text)
    toc = build_toc(headings)

    block = f"{TOC_START}\n\n## 목차\n\n{toc}\n\n{TOC_END}"

    if TOC_START in text and TOC_END in text:
        new = re.sub(
            re.escape(TOC_START) + r"[\s\S]*?" + re.escape(TOC_END),
            block,
            text,
            flags=re.M,
        )
    else:
        # insert after first H1 block (after first heading + optional following lines)
        parts = text.splitlines()
        insert_at = 0
        for i, ln in enumerate(parts):
            if ln.startswith("# "):
                insert_at = i + 1
                break
        # skip following blank lines
        while insert_at < len(parts) and parts[insert_at].strip() == "":
            insert_at += 1
        new_lines = parts[:insert_at] + ["", block, ""] + parts[insert_at:]
        new = "\n".join(new_lines)

    if new != text:
        path.write_text(new.rstrip() + "\n", encoding="utf-8")
        return True
    return False


def main() -> None:
    targets = [
        BASE / "README.md",
        BASE / "index.md",
        BASE / "index.en.md",
        BASE / "docs" / "README.md",
        BASE / "docs" / "OPERATION_GUIDE.md",
        BASE / "pages" / "hub.md",
        BASE / "pages" / "hub.en.md",
    ]

    changed = 0
    for p in targets:
        if not p.exists():
            continue
        if upsert_toc(p):
            changed += 1

    print(f"insert_toc: changed={changed}/{len(targets)}")


if __name__ == "__main__":
    main()

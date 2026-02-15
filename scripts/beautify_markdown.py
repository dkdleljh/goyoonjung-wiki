#!/usr/bin/env python3
"""Beautify markdown files (safe formatter).

Scope
- Applies whitespace/structure formatting only.
- Does NOT change factual content.

Rules
- Normalize newlines to \n
- Strip trailing whitespace
- Ensure exactly one blank line:
  - after headings (unless immediately followed by list or blockquote)
  - before headings (unless at start)
- Collapse 3+ consecutive blank lines to 2
- Ensure file ends with a single trailing newline

Excludes
- news/*.md (automation logs)
- backups/, .git/, .venv/, data/ DBs

"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {".git", ".venv", "backups", "data", ".cache", ".pytest_cache", ".ruff_cache"}

HEADING_RE = re.compile(r"^(#{1,6})\s+.+")
CODE_FENCE_RE = re.compile(r"^```")


def iter_md_files() -> list[Path]:
    out: list[Path] = []
    for p in BASE.rglob("*.md"):
        rel = p.relative_to(BASE)
        if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
            continue
        if rel.parts and rel.parts[0] == "news":
            continue
        out.append(p)
    return sorted(out)


def beautify(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]

    out: list[str] = []
    in_code = False

    def last_nonempty_idx() -> int | None:
        for i in range(len(out) - 1, -1, -1):
            if out[i].strip() != "":
                return i
        return None

    for _i, ln in enumerate(lines):
        if CODE_FENCE_RE.match(ln.strip()):
            in_code = not in_code
            out.append(ln)
            continue

        if in_code:
            out.append(ln)
            continue

        is_heading = bool(HEADING_RE.match(ln))

        if is_heading:
            # ensure one blank line before heading (unless beginning)
            if out:
                j = last_nonempty_idx()
                if j is not None and j != len(out) - 1:
                    # already has blank lines
                    pass
                elif j is not None:
                    out.append("")
            out.append(ln)
            continue

        out.append(ln)

    # Post-process: collapse excessive blank lines
    collapsed: list[str] = []
    blank_run = 0
    for ln in out:
        if ln.strip() == "":
            blank_run += 1
            if blank_run <= 2:
                collapsed.append("")
            continue
        blank_run = 0
        collapsed.append(ln)

    # Ensure blank line after headings when next line is plain text
    final: list[str] = []
    for idx, ln in enumerate(collapsed):
        final.append(ln)
        if HEADING_RE.match(ln):
            nxt = collapsed[idx + 1] if idx + 1 < len(collapsed) else ""
            if nxt.strip() == "":
                continue
            if nxt.lstrip().startswith(("- ", ">", "* ", "+ ", "1.", "```")):
                continue
            final.append("")

    s = "\n".join(final).rstrip() + "\n"
    return s


def main() -> None:
    changed = 0
    scanned = 0
    for p in iter_md_files():
        scanned += 1
        try:
            orig = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new = beautify(orig)
        if new != orig.replace("\r\n", "\n").replace("\r", "\n"):
            p.write_text(new, encoding="utf-8")
            changed += 1

    print(f"beautify_markdown: scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()

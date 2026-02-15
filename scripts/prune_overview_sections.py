#!/usr/bin/env python3
"""Prune "## 한눈에 보기" sections from non-core markdown pages.

Rationale
- "한눈에 보기" is valuable on core, user-facing pages (hub/index/profile/etc).
- On auto-generated indexes/reports and deep leaf pages, it adds noise unless fully curated.

Behavior
- Removes the first H2 section titled exactly "## 한눈에 보기" from files NOT in keep allowlist.
- Safe best-effort: does not touch code fences.

Allowlist (keep): key entry pages and a few core docs.
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

KEEP = {
    "README.md",
    "index.md",
    "index.en.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "pages/hub.md",
    "pages/hub.en.md",
    "pages/profile.md",
    "pages/filmography.md",
    "pages/awards.md",
    "pages/timeline.md",
    "pages/works-characters.md",
    "pages/pictorials.md",
    "pages/endorsements.md",
    "pages/interviews.md",
    "pages/appearances.md",
    "pages/sns.md",
    "pages/schedule.md",
    "docs/OPERATION_GUIDE.md",
    "docs/README.md",
}

SKIP_DIRS = {".git", ".venv", "backups", "data", ".cache", ".pytest_cache", ".ruff_cache"}

H2_OVERVIEW_RE = re.compile(r"^##\s+한눈에\s+보기\s*$")
H2_ANY_RE = re.compile(r"^##\s+")
CODE_FENCE_RE = re.compile(r"^```")


def iter_md_files() -> list[Path]:
    out: list[Path] = []
    for p in BASE.rglob("*.md"):
        rel = p.relative_to(BASE)
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            continue
        if rel.parts and rel.parts[0] == "news":
            continue
        out.append(p)
    return sorted(out)


def should_keep(path: Path) -> bool:
    rel = path.relative_to(BASE).as_posix()
    return rel in KEEP


def prune(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []

    in_code = False
    i = 0
    removed = False

    while i < len(lines):
        ln = lines[i]
        if CODE_FENCE_RE.match(ln.strip()):
            in_code = not in_code
            out.append(ln)
            i += 1
            continue
        if in_code:
            out.append(ln)
            i += 1
            continue

        if not removed and H2_OVERVIEW_RE.match(ln.strip()):
            # skip this H2 block until next H2 (or EOF)
            removed = True
            i += 1
            while i < len(lines):
                if CODE_FENCE_RE.match(lines[i].strip()):
                    # If overview contains code fence, stop pruning to avoid breaking structure
                    # (unlikely in our placeholder block)
                    break
                if H2_ANY_RE.match(lines[i].strip()):
                    break
                i += 1
            # do not copy skipped lines; keep a single blank line separation
            if out and out[-1].strip() != "":
                out.append("")
            continue

        out.append(ln)
        i += 1

    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    scanned = 0
    changed = 0

    for p in iter_md_files():
        scanned += 1
        if should_keep(p):
            continue
        orig = p.read_text(encoding="utf-8", errors="ignore")
        if "## 한눈에 보기" not in orig:
            continue
        new = prune(orig)
        if new != orig:
            p.write_text(new, encoding="utf-8")
            changed += 1

    print(f"prune_overview_sections: scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()

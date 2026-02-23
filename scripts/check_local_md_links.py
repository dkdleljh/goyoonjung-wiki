#!/usr/bin/env python3
"""Check local (relative) markdown links for existence.

- Scans all .md files in repo.
- Extracts markdown links: [text](target)
- Ignores http(s), mailto, fragments-only, and image links.
- Resolves relative paths against the current file's directory.
- Reports missing targets (file not found).

Outputs: pages/recommendations/local-link-issues.md

This does not validate external URLs; use scripts/check_links.py for that.
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "pages" / "recommendations" / "local-link-issues.md"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def is_external(t: str) -> bool:
    return t.startswith("http://") or t.startswith("https://") or t.startswith("mailto:")


def normalize_target(t: str) -> str:
    t = t.strip()
    # remove surrounding <>
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1]
    # strip fragment
    if "#" in t:
        t = t.split("#", 1)[0]
    # strip query
    if "?" in t:
        t = t.split("?", 1)[0]
    return t.strip()


def main() -> int:
    missing: list[tuple[str, int, str]] = []

    for p in sorted(BASE.rglob("*.md")):
        # skip venv/cache
        if any(part in {".git", ".venv", ".pytest_cache", ".ruff_cache", "node_modules"} for part in p.parts):
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for i, ln in enumerate(lines, 1):
            for raw in LINK_RE.findall(ln):
                t = normalize_target(raw)
                if not t:
                    continue
                if is_external(t):
                    continue
                if t.startswith("#"):
                    continue
                # Only consider plausible file links (avoid false positives like (link) or regex docs).
                if not (
                    t.startswith("./")
                    or t.startswith("../")
                    or "/" in t
                    or t.endswith(".md")
                ):
                    continue
                # ignore images and assets
                if any(t.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]):
                    continue
                target = (p.parent / t).resolve()
                # keep within repo
                try:
                    target.relative_to(BASE)
                except Exception:
                    continue
                if not target.exists():
                    missing.append((str(p.relative_to(BASE)), i, t))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_lines = [
        "# 로컬 링크 점검(상대경로)\n",
        "> 목적: index/hub/README 등에서 내부 링크가 깨지지 않게 확인합니다.\n",
        "\n## 결과\n",
    ]

    if not missing:
        out_lines.append("- (문제 없음)\n")
    else:
        out_lines.append(f"- 누락 링크: **{len(missing)}**\n")
        out_lines.append("\n## 누락 목록\n")
        for f, ln, t in missing[:400]:
            out_lines.append(f"- `{f}:{ln}` → `{t}`")
        out_lines.append("")

    OUT.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    print(f"check_local_md_links: missing={len(missing)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

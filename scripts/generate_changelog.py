#!/usr/bin/env python3
"""Generate CHANGELOG.md from git tags + commit subjects.

Policy:
- Canonical release tags are SemVer annotated tags: vMAJOR.MINOR.PATCH
- We only consider MAJOR >= 1 and < 1000 (to ignore legacy date-style tags)
- For each release tag, we list commit subjects since previous canonical tag.

This script overwrites CHANGELOG.md deterministically.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime

BASE = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()

SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def sh(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, cwd=BASE, text=True).strip()


def lines(cmd: list[str]) -> list[str]:
    out = subprocess.check_output(cmd, cwd=BASE, text=True)
    return [ln.rstrip("\n") for ln in out.splitlines()]


@dataclass(frozen=True)
class Tag:
    name: str
    major: int
    minor: int
    patch: int


def canonical_tags() -> list[Tag]:
    tags = []
    for t in lines(["git", "tag", "-l", "v*.*.*"]):
        m = SEMVER_RE.match(t.strip())
        if not m:
            continue
        major, minor, patch = map(int, m.groups())
        if major < 1 or major >= 1000:
            continue
        tags.append(Tag(t, major, minor, patch))

    # sort ascending by version
    tags.sort(key=lambda x: (x.major, x.minor, x.patch))
    return tags


def tag_date(tag: str) -> str:
    # ISO-like date for display
    try:
        return sh(["git", "log", "-1", "--format=%ad", "--date=short", tag])
    except Exception:
        return ""


def commits_between(a: str | None, b: str) -> list[str]:
    rev = f"{a}..{b}" if a else b
    # subjects only (keep deterministic & compact)
    out = lines(["git", "log", "--format=%s", rev])
    # reverse chronological -> make it chronological within release for readability
    return list(reversed([s for s in out if s.strip()]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--next-tag",
        default="",
        help="If set, render a 'next release' section with this tag name using commits up to HEAD.",
    )
    args = ap.parse_args(argv)

    tags = canonical_tags()

    header = [
        "# CHANGELOG",
        "",
        "## Release process",
        "- 정식 릴리즈는 SemVer 태그(`vMAJOR.MINOR.PATCH`)로 관리합니다.",
        "- 규칙/자동화 상세: [`docs/RELEASING.md`](docs/RELEASING.md)",
        "",
    ]

    if not tags:
        content = header + ["(no canonical semver tags found)", ""]
        open(f"{BASE}/CHANGELOG.md", "w", encoding="utf-8").write("\n".join(content))
        return 0

    # Render newest releases first (descending).
    blocks: list[str] = []
    for i in range(len(tags) - 1, -1, -1):
        cur = tags[i]
        prev = tags[i - 1].name if i - 1 >= 0 else None
        d = tag_date(cur.name)
        blocks.append(f"## {cur.name}" + (f" ({d})" if d else ""))
        msgs = commits_between(prev, cur.name)
        if not msgs:
            blocks.append("- (no changes)")
        else:
            for m in msgs:
                blocks.append(f"- {m}")
        blocks.append("")

    # Optional: next release section (commits since latest canonical tag up to HEAD)
    if args.next_tag:
        latest = tags[-1].name if tags else None
        d = datetime.now().strftime("%Y-%m-%d")
        blocks.insert(0, "")
        blocks.insert(0, f"## {args.next_tag} ({d})")
        msgs = commits_between(latest, "HEAD") if latest else commits_between(None, "HEAD")
        if not msgs:
            blocks.insert(1, "- (no changes)")
        else:
            for i, m in enumerate(msgs, start=1):
                blocks.insert(i, f"- {m}")

    # Unreleased section (HEAD since latest tag) — only when not rendering next-tag
    if not args.next_tag and tags:
        latest = tags[-1].name
        unreleased = commits_between(latest, "HEAD")
        if unreleased:
            blocks.insert(0, "## Unreleased")
            for m in unreleased:
                blocks.insert(1, f"- {m}")
            blocks.insert(len(unreleased) + 2, "")

    open(f"{BASE}/CHANGELOG.md", "w", encoding="utf-8").write("\n".join(header + blocks).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

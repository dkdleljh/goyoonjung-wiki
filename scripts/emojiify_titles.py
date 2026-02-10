#!/usr/bin/env python3
"""Add emoji decorations to Markdown titles (H1) for a more friendly wiki vibe.

Target:
- pages/**/*.md
- sources/*.md

Non-target:
- news/** (logs)
- root index/README/CHANGELOG (already curated)

Rule:
- If the first non-empty line is an H1 (`# ...`) and it does not already start with an emoji,
  prefix an emoji selected by path/title heuristics.

Safe:
- Only edits the H1 line.
- Deterministic, idempotent.
"""

from __future__ import annotations

import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

EMOJI_BY_PREFIX = [
    ("pages/works/", "🎬"),
    ("pages/pictorials/", "📸"),
    ("pages/endorsements/", "🤝"),
    ("pages/", "🧾"),
    ("sources/", "🔎"),
]

# More specific by filename
EMOJI_BY_BASENAME = {
    "hub.md": "🧭",
    "profile.md": "👤",
    "filmography.md": "🎬",
    "timeline.md": "🗓️",
    "awards.md": "🏆",
    "interviews.md": "📰",
    "appearances.md": "🎤",
    "pictorials.md": "📸",
    "endorsements.md": "🤝",
    "sns.md": "📱",
    "schedule.md": "🗓️",
    "strategy.md": "🧩",
    "legal.md": "⚖️",
    "style-guide.md": "✍️",
    "naming.md": "🔤",
    "index-by-tag.md": "🏷️",
    "quality-report.md": "🧪",
    "daily-report.md": "📝",
    "progress.md": "📈",
}

# crude emoji detection: starts with common emoji ranges
EMOJI_START_RE = re.compile(
    r"^[\U0001F300-\U0001FAFF\u2600-\u27BF]"  # emoji + misc symbols
)


def iter_targets() -> list[str]:
    out: list[str] = []
    for root, _, files in os.walk(os.path.join(BASE, "pages")):
        for fn in files:
            if fn.endswith(".md"):
                out.append(os.path.join(root, fn))
    for root, _, files in os.walk(os.path.join(BASE, "sources")):
        for fn in files:
            if fn.endswith(".md"):
                out.append(os.path.join(root, fn))
    return out


def pick_emoji(rel: str) -> str:
    base = os.path.basename(rel)
    if base in EMOJI_BY_BASENAME:
        return EMOJI_BY_BASENAME[base]
    for pref, emo in EMOJI_BY_PREFIX:
        if rel.startswith(pref):
            return emo
    return "🧾"


def main() -> int:
    changed = 0
    for path in iter_targets():
        rel = os.path.relpath(path, BASE).replace(os.sep, "/")
        # skip news-like files even if symlinked (extra safety)
        if rel.startswith("news/"):
            continue

        lines = open(path, "r", encoding="utf-8").read().splitlines(True)
        # find first non-empty
        idx = None
        for i, ln in enumerate(lines):
            if ln.strip() == "":
                continue
            idx = i
            break
        if idx is None:
            continue
        ln = lines[idx]
        if not ln.startswith("# "):
            continue

        title = ln[2:].strip()
        if not title:
            continue

        # already emoji?
        if EMOJI_START_RE.match(title):
            continue

        emo = pick_emoji(rel)
        lines[idx] = f"# {emo} {title}\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        changed += 1

    print(f"emojiify_titles: changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

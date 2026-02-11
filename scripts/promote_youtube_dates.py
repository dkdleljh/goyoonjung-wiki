#!/usr/bin/env python3
"""Promote missing dates from YouTube metadata.

Purpose:
- Auto-fill placeholders like '(확인 필요)' when the primary link is a YouTube video.
- Uses yt-dlp to fetch upload_date (YYYYMMDD), which is a stable first-party-ish signal for video publish date.

Scope (safe):
- Only replaces if:
  - a YouTube URL is present in the same entry/block
  - the date field is exactly '(확인 필요)'
- Does NOT change statuses.

Targets:
- pages/pictorials/*.md : '- 날짜: (확인 필요)'
- pages/endorsements/*.md : '발표일/시작일: (확인 필요)'

No external Python deps.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

YOUTUBE_RE = re.compile(r"https?://(?:www\.)?(?:youtu\.be/|youtube\.com/watch\?v=)[^\s)]+")


@dataclass
class ReplacePlan:
    path: Path
    old: str
    new: str


def yt_upload_date(url: str) -> str | None:
    """Return YYYY-MM-DD from yt-dlp upload_date, or None."""
    try:
        out = subprocess.check_output(
            [
                "yt-dlp",
                "--no-warnings",
                "--quiet",
                "--skip-download",
                "--print",
                "upload_date",
                url,
            ],
            stderr=subprocess.DEVNULL,
            timeout=20,
            text=True,
        ).strip()
    except Exception:
        return None

    if not re.fullmatch(r"\d{8}", out):
        return None
    return f"{out[0:4]}-{out[4:6]}-{out[6:8]}"


def file_targets() -> list[Path]:
    paths: list[Path] = []
    paths += sorted((BASE / "pages" / "pictorials").glob("*.md"))
    paths += sorted((BASE / "pages" / "endorsements").glob("*.md"))
    return [p for p in paths if p.exists()]


def promote_in_text(text: str) -> tuple[str, int]:
    changed = 0

    # Strategy:
    # - For pictorial blocks: find "- 날짜: (확인 필요)" and a YouTube URL nearby (within the next ~12 lines)
    # - For endorsements: find "발표일/시작일: (확인 필요)" and a YouTube URL nearby

    lines = text.splitlines(True)

    def find_youtube_near(i: int, window: int = 14) -> str | None:
        chunk = "".join(lines[i : min(len(lines), i + window)])
        m = YOUTUBE_RE.search(chunk)
        return m.group(0) if m else None

    for i, ln in enumerate(lines):
        if ln.strip() == "- 날짜: (확인 필요)":
            url = find_youtube_near(i)
            if not url:
                continue
            d = yt_upload_date(url)
            if not d:
                continue
            lines[i] = ln.replace("(확인 필요)", d)
            changed += 1

        if "발표일/시작일:" in ln and "(확인 필요)" in ln:
            url = find_youtube_near(i)
            if not url:
                continue
            d = yt_upload_date(url)
            if not d:
                continue
            lines[i] = re.sub(r"\(확인 필요\)", d, ln)
            changed += 1

    return "".join(lines), changed


def main() -> int:
    total = 0
    for path in file_targets():
        text = path.read_text(encoding="utf-8")
        new_text, ch = promote_in_text(text)
        if ch:
            path.write_text(new_text, encoding="utf-8")
            total += ch

    print(f"promote_youtube_dates: changed={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

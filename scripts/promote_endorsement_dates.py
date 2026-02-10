#!/usr/bin/env python3
"""Promote endorsement announcement/start dates when objectively extractable.

Scope (safe):
- If an endorsement block has '발표일/시작일: (확인 필요)' (or empty), and has a YouTube link,
  fetch the YouTube watch page HTML and extract datePublished (YYYY-MM-DD).
- Write the date back into the same block.

Non-goals:
- No guessing from secondary sources.
- No Instagram date extraction.
- No image downloads.

This is best-effort and will skip on any parsing failure.
"""

from __future__ import annotations

import os
import re
import sys
import time
from urllib.parse import urlparse, parse_qs

import requests

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}
TIMEOUT = 25

FILES = [
    "pages/endorsements/beauty.md",
    "pages/endorsements/fashion.md",
    "pages/endorsements/lifestyle.md",
]

YOUTUBE_URL_RE = re.compile(r"https?://(?:www\.)?(?:youtu\.be/|youtube\.com/watch\?v=)([A-Za-z0-9_-]{6,})")
DATE_PUBLISHED_RE = re.compile(r"\"datePublished\"\s*:\s*\"(20\d{2}-\d{2}-\d{2})\"")
DATE_TEXT_RE = re.compile(r"\"dateText\"\s*:\s*\{\s*\"simpleText\"\s*:\s*\"(20\d{2})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?\"", re.S)


def read_lines(rel: str) -> list[str]:
    with open(os.path.join(BASE, rel), "r", encoding="utf-8") as f:
        return f.read().splitlines(True)


def write_lines(rel: str, lines: list[str]) -> None:
    with open(os.path.join(BASE, rel), "w", encoding="utf-8") as f:
        f.write("".join(lines))


def to_watch_url(url: str) -> str:
    if "youtu.be/" in url:
        vid = url.rstrip("/").split("/")[-1]
        return f"https://www.youtube.com/watch?v={vid}"
    return url


def fetch_date_published(youtube_url: str) -> str | None:
    """Try multiple safe methods to obtain an objective upload/publish date."""
    url = to_watch_url(youtube_url)

    # Method 1) Parse HTML (fast, no extra deps)
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        html = r.text
    except Exception:
        html = ""

    if html:
        m = DATE_PUBLISHED_RE.search(html)
        if m:
            return m.group(1)
        m2 = DATE_TEXT_RE.search(html)
        if m2:
            y, mo, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
            return f"{y:04d}-{mo:02d}-{d:02d}"

    # Method 2) yt-dlp (more robust; still objective)
    # upload_date is typically YYYYMMDD
    try:
        import subprocess

        out = subprocess.check_output(
            ["yt-dlp", "--no-warnings", "--skip-download", "--print", "%(upload_date)s", url],
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).decode("utf-8", "ignore").strip()
        if re.fullmatch(r"20\d{2}[01]\d[0-3]\d", out):
            return f"{out[0:4]}-{out[4:6]}-{out[6:8]}"
    except Exception:
        pass

    return None


def block_range(lines: list[str], start: int) -> tuple[int, int]:
    # endorsement blocks start with '- 브랜드/회사명:' and continue until next same or section header
    i = start
    j = i + 1
    while j < len(lines) and not lines[j].strip().startswith("- 브랜드/회사명:") and not lines[j].startswith("## "):
        j += 1
    return i, j


def process_file(rel: str) -> int:
    lines = read_lines(rel)
    changed = 0
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("- 브랜드/회사명:"):
            s, e = block_range(lines, i)
            block = "".join(lines[s:e])

            # only if date is missing/unknown
            if re.search(r"발표일/시작일:\s*\(확인 필요\)", block) or re.search(r"발표일/시작일:\s*$", block):
                ym = YOUTUBE_URL_RE.search(block)
                if ym:
                    yt_url = ym.group(0)
                    date = fetch_date_published(yt_url)
                    if date:
                        # replace only the first occurrence in the block
                        for k in range(s, e):
                            if "발표일/시작일:" in lines[k]:
                                indent = re.match(r"^\s*", lines[k]).group(0)
                                lines[k] = f"{indent}- 발표일/시작일: {date} (YouTube datePublished)\n"
                                changed += 1
                                break
                    time.sleep(0.4)

            i = e
        else:
            i += 1

    if changed:
        write_lines(rel, lines)
    return changed


def main() -> int:
    total = 0
    for rel in FILES:
        if os.path.exists(os.path.join(BASE, rel)):
            total += process_file(rel)
    print(f"promote_endorsement_dates: updated={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

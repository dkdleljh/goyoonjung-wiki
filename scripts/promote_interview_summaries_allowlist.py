#!/usr/bin/env python3
"""Auto-fill summaries for a small allowlist of interview/article sites.

Targets pages/interviews.md blocks that contain:
- '(요약 보강 필요)'
- and a URL matching allowlist domains

Produces 2~3 bullet summary lines (short, non-verbatim-ish), similar to KBS logic.

Allowlist (initial):
- www.marieclairekorea.com
- www.vogue.co.kr
- www.elle.co.kr

Limits:
- Max updated blocks per run: 2
- Strict timeouts
"""

from __future__ import annotations

import os
import re
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILE = os.path.join(BASE, "pages", "interviews.md")

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
TIMEOUT = 12

ALLOW = {
    "www.marieclairekorea.com",
    "www.vogue.co.kr",
    "www.elle.co.kr",
}

URL_RE = re.compile(r"https?://[^\s)]+")


def fetch(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    # pick the longest among common article containers
    candidates = []
    for sel in ["article", ".article", ".post", ".entry", ".content", ".article-body", ".view"]:
        node = soup.select_one(sel)
        if node:
            txt = node.get_text(" ", strip=True)
            if len(txt) > 400:
                candidates.append(txt)
    if candidates:
        candidates.sort(key=len, reverse=True)
        return candidates[0]
    return soup.get_text(" ", strip=True)


def split_sentences(text: str, limit: int = 3) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[\.!?。])\s+|(?<=다\.)\s+|(?<=요\.)\s+", text)
    out = []
    seen = set()
    for p in parts:
        p = p.strip()
        if len(p) < 25:
            continue
        if len(p) > 170:
            p = p[:167] + "…"
        if any(bad in p for bad in ["개인정보", "쿠키", "로그인", "구독", "무단전재", "재배포", "광고"]):
            continue
        key = re.sub(r"\s+", "", p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
        if len(out) >= limit:
            break
    return out


def replace_summary(lines: list[str], start: int, end: int, bullets: list[str]) -> bool:
    for i in range(start, end):
        if lines[i].strip() == "- 요약(3~5줄):":
            j = i + 1
            while j < end and lines[j].lstrip().startswith("  -"):
                j += 1
            lines[i + 1 : j] = ["  - " + b + "\n" for b in bullets]
            return True
    return False


def main() -> int:
    if not os.path.exists(FILE):
        return 0
    lines = open(FILE, "r", encoding="utf-8").read().splitlines(True)

    updated = 0
    i = 0
    while i < len(lines) and updated < 2:
        if lines[i].lstrip().startswith("- 날짜:"):
            start = i
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("- 날짜:") and not lines[j].startswith("## "):
                j += 1
            end = j
            block = "".join(lines[start:end])
            if "요약 보강 필요" not in block:
                i = end
                continue
            m = URL_RE.search(block)
            if not m:
                i = end
                continue
            url = m.group(0)
            d = urlparse(url).netloc
            if d not in ALLOW:
                i = end
                continue
            try:
                html = fetch(url)
                text = extract_text(html)
                bullets = split_sentences(text, limit=3)
            except Exception:
                bullets = []
            if bullets and replace_summary(lines, start, end, bullets):
                updated += 1
            time.sleep(0.35)
            i = end
        else:
            i += 1

    if updated:
        with open(FILE, "w", encoding="utf-8") as f:
            f.write("".join(lines))

    print(f"promote_interview_summaries_allowlist: updated_blocks={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

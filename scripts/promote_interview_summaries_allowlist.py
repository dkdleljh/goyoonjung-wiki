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

ALL_DOMAINS = [
    "www.marieclairekorea.com",
    "www.vogue.co.kr",
    "www.elle.co.kr",
    "www.gqkorea.co.kr",
    "www.wkorea.com",
    "www.harpersbazaar.co.kr",
    "www.esquirekorea.co.kr",
    "www.cosmopolitan.co.kr",
]

KNOWN_GOOD_PATH = os.path.join(BASE, ".locks", "interview-allow-known-good.json")

def load_known_good() -> set[str]:
    try:
        import json
        if os.path.exists(KNOWN_GOOD_PATH):
            return set(json.loads(open(KNOWN_GOOD_PATH, "r", encoding="utf-8").read()))
    except Exception:
        pass
    return set()


def save_known_good(domains: set[str]) -> None:
    try:
        import json
        os.makedirs(os.path.dirname(KNOWN_GOOD_PATH), exist_ok=True)
        with open(KNOWN_GOOD_PATH, "w", encoding="utf-8") as f:
            f.write(json.dumps(sorted(domains), ensure_ascii=False, indent=2) + "\n")
    except Exception:
        pass


def domains_to_try() -> set[str]:
    good = load_known_good()
    # Always try known-good domains; plus 1 exploratory domain in rotation.
    # Rotation key: day-of-year from system date.
    try:
        import datetime
        doy = int(datetime.datetime.now().strftime("%j"))
    except Exception:
        doy = 0
    extra = ALL_DOMAINS[doy % len(ALL_DOMAINS)] if ALL_DOMAINS else None
    if extra:
        good.add(extra)
    return good

SELECTORS_BY_DOMAIN = {
    # magazines (best-effort)
    "www.vogue.co.kr": ["article", ".article", ".post", ".entry-content", ".content"],
    "www.elle.co.kr": ["article", ".article", ".post", ".content", ".view"],
    "www.marieclairekorea.com": ["article", ".article", ".post", ".entry", ".content"],
    "www.gqkorea.co.kr": ["article", ".article", ".post", ".content"],
    "www.wkorea.com": ["article", ".article", ".post", ".content"],
    "www.harpersbazaar.co.kr": ["article", ".article", ".post", ".content"],
    "www.esquirekorea.co.kr": ["article", ".article", ".post", ".content"],
    "www.cosmopolitan.co.kr": ["article", ".article", ".post", ".content"],
}

URL_RE = re.compile(r"https?://[^\s)]+")


def fetch(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def extract_text(html: str, dom: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()

    sels = SELECTORS_BY_DOMAIN.get(dom) or ["article", ".article", ".post", ".entry", ".content", ".article-body", ".view"]

    # pick the longest among candidate containers
    candidates = []
    for sel in sels:
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
    good = load_known_good()
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
            allow = domains_to_try()
            if d not in allow:
                i = end
                continue
            try:
                html = fetch(url)
                text = extract_text(html, d)
                bullets = split_sentences(text, limit=3)
            except Exception:
                bullets = []
            if bullets and replace_summary(lines, start, end, bullets):
                updated += 1
                good.add(d)
                save_known_good(good)
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

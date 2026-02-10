#!/usr/bin/env python3
"""Auto-fill awards '근거(공식)' when a candidate official page can be verified.

Approach (conservative, best-effort):
- For each awards row with empty proof:
  1) Build a web query (DuckDuckGo HTML) like: "<시상식> <연도> 고윤정".
  2) Collect result URLs and keep only those on the expected official domain.
  3) Fetch each candidate page and verify it contains:
     - the year (e.g., 2024)
     - the name "고윤정"
     - and at least one of: award name token or category token (weak)
  4) If verified, write the URL into the proof column.

Limits:
- Max rows to fill per run: 3 (to avoid too many web calls)
- Max candidates per row: 5

Safety:
- Never uses non-official domains for proof.
- Skips when uncertain.
- No new awards are added; only fills proof URLs.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AWARDS_PATH = os.path.join(BASE, "pages", "awards.md")

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
TIMEOUT = 25

# Official domains allowlist
OFFICIAL_DOMAINS = {
    "백상예술대상": "www.baeksangawards.co.kr",
    "청룡시리즈어워즈": "bsa.blueaward.co.kr",
    "청룡영화상": "www.blueaward.co.kr",
    "대종상": "daejong.or.kr",
    "부일영화상": "www.builfilmawards.com",
    "춘사국제영화제": "www.chunsa.kr",
    "코리아 드라마 어워즈": "koreadramaawards.com",
    "아시아콘텐츠어워즈 & 글로벌OTT어워즈": "asiacontentsawards.com",
    "아시아콘텐츠어워즈": "asiacontentsawards.com",
    "씨네21": "www.cine21.com",
    "대한민국 대중문화예술상": "www.mcst.go.kr",
}


@dataclass
class Row:
    line_no: int
    cols: list[str]


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, s: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def ddg_search(query: str) -> list[str]:
    url = "https://duckduckgo.com/html/?q=" + quote(query)
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    urls: list[str] = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if not href:
            continue
        urls.append(href)
    # de-dupe preserve order
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def domain_of(u: str) -> str:
    try:
        return urlparse(u).netloc
    except Exception:
        return ""


def fetch_text(u: str) -> str:
    r = requests.get(u, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return soup.get_text(" ", strip=True)


def verify(text: str, year: str, must_tokens: list[str]) -> bool:
    if year not in text:
        return False
    if "고윤정" not in text:
        return False
    # require at least one contextual token
    for tok in must_tokens:
        if tok and tok in text:
            return True
    return False


def parse_awards_table(md: str) -> list[Row]:
    rows: list[Row] = []
    for idx, ln in enumerate(md.splitlines(), start=1):
        if not ln.startswith("|"):
            continue
        if "연도" in ln and "시상식" in ln:
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 8:
            continue
        year = cols[0]
        if not re.fullmatch(r"20\d{2}", year):
            continue
        proof = cols[6]
        if proof:
            continue
        rows.append(Row(line_no=idx, cols=cols))
    return rows


def fill_proof_in_line(line: str, url: str) -> str:
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cols) < 8:
        return line
    cols[6] = url
    return "| " + " | ".join(cols[:8]) + " |\n"


def main() -> int:
    if not os.path.exists(AWARDS_PATH):
        return 0
    md = read_text(AWARDS_PATH)
    lines = md.splitlines(True)
    rows = parse_awards_table(md)

    filled = 0
    for row in rows:
        if filled >= 3:
            break
        year, award, category, work, result, status, proof, note = row.cols[:8]
        official_domain = OFFICIAL_DOMAINS.get(award)
        if not official_domain:
            continue

        q = f"{award} {year} 고윤정"
        try:
            results = ddg_search(q)
        except Exception:
            continue

        candidates = [u for u in results if domain_of(u) == official_domain][:5]
        if not candidates:
            continue

        must_tokens = [award, category]
        ok_url = None
        for u in candidates:
            try:
                text = fetch_text(u)
            except Exception:
                continue
            if verify(text, year, must_tokens):
                ok_url = u
                break
            time.sleep(0.2)

        if not ok_url:
            continue

        # Patch the specific line in file
        line_index = row.line_no - 1
        old = lines[line_index]
        if not old.startswith("|"):
            continue
        lines[line_index] = fill_proof_in_line(old, ok_url)
        filled += 1
        time.sleep(0.4)

    if filled:
        write_text(AWARDS_PATH, "".join(lines))

    print(f"promote_awards_official_proofs: filled={filled}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

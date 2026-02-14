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
- Max rows to fill per run: 2 (to avoid too many web calls)
- Max candidates per row: 5
- Per-run time budget: 60s (soft via internal checks)

Safety:
- Never uses non-official domains for proof.
- Skips when uncertain.
- No new awards are added; only fills proof URLs.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AWARDS_PATH = os.path.join(BASE, "pages", "awards.md")
HINTS_PATH = os.path.join(BASE, "config", "awards-url-hints.json")
CACHE_PATH = os.path.join(BASE, "config", "awards-official-cache.json")

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
TIMEOUT = 15

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
    with open(path, encoding="utf-8") as f:
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


def fetch_html(u: str) -> str:
    r = requests.get(u, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def fetch_text(u: str) -> str:
    html = fetch_html(u)
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return soup.get_text(" ", strip=True)


def extract_links_same_domain(html: str, base_url: str, domain: str, limit: int = 80) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    seen = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        u = urljoin(base_url, href)
        if domain_of(u) != domain:
            continue
        u = u.split("#")[0]
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)
        if len(urls) >= limit:
            break
    return urls


def load_hints() -> dict[str, list[str]]:
    if not os.path.exists(HINTS_PATH):
        return {}
    try:
        return json.loads(read_text(HINTS_PATH))
    except Exception:
        return {}


def load_cache() -> dict[str, list[str]]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        return json.loads(read_text(CACHE_PATH))
    except Exception:
        return {}


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
    hints = load_hints()
    cache = load_cache()

    start_ts = time.time()
    filled = 0
    for row in rows:
        if filled >= 2:
            break
        if time.time() - start_ts > 60:
            break
        year, award, category, work, result, status, proof, note = row.cols[:8]
        official_domain = OFFICIAL_DOMAINS.get(award)
        if not official_domain:
            continue

        must_tokens = [award, category]
        ok_url = None

        # Phase 0) Cached official links (fast path)
        cached = [u for u in cache.get(award, []) if domain_of(u) == official_domain]
        year_cached = [u for u in cached if year in u][:10]
        other_cached = [u for u in cached if u not in year_cached][:10]
        for u in year_cached + other_cached:
            try:
                text = fetch_text(u)
            except Exception:
                continue
            if verify(text, year, must_tokens):
                ok_url = u
                break
            time.sleep(0.12)

        # Phase 1) Hint pages crawl (more deterministic than search)
        if not ok_url:
            for seed in hints.get(award, [])[:3]:
                if domain_of(seed) != official_domain:
                    continue
                try:
                    html = fetch_html(seed)
                except Exception:
                    continue
                # collect same-domain links and try those that contain year first
                links = extract_links_same_domain(html, seed, official_domain, limit=80)
                year_links = [u for u in links if year in u][:20]
                other_links = [u for u in links if u not in year_links][:20]
                for u in year_links + other_links:
                    try:
                        text = fetch_text(u)
                    except Exception:
                        continue
                    if verify(text, year, must_tokens):
                        ok_url = u
                        break
                    time.sleep(0.15)
                if ok_url:
                    break

        # Phase 2) DuckDuckGo search fallback
        if not ok_url:
            q = f"{award} {year} 고윤정"
            try:
                results = ddg_search(q)
            except Exception:
                results = []

            candidates = [u for u in results if domain_of(u) == official_domain][:5]
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

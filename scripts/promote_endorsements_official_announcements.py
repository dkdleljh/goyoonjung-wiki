#!/usr/bin/env python3
"""Auto-fill endorsements '링크(공식 발표)' when an official page can be verified.

Conservative approach (best-effort):
- Uses brand official domains from sources/brands-watch.md.
- For each endorsements entry with '링크(공식 발표): (확인 필요)':
  - If we know an official domain, crawl a small set of same-domain pages starting from the brand homepage.
  - Verify a candidate page contains:
    - '고윤정' OR 'Go Youn-jung'
    - and one of keywords: 모델 / 뮤즈 / 앰버서더 / ambassador / muse
  - If verified, write that URL into '링크(공식 발표)'.

Limits:
- Max fills per run: 1 (to keep it safe and cheap)
- Max pages fetched per brand: 25
- Timeouts are strict; failures are skipped.

Note:
- This does NOT guarantee the page is a press release; it only ensures it is on the official domain
  and contains the relevant tokens. If too strict/too lax, adjust keywords.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BRANDS_WATCH = os.path.join(BASE, "sources", "brands-watch.md")

ENDO_FILES = [
    os.path.join(BASE, "pages", "endorsements", "beauty.md"),
    os.path.join(BASE, "pages", "endorsements", "fashion.md"),
    os.path.join(BASE, "pages", "endorsements", "lifestyle.md"),
]

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
TIMEOUT = 12

BRAND_LINE_RE = re.compile(r"^\s*-\s*([A-Za-z0-9\-\s\uAC00-\uD7A3&/().']+):\s*(https?://\S+)")

KEYWORDS = ["모델", "뮤즈", "앰버서더", "ambassador", "muse"]
NAME_TOKENS = ["고윤정", "Go Youn-jung", "GO YOUNJUNG", "GO YOUNJUNG"]


@dataclass
class EndoEntry:
    file: str
    start: int
    end: int
    brand: str


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def fetch(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def text_of(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return soup.get_text(" ", strip=True)


def extract_links(html: str, base_url: str, want_domain: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    seen = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        u = urljoin(base_url, href)
        if domain(u) != want_domain:
            continue
        u = u.split("#")[0]
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= 120:
            break
    return out


def verified(url: str, html: str) -> bool:
    t = text_of(html)
    if not any(tok in t for tok in NAME_TOKENS):
        return False
    if not any(k.lower() in t.lower() for k in KEYWORDS):
        return False
    # avoid obvious non-content pages
    if any(bad in t for bad in ["개인정보", "쿠키", "로그인", "회원가입", "장바구니", "결제"]):
        return False
    return True


def parse_brand_domains(md: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in md.splitlines():
        m = BRAND_LINE_RE.match(ln.strip())
        if not m:
            continue
        name = m.group(1).strip()
        url = m.group(2).strip().rstrip(")")
        d = domain(url)
        if not d:
            continue
        key = name.split("(", 1)[0].strip()
        if key:
            out[key] = url
        out[name] = url
    return out


def find_entries(path: str) -> list[EndoEntry]:
    lines = read(path).splitlines(True)
    out: list[EndoEntry] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("- 브랜드/회사명:"):
            brand = lines[i].split(":", 1)[1].strip()
            j = i + 1
            end = j
            while end < len(lines) and not lines[end].startswith("- 브랜드/회사명:") and not lines[end].startswith("## "):
                end += 1
            block = "".join(lines[i:end])
            if "링크(공식 발표): (확인 필요)" in block:
                out.append(EndoEntry(file=path, start=i, end=end, brand=brand))
            i = end
        else:
            i += 1
    return out


def fill_entry(path: str, entry: EndoEntry, url: str) -> bool:
    lines = read(path).splitlines(True)
    changed = False
    for k in range(entry.start, entry.end):
        if lines[k].strip() == "- 링크(공식 발표): (확인 필요)":
            lines[k] = f"  - 링크(공식 발표): {url}\n"
            changed = True
            break
    if changed:
        write_lines(path, lines)
    return changed


def main() -> int:
    brands_md = read(BRANDS_WATCH) if os.path.exists(BRANDS_WATCH) else ""
    brand_home = parse_brand_domains(brands_md)

    # gather candidate entries
    entries: list[EndoEntry] = []
    for f in ENDO_FILES:
        if os.path.exists(f):
            entries.extend(find_entries(f))

    filled = 0
    for e in entries:
        if filled >= 1:
            break
        brand_key = e.brand.split("(", 1)[0].strip()
        home = brand_home.get(e.brand) or brand_home.get(brand_key)
        if not home:
            continue
        d = domain(home)
        if not d:
            continue

        # crawl small set
        try:
            html0 = fetch(home)
        except Exception:
            continue

        links = extract_links(html0, home, d)
        # prioritize links that look like news/notice/press
        def score(u: str) -> int:
            u2 = u.lower()
            s = 0
            for kw in ["news", "notice", "press", "media", "event", "campaign", "ambassador", "muse", "model"]:
                if kw in u2:
                    s += 2
            if "go" in u2 or "youn" in u2 or "%ea%b3%a0%ec%9c%a4%ec%a0%95" in u2:
                s += 3
            return -s

        links = sorted(links, key=score)
        checked = 0
        for u in links:
            if checked >= 25:
                break
            checked += 1
            try:
                h = fetch(u)
            except Exception:
                continue
            if verified(u, h):
                if fill_entry(e.file, e, u):
                    filled += 1
                break
            time.sleep(0.15)

    print(f"promote_endorsements_official_announcements: filled={filled}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

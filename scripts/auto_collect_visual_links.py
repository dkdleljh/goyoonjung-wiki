#!/usr/bin/env python3
"""Auto-collect visual-friendly links (events/photos/stills/interviews) and land them into markdown.

Design goals:
- Link-only (no image downloading)
- Deterministic
- De-dupe via: (1) existing markdown contains URL, (2) sources/seen-urls.txt
- Prefer reliable, server-rendered sources:
  - KBS연예 스타박스(person_view) → list_view articles
  - Vogue search (?s=고윤정) → dated posts (best-effort)

This is intentionally conservative: it adds *links* with minimal metadata.
"""
# noqa: E701, E702

from __future__ import annotations

import os
import re
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
TIMEOUT = 25

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SEEN_TXT = os.path.join(BASE, "sources", "seen-urls.txt")

EVENTS_MD = os.path.join(BASE, "pages", "pictorials", "events.md")
STILLS_MD = os.path.join(BASE, "pages", "pictorials", "stills-posters.md")
INTERVIEWS_MD = os.path.join(BASE, "pages", "interviews.md")
APPEARANCES_MD = os.path.join(BASE, "pages", "appearances.md")
EDITORIAL_MD = os.path.join(BASE, "pages", "pictorials", "editorial.md")

KBS_PERSON = "https://kstar.kbs.co.kr/person_view.html?idx=220921"  # 고윤정
VOGUE_SEARCH = "https://www.vogue.co.kr/?s=%EA%B3%A0%EC%9C%A4%EC%A0%95"
ELLE_SEARCH = "https://www.elle.co.kr/?s=%EA%B3%A0%EC%9C%A4%EC%A0%95"
W_SEARCH = "https://www.wkorea.com/?s=%EA%B3%A0%EC%9C%A4%EC%A0%95"
BAZAAR_SEARCH = "https://www.harpersbazaar.co.kr/?s=%EA%B3%A0%EC%9C%A4%EC%A0%95"
GQ_SEARCH = "https://www.gqkorea.co.kr/?s=%EA%B3%A0%EC%9C%A4%EC%A0%95"


@dataclass(frozen=True)
class Entry:
    year: int
    block: str  # markdown block (must include id URL line)
    url: str


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_seen_urls() -> set[str]:
    if not os.path.exists(SEEN_TXT):
        return set()
    s = set()
    with open(SEEN_TXT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            s.add(line)
    return s


def http_get(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def extract_date_from_text(text: str) -> str | None:
    # KBS pages often include 2025.05.10 or 2025-05-10
    m = re.search(r"(20\d{2})[\.-](\d{2})[\.-](\d{2})", text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def ensure_year_section(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    # insert before the first older year section if possible, else append at end
    years = sorted({int(y) for y in re.findall(r"^## (\d{4})\s*$", md, flags=re.M)}, reverse=True)
    if not years:
        return md + f"\n\n{hdr}\n(추가 보강 필요)\n"
    # place it to keep descending order
    for y in years:
        if year > y:
            # insert before section for y
            pat = re.compile(rf"^## {y}\s*$", flags=re.M)
            m = pat.search(md)
            if m:
                insert_at = m.start()
                return md[:insert_at] + f"{hdr}\n(추가 보강 필요)\n\n" + md[insert_at:]
    # year is older than all existing, append at end
    return md + f"\n\n{hdr}\n(추가 보강 필요)\n"


def insert_entry_under_year(md: str, year: int, block: str, url: str) -> str:
    if url in md:
        return md
    md = ensure_year_section(md, year)
    hdr = f"## {year}"
    # find section range
    lines = md.splitlines(True)
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == hdr:
            start = i
            break
    if start is None:
        return md + "\n" + block.rstrip() + "\n"
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ") and lines[j].strip() != hdr:
            end = j
            break
    section = "".join(lines[start:end])
    # if section is placeholder-only, keep placeholder but append entries after it
    new_section = section.rstrip() + "\n\n" + block.rstrip() + "\n"
    new_md = "".join(lines[:start]) + new_section + "".join(lines[end:])
    return new_md


def kbs_collect() -> tuple[list[Entry], list[Entry], list[Entry]]:
    """Return (events, appearances, interviews) entries from KBS person box."""
    html = http_get(KBS_PERSON)
    idxs = sorted({int(x) for x in re.findall(r"list_view\.html\?idx=(\d+)", html)})
    events: list[Entry] = []
    appearances: list[Entry] = []
    interviews: list[Entry] = []

    for idx in idxs:
        url = f"https://kstar.kbs.co.kr/list_view.html?idx={idx}"
        try:
            page = http_get(url)
        except Exception:
            continue
        soup = BeautifulSoup(page, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = " ".join(soup.title.string.split())
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = " ".join(og["content"].split())

        text = soup.get_text("\n")
        date = extract_date_from_text(text) or "(페이지 내 표기 확인 필요)"
        year = int(date[:4]) if date and date[0].isdigit() else 0
        if year == 0:
            continue

        # heuristics
        title.lower()
        is_press = any(k in title for k in ["제작발표회", "시사회", "포토", "포토타임", "포토월"]) or "현장" in title
        is_interview = "[인터뷰]" in title or "인터뷰" in title

        # events.md (visual archive)
        if is_press:
            block = "\n".join([
                f"- 날짜: {date}",
                "- 구분: 제작발표회/시사회/포토타임(보도)",
                f"- 행사명: {title}",
                "- 주최/플랫폼: KBS연예",
                f"- 링크(공식/원문): {url}",
                "- 상태: 보도(1차)",
                f"- id: {url}",
                "- 메모: 보도(1차). 사진/스틸 포함 가능.",
            ])
            events.append(Entry(year=year, block=block, url=url))

        # appearances.md (activity log)
        block2 = "\n".join([
            f"- 날짜: {date}",
            "- 구분: 기타(보도/홍보)",
            f"- 프로그램/행사명: {title}",
            "- 플랫폼/방송사: KBS연예",
            f"- 링크(공식/원문): {url}",
            "- 상태: 보도(1차)",
            f"- id: {url}",
            "- 메모: 보도(1차). 사진/스틸 포함 가능.",
        ])
        appearances.append(Entry(year=year, block=block2, url=url))

        # interviews.md (only if interview)
        if is_interview:
            block3 = "\n".join([
                f"- 날짜: {date}",
                "- 매체: KBS연예",
                f"- 제목: {title}",
                f"- 링크: {url}",
                "- 상태: 보도(1차)",
                f"- id: {url}",
                "- 요약(3~5줄):",
                "  - (요약 보강 필요) 원문 기반 요약.",
                "- 키워드: 인터뷰",
            ])
            interviews.append(Entry(year=year, block=block3, url=url))

        time.sleep(0.2)

    return events, appearances, interviews


def vogue_collect(limit: int = 12) -> list[Entry]:
    """Collect Vogue posts whose title/og:title contains 고윤정."""
    try:
        html = http_get(VOGUE_SEARCH)
    except Exception:
        return []
    links = re.findall(r"href=[\"']([^\"']+)[\"']", html, flags=re.I)
    urls = []
    seen = set()
    for href in links:
        u = urljoin(VOGUE_SEARCH, href).split("#")[0]
        if "www.vogue.co.kr/20" not in u:
            continue
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)
    urls = sorted(urls)  # deterministic

    out: list[Entry] = []
    for u in urls:
        if len(out) >= limit:
            break
        try:
            page = http_get(u)
        except Exception:
            continue
        soup = BeautifulSoup(page, "html.parser")
        title = ""
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = " ".join(og["content"].split())
        elif soup.title and soup.title.string:
            title = " ".join(soup.title.string.split())
        if "고윤정" not in title:
            continue
        # infer date from URL
        m = re.search(r"/((20\d{2})/(\d{2})/(\d{2}))/", u)
        date = "(페이지 내 표기 확인 필요)"
        year = None
        if m:
            year = int(m.group(2))
            date = f"{m.group(2)}-{m.group(3)}-{m.group(4)}"
        if not year:
            continue
        block = "\n".join([
            f"- 날짜: {date}",
            "- 매체: Vogue Korea (보그 코리아)",
            "- 구분: 화보/기사",
            f"- 제목: {title}",
            f"- 링크(원문): {u}",
            "- 상태: 공식확정",
            f"- id: {u}",
        ])
        out.append(Entry(year=year, block=block, url=u))
        time.sleep(0.2)
    return out


def generic_search_collect(site: str, search_url: str, brand: str, limit: int = 10) -> list[Entry]:
    """Generic collector for magazine sites with a server-rendered search page.

    This is best-effort and conservative:
    - parse hrefs from search HTML
    - visit candidate URLs and use og:title
    - infer date from URL when possible

    If anything is blocked/slow, it returns [] (no hard failure).
    """
    try:
        html = http_get(search_url)
    except Exception:
        return []

    links = re.findall(r"href=[\"']([^\"']+)[\"']", html, flags=re.I)
    urls: list[str] = []
    seen_local: set[str] = set()
    for href in links:
        u = urljoin(search_url, href).split("#")[0]
        if site not in u:
            continue
        # avoid obvious non-content pages
        if any(x in u for x in ["/wp-admin", "/feed", "/tag/", "/category/"]):
            continue
        if u in seen_local:
            continue
        seen_local.add(u)
        urls.append(u)

    urls = sorted(urls)

    out: list[Entry] = []
    for u in urls:
        if len(out) >= limit:
            break

        # Hard filter: only visit pages with a date-like path (/YYYY/MM/DD/). This keeps runtime bounded.
        if not re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", u):
            continue

        try:
            page = http_get(u)
        except Exception:
            continue
        soup = BeautifulSoup(page, "html.parser")
        title = ""
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = " ".join(og["content"].split())
        elif soup.title and soup.title.string:
            title = " ".join(soup.title.string.split())
        if "고윤정" not in title:
            continue

        date = "(페이지 내 표기 확인 필요)"
        year = None
        # try: /YYYY/MM/DD/
        m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", u)
        if m:
            year = int(m.group(1))
            date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

        if not year:
            continue

        block = "\n".join([
            f"- 날짜: {date}",
            f"- 매체: {brand}",
            "- 구분: 화보/기사",
            f"- 제목: {title}",
            f"- 링크(원문): {u}",
            "- 상태: 공식확정",
            f"- id: {u}",
        ])
        out.append(Entry(year=year, block=block, url=u))
        time.sleep(0.2)

    return out


def apply_entries(path: str, entries: Iterable[Entry]) -> tuple[int, list[str]]:
    md = read_text(path)
    changed = 0
    added_urls: list[str] = []
    for e in sorted(entries, key=lambda x: (x.year, x.url)):
        before = md
        md = insert_entry_under_year(md, e.year, e.block, e.url)
        if md != before:
            changed += 1
            added_urls.append(e.url)
    if changed:
        write_text(path, md)
    return changed, added_urls


def add_to_seen(urls: Iterable[str]) -> None:
    """Best-effort: call scripts/add_seen_url.sh for each url."""
    import subprocess

    add_seen = os.path.join(BASE, "scripts", "add_seen_url.sh")
    for u in urls:
        try:
            subprocess.run([add_seen, u], cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass


def main() -> int:
    seen = load_seen_urls()

    events, appearances, interviews = kbs_collect()
    # filter by seen-urls, too
    events = [e for e in events if e.url not in seen]
    appearances = [e for e in appearances if e.url not in seen]
    interviews = [e for e in interviews if e.url not in seen]

    vogue_entries = [e for e in vogue_collect() if e.url not in seen]
    elle_entries = [e for e in generic_search_collect("www.elle.co.kr", ELLE_SEARCH, "ELLE Korea", limit=8) if e.url not in seen]
    w_entries = [e for e in generic_search_collect("www.wkorea.com", W_SEARCH, "W Korea", limit=8) if e.url not in seen]
    bazaar_entries = [e for e in generic_search_collect("www.harpersbazaar.co.kr", BAZAAR_SEARCH, "Harper’s BAZAAR Korea", limit=8) if e.url not in seen]
    gq_entries = [e for e in generic_search_collect("www.gqkorea.co.kr", GQ_SEARCH, "GQ Korea", limit=8) if e.url not in seen]

    ch = 0
    added_all: list[str] = []

    c, u = apply_entries(EVENTS_MD, events)
    ch += c; added_all += u
    c, u = apply_entries(APPEARANCES_MD, appearances)
    ch += c; added_all += u
    c, u = apply_entries(INTERVIEWS_MD, interviews)
    ch += c; added_all += u
    c, u = apply_entries(EDITORIAL_MD, vogue_entries)
    ch += c; added_all += u
    c, u = apply_entries(EDITORIAL_MD, elle_entries)
    ch += c; added_all += u
    c, u = apply_entries(EDITORIAL_MD, w_entries)
    ch += c; added_all += u
    c, u = apply_entries(EDITORIAL_MD, bazaar_entries)
    ch += c; added_all += u
    c, u = apply_entries(EDITORIAL_MD, gq_entries)
    ch += c; added_all += u

    # Auto-add to seen-urls (best-effort)
    if added_all:
        add_to_seen(added_all)

    print(f"auto_collect_visual_links: added blocks: {ch}, added_to_seen: {len(added_all)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

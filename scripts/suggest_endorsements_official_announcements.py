#!/usr/bin/env python3
"""Suggest official announcement link candidates for endorsements entries.

Goal:
- For endorsements entries where '링크(공식 발표)' is '(확인 필요)', output Google site-search links
  against known official brand domains (from sources/brands-watch.md).

Writes into news/YYYY-MM-DD.md under a marker block.
No web fetching.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from urllib.parse import quote, urlparse

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = "Asia/Seoul"

BRANDS_WATCH = os.path.join(BASE, "sources", "brands-watch.md")
NEWS_DIR = os.path.join(BASE, "news")

ENDORSEMENT_FILES = [
    os.path.join(BASE, "pages", "endorsements", "beauty.md"),
    os.path.join(BASE, "pages", "endorsements", "fashion.md"),
    os.path.join(BASE, "pages", "endorsements", "lifestyle.md"),
]

MARK_START = "<!-- AUTO-ENDORSEMENTS-OFFICIAL-ANNOUNCE-SUGGEST:START -->"
MARK_END = "<!-- AUTO-ENDORSEMENTS-OFFICIAL-ANNOUNCE-SUGGEST:END -->"

BRAND_LINE_RE = re.compile(r"^\s*-\s*([A-Za-z0-9\-\s\uAC00-\uD7A3&/().']+):\s*(https?://\S+)")


@dataclass
class Entry:
    file: str
    brand: str
    campaign_url: str | None


def today() -> str:
    return os.environ.get("WIKI_TODAY") or os.popen(f"TZ={TZ} date +%Y-%m-%d").read().strip()


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, s: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def google(q: str) -> str:
    return "https://www.google.com/search?q=" + quote(q)


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def parse_brand_domains(md: str) -> dict[str, str]:
    """Return mapping of normalized brand token -> domain (netloc)."""
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
        # normalize: take token before '(' as simple key too
        key = name
        out[key] = d
        key2 = name.split("(", 1)[0].strip()
        if key2 and key2 not in out:
            out[key2] = d
    return out


def parse_endorsements() -> list[Entry]:
    entries: list[Entry] = []
    for f in ENDORSEMENT_FILES:
        if not os.path.exists(f):
            continue
        lines = read(f).splitlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("- 브랜드/회사명:"):
                brand = lines[i].split(":", 1)[1].strip()
                j = i + 1
                end = j
                while end < len(lines) and not lines[end].startswith("- 브랜드/회사명:") and not lines[end].startswith("## "):
                    end += 1
                block = "\n".join(lines[i:end])
                if "링크(공식 발표): (확인 필요)" not in block:
                    i = end
                    continue
                campaign = None
                for ln in block.splitlines():
                    if "링크(공식 영상/캠페인):" in ln:
                        campaign = ln.split(":", 1)[1].strip()
                        break
                entries.append(Entry(file=os.path.relpath(f, BASE), brand=brand, campaign_url=campaign))
                i = end
            else:
                i += 1
    return entries


def build_block(domains: dict[str, str], entries: list[Entry]) -> str:
    lines = [
        MARK_START,
        "## 광고/엠버서더 ‘공식 발표’ 링크 후보(자동)",
        "> 목표: `pages/endorsements/*`의 `링크(공식 발표): (확인 필요)` 항목을 공식 도메인 근거로 보강하기 위한 검색 링크입니다.",
        "> 주의: 자동 적용하지 않습니다. 브랜드 공식 사이트/공식 뉴스/공식 보도자료에서 ‘모델/뮤즈/앰버서더’ 문구를 확인 후 반영하세요.",
        "",
    ]

    if not entries:
        lines += ["- (현재 제안할 항목이 없습니다)", "", MARK_END]
        return "\n".join(lines)

    # limit output size
    entries = entries[:12]

    for e in entries:
        d = None
        # try match direct key or prefix before '(' 
        k1 = e.brand
        k2 = e.brand.split("(", 1)[0].strip()
        d = domains.get(k1) or domains.get(k2)

        lines.append(f"### {e.brand} ({e.file})")
        if d:
            lines.append(f"- site search(공식 도메인): {google(f'site:{d} 고윤정 모델')}")
            lines.append(f"- site search(뮤즈/앰버서더): {google(f'site:{d} 고윤정 뮤즈')}")
            lines.append(f"- site search(영문/국문 병행): {google(f'site:{d} Go Youn-jung ambassador')}")
        else:
            lines.append(f"- 도메인 힌트 없음(brands-watch 보강 필요): {google(f'{e.brand} 고윤정 공식 발표 모델')}")

        if e.campaign_url:
            lines.append(f"- 참고(캠페인/영상): {e.campaign_url}")
        lines.append("")

    lines.append(MARK_END)
    return "\n".join(lines)


def upsert_block(news_md: str, block: str) -> str:
    if MARK_START in news_md and MARK_END in news_md:
        pre = news_md.split(MARK_START)[0]
        post = news_md.split(MARK_END, 1)[1]
        return pre.rstrip() + "\n\n" + block + "\n\n" + post.lstrip()

    if "## 실행 이력" in news_md:
        a, b = news_md.split("## 실행 이력", 1)
        return a.rstrip() + "\n\n" + block + "\n\n## 실행 이력" + b

    return news_md.rstrip() + "\n\n" + block + "\n"


def main() -> int:
    brands_md = read(BRANDS_WATCH) if os.path.exists(BRANDS_WATCH) else ""
    domains = parse_brand_domains(brands_md)
    entries = parse_endorsements()
    block = build_block(domains, entries)

    t = today()
    news_path = os.path.join(NEWS_DIR, f"{t}.md")
    if os.path.exists(news_path):
        news = read(news_path)
    else:
        news = f"# {t} 업데이트\n\n## 실행 상태\n\n## 실행 이력\n"

    out = upsert_block(news, block)
    if out != news:
        write(news_path, out)

    print("suggest_endorsements_official_announcements: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

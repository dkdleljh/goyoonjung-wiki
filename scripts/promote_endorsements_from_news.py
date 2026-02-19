#!/usr/bin/env python3
"""Promote endorsement/brand items from today's news log into pages/endorsements.md.

Link-first, conservative rules:
- Require name (고윤정) in title
- Require at least one brand/endorsement token
- Append minimal block with URL only

Best-effort; never fails pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import domain_policy

BASE = Path(__file__).resolve().parent.parent
NEWS = BASE / "news" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
OUT = BASE / "pages" / "endorsements.md"

NAME = "고윤정"
TOKENS = [
    "엠버서더",
    "앰버서더",
    "모델",
    "캠페인",
    "광고",
    "화보",
    "샤넬",
    "구달",
    "보다나",
    "마리떼",
    "렌즈미",
    "푸라닭",
    "디스커버리",
    "부쉐론",
    "캐롯",
]

BRAND_MAP_PATH = BASE / "config" / "endorsement-brand-map.yml"

URL_RE = re.compile(r"https?://[^\s)]+")
MD_LINK_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)]+)\)")


@dataclass(frozen=True)
class Item:
    title: str
    url: str


def parse_items(text: str) -> list[Item]:
    out: list[Item] = []
    for ln in text.splitlines():
        m = MD_LINK_RE.search(ln)
        if not m:
            continue
        title = " ".join(m.group("title").split())
        url = m.group("url").strip()
        if title and url:
            out.append(Item(title=title, url=url))
    return out


def ensure_year(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    return md.rstrip() + f"\n\n{hdr}\n"


def insert(md: str, year: int, block: str, url: str) -> str:
    if url in md:
        return md
    md = ensure_year(md, year)
    hdr = f"## {year}"
    parts = md.split(hdr)
    if len(parts) < 2:
        return md + "\n" + block.rstrip() + "\n"
    before = parts[0] + hdr
    after = hdr.join(parts[1:])
    return before + "\n" + block.rstrip() + "\n\n" + after.lstrip("\n")


def load_brand_map() -> dict[str, str]:
    # minimal YAML (key: value) parser
    out: dict[str, str] = {}
    if not BRAND_MAP_PATH.exists():
        return out
    for raw in BRAND_MAP_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith('#') or ':' not in ln:
            continue
        k, v = ln.split(':', 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def detect_brand(title: str, brand_map: dict[str, str]) -> str:
    for tok, label in brand_map.items():
        if tok and tok in title:
            return label
    # fallback: first matching token
    for t in TOKENS:
        if t in title:
            return t
    return "(자동 분류 필요)"


def main() -> int:
    try:
        policy = domain_policy.load_policy()
        if not NEWS.exists() or not OUT.exists():
            return 0
        brand_map = load_brand_map()
        news = NEWS.read_text(encoding="utf-8", errors="ignore")
        items = parse_items(news)
        cands = [
            it
            for it in items
            if (
                NAME in it.title
                and any(t in it.title for t in TOKENS)
                and policy.grade_for_url(it.url) == "S"
            )
        ]
        if not cands:
            print("promote_endorsements_from_news: promoted=0")
            return 0

        md = OUT.read_text(encoding="utf-8", errors="ignore")
        promoted = 0
        for it in cands:
            year = datetime.now().year
            brand = detect_brand(it.title, brand_map)
            block = "\n".join(
                [
                    f"- 날짜: {datetime.now().strftime('%Y-%m-%d')}",
                    "- 구분: 광고/브랜드(뉴스 자동 반영)",
                    f"- 브랜드/캠페인: {brand}",
                    f"- 링크(원문): {it.url}",
                    "- 상태: 보도(2차)",
                    f"- id: {it.url}",
                    f"- 메모: 자동 감지(제목: {it.title})",
                ]
            )
            before = md
            md = insert(md, year, block, it.url)
            if md != before:
                promoted += 1

        if promoted:
            OUT.write_text(md, encoding="utf-8")
        print(f"promote_endorsements_from_news: promoted={promoted}")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

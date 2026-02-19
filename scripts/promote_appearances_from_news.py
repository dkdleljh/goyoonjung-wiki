#!/usr/bin/env python3
"""Promote appearance/event items from daily news log into pages/appearances.md.

Design goals:
- Unmanned + link-first (copyright-safe): only store URLs + minimal metadata.
- Best-effort: never fail the pipeline.
- Conservative: only promote when we are confident it's an appearance/event.

Current rule set (v1):
- If a news item mentions "마니또 클럽" and "고윤정" (title/desc), create an appearance entry.

Inputs:
- news/YYYY-MM-DD.md (today)
Outputs:
- pages/appearances.md (append under year section)
- sources/seen-urls.* (optional) via scripts/add_seen_url.sh when present

This intentionally avoids copying article text.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import domain_policy

BASE = Path(__file__).resolve().parent.parent
NEWS_DIR = BASE / "news"
APPEARANCES_MD = BASE / "pages" / "appearances.md"
ADD_SEEN = BASE / "scripts" / "add_seen_url.sh"

NAME = "고윤정"

# 프로그램/채널 키워드 → 표시용 프로그램명/플랫폼 힌트
# (보수적으로: 제목에 NAME + 키워드가 같이 있을 때만 승격)
RULES: list[tuple[list[str], str, str]] = [
    (["마니또 클럽"], "MBC <마니또 클럽>", "MBC"),
    (["유 퀴즈", "유퀴즈", "YOU QUIZ", "You Quiz"], "tvN <유 퀴즈 온 더 블럭>", "tvN"),
    (["살롱드립"], "YouTube <살롱드립>", "YouTube"),
    (["채널십오야", "십오야"], "YouTube <채널십오야>", "YouTube"),
    (["와글와글"], "YouTube <나영석의 와글와글>", "YouTube"),
]


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    dt: datetime | None


def today_path() -> Path:
    return NEWS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"


def parse_dt(s: str) -> datetime | None:
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def parse_news_markdown(md: str) -> list[NewsItem]:
    items: list[NewsItem] = []

    # Accept common formats from collectors:
    # - [Category] [Title](URL) - Source (YYYY-MM-DD HH:MM)
    # - [GoogleNews/Q:LABEL] [Title](URL) (YYYY-MM-DD HH:MM)
    pat = re.compile(
        r"^-\s*\[[^\]]+\]\s*\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)]+)\)(?:\s*-\s*(?P<source>[^()]+))?\s*(?:\((?P<dt>\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)\))?\s*$"
    )

    for raw in md.splitlines():
        m = pat.match(raw.strip())
        if not m:
            continue
        title = " ".join((m.group("title") or "").split())
        url = (m.group("url") or "").strip()
        source = " ".join((m.group("source") or "").strip().split())
        dt = parse_dt(m.group("dt") or "")
        if not title or not url:
            continue
        items.append(NewsItem(title=title, url=url, source=source, dt=dt))

    return items


def match_rule(item: NewsItem) -> tuple[str, str] | None:
    """Return (program_name, platform) if matches a known appearance rule."""
    text = item.title
    if NAME not in text:
        return None
    for keywords, program, platform in RULES:
        if any(k in text for k in keywords):
            return program, platform
    return None


def classify_appearance(item: NewsItem) -> tuple[str, str, str]:
    """Return (date_yyyy_mm_dd, category_text, status_text)."""
    # date
    if item.dt is not None:
        date_s = item.dt.strftime("%Y-%m-%d")
    else:
        date_s = datetime.now().strftime("%Y-%m-%d")

    # category
    cat = "예능"

    # status heuristic
    t = item.title
    if any(k in t for k in ("공개", "라인업", "합류", "추가", "출연 확정", "출연확정", "출연")):
        status = "보도(1차)"
    elif any(k in t for k in ("예고", "티저", "방송 말미", "방송")):
        status = "보도(2차)"
    else:
        status = "보도(2차)"

    return date_s, cat, status


def ensure_year_section(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    # Insert before next lower year if exists, else append.
    years = sorted({int(y) for y in re.findall(r"^## (\d{4})\s*$", md, flags=re.M)}, reverse=True)
    if not years:
        return md + f"\n\n{hdr}\n"
    for y in years:
        if year > y:
            m = re.search(rf"^## {y}\s*$", md, flags=re.M)
            if m:
                return md[: m.start()] + f"{hdr}\n\n" + md[m.start() :]
    return md + f"\n\n{hdr}\n"


def insert_under_year(md: str, year: int, block: str, url: str) -> str:
    if url in md:
        return md
    md = ensure_year_section(md, year)
    hdr = f"## {year}"
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
    new_section = section.rstrip() + "\n" + block.rstrip() + "\n\n"
    return "".join(lines[:start]) + new_section + "".join(lines[end:])


def try_add_seen_url(url: str) -> None:
    if not ADD_SEEN.exists():
        return
    try:
        subprocess.run([str(ADD_SEEN), url], cwd=str(BASE), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return


def main() -> int:
    try:
        policy = domain_policy.load_policy()
        p = today_path()
        if not p.exists() or not APPEARANCES_MD.exists():
            return 0

        news_md = p.read_text(encoding="utf-8")
        items = parse_news_markdown(news_md)
        matched: list[tuple[NewsItem, str, str]] = []
        for it in items:
            if policy.grade_for_url(it.url) != "S":
                continue
            m = match_rule(it)
            if m:
                program, platform = m
                matched.append((it, program, platform))
        if not matched:
            print("promote_appearances_from_news: promoted=0 (no candidates)")
            return 0

        app_md = APPEARANCES_MD.read_text(encoding="utf-8")
        promoted = 0

        for it, program, platform in matched:
            date_s, cat, status = classify_appearance(it)
            year = int(date_s[:4])

            # If URL is YouTube, override platform hint
            if any(x in it.url for x in ("youtube.com", "youtu.be")):
                platform = "YouTube"

            block = "\n".join(
                [
                    f"- 날짜: {date_s}",
                    f"- 구분: {cat}",
                    f"- 프로그램/행사명: {program} (뉴스 자동 반영)",
                    f"- 플랫폼/방송사: {platform}",
                    f"- 링크(공식/원문): {it.url}",
                    f"- 상태: {status}",
                    f"- id: {it.url}",
                    f"- 메모: 자동 수집 로그에서 감지(제목: {it.title}).",
                    "",
                ]
            )

            before = app_md
            app_md = insert_under_year(app_md, year, block, it.url)
            if app_md != before:
                promoted += 1
                try_add_seen_url(it.url)

        if promoted:
            APPEARANCES_MD.write_text(app_md, encoding="utf-8")

        print(f"promote_appearances_from_news: promoted={promoted}")
        return 0
    except Exception:
        # Best-effort: never break pipeline
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

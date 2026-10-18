#!/usr/bin/env python3
"""Collect official YouTube uploads via RSS feeds.

- Reads config/youtube-feeds.yml (simple YAML subset)
- Filters by keyword in title (default: "고윤정")
- De-dupes via SQLite (wiki.db) using db_manager
- Appends link-only items into today's news/YYYY-MM-DD.md

If RSS fails, validate the same channel’s public uploads playlist metadata.
No video, transcript, login or private API is used.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
sys.path.append(str(SCRIPT_DIR))
import db_manager  # noqa: E402
import relevance  # noqa: E402
from collector_io import append_news_lines  # noqa: E402
from source_transport import request, save_report  # noqa: E402
from youtube_sources import collect_source  # noqa: E402

CONF_PATH = BASE / "config" / "youtube-feeds.yml"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
TIMEOUT = 15




def parse_simple_yml(text: str) -> dict:
    out: dict = {"feeds": []}
    cur = None
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        if ln.startswith("keyword:"):
            out["keyword"] = ln.split(":", 1)[1].strip().strip('"')
            continue
        if ln.startswith("feeds:"):
            continue
        if ln.startswith("-"):
            cur = {}
            out["feeds"].append(cur)
            rest = ln[1:].strip()
            if rest and ":" in rest:
                k, v = rest.split(":", 1)
                cur[k.strip()] = v.strip().strip('"')
            continue
        if cur is not None and ":" in ln:
            k, v = ln.split(":", 1)
            cur[k.strip()] = v.strip().strip('"')
    return out


def fetch(url: str) -> bytes:
    return request(url)


def get_today_news_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return BASE / "news" / f"{today}.md"


def ensure_news_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {datetime.now().strftime('%Y-%m-%d')} 업데이트\n\n## 뉴스/업데이트\n", encoding="utf-8")


def append_lines(path: Path, lines: list[str]) -> None:
    append_news_lines(path, lines)


def text_of(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def main(check: bool = False) -> int:
    if not CONF_PATH.exists():
        print("Missing YouTube configuration")
        return 1
    conf = parse_simple_yml(CONF_PATH.read_text(encoding="utf-8"))
    keyword, feeds = conf.get("keyword", "고윤정"), conf.get("feeds", [])
    if not feeds:
        print("No YouTube sources configured")
        return 1
    # By default check every configured channel. Explicit small batches remain supported.
    max_feeds = int(os.environ.get("MAX_YT_FEEDS", "0"))
    offset = int(os.environ.get("BATCH_OFFSET_YT", "0")) % len(feeds)
    if not check and max_feeds > 0 and len(feeds) > max_feeds:
        feeds = (feeds[offset:] + feeds[:offset])[:max_feeds]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda feed: collect_source(feed, fetch), feeds))
    pending, out_lines, reports = [], [], []
    if not check:
        db_manager.init_db()
    for feed, (rows, report) in zip(feeds, results, strict=True):
        name = feed["name"]
        related = [r for r in rows if keyword in r["title"] and relevance.is_relevant(r["title"], r["url"], name, "")]
        report["matched"] = len(related)
        reports.append(report)
        if check:
            continue
        for row in related:
            href = row["url"]
            if db_manager.is_url_seen(href):
                continue
            date = row["date"].replace("T", " ").replace("Z", "")[:16] if row["date"] else "게시일 확인 필요"
            title = " ".join(row["title"].split()).replace("[", "［").replace("]", "］")
            out_lines.append(f"- [YouTube/{name}] [{title}]({href}) ({date})")
            pending.append((href, f"youtube:{name}"))
    if check:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        append_lines(get_today_news_path(), out_lines)
        for url, source in pending:
            db_manager.add_seen_url(url, source=source)
        save_report("youtube", reports)
        print(f"auto_collect_youtube_feeds: new={len(out_lines)}")
    errors = sum(r["status"] != "success" for r in reports)
    print(f"source_errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check all channels without writing data")
    raise SystemExit(main(check=parser.parse_args().check))

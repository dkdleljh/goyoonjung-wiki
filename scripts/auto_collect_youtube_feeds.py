#!/usr/bin/env python3
"""Collect official YouTube uploads via RSS feeds.

- Reads config/youtube-feeds.yml (simple YAML subset)
- Filters by keyword in title (default: "고윤정")
- De-dupes via SQLite (wiki.db) using db_manager
- Appends link-only items into today's news/YYYY-MM-DD.md

This avoids scraping YouTube HTML and is stable/unmanned.
"""

from __future__ import annotations

import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
sys.path.append(str(SCRIPT_DIR))
import db_manager  # noqa: E402
import relevance  # noqa: E402

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


def fetch(url: str) -> bytes | None:
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except Exception:
        return None


def get_today_news_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return BASE / "news" / f"{today}.md"


def ensure_news_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {datetime.now().strftime('%Y-%m-%d')} 업데이트\n\n## 뉴스/업데이트\n", encoding="utf-8")


def append_lines(path: Path, lines: list[str]) -> None:
    if not lines:
        return
    ensure_news_file(path)
    with path.open("a", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def text_of(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def main() -> int:
    if not CONF_PATH.exists():
        return 0

    conf = parse_simple_yml(CONF_PATH.read_text(encoding="utf-8"))
    keyword = conf.get("keyword", "고윤정")
    feeds = conf.get("feeds", [])
    if not feeds:
        return 0

    db_manager.init_db()
    out_lines: list[str] = []

    # Rolling batch
    max_feeds = int(os.environ.get("MAX_YT_FEEDS", "4"))
    offset = int(os.environ.get("BATCH_OFFSET_YT", "0"))
    if max_feeds > 0 and len(feeds) > max_feeds:
        feeds = (feeds[offset:] + feeds[:offset])[:max_feeds]

    for feed in feeds:
        name = feed.get("name", "YouTube")
        url = feed.get("url")
        if not url:
            continue
        xml_data = fetch(url)
        if not xml_data:
            continue
        try:
            root = ET.fromstring(xml_data)
        except Exception:
            continue

        # YouTube atom: entry
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry")[:15]:
            title = text_of(entry.find("{http://www.w3.org/2005/Atom}title"))
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            href = link_el.get("href") if link_el is not None else ""
            published = text_of(entry.find("{http://www.w3.org/2005/Atom}published"))

            if not title or not href:
                continue
            # relevance gate: require keyword in title (or description via relevance if present)
            if keyword not in title:
                continue
            if db_manager.is_url_seen(href):
                continue
            if not relevance.is_relevant(title, href, name, ""):
                continue

            date_str = published.replace("T", " ").replace("Z", "")[:16] if published else datetime.now().strftime("%Y-%m-%d %H:%M")
            out_lines.append(f"- [YouTube/{name}] [{title}]({href}) ({date_str})")
            db_manager.add_seen_url(href, source=f"youtube:{name}")
            time.sleep(0.05)

    append_lines(get_today_news_path(), out_lines)
    print(f"auto_collect_youtube_feeds: new={len(out_lines)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

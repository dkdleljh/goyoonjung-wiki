#!/usr/bin/env python3
"""Collect links via Google News RSS using custom keyword queries.

- Reads config/google-news-queries.txt (tab-separated: label \t query)
- Fetches Google News RSS for each query
- Decodes Google News redirect URLs (HEAD)
- De-dupes via SQLite DB (db_manager)
- Appends to today's news/YYYY-MM-DD.md as link-only lines

Best-effort, always returns 0.
"""

from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
sys.path.append(str(SCRIPT_DIR))
import db_manager
import relevance

CONF_PATH = BASE / "config" / "google-news-queries.txt"
ALLOWLIST = BASE / "config" / "allowlist-domains.txt"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
TIMEOUT = 15
RSS_TEMPLATE = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"


def decode_google_news_url(source_url: str) -> str:
    """Resolve Google News redirect URL.

    Quality rule:
    - If it can't be resolved away from news.google.com, we skip the item later.
    """
    import urllib.request
    try:
        req = urllib.request.Request(
            source_url,
            method="GET",
            headers={"User-Agent": UA},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.geturl()
    except Exception:
        return source_url


def fetch_rss(url: str) -> bytes | None:
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


def load_allowlist() -> set[str]:
    if not ALLOWLIST.exists():
        return set()
    out: set[str] = set()
    for raw in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith('#'):
            continue
        ln = ln.replace('https://', '').replace('http://', '')
        out.add(ln.strip('/'))
    return out


def load_queries() -> list[tuple[str, str]]:
    if not CONF_PATH.exists():
        return []
    out: list[tuple[str, str]] = []
    for raw in CONF_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        out.append((parts[0].strip(), parts[1].strip()))
    return out


def main() -> int:
    db_manager.init_db()
    allow = load_allowlist()
    qlist = load_queries()
    if not qlist:
        return 0

    news_path = get_today_news_path()
    total = 0

    for label, query in qlist:
        rss_url = RSS_TEMPLATE.format(q=quote_plus(query))
        xml_data = fetch_rss(rss_url)
        if not xml_data:
            continue

        try:
            root = ET.fromstring(xml_data)
        except Exception:
            continue

        channel = root.find("channel")
        if channel is None:
            continue

        new_lines: list[str] = []
        for item in channel.findall("item")[:15]:
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").replace("<b>", "").replace("</b>", "").strip()
            desc_el = item.find("description")
            desc = desc_el.text if desc_el is not None and desc_el.text else ""
            if not relevance.is_relevant(title, "", label, desc):
                continue
            origin_link = (link_el.text or "").strip()
            if not title or not origin_link:
                continue

            real_url = decode_google_news_url(origin_link)
            # 품질: 리다이렉트 해소 실패(여전히 news.google.com)이면 스킵
            if "news.google.com" in real_url:
                continue
            # allowlist gate (optional)
            if allow:
                from urllib.parse import urlsplit
                host = urlsplit(real_url).netloc.lower().split(':', 1)[0]
                if host not in allow:
                    continue

            if db_manager.is_url_seen(real_url):
                continue

            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            if pub_el is not None and pub_el.text:
                try:
                    dt = parsedate_to_datetime(pub_el.text)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            new_lines.append(f"- [GoogleNews/Q:{label}] [{title}]({real_url}) ({date_str})")
            db_manager.add_seen_url(real_url, source=f"gnews_query:{label}")
            total += 1
            time.sleep(0.05)

        append_lines(news_path, new_lines)

    print(f"auto_collect_google_news_queries: new={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

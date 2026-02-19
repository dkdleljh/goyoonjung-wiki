#!/usr/bin/env python3
"""Collect more links via Google News RSS using site: filters.

Why:
- RSS is more stable than scraping portal HTML.
- site:domain queries help catch magazine/press pages even if their RSS is blocked.

Behavior:
- For each domain in config/google-news-sites.txt, fetch Google News RSS:
  https://news.google.com/rss/search?q=site:<domain>+고윤정+when:7d&hl=ko&gl=KR&ceid=KR:ko
- Decode Google News URLs (HEAD) to the real article URL.
- De-dupe using SQLite DB (db_manager) used by existing google news collector.
- Append link-only items to today's news/YYYY-MM-DD.md under "## 뉴스/업데이트".

Never hard-fails the pipeline; returns 0.
"""

from __future__ import annotations

import os
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
sys.path.append(str(SCRIPT_DIR))
import db_manager  # noqa: E402
import domain_policy  # noqa: E402
import normalize_url  # noqa: E402
import relevance  # noqa: E402

CONF_PATH = BASE / "config" / "google-news-sites.txt"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
TIMEOUT = 15

KEYWORD = "고윤정"
RSS_TEMPLATE = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"


@dataclass(frozen=True)
class Site:
    domain: str
    label: str
    hint: str


def decode_google_news_url(source_url: str) -> str:
    import urllib.request

    try:
        req = urllib.request.Request(source_url, method="GET", headers={"User-Agent": UA})
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


def load_sites() -> list[Site]:
    """Load site list.

    Supports rolling batches via environment variables:
    - MAX_SITES: max number of domains to process per run (default: 8)
    - BATCH_OFFSET: start offset (optional; used by runner)

    This prevents very large site lists from causing long runtimes / OOM.
    """
    if not CONF_PATH.exists():
        return []
    out: list[Site] = []
    for raw in CONF_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        domain = parts[0].strip()
        label = parts[1].strip()
        hint = parts[2].strip() if len(parts) >= 3 else "general"
        out.append(Site(domain=domain, label=label, hint=hint))
    return out


def ensure_news_file(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {datetime.now().strftime('%Y-%m-%d')} 업데이트\n\n## 뉴스/업데이트\n", encoding="utf-8")


def append_items(path: Path, items: list[dict]) -> None:
    if not items:
        return
    ensure_news_file(path)
    with path.open("a", encoding="utf-8") as f:
        for it in items:
            f.write(
                f"- [GoogleNews/{it['label']}] [{it['title']}]({it['url']}) ({it['date']})\n"
            )


def main() -> int:
    db_manager.init_db()
    policy = domain_policy.load_policy()
    sites = load_sites()
    if not sites:
        return 0

    news_path = get_today_news_path()

    total_new = 0
    # Rolling batch (round-robin)
    max_sites = int(os.environ.get("MAX_SITES", "8"))
    offset = int(os.environ.get("BATCH_OFFSET", "0"))
    if max_sites > 0 and len(sites) > max_sites:
        sites = (sites[offset:] + sites[:offset])[:max_sites]

    for s in sites:
        q = f"site:{s.domain} {KEYWORD} when:7d"
        rss_url = RSS_TEMPLATE.format(q=quote_plus(q))
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

        new_items: list[dict] = []
        for item in channel.findall("item")[:15]:
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").replace("<b>", "").replace("</b>", "").strip()
            desc_el = item.find("description")
            desc = desc_el.text if desc_el is not None and desc_el.text else ""
            if not relevance.is_relevant(title, "", s.label, desc):
                continue
            origin_link = (link_el.text or "").strip()
            if not title or not origin_link:
                continue
            if KEYWORD not in title:
                continue

            real_url = normalize_url.norm(decode_google_news_url(origin_link))
            if "news.google.com" in real_url:
                continue
            grade = policy.grade_for_url(real_url)
            lane = policy.lane_for_url(real_url)
            if lane == "discard":
                db_manager.record_url_event(real_url, grade, "blocked", f"gnews_site:{s.domain}")
                continue

            if db_manager.is_url_seen(real_url):
                db_manager.record_url_event(
                    real_url, grade, "duplicate", f"gnews_site:{s.domain}", is_duplicate=True
                )
                continue

            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            if pub_el is not None and pub_el.text:
                try:
                    dt = parsedate_to_datetime(pub_el.text)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            if lane == "landed":
                new_items.append({"title": title, "url": real_url, "date": date_str, "label": s.label})
                db_manager.record_url_event(real_url, grade, "landed", f"gnews_site:{s.domain}")
                total_new += 1
            else:
                db_manager.add_or_update_candidate(
                    real_url,
                    grade=grade,
                    lane=lane,
                    title=title,
                    source=s.label,
                )
                db_manager.record_url_event(real_url, grade, lane, f"gnews_site:{s.domain}")
            db_manager.add_seen_url(real_url, source=f"gnews_site:{s.domain}")
            time.sleep(0.05)

        append_items(news_path, new_items)

    print(f"auto_collect_google_news_sites: new={total_new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""RSS-based collector for magazine sites (stable, unmanned).

- Reads config/magazine-rss.yml
- Fetches RSS feeds (XML)
- De-dupes using:
  - sources/seen-urls.txt (best-effort)
  - existing markdown contains URL
- Lands link-only entries into:
  - pages/pictorials/editorial.md (default)
  - pages/interviews.md (when type_hint is interview)

No article text is copied.
"""

from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
CONF_PATH = BASE / "config" / "magazine-rss.yml"
SEEN_TXT = BASE / "sources" / "seen-urls.txt"
EDITORIAL_MD = BASE / "pages" / "pictorials" / "editorial.md"
INTERVIEWS_MD = BASE / "pages" / "interviews.md"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
TIMEOUT = 15


@dataclass(frozen=True)
class Entry:
    year: int
    block: str
    url: str
    target: str  # 'editorial' | 'interviews'


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def load_seen() -> set[str]:
    if not SEEN_TXT.exists():
        return set()
    return {ln.strip() for ln in SEEN_TXT.read_text(encoding="utf-8").splitlines() if ln.strip()}


def fetch(url: str) -> bytes | None:
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except Exception:
        return None


def parse_simple_yml(text: str) -> dict:
    """Very small YAML subset parser: key: value + list of dict items.

    Avoids extra dependencies.
    Expected structure:
      keyword: "..."
      feeds:
        - name: "..."
          url: "..."
          type_hint: "..."
    """
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
            # allow '- name: x' inline
            rest = ln[1:].strip()
            if rest:
                k, v = rest.split(":", 1)
                cur[k.strip()] = v.strip().strip('"')
            continue
        if cur is not None and ":" in ln:
            k, v = ln.split(":", 1)
            cur[k.strip()] = v.strip().strip('"')
    return out


def clean_title(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def ensure_year_section(md: str, year: int) -> str:
    hdr = f"## {year}"
    if hdr in md:
        return md
    years = sorted({int(y) for y in re.findall(r"^## (\d{4})\s*$", md, flags=re.M)}, reverse=True)
    if not years:
        return md + f"\n\n{hdr}\n(추가 보강 필요)\n"
    for y in years:
        if year > y:
            m = re.search(rf"^## {y}\s*$", md, flags=re.M)
            if m:
                return md[: m.start()] + f"{hdr}\n(추가 보강 필요)\n\n" + md[m.start() :]
    return md + f"\n\n{hdr}\n(추가 보강 필요)\n"


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
    new_section = section.rstrip() + "\n\n" + block.rstrip() + "\n"
    return "".join(lines[:start]) + new_section + "".join(lines[end:])


def apply_entries(path: Path, entries: Iterable[Entry]) -> int:
    md = read_text(path)
    changed = 0
    for e in sorted(entries, key=lambda x: (x.year, x.url)):
        before = md
        md = insert_under_year(md, e.year, e.block, e.url)
        if md != before:
            changed += 1
    if changed:
        write_text(path, md)
    return changed


def main() -> int:
    if not CONF_PATH.exists():
        return 0
    conf = parse_simple_yml(read_text(CONF_PATH))
    keyword = conf.get("keyword", "고윤정")
    feeds = conf.get("feeds", [])

    seen = load_seen()

    entries: list[Entry] = []

    for feed in feeds:
        url = feed.get("url")
        name = feed.get("name", "feed")
        hint = feed.get("type_hint", "pictorial")
        target = "interviews" if hint == "interview" else "editorial"

        xml_data = fetch(url)
        if not xml_data:
            continue

        try:
            root = ET.fromstring(xml_data)
        except Exception:
            continue

        channel = root.find("channel")
        if channel is None:
            continue

        for item in channel.findall("item")[:20]:
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            if title_el is None or link_el is None:
                continue
            title = clean_title(title_el.text or "")
            link = (link_el.text or "").strip()
            if not link or link in seen:
                continue
            if keyword not in title:
                continue

            date = "(페이지 내 표기 확인 필요)"
            year = datetime.now().year
            if pub_el is not None and pub_el.text:
                try:
                    dt = parsedate_to_datetime(pub_el.text)
                    date = dt.strftime("%Y-%m-%d")
                    year = dt.year
                except Exception:
                    pass

            block = "\n".join(
                [
                    f"- 날짜: {date}",
                    f"- 매체: {name}",
                    "- 구분: 화보/기사(RSS)",
                    f"- 제목: {title}",
                    f"- 링크(원문): {link}",
                    "- 상태: 공식확정",
                    f"- id: {link}",
                ]
            )
            entries.append(Entry(year=year, block=block, url=link, target=target))
            time.sleep(0.05)

    # Split by target
    editorial_entries = [e for e in entries if e.target == "editorial"]
    interview_entries = [e for e in entries if e.target == "interviews"]

    ch = 0
    if editorial_entries:
        ch += apply_entries(EDITORIAL_MD, editorial_entries)
    if interview_entries:
        ch += apply_entries(INTERVIEWS_MD, interview_entries)

    print(f"auto_collect_magazine_rss: entries={len(entries)} changed={ch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

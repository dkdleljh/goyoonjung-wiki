#!/usr/bin/env python3
"""Collect link-only articles using verified official searches and RSS feeds.

- Reads config/magazine-rss.yml
- Fetches configured public search results or RSS, validating each response
- De-dupes against the destination Markdown before each durable write
- Lands link-only entries into:
  - pages/pictorials/editorial.md (default)
  - pages/interviews.md (when type_hint is interview)

No article text is copied.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from source_transport import SourceError, atomic_write, request, save_report

BASE = Path(__file__).resolve().parent.parent
CONF_PATH = BASE / "config" / "magazine-rss.yml"
EDITORIAL_MD = BASE / "pages" / "pictorials" / "editorial.md"
INTERVIEWS_MD = BASE / "pages" / "interviews.md"



@dataclass(frozen=True)
class Entry:
    year: int | None
    block: str
    url: str
    target: str  # 'editorial' | 'interviews'


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    atomic_write(path, content)


def fetch(url: str) -> bytes:
    return request(url)


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
    if year is None:
        return md if "## 날짜 미상" in md else md + "\n\n## 날짜 미상\n"
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
    hdr = f"## {year}" if year is not None else "## 날짜 미상"
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
    for e in sorted(entries, key=lambda x: (x.year or 0, x.url)):
        before = md
        md = insert_under_year(md, e.year, e.block, e.url)
        if md != before:
            changed += 1
    if changed:
        write_text(path, md)
    return changed


def parse_rss(data: bytes) -> tuple[list[dict], list[str]]:
    if not data:
        raise SourceError("No response", "network", True)
    warnings = []
    # Vogue emits media:thumbnail without declaring the standard media namespace.
    # Repair only that declaration; other malformed XML remains a failure.
    if b"media:thumbnail" in data and b"xmlns:media=" not in data:
        data = re.sub(rb"<rss(?=[\s>])", b'<rss xmlns:media="http://search.yahoo.com/mrss/"', data, count=1)
        warnings.append("RSS media namespace declaration repaired")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise SourceError(f"Invalid RSS XML: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None:
        raise SourceError("Expected RSS channel; got HTML or unsupported feed")
    rows = []
    for item in channel.findall("item"):
        title, link = item.findtext("title"), item.findtext("link")
        if not title or not link:
            raise SourceError("RSS item missing title or link")
        rows.append({"title": title, "url": link, "date": item.findtext("pubDate", "")})
    return rows, warnings


def parse_hll(data: bytes) -> list[dict]:
    soup = BeautifulSoup(data.decode("utf-8"), "html.parser")
    container = soup.select_one(".atc_list")
    if container is None:
        # Only an explicit empty-result component may count as no new articles.
        if soup.select_one(".no_data, .nodata") and "검색" in soup.get_text():
            return []
        raise SourceError("Search result structure missing (.atc_list)")
    rows = []
    for a in container.select('a[href^="/article/"]'):
        title = a.select_one(".tit")
        if title is None:
            raise SourceError("Article title missing from search result")
        rows.append({"title": title.get_text("", strip=True), "url": a["href"], "date": ""})
    if not rows:
        raise SourceError("Search result container has no article links")
    return rows


def collect_feed(feed: dict, keyword: str) -> tuple[list[dict], dict]:
    url = feed["url"]
    mode = feed.get("mode", "rss")
    page = int(feed.get("page", 1))
    report = {"name": feed["name"], "url": url, "scope": feed.get("scope", "keyword_search"), "status": "failed"}
    try:
        warnings = []
        if mode == "rss":
            rows, warnings = parse_rss(fetch(url + (("&" if "?" in url else "?") + f"paged={page}" if page > 1 else "")))
        elif mode == "hll_search":
            rows = parse_hll(request(url, method="POST", json={"page": page, "id": "artnews", "keyword": keyword, "sortOption": "latest"}))
        elif mode == "wp_search":
            payload = json.loads(request(url, method="POST", data={"action": "get_search_custom", "posts_per_page": 20,
                              "post_type": "post", "paged": page, "query[s]": keyword}))
            if not isinstance(payload, dict) or "count_posts" not in payload or not isinstance(payload.get("current_posts"), list):
                raise SourceError("Invalid magazine search response")
            if page == 1 and int(payload["count_posts"]) > 0 and not payload["current_posts"]:
                raise SourceError("Search reports articles but returned none")
            rows = [{"title": r["post_title"], "url": r["permalink"], "date": r.get("post_date", "")} for r in payload["current_posts"]]
        elif mode == "singles_search":
            payload = json.loads(request(url, params={"q": keyword, "offset": (page - 1) * 25, "limit": 25}))
            if not isinstance(payload, dict) or payload.get("success") is not True or not isinstance(payload.get("articles"), list):
                raise SourceError("Invalid Singles search response")
            if page == 1 and payload.get("total", 0) > 0 and not payload["articles"]:
                raise SourceError("Search reports articles but returned none")
            rows = [{"title": r["title"], "url": r["link"], "date": r.get("publishedAt", "")} for r in payload["articles"]]
        else:
            raise SourceError(f"Unknown source mode: {mode}", "config")
        matched = []
        host = urlsplit(url).hostname.removeprefix("www.")
        for row in rows:
            row["title"] = clean_title(BeautifulSoup(row["title"], "html.parser").get_text())
            row["url"] = urljoin(url, row["url"].strip())
            parsed = urlsplit(row["url"])
            if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").removeprefix("www.") != host:
                raise SourceError("Article link is outside the configured official source")
            if keyword in row["title"]:
                matched.append(row)
        report.update(status="success", fetched=len(rows), matched=len(matched), warnings=warnings,
                      page=page, page_fingerprint=__import__("hashlib").sha256("|".join(row["url"] for row in rows).encode()).hexdigest())
        return matched, report
    except (SourceError, ValueError, KeyError, TypeError, AttributeError) as exc:
        report.update(error=str(exc), kind=getattr(exc, "kind", "parse"), retryable=getattr(exc, "retryable", False))
        return [], report


def make_entry(row: dict, feed: dict) -> Entry:
    date = "(페이지 내 표기 확인 필요)"
    year = None
    stamp = row.get("date", "")
    if stamp:
        try:
            dt = datetime.strptime(stamp[:10].replace(".", "-"), "%Y-%m-%d") if re.match(r"^\d{4}[-.]", stamp) else parsedate_to_datetime(stamp)
            date, year = dt.strftime("%Y-%m-%d"), dt.year
        except (ValueError, TypeError):
            pass
    title = row["title"].replace("\n", " ")
    link = row["url"]
    target = "interviews" if feed.get("type_hint") == "interview" else "editorial"
    block = "\n".join([f"- 날짜: {date}", f"- 매체: {feed['name']}", "- 구분: 화보/기사(공식 출처)",
                         f"- 제목: {title}", f"- 링크(원문): {link}", "- 상태: 원문 메타데이터 수집", f"- id: {link}"])
    return Entry(year, block, link, target)


def main(check: bool = False) -> int:
    if not CONF_PATH.exists():
        print(f"Missing configuration: {CONF_PATH}")
        return 1
    conf = parse_simple_yml(read_text(CONF_PATH))
    feeds, keyword = conf.get("feeds", []), conf.get("keyword", "고윤정")
    if not feeds:
        print("No magazine sources configured")
        return 1
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda feed: collect_feed(feed, keyword), feeds))
    reports = [report for _, report in results]
    if check:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        entries = [make_entry(row, feed) for feed, (rows, _) in zip(feeds, results, strict=True) for row in rows]
        changed = sum(apply_entries(path, [e for e in entries if e.target == target]) for target, path in
                      [("editorial", EDITORIAL_MD), ("interviews", INTERVIEWS_MD)])
        save_report("magazines", reports)
        print(f"auto_collect_magazine_rss: entries={len(entries)} changed={changed}")
    errors = sum(r["status"] != "success" for r in reports)
    print(f"source_errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fetch and parse all sources without writing content or reports")
    sys.exit(main(check=parser.parse_args().check))

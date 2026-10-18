#!/usr/bin/env python3
"""Link health check for markdown repository.

- Extracts URLs from pages/ and sources/
- Performs lightweight HEAD/GET checks (conservative timeouts)
- Writes pages/link-health.md
- Optional: tag 404 URLs in-place with an HTML comment (self-healing)

Design goals:
- Never hang the unmanned pipeline
- Prefer false-warn over false-bad
- Skip very heavy/blocked domains by default
"""

from __future__ import annotations

import json
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE / "pages"
SOURCES_DIR = BASE / "sources"
OUT = PAGES_DIR / "link-health.md"

TIMEOUT = 8
MAX_URLS = int(__import__("os").environ.get("MAX_URLS", "250"))  # keep bounded for unmanned runs
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")

SKIP_DOMAINS = (
    # Social / heavy JS
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",


)




@dataclass(frozen=True)
class Result:
    url: str
    status: str  # ok|warn|bad|unchecked
    code: int | None
    note: str = ""


def iter_md_files():
    for root in (PAGES_DIR, SOURCES_DIR):
        if not root.exists():
            continue
        yield from (p for p in sorted(root.rglob("*.md")) if p != OUT and p.name not in {"alternative-proof-candidates.md", "skipped-link-backlog.md"})


def normalize_extracted_url(url: str) -> str:
    """Normalize raw extracted URLs.

    Problem:
    - In markdown, URLs are often followed by punctuation (comma, middle dot, etc.).
      Our regex intentionally stays permissive, which can accidentally include
      trailing punctuation or an encoded comma (%2C).

    We only apply conservative, end-of-token cleanup.
    """

    u = url.strip()

    # Common trailing punctuation in our markdown style.
    u = u.rstrip(".,;:·")

    # Remove trailing literal commas.
    while u.endswith(","):
        u = u[:-1]

    # Remove trailing encoded commas (often extracted when a URL is followed by ',').
    while u.lower().endswith("%2c"):
        u = u[:-3]

    # Remove accidental path segments like '/%2C' or '/%2C%2C'.
    u = re.sub(r"/%2c(?:%2c)*$", "", u, flags=re.I)

    return u


def extract_urls(text: str) -> list[str]:
    return [normalize_extracted_url(u) for u in URL_RE.findall(text)]


def safe_url(url: str) -> str:
    """Percent-encode unsafe characters so urllib won't crash on non-ASCII URLs."""
    try:
        parts = urlsplit(url)
        # Keep scheme/netloc as-is, encode path/query/fragment conservatively.
        path = quote(parts.path, safe="/%:@")
        query = quote(parts.query, safe="=&?/%:@+")
        frag = quote(parts.fragment, safe="")
        return urlunsplit((parts.scheme, parts.netloc, path, query, frag))
    except Exception:
        return url


def fetch_status(url: str) -> Result:
    original = url
    parts = urlsplit(url)
    host = (parts.hostname or '').removeprefix('www.')
    if host in {'youtube.com', 'youtu.be'}:
        video = parts.path.lstrip('/') if host == 'youtu.be' else parse_qs(parts.query).get('v', [''])[0]
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
            try:
                endpoint = 'https://www.youtube.com/oembed?format=json&url='+quote('https://www.youtube.com/watch?v='+video, safe='')
                with urlopen(Request(endpoint, headers={'User-Agent':UA}), timeout=TIMEOUT) as response:
                    data = json.load(response)
                if data.get('title') and data.get('author_url'):
                    return Result(original, 'ok', 200, 'Public video metadata and author returned')
                return Result(original, 'warn', None, 'Video metadata incomplete')
            except Exception as exc:
                return Result(original, 'warn', None, 'Video metadata unavailable: '+type(exc).__name__)
    url = safe_url(url)
    # Prefer HEAD, fallback to GET
    try:
        req = Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, "status", None) or 200
            if 200 <= code < 400:
                destination = resp.geturl()
                if isinstance(destination, str) and urlsplit(url).path not in {'', '/'} and urlsplit(destination).path in {'', '/'}:
                    return Result(url=url, status="warn", code=code, note="Article redirected to homepage")
                return Result(url=url, status="ok", code=code, note="HTTP reachable; factual identity not verified")
            if code in {404, 410}:
                return Result(url=url, status="bad", code=code)
            return Result(url=url, status="warn", code=code)
    except Exception:
        pass

    try:
        req = Request(url, headers={"User-Agent": UA}, method="GET")
        with urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, "status", None) or 200
            if 200 <= code < 400:
                return Result(url=url, status="ok", code=code, note="GET fallback")
            if code in {404, 410}:
                return Result(url=url, status="bad", code=code, note="GET fallback")
            return Result(url=url, status="warn", code=code, note="GET fallback")
    except HTTPError as e:
        return Result(url=url, status="bad" if e.code in {404, 410} and "/feeds/videos.xml" not in url else "warn", code=e.code, note="RSS endpoint unavailable; collector has channel-verified uploads fallback" if "/feeds/videos.xml" in url else "GET fallback")
    except Exception as e:
        return Result(url=url, status="warn", code=None, note=f"error: {type(e).__name__}")


def heal_tag_404(path: Path, url: str) -> None:
    """Append a hidden HTML comment tag to a raw URL occurrence (best-effort)."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return

    if url not in content:
        return

    # If already tagged (any date), do nothing.
    if re.search(re.escape(url) + r"\s*<!--\s*Broken/404:", content):
        return

    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    tag = f" <!-- Broken/404: {today} -->"

    # Place annotations outside Markdown destinations and never alter stable IDs.
    new_content = "\n".join(
        line + tag if url in line and "Broken/404:" not in line and not line.lstrip().startswith("- id:") else line
        for line in content.split("\n")
    )
    if new_content != content:
        try:
            path.write_text(new_content, encoding="utf-8")
        except Exception:
            return


def write_report(results: list[Result], checked: int) -> None:
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
    ok = [r for r in results if r.status == "ok"]
    warn = [r for r in results if r.status == "warn"]
    bad = [r for r in results if r.status == "bad"]
    unchecked = [r for r in results if r.status == "unchecked"]

    lines: list[str] = []
    lines.append("# 링크 건강검진")
    lines.append("")
    lines.append(f"> 갱신: {now} (Asia/Seoul) · 대상 URL: {checked} (최대 {MAX_URLS})")
    lines.append("")
    lines.append(f"- OK: **{len(ok)}** / WARN: **{len(warn)}** / BAD: **{len(bad)}** / UNCHECKED: **{len(unchecked)}**")
    lines.append("- 검사 범위 밖 URL과 자동 접근을 생략한 URL은 정상으로 간주하지 않습니다.")
    lines.append("")

    def render(title: str, arr: list[Result]):
        lines.append(f"## {title}")
        lines.append("")
        if not arr:
            lines.append("- 없음")
            lines.append("")
            return
        for r in arr[:200]:
            code = r.code if r.code is not None else "-"
            note = f" · {r.note}" if r.note else ""
            lines.append(f"- ({code}) {r.url}{note}")
        lines.append("")

    render("BAD (수정/교체 권장 — 404는 자동 태깅됨)", bad)
    render("WARN (차단/리다이렉트/확인 필요)", warn)
    render("UNCHECKED (미검사)", unchecked)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    socket.setdefaulttimeout(TIMEOUT)

    url_to_paths: dict[str, set[Path]] = {}
    seen: set[str] = set()
    urls: list[str] = []

    for p in iter_md_files():
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for u in extract_urls(text):
            url_to_paths.setdefault(u, set()).add(p)
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)

    results: list[Result] = []

    cache_path = BASE / 'data/reports/link-checkpoints.json'
    try:
        cache = json.loads(cache_path.read_text())
    except (OSError, ValueError):
        cache = {}
    eligible = []
    for u in urls:
        host = urlsplit(u).hostname or ''
        if any(host == d or host.endswith('.'+d) for d in SKIP_DOMAINS):
            results.append(Result(u, 'unchecked', None, 'social platform requires source-specific verification'))
        else:
            eligible.append(u)
    probe_urls = sorted(eligible, key=lambda u: cache.get(u, {}).get('checked_at', 0))[:MAX_URLS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for u, res in zip(probe_urls, pool.map(fetch_status, probe_urls), strict=True):
            results.append(res)
            cache[u] = {**asdict(res), 'checked_at': time.time()}
            if res.status == 'bad' and res.code == 404:
                for p in url_to_paths.get(u, set()):
                    heal_tag_404(p, u)
    for u in set(eligible) - set(probe_urls):
        old = cache.get(u)
        if old and time.time() - old['checked_at'] < 7 * 86400:
            results.append(Result(u, old['status'], old['code'], old['note'] + ' (cached within 7 days)'))
        else:
            results.append(Result(u, 'unchecked', None, 'awaiting rotating check'))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    from source_transport import atomic_write
    atomic_write(cache_path, json.dumps({u:v for u,v in cache.items() if u in seen}, ensure_ascii=False, indent=2)+'\n')

    write_report(results, checked=len(urls))
    ok_n = sum(r.status == 'ok' for r in results)
    warn_n = sum(r.status == 'warn' for r in results)
    bad_n = sum(r.status == 'bad' for r in results)
    print(f"check_links: urls={len(urls)} ok={ok_n} warn={warn_n} bad={bad_n}")
    return 1 if bad_n else 0


if __name__ == "__main__":
    sys.exit(main())

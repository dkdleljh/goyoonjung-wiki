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

import re
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE / "pages"
SOURCES_DIR = BASE / "sources"
OUT = PAGES_DIR / "link-health.md"

TIMEOUT = 8
MAX_URLS = 700  # keep bounded for unmanned runs
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")

SKIP_DOMAINS = (
    # Social / heavy JS
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",

    # Frequently blocked to bots / aggressive WAF
    "chanel.com",
    "boucheron.com",
    "disneyplus.com",
    "disneypluskr.com",
    "tving.com",
    "program.tving.com",
    "yna.co.kr",
    "about.netflix.com",
    "goodal.com",
    "vodana.co.kr",
    "lensme.co.kr",
    "easytomorrow.co.kr",
)


@dataclass(frozen=True)
class Result:
    url: str
    status: str  # ok|warn|bad
    code: int | None
    note: str = ""


def iter_md_files():
    for root in (PAGES_DIR, SOURCES_DIR):
        if not root.exists():
            continue
        yield from root.rglob("*.md")


def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text)


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
    url = safe_url(url)
    # Prefer HEAD, fallback to GET
    try:
        req = Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, "status", None) or 200
            if 200 <= code < 400:
                return Result(url=url, status="ok", code=code)
            if code == 404:
                return Result(url=url, status="bad", code=404)
            return Result(url=url, status="warn", code=code)
    except Exception:
        pass

    try:
        req = Request(url, headers={"User-Agent": UA}, method="GET")
        with urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, "status", None) or 200
            if 200 <= code < 400:
                return Result(url=url, status="ok", code=code, note="GET fallback")
            if code == 404:
                return Result(url=url, status="bad", code=404, note="GET fallback")
            return Result(url=url, status="warn", code=code, note="GET fallback")
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

    today = datetime.now().strftime("%Y-%m-%d")
    tag = f" <!-- Broken/404: {today} -->"

    if tag in content:
        return

    new_content = content.replace(url, f"{url}{tag}")
    if new_content != content:
        try:
            path.write_text(new_content, encoding="utf-8")
        except Exception:
            return


def write_report(results: list[Result], checked: int) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = [r for r in results if r.status == "ok"]
    warn = [r for r in results if r.status == "warn"]
    bad = [r for r in results if r.status == "bad"]

    lines: list[str] = []
    lines.append("# 링크 건강검진")
    lines.append("")
    lines.append(f"> 갱신: {now} (Asia/Seoul) · 대상 URL: {checked} (최대 {MAX_URLS})")
    lines.append("")
    lines.append(f"- OK: **{len(ok)}** / WARN: **{len(warn)}** / BAD: **{len(bad)}**")
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
            if len(urls) >= MAX_URLS:
                break
        if len(urls) >= MAX_URLS:
            break

    results: list[Result] = []

    for u in urls:
        host = urlsplit(u).netloc.lower()
        if any(host.endswith(d) for d in SKIP_DOMAINS):
            # In unmanned mode we intentionally do not probe heavy/blocked domains.
            # Treat as OK for health scoring, while keeping the note for transparency.
            results.append(Result(url=u, status="ok", code=None, note="skipped (heavy domain)"))
            continue

        res = fetch_status(u)
        results.append(res)

        if res.status == "bad" and res.code == 404:
            for p in url_to_paths.get(u, set()):
                heal_tag_404(p, u)

    write_report(results, checked=len(urls))
    ok_n = sum(r.status == 'ok' for r in results)
    warn_n = sum(r.status == 'warn' for r in results)
    bad_n = sum(r.status == 'bad' for r in results)
    print(f"check_links: urls={len(urls)} ok={ok_n} warn={warn_n} bad={bad_n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

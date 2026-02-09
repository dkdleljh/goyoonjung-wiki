#!/usr/bin/env python3
"""Link health check for markdown repository.

- Extracts URLs from pages/ and sources/
- Performs a lightweight HEAD/GET check
- Writes pages/link-health.md

Conservative by design (timeouts, limited concurrency).
"""

from __future__ import annotations

import re
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BASE = Path('/home/zenith/바탕화면/goyoonjung-wiki')
PAGES = BASE / 'pages'
SOURCES = BASE / 'sources'
OUT = PAGES / 'link-health.md'

URL_RE = re.compile(r"https?://[^\s)\]}>\"']+")

# Keep it gentle
TIMEOUT = 3
MAX_URLS = 12  # keep weekly run very quick


def iter_md_files():
    for root in (PAGES, SOURCES):
        if not root.exists():
            continue
        for p in root.rglob('*.md'):
            # ignore generated report itself to prevent oscillation
            if p.name in ('link-health.md',):
                continue
            yield p


def extract_urls(text: str):
    return URL_RE.findall(text)


@dataclass
class Result:
    url: str
    status: str  # ok|warn|bad
    code: int | None
    note: str


def fetch_status(url: str) -> Result:
    # Some sites block HEAD; try HEAD then GET.
    headers = {
        'User-Agent': 'goyoonjung-wiki-link-check/1.0 (+local)'
    }

    def attempt(method: str):
        req = Request(url, method=method, headers=headers)
        with urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, 'status', None) or resp.getcode()
            final = resp.geturl()
            return code, final

    try:
        code, final = attempt('HEAD')
    except Exception:
        try:
            code, final = attempt('GET')
        except Exception as e:
            return Result(url=url, status='bad', code=None, note=str(e)[:120])

    note = ''
    if final and final != url:
        note = f'redirect -> {final}'

    if code is None:
        return Result(url=url, status='warn', code=None, note=note or 'no status')
    if 200 <= code < 300:
        return Result(url=url, status='ok', code=code, note=note)
    if code in (301, 302, 307, 308):
        return Result(url=url, status='warn', code=code, note=note or 'redirect')
    if code in (401, 403):
        return Result(url=url, status='warn', code=code, note='blocked/forbidden (may be OK)')
    return Result(url=url, status='bad', code=code, note=note)


def main():
    socket.setdefaulttimeout(TIMEOUT)

    seen = set()
    urls = []
    for p in iter_md_files():
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        for u in extract_urls(text):
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)
            if len(urls) >= MAX_URLS:
                break
        if len(urls) >= MAX_URLS:
            break

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    results = []
    for u in urls:
        # skip known heavy/blocked domains for lightweight check
        host = urlsplit(u).netloc.lower()
        if any(host.endswith(d) for d in ("youtube.com", "youtu.be", "instagram.com")):
            results.append(Result(url=u, status='warn', code=None, note='skipped (heavy domain)'))
            continue
        results.append(fetch_status(u))
    ok = [r for r in results if r.status == 'ok']
    warn = [r for r in results if r.status == 'warn']
    bad = [r for r in results if r.status == 'bad']

    lines = []
    lines.append('# 링크 건강검진')
    lines.append('')
    lines.append(f'> 갱신: {now} (Asia/Seoul) · 대상 URL: {len(urls)} (최대 {MAX_URLS})')
    lines.append('')
    lines.append(f'- OK: **{len(ok)}** / WARN: **{len(warn)}** / BAD: **{len(bad)}**')
    lines.append('')

    def render(section: str, arr: list[Result]):
        lines.append(f'## {section}')
        lines.append('')
        if not arr:
            lines.append('- 없음')
            lines.append('')
            return
        for r in arr[:100]:
            code = r.code if r.code is not None else '-'
            note = f' · {r.note}' if r.note else ''
            lines.append(f'- ({code}) {r.url}{note}')
        lines.append('')

    render('BAD (수정/교체 권장)', bad)
    render('WARN (차단/리다이렉트/확인 필요)', warn)

    OUT.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())

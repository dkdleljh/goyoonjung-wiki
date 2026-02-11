#!/usr/bin/env python3
"""Link health check for markdown repository.

- Extracts URLs from pages/ and sources/
- Performs a lightweight HEAD/GET check
- Writes pages/link-health.md

Conservative by design (timeouts, limited concurrency).
"""

from __future__ import annotations

import os
import re
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / 'pages'
    try:
        content = path.read_text(encoding='utf-8')
        if url not in content: return
        
        # Simple string replacement: url -> url (Broken: YYYY-MM-DD)
        # Prevent double tagging
        today = datetime.now().strftime('%Y-%m-%d')
        tag = f" <!-- Broken/404: {today} -->"
        
        # Regex to match URL not already followed by tag
        # We just replace the raw URL string with URL+Tag for simplicity in this MVP
        # But we must be careful about partial matches. 
        # For safety/unmanned goals, we will append a comment tag which Markdown hides but search sees.
        
        if tag in content: # duplicate check
            return 
            
        new_content = content.replace(url, f"{url}{tag}")
        if new_content != content:
            path.write_text(new_content, encoding='utf-8')
            print(f"Healed(Tagged): {url} in {path.name}")
            
    except Exception as e:
        print(f"Failed to heal {path}: {e}")

def write_report(text: str) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(f"{OUT.suffix}.tmp")
    tmp.write_text(text, encoding='utf-8')
    os.replace(tmp, OUT)


def main() -> int:
    socket.setdefaulttimeout(TIMEOUT)

    # Dictionary to map URL back to File Paths for healing
    url_map = {} # url -> set(Path)

    seen = set()
    urls = []
    for p in iter_md_files():
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        extracted = extract_urls(text)
        for u in extracted:
            if u not in url_map:
                url_map[u] = set()
            url_map[u].add(p)
            
            if u in seen:
                continue
            seen.add(u)
            urls.append(u)
            if len(urls) >= MAX_URLS: # Hard limit for daily/unmanned speed
                break
        if len(urls) >= MAX_URLS:
            break

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # ... (checking logic same as before) ...
    results = []
    for u in urls:
        # skip known heavy/blocked domains
        host = urlsplit(u).netloc.lower()
        if any(host.endswith(d) for d in ("youtube.com", "youtu.be", "instagram.com")):
            results.append(Result(url=u, status='warn', code=None, note='skipped (heavy domain)'))
            continue
        res = fetch_status(u)
        results.append(res)
        
        # SELF-HEALING Logic
        if res.status == 'bad' and res.code == 404:
            # Tag the files
            paths = url_map.get(u, [])
            for p in paths:
                heal_link_in_file(p, u, 404)

    # ... (reporting logic) ...
    ok = [r for r in results if r.status == 'ok']
    warn = [r for r in results if r.status == 'warn']
    bad = [r for r in results if r.status == 'bad']

    lines = []
    lines.append('# 링크 건강검진 (Self-Healing Enabled)')
    lines.append('')
    lines.append(f'> 갱신: {now} (Asia/Seoul) · 대상 URL: {len(urls)} (최대 {MAX_URLS})')
    lines.append('')
    lines.append(f'- OK: **{len(ok)}** / WARN: **{len(warn)}** / BAD: **{len(bad)}**')
    lines.append('')
    
    # ...
    
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

    render('BAD (수정/교체 권장 - 404는 자동 태깅됨)', bad)
    render('WARN (차단/리다이렉트/확인 필요)', warn)

    report = '\n'.join(lines).rstrip() + '\n'
    try:
        write_report(report)
    except Exception as e:
        print(
            f"ERR: failed to write report: path={OUT} reason={e}",
            file=sys.stderr,
        )
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

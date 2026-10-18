#!/usr/bin/env python3
"""Monitor the configured official profile; preserve outages and parsing failures."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from agency_policy import load_config
from bs4 import BeautifulSoup
from collector_io import append_news_lines
from source_transport import SourceError, request, save_report

BASE = Path(__file__).resolve().parent.parent
CONF_PATH = BASE / 'config/agency-sources.json'
MAA_URL = 'https://maa.co.kr/artists/go-younjung'


def fetch_html(url: str = MAA_URL) -> str:
    return request(url).decode('utf-8')


def extract_works(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer']):
        tag.decompose()
    text = soup.get_text(' ', strip=True)
    if not re.search(r'고윤정|GO\s*YOUN[ -]?JUNG', text, re.I):
        raise SourceError('Expected actor identity missing; refused generic/error page')
    # Parse the actual section text, not newline formatting or platform names.
    # Movie credits often have no platform name at all.
    sections = re.split(r'\b(Drama(?:\s*\(pending release\))?|Film|Awards|AD|Advertising|Music Video)\b', text, flags=re.I)
    works = []
    for index in range(1, len(sections) - 1, 2):
        if not re.match(r'^(Drama|Film)', sections[index], re.I):
            continue
        for item in re.split(r'(?=\b(?:19|20)\d{2}\b)', sections[index + 1]):
            item = ' '.join(item.split()).strip(' ,;')
            if re.match(r'^(?:19|20)\d{2}\b', item) and len(item) > 8:
                works.append(item)
    return list(dict.fromkeys(works))


def main(check: bool = False) -> int:
    config = load_config(CONF_PATH)
    urls = config['urls']
    if not urls:
        raise SourceError('No agency source configured', 'config')
    report = {'name': config['name'], 'url': urls[0], 'scope': 'configured_agency_profile', 'status': 'failed'}
    if config.get('lifecycle') == 'retired':
        report.update(status='retired', scope='historical_profile', reason=config['reason'],
                      evidence=config['evidence'], retired_at=config['retired_at'])
        if check:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            save_report('agency', [report])
        return 0
    failures = []
    for url in urls:
        try:
            print(f'Fetching official profile: {url}', flush=True)
            works = extract_works(fetch_html(url))
            if not works:
                raise SourceError('Actor page has no recognized Drama/Film credits; parser needs review')
            report.update(status='success', url=url, fetched=len(works), matched=len(works), warnings=failures)
            if not check:
                today = datetime.now().strftime('%Y-%m-%d')
                append_news_lines(BASE / 'news' / f'{today}.md', [
                    f"- [Agency] [{config['name']}]({url}) 작품 목록 확인: {len(works)}건 (변동 확인용)"
                ])
            break
        except (SourceError, UnicodeError) as exc:
            failures.append(f'{url}: {exc}')
            report.update(error='; '.join(failures), kind=getattr(exc, 'kind', 'parse'),
                          retryable=getattr(exc, 'retryable', False))
    if report['status'] == 'success':
        for key in ('error', 'kind', 'retryable'):
            report.pop(key, None)
    if check:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        save_report('agency', [report])
    return 0 if report['status'] == 'success' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fetch/parse only; do not write news or reports')
    raise SystemExit(main(check=parser.parse_args().check))

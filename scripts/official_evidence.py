"""Fetch first-party announcements and validate claim-level evidence.

Only metadata, short evidence excerpts and hashes are persisted. Search results
are discovery hints; they cannot confirm a claim without the original page.
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from google_news_resolver import resolve as decode_google_news_url
from source_schedule import record, search_window
from source_transport import atomic_write, request, save_report

BASE = Path(__file__).resolve().parents[1]
CONFIG = BASE / 'config/official-sources.json'
EVIDENCE = BASE / 'data/facts/evidence.json'
ACTOR = re.compile(r'고윤정|go[\s-]*you[n]?g?[\s-]*jung|go[\s-]*yoon[\s-]*jung|ko[\s-]*yoon[\s-]*jung|コ[・\s]?ユンジョン|高允贞|高允貞', re.I)


def load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def host(url: str) -> str:
    return (urlsplit(url).hostname or '').removeprefix('www.')


def same_source(url: str, domain: str) -> bool:
    return urlsplit(url).scheme == 'https' and (host(url) == domain or host(url).endswith('.'+domain))


def nodes(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from nodes(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from nodes(value)


def parse_document(content: str, url: str, source: dict) -> dict:
    soup = BeautifulSoup(content, 'html.parser')
    structured = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            structured.extend(nodes(json.loads(script.string or script.get_text())))
        except ValueError:
            continue
    def meta(key):
        tag = soup.find('meta', property=key) or soup.find('meta', attrs={'name': key})
        return tag.get('content', '') if tag else ''
    title = meta('og:title') or (soup.title.get_text(' ', strip=True) if soup.title else '')
    description = meta('og:description') or meta('description')
    article = soup.find('article') or soup.find('main') or soup.body or soup
    for tag in article.select('script,style,nav,footer,header'):
        tag.decompose()
    text = article.get_text(' ', strip=True)
    if not title or re.search(r'access denied|just a moment|페이지를 찾을 수|404 not found', title, re.I):
        raise ValueError('Error/soft-404 page is not evidence')
    actor = ACTOR.search(title+' '+description+' '+text)
    claims = []
    # Machine-readable cast credit: require an explicit actor relationship.
    for node in structured:
        types = node.get('@type', [])
        types = types if isinstance(types, list) else [types]
        if not set(types) & {'Movie', 'TVSeries', 'TVSeason'}:
            continue
        cast = node.get('actor', node.get('actors', []))
        if not ACTOR.search(json.dumps(cast, ensure_ascii=False)):
            continue
        name = str(node.get('name', '')).strip()
        if name and len(name) <= 100:
            claims.append({'entity': name, 'field': 'cast', 'value': '고윤정', 'method': 'schema_actor'})
            date = str(node.get('datePublished', ''))
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                try:
                    datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    continue
                claims.append({'entity': name, 'field': 'release_date', 'value': date, 'method': 'schema_release'})
    # A bounded sentence, not an entire page with unrelated sidebar mentions.
    for sentence in re.split(r'(?<=[.!?。])\s+|\n', title+'\n'+description):
        if not ACTOR.search(sentence) or len(sentence) > 500:
            continue
        if re.search(r'검토|논의|루머|미확정|불발|취소|부인', sentence):
            continue
        match = re.search(r'[《〈「『\'“‘<]([^》〉」』\'”’>]{2,80})[》〉」』\'”’>]', sentence)
        quoted = re.findall(r'[《〈「『\'“‘<]([^》〉」』\'”’>]{2,80})[》〉」』\'”’>]', sentence)
        if match and len(set(quoted)) == 1 and re.search(r'출연(?:을)?\s*확정|캐스팅(?:을)?\s*확정|출연한다|캐스팅했다', sentence):
            claims.append({'entity': match[1], 'field': 'cast', 'value': '고윤정', 'method': 'explicit_announcement'})
    now = datetime.now(UTC).isoformat()
    return {'id': hashlib.sha256(url.encode()).hexdigest()[:24], 'url': url, 'publisher': source['domain'],
            'category': source['category'], 'first_party': source.get('first_party', False),
            'title': title[:250], 'published_at': meta('article:published_time') or None,
            'collected_at': now, 'content_hash': hashlib.sha256(content.encode()).hexdigest(),
            'excerpt': description[:160], 'actor_mentioned': bool(actor),
            'claims': claims if source.get('first_party') else [], 'status': 'fetched'}


def fetch_document(url: str, source: dict, previous: dict | None = None) -> dict:
    if not same_source(url, source['domain']):
        raise ValueError('Discovery URL does not belong to configured publisher')
    headers = {'User-Agent': 'goyoonjung-wiki/2.0 (public evidence monitor)'}
    previous = previous or {}
    for field, header in [('etag', 'If-None-Match'), ('last_modified', 'If-Modified-Since')]:
        if previous.get(field):
            headers[header] = previous[field]
    with requests.get(url, headers=headers, timeout=(5, 15), allow_redirects=True) as response:
        if not same_source(response.url, source['domain']):
            raise ValueError('Redirect left configured publisher')
        if urlsplit(url).path not in {'', '/'} and urlsplit(response.url).path in {'', '/'}:
            raise ValueError('Article redirected to homepage')
        if response.status_code == 304 and previous:
            return {**previous, 'collected_at': datetime.now(UTC).isoformat()}
        response.raise_for_status()
        result = parse_document(response.text, response.url, source)
        result.update(etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'),
                      first_seen=previous.get('first_seen', previous.get('collected_at', result['collected_at'])))
        return result


def main() -> int:
    all_sources = load(CONFIG, [])
    evidence = {r['url']: r for r in load(EVIDENCE, [])}
    sources = all_sources
    reports = []
    snapshot = dict(evidence)
    def collect_one(source):
        evidence = dict(snapshot)
        updates = {}
        key = 'official:'+source['domain']
        report = {'name': source['name'], 'url': source['url'], 'scope': 'official search + original page', 'status': 'failed'}
        try:
            direct_urls = []
            index_error = None
            try:
                landing = request(source['url'], attempts=1)
                landing_soup = BeautifulSoup(landing, 'html.parser')
                if not landing_soup.title or re.search(r'access denied|just a moment|404', landing_soup.title.get_text(), re.I):
                    raise ValueError('Official index is blocked or invalid')
                for anchor in landing_soup.select('a[href]'):
                    if ACTOR.search(anchor.get_text(' ', strip=True)):
                        target = urljoin(source['url'], anchor['href'])
                        if same_source(target, source['domain']):
                            direct_urls.append(target)
            except Exception as exc:
                index_error = str(exc)[:180]
            query = f'site:{source["domain"]} 고윤정 {search_window(key)}'
            rss = request('https://news.google.com/rss/search?q='+quote_plus(query)+'&hl=ko&gl=KR&ceid=KR:ko')
            root = ET.fromstring(rss)
            if root.find('channel') is None:
                raise ValueError('Not a search RSS response')
            urls = list(source.get('watch_urls', []))[:1] + direct_urls[:4]
            for item in root.findall('./channel/item')[:6]:
                url = decode_google_news_url(item.findtext('link', ''))
                if same_source(url, source['domain']):
                    urls.append(url)
            # Revisit old evidence: corrections and changed announcements matter.
            prior = sorted((r for r in evidence.values() if r['publisher'] == source['domain']), key=lambda r:r['collected_at'])
            urls += [r['url'] for r in prior[:1]]
            fetched = 0
            failures = [f'Index unavailable: {index_error}'] if index_error else []
            for url in dict.fromkeys(urls):
                try:
                    row = fetch_document(url, source, evidence.get(url))
                    if row['actor_mentioned'] or row['claims']:
                        updates[url] = row
                    fetched += 1
                except (requests.RequestException, ValueError) as exc:
                    failures.append(f'{url}: {str(exc)[:100]}')
            report.update(status='failed' if failures else 'success', fetched=fetched, index_checked=index_error is None,
                          matched=len(updates), warnings=failures)
        except Exception as exc:
            report['error'] = str(exc)[:200]
        return source, report, updates
    with ThreadPoolExecutor(max_workers=4) as pool:
        for source, report, updates in pool.map(collect_one, sources):
            evidence.update(updates)
            record('official:'+source['domain'], report['status'] == 'success')
            reports.append(report)
            atomic_write(EVIDENCE, json.dumps(list(evidence.values()), ensure_ascii=False, indent=2)+'\n')
    atomic_write(EVIDENCE, json.dumps(list(evidence.values()), ensure_ascii=False, indent=2)+'\n')
    save_report('official-live', reports)
    return int(any(r['status'] != 'success' for r in reports))


if __name__ == '__main__':
    raise SystemExit(main())

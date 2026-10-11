"""Resolve modern Google News links with bounded requests and a durable cache."""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from googlenewsdecoder import gnews_decoder_async

CACHE = Path(__file__).resolve().parent.parent / '.cache/news-decodes'
MEMORY: dict[str, str] = {}


def is_google(url: str) -> bool:
    return urlsplit(url).hostname == 'news.google.com'


def valid_result(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme in {'http', 'https'} and bool(parsed.hostname) and not is_google(url)


def cache_path(url: str) -> Path:
    return CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.json')


def cached(url: str) -> str | None:
    if url in MEMORY:
        return MEMORY[url]
    try:
        value = json.loads(cache_path(url).read_text())['url']
        if valid_result(value):
            MEMORY[url] = value
            return value
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def warm_cache(urls: list[str]) -> None:
    pending = list(dict.fromkeys(url for url in urls if url and is_google(url) and not cached(url)))
    if not pending:
        return
    try:
        results = asyncio.run(gnews_decoder_async(pending, timeout=8, concurrency=4))
    except Exception:
        # Preserve original links and let callers record the source failure.
        return
    for original, result in zip(pending, results, strict=False):
        resolved = result.get('decoded_url', '')
        if result.get('success') and valid_result(resolved):
            MEMORY[original] = resolved
            CACHE.mkdir(parents=True, exist_ok=True)
            target = cache_path(original)
            temporary = target.with_suffix('.tmp')
            temporary.write_text(json.dumps({'url': resolved}) + '\n')
            temporary.replace(target)
        else:
            MEMORY[original] = original  # Retry failed resolutions in the next process.


def resolve(url: str) -> str:
    if not is_google(url):
        return url
    warm_cache([url])
    return cached(url) or url

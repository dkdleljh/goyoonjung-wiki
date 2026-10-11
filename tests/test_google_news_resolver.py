import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import google_news_resolver as resolver


def test_resolved_links_survive_restart_and_batch_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(resolver, 'CACHE', tmp_path)
    monkeypatch.setattr(resolver, 'MEMORY', {})
    calls = []
    async def decode(urls, **kwargs):
        calls.append(urls)
        return [{'success': True, 'decoded_url': 'https://publisher.example/article'} for url in urls]
    monkeypatch.setattr(resolver, 'gnews_decoder_async', decode)
    url = 'https://news.google.com/rss/articles/test'
    resolver.warm_cache([url, url])
    resolver.MEMORY.clear()
    assert resolver.resolve(url) == 'https://publisher.example/article'
    assert calls == [[url]]


def test_failure_is_retryable_after_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(resolver, 'CACHE', tmp_path)
    monkeypatch.setattr(resolver, 'MEMORY', {})
    calls = []
    async def decode(urls, **kwargs):
        calls.append(urls)
        return [{'success': False, 'message': 'rate limited'}]
    monkeypatch.setattr(resolver, 'gnews_decoder_async', decode)
    url = 'https://news.google.com/rss/articles/test'
    assert resolver.resolve(url) == url
    assert resolver.resolve(url) == url
    assert len(calls) == 1
    resolver.MEMORY.clear()
    resolver.resolve(url)
    assert len(calls) == 2
    assert not list(tmp_path.iterdir())


def test_external_urls_are_unchanged_and_unsafe_results_rejected():
    assert resolver.resolve('https://publisher.example/article') == 'https://publisher.example/article'
    assert not resolver.valid_result('javascript:alert(1)')
    assert not resolver.valid_result('https://news.google.com/articles/id')

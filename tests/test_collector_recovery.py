import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('name', ['google_news_sites', 'google_news_queries', 'google_news_queries_i18n', 'youtube_feeds', 'magazine_rss'])
@pytest.mark.parametrize('broken', [False, True])
def test_feed_failure_is_not_reported_as_empty_success(name, broken, tmp_path, monkeypatch):
    mod = importlib.import_module('scripts.auto_collect_' + name)
    if hasattr(mod, 'save_report'):
        monkeypatch.setattr(mod, 'save_report', lambda *args: None)
    if hasattr(mod, 'db_manager'):
        monkeypatch.setattr(mod.db_manager, 'init_db', lambda: None)
    if hasattr(mod, 'load_sites'):
        monkeypatch.setattr(mod, 'load_sites', lambda: [SimpleNamespace(domain='example.org', label='Test')])
    if hasattr(mod, 'load_queries'):
        query = ('test', '고윤정', 'ko', 'KR', 'KR:ko') if name.endswith('i18n') else ('test', '고윤정')
        monkeypatch.setattr(mod, 'load_queries', lambda: [query])
    if hasattr(mod, 'parse_simple_yml'):
        config = tmp_path / 'feed.yml'
        config.write_text('test')
        monkeypatch.setattr(mod, 'CONF_PATH', config)
        monkeypatch.setattr(mod, 'parse_simple_yml', lambda text: {'feeds': [{'url': 'https://example.org/feed', 'name': 'Test'}]})
    payload = b'<feed xmlns="http://www.w3.org/2005/Atom"/>' if name == 'youtube_feeds' else b'<rss><channel/></rss>'
    monkeypatch.setattr(mod, 'fetch_rss' if hasattr(mod, 'fetch_rss') else 'fetch', lambda url: None if broken else payload)
    assert mod.main() == (1 if broken else 0)


def test_failed_write_does_not_mark_news_seen_and_retry_recovers(tmp_path, monkeypatch):
    import scripts.auto_collect_google_news as mod
    body = '<rss><channel><item><title>고윤정 인터뷰</title><link>https://example.org/news/1</link></item></channel></rss>'
    monkeypatch.setattr(mod, 'fetch_rss', lambda: body.encode())
    monkeypatch.setattr(mod, 'decode_google_news_url', lambda url: url)
    monkeypatch.setattr(mod.relevance, 'is_relevant', lambda *args: True)
    monkeypatch.setattr(mod.domain_policy, 'load_policy', lambda: SimpleNamespace(grade_for_url=lambda url: 'S', lane_for_url=lambda url: 'landed'))
    monkeypatch.setattr(mod.db_manager, 'is_url_seen', lambda url: False)
    monkeypatch.setattr(mod.db_manager, 'record_url_event', lambda *args, **kwargs: None)
    seen = []
    monkeypatch.setattr(mod.db_manager, 'add_seen_url', lambda url, **kwargs: seen.append(url))
    target = tmp_path / 'news/day.md'
    monkeypatch.setattr(mod, 'get_today_news_path', lambda: str(target))
    original = mod.append_news_lines
    monkeypatch.setattr(mod, 'append_news_lines', lambda *args: (_ for _ in ()).throw(OSError('disk unavailable')))
    with pytest.raises(OSError):
        mod.main()
    assert seen == []
    monkeypatch.setattr(mod, 'append_news_lines', original)
    assert mod.main() == 0
    assert seen == ['https://example.org/news/1']
    # Simulate a crash between the durable write and the seen checkpoint.
    mod.main()
    assert target.read_text().count('https://example.org/news/1') == 1


def test_atomic_replace_failure_preserves_old_news(tmp_path, monkeypatch):
    import collector_io as io
    target = tmp_path / 'day.md'
    target.write_text('original\n')
    monkeypatch.setattr(io.os, 'replace', lambda *args: (_ for _ in ()).throw(OSError('disk full')))
    with pytest.raises(OSError):
        io.append_news_lines(target, ['new line'])
    assert target.read_text() == 'original\n'
    assert list(tmp_path.iterdir()) == [target]

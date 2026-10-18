import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
mag = importlib.import_module('scripts.auto_collect_magazine_rss')
agency = importlib.import_module('scripts.auto_collect_agency')
transport = importlib.import_module('source_transport')
network = importlib.import_module('network_readiness')


def test_missing_media_namespace_recovers_only_valid_article_metadata():
    xml = b'<rss><channel><item><title>title</title><link>https://example.org/a</link><media:thumbnail url="x"/></item></channel></rss>'
    rows, warnings = mag.parse_rss(xml)
    assert rows[0]['url'] == 'https://example.org/a'
    assert warnings


@pytest.mark.parametrize('xml', [b'<html/>', b'<rss><channel><item>', b'<rss><channel><item><title>x</title></item></channel></rss>'])
def test_html_truncated_xml_and_missing_links_are_failures(xml):
    with pytest.raises(transport.SourceError):
        mag.parse_rss(xml)


def test_valid_empty_feed_is_success():
    assert mag.parse_rss(b'<rss><channel/></rss>') == ([], [])


def test_official_search_extracts_title_without_category_and_resolves_links(monkeypatch):
    monkeypatch.setattr(mag, 'request', lambda *a, **kw: '<div class="atc_list"><a href="/article/12"><span>FASHION</span><p class="tit">고윤정 인터뷰</p></a></div>'.encode())
    rows, report = mag.collect_feed({'name': 'Test', 'url': 'https://example.org/search', 'mode': 'hll_search'}, '고윤정')
    assert report['status'] == 'success'
    assert rows == [{'title': '고윤정 인터뷰', 'url': 'https://example.org/article/12', 'date': ''}]


def test_challenge_page_is_not_empty_success(monkeypatch):
    monkeypatch.setattr(mag, 'request', lambda *a, **kw: b'<html>Please enable cookies</html>')
    _, report = mag.collect_feed({'name': 'Test', 'url': 'https://example.org/search', 'mode': 'hll_search'}, '고윤정')
    assert report['status'] == 'failed'


@pytest.mark.parametrize('payload', [{'success': False, 'articles': []}, {'success': True, 'total': 3, 'articles': []}, {'success': True, 'articles': [{'title': '고윤정', 'link': 'https://evil.example/a'}]}])
def test_api_error_incomplete_results_and_offsite_links_fail(payload, monkeypatch):
    monkeypatch.setattr(mag, 'request', lambda *a, **kw: json.dumps(payload).encode())
    _, report = mag.collect_feed({'name': 'Test', 'url': 'https://example.org/api', 'mode': 'singles_search'}, '고윤정')
    assert report['status'] == 'failed'


def test_missing_date_is_not_fabricated_and_repeated_write_is_idempotent(tmp_path):
    target = tmp_path / 'editorial.md'
    target.write_text('# Editorial\n')
    entry = mag.make_entry({'title': '고윤정', 'url': 'https://example.org/1'}, {'name': 'Test'})
    assert entry.year is None
    assert mag.apply_entries(target, [entry]) == 1
    assert mag.apply_entries(target, [entry]) == 0
    assert '## 날짜 미상' in target.read_text()


def test_profile_parser_handles_minified_html_and_movie_without_platform():
    html = '<h1>GO YOUNJUNG</h1><h2>Drama</h2><ul><li>2023 Disney+ Moving</li><li>2022 tvN Alchemy of Souls</li></ul><h2>Film</h2><p>2022 Hunt Jo Yoo-Jung</p><h2>Awards</h2><p>2023 Award</p>'
    works = agency.extract_works(html)
    assert len(works) == 3
    assert any('Hunt' in item for item in works)
    assert not any('Award' in item for item in works)


def test_profile_rejects_generic_page():
    with pytest.raises(transport.SourceError, match='identity'):
        agency.extract_works('<h1>Maintenance</h1><p>Drama 2026 some title</p>')


def test_profile_outage_remains_failure_without_writing_news(tmp_path, monkeypatch):
    config = tmp_path / 'agency.json'
    config.write_text(json.dumps({'name': 'Test', 'urls': ['https://example.org/profile']}))
    monkeypatch.setattr(agency, 'CONF_PATH', config)
    monkeypatch.setattr(agency, 'fetch_html', lambda *a: (_ for _ in ()).throw(transport.SourceError('timeout', 'network', True)))
    monkeypatch.setattr(agency, 'append_news_lines', lambda *a: pytest.fail('must not write'))
    assert agency.main(check=True) == 1


class Response:
    def __init__(self, code=200):
        self.status_code, self.content = code, b'content'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.mark.parametrize('code,expected', [(404, 1), (403, 1), (503, 2), (429, 2)])
def test_only_transient_http_errors_retry(code, expected, monkeypatch):
    calls = []
    def request(*args, **kwargs):
        calls.append(args)
        return Response(code)
    monkeypatch.setattr(transport.requests, 'request', request)
    monkeypatch.setattr(transport.time, 'sleep', lambda _: None)
    with pytest.raises(transport.SourceError):
        transport.request('https://example.org')
    assert len(calls) == expected


def test_timeout_retry_recovers(monkeypatch):
    calls = []
    def request(*a, **kw):
        calls.append(a)
        if len(calls) == 1:
            raise requests.Timeout('timeout')
        return Response()
    monkeypatch.setattr(transport.requests, 'request', request)
    monkeypatch.setattr(transport.time, 'sleep', lambda _: None)
    assert transport.request('https://example.org') == b'content'
    assert len(calls) == 2


def test_report_preserves_last_success_during_outage(tmp_path, monkeypatch):
    monkeypatch.setattr(transport, 'BASE', tmp_path)
    transport.save_report('test', [{'name': 'Test', 'url': 'https://example.org', 'status': 'success'}])
    target = tmp_path / 'data/reports/collectors/test.json'
    last = json.loads(target.read_text())['sources'][0]['last_success']
    transport.save_report('test', [{'name': 'Test', 'url': 'https://example.org', 'status': 'failed', 'error': 'timeout'}])
    row = json.loads(target.read_text())['sources'][0]
    assert row['last_success'] == last
    assert row['consecutive_failures'] == 1
    assert 'timeout' in (tmp_path / 'pages/source-collection-status.md').read_text()


def test_network_wait_recovers_after_boot_dns_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(network, 'BASE', tmp_path)
    monkeypatch.setattr(network.time, 'sleep', lambda _: None)
    calls = []
    def probe(*args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            raise transport.SourceError('DNS unavailable', 'network', True)
    monkeypatch.setattr(network, 'request', probe)
    network.wait_for_network()
    assert len(calls) == 2
    assert json.loads((tmp_path / '.locks/network-readiness.json').read_text())['status'] == 'ready'


@pytest.mark.parametrize('error,retries', [('Could not resolve host: github.com', 3), ('Authentication failed', 1), ('non-fast-forward', 1)])
def test_git_does_not_retry_authentication_or_conflicts(error, retries, monkeypatch):
    calls = []
    def command(*args, **kwargs):
        calls.append(args)
        raise subprocess.CalledProcessError(128, 'git', stderr=error)
    monkeypatch.setattr(network.subprocess, 'check_output', command)
    monkeypatch.setattr(network.time, 'sleep', lambda _: None)
    with pytest.raises(RuntimeError):
        network.retry_output(['git', 'fetch'])
    assert len(calls) == retries

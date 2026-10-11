"""Regressions for the repository review: evidence, state, links and dashboard."""
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from scripts import apply_alternative_proofs as proofs
from scripts import auto_detect_future_works as future
from scripts import check_links as links
from scripts import extract_facts_from_markdown as facts
from scripts import operational_status as ops
from scripts import web_dashboard as dashboard
from scripts.work_status import work_status


@pytest.mark.parametrize('note,expected', [
    ('출연 검토 중', 'unknown'), ('공개 예정', 'reported_once'), ('미공개', 'unknown'),
    ('비공식 루머: 내년 공개 예정', 'unknown'), ('Netflix 공식 공개 예정', 'reported_once'),
    ('공개됨 (1월 16일)', 'released'), ('종영', 'released'), ('2026 상반기 공개', 'unknown'),
])
def test_no_keyword_promotion(note, expected):
    assert work_status(note) == expected
    assert future.status_for(note) == expected


def test_year_is_not_release_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(facts, 'PAGES', tmp_path)
    (tmp_path / 'filmography.md').write_text('| 2020 | Netflix | 작품 | 역할 | 공개 예정 | https://example.org |\n')
    assert facts.extract_works()[0]['status'] == 'reported_once'


@pytest.mark.parametrize('line', ['(보강 예정) tvN 공식 소개 문구', '헌트 인터뷰: 촬영 당시', '촬영 현장 사진'])
def test_editorial_tasks_not_future_works(line):
    assert not future.is_future_candidate(line)


def test_proof_needs_review_and_exact_unique_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(proofs, 'BASE', tmp_path)
    (tmp_path / 'pages').mkdir()
    page = tmp_path / 'pages' / 'schedule.md'
    target = '- 제목: Moving https://original.example/moving'
    page.write_text(target + '\n- 제목: Other https://original.example/other\n')
    item = {'file': 'pages/schedule.md', 'skipped_url': 'https://original.example/moving',
            'alternatives': ['https://reviewed.example/moving'], 'target_line': target}
    assert not proofs.apply_item(item)
    item.update(review_status='approved', claim_id='work-moving-release',
                reviewed_by='editor', reviewed_at='2026-10-11')
    assert proofs.apply_item(item)
    assert not proofs.apply_item(item)  # idempotent; changed source needs another review
    assert 'Other https://original.example/other\n' in page.read_text()
    item['file'] = '../outside.md'
    assert not proofs.apply_item(item)
    page.write_text(target + '\n' + target + '\n')
    item['file'] = 'pages/schedule.md'
    assert not proofs.apply_item(item)


def test_http_error_404_is_bad():
    error = HTTPError('https://example.org/x', 404, 'Not Found', {}, None)
    with patch.object(links, 'urlopen', side_effect=error):
        result = links.fetch_status(error.url)
    assert (result.status, result.code) == ('bad', 404)


def test_head_not_supported_falls_back_to_get():
    from unittest.mock import MagicMock
    response = MagicMock()
    response.__enter__.return_value.status = 200
    with patch.object(links, 'urlopen', side_effect=[HTTPError('https://e.org', 405, '', {}, None), response]):
        assert links.fetch_status('https://e.org').status == 'ok'


def test_network_error_is_not_broken_link():
    with patch.object(links, 'urlopen', side_effect=URLError('timeout')):
        assert links.fetch_status('https://e.org').status == 'warn'


def test_skipped_and_outside_budget_never_ok(tmp_path, monkeypatch):
    page = tmp_path / 'page.md'
    page.write_text('https://youtube.com/watch?v=1 https://example.org')
    monkeypatch.setattr(links, 'iter_md_files', lambda: [page])
    monkeypatch.setattr(links, 'MAX_URLS', 1)
    with patch.object(links, 'fetch_status') as fetch, patch.object(links, 'write_report') as report:
        links.main()
    fetch.assert_not_called()
    assert all(r.status == 'unchecked' for r in report.call_args.args[0])


def write_run(base, at, result='성공', note='gnews:OK, agency:FAIL'):
    (base / 'news').mkdir(exist_ok=True)
    (base / 'news' / f'{at:%Y-%m-%d}.md').write_text(
        f'- 실행: {at:%Y-%m-%d %H:%M} (Asia/Seoul)\n- 결과: {result}\n- 메모: {note}\n')


def test_health_uses_recorded_time_and_partial_failures(tmp_path):
    now = datetime(2026, 10, 11, 12, tzinfo=ops.SEOUL)
    write_run(tmp_path, now)
    assert ops.health(tmp_path, now)['status'] == 'partial'
    assert ops.health(tmp_path, now + timedelta(days=2))['status'] == 'stale'
    assert ops.health(tmp_path, now - timedelta(hours=1))['status'] == 'invalid_timestamp'
    write_run(tmp_path, now, '진행중', 'running')
    assert ops.health(tmp_path, now + timedelta(minutes=41))['status'] == 'stalled'


def test_dashboard_no_fake_metrics_or_trigger(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard, 'BASE', tmp_path)
    with TestClient(dashboard.app) as client:
        data = client.get('/api/status').json()
        assert data['automation']['status'] == 'unknown'
        assert data['performance_metrics']['success_rate'] is None
        assert data['performance_metrics']['avg_execution_time'] is None
        assert all(c['last_run'] is None for c in data['collectors'])
        assert client.post('/api/trigger/gnews').status_code == 501
        assert client.get('/healthz').status_code == 200
        html = client.get('/').text
        assert 'location.host' in html and 'wss:' in html
        assert 'innerHTML' not in html


def test_report_regeneration_does_not_refresh_data(tmp_path):
    now = datetime(2026, 10, 11, tzinfo=ops.SEOUL)
    write_run(tmp_path, now - timedelta(days=100), note='gnews:OK')
    before = ops.health(tmp_path, now)
    (tmp_path / 'pages').mkdir()
    (tmp_path / 'pages' / 'system_status.md').write_text(f'Updated: {now}')
    assert ops.health(tmp_path, now) == before


def test_broken_annotation_does_not_damage_markdown_or_id(tmp_path):
    page = tmp_path / 'x.md'
    page.write_text('[title](https://example.org/broken)\n- id: https://example.org/broken\n')
    links.heal_tag_404(page, 'https://example.org/broken')
    once = page.read_text()
    assert '[title](https://example.org/broken) <!-- Broken/404:' in once
    assert '- id: https://example.org/broken\n' in once
    links.heal_tag_404(page, 'https://example.org/broken')
    assert page.read_text() == once


def test_link_score_counts_unchecked_and_warnings(tmp_path, monkeypatch):
    from scripts import wiki_score
    report = tmp_path / 'link-health.md'
    stamp = datetime.now(ops.SEOUL).strftime('%Y-%m-%d %H:%M')
    report.write_text(f'> 갱신: {stamp}\nOK: **50** / WARN: **10** / BAD: **0** / UNCHECKED: **40**')
    monkeypatch.setattr(wiki_score, 'LINK_HEALTH', str(report))
    assert wiki_score.link_health_score().score == 50


@pytest.mark.parametrize('title,expected', [('2020년 12월 1일 공개', None),
    ('10월 11일 공개', '2026-10-11'), ('9월 1일 공개', None), ('2월 30일 공개', None)])
def test_schedule_does_not_move_past_events_into_next_year(title, expected):
    from scripts.auto_collect_schedule import extract_future_date
    result = extract_future_date(title, datetime(2026, 10, 11, 12))
    assert (result.date().isoformat() if result else None) == expected


def test_proof_generator_never_reuses_reports(tmp_path, monkeypatch):
    from scripts import suggest_alternative_proofs as suggest
    monkeypatch.setattr(suggest, 'PAGES', tmp_path)
    (tmp_path / 'filmography.md').write_text('canonical')
    (tmp_path / 'alternative-proof-candidates.md').write_text('generated')
    (tmp_path / 'source-confidence.md').write_text('generated')
    assert [p.name for p in suggest.iter_md_files()] == ['filmography.md']
    assert suggest.nearby_alternatives([(1, 'https://example.org/other')], 2) == []

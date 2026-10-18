"""Regression cases for missed windows, false facts, recovery and rotating coverage."""
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts import collector_batch_state as batch
from scripts import source_schedule as schedule
from scripts.auto_collect_magazine_backfill import is_article
from scripts.official_evidence import parse_document
from scripts.reconcile_evidence import audit_claims
from scripts.remote_backup import create, verify
from scripts.work_status import is_future_candidate, work_status


def test_nonoverlapping_batches_cover_every_source(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, 'STATE_DIR', tmp_path)
    monkeypatch.setattr(batch, 'STATE_PATH', tmp_path/'state.json')
    offsets = [batch.get_and_bump('sites', 40, 4) for _ in range(10)]
    assert offsets == list(range(0, 40, 4))


def test_failed_source_does_not_advance_watermark(tmp_path, monkeypatch):
    monkeypatch.setattr(schedule, 'STATE', tmp_path/'state.json')
    last = datetime.now(UTC) - timedelta(days=12)
    schedule.STATE.write_text(json.dumps({'site:test': {'last_success': last.isoformat()}}))
    schedule.record('site:test', False)
    assert schedule.load()['site:test']['last_success'] == last.isoformat()
    assert schedule.search_window('site:test') == f'after:{last-timedelta(days=2):%Y-%m-%d}'
    schedule.record('site:test', True)
    assert schedule.load()['site:test']['last_success'] != last.isoformat()


@pytest.mark.parametrize('url', ['https://www.elle.co.kr/article/80538',
    'https://www.vogue.co.kr/2020/01/01/test/', 'https://www.harpersbazaar.co.kr/article/1874970',
    'https://www.wkorea.com/2021/01/01/test/', 'https://www.gqkorea.co.kr/2021/01/01/test/',
    'https://www.esquirekorea.co.kr/article/12345', 'https://www.cosmopolitan.co.kr/article/12345'])
def test_historical_article_url_patterns(url):
    assert is_article(url)


def test_retrospective_correction_is_not_a_future_announcement():
    text = '이전의 ‘2026 상반기 공개 예정’ 표기를 종영 상태로 수정했다.'
    assert not is_future_candidate(text)
    assert work_status(text) == 'released'
    assert work_status('촬영 중, 공개일 미정') == 'filming'
    assert not is_future_candidate('- 구분: 작품/캐스팅(뉴스 자동 반영)')


def document(actor='고윤정'):
    schema = {'@type': 'TVSeries', 'name': '새 작품', 'actor': [{'@type':'Person','name':actor}], 'datePublished':'2027-01-02'}
    return '<title>새 작품</title><script type="application/ld+json">'+json.dumps(schema)+'</script><main>고윤정</main>'


def test_sidebar_name_does_not_verify_a_different_cast():
    source = {'domain':'example.org', 'category':'works', 'first_party':True}
    assert parse_document(document('다른 배우'), 'https://example.org/a', source)['claims'] == []
    result = parse_document(document(), 'https://example.org/a', source)
    assert {(c['field'], c['value']) for c in result['claims']} == {('cast','고윤정'), ('release_date','2027-01-02')}
    source['first_party'] = False
    assert parse_document(document(), 'https://example.org/a', source)['claims'] == []


def test_conflicting_dates_never_auto_confirm():
    source = {'domain':'example.org', 'category':'works', 'first_party':True}
    a = parse_document(document(), 'https://example.org/a', source)
    b = parse_document(document().replace('2027-01-02','2027-02-03'), 'https://example.org/b', source)
    accepted, conflicts = audit_claims([a,b])
    assert len(conflicts) == 1
    assert all(row['field'] != 'release_date' for row in accepted)


def test_public_backup_excludes_credentials_and_symlinks(tmp_path):
    (tmp_path/'news').mkdir()
    (tmp_path/'news/2026-10-18.md').write_text('public')
    (tmp_path/'.env').write_text('PRIVATE_SECRET=never-upload')
    (tmp_path/'news/private.md').symlink_to(tmp_path/'.env')
    payload = create(tmp_path)
    report = verify(payload)
    assert report['files'] == 1


def test_new_confirmed_work_gets_page_and_table_idempotently(tmp_path, monkeypatch):
    from scripts import reconcile_evidence as reconcile
    (tmp_path/'pages/works').mkdir(parents=True)
    (tmp_path/'pages/filmography.md').write_text('# 필모그래피\n')
    (tmp_path/'data/facts').mkdir(parents=True)
    path = tmp_path/'data/facts/evidence.json'
    path.write_text(json.dumps([parse_document(document(), 'https://example.org/work',
        {'domain':'example.org','category':'works','first_party':True})]))
    monkeypatch.setattr(reconcile, 'BASE', tmp_path)
    monkeypatch.setattr(reconcile, 'EVIDENCE', path)
    reconcile.main()
    reconcile.main()
    assert len(list((tmp_path/'pages/works').glob('*.md'))) == 1
    assert (tmp_path/'pages/filmography.md').read_text().count('| 새 작품 |') == 1
    assert json.loads((tmp_path/'data/facts/work-evidence-status.json').read_text())['새 작품']['status'] == 'scheduled'


def test_link_checks_rotate_and_skips_do_not_use_budget(tmp_path, monkeypatch):
    from scripts import check_links as links
    page = tmp_path/'page.md'
    page.write_text('https://instagram.com/p/x https://a.example/ https://b.example/')
    monkeypatch.setattr(links, 'BASE', tmp_path)
    monkeypatch.setattr(links, 'MAX_URLS', 1)
    monkeypatch.setattr(links, 'iter_md_files', lambda: [page])
    seen = []
    def probe(url):
        seen.append(url)
        return links.Result(url, 'ok', 200)
    monkeypatch.setattr(links, 'fetch_status', probe)
    monkeypatch.setattr(links, 'write_report', lambda *args, **kwargs: None)
    links.main()
    links.main()
    assert seen == ['https://a.example/', 'https://b.example/']


def test_withdrawn_automatic_claim_loses_confirmation(tmp_path, monkeypatch):
    from scripts import reconcile_evidence as reconcile
    (tmp_path/'pages/works').mkdir(parents=True)
    (tmp_path/'pages/filmography.md').write_text('# 필모그래피\n')
    (tmp_path/'data/facts').mkdir(parents=True)
    path = tmp_path/'data/facts/evidence.json'
    item = parse_document(document(), 'https://example.org/work', {'domain':'example.org','category':'works','first_party':True})
    path.write_text(json.dumps([item]))
    monkeypatch.setattr(reconcile, 'BASE', tmp_path)
    monkeypatch.setattr(reconcile, 'EVIDENCE', path)
    reconcile.main()
    item['claims'] = []
    path.write_text(json.dumps([item]))
    reconcile.main()
    assert json.loads((tmp_path/'data/facts/work-evidence-status.json').read_text())['새 작품']['status'] == 'review_required'
    assert '근거 변경·확인 필요' in (tmp_path/'pages/filmography.md').read_text()

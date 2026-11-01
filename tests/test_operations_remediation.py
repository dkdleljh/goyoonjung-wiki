import json
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts import auto_collect_magazine_rss as magazine
from scripts import check_links, daily_status, source_schedule, source_transport
from scripts import rebuild_group_link_candidates as groups


def test_recent_summary_handles_large_history_without_sigpipe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    (tmp_path/'scripts').mkdir()
    (tmp_path/'news').mkdir()
    shutil.copy2(root/'scripts/rebuild_recent_summary.sh', tmp_path/'scripts')
    for year in range(1980, 2027):
        for month in range(1, 13):
            for day in range(1, 29):
                (tmp_path/f'news/{year}-{month:02}-{day:02}.md').touch()
    subprocess.run(['bash', 'scripts/rebuild_recent_summary.sh'], cwd=tmp_path, check=True, capture_output=True)
    result = (tmp_path/'news/README.md').read_text()
    assert result.count('- [') == 7
    assert '- [2026-12-28]' in result and '- [2026-12-21]' not in result


def test_candidate_update_preserves_photo_and_notes_on_both_sides(tmp_path, monkeypatch):
    monkeypatch.setattr(groups, 'PAGES', tmp_path)
    target = tmp_path/'chanel.md'
    prefix = '# CHANEL\n\n![photo](https://example.org/photo.webp)\n\nManual introduction\n'
    suffix = '\nManual tail\n'
    target.write_text(prefix+groups.START+'\nold\n'+groups.END+suffix)
    items = [('interviews.md', 'new', 'https://example.org/new')]
    groups.update_page(target, 'CHANEL', items)
    first = target.read_text()
    assert first.startswith(prefix) and first.endswith(suffix)
    assert 'https://example.org/new' in first
    groups.update_page(target, 'CHANEL', items)
    assert target.read_text() == first


def test_rss_control_byte_repair_preserves_metadata():
    rows, warnings = magazine.parse_rss(b'<rss><channel><item><title>Go\x07 Younjung</title><link>https://example.org/a</link></item></channel></rss>')
    assert rows[0]['title'] == 'Go Younjung'
    assert warnings == ['XML-forbidden control bytes removed: 1']


def test_failure_backoff_retains_failure_until_retry_is_due(tmp_path, monkeypatch):
    monkeypatch.setattr(source_schedule, 'STATE', tmp_path/'state.json')
    now = datetime.now(UTC)
    source_schedule.STATE.write_text(json.dumps({'official:test': {'status':'failed', 'failures':20, 'last_attempt':now.isoformat()}}))
    assert not source_schedule.retry_due('official:test', now+timedelta(hours=1))
    assert source_schedule.retry_due('official:test', now+timedelta(days=1))
    assert source_schedule.load()['official:test']['status'] == 'failed'


def test_deferred_source_does_not_invent_a_new_check(tmp_path, monkeypatch):
    monkeypatch.setattr(source_transport, 'BASE', tmp_path)
    source_transport.save_report('test', [{'name':'Test','url':'https://example.org','status':'failed'}])
    path=tmp_path/'data/reports/collectors/test.json'
    old=json.loads(path.read_text())['sources'][0]
    source_transport.save_report('test', [{**old, 'deferred':True}])
    new=json.loads(path.read_text())['sources'][0]
    assert (new['checked_at'],new['consecutive_failures'],new['last_success']) == (old['checked_at'],old['consecutive_failures'],old['last_success'])
    assert new['status'] == 'failed'


def test_api_and_retired_urls_are_not_misreported_as_dead_articles():
    for url in ['https://www.wkorea.com/wp-admin/admin-ajax.php','https://maa.co.kr/artists/go-younjung']:
        assert check_links.fetch_status(url).status == 'unchecked'


def test_daily_warning_is_distinct_from_core_failure():
    row={'timestamp':datetime.now(UTC).isoformat(),'status':'partial','steps':[{'name':'RC_MAG_RSS','returncode':1}]}
    assert daily_status.classify(row)['status'] == 'partial'
    row['steps'][0]['name']='RC_FACTS'
    assert daily_status.classify(row)['status'] == 'failure'
    row['steps']=[]
    assert daily_status.classify(row)['status'] == 'failure'

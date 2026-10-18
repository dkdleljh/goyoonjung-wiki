import json
from datetime import UTC, datetime, timedelta

import pytest

from scripts.operational_status import CORE_COLLECTORS, alert_status


@pytest.fixture
def telemetry(tmp_path):
    now = datetime.now(UTC)
    reports = tmp_path / 'data/reports'
    reports.mkdir(parents=True)
    heartbeat = {'timestamp': now.isoformat(), 'status': 'partial',
                 'steps': [{'name': name, 'returncode': 0} for name in CORE_COLLECTORS]
                          + [{'name': 'official_evidence.py', 'returncode': 1}]}
    state = {name: {'returncode': 0, 'last_success': now.timestamp()} for name in CORE_COLLECTORS}
    def save():
        (reports / 'heartbeat.json').write_text(json.dumps(heartbeat))
        (reports / 'fast-task-state.json').write_text(json.dumps(state))
    save()
    return tmp_path, now, heartbeat, state, save


def test_optional_source_failure_remains_visible_without_outage(telemetry):
    base, now, *_ = telemetry
    result = alert_status(base, now)
    assert result['status'] == 'partial'
    assert result['errors'] == []
    assert result['warnings'] == ['official_evidence.py exited 1']


@pytest.mark.parametrize('name,rc', [('auto_collect_google_news.py', 1),
                                   ('auto_collect_youtube_feeds.py', 1),
                                   ('render_pages_from_facts.py', 1),
                                   ('official_evidence.py', 124), ('unknown.py', 1)])
def test_core_transform_timeout_and_unknown_failures_still_alert(telemetry, name, rc):
    base, now, heartbeat, _, save = telemetry
    heartbeat['steps'].append({'name': name, 'returncode': rc})
    save()
    assert alert_status(base, now)['status'] == 'failure'


@pytest.mark.parametrize('minutes', [31, -6])
def test_stale_and_future_heartbeat_still_alert(telemetry, minutes):
    base, now, *_ = telemetry
    assert alert_status(base, now + timedelta(minutes=minutes))['errors']


def test_fresh_heartbeat_cannot_hide_stopped_core_collector(telemetry):
    base, now, _, state, save = telemetry
    state['auto_collect_google_news.py']['last_success'] -= 1801
    save()
    assert alert_status(base, now)['errors']


def test_missing_or_invalid_telemetry_alerts(tmp_path):
    assert alert_status(tmp_path)['errors']


def test_recent_core_success_can_be_reused_when_not_due(telemetry):
    base, now, heartbeat, _, save = telemetry
    heartbeat['steps'] = [{'name': 'official_evidence.py', 'returncode': 1}]
    save()
    assert not alert_status(base, now)['errors']


def test_uncaught_exception_in_optional_collector_still_alerts(telemetry):
    base, now, heartbeat, _, save = telemetry
    heartbeat['steps'][-1]['crashed'] = True
    save()
    assert alert_status(base, now)['errors']

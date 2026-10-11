from datetime import datetime, timezone
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import automation_tick as tick
import publish_website_content as publisher


@pytest.mark.parametrize('status,age,due', [
    ('success', 21599, False), ('success', 21600, True),
    ('partial', 3599, False), ('partial', 3600, True),
    ('failure', 900, True), ('running', 900, True), ('unknown', 900, True),
])
def test_collection_retry_schedule(status, age, due):
    now = 1000000
    state = {'status': status, 'last_run': datetime.fromtimestamp(now-age, timezone.utc).isoformat()}
    assert tick.collection_due(state, 0, now) is due


def test_failed_attempt_cooldown_and_clock_recovery():
    state = {'status': 'unknown', 'last_run': None}
    assert not tick.collection_due(state, 999999, 1000000)
    assert tick.collection_due(state, 1000001, 1000000)


def test_abandoned_marker_recovers_under_exclusive_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(publisher, 'BASE', tmp_path)
    marker = tmp_path / '.locks/lock'
    marker.mkdir(parents=True)
    with publisher.content_lock():
        publisher.recover_collection_marker()
        with pytest.raises(BlockingIOError):
            with publisher.content_lock():
                pytest.fail('Second publisher obtained the same lock')
    assert not marker.exists()
    with publisher.content_lock():
        pass


def test_tick_retries_collection_after_failure_and_publication_after_success(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    monkeypatch.setattr(tick, 'BASE', tmp_path)
    monkeypatch.setattr(tick.time, 'time', lambda: 1000000)
    state = {'status': 'failure', 'last_run': None}
    monkeypatch.setattr(tick, 'health', lambda base: state)
    calls = []
    monkeypatch.setattr(tick.subprocess, 'run', lambda command, **kwargs: (calls.append(command) or SimpleNamespace(returncode=1)))
    assert tick.tick() == 1
    assert calls[-1][1] == 'scripts/collect_and_sync_website.sh'
    # A just-completed collection followed by a failed push must only retry publishing.
    state.update(status='success', last_run=datetime.fromtimestamp(999990, timezone.utc).isoformat())
    tick.tick()
    assert calls[-1][1] == 'scripts/publish_website_content.py'
    assert json.loads((tmp_path / '.locks/automation-tick.json').read_text())['status'] == 'partial_or_failed'


def test_sigkill_releases_os_lock_and_next_run_recovers(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(publisher, 'BASE', tmp_path)
    locks = tmp_path / '.locks'
    locks.mkdir()
    code = "import fcntl, pathlib, time; p=pathlib.Path('.locks'); f=(p/'content-sync.lock').open('w'); fcntl.flock(f,fcntl.LOCK_EX); (p/'lock').mkdir(); print('ready',flush=True); time.sleep(60)"
    process = subprocess.Popen([sys.executable, '-c', code], cwd=tmp_path, stdout=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline().strip() == 'ready'
        with pytest.raises(BlockingIOError):
            with publisher.content_lock():
                pass
        process.kill()
        process.wait(timeout=5)
        with publisher.content_lock():
            publisher.recover_collection_marker()
        assert not (locks / 'lock').exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_wrapper_holds_one_lock_across_all_phases(tmp_path):
    import os
    import shutil
    import subprocess
    root = Path(__file__).resolve().parents[1]
    (tmp_path / 'scripts').mkdir()
    (tmp_path / '.venv/bin').mkdir(parents=True)
    shutil.copy(root / 'scripts/collect_and_sync_website.sh', tmp_path / 'scripts')
    body = '''#!/usr/bin/env bash
set -eu
[[ "$CONTENT_SYNC_LOCK_FD" = 9 ]]
[[ /proc/self/fd/9 -ef .locks/content-sync.lock ]]
if flock -n .locks/content-sync.lock -c true; then exit 99; fi
echo phase >> phases
'''
    for name in ('.venv/bin/python', 'scripts/run_daily_update.sh'):
        file = tmp_path / name
        file.write_text(body)
        file.chmod(0o755)
    result = subprocess.run(['bash', 'scripts/collect_and_sync_website.sh'], cwd=tmp_path,
                            env=dict(os.environ), timeout=10)
    assert result.returncode == 0
    assert (tmp_path / 'phases').read_text().splitlines() == ['phase'] * 3


def test_busy_tick_does_not_delay_next_collection(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    monkeypatch.setattr(tick, 'BASE', tmp_path)
    monkeypatch.setattr(tick.time, 'time', lambda: 1000000)
    monkeypatch.setattr(tick, 'health', lambda base: {'status': 'failure', 'last_run': None})
    monkeypatch.setattr(tick.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=75))
    assert tick.tick() == 75
    report = json.loads((tmp_path / '.locks/automation-tick.json').read_text())
    assert report['collection_attempt'] == 0
    assert report['status'] == 'busy'

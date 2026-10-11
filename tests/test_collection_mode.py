"""Exercise the actual shell coordinator with deterministic collector substitutes."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('fail_step,expected', [(False, 0), (True, 1)])
def test_gitless_collection_never_publishes_or_notifies(tmp_path, fail_step, expected):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    for source in (BASE / 'scripts').iterdir():
        if source.suffix not in {'.py', '.sh'}:
            continue
        target = scripts / source.name
        if source.name in {'run_daily_update.sh', 'mark_news_status.sh'}:
            shutil.copy(source, target)
        elif source.suffix == '.py':
            if 'notify' in source.name:
                target.write_text("from pathlib import Path\nPath('NOTIFICATION_CALLED').touch()\n")
            elif source.name == 'collector_batch_state.py':
                target.write_text("print(0)\n")
            else:
                code = 1 if fail_step and source.name == 'rebuild_work_link_candidates.py' else 0
                target.write_text(f'#!/usr/bin/env python3\nraise SystemExit({code})\n')
        else:
            target.write_text('#!/usr/bin/env bash\nexit 0\n')
        target.chmod(0o755)
    # Any Git call is recorded and fails, including supposedly harmless preflight fetches.
    (scripts / 'git').write_text('#!/usr/bin/env bash\ntouch GIT_CALLED\nexit 99\n')
    (scripts / 'git').chmod(0o755)
    shutil.copytree(BASE / 'config', tmp_path / 'config')
    (tmp_path / 'pages').mkdir()
    env = dict(os.environ, COLLECT_ONLY='1', FORCE='1', PATH=os.environ['PATH'])
    result = subprocess.run(['bash', str(scripts / 'run_daily_update.sh')], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == expected, result.stderr
    assert not (tmp_path / 'GIT_CALLED').exists()
    assert not (tmp_path / 'NOTIFICATION_CALLED').exists()
    news = next((tmp_path / 'news').glob('*.md')).read_text()
    assert ('- 결과: 부분성공' if fail_step else '- 결과: 성공') in news
    assert 'not published' in news
    assert not (tmp_path / '.locks' / 'lock').exists()


def test_preflight_gitless_mode(tmp_path, monkeypatch):
    from scripts import preflight_automation as preflight
    monkeypatch.setenv('COLLECT_ONLY', '1')
    monkeypatch.setattr(preflight, 'BASE', tmp_path)
    monkeypatch.setattr(preflight, 'PAGES', tmp_path / 'pages')
    monkeypatch.setattr(preflight, 'REPORTS', tmp_path / 'reports')
    monkeypatch.setattr(preflight, 'timer_status', lambda name: (name, 'WARN', 'not installed'))
    monkeypatch.setattr(preflight, 'run_cmd', lambda *a, **k: pytest.fail('Git must not run'))
    assert preflight.main() == 0


def test_concurrent_attempt_preserves_running_log(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copy(BASE / 'scripts' / 'run_daily_update.sh', scripts)
    locks = tmp_path / '.locks'
    (locks / 'lock').mkdir(parents=True)
    today = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d')
    log = locks / f'run_{today}.log'
    log.write_text('existing run evidence\n')
    result = subprocess.run(['bash', str(scripts / 'run_daily_update.sh')], cwd=tmp_path,
                            env=dict(os.environ, COLLECT_ONLY='1'), capture_output=True, timeout=5)
    assert result.returncode == 0
    assert log.read_text() == 'existing run evidence\n'


def test_timeout_stops_nested_children(tmp_path):
    import sys
    import time
    marker = tmp_path / 'orphan-wrote'
    child = "import time; from pathlib import Path; time.sleep(1); Path(" + repr(str(marker)) + ").touch()"
    parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",' + repr(child) + ']); time.sleep(10)'
    tool = BASE / 'scripts' / 'timeout'
    result = subprocess.run([str(tool), '0.2', str(tool), '10', sys.executable, '-c', parent], timeout=5)
    assert result.returncode == 124
    time.sleep(1.1)
    assert not marker.exists()


def test_publisher_lock_prevents_collection(tmp_path):
    import fcntl
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copy(BASE / 'scripts' / 'run_daily_update.sh', scripts)
    locks = tmp_path / '.locks'
    locks.mkdir()
    with (locks / 'content-sync.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run(['bash', str(scripts / 'run_daily_update.sh')], cwd=tmp_path,
                                env=dict(os.environ, COLLECT_ONLY='1'), capture_output=True, timeout=5)
    assert result.returncode == 75
    assert not (locks / 'lock').exists()
    assert not (tmp_path / 'news').exists()

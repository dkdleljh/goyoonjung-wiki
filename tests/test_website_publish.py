import importlib.util
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
spec = importlib.util.spec_from_file_location('publisher', BASE / 'scripts/publish_website_content.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.mark.parametrize('path', ['pages/profile.md', 'data/facts/works.json', 'news/2026-10-12.md', 'sources/seen-urls.jsonl'])
def test_content_allowed(path):
    assert m.allowed(path)


@pytest.mark.parametrize('path', ['.env', '.github/workflows/ci.yml', 'scripts/collector.py', 'pages/code.sh', '../pages/profile.md', '/pages/profile.md', 'data/quarantine/new.json'])
def test_unreviewed_changes_rejected(path):
    assert not m.allowed(path)


def test_unfinished_collection_never_runs_git(tmp_path, monkeypatch):
    (tmp_path / '.locks/lock').mkdir(parents=True)
    monkeypatch.setattr(m, 'BASE', tmp_path)
    monkeypatch.setattr(m, 'run', lambda *args: pytest.fail('Must reject before git'))
    with pytest.raises(RuntimeError, match='still running'):
        m.publish()


def setup_publish(tmp_path, monkeypatch, changed='', fail_push=False):
    monkeypatch.setattr(m, 'BASE', tmp_path)
    monkeypatch.setattr(m, 'health', lambda base: {'status': 'partial'})
    calls = []
    monkeypatch.setattr(m, 'verify', lambda **kwargs: (_ for _ in ()).throw(RuntimeError('not deployed')))
    monkeypatch.setattr(m, 'wait_for_sync', lambda **kwargs: {'source_files': 3})
    monkeypatch.setattr(m, 'save_report', lambda report: None)

    def fake_run(*args):
        calls.append(args)
        if args == ('git', 'branch', '--show-current'):
            return 'main'
        if args == ('git', 'remote', 'get-url', 'origin'):
            return 'https://github.com/dkdleljh/goyoonjung-wiki.git'
        if args == ('git', 'diff', '--name-only', '-z', 'HEAD'):
            return changed
        if args[:2] == ('git', 'push') and fail_push:
            raise RuntimeError('push rejected')
        return ''
    monkeypatch.setattr(m, 'run', fake_run)
    return calls


def test_code_changes_stop_before_commit(tmp_path, monkeypatch):
    calls = setup_publish(tmp_path, monkeypatch, 'scripts/unsafe.py')
    with pytest.raises(RuntimeError, match='Unreviewed'):
        m.publish()
    assert not any(c[1] in {'commit', 'push', 'workflow'} for c in calls)


def test_failed_push_cannot_trigger_deployment(tmp_path, monkeypatch):
    calls = setup_publish(tmp_path, monkeypatch, fail_push=True)
    with pytest.raises(RuntimeError, match='push rejected'):
        m.publish()
    assert not any(c[0] == 'gh' for c in calls)


def test_retry_clean_state_pushes_before_dispatch(tmp_path, monkeypatch):
    calls = setup_publish(tmp_path, monkeypatch)
    m.publish()
    assert next(i for i, c in enumerate(calls) if c[1] == 'push') < next(i for i, c in enumerate(calls) if c[0] == 'gh')
    assert not any(c[1] == 'commit' for c in calls)


def test_already_synchronized_does_not_redeploy(tmp_path, monkeypatch):
    calls = setup_publish(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'verify', lambda **kwargs: {'source_files': 3})
    m.publish()
    assert not any(c[0] == 'gh' for c in calls)


def test_dispatch_success_is_not_reported_as_deployment_success(tmp_path, monkeypatch):
    setup_publish(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'wait_for_sync', lambda **kwargs: (_ for _ in ()).throw(RuntimeError('deploy failed')))
    with pytest.raises(RuntimeError, match='deploy failed'):
        m.publish()


def test_source_conflict_never_overwrites_dirty_files(tmp_path, monkeypatch):
    import subprocess
    calls = setup_publish(tmp_path, monkeypatch, 'pages/profile.md')
    previous = m.run

    def fake_run(*args):
        if args[:2] == ('git', 'merge-base'):
            raise subprocess.CalledProcessError(1, args)
        return previous(*args)
    monkeypatch.setattr(m, 'run', fake_run)
    with pytest.raises(RuntimeError, match='merge needs review'):
        m.publish()
    assert not any(c[1] in {'merge', 'commit', 'push'} for c in calls)


def test_clean_remote_update_fast_forwards_real_git(tmp_path, monkeypatch):
    import subprocess
    remote = tmp_path / 'remote.git'
    source = tmp_path / 'source'
    local = tmp_path / 'local'

    def command(*args, cwd=None):
        return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    command('git', 'init', '--bare', '-b', 'main', str(remote))
    command('git', 'clone', str(remote), str(source))
    command('git', 'config', 'user.name', 'Test', cwd=source)
    command('git', 'config', 'user.email', 'test@example.invalid', cwd=source)
    (source / 'pages').mkdir()
    (source / 'pages/profile.md').write_text('original')
    command('git', 'add', '.', cwd=source)
    command('git', 'commit', '-m', 'initial', cwd=source)
    command('git', 'push', 'origin', 'main', cwd=source)
    command('git', 'clone', str(remote), str(local))
    (source / 'pages/profile.md').write_text('remote update')
    command('git', 'commit', '-am', 'update', cwd=source)
    command('git', 'push', 'origin', 'main', cwd=source)
    monkeypatch.setattr(m, 'BASE', local)

    def local_run(*args):
        if args == ('git', 'remote', 'get-url', 'origin'):
            return 'https://github.com/dkdleljh/goyoonjung-wiki.git'
        return command(*args, cwd=local)
    monkeypatch.setattr(m, 'run', local_run)
    assert m.prepare() == set()
    assert (local / 'pages/profile.md').read_text() == 'remote update'


def test_existing_deployment_is_awaited_without_duplicate_dispatch(tmp_path, monkeypatch):
    calls = setup_publish(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'deployment_active', lambda: True)
    m.publish()
    assert not any(c[:3] == ('gh', 'workflow', 'run') for c in calls)


def test_clean_website_checkout_pulls_remote_main(tmp_path, monkeypatch):
    site = tmp_path / 'goyounjung'
    (site / '.git').mkdir(parents=True)
    monkeypatch.setattr(m, 'BASE', tmp_path / 'wiki')
    calls = []

    def command(args, **kwargs):
        calls.append(args)
        if args[-2:] == ['branch', '--show-current']:
            return 'main'
        if args[-3:] == ['remote', 'get-url', 'origin']:
            return 'https://github.com/dkdleljh/goyounjung.git'
        return ''
    monkeypatch.setattr(m.subprocess, 'check_output', command)
    m.sync_website_checkout()
    assert any(c[-3:] == ['merge', '--ff-only', 'origin/main'] for c in calls)


def test_corrupt_public_artifact_triggers_repair_build(tmp_path, monkeypatch):
    calls = setup_publish(tmp_path, monkeypatch)
    def verify(full=False):
        if full:
            raise RuntimeError('corrupt public file')
        return {'source_files': 3}
    monkeypatch.setattr(m, 'verify', verify)
    m.publish()
    assert any(c[:3] == ('gh', 'workflow', 'run') for c in calls)

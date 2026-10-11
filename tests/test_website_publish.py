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

    def fake_run(*args):
        calls.append(args)
        if args == ('git', 'branch', '--show-current'):
            return 'main'
        if args == ('git', 'remote', 'get-url', 'origin'):
            return 'https://github.com/dkdleljh/goyoonjung-wiki.git'
        if args == ('git', 'diff', '--name-only', 'HEAD'):
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

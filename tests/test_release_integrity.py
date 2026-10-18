"""Exercise release guards against real temporary local Git repositories."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'auto_release.sh'


def git(base, *args):
    return subprocess.check_output(['git', '-C', str(base), *args], text=True).strip()


@pytest.fixture
def release_repo(tmp_path):
    remote = tmp_path / 'origin.git'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    repo = tmp_path / 'repo'
    subprocess.run(['git', 'clone', str(remote), str(repo)], check=True, capture_output=True)
    git(repo, 'checkout', '-b', 'main')
    git(repo, 'config', 'user.name', 'Test')
    git(repo, 'config', 'user.email', 'test@example.org')
    (repo / 'scripts').mkdir()
    shutil.copy(SCRIPT, repo / 'scripts' / SCRIPT.name)
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'baseline')
    git(repo, 'tag', 'v1.0.0')
    (repo / 'change.txt').write_text('fix')
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'fix: real behavior')
    git(repo, 'push', 'origin', 'main', '--tags')
    sha = git(repo, 'rev-parse', 'HEAD')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    fake = bin_dir / 'gh'
    fake.write_text('#!/usr/bin/env python3\nimport os, sys\n'
                    'if sys.argv[1:3] == ["run", "view"]: print(os.environ["EVIDENCE"])\n'
                    'elif sys.argv[1:3] == ["release", "view"]: sys.exit(1)\n'
                    'elif sys.argv[1:3] == ["release", "create"]: sys.exit(int(os.environ.get("CREATE_RC", "0")))\n'
                    'else: sys.exit(99)\n')
    fake.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH'], RELEASE_SHA=sha,
               CI_RUN_ID='123', EVIDENCE=json.dumps({'headSha': sha, 'headBranch': 'main',
               'workflowName': 'ci', 'event': 'push', 'conclusion': 'success'}))
    return repo, remote, sha, env


def release(repo, env):
    return subprocess.run(['bash', 'scripts/auto_release.sh'], cwd=repo, env=env, text=True, capture_output=True)


def test_tag_is_exact_tested_sha_no_new_commit(release_repo):
    repo, remote, sha, env = release_repo
    result = release(repo, env)
    assert result.returncode == 0, result.stderr
    assert git(repo, 'rev-parse', 'HEAD') == sha
    assert git(repo, 'status', '--porcelain') == ''
    assert git(remote, 'rev-parse', 'v1.0.1^{commit}') == sha
    assert git(remote, 'rev-parse', 'main') == sha
    assert release(repo, env).returncode == 0


@pytest.mark.parametrize('field,value', [('headSha', '0' * 40), ('conclusion', 'failure'),
                                        ('headBranch', 'feature'), ('event', 'pull_request')])
def test_invalid_ci_never_creates_tag(release_repo, field, value):
    repo, remote, sha, env = release_repo
    evidence = json.loads(env['EVIDENCE'])
    evidence[field] = value
    env['EVIDENCE'] = json.dumps(evidence)
    assert release(repo, env).returncode != 0
    assert git(remote, 'tag', '--list') == 'v1.0.0'


def test_main_race_skips_release(release_repo):
    repo, remote, sha, env = release_repo
    git(repo, 'commit', '--allow-empty', '-m', 'later untested change')
    git(repo, 'push', 'origin', 'main')
    git(repo, 'checkout', '--detach', sha)
    assert release(repo, env).returncode == 0
    assert git(remote, 'tag', '--list') == 'v1.0.0'


def test_publish_failure_visible_and_retry_safe(release_repo):
    repo, remote, sha, env = release_repo
    env['CREATE_RC'] = '42'
    assert release(repo, env).returncode == 42
    assert git(remote, 'rev-parse', 'v1.0.1^{commit}') == sha
    env['CREATE_RC'] = '0'
    assert release(repo, env).returncode == 0
    assert git(remote, 'tag', '--list').splitlines() == ['v1.0.0', 'v1.0.1']


def test_large_tag_history_does_not_exit_with_sigpipe(release_repo):
    repo, remote, sha, env = release_repo
    baseline = git(repo, 'rev-parse', 'v1.0.0')
    # Exceed the pipe buffer so early reader termination reliably breaks git.
    refs = ''.join(f'create refs/tags/v1.0.{i} {baseline}\n' for i in range(1, 6000))
    subprocess.run(['git', '-C', str(repo), 'update-ref', '--stdin'], input=refs, text=True,
                   check=True, capture_output=True)
    result = release(repo, env)
    assert result.returncode == 0, result.stderr
    assert git(remote, 'rev-parse', 'v1.0.6000^{commit}') == sha

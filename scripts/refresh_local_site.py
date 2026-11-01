"""Build committed wiki/site snapshots and atomically serve a verified local release."""
import fcntl
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

WIKI = Path(__file__).resolve().parents[1]
SITE = Path.home()/'goyounjung'
STATE = Path.home()/'.local/share/goyounjung-preview'


def run(*args, cwd=None, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True, stderr=subprocess.STDOUT, timeout=240).strip()


def refresh():
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE/'build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        wiki_sha = run('git', '-C', str(WIKI), 'rev-parse', 'HEAD')
        site_sha = run('git', '-C', str(SITE), 'rev-parse', 'HEAD')
        identity = wiki_sha[:12]+'-'+site_sha[:12]
        target = STATE/'releases'/identity
        current = STATE/'current'
        if current.exists() and current.resolve() == target:
            print('Local preview current:', identity)
            return
        if run('git', '-C', str(SITE), 'status', '--porcelain'):
            raise RuntimeError('Website has uncommitted changes; keeping last validated preview')
        with tempfile.TemporaryDirectory(prefix='build-', dir=STATE) as tmp:
            stage = Path(tmp)
            for src, name, sha in [(WIKI, 'wiki', wiki_sha), (SITE, 'site', site_sha)]:
                run('git', '-c', 'core.hooksPath=/dev/null', 'clone', '--quiet', '--shared', str(src), str(stage/name))
                run('git', '-C', str(stage/name), '-c', 'core.hooksPath=/dev/null', 'checkout', '--quiet', sha)
            (stage/'site/node_modules').symlink_to(SITE/'node_modules', target_is_directory=True)
            env = {**os.environ, 'WIKI_DIR': str(stage/'wiki'), 'CI': 'true'}
            for command in [('npm', 'test'), ('npm', 'run', 'build'), ('npm', 'run', 'check:links')]:
                print(run(*command, cwd=stage/'site', env=env)[-1500:], flush=True)
            metadata = json.loads((stage/'site/dist/sync.json').read_text())
            if metadata['revision'] != wiki_sha or metadata['siteRevision'] != site_sha:
                raise RuntimeError('Built preview provenance mismatch')
            if run('git', '-C', str(SITE), 'rev-parse', 'HEAD') != site_sha or run('git', '-C', str(SITE), 'status', '--porcelain'):
                raise RuntimeError('Website changed during build; retry on next timer')
            target.mkdir(parents=True, exist_ok=True)
            if not (target/'goyounjung').exists():
                shutil.move(stage/'site/dist', target/'goyounjung')
        next_link = STATE/'current.next'
        next_link.unlink(missing_ok=True)
        next_link.symlink_to(target, target_is_directory=True)
        next_link.replace(current)
        for old in sorted((STATE/'releases').iterdir(), key=lambda p:p.stat().st_mtime, reverse=True)[3:]:
            if old != target and not old.is_symlink():
                shutil.rmtree(old)
        print('Local preview updated:', identity)


if __name__ == '__main__':
    try:
        refresh()
    except BlockingIOError:
        print('Build already running')

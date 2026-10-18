"""Explicitly allowlisted public content/state backup, stored on a separate branch."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = 'dkdleljh/goyoonjung-wiki'
BRANCH = 'automation-backups'
ROOTS = ('pages', 'news', 'sources', 'data/facts', 'data/reports')


def api(endpoint: str, method: str = 'GET', body: dict | None = None):
    command = ['gh', 'api', f'repos/{REPO}/{endpoint}', '--method', method]
    if body is not None:
        command += ['--input', '-']
    return json.loads(subprocess.check_output(command, input=json.dumps(body) if body is not None else None,
                                             text=True, stderr=subprocess.PIPE, timeout=120))


def create(base: Path = BASE) -> bytes:
    buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as temporary, tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for root in ROOTS:
            for path in sorted((base/root).rglob('*')):
                if path.is_file() and not path.is_symlink() and path.suffix in {'.md', '.json', '.jsonl', '.txt'}:
                    archive.add(path, arcname=path.relative_to(base), recursive=False)
        db = base/'data/wiki.db'
        if db.exists():
            snapshot = Path(temporary)/'wiki.db'
            with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as source, sqlite3.connect(snapshot) as dest:
                source.backup(dest)
                if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise RuntimeError('SQLite backup integrity check failed')
            archive.add(snapshot, arcname='data/wiki.db', recursive=False)
    return buffer.getvalue()


def verify(payload: bytes) -> dict:
    with tempfile.TemporaryDirectory() as temporary, tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        for member in archive.getmembers():
            name = Path(member.name)
            if not member.isfile() or name.is_absolute() or '..' in name.parts:
                raise ValueError('Unsafe backup member')
            if member.name != 'data/wiki.db' and not any(member.name.startswith(root+'/') for root in ROOTS):
                raise ValueError('Unapproved backup path')
        for member in archive.getmembers():
            source = archive.extractfile(member)
            if source is None or member.size > 100_000_000:
                raise ValueError('Invalid backup payload')
            destination = Path(temporary)/member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read())
        db = Path(temporary)/'data/wiki.db'
        if db.exists():
            with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as con:
                if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('Restored SQLite failed integrity check')
        return {'sha256': hashlib.sha256(payload).hexdigest(), 'files': len(archive.getmembers()),
                'bytes': len(payload), 'restore_verified_at': datetime.now(UTC).isoformat()}


def upload() -> dict:
    payload = create()
    report = verify(payload)
    try:
        api(f'git/ref/heads/{BRANCH}')
    except subprocess.CalledProcessError as exc:
        if '404' not in exc.stderr:
            raise
        head = api('git/ref/heads/main')['object']['sha']
        api('git/refs', 'POST', {'ref': 'refs/heads/'+BRANCH, 'sha': head})
    try:
        old = api('contents/backup/latest.tar.gz?ref='+BRANCH)
    except subprocess.CalledProcessError as exc:
        if '404' not in exc.stderr:
            raise
        old = {}
    body = {'message': 'backup: verified public content and collector state', 'branch': BRANCH,
            'content': base64.b64encode(payload).decode()}
    if old.get('sha'):
        body['sha'] = old['sha']
    api('contents/backup/latest.tar.gz', 'PUT', body)
    # Verify the remote copy, not only the local archive.
    remote = api('contents/backup/latest.tar.gz?ref='+BRANCH)
    raw = subprocess.check_output(['gh', 'api', f'repos/{REPO}/git/blobs/{remote["sha"]}'], text=True, timeout=120)
    downloaded = base64.b64decode(json.loads(raw)['content'])
    if verify(downloaded)['sha256'] != report['sha256']:
        raise RuntimeError('Remote backup hash mismatch')
    from source_transport import atomic_write
    atomic_write(BASE/'data/reports/remote-backup.json', json.dumps(report, indent=2)+'\n')
    return report


def restore_database() -> None:
    remote = api('contents/backup/latest.tar.gz?ref='+BRANCH)
    blob = api('git/blobs/'+remote['sha'])
    payload = base64.b64decode(blob['content'])
    verify(payload)
    # Repository checkout already contains content and cursors. Restore only DB.
    target = BASE/'data/wiki.db'
    if target.exists():
        return
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        file = archive.extractfile('data/wiki.db')
        if file:
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(file.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore-database', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.restore_database:
        restore_database()
    else:
        print(json.dumps(verify(create()) if args.verify_only else upload(), indent=2))

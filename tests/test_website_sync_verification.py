import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify_website_sync as verifier


@pytest.fixture
def deployment(tmp_path, monkeypatch):
    inputs = {'pages/profile.md': '# Profile\n', 'data/facts/profile.json': '{}', 'data/facts/works.json': '[]'}
    sha = lambda value: hashlib.sha256(value).hexdigest()
    for name, text in inputs.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
    metadata = {'schemaVersion': 2, 'revision': 'wiki-sha', 'siteRevision': 'site-sha',
                'builtAt': '2026-10-12T00:00:00Z', 'documents': 1,
                'sourceFiles': [{'file': p, 'sha256': sha(s.encode())} for p, s in inputs.items()]}
    files = {p: b'<html>test</html>' for p in ('index.html', 'works/index.html', 'archive/index.html', 'search/index.html')}
    files['wiki/pages/profile/index.html'] = f'<article data-source-sha256="{sha(inputs["pages/profile.md"].encode())}">Profile</article>'.encode()
    files['search-index.json'] = b'[]'
    files['sync.json'] = json.dumps(metadata).encode()
    manifest = {'revision': 'wiki-sha', 'siteRevision': 'site-sha', 'builtAt': metadata['builtAt'],
                'files': [{'path': p, 'sha256': sha(body)} for p, body in files.items()]}
    files['artifact-manifest.json'] = json.dumps(manifest).encode()

    def fake_git(*args):
        if args[0] == 'status':
            return ''
        if args[0] == 'branch':
            return 'main'
        if args[0] == 'rev-parse':
            return 'wiki-sha'
        if args[0] == 'ls-files':
            return '\0'.join(inputs)
        return ('site-sha' if args[1] == verifier.SITE_REPO else 'wiki-sha') + '\trefs/heads/main'
    def fetch(path):
        return files[path + 'index.html' if not path or path.endswith('/') else path]
    monkeypatch.setattr(verifier, 'BASE', tmp_path)
    monkeypatch.setattr(verifier, 'git', fake_git)
    monkeypatch.setattr(verifier, 'fetch', fetch)
    return files, metadata, manifest


def test_all_three_layers_and_every_artifact_verified(deployment):
    result = verifier.verify()
    assert result['source_files'] == 3
    assert result['verified_artifacts'] == 7


def test_identical_commit_with_corrupt_local_content_is_rejected(deployment):
    (verifier.BASE / 'pages/profile.md').write_text('unpublished alteration')
    with pytest.raises(RuntimeError, match='Source content mismatch'):
        verifier.verify()


def test_missing_source_document_is_rejected(deployment):
    files, metadata, _ = deployment
    metadata['sourceFiles'] = metadata['sourceFiles'][1:]
    files['sync.json'] = json.dumps(metadata).encode()
    with pytest.raises(RuntimeError, match='inventory'):
        verifier.verify()


def test_actual_public_file_mismatch_is_rejected(deployment):
    files, _, _ = deployment
    files['index.html'] = b'old cached deployment'
    with pytest.raises(RuntimeError, match='differs from build'):
        verifier.verify()


def test_missing_page_in_manifest_is_rejected(deployment):
    files, _, manifest = deployment
    manifest['files'] = [x for x in manifest['files'] if not x['path'].startswith('wiki/')]
    files['artifact-manifest.json'] = json.dumps(manifest).encode()
    with pytest.raises(RuntimeError, match='omits required'):
        verifier.verify()


def test_old_build_is_rejected_even_with_same_source_revision(deployment):
    files, _, manifest = deployment
    manifest['builtAt'] = 'older'
    files['artifact-manifest.json'] = json.dumps(manifest).encode()
    with pytest.raises(RuntimeError, match='different deployments'):
        verifier.verify()


def test_artifact_urls_are_verified_without_claiming_directory_cache_freshness(deployment, monkeypatch):
    files, _, _ = deployment
    def fetch(path):
        if not path or path.endswith('/'):
            return b'older CDN alias'
        return files[path]
    monkeypatch.setattr(verifier, 'fetch', fetch)
    with pytest.raises(RuntimeError, match='differs from build'):
        verifier.verify()
    result = verifier.verify(artifact_urls=True)
    assert result['verified_artifacts'] == 7
    assert 'directory aliases may remain cached' in result['url_scope']
    files['index.html'] = b'corrupt exact artifact'
    with pytest.raises(RuntimeError, match='differs from build'):
        verifier.verify(artifact_urls=True)

#!/usr/bin/env python3
"""Publish only reviewed content paths, then request a website rebuild.

Run after COLLECT_ONLY collection. Unknown/code changes or divergence stop publishing.
No force pushes, notifications, release creation, or credential files.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from network_readiness import retry_output, wait_for_network
from operational_status import health
from verify_website_sync import save_report, verify, wait_for_sync

BASE = Path(__file__).resolve().parent.parent
CONTENT_DIRS = ("pages/", "sources/", "news/", "data/facts/", "data/reports/")
CONTENT_FILES = {"index.md", "README.md", "docs/README.md", "data/alternative_proofs.json", "data/skipped_links.json"}


def allowed(name: str) -> bool:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    return (name in CONTENT_FILES or name.startswith(CONTENT_DIRS)) and path.suffix in {".md", ".json", ".jsonl", ".txt"}


def run(*args: str) -> str:
    env = {**os.environ, "NO_HOOK_NOTIFY": "1", "GOYOONJUNG_WIKI_AUTOMATION_PUSH": "1"}
    # The publisher never runs local hooks that could send external notifications.
    command = ["git", "-c", "core.hooksPath=/dev/null", *args[1:]] if args[0] == "git" else list(args)
    execute = retry_output if args[0] == "git" and args[1] in {"fetch", "push"} else subprocess.check_output
    return execute(command, cwd=BASE, env=env, text=True, timeout=180).strip()


def changed_paths() -> set[str]:
    changed = set()
    for args in [("diff", "--name-only", "-z", "HEAD"),
                 ("diff", "--cached", "--name-only", "-z"),
                 ("ls-files", "--others", "--exclude-standard", "-z")]:
        changed.update(p for p in run("git", *args).split("\0") if p)
    return changed


def prepare() -> set[str]:
    if (BASE / ".locks/lock").exists():
        raise RuntimeError("Collection is still running; refusing an incomplete snapshot")
    if run("git", "branch", "--show-current") != "main":
        raise RuntimeError("Publisher requires main")
    if run("git", "remote", "get-url", "origin") not in {"https://github.com/dkdleljh/goyoonjung-wiki.git", "git@github.com:dkdleljh/goyoonjung-wiki.git"}:
        raise RuntimeError("Unexpected origin")
    changed = changed_paths()
    rejected = sorted(p for p in changed if not allowed(p))
    if rejected:
        raise RuntimeError(f"Unreviewed changes outside content paths: {rejected}")
    run("git", "fetch", "origin", "main")
    try:
        run("git", "merge-base", "--is-ancestor", "origin/main", "HEAD")
    except subprocess.CalledProcessError as exc:
        if changed:
            raise RuntimeError("Remote changed while local content is dirty; merge needs review") from exc
        run("git", "merge", "--ff-only", "origin/main")
    return changed


def sync_website_checkout() -> None:
    site = BASE.parent / "goyounjung"
    if not (site / ".git").exists():
        return

    def command(*args: str) -> str:
        execute = retry_output if args[0] == "fetch" else subprocess.check_output
        return execute(["git", "-c", "core.hooksPath=/dev/null", "-C", str(site), *args],
                       text=True, timeout=180).strip()
    if command("branch", "--show-current") != "main" or command("status", "--porcelain"):
        raise RuntimeError("Website checkout needs review: expected clean main")
    if command("remote", "get-url", "origin") not in {"https://github.com/dkdleljh/goyounjung.git", "git@github.com:dkdleljh/goyounjung.git"}:
        raise RuntimeError("Unexpected website origin")
    command("fetch", "origin", "main")
    command("merge", "--ff-only", "origin/main")
    if command("rev-parse", "HEAD") != command("rev-parse", "origin/main"):
        raise RuntimeError("Unpublished website code requires review")


def deployment_active() -> bool:
    raw = run("gh", "run", "list", "--repo", "dkdleljh/goyounjung", "--workflow", "deploy.yml",
              "--branch", "main", "--limit", "10", "--json", "status")
    return any(row["status"] != "completed" for row in json.loads(raw or "[]"))


def full_check_due(result: dict) -> bool:
    try:
        previous = json.loads((BASE / ".locks/website-sync-full.json").read_text())
        age = (datetime.now(UTC) - datetime.fromisoformat(previous["verified_at"])).total_seconds()
        return not (0 <= age < 86400 and all(previous[k] == result[k] for k in ("wiki_revision", "site_revision")))
    except (OSError, ValueError, KeyError):
        return True


def publish(pull_only: bool = False) -> None:
    sync_website_checkout()
    changed = prepare()
    if pull_only:
        print("Remote main checked before collection")
        return
    if changed:
        state = health(BASE)
        # An old completed run may accompany a manual content edit. Preserve its age
        # on the site rather than blocking all edits when a collector is stale.
        if state.get("recorded_result", state["status"]) not in {"success", "partial"}:
            raise RuntimeError(f"Collection is not publishable: {state['status']}")
    for name in changed:
        file = BASE / name
        if file.is_symlink():
            raise RuntimeError(f"Symlinks cannot be published: {name}")
        if file.exists() and file.suffix == ".json":
            json.loads(file.read_text(encoding="utf-8"))
        elif file.exists() and file.suffix == ".jsonl":
            for line in file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    json.loads(line)
    run("git", "diff", "--check")
    run("git", "diff", "--cached", "--check")
    if changed:
        run("git", "add", "--", *sorted(changed))
        run("git", "commit", "-m", "docs: sync collected wiki content for website")
    # Also retries a rejected push when no new files changed.
    run("git", "push", "origin", "HEAD:main")
    sha = run("git", "rev-parse", "HEAD")
    if os.environ.get('PUBLISH_ASYNC') == '1':
        # Hosted fallback cannot dispatch across repositories with GITHUB_TOKEN.
        # The website also polls the wiki revision; local credentials can dispatch.
        if os.environ.get('GITHUB_ACTIONS') != 'true' and not deployment_active():
            run('gh', 'workflow', 'run', 'deploy.yml', '--repo', 'dkdleljh/goyounjung', '--ref', 'main')
        print(f'Published wiki {sha}; deployment verification runs separately')
        return
    try:
        result = verify(full=False)
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError):
        if not deployment_active():
            run("gh", "workflow", "run", "deploy.yml", "--repo", "dkdleljh/goyounjung", "--ref", "main")
        result = wait_for_sync(timeout=900, full=True)
    else:
        if changed or full_check_due(result):
            try:
                result = verify(full=True)
            except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError):
                if not deployment_active():
                    run("gh", "workflow", "run", "deploy.yml", "--repo", "dkdleljh/goyounjung", "--ref", "main")
                result = wait_for_sync(timeout=900, full=True)
    save_report(result)
    print(f"Verified wiki {sha} on GitHub Pages; source_files={result['source_files']}")


@contextmanager
def content_lock():
    path = BASE / ".locks/content-sync.lock"
    path.parent.mkdir(exist_ok=True)
    if os.environ.get("CONTENT_SYNC_LOCK_FD") == "9":
        inherited = os.fstat(9)
        actual = path.stat()
        if (inherited.st_dev, inherited.st_ino) != (actual.st_dev, actual.st_ino):
            raise RuntimeError("Invalid inherited content lock")
        fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    else:
        with path.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield


def recover_collection_marker() -> None:
    # Call only while holding content_lock. A killed collector leaves the marker,
    # but the kernel releases its OS lock. Keep its failed/unfinished content.
    marker = BASE / ".locks/lock"
    if marker.exists():
        marker.rmdir()
        print("Recovered abandoned collection marker", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pull-only", action="store_true")
    args = parser.parse_args()
    try:
        with content_lock():
            recover_collection_marker()
            wait_for_network()
            publish(pull_only=args.pull_only)
    except BlockingIOError:
        print("Collector or publisher active; the next timer will retry")
        raise SystemExit(75) from None
    except Exception as exc:
        save_report({"status": "failed", "error": str(exc)})
        raise


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Publish only reviewed content paths, then request a website rebuild.

Run after COLLECT_ONLY collection. Unknown/code changes or divergence stop publishing.
No force pushes, notifications, release creation, or credential files.
"""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
from pathlib import Path

from operational_status import health

BASE = Path(__file__).resolve().parent.parent
CONTENT_DIRS = ("pages/", "sources/", "news/", "data/facts/", "data/reports/")
CONTENT_FILES = {"index.md", "README.md", "docs/README.md", "data/alternative_proofs.json"}


def allowed(name: str) -> bool:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    return (name in CONTENT_FILES or name.startswith(CONTENT_DIRS)) and path.suffix in {".md", ".json", ".jsonl", ".txt"}


def run(*args: str) -> str:
    env = {**os.environ, "NO_HOOK_NOTIFY": "1", "GOYOONJUNG_WIKI_AUTOMATION_PUSH": "1"}
    # The publisher never runs local hooks that could send external notifications.
    command = ["git", "-c", "core.hooksPath=/dev/null", *args[1:]] if args[0] == "git" else list(args)
    return subprocess.check_output(command, cwd=BASE, env=env, text=True, timeout=180).strip()


def publish() -> None:
    if (BASE / ".locks/lock").exists():
        raise RuntimeError("Collection is still running; refusing an incomplete snapshot")
    if run("git", "branch", "--show-current") != "main":
        raise RuntimeError("Publisher requires main")
    if run("git", "remote", "get-url", "origin") not in {"https://github.com/dkdleljh/goyoonjung-wiki.git", "git@github.com:dkdleljh/goyoonjung-wiki.git"}:
        raise RuntimeError("Unexpected origin")
    state = health(BASE)
    if state["status"] not in {"success", "partial"}:
        raise RuntimeError(f"Collection is not publishable: {state['status']}")
    changed = set(run("git", "diff", "--name-only", "HEAD").splitlines())
    changed.update(run("git", "ls-files", "--others", "--exclude-standard").splitlines())
    rejected = sorted(p for p in changed if not allowed(p))
    if rejected:
        raise RuntimeError(f"Unreviewed changes outside content paths: {rejected}")
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
    run("git", "fetch", "origin", "main")
    # A rejected earlier push can be retried; never absorb remote edits over dirty data.
    run("git", "merge-base", "--is-ancestor", "origin/main", "HEAD")
    if changed:
        run("git", "add", "--", *sorted(changed))
        run("git", "commit", "-m", "docs: sync collected wiki content for website")
    # Also retries a previously failed push, even when no new content changed.
    run("git", "push", "origin", "HEAD:main")
    sha = run("git", "rev-parse", "HEAD")
    run("gh", "workflow", "run", "deploy.yml", "--repo", "dkdleljh/goyounjung", "--ref", "main")
    print(f"Published wiki {sha}; website deployment requested; collection={state['status']}")


def main() -> None:
    (BASE / ".locks").mkdir(exist_ok=True)
    with (BASE / ".locks/website-publish.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        publish()


if __name__ == "__main__":
    main()

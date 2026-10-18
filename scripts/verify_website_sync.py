#!/usr/bin/env python3
"""Compare local Git, remote main, deployed source hashes, and actual Pages bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
SITE = "https://dkdleljh.github.io/goyounjung/"
SITE_REPO = "https://github.com/dkdleljh/goyounjung.git"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=BASE, text=True, timeout=60).strip()


def fetch(path: str) -> bytes:
    # Ordinary public URLs: check what visitors receive, including CDN propagation.
    req = Request(SITE + quote(path, safe="/"), headers={"User-Agent": "goyounjung-sync-verifier/1"})
    with urlopen(req, timeout=30) as response:
        return response.read()


def safe_path(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts and "\\" not in name


def expected_source_paths() -> set[str]:
    paths = git("ls-files", "-z").split("\0")
    return {p for p in paths if p.startswith(("pages/", "sources/", "news/"))
            and p.endswith(".md") and not any(x in p.split("/") for x in ("templates", "checklists"))} | {
                "data/facts/profile.json", "data/facts/works.json"} | ({"data/reports/heartbeat.json"} if "data/reports/heartbeat.json" in paths else set())


def verify(full: bool = True) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("Local working tree has unpublished changes")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("Local checkout is not main")
    sha = git("rev-parse", "HEAD")
    remote = git("ls-remote", "origin", "refs/heads/main").split()[0]
    if remote != sha:
        raise RuntimeError(f"Local/remote mismatch: {sha} != {remote}")
    metadata = json.loads(fetch("sync.json"))
    site_sha = git("ls-remote", SITE_REPO, "refs/heads/main").split()[0]
    site_checkout = BASE.parent / "goyounjung"
    if (site_checkout / ".git").exists():
        def site_git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", str(site_checkout), *args], text=True, timeout=30).strip()
        if site_git("status", "--porcelain") or site_git("rev-parse", "HEAD") != site_sha:
            raise RuntimeError("Local website source differs from GitHub main")
    if metadata.get("revision") != sha or metadata.get("siteRevision") != site_sha:
        raise RuntimeError("Pages has not deployed both latest repository commits")
    source_files = metadata.get("sourceFiles", [])
    names = [item["file"] for item in source_files]
    if len(names) != len(set(names)) or set(names) != expected_source_paths():
        raise RuntimeError("Published source inventory does not match the complete local inventory")
    for item in source_files:
        name = item["file"]
        if not safe_path(name) or (BASE / name).is_symlink():
            raise RuntimeError(f"Unsafe source path: {name}")
        digest = hashlib.sha256((BASE / name).read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise RuntimeError(f"Source content mismatch: {name}")
    count = 0
    if full:
        manifest = json.loads(fetch("artifact-manifest.json"))
        if any(manifest.get(k) != metadata.get(k) for k in ("revision", "siteRevision", "builtAt")):
            raise RuntimeError("CDN manifest and metadata belong to different deployments")
        items = manifest.get("files", [])
        paths = [item["path"] for item in items]
        required = {"index.html", "works/index.html", "archive/index.html", "search/index.html", "sync.json", "search-index.json"}
        required |= {"wiki/" + name[:-3] + "/index.html" for name in names if name.endswith(".md")}
        if len(paths) != len(set(paths)) or not required.issubset(paths):
            raise RuntimeError("Artifact manifest omits required public pages")

        def check(item: dict) -> None:
            name = item["path"]
            if not safe_path(name):
                raise RuntimeError(f"Unsafe artifact path: {name}")
            # /index.html and / are equivalent in Pages; use the visitor-facing URL.
            public_path = name.removesuffix("index.html") if name.endswith("/index.html") or name == "index.html" else name
            body = fetch(public_path)
            if name.startswith("wiki/") and name.endswith("/index.html"):
                source = name[len("wiki/"):-len("/index.html")] + ".md"
                source_hash = next((entry["sha256"] for entry in source_files if entry["file"] == source), None)
                if source_hash and f'data-source-sha256="{source_hash}"'.encode() not in body:
                    raise RuntimeError(f"Page provenance differs from source: {source}")
            if hashlib.sha256(body).hexdigest() != item["sha256"]:
                raise RuntimeError(f"Deployed file differs from build artifact: {name}")
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(check, items))
        count = len(items)
    # Detect a push or local edit during a long verification.
    if git("rev-parse", "HEAD") != sha or git("status", "--porcelain") or git("ls-remote", "origin", "refs/heads/main").split()[0] != sha:
        raise RuntimeError("Source changed during verification; retry on the new snapshot")
    if git("ls-remote", SITE_REPO, "refs/heads/main").split()[0] != site_sha:
        raise RuntimeError("Website source changed during verification; retry")
    return {"status": "verified", "verified_at": datetime.now().astimezone().isoformat(),
            "wiki_revision": sha, "site_revision": site_sha, "source_files": len(source_files),
            "documents": metadata["documents"], "verified_artifacts": count, "full": full,
            "collection": metadata.get("latestRun"), "url": SITE}


def wait_for_sync(timeout: int = 900, full: bool = True) -> dict:
    deadline = time.monotonic() + timeout
    while True:
        try:
            return verify(full=full)
        except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Website synchronization not verified: {exc}") from exc
            print(f"Waiting for synchronization: {exc}", flush=True)
            time.sleep(min(20, max(0, deadline - time.monotonic())))


def save_report(report: dict) -> None:
    target = BASE / ".locks/website-sync-status.json"
    target.parent.mkdir(exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    if report.get("full") and report.get("status") == "verified":
        target.with_name("website-sync-full.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait", type=int, default=0, help="Maximum CDN/deployment wait in seconds")
    parser.add_argument("--quick", action="store_true", help="Compare all source hashes; skip public artifact downloads")
    args = parser.parse_args()
    try:
        result = wait_for_sync(args.wait, full=not args.quick)
        save_report(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        save_report({"status": "failed", "checked_at": datetime.now().astimezone().isoformat(), "error": str(exc)})
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

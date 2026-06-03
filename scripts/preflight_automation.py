#!/usr/bin/env python3
"""Preflight checks for unattended automation."""

from __future__ import annotations

import os
import shutil

try:
    from scripts.automation_common import (
        BASE,
        PAGES,
        REPORTS,
        md_table,
        report_header,
        run_cmd,
        write_json,
    )
    from scripts.config_loader import load_config
except Exception:  # pragma: no cover
    from automation_common import (  # type: ignore
        BASE,
        PAGES,
        REPORTS,
        md_table,
        report_header,
        run_cmd,
        write_json,
    )
    from config_loader import load_config  # type: ignore

CORE_TIMERS = [
    "goyoonjung-wiki-daily.timer",
    "goyoonjung-wiki-sync.timer",
    "goyoonjung-wiki-linkhealth.timer",
    "goyoonjung-wiki-notifyflush.timer",
    "goyoonjung-wiki-backupcleanup.timer",
    "goyoonjung-wiki-watchdog.timer",
]


def check_tool(path: str) -> tuple[str, str, str]:
    p = BASE / path
    return (path, "OK" if p.exists() and os.access(p, os.X_OK) else "WARN", "present" if p.exists() else "missing")


def timer_status(name: str) -> tuple[str, str, str]:
    result = run_cmd(["systemctl", "--user", "list-timers", "--all", name, "--no-pager"], timeout=8)
    if result.rc != 0:
        return (name, "WARN", "systemctl unavailable or user bus not ready")
    lines = [line for line in result.out.splitlines() if name in line]
    if not lines:
        return (name, "WARN", "not listed")
    line = lines[0]
    if line.startswith("-"):
        return (name, "WARN", "no next run")
    return (name, "OK", "next run scheduled")


def main() -> int:
    checks: list[tuple[str, str, str]] = []
    fatal = False

    for tool in [".venv/bin/python", ".venv/bin/ruff", ".venv/bin/bandit", ".venv/bin/pytest"]:
        checks.append(check_tool(tool))

    remote = run_cmd(["git", "remote", "get-url", "origin"])
    checks.append(("git remote origin", "OK" if remote.rc == 0 else "FAIL", remote.out or "missing"))
    if remote.rc != 0:
        fatal = True

    fetch = run_cmd(["git", "fetch", "-q", "origin", "main"], timeout=20)
    checks.append(("git fetch origin main", "OK" if fetch.rc == 0 else "FAIL", fetch.out or "reachable"))
    if fetch.rc != 0:
        fatal = True

    head = run_cmd(["git", "rev-parse", "HEAD"])
    origin = run_cmd(["git", "rev-parse", "origin/main"])
    same = head.rc == 0 and origin.rc == 0 and head.out == origin.out
    checks.append(("HEAD == origin/main", "OK" if same else "WARN", "synced" if same else "local/remote differ"))

    dirty = run_cmd(["git", "status", "--porcelain"])
    checks.append(("working tree", "OK" if not dirty.out else "WARN", "clean" if not dirty.out else "dirty"))

    cfg = load_config()
    webhook = bool(cfg.get("discord_webhook_url") or os.environ.get("DISCORD_WEBHOOK_URL"))
    checks.append(("Discord webhook", "OK" if webhook else "WARN", "configured" if webhook else "not configured"))

    free = shutil.disk_usage(BASE).free // (1024 * 1024)
    checks.append(("disk free", "OK" if free >= 1024 else "WARN", f"{free} MiB"))

    lock = BASE / ".locks" / "lock"
    checks.append(("run lock", "WARN" if lock.exists() else "OK", "present" if lock.exists() else "absent"))

    for timer in CORE_TIMERS:
        checks.append(timer_status(timer))

    status = "FAIL" if fatal else "OK"
    rows = [[name, state, detail.replace("|", "/")] for name, state, detail in checks]
    lines = report_header("Automation Preflight Report (auto)")
    lines += ["## Summary", f"- status: {status}", "", "## Checks", md_table(rows, ["check", "state", "detail"])]
    PAGES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (PAGES / "preflight-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(REPORTS / "preflight.json", {"status": status, "checks": checks})
    print(f"preflight_automation: status={status} checks={len(checks)}")
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main())

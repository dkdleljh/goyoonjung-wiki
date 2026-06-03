#!/usr/bin/env python3
"""Safe self-healing for unattended automation."""

from __future__ import annotations

import os
import time

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

SAFE_TIMERS = [
    "goyoonjung-wiki-daily.timer",
    "goyoonjung-wiki-sync.timer",
    "goyoonjung-wiki-linkhealth.timer",
    "goyoonjung-wiki-notifyflush.timer",
    "goyoonjung-wiki-backupcleanup.timer",
    "goyoonjung-wiki-watchdog.timer",
]


def main() -> int:
    actions: list[tuple[str, str, str]] = []
    lock = BASE / ".locks" / "lock"
    if lock.exists():
        age = time.time() - lock.stat().st_mtime
        if age > 6 * 3600:
            lock.unlink()
            actions.append(("stale lock", "fixed", f"removed age={int(age)}s"))
        else:
            actions.append(("run lock", "kept", f"fresh age={int(age)}s"))
    else:
        actions.append(("run lock", "ok", "absent"))

    flush = run_cmd(["python3", "scripts/flush_notify_queue.py"], timeout=30)
    actions.append(("notify queue", "ok" if flush.rc == 0 else "warn", flush.out[-200:]))

    for cmd, label in [
        (["python3", "scripts/rebuild_quality_report.py"], "quality report"),
        (["python3", "scripts/rebuild_verification_queue.py"], "verification queue"),
        (["python3", "scripts/audit_official_coverage.py"], "official coverage"),
        (["python3", "scripts/generate_doc_portals.py"], "doc portals"),
    ]:
        res = run_cmd(cmd, timeout=60)
        actions.append((label, "ok" if res.rc == 0 else "warn", res.out[-200:]))

    if os.environ.get("GOYOONJUNG_RESTART_TIMERS", "1") != "0":
        run_cmd(["systemctl", "--user", "daemon-reload"], timeout=10)
        for timer in SAFE_TIMERS:
            res = run_cmd(["systemctl", "--user", "enable", "--now", timer], timeout=10)
            actions.append((timer, "ok" if res.rc == 0 else "warn", res.out[-200:] or "enabled"))

    rows = [[a, s, d.replace("|", "/")] for a, s, d in actions]
    lines = report_header("Self-Heal Report (auto)")
    lines += [
        "## Summary",
        f"- actions: {len(actions)}",
        "- destructive_actions: 0",
        "",
        "## Actions",
        md_table(rows, ["action", "state", "detail"]),
        "",
        "## Safety",
        "- git reset, force push, secret creation, mass deletion are intentionally not performed.",
    ]
    PAGES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (PAGES / "self-heal-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(REPORTS / "self_heal.json", {"actions": actions})
    print(f"self_heal_automation: actions={len(actions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

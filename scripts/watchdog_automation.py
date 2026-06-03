#!/usr/bin/env python3
"""Watchdog report for phase-5 unattended operation."""

from __future__ import annotations

try:
    from scripts.automation_common import (
        PAGES,
        REPORTS,
        md_table,
        run_cmd,
        write_json,
    )
except Exception:  # pragma: no cover
    from automation_common import (  # type: ignore
        PAGES,
        REPORTS,
        md_table,
        run_cmd,
        write_json,
    )

TIMERS = [
    "goyoonjung-wiki-daily.timer",
    "goyoonjung-wiki-sync.timer",
    "goyoonjung-wiki-linkhealth.timer",
    "goyoonjung-wiki-notifyflush.timer",
    "goyoonjung-wiki-backupcleanup.timer",
    "goyoonjung-wiki-watchdog.timer",
]


def timer_row(timer: str) -> list[str]:
    res = run_cmd(["systemctl", "--user", "list-timers", "--all", timer, "--no-pager"], timeout=8)
    if res.rc != 0:
        return [timer, "WARN", "systemctl unavailable or user bus not ready"]

    lines = [line for line in res.out.splitlines() if timer in line]
    if not lines:
        return [timer, "WARN", "not listed"]
    if lines[0].startswith("-"):
        return [timer, "OK", "listed; no fixed next run"]
    return [timer, "OK", "listed; next run scheduled"]


def main() -> int:
    rows: list[list[str]] = []
    warnings = 0
    for timer in TIMERS:
        row = timer_row(timer)
        if row[1] != "OK":
            warnings += 1
        rows.append(row)

    health = run_cmd(["bash", "scripts/check_automation_health.sh"], timeout=40)
    rows.append(["check_automation_health", "OK" if health.rc == 0 else "WARN", "passed" if health.rc == 0 else health.out[-180:]])
    if health.rc != 0:
        warnings += 1

    status = "OK" if warnings == 0 else "WARN"
    lines = ["# Watchdog Report (auto)", "", "> Stable watchdog snapshot; volatile timer countdowns are omitted.", ""]
    lines += ["## Summary", f"- status: {status}", f"- warnings: {warnings}", "", "## Checks", md_table(rows, ["target", "state", "detail"])]
    PAGES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (PAGES / "watchdog-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(REPORTS / "watchdog.json", {"status": status, "warnings": warnings, "rows": rows})
    print(f"watchdog_automation: status={status} warnings={warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

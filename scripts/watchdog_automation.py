#!/usr/bin/env python3
"""Watchdog report for phase-5 unattended operation."""

from __future__ import annotations

try:
    from scripts.automation_common import (
        PAGES,
        REPORTS,
        md_table,
        report_header,
        run_cmd,
        write_json,
    )
except Exception:  # pragma: no cover
    from automation_common import (  # type: ignore
        PAGES,
        REPORTS,
        md_table,
        report_header,
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


def main() -> int:
    rows: list[list[str]] = []
    warnings = 0
    for timer in TIMERS:
        res = run_cmd(["systemctl", "--user", "list-timers", "--all", timer, "--no-pager"], timeout=8)
        detail = res.out.replace("\n", " ")[:180]
        ok = res.rc == 0 and timer in res.out and not detail.lstrip().startswith("-")
        if not ok:
            warnings += 1
        rows.append([timer, "OK" if ok else "WARN", detail or "not available"])

    health = run_cmd(["bash", "scripts/check_automation_health.sh"], timeout=40)
    rows.append(["check_automation_health", "OK" if health.rc == 0 else "WARN", health.out[-180:]])
    if health.rc != 0:
        warnings += 1

    status = "OK" if warnings == 0 else "WARN"
    lines = report_header("Watchdog Report (auto)")
    lines += ["## Summary", f"- status: {status}", f"- warnings: {warnings}", "", "## Checks", md_table(rows, ["target", "state", "detail"])]
    PAGES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (PAGES / "watchdog-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(REPORTS / "watchdog.json", {"status": status, "warnings": warnings, "rows": rows})
    print(f"watchdog_automation: status={status} warnings={warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

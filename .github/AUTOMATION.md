# GitHub Automation for goyoonjung-wiki

This repository is maintained by an unattended local automation pipeline.

## Automation Scope

The local runner performs:

1. source collection
2. official/source-grade filtering
3. fact extraction
4. fact conflict auditing
5. verification queue generation
6. Markdown report generation
7. lint/test/health checks
8. git commit and push
9. release note/tag automation
10. Discord notification and queued retry

## Important Scripts

- `scripts/run_daily_update.sh`
- `scripts/check_automation_health.sh`
- `scripts/auto_release.sh`
- `scripts/preflight_automation.py`
- `scripts/self_heal_automation.py`
- `scripts/watchdog_automation.py`
- `scripts/extract_facts_from_markdown.py`
- `scripts/audit_fact_conflicts.py`
- `scripts/source_confidence.py`

## GitHub Workflows

- `.github/workflows/ci.yml`: lint, security scan, compile check, shellcheck, tests
- `.github/workflows/release.yml`: release support workflow

## Safety Rules

- Unofficial future information is not auto-confirmed.
- Rumors and single-source claims stay in queue/watch pages.
- Secrets are never committed.
- The automation does not use force push or destructive reset.
- Generated files are listed in `config/automation-generated-files.txt`.

## Local Health Commands

```bash
make check
bash scripts/check_automation_health.sh
python3 scripts/preflight_automation.py
python3 scripts/watchdog_automation.py
```

## Key Reports

- `pages/system_status.md`
- `pages/preflight-report.md`
- `pages/watchdog-report.md`
- `pages/self-heal-report.md`
- `pages/source-confidence.md`
- `pages/fact-conflicts.md`
- `pages/future-watch.md`

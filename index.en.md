# Go Youn-jung Wiki Index

This wiki operates around two goals:

- **"A wiki that captures everything about Go Youn-jung's past, present, and future"**
- **"Perfect unmanned automation"**

Korean index: [`index.md`](index.md)

## Start Here

- Hub portal (KR): [`pages/hub.md`](pages/hub.md)
- Hub portal (EN): [`pages/hub.en.md`](pages/hub.en.md)
- Profile: [`pages/profile.md`](pages/profile.md)
- Filmography: [`pages/filmography.md`](pages/filmography.md)
- Timeline: [`pages/timeline.md`](pages/timeline.md)
- Recent logs: [`news/README.md`](news/README.md)

## Perfect Scorecard

- Location: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)
- Generator: `python3 scripts/compute_perfect_scorecard.py`

How to read A/B/C/D:

- **A**: coverage-system readiness
- **B**: unmanned-automation readiness
- **C**: actual information volume (grows over time)
- **D**: quality, provenance, and link health

Important note:

- The score is an operating indicator.
- **True 100% completeness cannot be proven.**

## Automation Pipeline (High-level)

Details: [`docs/ux-automation-system.md`](docs/ux-automation-system.md)

1. Daily update
- `scripts/run_daily_update.sh`
- Daily collection, normalization, promotions, reports, and index refresh

2. Backfill
- `scripts/run_backfill_micro.sh`
- `scripts/run_backfill_slice.sh`
- `scripts/run_weekly_backfill.sh`

3. Resilience / Observability
- `scripts/check_automation_health.sh`
- `pages/system_status.md`, `pages/daily-report.md`, `pages/lint-report.md`, `pages/quality-report.md`

## Common Commands

```bash
make venv
make check
./scripts/check_automation_health.sh
python3 scripts/compute_perfect_scorecard.py
```

## Editorial Guardrails

- Prefer official/primary sources
- Exclude rumors/private-life speculation
- Stay link-first for copyright safety

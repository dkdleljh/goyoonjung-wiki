# docs/ Documentation Portal

The `docs/` directory contains documentation explaining the operation principles, automation architecture, and scoring model of the Goyoonjung Wiki.

Project Goals:

- **"A wiki that captures all of Go Youn-jung's past, present, and future"**
- **"Perfect unmanned automation"**

## Quick Start

1. Automation Overview: [`ux-automation-system.md`](ux-automation-system.md)
2. Operation Guide: [`OPERATION_GUIDE.md`](OPERATION_GUIDE.md)
3. System Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)
4. Scoring System: [`scoring.md`](scoring.md)
5. Release/Tag Rules: [`RELEASING.md`](RELEASING.md)
6. Deployment/Unattended runtime (systemd): [`automation-deployment.md`](automation-deployment.md)
7. Changelog Generation: `python3 scripts/generate_changelog.py`

## Perfect Scorecard Documentation

- Result Page: [`../pages/perfect-scorecard.md`](../pages/perfect-scorecard.md)
- Calculation Script: `../scripts/compute_perfect_scorecard.py`
- Health Check: `../scripts/check_automation_health.sh`

Key Interpretation:

- A/B represent system readiness.
- C represents actual accumulated content (changes over time).
- D shows quality/link/source system health.
- **True 100% completeness cannot be proven.**

## Automation Pipeline Documentation

- Daily update + backfill + observability overview: [`ux-automation-system.md`](ux-automation-system.md)
- Operation checklist/execution procedures: [`OPERATION_GUIDE.md`](OPERATION_GUIDE.md)

## Accuracy Principles

- Commands in documentation should **only use scripts that actually exist**.
- When repository structure/links change, synchronize `README.md`, `index.md`, `index.en.md`, and `pages/hub*.md` together.
- Since external links can change, the baseline is **official/primary link priority + link health checks** for management.

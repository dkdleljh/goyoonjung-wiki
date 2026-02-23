#!/usr/bin/env bash
set -euo pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"
TZ="Asia/Seoul"

TODAY=$(TZ="$TZ" date +%F)
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks/lock"
DEBOUNCE_FILE="$BASE/.locks/last-recommended-run.epoch"
DEBOUNCE_SECONDS=$((6*3600))

# Avoid overlapping with the main daily runner.
if [ -e "$LOCK_DIR" ]; then
  echo "SKIP: lock present ($LOCK_DIR)"
  exit 0
fi

# Debounce (best-effort)
if [ -f "$DEBOUNCE_FILE" ]; then
  last=$(cat "$DEBOUNCE_FILE" 2>/dev/null || echo 0)
  now_epoch=$(TZ="$TZ" date +%s)
  if [ "$last" -gt 0 ] && [ $((now_epoch - last)) -lt "$DEBOUNCE_SECONDS" ]; then
    echo "SKIP: debounce (<${DEBOUNCE_SECONDS}s)"
    exit 0
  fi
fi

mkdir -p "$BASE/.locks"
TZ="$TZ" date +%s > "$DEBOUNCE_FILE" 2>/dev/null || true

# 1) Micro backfill (recommended set)
for mode in gnews-sites gnews-queries youtube i18n promote score; do
  echo "[routine] backfill_micro MODE=$mode"
  env MODE="$mode" ./scripts/run_backfill_micro.sh >/dev/null 2>&1 || true
done

# 2) Rebuild indexes + status
./scripts/update_indexes.sh >/dev/null 2>&1 || true
python3 ./scripts/wiki_score.py >/dev/null 2>&1 || true

# 3) Quality checks (recommended)
./scripts/lint_wiki.sh >/dev/null 2>&1 || true
python3 ./scripts/rebuild_quality_report.py >/dev/null 2>&1 || true
python3 ./scripts/quality_alerts.py >/dev/null 2>&1 || true

# 4) Single commit if changed
# Stage everything except backups
git add -A ":(exclude)backups" >/dev/null 2>&1 || true

if git diff --cached --quiet; then
  echo "OK: no changes to commit"
  exit 0
fi

MSG="routine: recommended (coverage+quality) ${TODAY}"
git commit -m "$MSG" >/dev/null

# Push
export NO_HOOK_NOTIFY=1
export GOYOONJUNG_WIKI_AUTOMATION_PUSH=1

git push origin main >/dev/null

echo "OK: committed+push at ${NOW}"

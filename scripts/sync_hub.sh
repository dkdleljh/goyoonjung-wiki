#!/usr/bin/env bash
set -euo pipefail

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
cd "$BASE"

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
DEBOUNCE_LOCK="$LOCK_DIR/sync-debounce.lock"
LAST_RUN_STAMP="$LOCK_DIR/last-sync-run.epoch"

# Serialize sync runs and debounce rapid edit events.
exec 9>"$DEBOUNCE_LOCK"
flock 9

# Debounce window: wait a bit so multiple edits coalesce into one run.
sleep 25

now=$(date +%s)
last=0
if [ -f "$LAST_RUN_STAMP" ]; then
  last=$(cat "$LAST_RUN_STAMP" 2>/dev/null || echo 0)
fi

# If we ran very recently, skip (another trigger already handled it)
if [ "$last" -gt 0 ] && [ $((now - last)) -lt 20 ]; then
  exit 0
fi

echo "$now" > "$LAST_RUN_STAMP" 2>/dev/null || true

git checkout main >/dev/null 2>&1 || true

# If no local changes, pull first. If pull/rebase fails, mark failure and exit nonzero.
if git diff --quiet && git diff --cached --quiet; then
  git fetch -q origin main
  if ! git pull --rebase origin main; then
    ./scripts/mark_news_status.sh 실패 "sync: pull/rebase failed (manual resolve needed)" >/dev/null 2>&1 || true
    exit 1
  fi
fi

# Deterministic pipeline does: collect/index/lint + commit/push + status logging.
./scripts/run_daily_update.sh

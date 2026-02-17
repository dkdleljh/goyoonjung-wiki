#!/usr/bin/env bash
set -euo pipefail

# Backfill slice (I18N) runner: only EN/JA Google News queries.
# Kept separate to reduce resource contention and SIGKILL risk.

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_PATH="$LOCK_DIR/backfill-slice-i18n.lock"

if ! mkdir "$LOCK_PATH" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK_PATH" 2>/dev/null || true' EXIT

RUN_LOG="$LOCK_DIR/backfill_slice_i18n_${TODAY}.log"
: >> "$RUN_LOG" 2>/dev/null || true

echo "== i18n slice start: $NOW ($TZ) ==" >>"$RUN_LOG"

export MAX_QUERIES_I18N="${MAX_QUERIES_I18N:-1}"

I18N_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-queries-i18n.txt 2>/dev/null | wc -l | tr -d ' ')
I18N_TOTAL=${I18N_TOTAL:-0}
OFFSET_I18N=$(python3 ./scripts/collector_batch_state.py get gnews_i18n "$I18N_TOTAL" 2>/dev/null || echo 0)

set +e
run_step() {
  local step="$1"; shift
  echo "[i18n] $step" >>"$RUN_LOG"
  "$@" >>"$RUN_LOG" 2>&1
  local rc=$?
  if [ $rc -ne 0 ]; then
    python3 ./scripts/append_skip_reason.py "$step" "$rc" "backfill-i18n slice failed" >/dev/null 2>&1 || true
  fi
  return 0
}

run_step "i18n:gnews" timeout 35 env BATCH_OFFSET_I18N="$OFFSET_I18N" python3 ./scripts/auto_collect_google_news_queries_i18n.py
run_step "i18n:sanitize-news" timeout 25 python3 ./scripts/sanitize_news_log.py
run_step "i18n:score" timeout 25 python3 ./scripts/compute_perfect_scorecard.py

set -e

echo "== i18n slice end ==" >>"$RUN_LOG"
exit 0

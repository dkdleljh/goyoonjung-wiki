#!/usr/bin/env bash
set -euo pipefail

# Backfill slice runner (ultra-safe, short runtime)
# Intended to be scheduled multiple times (e.g., 6 times on Sunday) instead of one long job.

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_PATH="$LOCK_DIR/backfill-slice.lock"

if ! mkdir "$LOCK_PATH" 2>/dev/null; then
  echo "backfill slice: another slice is already running. Exiting." >&2
  exit 0
fi
trap 'rmdir "$LOCK_PATH" 2>/dev/null || true' EXIT

RUN_LOG="$LOCK_DIR/backfill_slice_${TODAY}.log"
: >> "$RUN_LOG" 2>/dev/null || true

echo "== backfill slice start: $NOW ($TZ) ==" >>"$RUN_LOG"

# Recommended ultra-safe caps
export MAX_SITES="${MAX_SITES:-3}"
export MAX_QUERIES="${MAX_QUERIES:-3}"
export MAX_YT_FEEDS="${MAX_YT_FEEDS:-2}"
export MAX_QUERIES_I18N="${MAX_QUERIES_I18N:-1}"

# Rolling offsets
SITES_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-sites.txt 2>/dev/null | wc -l | tr -d ' ')
SITES_TOTAL=${SITES_TOTAL:-0}
OFFSET_SITES=$(python3 ./scripts/collector_batch_state.py get gnews_sites "$SITES_TOTAL" 2>/dev/null || echo 0)

QUERIES_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-queries.txt 2>/dev/null | wc -l | tr -d ' ')
QUERIES_TOTAL=${QUERIES_TOTAL:-0}
OFFSET_QUERIES=$(python3 ./scripts/collector_batch_state.py get gnews_queries "$QUERIES_TOTAL" 2>/dev/null || echo 0)

YT_TOTAL=$(grep -n "^\s*- name:" -n ./config/youtube-feeds.yml 2>/dev/null | wc -l | tr -d ' ')
YT_TOTAL=${YT_TOTAL:-0}
OFFSET_YT=$(python3 ./scripts/collector_batch_state.py get yt_feeds "$YT_TOTAL" 2>/dev/null || echo 0)

I18N_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-queries-i18n.txt 2>/dev/null | wc -l | tr -d ' ')
I18N_TOTAL=${I18N_TOTAL:-0}
OFFSET_I18N=$(python3 ./scripts/collector_batch_state.py get gnews_i18n "$I18N_TOTAL" 2>/dev/null || echo 0)

set +e
run_step() {
  local step="$1"; shift
  echo "[slice] $step" >>"$RUN_LOG"
  "$@" >>"$RUN_LOG" 2>&1
  local rc=$?
  if [ $rc -ne 0 ]; then
    python3 ./scripts/append_skip_reason.py "$step" "$rc" "backfill-slice step failed" >/dev/null 2>&1 || true
  fi
  return 0
}

# Do only the heaviest collectors in short bursts
run_step "slice:gnews-sites" timeout 45 env BATCH_OFFSET="$OFFSET_SITES" python3 ./scripts/auto_collect_google_news_sites.py
run_step "slice:gnews-queries" timeout 45 env BATCH_OFFSET="$OFFSET_QUERIES" python3 ./scripts/auto_collect_google_news_queries.py
run_step "slice:youtube-feeds" timeout 45 env BATCH_OFFSET_YT="$OFFSET_YT" python3 ./scripts/auto_collect_youtube_feeds.py
run_step "slice:gnews-i18n" timeout 45 env BATCH_OFFSET_I18N="$OFFSET_I18N" python3 ./scripts/auto_collect_google_news_queries_i18n.py

# Quick sanitize + promotions
run_step "slice:sanitize-news" timeout 30 python3 ./scripts/sanitize_news_log.py
run_step "slice:promote:appearances" timeout 20 python3 ./scripts/promote_appearances_from_news.py
run_step "slice:promote:endorsements" timeout 20 python3 ./scripts/promote_endorsements_from_news.py
run_step "slice:promote:works" timeout 20 python3 ./scripts/promote_works_from_news.py

# Lightweight scoring
run_step "slice:score" timeout 30 python3 ./scripts/compute_perfect_scorecard.py

set -e

echo "== backfill slice end ==" >>"$RUN_LOG"
exit 0

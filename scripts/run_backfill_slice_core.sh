#!/usr/bin/env bash
set -euo pipefail

# Backfill slice (CORE) runner: KR sources + YouTube, excludes i18n.
# Ultra-safe, short runtime.

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_PATH="$LOCK_DIR/backfill-slice-core.lock"

if ! mkdir "$LOCK_PATH" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK_PATH" 2>/dev/null || true' EXIT

RUN_LOG="$LOCK_DIR/backfill_slice_core_${TODAY}.log"
: >> "$RUN_LOG" 2>/dev/null || true

echo "== core slice start: $NOW ($TZ) ==" >>"$RUN_LOG"

export MAX_SITES="${MAX_SITES:-3}"
export MAX_QUERIES="${MAX_QUERIES:-3}"
export MAX_YT_FEEDS="${MAX_YT_FEEDS:-2}"

SITES_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-sites.txt 2>/dev/null | wc -l | tr -d ' ')
SITES_TOTAL=${SITES_TOTAL:-0}
OFFSET_SITES=$(python3 ./scripts/collector_batch_state.py get gnews_sites "$SITES_TOTAL" 2>/dev/null || echo 0)

QUERIES_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-queries.txt 2>/dev/null | wc -l | tr -d ' ')
QUERIES_TOTAL=${QUERIES_TOTAL:-0}
OFFSET_QUERIES=$(python3 ./scripts/collector_batch_state.py get gnews_queries "$QUERIES_TOTAL" 2>/dev/null || echo 0)

YT_TOTAL=$(grep -n "^\s*- name:" -n ./config/youtube-feeds.yml 2>/dev/null | wc -l | tr -d ' ')
YT_TOTAL=${YT_TOTAL:-0}
OFFSET_YT=$(python3 ./scripts/collector_batch_state.py get yt_feeds "$YT_TOTAL" 2>/dev/null || echo 0)

set +e
run_step() {
  local step="$1"; shift
  echo "[core] $step" >>"$RUN_LOG"
  "$@" >>"$RUN_LOG" 2>&1
  local rc=$?
  if [ $rc -ne 0 ]; then
    python3 ./scripts/append_skip_reason.py "$step" "$rc" "backfill-core slice failed" >/dev/null 2>&1 || true
  fi
  return 0
}

run_step "core:gnews-sites" timeout 35 env BATCH_OFFSET="$OFFSET_SITES" python3 ./scripts/auto_collect_google_news_sites.py
run_step "core:gnews-queries" timeout 35 env BATCH_OFFSET="$OFFSET_QUERIES" python3 ./scripts/auto_collect_google_news_queries.py
run_step "core:youtube-feeds" timeout 35 env BATCH_OFFSET_YT="$OFFSET_YT" python3 ./scripts/auto_collect_youtube_feeds.py

run_step "core:sanitize-news" timeout 25 python3 ./scripts/sanitize_news_log.py
run_step "core:promote:appearances" timeout 15 python3 ./scripts/promote_appearances_from_news.py
run_step "core:promote:endorsements" timeout 15 python3 ./scripts/promote_endorsements_from_news.py
run_step "core:promote:works" timeout 15 python3 ./scripts/promote_works_from_news.py

run_step "core:score" timeout 25 python3 ./scripts/compute_perfect_scorecard.py

set -e

echo "== core slice end ==" >>"$RUN_LOG"
exit 0

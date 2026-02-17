#!/usr/bin/env bash
set -euo pipefail

# Micro backfill runner (recommended for SIGKILL-prone environments)
# Runs ONE small task per invocation.
# Modes: gnews-sites | gnews-queries | youtube | i18n | promote | score

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

MODE="${MODE:-gnews-sites}"
TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_PATH="$LOCK_DIR/backfill-micro.lock"

if ! mkdir "$LOCK_PATH" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK_PATH" 2>/dev/null || true' EXIT

RUN_LOG="$LOCK_DIR/backfill_micro_${TODAY}.log"
: >> "$RUN_LOG" 2>/dev/null || true

echo "== micro start: $NOW ($TZ) mode=$MODE ==" >>"$RUN_LOG"

set +e
run_step() {
  local step="$1"; shift
  echo "[micro] $step" >>"$RUN_LOG"
  "$@" >>"$RUN_LOG" 2>&1
  local rc=$?
  if [ $rc -ne 0 ]; then
    python3 ./scripts/append_skip_reason.py "$step" "$rc" "backfill-micro step failed" >/dev/null 2>&1 || true
  fi
  return 0
}

# Ultra-safe caps: 1 item per run
export MAX_SITES="${MAX_SITES:-1}"
export MAX_QUERIES="${MAX_QUERIES:-1}"
export MAX_YT_FEEDS="${MAX_YT_FEEDS:-1}"
export MAX_QUERIES_I18N="${MAX_QUERIES_I18N:-1}"

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

case "$MODE" in
  gnews-sites)
    run_step "micro:gnews-sites" timeout 25 env BATCH_OFFSET="$OFFSET_SITES" python3 ./scripts/auto_collect_google_news_sites.py
    ;;
  gnews-queries)
    run_step "micro:gnews-queries" timeout 25 env BATCH_OFFSET="$OFFSET_QUERIES" python3 ./scripts/auto_collect_google_news_queries.py
    ;;
  youtube)
    run_step "micro:youtube-feeds" timeout 25 env BATCH_OFFSET_YT="$OFFSET_YT" python3 ./scripts/auto_collect_youtube_feeds.py
    ;;
  i18n)
    run_step "micro:gnews-i18n" timeout 25 env BATCH_OFFSET_I18N="$OFFSET_I18N" python3 ./scripts/auto_collect_google_news_queries_i18n.py
    ;;
  promote)
    run_step "micro:sanitize-news" timeout 20 python3 ./scripts/sanitize_news_log.py
    run_step "micro:promote:appearances" timeout 15 python3 ./scripts/promote_appearances_from_news.py
    run_step "micro:promote:endorsements" timeout 15 python3 ./scripts/promote_endorsements_from_news.py
    run_step "micro:promote:works" timeout 15 python3 ./scripts/promote_works_from_news.py
    ;;
  score)
    run_step "micro:score" timeout 20 python3 ./scripts/compute_perfect_scorecard.py
    run_step "micro:wiki_score" timeout 20 python3 ./scripts/wiki_score.py
    ;;
  *)
    echo "unknown MODE=$MODE" >>"$RUN_LOG" ;;
esac

set -e

echo "== micro end ==" >>"$RUN_LOG"
exit 0

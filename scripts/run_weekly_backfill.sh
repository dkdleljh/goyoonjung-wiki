#!/usr/bin/env bash
set -euo pipefail

# Weekly backfill runner (recommended defaults)
# Goal: increase C_current (actual accumulated content) without breaking daily stability.
# Strategy: run collectors with higher batch sizes + longer lookback queries already configured.

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_PATH="$LOCK_DIR/weekly-backfill.lock"

if ! mkdir "$LOCK_PATH" 2>/dev/null; then
  echo "weekly backfill: another run is already running (lock exists). Exiting." >&2
  exit 0
fi
trap 'rmdir "$LOCK_PATH" 2>/dev/null || true' EXIT

./scripts/mark_news_status.sh 진행중 "auto: weekly backfill running" >/dev/null || true

# Recommended backfill caps (higher than daily, still bounded)
# Keep conservative to avoid SIGKILL; weekly will rotate offsets across runs.
export MAX_SITES="${MAX_SITES:-6}"
export MAX_QUERIES="${MAX_QUERIES:-6}"
export MAX_YT_FEEDS="${MAX_YT_FEEDS:-3}"
export MAX_QUERIES_I18N="${MAX_QUERIES_I18N:-1}"

# Offsets: start from current rolling offsets (state file) so we sweep across runs.
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

# Collect (best-effort; keep pipeline moving)
set +e

RUN_LOG="$LOCK_DIR/weekly_backfill_${TODAY}.log"
: > "$RUN_LOG" 2>/dev/null || true

step() {
  local name="$1"; shift
  echo "[weekly-backfill] $name" >>"$RUN_LOG"
  # Capture stdout/stderr to log to avoid BrokenPipe when caller pipes output.
  "$@" >>"$RUN_LOG" 2>&1
  local rc=$?
  if [ $rc -ne 0 ]; then
    python3 ./scripts/append_skip_reason.py "$name" "$rc" "weekly-backfill step failed" >/dev/null 2>&1 || true
  fi
  return 0
}

step "collect:sync-media-watch" timeout 20 python3 ./scripts/sync_media_watch_sources.py
step "collect:gnews" timeout 45 ./scripts/auto_collect_google_news.py
step "collect:youtube-feeds" timeout 45 env BATCH_OFFSET_YT="$OFFSET_YT" python3 ./scripts/auto_collect_youtube_feeds.py
step "collect:gnews-sites" timeout 60 env BATCH_OFFSET="$OFFSET_SITES" python3 ./scripts/auto_collect_google_news_sites.py
step "collect:gnews-queries" timeout 60 env BATCH_OFFSET="$OFFSET_QUERIES" python3 ./scripts/auto_collect_google_news_queries.py
step "collect:mag-rss" timeout 60 python3 ./scripts/auto_collect_magazine_rss.py
step "collect:gnews-i18n" timeout 60 env BATCH_OFFSET_I18N="$OFFSET_I18N" python3 ./scripts/auto_collect_google_news_queries_i18n.py
step "collect:portal-news" timeout 60 python3 ./scripts/auto_collect_news_links.py
step "collect:sanitize-news" timeout 45 python3 ./scripts/sanitize_news_log.py

# Promote
step "promote:appearances-from-news" timeout 30 python3 ./scripts/promote_appearances_from_news.py
step "promote:endorsements-from-news" timeout 30 python3 ./scripts/promote_endorsements_from_news.py
step "promote:works-from-news" timeout 30 python3 ./scripts/promote_works_from_news.py

# Rebuild indexes + quality
step "indexes" timeout 45 python3 ./scripts/rebuild_year_indexes.py
step "lint" timeout 45 ./scripts/lint_wiki.sh
step "score:wiki_score" timeout 45 python3 ./scripts/wiki_score.py
step "score:perfect-scorecard" timeout 45 python3 ./scripts/compute_perfect_scorecard.py

set -e

./scripts/mark_news_status.sh 성공 "auto: weekly backfill done" >/dev/null || true

echo "weekly backfill: done ($NOW)"
#!/usr/bin/env bash
set -euo pipefail

# Deterministic daily update runner for goyoonjung-wiki.
# - Prevents runaway re-runs and commit spam
# - Updates status + appends execution history
# - Runs indexes/lint/candidates/backup
# - Commits + pushes only when there are meaningful changes

# Resolve BASE directory relative to this script
# (Assuming script is in /scripts/, so we go up one level)
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

# Unique run id for notification correlation
RUN_ID="$(TZ=\"$TZ\" date +%Y%m%d-%H%M%S)"

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_FILE="$LOCK_DIR/daily-update.lock"

# Notification throttle state (avoid spam)
NOTIFY_DIR="$LOCK_DIR"
SUCCESS_STAMP="$NOTIFY_DIR/last-success-notify.${TODAY}.stamp"
SUCCESS_COMMIT_FILE="$NOTIFY_DIR/last-success-notify.commit"
FAIL_STAMP="$NOTIFY_DIR/last-fail-notify.stamp"
STATUS_FILE="$NOTIFY_DIR/last-run-status.txt"
RECOVERY_STAMP="$NOTIFY_DIR/last-recovery-notify.${TODAY}.stamp"

# Run log (for detailed notifications)
RUN_LOG="$LOCK_DIR/run_${TODAY}.log"
: > "$RUN_LOG" 2>/dev/null || true
CURRENT_STEP="(init)"

# Acquire lock (avoid concurrent runs)
LOCK_PATH="$LOCK_DIR/lock"
if ! mkdir "$LOCK_PATH" 2>/dev/null; then
  # Stale-lock guard: if the lock dir is old, assume a crashed job and recover.
  NOW_EPOCH=$(date +%s)
  LOCK_MTIME=$(stat -c %Y "$LOCK_PATH" 2>/dev/null || echo 0)
  AGE=$((NOW_EPOCH - LOCK_MTIME))
  if [ "$LOCK_MTIME" -gt 0 ] && [ "$AGE" -gt 2700 ]; then
    echo "Stale lock detected (age=${AGE}s). Removing and retrying." >&2
    rm -rf "$LOCK_PATH" 2>/dev/null || true
    mkdir "$LOCK_PATH" 2>/dev/null || { echo "Another update is already running. Exiting." >&2; exit 0; }
  else
    echo "Another update is already running (lock exists). Exiting." >&2
    exit 0
  fi
fi

# Debounce: avoid hammering news logs with repeated runs triggered close together.
# (Cron retries / manual triggers can otherwise create many '진행중' entries.)
LAST_RUN_EPOCH_FILE="$LOCK_DIR/last-daily-run.epoch"
DEBOUNCE_SECONDS=600
now_epoch=$(date +%s)
last_epoch=0
if [ -f "$LAST_RUN_EPOCH_FILE" ]; then
  last_epoch=$(cat "$LAST_RUN_EPOCH_FILE" 2>/dev/null || echo 0)
fi
if [ "$last_epoch" -gt 0 ] && [ $((now_epoch - last_epoch)) -lt "$DEBOUNCE_SECONDS" ]; then
  echo "Debounce: last run was $((now_epoch - last_epoch))s ago (<${DEBOUNCE_SECONDS}s). Skipping." >&2
  rmdir "$LOCK_PATH" 2>/dev/null || true
  exit 0
fi
# Stamp immediately (we already hold the lock).
echo "$now_epoch" > "$LAST_RUN_EPOCH_FILE" 2>/dev/null || true

RUN_OK=0
on_exit() {
  local rc=$?
  # release lock
  rmdir "$LOCK_PATH" 2>/dev/null || true
  # if not marked success, mark failure (prevents stuck '진행중')
  if [ "$RUN_OK" -ne 1 ]; then
    echo "fail run_id=${RUN_ID:-unknown} at=${NOW:-unknown} step=${CURRENT_STEP:-unknown} rc=${rc}" > "${STATUS_FILE:-/dev/null}" 2>/dev/null || true
    ./scripts/mark_news_status.sh 실패 "auto: daily update aborted (rc=$rc)" >/dev/null 2>&1 || true
    # Debounce FAIL notifications: at most once per 30 minutes
    local now last
    now=$(date +%s)
    last=0
    if [ -n "${FAIL_STAMP:-}" ] && [ -f "${FAIL_STAMP}" ]; then
      last=$(cat "${FAIL_STAMP}" 2>/dev/null || echo 0)
    fi
    if [ $((now - last)) -ge 1800 ]; then
      [ -n "${FAIL_STAMP:-}" ] && echo "$now" > "${FAIL_STAMP}" 2>/dev/null || true
      # include step + last error-ish lines from log
      err_tail=$(tail -n 40 "${RUN_LOG:-/dev/null}" 2>/dev/null | grep -E "Traceback|ERROR|ERR:|Error|Failed|denied|403|404|timeout" | tail -n 8 | tr -d '\r' | sed -e 's/[`]/"/g' || true)
      legend="\n---\n색상 의미: GREEN=핵심 성공(스킵 없음) | YELLOW=성공(일부 스킵/경고) | RED=실패/중단"
      python3 ./scripts/notify_status.py "goyoonjung-wiki: 실패 (#${RUN_ID})" "step=${CURRENT_STEP:-unknown}\nrc=${rc}\n${FLUSH_SUM}\nlog_tail=${err_tail}\n(see news/${TODAY}.md)$legend" red >/dev/null 2>&1 || true
    fi
  fi
}
trap on_exit EXIT

# Ensure main branch
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git checkout main >/dev/null 2>&1 || true
fi

# Mark running
./scripts/mark_news_status.sh 진행중 "auto: daily update running" >/dev/null

# Best-effort: flush any queued notifications first
FLUSH_SUM=$(python3 ./scripts/flush_notify_queue.py 2>/dev/null || true)
if [ -z "${FLUSH_SUM:-}" ]; then FLUSH_SUM="flush: (no output)"; fi

# Notification throttle state already initialized above

# Core tasks
# 1) Collect new link-only items (events/photos/interviews) from reliable sources
#    (best-effort; never fail the whole run)
set +e

retry() {
  local tries="$1"; shift
  local delay="$1"; shift
  local n=1
  while true; do
    echo "[STEP:$CURRENT_STEP] run: $*" >>"$RUN_LOG"
    "$@" >>"$RUN_LOG" 2>&1
    local rc=$?
    if [ $rc -eq 0 ]; then
      return 0
    fi

    # observability: record first failure immediately
    python3 ./scripts/append_skip_reason.py "$CURRENT_STEP" "$rc" "command failed (try ${n}/${tries})" >/dev/null 2>&1 || true

    if [ $n -ge $tries ]; then
      return $rc
    fi
    sleep $delay
    n=$((n+1))
  done
}

# 0.9) Sync allowlist from curated watch sources (best-effort)
CURRENT_STEP="collect:sync-media-watch"
retry 2 2 timeout 20 python3 ./scripts/sync_media_watch_sources.py
RC_SYNC_WATCH=$?

# 1) Collect
CURRENT_STEP="collect:visual-links"
retry 3 20 ./scripts/auto_collect_visual_links.py
RC_COLLECT=$?

# 1.5) Collect News RSS (Google News)
CURRENT_STEP="collect:gnews"
retry 3 10 ./scripts/auto_collect_google_news.py
RC_GNEWS=$?

# 1.505) Collect official YouTube uploads (RSS)
CURRENT_STEP="collect:youtube-feeds"
retry 2 5 timeout 60 python3 ./scripts/auto_collect_youtube_feeds.py
RC_YT=$?

# 1.51) Collect Google News site-filtered RSS (magazines/press)
# Rolling batches to avoid long runs (prevents SIGKILL/OOM)
CURRENT_STEP="collect:gnews-sites"
SITES_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-sites.txt 2>/dev/null | wc -l | tr -d ' ')
SITES_TOTAL=${SITES_TOTAL:-0}
OFFSET_SITES=$(python3 ./scripts/collector_batch_state.py get gnews_sites "$SITES_TOTAL" 2>/dev/null || echo 0)
MAX_SITES=${MAX_SITES:-8}
retry 2 5 timeout 90 env MAX_SITES="$MAX_SITES" BATCH_OFFSET="$OFFSET_SITES" ./scripts/auto_collect_google_news_sites.py
RC_GNEWS_SITES=$?

# 1.515) Collect Google News custom queries (brands/ads/etc)
CURRENT_STEP="collect:gnews-queries"
QUERIES_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-queries.txt 2>/dev/null | wc -l | tr -d ' ')
QUERIES_TOTAL=${QUERIES_TOTAL:-0}
OFFSET_QUERIES=$(python3 ./scripts/collector_batch_state.py get gnews_queries "$QUERIES_TOTAL" 2>/dev/null || echo 0)
MAX_QUERIES=${MAX_QUERIES:-8}
retry 2 5 timeout 90 env MAX_QUERIES="$MAX_QUERIES" BATCH_OFFSET="$OFFSET_QUERIES" ./scripts/auto_collect_google_news_queries.py
RC_GNEWS_QUERIES=$?

# 1.52) Collect magazine RSS feeds
CURRENT_STEP="collect:mag-rss"
retry 2 5 timeout 90 ./scripts/auto_collect_magazine_rss.py
RC_MAG_RSS=$?

# 1.525) Collect Google News i18n queries (EN/JA)
CURRENT_STEP="collect:gnews-i18n"
I18N_TOTAL=$(grep -vE '^\s*(#|$)' ./config/google-news-queries-i18n.txt 2>/dev/null | wc -l | tr -d ' ')
I18N_TOTAL=${I18N_TOTAL:-0}
OFFSET_I18N=$(python3 ./scripts/collector_batch_state.py get gnews_i18n "$I18N_TOTAL" 2>/dev/null || echo 0)
MAX_QUERIES_I18N=${MAX_QUERIES_I18N:-4}
retry 2 5 timeout 90 env MAX_QUERIES_I18N="$MAX_QUERIES_I18N" BATCH_OFFSET_I18N="$OFFSET_I18N" python3 ./scripts/auto_collect_google_news_queries_i18n.py
RC_GNEWS_I18N=$?

# 1.55) Collect portal news links (Naver/Daum)
CURRENT_STEP="collect:portal-news"
retry 2 5 timeout 120 ./scripts/auto_collect_news_links.py
RC_PORTAL_NEWS=$?

# 1.6) Sanitize today's news log
CURRENT_STEP="collect:sanitize-news"
retry 2 2 timeout 30 ./scripts/sanitize_news_log.py
RC_SAN_NEWS=$?

# 1.605) Promote appearances/events from today's news log (best-effort)
CURRENT_STEP="promote:appearances-from-news"
retry 2 2 timeout 30 python3 ./scripts/promote_appearances_from_news.py
RC_PROMOTE_APP=$?

# 1.6) Estimate Schedule
CURRENT_STEP="collect:schedule"
retry 3 5 ./scripts/auto_collect_schedule.py
RC_SCHED=$?

# 1.7) Link Health (weekly; keep daily runs fast)
DOW=$(TZ="$TZ" date +%u)
if [ "$DOW" -eq 7 ]; then
  ./scripts/check_links.py >/dev/null 2>&1
  RC_LINK=$?
else
  RC_LINK=0
fi

# 1.8) Agency (MAA) Monitoring
CURRENT_STEP="collect:agency"
retry 2 10 ./scripts/auto_collect_agency.py
RC_AGENCY=$?

# 1.9) Encyclopedia Monitoring
CURRENT_STEP="collect:encyclopedia"
retry 2 10 ./scripts/auto_collect_encyclopedia.py
RC_ENCY=$?

# 2) Write daily encyclopedia-promotion suggestions
retry 2 5 ./scripts/suggest_encyclopedia_promotions.py
RC_SUGGEST=$?

# 2.5) Context Awareness: Update Profile Status (Phase 2)
retry 2 5 ./scripts/update_profile_status.py
RC_STATUS=$?

# 3) Suggest lead paragraphs
retry 2 5 ./scripts/suggest_lead_paragraphs.py
RC_LEAD=$?

# 3.1) Visuals: Generate Timeline (Phase 3)
./scripts/generate_timeline.py >/dev/null 2>&1
RC_VISUAL=$?

# 3.2) Ops: Update Dashboard (Phase 3)
./scripts/update_dashboard.py >/dev/null 2>&1
RC_DASH=$?

# 3.25) Perfect scorecard (multi-axis KPI)
CURRENT_STEP="score:perfect-scorecard"
retry 2 2 timeout 30 python3 ./scripts/compute_perfect_scorecard.py
RC_PERF=$?

# 3.5) Suggest official proof links for awards (no auto-apply)
retry 2 5 ./scripts/suggest_awards_official_proofs.py
RC_AWARD_PROOF=$?

# 3.6) Auto-fill official proof links for awards when verified (strict allowlist)
# Keep bounded: official sites/search can be slow or block.
retry 2 20 timeout 90 ./scripts/promote_awards_official_proofs.py
RC_AWARD_PROOF_AUTO=$?

# 4) Safe metadata promotion
retry 2 10 ./scripts/promote_safe_metadata.py
RC_PROMOTE_SAFE=$?

# 4.1) Auto-fill missing dates from YouTube metadata (safe)
retry 2 5 timeout 45 ./scripts/promote_youtube_dates.py
RC_YT_DATES=$?

# 4.5) Endorsements date promotion
# Bounded: may call network/yt-dlp.
retry 2 15 timeout 60 ./scripts/promote_endorsement_dates.py
RC_ENDO_DATES=$?

# 4.6) Interviews: auto-fill short summaries for KBS entries
retry 2 20 timeout 90 ./scripts/promote_interview_summaries_kbs.py
RC_INT_SUM=$?

# 5) Rebuild candidates for work pages
CURRENT_STEP="build:work-candidates"
./scripts/rebuild_work_link_candidates.py >/dev/null 2>&1
RC_CAND=$?

# 5.1) Backlog candidate promotions (safe)
CURRENT_STEP="promote:mv-candidates"
retry 2 2 timeout 20 ./scripts/promote_mv_candidates_from_news.py
RC_MV_CAND=$?

CURRENT_STEP="promote:tv-ott-candidates"
retry 2 2 timeout 20 ./scripts/promote_official_tv_ott_candidates.py
RC_TVOTT_CAND=$?

set -e

# Keep human-facing 'today' links correct
python3 ./scripts/update_readme_today_links.py >/dev/null 2>&1 || true
python3 ./scripts/update_index_last_updated.py >/dev/null 2>&1 || true

./scripts/update_indexes.sh >/dev/null
./scripts/lint_wiki.sh >/dev/null

# Backup (doesn't enter git)
# Frequent runs can create too many tar.gz files. By default, create at most 1 backup per day.
# But for observability, always record which backup exists/was created.
BACKUP_PATH=""
BACKUP_NOTE="backup:SKIP"
TODAY_STAMP="$TODAY"
EXISTING_BACKUP=$(ls -1t "$BASE/backups/goyoonjung-wiki_${TODAY_STAMP}_"*.tar.gz 2>/dev/null | head -n 1 || true)
if [ -n "${EXISTING_BACKUP:-}" ]; then
  BACKUP_NOTE="backup:$(basename "$EXISTING_BACKUP")"
else
  BACKUP_PATH=$(./scripts/daily_backup.sh)
  BACKUP_NOTE="backup:$(basename "$BACKUP_PATH")"
fi

# Mark success (include key results)
NOTE="auto: done (indexes:OK,lint:OK,${BACKUP_NOTE})"
if [ "${RC_COLLECT:-0}" -ne 0 ]; then
  NOTE="$NOTE, collect:SKIP"
else
  NOTE="$NOTE, collect:OK"
fi
if [ "${RC_GNEWS:-0}" -ne 0 ]; then
  NOTE="$NOTE, gnews:SKIP"
else
  NOTE="$NOTE, gnews:OK"
fi
if [ "${RC_GNEWS_SITES:-0}" -ne 0 ]; then
  NOTE="$NOTE, gnews-sites:SKIP"
else
  NOTE="$NOTE, gnews-sites:OK"
fi
if [ "${RC_GNEWS_QUERIES:-0}" -ne 0 ]; then
  NOTE="$NOTE, gnews-queries:SKIP"
else
  NOTE="$NOTE, gnews-queries:OK"
fi
if [ "${RC_MAG_RSS:-0}" -ne 0 ]; then
  NOTE="$NOTE, mag-rss:SKIP"
else
  NOTE="$NOTE, mag-rss:OK"
fi
if [ "${RC_SCHED:-0}" -ne 0 ]; then
  NOTE="$NOTE, sched:SKIP"
else
  NOTE="$NOTE, sched:OK"
fi
if [ "${RC_LINK:-0}" -ne 0 ]; then
  NOTE="$NOTE, link-health:SKIP"
else
  # only meaningful on Sundays
  if [ "${DOW:-0}" -eq 7 ]; then NOTE="$NOTE, link-health:OK"; fi
fi
if [ "${RC_PORTAL_NEWS:-0}" -ne 0 ]; then
  NOTE="$NOTE, portal-news:SKIP"
else
  NOTE="$NOTE, portal-news:OK"
fi
if [ "${RC_SAN_NEWS:-0}" -ne 0 ]; then
  NOTE="$NOTE, san-news:SKIP"
else
  NOTE="$NOTE, san-news:OK"
fi
if [ "${RC_AGENCY:-0}" -ne 0 ]; then
  NOTE="$NOTE, agency:SKIP"
else
  NOTE="$NOTE, agency:OK"
fi
if [ "${RC_ENCY:-0}" -ne 0 ]; then
  NOTE="$NOTE, ency:SKIP"
else
  NOTE="$NOTE, ency:OK"
fi
if [ "${RC_SUGGEST:-0}" -ne 0 ]; then
  NOTE="$NOTE, promote-suggest:SKIP"
else
  NOTE="$NOTE, promote-suggest:OK"
fi
if [ "${RC_LEAD:-0}" -ne 0 ]; then
  NOTE="$NOTE, lead-suggest:SKIP"
else
  NOTE="$NOTE, lead-suggest:OK"
fi
if [ "${RC_AWARD_PROOF:-0}" -ne 0 ]; then
  NOTE="$NOTE, awards-proof-suggest:SKIP"
else
  NOTE="$NOTE, awards-proof-suggest:OK"
fi
if [ "${RC_AWARD_PROOF_AUTO:-0}" -ne 0 ]; then
  NOTE="$NOTE, awards-proof-auto:SKIP"
else
  NOTE="$NOTE, awards-proof-auto:OK"
fi
if [ "${RC_PROMOTE_SAFE:-0}" -ne 0 ]; then
  NOTE="$NOTE, promote-safe:SKIP"
else
  NOTE="$NOTE, promote-safe:OK"
fi
if [ "${RC_ENDO_DATES:-0}" -ne 0 ]; then
  NOTE="$NOTE, endo-dates:SKIP"
else
  NOTE="$NOTE, endo-dates:OK"
fi
if [ "${RC_INT_SUM:-0}" -ne 0 ]; then
  NOTE="$NOTE, interview-sum:SKIP"
else
  NOTE="$NOTE, interview-sum:OK"
fi
if [ "$RC_CAND" -ne 0 ]; then
  NOTE="$NOTE, work-candidates:SKIP"
else
  NOTE="$NOTE, work-candidates:OK"
fi
if [ "${RC_STATUS:-0}" -ne 0 ]; then
  NOTE="$NOTE, status-update:SKIP"
else
  NOTE="$NOTE, status-update:OK"
fi
if [ "${RC_VISUAL:-0}" -ne 0 ]; then
  NOTE="$NOTE, visual:SKIP"
else
  NOTE="$NOTE, visual:OK"
fi
if [ "${RC_DASH:-0}" -ne 0 ]; then
  NOTE="$NOTE, dashboard:SKIP"
else
  NOTE="$NOTE, dashboard:OK"
fi
./scripts/mark_news_status.sh 성공 "$NOTE" >/dev/null
# record last status for recovery notifications
echo "ok run_id=${RUN_ID} at=${NOW}" > "${STATUS_FILE}" 2>/dev/null || true
RUN_OK=1

# Commit only if there are changes (excluding backups)
# Stage everything except backups (already excluded by .gitignore, but be explicit)
git add -A ":(exclude)backups" >/dev/null 2>&1 || true

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

MSG="daily: update ${TODAY}"
git commit -m "$MSG" >/dev/null

# Prevent git hooks from sending duplicate notifications for automation pushes
export NO_HOOK_NOTIFY=1
export GOYOONJUNG_WIKI_AUTOMATION_PUSH=1

git push origin main >/dev/null

NEW_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)

# Success notification:
# - send if HEAD changed since last notified success (prevents missing notifications but avoids spam)
# - also send a one-off RECOVERED if last status was FAIL
SEND_KIND=""
LAST_OK_COMMIT=""
if [ -f "$SUCCESS_COMMIT_FILE" ]; then LAST_OK_COMMIT=$(cat "$SUCCESS_COMMIT_FILE" 2>/dev/null || true); fi

if [ "$NEW_HEAD" != "unknown" ] && [ "$NEW_HEAD" != "$LAST_OK_COMMIT" ]; then
  SEND_KIND="ok"
  echo "$NEW_HEAD" > "$SUCCESS_COMMIT_FILE" 2>/dev/null || true
  date -Iseconds > "$SUCCESS_STAMP" 2>/dev/null || true
elif [ -f "$STATUS_FILE" ] && grep -q '^fail ' "$STATUS_FILE" 2>/dev/null && [ ! -f "$RECOVERY_STAMP" ]; then
  SEND_KIND="recovered"
  date -Iseconds > "$RECOVERY_STAMP" 2>/dev/null || true
fi

if [ -n "$SEND_KIND" ]; then
  # Readable per-module summary
  fmt() { local name="$1"; local rc="$2"; if [ "${rc:-0}" -eq 0 ]; then echo "$name:OK"; else echo "$name:SKIP(rc=$rc)"; fi; }

  detail_lines=$(cat <<EOF
$(fmt collect "$RC_COLLECT")
$(fmt gnews "$RC_GNEWS")
$(fmt gnews-sites "$RC_GNEWS_SITES")
$(fmt gnews-queries "$RC_GNEWS_QUERIES")
$(fmt mag-rss "$RC_MAG_RSS")
$(fmt portal-news "$RC_PORTAL_NEWS")
$(fmt san-news "$RC_SAN_NEWS")
$(fmt schedule "$RC_SCHED")
$(fmt agency "$RC_AGENCY")
$(fmt encyclopedia "$RC_ENCY")
$(fmt awards-auto "$RC_AWARD_PROOF_AUTO")
$(fmt promote-safe "$RC_PROMOTE_SAFE")
$(fmt yt-dates "$RC_YT_DATES")
$(fmt endo-dates "$RC_ENDO_DATES")
$(fmt interview-sum "$RC_INT_SUM")
$(fmt work-candidates "$RC_CAND")
$(fmt dashboard "$RC_DASH")
$(fmt visuals "$RC_VISUAL")
$(fmt mv-candidates "$RC_MV_CAND")
$(fmt tv-ott-candidates "$RC_TVOTT_CAND")
EOF
)

  # Color policy for SUCCESS runs (unmanned practical):
  # - green: all CRITICAL modules OK
  # - yellow: run succeeded but at least one CRITICAL module SKIP
  # Optional modules (do not affect color): encyclopedia, awards-proof-suggest, yt-dates, endo-dates, interview-sum, work-candidates
  color="green"
  critical=$(cat <<EOF
$(fmt collect "$RC_COLLECT")
$(fmt gnews "$RC_GNEWS")
$(fmt gnews-sites "$RC_GNEWS_SITES")
$(fmt gnews-queries "$RC_GNEWS_QUERIES")
$(fmt mag-rss "$RC_MAG_RSS")
$(fmt portal-news "$RC_PORTAL_NEWS")
$(fmt san-news "$RC_SAN_NEWS")
$(fmt schedule "$RC_SCHED")
$(fmt agency "$RC_AGENCY")
EOF
)
  if echo "$critical" | grep -q "SKIP"; then
    color="yellow"
  fi

  legend="\n---\n색상 의미: GREEN=핵심 성공(스킵 없음) | YELLOW=성공(일부 스킵/경고) | RED=실패/중단"
  title="goyoonjung-wiki: 성공 (#${RUN_ID})"
  if [ "$SEND_KIND" = "recovered" ]; then
    title="goyoonjung-wiki: 복구 성공 (#${RUN_ID})"
  fi
  python3 ./scripts/notify_status.py "$title" "$MSG (commit=$NEW_HEAD)\n$NOTE\n${FLUSH_SUM}\n---\n$detail_lines$legend" "$color" >/dev/null 2>&1 || true
fi

echo "OK: $MSG"

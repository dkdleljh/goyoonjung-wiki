#!/usr/bin/env bash
set -euo pipefail

# Deterministic daily update runner for goyoonjung-wiki.
# - Prevents runaway re-runs and commit spam
# - Updates status + appends execution history
# - Runs indexes/lint/candidates/backup
# - Commits + pushes only when there are meaningful changes

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
cd "$BASE"

TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

LOCK_DIR="$BASE/.locks"
mkdir -p "$LOCK_DIR"
LOCK_FILE="$LOCK_DIR/daily-update.lock"

# Acquire lock (avoid concurrent cron runs)
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  # Stale-lock guard: if the lock file hasn't been touched for a while,
  # assume a crashed job and try once to recover.
  NOW_EPOCH=$(date +%s)
  LOCK_MTIME=$(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)
  AGE=$((NOW_EPOCH - LOCK_MTIME))
  if [ "$LOCK_MTIME" -gt 0 ] && [ "$AGE" -gt 2700 ]; then
    echo "Stale lock detected (age=${AGE}s). Retrying lock acquisition." >&2
    rm -f "$LOCK_FILE" 2>/dev/null || true
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
      echo "Another update is already running. Exiting." >&2
      exit 0
    fi
  else
    echo "Another update is already running. Exiting." >&2
    exit 0
  fi
fi

lock_touch() {
  # keep lock mtime fresh so other runners can detect true staleness
  touch "$LOCK_FILE" 2>/dev/null || true
}
lock_touch

# Ensure main branch
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git checkout main >/dev/null 2>&1 || true
fi

# Cleanup stale '진행중' status from crashed runs (best-effort)
./scripts/cleanup_stale_running.sh >/dev/null 2>&1 || true

# Apply any user-approved promotions from today's news (best-effort)
./scripts/apply_approved_promotions.py >/dev/null 2>&1 || true

# Mark running
lock_touch
./scripts/mark_news_status.sh 진행중 "auto: daily update running" >/dev/null

FINAL_STATUS="실패"
FINAL_NOTE="auto: crashed"

on_exit() {
  local rc=$?
  lock_touch
  if [ "$FINAL_STATUS" != "" ]; then
    ./scripts/mark_news_status.sh "$FINAL_STATUS" "$FINAL_NOTE" >/dev/null 2>&1 || true
  fi
  exit $rc
}
trap on_exit EXIT

# Core tasks
# 1) Collect new link-only items (events/photos/interviews) from reliable sources
#    (best-effort; never fail the whole run)
set +e

retry() {
  local tries="$1"; shift
  local delay="$1"; shift
  local n=1
  while true; do
    "$@" >/dev/null 2>&1
    local rc=$?
    if [ $rc -eq 0 ]; then
      return 0
    fi
    if [ $n -ge $tries ]; then
      return $rc
    fi
    sleep $delay
    n=$((n+1))
  done
}

# 1) Collect
retry 3 20 ./scripts/auto_collect_visual_links.py
RC_COLLECT=$?

# 2) Write daily encyclopedia-promotion suggestions
retry 2 5 ./scripts/suggest_encyclopedia_promotions.py
RC_SUGGEST=$?

# 2.5) Suggest one daily promotion task (approval-based)
retry 2 5 ./scripts/suggest_daily_promotion_task.py
RC_DAILY_TASK=$?

# 3) Suggest lead paragraphs
retry 2 5 ./scripts/suggest_lead_paragraphs.py
RC_LEAD=$?

# 3.2) Suggest official/primary proof candidates for profile fields (no auto-apply)
retry 2 5 ./scripts/suggest_profile_official_proofs.py
RC_PROFILE_PROOF=$?

# 3.3) Suggest official announcement link candidates for endorsements (no auto-apply)
retry 2 5 ./scripts/suggest_endorsements_official_announcements.py
RC_ENDO_PROOF_SUGGEST=$?

# 3.5) Suggest official proof links for awards (no auto-apply)
retry 2 5 ./scripts/suggest_awards_official_proofs.py
RC_AWARD_PROOF=$?

# 3.6) Auto-fill official proof links for awards when verified (strict allowlist)
# Keep this best-effort and time-bounded to avoid delaying the whole pipeline.
timeout 90 ./scripts/promote_awards_official_proofs.py >/dev/null 2>&1
RC_AWARD_PROOF_AUTO=$?

# 4) Safe metadata promotion
retry 2 10 ./scripts/promote_safe_metadata.py
RC_PROMOTE_SAFE=$?

# 4.4) Endorsements: try to auto-fill official announcement links when verified (best-effort)
set +e
timeout 45 ./scripts/promote_endorsements_official_announcements.py >/dev/null 2>&1
RC_ENDO_ANNOUNCE=$?
set -e

# 4.5) Endorsements date promotion (can be slow due to yt-dlp/network)
# Run at most once per day.
ENDO_STAMP_FILE="$LOCK_DIR/endo-dates.${TODAY}.done"
RC_ENDO_DATES=0
if [ -f "$ENDO_STAMP_FILE" ]; then
  RC_ENDO_DATES=0
else
  set +e
  timeout 60 ./scripts/promote_endorsement_dates.py >/dev/null 2>&1
  RC_ENDO_DATES=$?
  set -e
  # Mark done even if it times out; retry tomorrow.
  : > "$ENDO_STAMP_FILE" || true
fi

# 4.6) Interviews: auto-fill short summaries for KBS entries — hard timeout
set +e
timeout 60 ./scripts/promote_interview_summaries_kbs.py >/dev/null 2>&1
RC_INT_SUM=$?
set -e

# 5) Rebuild candidates for work pages
./scripts/rebuild_work_link_candidates.py >/dev/null 2>&1
RC_CAND=$?
set -e

lock_touch
./scripts/update_indexes.sh >/dev/null
lock_touch
./scripts/lint_wiki.sh >/dev/null

# Backup (doesn't enter git)
# Frequent runs can create too many tar.gz files. By default, create at most 1 backup per day.
BACKUP_PATH=""
BACKUP_NOTE="backup:SKIP"
TODAY_STAMP="$TODAY"
if ls "$BASE/backups/goyoonjung-wiki_${TODAY_STAMP}_"*.tar.gz >/dev/null 2>&1; then
  : # already backed up today
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
if [ "${RC_SUGGEST:-0}" -ne 0 ]; then
  NOTE="$NOTE, promote-suggest:SKIP"
else
  NOTE="$NOTE, promote-suggest:OK"
fi
if [ "${RC_DAILY_TASK:-0}" -ne 0 ]; then
  NOTE="$NOTE, daily-task:SKIP"
else
  NOTE="$NOTE, daily-task:OK"
fi
if [ "${RC_LEAD:-0}" -ne 0 ]; then
  NOTE="$NOTE, lead-suggest:SKIP"
else
  NOTE="$NOTE, lead-suggest:OK"
fi
if [ "${RC_PROFILE_PROOF:-0}" -ne 0 ]; then
  NOTE="$NOTE, profile-proof-suggest:SKIP"
else
  NOTE="$NOTE, profile-proof-suggest:OK"
fi
if [ "${RC_ENDO_PROOF_SUGGEST:-0}" -ne 0 ]; then
  NOTE="$NOTE, endo-proof-suggest:SKIP"
else
  NOTE="$NOTE, endo-proof-suggest:OK"
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
if [ "${RC_ENDO_ANNOUNCE:-0}" -ne 0 ]; then
  NOTE="$NOTE, endo-announce:SKIP"
else
  NOTE="$NOTE, endo-announce:OK"
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
FINAL_STATUS="성공"
FINAL_NOTE="$NOTE"
./scripts/mark_news_status.sh 성공 "$NOTE" >/dev/null

# Commit only if there are changes (excluding backups)
# Stage everything except backups (already excluded by .gitignore, but be explicit)
lock_touch
git add -A ":(exclude)backups" >/dev/null 2>&1 || true

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

MSG="daily: update ${TODAY}"
git commit -m "$MSG" >/dev/null

git push origin main >/dev/null

echo "OK: $MSG"

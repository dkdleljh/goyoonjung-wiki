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
REASONS_JSON="$LOCK_DIR/last-run-reasons.json"

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

# NOTE: Unmanned mode: no human approvals required.
# (If approvals exist, they are ignored by default to avoid manual dependency.)

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

# Record skip/failure reasons (unmanned transparency)
REASONS_TMP="$LOCK_DIR/last-run-reasons.tmp"
: > "$REASONS_TMP" || true
record_reason() {
  # args: name rc reason note
  local name="$1"; shift
  local rc="$1"; shift
  local reason="$1"; shift
  local note="${1:-}"
  printf '%s\t%s\t%s\t%s\n' "$name" "$rc" "$reason" "$note" >> "$REASONS_TMP" || true
}


# 1) Collect
retry 3 20 ./scripts/auto_collect_visual_links.py
RC_COLLECT=$?

# 2) Write daily encyclopedia-promotion suggestions
retry 2 5 ./scripts/suggest_encyclopedia_promotions.py
RC_SUGGEST=$?

# 2.5) Suggest one daily promotion task (auto-only; no approvals required)
retry 2 5 ./scripts/suggest_daily_promotion_task.py
RC_DAILY_TASK=$?

# 3) Suggest lead paragraphs
retry 2 5 ./scripts/suggest_lead_paragraphs.py
RC_LEAD=$?

# 3.2) (Unmanned) No user-facing URL-hunting suggestion steps here.
#     Proof-link discovery is handled by strict auto-promoters only.
RC_PROFILE_PROOF=0
RC_ENDO_PROOF_SUGGEST=0
RC_AWARD_PROOF=0

# 3.55) Rebuild small cache of official award-site URLs (best-effort)
set +e
timeout 30 ./scripts/rebuild_awards_official_cache.py >/dev/null 2>&1
RC_AWARDS_CACHE=$?
set -e
if [ "$RC_AWARDS_CACHE" -ne 0 ] && [ "$RC_AWARDS_CACHE" -eq 124 ]; then
  record_reason "awards-cache" "$RC_AWARDS_CACHE" "timeout" "cache rebuild timed out"
fi

# 3.6) Auto-fill official proof links for awards when verified (strict allowlist)
# Keep this best-effort and time-bounded to avoid delaying the whole pipeline.
# Circuit breaker: run at most once per day.
AWARDS_PROOF_STAMP_FILE="$LOCK_DIR/awards-proof-auto.${TODAY}.done"
RC_AWARD_PROOF_AUTO=0
if [ -f "$AWARDS_PROOF_STAMP_FILE" ]; then
  RC_AWARD_PROOF_AUTO=0
else
  set +e
  timeout 60 ./scripts/promote_awards_official_proofs.py >/dev/null 2>&1
  RC_AWARD_PROOF_AUTO=$?
  set -e
  if [ "$RC_AWARD_PROOF_AUTO" -ne 0 ]; then
    if [ "$RC_AWARD_PROOF_AUTO" -eq 124 ]; then
      record_reason "awards-proof-auto" "$RC_AWARD_PROOF_AUTO" "timeout" "auto-verify step timed out (may be slow official sites)"
    else
      record_reason "awards-proof-auto" "$RC_AWARD_PROOF_AUTO" "error" "nonzero exit"
    fi
  fi
  # Mark done even if it times out; retry tomorrow.
  : > "$AWARDS_PROOF_STAMP_FILE" || true
fi

# 4) Safe metadata promotion
retry 2 10 ./scripts/promote_safe_metadata.py
RC_PROMOTE_SAFE=$?

# 4.1) Profile policy adjustment for unmanned mode (reduces perpetual '교차검증 필요')
set +e
timeout 15 ./scripts/promote_profile_policy_unmanned.py >/dev/null 2>&1
RC_PROFILE_POLICY=$?
set -e
if [ "$RC_PROFILE_POLICY" -ne 0 ]; then
  record_reason "profile-policy" "$RC_PROFILE_POLICY" "error" "policy script nonzero"
fi

# 4.2) Dates from meta tags (interviews/pictorials)
set +e
timeout 60 ./scripts/promote_dates_from_meta.py >/dev/null 2>&1
RC_META_DATES=$?
set -e
if [ "$RC_META_DATES" -ne 0 ]; then
  if [ "$RC_META_DATES" -eq 124 ]; then
    record_reason "meta-dates" "$RC_META_DATES" "timeout" "meta date promotion timed out"
  else
    record_reason "meta-dates" "$RC_META_DATES" "error" "nonzero exit"
  fi
fi

# 4.3) Interview summaries for allowlist domains (magazines)
set +e
timeout 60 ./scripts/promote_interview_summaries_allowlist.py >/dev/null 2>&1
RC_INT_SUM_ALLOW=$?
set -e
if [ "$RC_INT_SUM_ALLOW" -ne 0 ]; then
  if [ "$RC_INT_SUM_ALLOW" -eq 124 ]; then
    record_reason "interview-sum-allow" "$RC_INT_SUM_ALLOW" "timeout" "allowlist summary timed out"
  else
    record_reason "interview-sum-allow" "$RC_INT_SUM_ALLOW" "error" "nonzero exit"
  fi
fi

# 4.4) Endorsements: try to auto-fill official announcement links when verified (best-effort)
set +e
timeout 45 ./scripts/promote_endorsements_official_announcements.py >/dev/null 2>&1
RC_ENDO_ANNOUNCE=$?
if [ "$RC_ENDO_ANNOUNCE" -ne 0 ]; then
  if [ "$RC_ENDO_ANNOUNCE" -eq 124 ]; then
    record_reason "endo-announce" "$RC_ENDO_ANNOUNCE" "timeout" "official-site crawl timed out"
  else
    record_reason "endo-announce" "$RC_ENDO_ANNOUNCE" "error" "nonzero exit"
  fi
fi
# Fallback: if official sites are blocked, use the already-linked official channel post/video as '공식 발표'
timeout 20 ./scripts/promote_endorsements_announce_fallback.py >/dev/null 2>&1
RC_ENDO_ANNOUNCE_FALLBACK=$?
if [ "$RC_ENDO_ANNOUNCE_FALLBACK" -ne 0 ]; then
  if [ "$RC_ENDO_ANNOUNCE_FALLBACK" -eq 124 ]; then
    record_reason "endo-announce-fallback" "$RC_ENDO_ANNOUNCE_FALLBACK" "timeout" "fallback step timed out"
  else
    record_reason "endo-announce-fallback" "$RC_ENDO_ANNOUNCE_FALLBACK" "error" "nonzero exit"
  fi
fi
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
  if [ "$RC_ENDO_DATES" -ne 0 ]; then
    if [ "$RC_ENDO_DATES" -eq 124 ]; then
      record_reason "endo-dates" "$RC_ENDO_DATES" "timeout" "yt-dlp/network step timed out"
    else
      record_reason "endo-dates" "$RC_ENDO_DATES" "error" "nonzero exit"
    fi
  fi
  # Mark done even if it times out; retry tomorrow.
  : > "$ENDO_STAMP_FILE" || true
fi

# 4.6) Interviews: auto-fill short summaries for KBS entries — hard timeout
set +e
timeout 60 ./scripts/promote_interview_summaries_kbs.py >/dev/null 2>&1
RC_INT_SUM=$?
if [ "$RC_INT_SUM" -ne 0 ]; then
  if [ "$RC_INT_SUM" -eq 124 ]; then
    record_reason "interview-sum" "$RC_INT_SUM" "timeout" "KBS fetch/parse timed out"
  else
    record_reason "interview-sum" "$RC_INT_SUM" "error" "nonzero exit"
  fi
fi
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
# (Unmanned) user-facing URL-hunting suggestions removed
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
if [ "${RC_PROFILE_POLICY:-0}" -ne 0 ]; then
  NOTE="$NOTE, profile-policy:SKIP"
else
  NOTE="$NOTE, profile-policy:OK"
fi
if [ "${RC_META_DATES:-0}" -ne 0 ]; then
  NOTE="$NOTE, meta-dates:SKIP"
else
  NOTE="$NOTE, meta-dates:OK"
fi
if [ "${RC_INT_SUM_ALLOW:-0}" -ne 0 ]; then
  NOTE="$NOTE, interview-allow:SKIP"
else
  NOTE="$NOTE, interview-allow:OK"
fi
if [ "${RC_ENDO_ANNOUNCE:-0}" -ne 0 ]; then
  NOTE="$NOTE, endo-announce:SKIP"
else
  NOTE="$NOTE, endo-announce:OK"
fi
if [ "${RC_ENDO_ANNOUNCE_FALLBACK:-0}" -ne 0 ]; then
  NOTE="$NOTE, endo-announce-fallback:SKIP"
else
  NOTE="$NOTE, endo-announce-fallback:OK"
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
# Write skip reasons JSON + insert into news (best-effort)
{
  echo "{";
  echo "  \"timestamp\": \"$NOW\",";
  echo "  \"steps\": [";
  first=1;
  while IFS=$'\t' read -r name rc reason note; do
    [ -z "${name:-}" ] && continue
    if [ $first -eq 0 ]; then echo "    ,"; fi
    first=0
    # naive JSON escaping for quotes
    note_esc=$(printf '%s' "$note" | sed 's/"/\\"/g')
    reason_esc=$(printf '%s' "$reason" | sed 's/"/\\"/g')
    name_esc=$(printf '%s' "$name" | sed 's/"/\\"/g')
    echo "    {\"name\": \"$name_esc\", \"rc\": $rc, \"reason\": \"$reason_esc\", \"note\": \"$note_esc\"}";
  done < "$REASONS_TMP";
  echo "  ]";
  echo "}";
} > "$REASONS_JSON" 2>/dev/null || true
./scripts/write_skip_reasons_to_news.py >/dev/null 2>&1 || true

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

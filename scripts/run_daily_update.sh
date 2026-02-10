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
  echo "Another update is already running. Exiting."
  exit 0
fi

# Ensure main branch
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git checkout main >/dev/null 2>&1 || true
fi

# Mark running
./scripts/mark_news_status.sh 진행중 "auto: daily update running" >/dev/null

# Core tasks
# 1) Collect new link-only items (events/photos/interviews) from reliable sources
#    (best-effort; never fail the whole run)
set +e
./scripts/auto_collect_visual_links.py >/dev/null 2>&1
RC_COLLECT=$?

# 2) Write daily encyclopedia-promotion suggestions into today's news log
./scripts/suggest_encyclopedia_promotions.py >/dev/null 2>&1
RC_SUGGEST=$?

# 3) Suggest lead paragraphs (drafts only; no auto-apply)
./scripts/suggest_lead_paragraphs.py >/dev/null 2>&1
RC_LEAD=$?

# 4) Safe metadata promotion (fill objective dates/titles)
./scripts/promote_safe_metadata.py >/dev/null 2>&1
RC_PROMOTE_SAFE=$?

# 5) Rebuild candidates for work pages
./scripts/rebuild_work_link_candidates.py >/dev/null 2>&1
RC_CAND=$?
set -e

./scripts/update_indexes.sh >/dev/null
./scripts/lint_wiki.sh >/dev/null

# Backup (doesn't enter git)
BACKUP_PATH=$(./scripts/daily_backup.sh)

# Mark success (include key results)
NOTE="auto: done (indexes:OK,lint:OK,backup:$(basename "$BACKUP_PATH"))"
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
if [ "${RC_LEAD:-0}" -ne 0 ]; then
  NOTE="$NOTE, lead-suggest:SKIP"
else
  NOTE="$NOTE, lead-suggest:OK"
fi
if [ "${RC_PROMOTE_SAFE:-0}" -ne 0 ]; then
  NOTE="$NOTE, promote-safe:SKIP"
else
  NOTE="$NOTE, promote-safe:OK"
fi
if [ "$RC_CAND" -ne 0 ]; then
  NOTE="$NOTE, work-candidates:SKIP"
else
  NOTE="$NOTE, work-candidates:OK"
fi
./scripts/mark_news_status.sh 성공 "$NOTE" >/dev/null

# Commit only if there are changes (excluding backups)
# Stage everything except backups (already excluded by .gitignore, but be explicit)
git add -A ":(exclude)backups" >/dev/null 2>&1 || true

if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

MSG="daily: update ${TODAY}"
git commit -m "$MSG" >/dev/null

git push origin main >/dev/null

echo "OK: $MSG"

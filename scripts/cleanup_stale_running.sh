#!/usr/bin/env bash
set -euo pipefail

# If today's news summary is stuck at '진행중' for too long, mark it as 실패.
# This prevents the wiki from looking "forever running" after crashes/SIGKILL.

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
FILE="$BASE/news/$TODAY.md"

[ -f "$FILE" ] || exit 0

RESULT=$(grep -m1 "^- 결과:" "$FILE" | sed -E 's/^\- 결과:\s*//')
RUN_AT=$(grep -m1 "^- 실행:" "$FILE" | sed -E 's/^\- 실행:\s*//' | sed -E "s/\s*\($TZ\)\s*$//")

if [ "$RESULT" != "진행중" ]; then
  exit 0
fi

# parse RUN_AT like: YYYY-MM-DD HH:MM
RUN_EPOCH=$(TZ="$TZ" date -d "$RUN_AT" +%s 2>/dev/null || echo 0)
NOW_EPOCH=$(TZ="$TZ" date +%s)

if [ "$RUN_EPOCH" -le 0 ]; then
  exit 0
fi

AGE=$((NOW_EPOCH - RUN_EPOCH))

# 30 minutes
if [ "$AGE" -gt 1800 ]; then
  "$BASE/scripts/mark_news_status.sh" 실패 "stale: auto-marked failed (was running for ${AGE}s)" >/dev/null
fi

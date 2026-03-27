#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib_paths.sh
source "$SCRIPT_DIR/lib_paths.sh"
BASE="$(resolve_wiki_base)"
TZ="Asia/Seoul"
cd "$BASE"

TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NEWS="$BASE/news/${TODAY}.md"
LATEST_NEWS="$(find "$BASE/news" -maxdepth 1 -type f -name '20??-??-??.md' | LC_ALL=C sort | tail -n 1)"
MAX_LOG_AGE_HOURS="${MAX_LOG_AGE_HOURS:-36}"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

to_epoch() {
  local raw="$1"
  python3 - "$raw" <<'PY'
from datetime import datetime
import sys

raw = sys.argv[1].strip()
for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
    try:
        print(int(datetime.strptime(raw, fmt).timestamp()))
        raise SystemExit(0)
    except ValueError:
        pass
print(0)
PY
}

diagnose_fetch_failure() {
  local rc="$1"
  local remote_url upstream head_ref local_head origin_head

  remote_url=$(git remote get-url origin 2>/dev/null || echo "(missing)")
  upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "(none)")
  head_ref=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(unknown)")
  local_head=$(git rev-parse --short HEAD 2>/dev/null || echo "(unknown)")
  origin_head=$(git rev-parse --short origin/main 2>/dev/null || echo "(unknown)")

  {
    echo "DIAG: git fetch failed (rc=$rc)"
    echo "DIAG: branch=${head_ref} upstream=${upstream}"
    echo "DIAG: origin=${remote_url}"
    echo "DIAG: local_head=${local_head} origin_main=${origin_head}"
  } >&2

  if [ "$rc" -eq 255 ]; then
    echo "DIAG: rc=255 usually means network/auth/host-key issue. Check VPN/SSH key/token/remote URL." >&2
  fi

  if command -v timeout >/dev/null 2>&1; then
    set +e
    timeout 5 git ls-remote --heads origin main >/dev/null 2>&1
    local rc_ls=$?
    set -e
    if [ "$rc_ls" -ne 0 ]; then
      echo "DIAG: git ls-remote origin main also failed (rc=$rc_ls)." >&2
    else
      echo "DIAG: git ls-remote origin main succeeded (remote reachable)." >&2
    fi
  fi
}

if [ ! -f "$NEWS" ]; then
  if [ -z "${LATEST_NEWS:-}" ]; then
    fail "missing news file: $NEWS"
  fi
  NEWS="$LATEST_NEWS"
fi

# NOTE: this script runs with set -euo pipefail; missing grep matches must not abort.
RESULT=$(grep -m1 "^- 결과:" "$NEWS" 2>/dev/null | sed -E 's/^\- 결과:\s*//' | xargs || true)
RUN_AT=$(grep -m1 "^- 실행:" "$NEWS" 2>/dev/null | sed -E 's/^\- 실행:\s*//' | sed -E 's/\s*\([^)]*\)\s*$//' | xargs || true)
NOTE=$(grep -m1 "^- 메모:" "$NEWS" 2>/dev/null | sed -E 's/^\- 메모:\s*//' | xargs || true)

if [ -z "${RESULT:-}" ] || [ -z "${RUN_AT:-}" ]; then
  # Self-heal: some generators may rewrite today's news blocks.
  # Try to reconstruct the minimal run header and re-parse.
  python3 ./scripts/ensure_news_run_header.py >/dev/null 2>&1 || true
  RESULT=$(grep -m1 "^- 결과:" "$NEWS" 2>/dev/null | sed -E 's/^\- 결과:\s*//' | xargs || true)
  RUN_AT=$(grep -m1 "^- 실행:" "$NEWS" 2>/dev/null | sed -E 's/^\- 실행:\s*//' | sed -E 's/\s*\([^)]*\)\s*$//' | xargs || true)
  NOTE=$(grep -m1 "^- 메모:" "$NEWS" 2>/dev/null | sed -E 's/^\- 메모:\s*//' | xargs || true)
fi

if [ -z "${RESULT:-}" ] || [ -z "${RUN_AT:-}" ]; then
  fail "news header missing run/result"
fi

LOG_EPOCH=$(to_epoch "$RUN_AT")
NOW_EPOCH=$(TZ="$TZ" date +%s)
LOG_AGE_HOURS=$(( (NOW_EPOCH - LOG_EPOCH) / 3600 ))
if [ "$LOG_EPOCH" -le 0 ]; then
  fail "news timestamp parse failed: run=${RUN_AT}"
fi
if [ "$LOG_AGE_HOURS" -gt "$MAX_LOG_AGE_HOURS" ]; then
  fail "latest automation log is stale: file=$(basename "$NEWS") age=${LOG_AGE_HOURS}h threshold=${MAX_LOG_AGE_HOURS}h"
fi

# Interpret state
# - 성공: healthy
# - 진행중: healthy IF recent (avoid false alerts during long runs)
# - 부분성공/실패: unhealthy
RUN_EPOCH="$LOG_EPOCH"
AGE_RUN=$((NOW_EPOCH - RUN_EPOCH))

case "$RESULT" in
  성공) : ;;
  진행중)
    if [ "$RUN_EPOCH" -gt 0 ] && [ "$AGE_RUN" -le 2400 ]; then
      echo "OK: news=${RESULT} run=${RUN_AT} (age=${AGE_RUN}s) | automation running"
      exit 0
    fi
    fail "news status stale running: result=${RESULT} run=${RUN_AT} age=${AGE_RUN}s"
    ;;
  부분성공|실패)
    fail "news status not success: result=${RESULT} run=${RUN_AT}"
    ;;
  *)
    fail "unknown news result: ${RESULT}"
    ;;
esac

# If a run lock is present and fresh, we may be in the finalization window.
LOCK_FILE="$BASE/.locks/lock"
if [ -f "$LOCK_FILE" ]; then
  LOCK_MTIME=$(date -r "$LOCK_FILE" +%s 2>/dev/null || echo 0)
  NOW_EPOCH=$(TZ="$TZ" date +%s)
  LOCK_AGE=$((NOW_EPOCH - LOCK_MTIME))
  if [ "$LOCK_MTIME" -gt 0 ] && [ "$LOCK_AGE" -le 1200 ]; then
    echo "OK: news=${RESULT} run=${RUN_AT} | lock present (age=${LOCK_AGE}s): finalizing (treated OK)"
    exit 0
  fi
fi

# Detect stale running in history robustly.
LATEST_HIST=$(awk '
  /^## 실행 이력/{in_hist=1; next}
  in_hist && /^- /{print}
' "$NEWS" 2>/dev/null | head -n 200 || true)

if [ -n "${LATEST_HIST:-}" ]; then
  newest_line=""
  newest_epoch=0
  while IFS= read -r ln; do
    HIST_TIME=$(echo "$ln" | sed -E 's/^\- ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}).*/\1/')
    [ -z "$HIST_TIME" ] && continue
    HIST_EPOCH=$(to_epoch "$HIST_TIME")
    if [ "$HIST_EPOCH" -gt "$newest_epoch" ]; then
      newest_epoch="$HIST_EPOCH"
      newest_line="$ln"
    fi
  done <<< "$LATEST_HIST"

  if echo "$newest_line" | grep -q "· 진행중 ·"; then
    NOW_EPOCH=$(TZ="$TZ" date +%s)
    AGE=$((NOW_EPOCH - newest_epoch))
    if [ "$newest_epoch" -gt 0 ] && [ "$AGE" -gt 2400 ]; then
      fail "stale running in history: age=${AGE}s line=${newest_line}"
    fi
  fi
fi

set +e
if command -v timeout >/dev/null 2>&1; then
  timeout 15 git fetch -q origin main >/dev/null 2>&1
else
  git fetch -q origin main >/dev/null 2>&1
fi
RC_FETCH=$?
set -e
if [ $RC_FETCH -ne 0 ]; then
  diagnose_fetch_failure "$RC_FETCH"
  fail "git fetch failed (rc=$RC_FETCH)"
fi

DIRTY_FILES=$(git diff --name-only)
if [ -n "${DIRTY_FILES:-}" ]; then
  SORTED=$(echo "$DIRTY_FILES" | LC_ALL=C sort -u)
ALLOWLIST_FILE="$BASE/config/automation-generated-files.txt"
ALLOWLIST=""
if [ -f "$ALLOWLIST_FILE" ]; then
  ALLOWLIST=$(grep -vE '^\s*(#|$)' "$ALLOWLIST_FILE" || true)
fi
ALLOWLIST="${ALLOWLIST}
news/${TODAY}.md"
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    echo "$ALLOWLIST" | grep -qx "$f" || fail "working tree dirty"
  done <<< "$SORTED"
fi

HEAD=$(git rev-parse HEAD)
ORIGIN=$(git rev-parse origin/main)
if [ "$HEAD" != "$ORIGIN" ]; then
  fail "HEAD != origin/main (local not pushed?)"
fi

LAST=$(git log -1 --oneline --decorate)

echo "OK: news=${RESULT} run=${RUN_AT} | last=${LAST}"
exit 0

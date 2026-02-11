#!/usr/bin/env bash
set -euo pipefail

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
TZ="Asia/Seoul"
cd "$BASE"

TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NEWS="$BASE/news/${TODAY}.md"

fail() {
  echo "FAIL: $*" >&2
  exit 1
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
  fail "missing news file: $NEWS"
fi

RESULT=$(grep -m1 "^- 결과:" "$NEWS" | sed -E 's/^\- 결과:\s*//')
RUN_AT=$(grep -m1 "^- 실행:" "$NEWS" | sed -E 's/^\- 실행:\s*//' | sed -E 's/\s*\([^)]*\)\s*$//')
NOTE=$(grep -m1 "^- 메모:" "$NEWS" | sed -E 's/^\- 메모:\s*//')

if [ -z "${RESULT:-}" ] || [ -z "${RUN_AT:-}" ]; then
  fail "news header missing run/result"
fi

# Fail on explicit bad states
case "$RESULT" in
  성공) : ;;
  진행중|부분성공|실패)
    fail "news status not success: result=${RESULT} run=${RUN_AT}"
    ;;
  *)
    fail "unknown news result: ${RESULT}"
    ;;
esac

# Detect stale running in history (if any)
# If the latest history line is 진행중 and older than 40m -> fail
LATEST_HIST=$(awk '
  /^## 실행 이력/{in_hist=1; next}
  in_hist && /^- /{print; exit}
' "$NEWS" 2>/dev/null || true)
if echo "$LATEST_HIST" | grep -q "· 진행중 ·"; then
  # extract datetime "YYYY-MM-DD HH:MM"
  HIST_TIME=$(echo "$LATEST_HIST" | sed -E 's/^\- ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}).*/\1/')
  if [ -n "$HIST_TIME" ]; then
    HIST_EPOCH=$(TZ="$TZ" date -d "$HIST_TIME" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(TZ="$TZ" date +%s)
    AGE=$((NOW_EPOCH - HIST_EPOCH))
    if [ "$HIST_EPOCH" -gt 0 ] && [ "$AGE" -gt 2400 ]; then
      fail "stale running in history: age=${AGE}s line=${LATEST_HIST}"
    fi
  fi
fi

# Git checks
# Ensure we can talk to origin
set +e
git fetch -q origin main >/dev/null 2>&1
RC_FETCH=$?
set -e
if [ $RC_FETCH -ne 0 ]; then
  diagnose_fetch_failure "$RC_FETCH"
  fail "git fetch failed (rc=$RC_FETCH)"
fi

if ! git diff --quiet; then
  fail "working tree dirty"
fi

HEAD=$(git rev-parse HEAD)
ORIGIN=$(git rev-parse origin/main)
if [ "$HEAD" != "$ORIGIN" ]; then
  fail "HEAD != origin/main (local not pushed?)"
fi

LAST=$(git log -1 --oneline --decorate)

echo "OK: news=${RESULT} run=${RUN_AT} | last=${LAST}"
exit 0

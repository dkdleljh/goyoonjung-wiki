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

# Interpret state
# - 성공: healthy
# - 진행중: healthy IF recent (avoid false alerts during long runs)
# - 부분성공/실패: unhealthy
RUN_EPOCH=$(TZ="$TZ" date -d "$RUN_AT" +%s 2>/dev/null || echo 0)
NOW_EPOCH=$(TZ="$TZ" date +%s)
AGE_RUN=$((NOW_EPOCH - RUN_EPOCH))

case "$RESULT" in
  성공) : ;;
  진행중)
    # If still running but older than 40 minutes, consider it stale/hung.
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

# Detect stale running in history (if any)
# If the latest history line is 진행중 and older than 40m -> fail
# Detect stale running in history robustly.
# Some files may have history lines not strictly ordered; find the newest history line.
LATEST_HIST=$(awk '
  /^## 실행 이력/{in_hist=1; next}
  in_hist && /^- /{print}
' "$NEWS" 2>/dev/null | head -n 200 || true)

if [ -n "${LATEST_HIST:-}" ]; then
  # Find newest timestamp among history lines (YYYY-MM-DD HH:MM)
  newest_line=""
  newest_epoch=0
  while IFS= read -r ln; do
    t=$(echo "$ln" | sed -E 's/^\- ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}).*/\1/')
    [ -z "$t" ] && continue
    e=$(TZ="$TZ" date -d "$t" +%s 2>/dev/null || echo 0)
    if [ "$e" -gt "$newest_epoch" ]; then
      newest_epoch="$e"
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

# Allow some auto-generated files to be dirty (written by automation).
DIRTY_FILES=$(git diff --name-only)
if [ -n "${DIRTY_FILES:-}" ]; then
  # Normalize to sorted unique list
  SORTED=$(echo "$DIRTY_FILES" | LC_ALL=C sort -u)
  # NOTE: use explicit allowlist (one per line)
  ALLOWLIST=$(cat <<'EOF'
pages/system_status.md
data/content_gaps.json
pages/content-gaps.md
EOF
)
  # Check every dirty file is allowlisted
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

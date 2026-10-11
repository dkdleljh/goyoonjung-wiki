#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE"
mkdir -p .locks
exec 9>"$BASE/.locks/content-sync.lock"
flock -n 9 || exit 75
export CONTENT_SYNC_LOCK_FD=9
"$BASE/.venv/bin/python" scripts/publish_website_content.py --pull-only
# Partial collection may publish its honest status. Failed or unfinished runs cannot.
rc=0
COLLECT_ONLY=1 bash scripts/run_daily_update.sh || rc=$?
if [[ "$rc" -gt 1 ]]; then
  echo "Collection aborted (rc=$rc); website publishing skipped." >&2
  exit "$rc"
fi
"$BASE/.venv/bin/python" scripts/publish_website_content.py
# Keep partial collection visible in systemd monitoring even after a successful sync.
exit "$rc"

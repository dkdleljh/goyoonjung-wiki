#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE"
mkdir -p .locks
exec 9>"$BASE/.locks/content-sync.lock"
flock -n 9 || exit 75
export CONTENT_SYNC_LOCK_FD=9 COLLECT_ONLY=1 TZ=Asia/Seoul PUBLISH_ASYNC=1
export PATH="$BASE/.venv/bin:$BASE/scripts:$PATH"
# A GitHub outage must not stop public-source ingestion. Publishing will retry.
python3 scripts/publish_website_content.py --pull-only || true
rc=0
python3 scripts/fast_collect.py || rc=$?
if [[ "$rc" -gt 1 ]]; then exit "$rc"; fi
python3 scripts/publish_website_content.py
exit "$rc"

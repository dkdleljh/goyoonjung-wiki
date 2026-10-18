#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE"
mkdir -p .locks
exec 9>"$BASE/.locks/content-sync.lock"
flock -n 9 || exit 75
export COLLECT_ONLY=1 TZ=Asia/Seoul
exec "$BASE/.venv/bin/python" scripts/archive_backfill.py

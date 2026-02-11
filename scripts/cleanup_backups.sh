#!/usr/bin/env bash
set -euo pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
DIR="$BASE/backups"

# Keep backups for last N days (by mtime)
KEEP_DAYS="${KEEP_DAYS:-14}"

mkdir -p "$DIR"

# delete tar.gz older than KEEP_DAYS
find "$DIR" -type f -name 'goyoonjung-wiki_*.tar.gz' -mtime +"$KEEP_DAYS" -print -delete || true

echo "cleanup_backups: kept_last_days=$KEEP_DAYS"

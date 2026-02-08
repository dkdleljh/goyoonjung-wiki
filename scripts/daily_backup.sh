#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/home/zenith/바탕화면/goyoonjung-wiki"
BACKUP_DIR="$BASE_DIR/backups"

mkdir -p "$BACKUP_DIR"

STAMP=$(date +"%Y-%m-%d_%H%M" )
OUT="$BACKUP_DIR/goyoonjung-wiki_${STAMP}.tar.gz"

# Exclude git + backups to keep size sane
TarExcludes=(
  --exclude="$BASE_DIR/.git"
  --exclude="$BACKUP_DIR"
)

tar -czf "$OUT" "${TarExcludes[@]}" -C "$(dirname "$BASE_DIR")" "$(basename "$BASE_DIR")"

echo "$OUT"

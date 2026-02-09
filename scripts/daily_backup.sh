#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/home/zenith/바탕화면/goyoonjung-wiki"
BACKUP_DIR="$BASE_DIR/backups"

mkdir -p "$BACKUP_DIR"

# Make stamp consistent with the wiki timezone.
STAMP=$(TZ='Asia/Seoul' date +"%Y-%m-%d_%H%M")
OUT="$BACKUP_DIR/goyoonjung-wiki_${STAMP}.tar.gz"

# NOTE: tar sees paths relative to -C, e.g. "goyoonjung-wiki/backups/...".
# Use relative exclude patterns so the backups directory (and the output tar itself)
# are not accidentally included (which can cause: "file changed as we read it").
ROOT_NAME="$(basename "$BASE_DIR")"
TarExcludes=(
  --exclude="$ROOT_NAME/.git"
  --exclude="$ROOT_NAME/backups"
)

tar -czf "$OUT" "${TarExcludes[@]}" -C "$(dirname "$BASE_DIR")" "$ROOT_NAME"

echo "$OUT"

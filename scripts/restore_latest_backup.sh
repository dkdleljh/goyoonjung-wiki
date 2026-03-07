#!/usr/bin/env bash
set -euo pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
BACKUP_DIR="$BASE/backups"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "backup dir not found: $BACKUP_DIR" >&2
  exit 1
fi

LATEST="$(ls -1t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -n1 || true)"
if [ -z "$LATEST" ]; then
  echo "no backup archive found in $BACKUP_DIR" >&2
  exit 1
fi

echo "restore source: $LATEST"

RESTORE_ROOT="${RESTORE_ROOT:-$BASE}"
TMP_DIR="${TMPDIR:-/tmp}/goyoonjung-wiki-restore-$$"
mkdir -p "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

tar -xzf "$LATEST" -C "$TMP_DIR"

SRC_DIR="$(find "$TMP_DIR" -maxdepth 1 -type d -name 'goyoonjung-wiki*' | head -n1 || true)"
if [ -z "$SRC_DIR" ]; then
  echo "restored root not found in archive" >&2
  exit 1
fi

for item in pages scripts config sources data README.md index.md config.yaml requirements.txt requirements-dev.txt; do
  if [ -e "$SRC_DIR/$item" ]; then
    rm -rf "$RESTORE_ROOT/$item"
    cp -a "$SRC_DIR/$item" "$RESTORE_ROOT/$item"
    echo "restored: $item"
  fi
done

echo "restore complete"

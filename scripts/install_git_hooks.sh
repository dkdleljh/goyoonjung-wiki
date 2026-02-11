#!/usr/bin/env bash
set -euo pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

HOOKS_DIR="$BASE/.git/hooks"
SRC_DIR="$BASE/scripts/git-hooks"

mkdir -p "$HOOKS_DIR"

install_one() {
  local name="$1"
  local src="$SRC_DIR/$name"
  local dst="$HOOKS_DIR/$name"
  if [ ! -f "$src" ]; then
    echo "ERR: missing hook source: $src" >&2
    exit 2
  fi
  cp -f "$src" "$dst"
  chmod +x "$dst"
  echo "installed: $dst"
}

install_one post-push

echo "OK: git hooks installed"

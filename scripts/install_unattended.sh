#!/usr/bin/env bash
set -euo pipefail
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="${GOYOONJUNG_RUNTIME:-$HOME/.local/share/goyoonjung-runtime/goyoonjung-wiki}"
mkdir -p "$(dirname "$RUNTIME")"
if [[ ! -d "$RUNTIME/.git" ]]; then
  git -c core.hooksPath=/dev/null clone --branch main https://github.com/dkdleljh/goyoonjung-wiki.git "$RUNTIME"
fi
if [[ -n "$(git -C "$RUNTIME" status --porcelain)" ]]; then
  echo 'Runtime has pending content; publish or recover it before reinstalling.' >&2
  exit 1
fi
git -c core.hooksPath=/dev/null -C "$RUNTIME" pull --ff-only
git -C "$RUNTIME" config core.hooksPath /dev/null
git -C "$RUNTIME" config user.name 'goyoonjung-wiki automation'
git -C "$RUNTIME" config user.email '41898282+github-actions[bot]@users.noreply.github.com'
if [[ ! -e "$RUNTIME/.venv" ]]; then ln -s "$SOURCE/.venv" "$RUNTIME/.venv"; fi
mkdir -p "$RUNTIME/.locks" "$RUNTIME/data" "$RUNTIME/.cache"
if [[ -d "$SOURCE/.cache/news-decodes" && ! -d "$RUNTIME/.cache/news-decodes" ]]; then
  cp -a "$SOURCE/.cache/news-decodes" "$RUNTIME/.cache/"
fi
if [[ ! -f "$RUNTIME/data/wiki.db" ]]; then
  "$SOURCE/.venv/bin/python" "$RUNTIME/scripts/remote_backup.py" --restore-database || true
fi
if [[ ! -f "$RUNTIME/data/wiki.db" ]]; then
  "$SOURCE/.venv/bin/python" - "$SOURCE" "$RUNTIME" <<'PY'
import sqlite3, sys
from pathlib import Path
source, target = map(Path, sys.argv[1:])
with sqlite3.connect(f'file:{source}/data/wiki.db?mode=ro', uri=True) as old, sqlite3.connect(target/'data/wiki.db') as new:
    old.backup(new)
PY
fi
mkdir -p "$HOME/.config/systemd/user"
for name in daily sync backup; do
  cp "$RUNTIME/deploy/systemd/goyoonjung-wiki-$name.service" "$HOME/.config/systemd/user/"
  cp "$RUNTIME/deploy/systemd/goyoonjung-wiki-$name.timer" "$HOME/.config/systemd/user/"
done
systemctl --user daemon-reload
systemctl --user enable --now goyoonjung-wiki-daily.timer goyoonjung-wiki-sync.timer goyoonjung-wiki-backup.timer
systemctl --user list-timers 'goyoonjung-wiki-*' --no-pager

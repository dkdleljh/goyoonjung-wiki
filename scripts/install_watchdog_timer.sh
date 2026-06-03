#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
cp "$BASE/deploy/systemd/user/goyoonjung-wiki-watchdog.service" "$UNIT_DIR/"
cp "$BASE/deploy/systemd/user/goyoonjung-wiki-watchdog.timer" "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now goyoonjung-wiki-watchdog.timer
systemctl --user list-timers --all 'goyoonjung-wiki-watchdog.timer' --no-pager

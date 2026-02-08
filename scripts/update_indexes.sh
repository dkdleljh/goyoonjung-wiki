#!/usr/bin/env bash
set -euo pipefail

/home/zenith/바탕화면/goyoonjung-wiki/scripts/rebuild_recent_summary.sh >/dev/null
/home/zenith/바탕화면/goyoonjung-wiki/scripts/rebuild_tag_index.sh >/dev/null
/home/zenith/바탕화면/goyoonjung-wiki/scripts/rebuild_schedule_highlights.py >/dev/null || true
/home/zenith/바탕화면/goyoonjung-wiki/scripts/mark_backlog_progress.sh >/dev/null || true

echo "OK"

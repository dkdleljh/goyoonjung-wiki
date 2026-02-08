#!/usr/bin/env bash
set -euo pipefail

/home/zenith/바탕화면/goyoonjung-wiki/scripts/rebuild_recent_summary.sh >/dev/null
/home/zenith/바탕화면/goyoonjung-wiki/scripts/rebuild_tag_index.sh >/dev/null
/home/zenith/바탕화면/goyoonjung-wiki/scripts/rebuild_schedule_highlights.py >/dev/null || true

echo "OK"

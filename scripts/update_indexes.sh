#!/usr/bin/env bash
set -euo pipefail

# Resolve BASE directory relative to this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE="$( cd "$SCRIPT_DIR/.." && pwd )"

"$SCRIPT_DIR/update_index_last_updated.py" >/dev/null || true
"$SCRIPT_DIR/update_readme_today_links.py" >/dev/null || true
"$SCRIPT_DIR/rebuild_recent_summary.sh" >/dev/null
"$SCRIPT_DIR/rebuild_tag_index.py" >/dev/null
"$SCRIPT_DIR/rebuild_schedule_highlights.py" >/dev/null || true
"$SCRIPT_DIR/rebuild_group_link_candidates.py" >/dev/null || true
"$SCRIPT_DIR/update_backlog_checkboxes.sh" >/dev/null || true
"$SCRIPT_DIR/mark_backlog_progress.sh" >/dev/null || true

# rebuild_progress.py often needs BASE or might import modules, run from BASE
(cd "$BASE" && "$SCRIPT_DIR/rebuild_progress.py") >/dev/null || true

"$SCRIPT_DIR/rebuild_daily_report.sh" >/dev/null || true
"$SCRIPT_DIR/rebuild_quality_report.py" >/dev/null || true
"$SCRIPT_DIR/wiki_score.py" >/dev/null || true
"$SCRIPT_DIR/rebuild_year_indexes.py" >/dev/null || true
"$SCRIPT_DIR/rebuild_endorsements_year_index.py" >/dev/null || true

# Reference lists
"$SCRIPT_DIR/collect_awards_official_pages.py" >/dev/null || true

echo "OK"

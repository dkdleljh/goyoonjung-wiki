#!/usr/bin/env bash
set -euo pipefail

# Writes a one-line progress summary into today's news file.
# Source checklist: pages/namu-backlog.md

TZ="Asia/Seoul"
BASE="/Users/zenith/Documents/goyoonjung-wiki"
BACKLOG="$BASE/pages/namu-backlog.md"
NEWS_DIR="$BASE/news"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NEWS="$NEWS_DIR/$TODAY.md"

START="<!-- AUTO-BACKLOG-PROGRESS:START -->"
END="<!-- AUTO-BACKLOG-PROGRESS:END -->"

mkdir -p "$NEWS_DIR"

if [ ! -f "$BACKLOG" ]; then
  echo "ERR: backlog missing: $BACKLOG" >&2
  exit 2
fi

# count checkboxes
TOTAL=$( (grep -E "^- \[[ xX]\]" "$BACKLOG" || true) | wc -l | tr -d ' ')
DONE=$( (grep -E "^- \[[xX]\]" "$BACKLOG" || true) | wc -l | tr -d ' ')

PCT=0
if [ "$TOTAL" -gt 0 ]; then
  PCT=$(( DONE * 100 / TOTAL ))
fi

LINE="- C(완성도 우선) 백로그 진행률: ${DONE}/${TOTAL} (${PCT}%)"
BLOCK=$(printf "%s\n%s\n%s" "$START" "$LINE" "$END")

# Ensure news file exists
if [ ! -f "$NEWS" ]; then
  {
    echo "# $TODAY 업데이트"
    echo
    echo "## 실행 상태"
    echo "- 실행: (자동)"
    echo "- 결과: 진행중"
    echo "- 메모:"
    echo
  } > "$NEWS"
fi

CONTENT=$(cat "$NEWS")

if grep -q "$START" "$NEWS" && grep -q "$END" "$NEWS"; then
  # Replace existing block (without perl): rewrite file and replace the marked region.
  awk -v start="$START" -v end="$END" -v block="$BLOCK" '
    BEGIN{skip=0}
    $0==start {print block; skip=1; next}
    skip==1 && $0==end {skip=0; next}
    skip==1 {next}
    {print}
  ' "$NEWS" > "$NEWS.tmp" && mv "$NEWS.tmp" "$NEWS"
else
  # Insert right after '## 실행 상태' section (after 메모 line if present), else near top.
  if grep -q "^## 실행 상태" "$NEWS"; then
    # Insert after first occurrence of '- 메모:' line if present; else after 결과 line.
    if grep -q "^- 메모:" "$NEWS"; then
      awk -v block="$BLOCK" '
        {print}
        $0 ~ /^- 메모:/ && inserted==0 {print block; inserted=1}
      ' "$NEWS" > "$NEWS.tmp" && mv "$NEWS.tmp" "$NEWS"
    else
      awk -v block="$BLOCK" '
        {print}
        $0 ~ /^- 결과:/ && inserted==0 {print block; inserted=1}
      ' "$NEWS" > "$NEWS.tmp" && mv "$NEWS.tmp" "$NEWS"
    fi
  else
    # Fallback: insert after title line
    tmp=$(mktemp)
    { head -n 1 "$NEWS"; echo; echo "$BLOCK"; echo; tail -n +2 "$NEWS"; } > "$tmp"
    mv "$tmp" "$NEWS"
  fi
fi

echo "$NEWS"

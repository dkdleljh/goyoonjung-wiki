#!/usr/bin/env bash
set -euo pipefail

# Usage: mark_news_status.sh <status> [note]
# status: 진행중|성공|부분성공|실패
#
# Behavior:
# - Maintains a single up-to-date summary block under "## 실행 상태"
# - Appends every call as a line under "## 실행 이력" (audit trail)

STATUS="${1:-}"
NOTE="${2:-}"
TZ="Asia/Seoul"

BASE="/Users/zenith/Documents/goyoonjung-wiki"
NEWS_DIR="$BASE/news"

if [ -z "$STATUS" ]; then
  echo "ERR: missing status" >&2
  exit 2
fi

TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")
FILE="$NEWS_DIR/$TODAY.md"

mkdir -p "$NEWS_DIR"

esc_repl() {
  # Escape backslashes and ampersands (sed replacement special chars)
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/&/\\&/g'
}

ensure_sections() {
  # Create file if missing, with both sections.
  if [ ! -f "$FILE" ]; then
    {
      echo "# $TODAY 업데이트"
      echo
      echo "## 실행 상태"
      echo "- 실행: $NOW ($TZ)"
      echo "- 결과: $STATUS"
      echo "- 메모: ${NOTE:-}"
      echo
      echo "## 실행 이력"
      echo "- $NOW ($TZ) · $STATUS · ${NOTE:-}"
      echo
    } > "$FILE"
    return
  fi

  # Ensure summary exists.
  if ! grep -q "^## 실행 상태" "$FILE"; then
    tmp=$(mktemp)
    {
      head -n 1 "$FILE"
      echo
      echo "## 실행 상태"
      echo "- 실행: $NOW ($TZ)"
      echo "- 결과: $STATUS"
      echo "- 메모: ${NOTE:-}"
      echo
      tail -n +2 "$FILE"
    } > "$tmp"
    mv "$tmp" "$FILE"
  fi

  # Ensure history section exists (append near top, after 실행 상태 block if possible)
  if ! grep -q "^## 실행 이력" "$FILE"; then
    # Insert right after the 실행 상태 block (after the first blank line following 메모)
    tmp=$(mktemp)
    awk '
      BEGIN{ins=0; in_status=0}
      /^## 실행 상태/{in_status=1}
      in_status && /^$/{
        if(!ins){
          print "## 실행 이력";
          print "";
          ins=1
        }
        in_status=0
      }
      {print}
      END{
        if(!ins){
          print "";
          print "## 실행 이력";
          print "";
        }
      }
    ' "$FILE" > "$tmp"
    mv "$tmp" "$FILE"
  fi
}

ensure_sections

# Update summary (always)
NOW_ESC=$(esc_repl "$NOW ($TZ)")
STATUS_ESC=$(esc_repl "$STATUS")
NOTE_ESC=$(esc_repl "${NOTE:-}")

sed -i '' -E "s|^(- 실행: ).*$|\\1${NOW_ESC}|" "$FILE"
sed -i '' -E "s|^(- 결과: ).*$|\\1${STATUS_ESC}|" "$FILE"
if grep -q "^- 메모:" "$FILE"; then
  sed -i '' -E "s|^(- 메모: ).*$|\\1${NOTE_ESC}|" "$FILE"
else
  sed -i '' -E "/^- 결과:/a\\
- 메모: ${NOTE_ESC}\\
" "$FILE"
fi

# Append history line (always)
LINE="- $NOW ($TZ) · $STATUS · ${NOTE:-}"
# shellcheck disable=SC2016
awk -v line="$LINE" '
  {print}
  $0 ~ /^## 실행 이력/ {
    getline; print; print line; next
  }
' "$FILE" > "$FILE.tmp" && mv "$FILE.tmp" "$FILE"

echo "$FILE"

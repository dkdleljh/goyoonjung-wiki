#!/usr/bin/env bash
set -euo pipefail

# Usage: mark_news_status.sh <status> [note]
# status: 진행중|성공|부분성공|실패

STATUS="${1:-}"
NOTE="${2:-}"
TZ="Asia/Seoul"

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
NEWS_DIR="$BASE/news"

if [ -z "$STATUS" ]; then
  echo "ERR: missing status" >&2
  exit 2
fi

# Today in Asia/Seoul
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")
FILE="$NEWS_DIR/$TODAY.md"

mkdir -p "$NEWS_DIR"

if [ ! -f "$FILE" ]; then
  {
    echo "# $TODAY 업데이트"
    echo
    echo "## 실행 상태"
    echo "- 실행: $NOW ($TZ)"
    echo "- 결과: $STATUS"
    if [ -n "$NOTE" ]; then
      echo "- 메모: $NOTE"
    else
      echo "- 메모:"
    fi
    echo
  } > "$FILE"
  echo "$FILE"
  exit 0
fi

# Ensure the section exists; if not, insert after first header.
if ! grep -q "^## 실행 상태" "$FILE"; then
  tmp=$(mktemp)
  {
    # print first line (title)
    head -n 1 "$FILE"
    echo
    echo "## 실행 상태"
    echo "- 실행: $NOW ($TZ)"
    echo "- 결과: $STATUS"
    if [ -n "$NOTE" ]; then
      echo "- 메모: $NOTE"
    else
      echo "- 메모:"
    fi
    echo
    tail -n +2 "$FILE"
  } > "$tmp"
  mv "$tmp" "$FILE"
else
  # Replace 실행/결과, and optionally 메모 if NOTE provided.
  sed -i -E "s/^(- 실행: ).*$/\1$NOW ($TZ)/" "$FILE"
  sed -i -E "s/^(- 결과: ).*$/\1$STATUS/" "$FILE"
  if [ -n "$NOTE" ]; then
    if grep -q "^- 메모:" "$FILE"; then
      sed -i -E "s/^(- 메모: ).*$/\1$NOTE/" "$FILE"
    else
      # append memo under the section
      awk -v note="$NOTE" '
        {print}
        $0=="## 실행 상태" {insec=1; next}
      ' "$FILE" >/dev/null
      # simple append near section end (after 결과 line)
      sed -i -E "/^- 결과:/a - 메모: $NOTE" "$FILE"
    fi
  fi
fi

echo "$FILE"

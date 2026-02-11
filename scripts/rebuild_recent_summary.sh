#!/usr/bin/env bash
set -euo pipefail
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
NEWS="$BASE/news"
OUT="$NEWS/README.md"

# Find last 7 news files by name (YYYY-MM-DD.md), descending
{
  echo "# news/"
  echo
  echo "날짜별 자동 업데이트 로그입니다. 파일명은 \`YYYY-MM-DD.md\`."
  echo
  echo "## 최근 7일 요약"

  found=0
  ls -1 "$NEWS"/*.md 2>/dev/null | grep -E '/[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' | sort -r | head -n 7 | while read -r f; do
      found=1
      bn=$(basename "$f" .md)
      # Take first non-empty bullet under the title section as a mini summary, fallback to file link only
      summary=$(awk 'NF{print; exit}' "$f" | tr -d '\r')
      echo "- [$bn]($bn.md)"
  done

  # If nothing printed by the loop (files empty or no match), we handle that check differently or assume if ls fails loop doesn't run.
  # Since found variable won't bubble up from pipe easily in bash 3.2 without shopt lastpipe...
  # A simple check: if no files in glob, ls fails or grep fails.
  if ! ls "$NEWS"/*.md >/dev/null 2>&1; then
      echo "- (아직 로그가 없습니다.)"
  fi
} > "$OUT"

echo "$OUT"

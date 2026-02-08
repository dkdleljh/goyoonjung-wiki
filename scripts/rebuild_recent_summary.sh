#!/usr/bin/env bash
set -euo pipefail
BASE="/home/zenith/바탕화면/goyoonjung-wiki"
NEWS="$BASE/news"
OUT="$NEWS/README.md"

# Find last 7 news files by name (YYYY-MM-DD.md), descending
mapfile -t files < <(ls -1 "$NEWS"/*.md 2>/dev/null | grep -E '/[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' | sort -r | head -n 7 || true)

{
  echo "# news/"
  echo
  echo "날짜별 자동 업데이트 로그입니다. 파일명은 \`YYYY-MM-DD.md\`."
  echo
  echo "## 최근 7일 요약"
  if [ ${#files[@]} -eq 0 ]; then
    echo "- (아직 로그가 없습니다.)"
  else
    for f in "${files[@]}"; do
      bn=$(basename "$f" .md)
      # Take first non-empty bullet under the title section as a mini summary, fallback to file link only
      summary=$(awk 'NF{print; exit}' "$f" | tr -d '\r')
      echo "- [$bn]($bn.md)"
    done
  fi
} > "$OUT"

echo "$OUT"

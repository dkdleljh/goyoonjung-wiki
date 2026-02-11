#!/usr/bin/env bash
set -euo pipefail
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
OUT="$BASE/pages/index-by-tag.md"

# Collect "키워드:" lines and map keywords -> files
# Format expected: "키워드: a, b, c"

declare -A tag_to_files

while IFS= read -r -d '' file; do
  # get all keyword lines
  while IFS= read -r line; do
    # strip prefix
    kw=${line#키워드:}
    # split by comma
    IFS=',' read -ra arr <<< "$kw"
    for t in "${arr[@]}"; do
      t=$(echo "$t" | sed 's/^ *//; s/ *$//')
      [ -z "$t" ] && continue
      rel=${file#"$BASE/pages/"}
      tag_to_files["$t"]+="$rel\n"
    done
  done < <(grep -h "^키워드:" "$file" 2>/dev/null || true)

done < <(find "$BASE/pages" -type f -name "*.md" -print0)

{
  echo "# 태그 인덱스"
  echo
  echo "> 자동 생성 파일입니다. (스크립트: scripts/rebuild_tag_index.sh)"
  echo
  echo "## 태그 목록"

  # sort tags (safe iteration: preserve spaces)
  printf "%s\n" "${!tag_to_files[@]}" | LC_ALL=C sort | while IFS= read -r tag; do
    [ -z "$tag" ] && continue
    echo "### $tag"
    # unique + sort files
    printf "%b" "${tag_to_files["$tag"]-}" | sort -u | while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      name=$(basename "$rel" .md)
      echo "- [$name]($rel)"
    done
    echo
  done
} > "$OUT"

echo "$OUT"

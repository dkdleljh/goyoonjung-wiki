#!/usr/bin/env bash
set -euo pipefail

# Heuristically auto-check items in pages/namu-backlog.md based on current wiki contents.
# Goal: make backlog progress reflect reality without manual checkbox edits.

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
BACKLOG="$BASE/pages/namu-backlog.md"

[ -f "$BACKLOG" ] || { echo "ERR: missing $BACKLOG" >&2; exit 2; }

# --- Heuristics ---
# endorsements: count items across three files
count_endorsements() {
  local n=0
  for f in "$BASE/pages/endorsements/beauty.md" "$BASE/pages/endorsements/fashion.md" "$BASE/pages/endorsements/lifestyle.md"; do
    [ -f "$f" ] || continue
    n=$(( n + $(grep -c "^- 브랜드/회사명" "$f" || true) ))
  done
  echo "$n"
}

# pictorials: count entries across cover/editorial/campaign/making
count_pictorials() {
  local n=0
  for f in "$BASE/pages/pictorials/cover.md" "$BASE/pages/pictorials/editorial.md" "$BASE/pages/pictorials/campaign.md" "$BASE/pages/pictorials/making.md"; do
    [ -f "$f" ] || continue
    n=$(( n + $(grep -c "^- 날짜:" "$f" || true) ))
  done
  echo "$n"
}

# appearances: entries beyond template
count_appearances() {
  local f="$BASE/pages/appearances.md"
  [ -f "$f" ] || { echo 0; return; }
  grep -c "^- 날짜:" "$f" || true
}

# works link box: consider done if each works page has at least one non-empty URL in '## 링크 박스' section
works_linkbox_done() {
  local ok=1
  for f in "$BASE"/pages/works/*.md; do
    [ -f "$f" ] || continue
    # Grab 15 lines after '## 링크 박스' and see if any http(s) url exists
    if ! awk 'found && c<20 {print; c++} /^## 링크 박스/{found=1; c=0}' "$f" | grep -Eq "https?://"; then
      ok=0
      break
    fi
  done
  echo "$ok"
}

ENDORSE=$(count_endorsements)
PICT=$(count_pictorials)
APPR=$(count_appearances)
WORKS_OK=$(works_linkbox_done)

# --- Update backlog checkboxes ---
# We only auto-check items when a minimal threshold is met.
# Thresholds are conservative to avoid false completion.
#
# - endorsements overall expansion: >= 10 items
# - pictorials overall expansion: >= 5 items
# - appearances expansion: >= 5 items
# - works link box: all works pages have at least one official link

TMP=$(mktemp)

while IFS= read -r line; do
  case "$line" in
    "- [ ] 광고/엠버서더 전체 확장"*)
      if [ "$ENDORSE" -ge 10 ]; then
        echo "- [x] 광고/엠버서더 전체 확장 (현재: ${ENDORSE}개 항목)" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] 화보/사진 전체 확장"*)
      if [ "$PICT" -ge 5 ]; then
        echo "- [x] 화보/사진 전체 확장 (현재: ${PICT}개 항목)" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] 방송/예능/행사/시상식 출연 기록 확장"*)
      if [ "$APPR" -ge 5 ]; then
        echo "- [x] 방송/예능/행사/시상식 출연 기록 확장 (현재: ${APPR}개 항목)" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] 작품별 페이지 링크 박스 보강"*)
      if [ "$WORKS_OK" -eq 1 ]; then
        echo "- [x] 작품별 페이지 링크 박스 보강" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    *)
      echo "$line" >> "$TMP"
      ;;
  esac

done < "$BACKLOG"

mv "$TMP" "$BACKLOG"

echo "$BACKLOG"

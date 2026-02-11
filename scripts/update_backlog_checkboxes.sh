#!/usr/bin/env bash
set -euo pipefail

# Heuristically auto-check items in pages/namu-backlog.md based on current wiki contents.
# Goal: make backlog progress reflect reality without manual checkbox edits.

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
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

# Targeted detectors
has_vogue_editorial() {
  local f="$BASE/pages/pictorials/editorial.md"
  [ -f "$f" ] || { echo 0; return; }
  grep -Eq "vogue\.co\.kr" "$f" && echo 1 || echo 0
}

has_campaign_entry() {
  local f="$BASE/pages/pictorials/campaign.md"
  [ -f "$f" ] || { echo 0; return; }
  # at least 1 official-confirmed entry with a URL
  awk 'BEGIN{ok=0} /^- 상태:/{st=$0} /^- 링크\(원문\):/{if(st ~ /공식확정/ && $0 ~ /https?:\/\//) ok=1} END{print ok}' "$f"
}

has_making_entry() {
  local f="$BASE/pages/pictorials/making.md"
  [ -f "$f" ] || { echo 0; return; }
  grep -Eq "^- 날짜: .*" "$f" && echo 1 || echo 0
}

has_mv_entry() {
  local f="$BASE/pages/appearances.md"
  [ -f "$f" ] || { echo 0; return; }
  grep -Eqi "뮤직비디오|\bMV\b" "$f" && echo 1 || echo 0
}

awards_has_official_proof() {
  local f="$BASE/pages/awards.md"
  [ -f "$f" ] || { echo 0; return; }
  # heuristics: at least one row contains an official-looking URL (baeksang/blueaward/daejong etc)
  grep -Eqi "https?://(www\.)?(baeksangawards\.co\.kr|bsa\.blueaward\.co\.kr|blueaward\.co\.kr|daejong\.or\.kr)" "$f" && echo 1 || echo 0
}

schedule_has_upcoming() {
  local f="$BASE/pages/schedule.md"
  [ -f "$f" ] || { echo 0; return; }
  # any explicit Upcoming marker
  grep -Eq "^## +Upcoming|\bUpcoming\b" "$f" && echo 1 || echo 0
}

VOGUE_OK=$(has_vogue_editorial)
CAMP_OK=$(has_campaign_entry)
MAKING_OK=$(has_making_entry)
MV_OK=$(has_mv_entry)
AWARDS_OK=$(awards_has_official_proof)
SCHED_OK=$(schedule_has_upcoming)

# --- Update backlog checkboxes ---
# We only auto-check items when a minimal threshold is met.
# Thresholds are conservative to avoid false completion.
#
# Existing (broad) thresholds:
# - endorsements overall expansion: >= 10 items
# - pictorials overall expansion: >= 5 items
# - appearances expansion: >= 5 items
# - works link box: all works pages have at least one official link
#
# Additional (targeted) heuristics for stalled progress:
# - Vogue/캠페인/메이킹: detect at least 1 matching entry in the target pages
# - awards official proof: detect at least 1 official proof URL in awards table
# - schedule: detect at least 1 Upcoming line
# - MV: detect at least 1 MV/뮤직비디오 entry in appearances

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
    "- [ ] (화보) Vogue Korea 원문 1건 확보"*)
      if [ "$VOGUE_OK" -eq 1 ]; then
        printf '%s\n' "- [x] (화보) Vogue Korea 원문 1건 확보 → pages/pictorials/editorial.md 착지" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] (캠페인) 브랜드 캠페인/룩북 원문 1건 확보"*)
      if [ "$CAMP_OK" -eq 1 ]; then
        printf '%s\n' "- [x] (캠페인) 브랜드 캠페인/룩북 원문 1건 확보 → pages/pictorials/campaign.md 착지" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] (메이킹) 공식 유튜브/매거진 메이킹 1건 확보"*)
      if [ "$MAKING_OK" -eq 1 ]; then
        printf '%s\n' "- [x] (메이킹) 공식 유튜브/매거진 메이킹 1건 확보 → pages/pictorials/making.md 착지" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] (MV) 공식 MV 링크 1건 확보"*)
      if [ "$MV_OK" -eq 1 ]; then
        printf '%s\n' "- [x] (MV) 공식 MV 링크 1건 확보 → pages/appearances.md (구분: 기타/MV)" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] (수상) 공식 시상식 페이지 1건에서 고윤정 항목/작품 후보 근거 확보"*)
      if [ "$AWARDS_OK" -eq 1 ]; then
        printf '%s\n' "- [x] (수상) 공식 시상식 페이지 1건에서 고윤정 항목/작품 후보 근거 확보 → pages/awards.md" >> "$TMP"
      else
        echo "$line" >> "$TMP"
      fi
      ;;
    "- [ ] (스케줄) 공개/방영/행사 등 공식 일정 1건 확보"*)
      if [ "$SCHED_OK" -eq 1 ]; then
        printf '%s\n' "- [x] (스케줄) 공개/방영/행사 등 공식 일정 1건 확보 → pages/schedule.md Upcoming/Past 정리" >> "$TMP"
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

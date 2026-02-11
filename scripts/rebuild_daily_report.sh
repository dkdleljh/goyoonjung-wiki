#!/usr/bin/env bash
set -euo pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"
TZ="Asia/Seoul"
TODAY=$(TZ="$TZ" date +"%Y-%m-%d")
NOW=$(TZ="$TZ" date +"%Y-%m-%d %H:%M")

OUT="pages/daily-report.md"
NEWS="news/${TODAY}.md"

LAST_COMMIT=$(git log -1 --format='%h %ad %s' --date=iso || true)
CHANGED=$(git show --name-only --pretty=format: HEAD | sed '/^$/d' | sed -n '1,120p' || true)

{
  echo "# 데일리 리포트"
  echo
  echo "> 갱신: ${NOW} (${TZ})"
  echo
  echo "## 1) 최신 커밋"
  echo
  echo "- ${LAST_COMMIT}"
  echo
  echo "## 2) 변경 파일(최근 커밋 기준)"
  echo
  if [ -n "${CHANGED}" ]; then
    echo "${CHANGED}" | sed 's/^/- /'
  else
    echo "- (없음)"
  fi
  echo
  echo "## 3) 오늘 실행 상태(news/${TODAY}.md)"
  echo
  if [ -f "${NEWS}" ]; then
    # include summary + history headers only
    awk '
      /^## 실행 상태/{p=1}
      /^## 변경 사항/{p=0}
      p{print}
    ' "${NEWS}" | sed -n '1,120p'
  else
    echo "- (오늘 news 파일 없음)"
  fi
  echo
  echo "## 4) 권장 체크"
  echo
  echo "- 자동 09시 실행이 잘 됐는지(09:25 모니터 보고)"
  echo "- 백로그 1개 전진 여부(pages/progress.md)"
  echo "- 링크 건강검진 주간 실행(pages/link-health.md)"
  echo
} > "${OUT}"

echo "${OUT}"

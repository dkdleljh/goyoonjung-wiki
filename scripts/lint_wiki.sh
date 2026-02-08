#!/usr/bin/env bash
set -euo pipefail
BASE="/home/zenith/바탕화면/goyoonjung-wiki"
cd "$BASE"

REPORT="pages/lint-report.md"

{
  echo "# 위키 점검 리포트"
  echo
  echo "> 생성: $(date +"%Y-%m-%d %H:%M" ) (Asia/Seoul)"
  echo

  echo "## 1) 빈 링크(\"공식 페이지:\" 등 콜론 뒤가 비어있는 줄)"
  echo
  grep -RIn --exclude-dir=.git --exclude="*.tar.gz" --exclude="lint-report.md" -E "(공식 페이지|링크)\s*:\s*$" pages || echo "- 없음"
  echo

  echo "## 2) 상태 태그 누락(인터뷰/화보/광고 템플릿 준수 여부)"
  echo
  echo "### interviews.md에서 '상태:' 없는 항목(간단 체크)"
  if grep -n "^- 날짜:" -n pages/interviews.md >/dev/null 2>&1; then
    awk 'BEGIN{d=0} /^- 날짜:/{d=1} d==1 && /^- 상태:/{d=0} END{}' pages/interviews.md >/dev/null 2>&1 || true
  fi
  echo "- 수동 확인 권장(항목별 상태 태그는 사람이 최종 확인)"
  echo

  echo "## 3) 날짜 형식(YYYY-MM-DD) 의심 라인"
  echo
  grep -RIn --exclude-dir=.git --exclude="*.tar.gz" --exclude="lint-report.md" -E "[0-9]{4}\.[0-9]{2}\.[0-9]{2}" . || echo "- 없음"
  echo
} > "$REPORT"

echo "$REPORT"

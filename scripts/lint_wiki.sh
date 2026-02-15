#!/usr/bin/env bash
set -euo pipefail
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

REPORT="pages/lint-report.md"

{
  echo "# 위키 점검 리포트"
  echo
  # Note: we avoid timestamps here so the report doesn't change when findings don't change
  echo "> 생성: (자동 생성)"
  echo

  echo "## 0) 커버리지(요약)"
  echo
  end_b=$(grep -c "^- 브랜드/회사명" pages/endorsements/beauty.md 2>/dev/null || true)
  end_f=$(grep -c "^- 브랜드/회사명" pages/endorsements/fashion.md 2>/dev/null || true)
  end_l=$(grep -c "^- 브랜드/회사명" pages/endorsements/lifestyle.md 2>/dev/null || true)
  pic_c=$(grep -c "^- 날짜:" pages/pictorials/cover.md 2>/dev/null || true)
  pic_e=$(grep -c "^- 날짜:" pages/pictorials/editorial.md 2>/dev/null || true)
  pic_ca=$(grep -c "^- 날짜:" pages/pictorials/campaign.md 2>/dev/null || true)
  pic_m=$(grep -c "^- 날짜:" pages/pictorials/making.md 2>/dev/null || true)
  app=$(grep -c "^- 날짜:" pages/appearances.md 2>/dev/null || true)
  itv=$(grep -c "^- 날짜:" pages/interviews.md 2>/dev/null || true)
  echo "- 광고/엠버서더: 뷰티 $end_b / 패션 $end_f / 라이프 $end_l"
  echo "- 화보/사진: 커버 $pic_c / 에디토리얼 $pic_e / 캠페인 $pic_ca / 메이킹 $pic_m"
  echo "- 출연/행사: $app"
  echo "- 인터뷰/기사: $itv"
  echo

  echo "## 1) 빈 링크(\"공식 페이지:\" 등 콜론 뒤가 비어있는 줄)"
  echo
  # Exclude templates/ because they intentionally contain blanks.
  grep -RIn --exclude-dir=.git --exclude-dir=templates --exclude="*.tar.gz" --exclude="lint-report.md" -E "(공식 페이지|링크)\s*:\s*$" pages || echo "- 없음"
  echo

  echo "## 2) 상태 태그 누락(인터뷰/화보/광고 템플릿 준수 여부)"
  echo
  echo "### interviews.md에서 '상태:' 없는 항목(간단 체크)"
  echo "- 수동 확인 권장(항목별 상태 태그는 사람이 최종 확인)"
  echo

  echo "## 3) 날짜 형식(YYYY-MM-DD) 의심 라인"
  echo
  grep -RIn --exclude-dir=.git --exclude="*.tar.gz" --exclude="lint-report.md" -E "[0-9]{4}\.[0-9]{2}\.[0-9]{2}" . || echo "- 없음"
  echo

  echo "## 4) 커버리지 목표 미달 경고(권장)"
  echo
  # Coverage targets (tunable). Defaults are set to current baseline so the report focuses on real regressions.
  END_B_TARGET=${END_B_TARGET:-5}
  END_F_TARGET=${END_F_TARGET:-5}
  END_L_TARGET=${END_L_TARGET:-5}
  PIC_C_TARGET=${PIC_C_TARGET:-2}
  PIC_E_TARGET=${PIC_E_TARGET:-3}
  APP_TARGET=${APP_TARGET:-3}

  warn=0
  if [ "$end_b" -lt "$END_B_TARGET" ]; then echo "- 경고: endorsements/beauty.md 항목이 ${END_B_TARGET}개 미만입니다."; warn=1; fi
  if [ "$end_f" -lt "$END_F_TARGET" ]; then echo "- 경고: endorsements/fashion.md 항목이 ${END_F_TARGET}개 미만입니다."; warn=1; fi
  if [ "$end_l" -lt "$END_L_TARGET" ]; then echo "- 경고: endorsements/lifestyle.md 항목이 ${END_L_TARGET}개 미만입니다."; warn=1; fi
  if [ "$pic_c" -lt "$PIC_C_TARGET" ]; then echo "- 경고: pictorials/cover.md 항목이 ${PIC_C_TARGET}개 미만입니다."; warn=1; fi
  if [ "$pic_e" -lt "$PIC_E_TARGET" ]; then echo "- 경고: pictorials/editorial.md 항목이 ${PIC_E_TARGET}개 미만입니다."; warn=1; fi
  if [ "$app" -lt "$APP_TARGET" ]; then echo "- 경고: appearances.md 항목이 ${APP_TARGET}개 미만입니다."; warn=1; fi
  [ "$warn" -eq 0 ] && echo "- 없음" || true
  echo
} > "$REPORT"

echo "$REPORT"

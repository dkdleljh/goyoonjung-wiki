# 위키 점검 리포트

> 생성: (자동 생성)

## 0) 커버리지(요약)

- 광고/엠버서더: 뷰티 5 / 패션 5 / 라이프 6
- 화보/사진: 커버 2 / 에디토리얼 10 / 캠페인 14 / 메이킹 2
- 출연/행사: 15
- 인터뷰/기사: 10

## 1) 빈 링크("공식 페이지:" 등 콜론 뒤가 비어있는 줄)

pages/pictorials/index.md:18:- 링크:
pages/interviews.md:11:- 링크:

## 2) 상태 태그 누락(인터뷰/화보/광고 템플릿 준수 여부)

### interviews.md에서 '상태:' 없는 항목(간단 체크)
- 수동 확인 권장(항목별 상태 태그는 사람이 최종 확인)

## 3) 날짜 형식(YYYY-MM-DD) 의심 라인

./scripts/auto_collect_visual_links.py:87:    # KBS pages often include 2025.05.10 or 2025-05-10
./pages/schedule.md:83:- 메모: JTBC 다시보기(1회) 페이지에 “2021.04.14 (Wed) 21:00 방송” 표기.

## 4) 커버리지 목표 미달 경고(권장)

- 경고: endorsements/beauty.md 항목이 10개 미만입니다.
- 경고: endorsements/fashion.md 항목이 10개 미만입니다.
- 경고: endorsements/lifestyle.md 항목이 10개 미만입니다.
- 경고: pictorials/cover.md 항목이 3개 미만입니다.


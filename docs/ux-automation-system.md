# UX + Automation System (운영 관점)

이 문서는 현재 저장소 기준의 자동화 시스템을 **운영자가 이해하기 쉽게** 요약합니다.

프로젝트 목표:

- **"고윤정의 과거/현재/미래의 모든 것을 담는 위키"**
- **"완벽한 무인 자동화"**

## 1. 시스템 개요

핵심 구조는 3개 축입니다.

1. Daily update
- 일일 수집/정리/승격/리포트/인덱스 갱신
- 메인 엔트리: `scripts/run_daily_update.sh`

2. Backfill
- 누락 데이터 보강, 배치 분산 처리
- 엔트리: `scripts/run_backfill_micro.sh`, `scripts/run_backfill_slice.sh`, `scripts/run_weekly_backfill.sh`

3. Resilience / Observability
- 장애 완화, 상태 점검, 결과 가시화
- 점검 스크립트: `scripts/check_automation_health.sh`
- 상태 문서: `pages/system_status.md`, `pages/daily-report.md`, `pages/lint-report.md`, `pages/quality-report.md`

## 2. 운영자가 보는 출력물

- 실행 로그: `news/YYYY-MM-DD.md`
- 일일 요약: `pages/daily-report.md`
- 품질 상태: `pages/quality-report.md`
- 링크 상태: `pages/lint-report.md`, `pages/link-health.md`
- 종합 점수: `pages/perfect-scorecard.md`

## 3. Perfect Scorecard 연결

- 생성: `python3 scripts/compute_perfect_scorecard.py`
- 결과: `pages/perfect-scorecard.md`

A/B/C/D는 아래를 의미합니다.

- A: 커버리지 시스템 준비도
- B: 무인 자동화 준비도
- C: 실제 정보 축적량(시간에 따라 증가)
- D: 품질 및 출처/링크 건강도

주의:

- 점수가 높아도 현실 세계의 절대적 완전성 100%는 증명 불가능합니다.

## 4. UX 관점의 원칙

- 사용자는 `index.md`/`index.en.md`에서 시작해 `pages/hub.md`로 이동
- 운영자는 로그/리포트/스코어카드로 시스템 상태를 판단
- 문서는 링크 중심으로 유지해 저작권/출처 추적성을 확보

## 5. 관련 문서

- 운영 절차: [`OPERATION_GUIDE.md`](OPERATION_GUIDE.md)
- 시스템 구조: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- 점수 체계: [`scoring.md`](scoring.md)

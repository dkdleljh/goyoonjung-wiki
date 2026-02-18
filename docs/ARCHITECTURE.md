# Architecture

goyoonjung-wiki의 현재 운영 아키텍처 요약 문서입니다.

## 1. 저장소 구조

```text
goyoonjung-wiki/
├── pages/      # 위키 본문/리포트/점수판
├── news/       # 날짜별 실행 로그
├── scripts/    # 자동화 스크립트
├── config/     # 수집/허용 도메인/쿼리 설정
├── data/       # SQLite 등 운영 데이터
├── docs/       # 운영/설계 문서
├── backups/    # 백업 산출물
└── tests/      # 테스트
```

## 2. 실행 계층

1. Daily runner
- `scripts/run_daily_update.sh`
- 수집 -> 정리 -> 승격 -> 리포트/인덱스 갱신

2. Backfill runners
- `scripts/run_backfill_micro.sh`
- `scripts/run_backfill_slice.sh`
- `scripts/run_backfill_slice_core.sh`
- `scripts/run_backfill_slice_i18n.sh`
- `scripts/run_weekly_backfill.sh`

3. Health and score
- `scripts/check_automation_health.sh`
- `scripts/compute_perfect_scorecard.py`

## 3. 관측 가능성(Observability)

시스템 상태는 문서형 아웃풋으로 남습니다.

- `news/YYYY-MM-DD.md`: 실행 상태/이력
- `pages/daily-report.md`: 일일 요약
- `pages/system_status.md`: 운영 상태 요약
- `pages/lint-report.md`, `pages/quality-report.md`: 품질 상태
- `pages/perfect-scorecard.md`: A/B/C/D 점수

## 4. 설계 원칙

- 링크 중심(저작권 안전)
- 공식/1차 출처 우선
- 무인 운영 + 감사 가능 로그
- 장애 시 재시도/배치 분할/상태 기록

## 5. 목표와 해석

- 프로젝트 목표:
- "고윤정의 과거/현재/미래의 모든 것을 담는 위키"
- "완벽한 무인 자동화"

- 점수 100은 운영 지표상 상태이며,
- **True 100% completeness cannot be proven.**

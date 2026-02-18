# 고윤정 위키 인덱스

고윤정 위키는 다음 두 목표를 동시에 추구합니다.

- **"고윤정의 과거/현재/미래의 모든 것을 담는 위키"**
- **"완벽한 무인 자동화"**

영문 인덱스: [`index.en.md`](index.en.md)

## 먼저 보면 좋은 페이지

- 허브(전체 포털): [`pages/hub.md`](pages/hub.md)
- 프로필: [`pages/profile.md`](pages/profile.md)
- 필모그래피: [`pages/filmography.md`](pages/filmography.md)
- 타임라인: [`pages/timeline.md`](pages/timeline.md)
- 최근 로그: [`news/README.md`](news/README.md)

## Perfect Scorecard

- 위치: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)
- 생성: `python3 scripts/compute_perfect_scorecard.py`

점수 해석:

- **A**: 커버리지 시스템 준비도
- **B**: 무인 자동화 준비도
- **C**: 실제 정보 축적량(시간이 지날수록 증가)
- **D**: 품질/출처/링크 건강도

주의:

- 점수는 운영 모델의 상태 지표입니다.
- **진짜 의미의 절대적 100% 완전성은 증명할 수 없습니다.**

## 자동화 파이프라인 요약

상세: [`docs/ux-automation-system.md`](docs/ux-automation-system.md)

1. Daily update
- `scripts/run_daily_update.sh`
- 일일 수집, 정리, 승격, 리포트, 인덱스 갱신

2. Backfill
- `scripts/run_backfill_micro.sh`
- `scripts/run_backfill_slice.sh`
- `scripts/run_weekly_backfill.sh`

3. Resilience / Observability
- `scripts/check_automation_health.sh`
- `pages/system_status.md`, `pages/daily-report.md`, `pages/lint-report.md`, `pages/quality-report.md`

## 자주 쓰는 명령

```bash
make venv
make check
./scripts/check_automation_health.sh
python3 scripts/compute_perfect_scorecard.py
```

## 운영 기준

- 공식/1차 출처 우선
- 루머/사생활/추측 배제
- 저작권 보호를 위한 링크 중심 기록

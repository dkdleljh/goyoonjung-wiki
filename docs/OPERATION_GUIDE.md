# Operation Guide

고윤정 위키 자동화 운영 가이드입니다.

## 1. 목표

- 콘텐츠 목표: **"고윤정의 과거/현재/미래의 모든 것을 담는 위키"**
- 운영 목표: **"완벽한 무인 자동화"**

## 2. 일일 운영 루프

메인 엔트리:

```bash
./scripts/run_daily_update.sh
```

주요 산출물:

- `news/YYYY-MM-DD.md`
- `pages/daily-report.md`
- `pages/kpi-report.md`
- `pages/candidate-pool.md`
- `pages/system_status.md`
- `pages/lint-report.md`
- `pages/quality-report.md`

도메인 등급 정책:

- `config/domain-grades.yml` (S/A/B/BLOCK)
- `config/allowlist-domains.txt` (하위 호환; 기본 A)

## 3. 백필(누락 보강)

```bash
./scripts/run_backfill_micro.sh
./scripts/run_backfill_slice.sh
./scripts/run_weekly_backfill.sh
```

환경변수 `MODE`를 사용해 `run_backfill_micro.sh`의 단계 실행을 제어할 수 있습니다.
(예: `MODE=score ./scripts/run_backfill_micro.sh`)

## 4. 상태 점검

```bash
./scripts/check_automation_health.sh
python3 scripts/compute_perfect_scorecard.py
```

결과 확인:

- 건강 점검 결과: 쉘 출력
- 점수 결과 문서: `pages/perfect-scorecard.md`
- KPI 문서: `pages/kpi-report.md`

## 5. Perfect Scorecard 해석

- 위치: `pages/perfect-scorecard.md`
- 축: A/B/C/D
- A/B: 시스템 준비도
- C: 실제 축적량(시간 경과에 따라 증가)
- D: 품질/링크/출처 상태

중요:

- 점수 100은 현재 지표 기준의 상태입니다.
- **절대적 100% 완전성은 증명할 수 없습니다.**

## 6. 문제 대응 기본

1. `news/YYYY-MM-DD.md`의 실행 상태 확인
2. `pages/daily-report.md`와 `pages/lint-report.md` 확인
3. `./scripts/check_automation_health.sh` 재실행
4. 필요 시 백필 스크립트로 누락 구간 보강

## 8. 도메인 등급 운영 규칙

- `S`: daily news에 즉시 landing, 자동 승격 대상
- `A`: `pages/promotion-queue.md` 후보로만 적재
- `B`: `pages/candidate-pool.md` 보관소로만 적재
- `BLOCK`: 수집 단계에서 폐기

Google News 키워드 파일은 분리 운영:

- 정밀 세트: `config/google-news-queries-precise.txt`
- 확장 세트: `config/google-news-queries-broad.txt`
- 기존 `config/google-news-queries.txt`는 fallback

## 7. 관련 문서

- 자동화 개요: [`ux-automation-system.md`](ux-automation-system.md)
- 아키텍처: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- 점수 체계: [`scoring.md`](scoring.md)

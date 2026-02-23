# 고윤정 위키 (Go Youn-jung Wiki)

고윤정 위키는 두 가지 목표를 중심으로 운영됩니다.

- 콘텐츠 목표: **"고윤정의 과거/현재/미래의 모든 것을 담는 위키"**
- 운영 목표: **"완벽한 무인 자동화"**

이 저장소는 링크 중심(저작권 안전) 아카이브 방식으로, 작품/인터뷰/화보/광고/출연/일정 정보를 장기적으로 누적합니다.

## 빠른 시작

- 한국어 메인 인덱스: [`index.md`](index.md)
- English main index: [`index.en.md`](index.en.md)
- 허브(포털): [`pages/hub.md`](pages/hub.md)
- Hub (English): [`pages/hub.en.md`](pages/hub.en.md)
- 자동화 시스템 설명: [`docs/ux-automation-system.md`](docs/ux-automation-system.md)
- 일일 리포트: [`pages/daily-report.md`](pages/daily-report.md)

## Perfect Scorecard 안내

Perfect Scorecard는 시스템/콘텐츠 상태를 4축으로 보여주는 운영 점수판입니다.

- 위치: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)
- 생성 스크립트: `python3 scripts/compute_perfect_scorecard.py`

A/B/C/D 의미:

- **A. Perfect wiki coverage system**: 채널/랜딩/탐지 체계가 얼마나 갖춰졌는지
- **B. Perfect unmanned automation**: 무인 파이프라인, 복원력, 관측성이 얼마나 갖춰졌는지
- **C. Unbeatable information volume**: 실제 축적 규모(시간이 지나며 증가)
- **D. Perfect quality**: 품질 부채/링크 상태/린트/출처 체계

중요:

- 점수 100은 "시스템 준비도/현재 상태"를 의미합니다.
- **현실의 모든 정보를 100% 완전하게 수집했다는 것을 수학적으로 증명할 수는 없습니다.**
- 따라서 이 프로젝트는 "장기 누적 + 낮은 부채 + 높은 신뢰성"을 목표로 최적화합니다.

## 자동화 파이프라인 (High-level)

상세 문서: [`docs/ux-automation-system.md`](docs/ux-automation-system.md)

1. **Daily update**
- 메인 러너: `scripts/run_daily_update.sh`
- 수집/정리/승격/리포트/인덱스 갱신을 일일 루프로 실행
- 결과 기록: `news/YYYY-MM-DD.md`, `pages/daily-report.md`

2. **Backfill**
- 마이크로 배치: `scripts/run_backfill_micro.sh`
- 슬라이스 실행: `scripts/run_backfill_slice.sh`, `scripts/run_backfill_slice_core.sh`, `scripts/run_backfill_slice_i18n.sh`
- 주간 러너: `scripts/run_weekly_backfill.sh`

3. **Resilience / Observability**
- 건강 점검: `scripts/check_automation_health.sh`
- 점수판 계산: `scripts/compute_perfect_scorecard.py`
- 운영 상태: `pages/system_status.md`, `pages/lint-report.md`, `pages/quality-report.md`

## 로컬 점검 명령

```bash
make venv
make check
./scripts/check_automation_health.sh
python3 scripts/compute_perfect_scorecard.py
```

## 문서 맵

- 기여 가이드: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- 문서 포털: [`docs/README.md`](docs/README.md)
- 아키텍처: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- 운영 가이드: [`docs/OPERATION_GUIDE.md`](docs/OPERATION_GUIDE.md)
- 점수 체계: [`docs/scoring.md`](docs/scoring.md)

## 운영 원칙

- 루머/사생활/추측은 기록하지 않습니다.
- 원문 복사보다 링크 + 메타데이터를 우선합니다.
- 공식/1차 출처를 우선하고, 근거 수준을 명시합니다.

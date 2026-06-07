# 🧭 고윤정 위키 허브

> 자동 생성 허브 · 마지막 갱신: 2026-06-07

## 운영/문서 링크
- [프로젝트 README](../README.md)
- [문서 포털](../docs/README.md)
- [운영 가이드](../docs/OPERATION_GUIDE.md)
- [릴리즈 정책](../docs/RELEASING.md)
- [CHANGELOG](../CHANGELOG.md)
- [시스템 상태](system_status.md)
- [Perfect Scorecard](perfect-scorecard.md)

## 운영 상태표
| 항목 | 값 |
|---|---|
| 최신 커밋 | `d99019d2` |
| 최신 릴리즈 태그 | `v1.32.1` |
| docs 문서 수 | `20` |
| 운영 페이지 수 | `19` |
| 문서 생성기 | `scripts/generate_doc_portals.py` |
| daily update | `scripts/run_daily_update.sh` |

## 운영 계약
- 목표: 과거/현재/미래 정보를 링크 중심으로 계속 확장한다.
- 증명 한계: ‘모든 정보 100%’는 증명할 수 없으므로 공식 근거, 누락 탐지, 검증 큐로 관리한다.
- 무인 운영: daily timer, health check, retry, lock, backup, commit/push, release notes를 자동화한다.
- 안전 원칙: 루머/사생활/비공식 단정은 금지하고, 미확정 항목은 검증 큐에 남긴다.
- 현재 판정: `bash scripts/check_automation_health.sh`와 `make check` 통과를 운영 기준으로 삼는다.

## 콘텐츠 핵심 링크
- [프로필](profile.md)
- [필모그래피](filmography.md)
- [타임라인](timeline.md)
- [인터뷰](interviews.md)
- [화보](pictorials.md)
- [광고](endorsements.md)
- [스케줄](schedule.md)

## 최근 변경 파일
- `pages/link-health.md`

## 운영 핵심 페이지
- [`pages/awards-official-watch.md`](awards-official-watch.md)
- [`pages/brand-evidence-watch.md`](brand-evidence-watch.md)
- [`pages/daily-report.md`](daily-report.md)
- [`pages/fact-conflicts.md`](fact-conflicts.md)
- [`pages/facts-index.md`](facts-index.md)
- [`pages/future-watch.md`](future-watch.md)
- [`pages/hub.en.md`](hub.en.md)
- [`pages/hub.md`](hub.md)
- [`pages/lint-report.md`](lint-report.md)
- [`pages/official-coverage-audit.md`](official-coverage-audit.md)
- [`pages/official-platform-watch.md`](official-platform-watch.md)
- [`pages/perfect-scorecard.md`](perfect-scorecard.md)
- [`pages/preflight-report.md`](preflight-report.md)
- [`pages/quality-report.md`](quality-report.md)
- [`pages/self-heal-report.md`](self-heal-report.md)
- [`pages/source-confidence.md`](source-confidence.md)
- [`pages/system_status.md`](system_status.md)
- [`pages/verification-queue.md`](verification-queue.md)
- [`pages/watchdog-report.md`](watchdog-report.md)

# 고윤정 위키 (Go Youn-jung Wiki)

![Repo](https://img.shields.io/badge/repo-goyoonjung-wiki-111827?style=flat-square) ![Latest Tag](https://img.shields.io/badge/latest-v1.11.0-2563eb?style=flat-square) ![Docs](https://img.shields.io/badge/docs-18-059669?style=flat-square) ![Automation](https://img.shields.io/badge/automation-daily__update-7c3aed?style=flat-square)

> 자동 생성 포털 문서 · 마지막 갱신: 2026-05-14

이 저장소는 **링크 중심 위키**이면서 동시에 **무인 자동화 운영 저장소**입니다.

## 문서 목차
- [빠른 시작](#빠른-시작)
- [상태 요약](#상태-요약)
- [현재 자동화 범위](#현재-자동화-범위)
- [최신 릴리즈](#최신-릴리즈)
- [최근 변경 요약](#최근-변경-요약)
- [최근 변경 파일](#최근-변경-파일)
- [자주 쓰는 명령](#자주-쓰는-명령)

## 빠른 시작
- 메인 인덱스: [`index.md`](index.md)
- 허브: [`pages/hub.md`](pages/hub.md)
- 문서 포털: [`docs/README.md`](docs/README.md)
- 운영 가이드: [`docs/OPERATION_GUIDE.md`](docs/OPERATION_GUIDE.md)
- 릴리즈 정책: [`docs/RELEASING.md`](docs/RELEASING.md)
- 시스템 상태: [`pages/system_status.md`](pages/system_status.md)
- Perfect Scorecard: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)

## 상태 요약
| 항목 | 값 |
|---|---|
| 최신 커밋 | `c53dab79` |
| 최신 릴리즈 태그 | `v1.11.0` |
| docs 문서 수 | `18` |
| 운영 페이지 수 | `7` |
| 문서 생성기 | `scripts/generate_doc_portals.py` |
| daily update | `scripts/run_daily_update.sh` |

## 현재 자동화 범위
- daily update
- automation health 검사
- stale lock 정리
- changelog 생성
- semver 태그/릴리즈
- release notes 자산 업로드

## 운영 계약
- 목표: 과거/현재/미래 정보를 링크 중심으로 계속 확장한다.
- 증명 한계: ‘모든 정보 100%’는 증명할 수 없으므로 공식 근거, 누락 탐지, 검증 큐로 관리한다.
- 무인 운영: daily timer, health check, retry, lock, backup, commit/push, release notes를 자동화한다.
- 안전 원칙: 루머/사생활/비공식 단정은 금지하고, 미확정 항목은 검증 큐에 남긴다.
- 현재 판정: `bash scripts/check_automation_health.sh`와 `make check` 통과를 운영 기준으로 삼는다.

## 최신 릴리즈
- `v1.11.0`
  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.11.0
  - 로컬 노트: `logs/releases/release-notes-v1.11.0.md`
- `v1.10.1`
  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.10.1
  - 로컬 노트: `logs/releases/release-notes-v1.10.1.md`
- `v1.10.0`
  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.10.0
  - 로컬 노트: `logs/releases/release-notes-v1.10.0.md`

## 최근 변경 요약
- [`c53dab79`](https://github.com/dkdleljh/goyoonjung-wiki/commit/c53dab79) — daily: update 2026-05-13
- [`a6b69790`](https://github.com/dkdleljh/goyoonjung-wiki/commit/a6b69790) — daily: update 2026-05-12
- [`f95751bc`](https://github.com/dkdleljh/goyoonjung-wiki/commit/f95751bc) — daily: update 2026-05-11
- [`3f1b26da`](https://github.com/dkdleljh/goyoonjung-wiki/commit/3f1b26da) — daily: update 2026-05-10
- [`1eb4f0d6`](https://github.com/dkdleljh/goyoonjung-wiki/commit/1eb4f0d6) — chore: link health 2026-05-10

## 최근 변경 파일
- `README.md`
- `docs/README.md`
- `index.md`
- `news/2026-05-12.md`
- `news/2026-05-13.md`
- `news/README.md`
- `pages/candidate-pool.md`
- `pages/daily-report.md`

## 자주 쓰는 명령
```bash
bash scripts/check_automation_health.sh
python3 scripts/wiki_score.py
python3 scripts/generate_doc_portals.py
FORCE=1 ./scripts/run_daily_update.sh
```

## 메모
- 이 README는 `scripts/generate_doc_portals.py`로 자동 생성됩니다.
- 상세 설명형 문서는 `docs/OPERATION_GUIDE.md`, `docs/RELEASING.md`에서 관리합니다.

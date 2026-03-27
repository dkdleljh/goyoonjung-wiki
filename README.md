# 고윤정 위키 (Go Youn-jung Wiki)

![Repo](https://img.shields.io/badge/repo-goyoonjung-wiki-111827?style=flat-square) ![Latest Tag](https://img.shields.io/badge/latest-v1.5.1-2563eb?style=flat-square) ![Docs](https://img.shields.io/badge/docs-17-059669?style=flat-square) ![Automation](https://img.shields.io/badge/automation-daily__update-7c3aed?style=flat-square)

> 자동 생성 포털 문서 · 마지막 갱신: 2026-03-27

이 저장소는 **링크 중심 위키**이면서 동시에 **무인 자동화 운영 저장소**입니다.

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
| 최신 커밋 | `389eaf44` |
| 최신 릴리즈 태그 | `v1.5.1` |
| docs 문서 수 | `17` |
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

## 최신 릴리즈
- `v1.5.1`
  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.5.1
  - 로컬 노트: `logs/releases/release-notes-v1.5.1.md`
- `v1.5.0`
  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.5.0
  - 로컬 노트: `logs/releases/release-notes-v1.5.0.md`
- `v1.4.1`
  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.4.1
  - 로컬 노트: `logs/releases/release-notes-v1.4.1.md`

## 최근 변경 요약
- [`389eaf44`](https://github.com/dkdleljh/goyoonjung-wiki/commit/389eaf44) — chore: prepare release v1.5.1
- [`526844fd`](https://github.com/dkdleljh/goyoonjung-wiki/commit/526844fd) — feat(docs): expand generated wiki doc indexes
- [`e0203d74`](https://github.com/dkdleljh/goyoonjung-wiki/commit/e0203d74) — chore: prepare release v1.5.0
- [`7fcbc1c5`](https://github.com/dkdleljh/goyoonjung-wiki/commit/7fcbc1c5) — feat(docs): auto-generate wiki doc portals
- [`a167ed9b`](https://github.com/dkdleljh/goyoonjung-wiki/commit/a167ed9b) — chore: prepare release v1.4.1

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

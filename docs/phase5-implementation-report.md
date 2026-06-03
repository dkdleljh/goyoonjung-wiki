# Phase 1~5 구현 결과 보고서

> 작성일: 2026-06-04  
> 대상: `goyoonjung-wiki` 전 생애 정보 수집·검증·무인 자동화 고도화

## 1. 요약

Phase 1부터 Phase 5까지의 계획을 실제 운영 가능한 스크립트, 리포트, 구조화 데이터, systemd watchdog, GitHub 문서로 구현했다. 이 구현은 “공식 근거 없는 정보를 자동 확정하지 않는다”는 원칙을 유지하면서, 고윤정 관련 과거·현재·미래 정보를 자동 감지하고 검증 큐로 관리하며, 무인 업데이트 파이프라인이 매일 반복 실행할 수 있도록 보강한다.

## 2. 구현된 핵심 파일

### Phase 1: 자동화 안정화

- `scripts/preflight_automation.py`
  - git remote, fetch, HEAD/origin 상태, venv 도구, webhook, 디스크, lock, systemd timer를 점검한다.
  - 결과: `pages/preflight-report.md`, `data/reports/preflight.json`
- `scripts/self_heal_automation.py`
  - stale lock, notify queue, 품질 리포트, 검증 큐, 공식 커버리지, 문서 포털, timer enable을 안전 범위에서 복구한다.
  - 결과: `pages/self-heal-report.md`, `data/reports/self_heal.json`
- `scripts/watchdog_automation.py`
  - daily/sync/linkhealth/notifyflush/backupcleanup/watchdog timer와 자동화 헬스를 감시한다.
  - 결과: `pages/watchdog-report.md`, `data/reports/watchdog.json`
- `deploy/systemd/user/goyoonjung-wiki-watchdog.service`
- `deploy/systemd/user/goyoonjung-wiki-watchdog.timer`
- `scripts/install_watchdog_timer.sh`

### Phase 2: 공식 출처 수집 강화

- `scripts/auto_collect_official_platforms.py`
  - 작품 페이지의 MAA, Netflix, Disney+, TVING, JTBC, tvN, YouTube 등 공식/플랫폼 링크를 감시한다.
  - 결과: `pages/official-platform-watch.md`, `data/facts/official_platforms.json`
- `scripts/auto_collect_awards_official.py`
  - `pages/awards.md`에서 공식확정/공식 근거 미확보 항목을 분리한다.
  - 결과: `pages/awards-official-watch.md`, `data/facts/awards_official_watch.json`
- `scripts/auto_collect_brands.py`
  - 브랜드/광고/화보 근거를 모으고 역할 불확정 항목을 자동 확정하지 않는다.
  - 결과: `pages/brand-evidence-watch.md`, `data/facts/brands.json`
- `scripts/auto_detect_future_works.py`
  - 공개 예정, 촬영, 캐스팅, pending release 등 미래 후보를 감지한다.
  - 결과: `pages/future-watch.md`, `pages/future-candidates.md`, `data/facts/future_candidates.json`

### Phase 3: 구조화 데이터 전환

- `scripts/extract_facts_from_markdown.py`
  - 필모그래피, 수상, 프로필을 구조화 JSON으로 추출한다.
  - 결과: `data/facts/works.json`, `data/facts/awards.json`, `data/facts/profile.json`
- `scripts/render_pages_from_facts.py`
  - 구조화 데이터 현황을 Markdown 색인으로 렌더링한다.
  - 결과: `pages/facts-index.md`
- `scripts/source_confidence.py`
  - 전체 Markdown URL을 도메인 등급 정책으로 집계한다.
  - 결과: `pages/source-confidence.md`, `data/facts/sources.json`
- `scripts/audit_fact_conflicts.py`
  - 작품명 기준 역할/날짜 충돌을 감지한다.
  - 결과: `pages/fact-conflicts.md`, `data/facts/fact_conflicts.json`

### Phase 4: 검증 부채 제거 체계

- 공식 출처가 없으면 자동 확정하지 않는 감시 페이지를 추가했다.
- 수상/브랜드/SNS/미래작의 불확정 항목을 본문 확정 대신 큐와 감시 리포트에 남긴다.
- `pages/verification-queue.md`, `pages/official-coverage-audit.md`, `pages/quality-report.md`와 함께 점진적으로 검증 부채를 줄이는 구조를 갖췄다.

### Phase 5: 완전 운영 체계

- `scripts/run_daily_update.sh`에 다음 단계를 연결했다.
  - preflight
  - 공식 플랫폼 수집
  - 시상식 공식 감시
  - 브랜드 감시
  - 미래작 감지
  - facts 추출
  - source confidence
  - fact conflict audit
  - facts index 렌더링
  - watchdog snapshot
- `config/automation-generated-files.txt`에 신규 자동 생성 산출물을 등록했다.
- `scripts/generate_doc_portals.py`의 운영 핵심 페이지 목록에 신규 리포트를 연결했다.
- GitHub 관련 자동화 문서 `.github/AUTOMATION.md`를 추가했다.

## 3. 현재 생성 결과

| 리포트 | 목적 |
|---|---|
| `pages/preflight-report.md` | 무인 실행 전 필수 상태 점검 |
| `pages/self-heal-report.md` | 안전 복구 수행 결과 |
| `pages/watchdog-report.md` | systemd timer와 자동화 헬스 감시 |
| `pages/official-platform-watch.md` | 작품별 공식 플랫폼 링크 감시 |
| `pages/awards-official-watch.md` | 수상/후보 공식 근거 감시 |
| `pages/brand-evidence-watch.md` | 브랜드 역할/근거 감시 |
| `pages/future-watch.md` | 미래작 후보 감지 |
| `pages/future-candidates.md` | 미래 정보 후보 큐 |
| `pages/facts-index.md` | 구조화 facts 색인 |
| `pages/fact-conflicts.md` | 사실 충돌 감지 결과 |
| `pages/source-confidence.md` | 출처 등급 통계 |

## 4. 실제 실행 결과

2026-06-04 기준 수동 실행으로 확인한 결과는 다음과 같다.

| 항목 | 결과 |
|---|---:|
| official platform links | 87 |
| awards items | 13 |
| awards unresolved | 11 |
| brand evidence items | 72 |
| brand role pending | 2 |
| future candidates | 8 |
| extracted works | 14 |
| extracted awards | 13 |
| source URLs scanned | 1025 |
| fact conflicts | 0 |

## 5. 남은 제약

다음 항목은 “완벽 자동 확정” 대상이 아니라 지속 감시 대상이다.

- 공식 근거가 아직 없는 수상/후보 항목
- 브랜드 역할이 공식적으로 확정되지 않은 항목
- 본인 SNS 계정처럼 소속사/공식 문서 교차확인이 필요한 항목
- 미래작 중 단일 보도 또는 루머성 정보

이 제약은 자동화 실패가 아니라, 잘못된 정보 확정을 막기 위한 안전 정책이다.

## 6. 운영 명령

```bash
python3 scripts/preflight_automation.py
python3 scripts/self_heal_automation.py
python3 scripts/watchdog_automation.py
python3 scripts/auto_collect_official_platforms.py
python3 scripts/auto_collect_awards_official.py
python3 scripts/auto_collect_brands.py
python3 scripts/auto_detect_future_works.py
python3 scripts/extract_facts_from_markdown.py
python3 scripts/source_confidence.py
python3 scripts/audit_fact_conflicts.py
python3 scripts/render_pages_from_facts.py
bash scripts/check_automation_health.sh
make check
```

watchdog timer 설치/갱신:

```bash
./scripts/install_watchdog_timer.sh
systemctl --user list-timers --all 'goyoonjung-wiki*' --no-pager
```

## 7. Phase 5 완료 판정

- daily timer: 운영 중
- sync timer: 운영 중
- linkhealth timer: 운영 중
- notifyflush timer: 운영 중
- backupcleanup timer: 운영 중
- watchdog timer: 추가 및 운영 중
- GitHub release automation: 기존 `scripts/auto_release.sh` 유지 및 문서 동기화 보강
- Discord alert: 기존 `notify_status.py`와 `flush_notify_queue.py` 유지 및 queue 복구 체계 보강
- health dashboard: `pages/system_status.md`, `pages/dashboard.md`, 신규 preflight/watchdog/self-heal 리포트로 확장

완료 판정은 단순 선언이 아니라 다음 명령 통과를 기준으로 한다.

```bash
make check
bash scripts/check_automation_health.sh
python3 scripts/preflight_automation.py
python3 scripts/watchdog_automation.py
```

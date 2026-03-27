# 고윤정 위키 (Go Youn-jung Wiki)

이 프로젝트는 **고윤정 관련 공개 정보를 장기적으로 축적하는 링크 중심 위키**이면서, 동시에 **완전 무인 자동화에 최대한 가깝게 운영되는 실전형 자동화 저장소**입니다.

핵심 목표는 두 가지입니다.

1. **콘텐츠 목표**  
   고윤정의 과거·현재·미래와 관련된 작품, 인터뷰, 화보, 광고, 일정, 활동 기록을 장기적으로 축적합니다.

2. **운영 목표**  
   수집, 정리, 검증, 점수화, 릴리즈, GitHub 반영까지 가능한 한 자동으로 돌아가게 만듭니다.

> 2026-03-27 기준 이 저장소는 daily update, health check, stale lock 정리, changelog 생성, semver 릴리즈, GitHub Release 자산 업로드까지 자동화되어 있습니다.

---

## 1. 프로젝트 철학

이 저장소는 “많이 모으는 것”만 목표로 하지 않습니다.

아래 네 가지를 동시에 만족시키는 것을 지향합니다.

- **저작권 안전**: 원문 복사보다 링크와 메타데이터를 우선
- **출처 신뢰성**: 공식/1차 출처 우선
- **운영 안정성**: 실패해도 복구 가능한 구조
- **지속 가능성**: 사람이 매번 붙지 않아도 굴러가는 체계

---

## 2. 빠른 시작

### 문서부터 볼 때
- 메인 허브: [`pages/hub.md`](pages/hub.md)
- 운영 상태: [`pages/system_status.md`](pages/system_status.md)
- 일일 결과: [`pages/daily-report.md`](pages/daily-report.md)
- 완성도 점수: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)
- 문서 포털: [`docs/README.md`](docs/README.md)

### 자동화 상태부터 볼 때
```bash
cd /Users/zenith/Documents/My-Second-Brain/20_Projects/Goyoonjung-Wiki
bash scripts/check_automation_health.sh
python3 scripts/wiki_score.py
```

---

## 3. 실제 운영 파이프라인

### 3-1. Daily update
메인 엔트리포인트:
- `scripts/run_daily_update.sh`

이 스크립트는 대략 다음을 수행합니다.

- 수집기 실행
- 각종 후보/큐 갱신
- status/dashboard/lint/quality 관련 산출물 재생성
- 백업
- 커밋/푸시
- changelog/release 자동화

### 3-2. Health / Observability
- 헬스체크: `scripts/check_automation_health.sh`
- 점수 계산: `scripts/wiki_score.py`
- 상태 문서:
  - `pages/system_status.md`
  - `pages/lint-report.md`
  - `pages/quality-report.md`
  - `pages/kpi-report.md`

### 3-3. Release automation
- 스크립트: `scripts/auto_release.sh`
- 현재 규칙: `vMAJOR.MINOR.PATCH`
- 산출물:
  - Git tag
  - GitHub Release
  - `logs/releases/release-notes-<tag>.md`
  - release notes 자산 업로드

---

## 4. 현재 설치된 무인 실행 스케줄

macOS 크론 기준 실제 연결된 주요 작업:

- 매일 `17:53` : `scripts/run_daily_update.sh`
- 매일 `18:10` : `scripts/check_automation_health.sh`
- 매시 `40분` : `scripts/cleanup_stale_running.sh`

즉, 이 저장소는 **하루 한 번 메인 갱신**, **후속 건강 점검**, **잠금/비정상 상태 정리**가 자동으로 이어집니다.

---

## 5. 현재 릴리즈 체계

최근 자동 릴리즈 예시는 다음과 같습니다.

- `v1.3.0`
- `v1.3.1`

릴리즈 노트에는 아래 정보가 자동 포함됩니다.

- Summary
- Impact
- Validation
- Risk
- Rollback
- Changes
- Assets

관련 파일:
- `docs/RELEASING.md`
- `scripts/auto_release.sh`
- `logs/releases/`

---

## 6. 자주 쓰는 명령

```bash
# 환경 준비
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# 핵심 점검
bash scripts/check_automation_health.sh
python3 scripts/wiki_score.py
python3 scripts/generate_changelog.py

# 실제 daily 실행
FORCE=1 ./scripts/run_daily_update.sh
```

---

## 7. 문서 안내

- 아키텍처: `docs/ARCHITECTURE.md`
- 운영 가이드: `docs/OPERATION_GUIDE.md`
- 릴리즈 정책: `docs/RELEASING.md`
- 점수 체계: `docs/scoring.md`
- 자동화 설명: `docs/ux-automation-system.md`

---

## 8. 운영 원칙

- 루머/사생활/무근거 추측은 기록하지 않습니다.
- 공식·1차 출처를 우선합니다.
- 링크가 살아 있는지, 문서가 재생성 가능한지, 자동화가 실제 도는지를 중요하게 봅니다.
- 문서와 코드는 함께 갱신합니다.

---

## 9. 한 줄 요약

이 저장소는 단순 팬 위키가 아니라,
**콘텐츠 축적 + 검증 + 운영 자동화 + 릴리즈 기록**이 결합된 장기 운영형 링크 아카이브 시스템입니다.


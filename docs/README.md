# docs/ 문서 포털

이 디렉터리는 고윤정 위키의 **운영 철학, 자동화 구조, 실무 절차, 릴리즈 정책**을 설명하는 문서 모음입니다.

코드만 읽어서는 전체 맥락을 놓치기 쉬우므로, 실제 운영/수정 전에 이 문서들을 먼저 읽는 것을 권장합니다.

---

## 1. 어떤 문서가 있는가

### 가장 먼저 읽을 문서
1. [`OPERATION_GUIDE.md`](OPERATION_GUIDE.md)
   - 실제로 프로젝트를 어떻게 굴리는지 설명하는 운영 안내서
2. [`ARCHITECTURE.md`](ARCHITECTURE.md)
   - 수집/정리/검증/리포트 파이프라인 구조
3. [`RELEASING.md`](RELEASING.md)
   - semver 태그, GitHub Release, 노트 생성 규칙
4. [`scoring.md`](scoring.md)
   - 점수 체계와 해석 기준
5. [`ux-automation-system.md`](ux-automation-system.md)
   - 자동화 UX/파이프라인 전반 설명

---

## 2. 문서 읽기 추천 순서

### 운영 담당자 관점
- `OPERATION_GUIDE.md`
- `RELEASING.md`
- `ARCHITECTURE.md`

### 구조 이해 관점
- `ARCHITECTURE.md`
- `ux-automation-system.md`
- `scoring.md`

### 품질 개선 관점
- `scoring.md`
- `verification-standardization-system.md`
- `content_schema.md`

---

## 3. 현재 문서가 반영하는 실제 상태

2026-03-27 기준 이 문서 포털은 아래 운영 상태를 기준으로 정리되어 있습니다.

- daily update 자동 실행
- automation health 자동 검사
- stale lock 정리 자동 실행
- `wiki_score.py` 기반 상태 점수 확인
- `generate_changelog.py` 기반 changelog 생성
- `auto_release.sh` 기반 semver release 자동화
- GitHub Release 노트 및 자산 업로드

즉, 이 문서들은 “계획 문서”가 아니라 **이미 연결된 실제 시스템 문서**입니다.

---

## 4. 문서 갱신 원칙

다음이 바뀌면 문서도 같이 바꿔야 합니다.

- 엔트리포인트 스크립트
- 릴리즈 정책
- 크론/스케줄
- 산출물 위치
- 상태 점검 방법
- 점수 계산 규칙

특히 아래 파일이 바뀌면 관련 문서 동기화를 권장합니다.

- `scripts/run_daily_update.sh`
- `scripts/check_automation_health.sh`
- `scripts/auto_release.sh`
- `scripts/generate_changelog.py`

---

## 5. 함께 보는 운영 파일

- `../README.md`
- `../CHANGELOG.md`
- `../pages/system_status.md`
- `../pages/perfect-scorecard.md`
- `../logs/releases/`

---

## 6. 중요한 해석 원칙

- 점수 100은 “현 시점의 운영 상태/준비도”를 뜻합니다.
- 실제 세계의 모든 정보를 절대적으로 100% 수집했다는 뜻은 아닙니다.
- 이 프로젝트는 **완전성의 증명**보다 **장기 누적 + 낮은 운영 부채 + 높은 재현성**을 목표로 합니다.


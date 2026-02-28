# OPERATION GUIDE (고윤정 위키 자동화 운영 가이드)

이 문서는 `goyoonjung-wiki` 레포의 **무인 자동화 운영**을 위한 실전 가이드입니다.
(원칙: 링크-first / 보수적 자동 승격 / 실패 내성 / 자동 복구)

## 100점 달성 시스템 개요

### 목표
- 콘텐츠 목표: **“고윤정의 과거/현재/미래의 모든 것을 담는 위키”**
- 운영 목표: **“완벽한 무인 자동화 + 자동 복구/수정”**

### 핵심 원칙
- **링크-first(저작권 안전)**: 원문/출처 링크를 우선하고, 2차 서술은 최소화합니다.
- **보수적 자동 승격**: 확실한 규칙이 있는 경우에만 상위 등급(landing/promotion)으로 자동 승격합니다.
- **SIGKILL/자원 제한 환경 대응**: 큰 작업을 한 번에 하지 않고, **마이크로 작업(1작업/1회)**으로 쪼개 누적합니다.
- **관측 가능성(Observability)**: 매 실행마다 리포트/로그/점수/헬스를 남깁니다.

### 주요 산출물(읽는 순서 추천)
- `news/YYYY-MM-DD.md` : 그 날의 daily 업데이트 결과(실행 상태/요약)
- `pages/daily-report.md` : 수집·정규화·후처리 통계/이슈
- `pages/lint-report.md` : 링크/형식/정책 위반
- `pages/quality-report.md` : 품질 지표, 누락·중복·정책 위반 요약
- `pages/kpi-report.md` : KPI(증감 추세)
- `pages/perfect-scorecard.md` : 100점 체계(A/B/C/D)
- `pages/system_status.md` : 시스템 상태 스냅샷
- `pages/candidate-pool.md` : 낮은 등급/보류 후보 저장소

### 점수 체계(Perfect Scorecard) 해석
- 위치: `pages/perfect-scorecard.md`
- 축: **A / B / C / D**
  - **A/B**: “준비도(100 가능)” 축 (시스템이 100점을 받을 수 있는 구조인지)
  - **C**: “누적량” 축
    - `C_current`: 실제 누적량(시간과 백필로 증가)
    - `C_capacity`: 잠재력/수집 가능 범위(정책·쿼리·커버리지)
  - **D**: 품질/링크/출처/정책 준수 축
- 주의: **점수 100은 ‘현재 기준 지표’에서의 상태**입니다. “절대적 100% 완전성”은 증명할 수 없습니다.

---

## 📋 운영 절차

### 0) 사전 준비(최초 1회)
1. 레포 위치로 이동
   ```bash
   cd ~/바탕화면/goyoonjung-wiki
   ```
2. 파이썬/의존성 확인(환경별로 user-site 설치를 사용하기도 함)
   ```bash
   python3 -V
   python3 -m pip -V
   ./ultrawork_verification.sh
   ```

### 1) 데일리 업데이트(매일 1회)
메인 엔트리:
```bash
./scripts/run_daily_update.sh
```
권장 확인 순서:
1. `news/YYYY-MM-DD.md` 오늘자 파일이 생성/갱신되었는지
2. `pages/daily-report.md`의 에러/스킵 요약
3. `pages/lint-report.md` 정책 위반/죽은 링크/형식 문제
4. `pages/perfect-scorecard.md` 점수 변화

### 2) 백필(누락 보강) — “마이크로 백필” 우선
자원 제한/불안정 환경에서는 **큰 백필을 피하고**, 쪼개서 누적합니다.
```bash
./scripts/run_backfill_micro.sh
```
단계 제어(예시):
```bash
MODE=score  ./scripts/run_backfill_micro.sh
MODE=collect ./scripts/run_backfill_micro.sh
MODE=fix    ./scripts/run_backfill_micro.sh
```
다른 백필 옵션:
```bash
./scripts/run_backfill_slice.sh
./scripts/run_weekly_backfill.sh
```

### 3) 정책(도메인 등급) 운영
도메인 등급 정책 파일:
- `config/domain-grades.yml` : S/A/B/BLOCK
- `config/allowlist-domains.txt` : 하위 호환(기본 A 취급)

등급 의미(권장 운용):
- **S**: daily news에 즉시 landing, 자동 승격 대상
- **A**: `pages/promotion-queue.md` 후보로만 적재
- **B**: `pages/candidate-pool.md` 보관소로만 적재
- **BLOCK**: 수집 단계에서 폐기

Google News 쿼리 세트:
- 정밀 세트: `config/google-news-queries-precise.txt`
- 확장 세트: `config/google-news-queries-broad.txt`
- 기존 `config/google-news-queries.txt`는 fallback

### 4) 상태 점검(문제 없더라도 주기적으로)
헬스 체크:
```bash
./scripts/check_automation_health.sh
```
점수 계산:
```bash
python3 scripts/compute_perfect_scorecard.py
```

### 5) Git 운영(자동화와 충돌 방지)
- 자동화 실행 후 변경사항이 쌓이면 `git status`로 확인합니다.
- daily update가 의도한 변경이라면 커밋/푸시합니다.
- 충돌/오염을 피하기 위해, 실험은 별도 브랜치에서 진행하는 것을 권장합니다.

---

## 🛠️ 트러블슈팅

### A. Exec failed (signal SIGKILL)
증상:
- 실행 중 프로세스가 강제 종료(SIGKILL)

원인 후보:
- 메모리/CPU 제한, OOM killer
- 너무 큰 단일 작업(대량 수집/대량 파싱/대량 링크 체크)

대응:
1. 큰 작업 대신 **마이크로 백필**로 전환
   ```bash
   ./scripts/run_backfill_micro.sh
   ```
2. 병렬도/단위 작업량을 줄이는 옵션이 있다면 낮춤(스크립트 옵션/환경변수 확인)
3. `pages/*report.md`와 `news/YYYY-MM-DD.md`에서 마지막 성공 지점 확인

### B. 링크 검사 실패/죽은 링크 증가
1. `pages/lint-report.md`에서 도메인/패턴 확인
2. 정책적으로 허용 가능한 도메인인지 `config/domain-grades.yml` 검토
3. 일시적 장애면 다음 실행에서 재시도(반복 실패 시 BLOCK 고려)

### C. 점수는 높지만 콘텐츠 누적(C)이 안 오름
- 정상일 수 있습니다. C는 “시간/백필로 누적되는 축”입니다.
- `run_backfill_micro.sh`를 주기적으로 돌려 **C_current를 천천히 올리는 전략**을 사용합니다.

### D. 문서/리포트는 있는데 실제 페이지가 비어 보임
- 링크-first 원칙에 따라 텍스트가 적고 링크 중심일 수 있습니다.
- 후보가 `candidate-pool`/`promotion-queue`로만 쌓이는지 확인하고,
  승격 규칙(도메인 등급, 증거/출처 조건)을 조정합니다.

---

## 📋 체크리스트

### 매일(데일리 업데이트 후 2분 점검)
- [ ] `news/YYYY-MM-DD.md` 오늘자 갱신됨
- [ ] `pages/daily-report.md` 치명적 에러 없음
- [ ] `pages/lint-report.md` BLOCK 급 이슈 폭증 없음
- [ ] `pages/perfect-scorecard.md`에서 A/B/D가 급락하지 않음
- [ ] `git status`에 예상치 못한 대량 변경 없음

### 주 1회(백필/정책 정리)
- [ ] `run_weekly_backfill.sh` 또는 slice 백필로 누락 구간 보강
- [ ] `config/domain-grades.yml`에 반복 실패 도메인 반영(BLOCK/등급 조정)
- [ ] `pages/candidate-pool.md`가 과도하게 커지면 정리 기준 검토

### 장애 발생 시(우선순위)
- [ ] `./scripts/check_automation_health.sh`
- [ ] `news/YYYY-MM-DD.md`에서 마지막 성공 단계 확인
- [ ] SIGKILL이면 대형 작업 중단 → micro backfill로 전환
- [ ] 필요 시 `python3 -m pytest -q`로 회귀 테스트

---

## 참고 문서
- 자동화 개요: `docs/ux-automation-system.md`
- 아키텍처: `docs/ARCHITECTURE.md`
- 점수 체계: `docs/scoring.md`

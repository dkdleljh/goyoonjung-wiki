# 고윤정 위키 고도화 계획: 전 생애 정보 수집과 완전 무인 자동화

> 작성일: 2026-06-04  
> 범위: `goyoonjung-wiki`의 수집 정확도, 공식 검증, 자동 업데이트, GitHub 커밋/푸시/릴리즈, 운영 복구 체계 고도화

## 0. 목표와 현실적 정의

이 프로젝트의 장기 목표는 **배우 고윤정의 과거, 현재, 미래 정보를 공식·신뢰 출처 기반으로 자동 수집하고, 검증 가능한 항목만 자동 업데이트하며, GitHub 반영까지 무인으로 운영하는 것**이다.

단, “모든 과거·현재·미래를 100% 자동 확정”하는 것은 외부 공개 여부, 공식 출처 존재 여부, 사이트 차단, 검색 색인 지연, 미래 일정 변경 가능성 때문에 증명할 수 없다. 따라서 운영 목표는 다음과 같이 정의한다.

- 공식 근거가 있는 정보는 자동 확정한다.
- 공식 근거가 부족한 정보는 본문에 단정하지 않고 검증 큐에 격리한다.
- 미래 정보는 루머, 단일 보도, 복수 보도, 공식 발표, 플랫폼 확정, 공개 완료 상태로 나눈다.
- 누락 가능성을 줄이기 위해 여러 수집기, 출처 등급, 충돌 감지, 정기 링크 검사, 자동 알림을 사용한다.
- 수집부터 테스트, 문서 생성, 커밋, 푸시, 릴리즈, 알림까지 사람이 개입하지 않아도 반복 가능하게 만든다.

## 1. 최종 목표 상태

| 영역 | 목표 상태 |
|---|---|
| 정보 수집 | 프로필, 필모그래피, 수상, 일정, 뉴스, 인터뷰, 화보, 브랜드, SNS, 미래 후보 자동 감지 |
| 공식 검증 | S/A/B/C/R 출처 등급으로 자동 분류 |
| 본문 반영 | 공식 또는 신뢰도 높은 출처만 자동 반영 |
| 미확정 정보 | 검증 큐와 미래 후보 페이지에 격리 |
| 자동화 | 수집 → 정규화 → 검증 → 문서 생성 → 테스트 → 커밋 → 푸시 → 릴리즈 → 알림 |
| 복구 | stale lock, notify queue, timer 중단, push 실패 자동 감지 및 복구 |
| 목표 점수 | automation_health 100, lint_clean 100, link_health 100, official_work_sync 95+, coverage_readiness 85+, wiki_completeness 85+ |

## 2. 수집 범위

### 2.1 프로필

- 이름, 영문명, 생년월일, 직업, 소속사, 활동 기간
- 출생지, 학력 등 공식 근거가 부족한 항목은 보조 참고로 분리
- 공식 소속사 프로필을 최우선 기준으로 사용

### 2.2 필모그래피

- 드라마, 영화, OTT 오리지널, 특별출연, 공개 예정작
- 작품별 역할명, 공개일, 플랫폼, 상태, 공식 링크 관리
- MAA 공식 필모그래피와 Netflix, Disney+, TVING, tvN, JTBC 등 플랫폼 공식 페이지를 교차 확인

### 2.3 수상 및 후보

- 백상예술대상, 청룡시리즈어워즈, 청룡영화상, 대종상, ACA & Global OTT Awards, 코리아 드라마 어워즈 등
- 공식 후보/수상자 페이지 또는 공식 영상이 확인된 항목만 `공식확정`으로 승격
- 보도 기반 항목은 검증 큐 유지

### 2.4 일정

- 작품 공개일, 제작발표회, 시사회, 인터뷰 공개, 브랜드 행사, 시상식 참석
- 미래 일정은 공식 발표 또는 플랫폼 공개일만 확정
- 보도 기반 일정은 후보 큐로 분리

### 2.5 뉴스/인터뷰/화보

- Google News, 국내 언론, 매거진 RSS, 공식 YouTube, KBS Starbox 등 수집
- 기사 전문 복제 금지, 링크 중심 요약 유지
- 인터뷰/화보는 원문 링크, 공개일, 매체명, 관련 작품/브랜드를 구조화

### 2.6 브랜드/광고

- 캠페인, 화보, 광고, 앰버서더, 프렌즈, 모델 여부 구분
- 브랜드 공식 페이지 또는 공식 SNS가 없으면 역할 단정 금지
- CHANEL 등 현재 검증 큐에 남은 항목을 우선 해소

### 2.7 SNS/공식 채널

- 본인 계정은 소속사/공식 프로필/공식 보도자료 교차확인 전까지 미확정 유지
- 소속사, 작품, 플랫폼, 브랜드 공식 채널을 우선 수집
- 사칭/동명이인 방지를 위해 자동 확정 조건을 엄격하게 둔다.

### 2.8 미래 정보

미래 정보는 아래 상태로 관리한다.

| 상태 | 의미 | 본문 반영 |
|---|---|---|
| `rumor` | 커뮤니티/비공식 추측 | 금지 |
| `reported_once` | 단일 보도 | 후보 큐 |
| `reported_multiple` | 복수 보도 | 후보 큐 + 보조 페이지 |
| `agency_confirmed` | 소속사 공식 확인 | 본문 반영 |
| `platform_confirmed` | 플랫폼/방송사 공식 확인 | 본문 반영 |
| `release_scheduled` | 공개일 확정 | 일정 반영 |
| `released` | 공개 완료 | 필모그래피 확정 |

## 3. 출처 등급 체계

| 등급 | 기준 | 자동 반영 |
|---|---|---|
| S | 소속사, 플랫폼, 방송사, 시상식, 브랜드 공식 페이지/공식 SNS | 가능 |
| A | 원문 보도, 공식 행사 취재, 공식 인터뷰 | 조건부 가능 |
| B | 신뢰 가능한 2차 자료 | 검증 큐 |
| C | 블로그, 커뮤니티, 검색 결과 조각 | 본문 반영 금지 |
| R | 루머, 미확정 캐스팅, 사생활 추측 | 격리 |

필수 보강 파일:

- `config/domain-grades.yml`
- `config/allowlist-domains.txt`
- `scripts/domain_policy.py`
- `docs/editorial_policy.md`

## 4. 수집기 고도화 계획

### 4.1 공식 플랫폼 수집기

신규 파일:

```text
scripts/auto_collect_official_platforms.py
```

대상:

- MAA
- Netflix
- Disney+
- TVING
- tvN
- JTBC
- YouTube 공식 채널

기능:

- 작품명/인물명 검색
- 역할명, 공개일, 플랫폼, 상태 추출
- 공식 링크 저장
- 기존 작품 페이지와 충돌 여부 점검

### 4.2 시상식 공식 수집기

신규 파일:

```text
scripts/auto_collect_awards_official.py
```

기능:

- 공식 후보/수상자 페이지 탐색
- `pages/awards.md`의 `검증불가` 항목을 공식 근거로 승격
- 근거가 없으면 검증 큐 유지

### 4.3 브랜드/광고 수집기

신규 파일:

```text
scripts/auto_collect_brands.py
```

기능:

- 브랜드 공식 페이지/SNS에서 고윤정 관련 캠페인 탐색
- 앰버서더, 프렌즈, 모델, 화보, 단순 착용을 구분
- 역할 불명확 시 본문 확정 금지

### 4.4 미래작 감지기

신규 파일:

```text
scripts/auto_detect_future_works.py
```

기능:

- “고윤정 차기작”, “고윤정 캐스팅”, “Go Youn-jung upcoming”, “Go Youn-jung Netflix” 등 검색
- 공식 발표 여부 판정
- 루머성 결과 격리
- `pages/future-watch.md`, `pages/future-candidates.md` 생성

### 4.5 사실 충돌 감지기

신규 파일:

```text
scripts/audit_fact_conflicts.py
```

기능:

- 같은 작품의 공개일/역할명/상태가 페이지마다 다른지 검사
- 중복 URL 제거
- 공식 근거보다 낮은 등급의 출처가 공식 사실을 덮어쓰지 못하게 차단

## 5. 구조화 데이터 도입

Markdown은 최종 산출물로 유지하되, 자동화 기준 데이터는 구조화한다.

신규 구조:

```text
data/facts/
  profile.json
  works.json
  awards.json
  schedules.json
  endorsements.json
  interviews.json
  sources.json
  future_candidates.json
```

예시:

```json
{
  "id": "work-can-this-love-be-translated",
  "type": "work",
  "title": "이 사랑 통역 되나요?",
  "person": "고윤정",
  "role": "차무희",
  "status": "released",
  "date": "2026-01-16",
  "sources": [
    {
      "url": "https://www.netflix.com/kr/title/81697769",
      "grade": "S",
      "checked_at": "2026-06-04T00:00:00+09:00"
    }
  ],
  "confidence": 100,
  "last_verified_at": "2026-06-04T00:00:00+09:00"
}
```

필수 도구:

- `scripts/extract_facts_from_markdown.py`
- `scripts/render_pages_from_facts.py`
- `scripts/audit_fact_conflicts.py`
- `scripts/source_confidence.py`

## 6. 완전 무인 자동화 파이프라인

목표 흐름:

```text
preflight
→ lock
→ remote fetch
→ 수집기 실행
→ 정규화
→ 출처 등급 평가
→ facts DB 업데이트
→ 충돌 검사
→ 검증 큐 갱신
→ Markdown 재생성
→ 링크 검사
→ 품질 점수 계산
→ 테스트
→ 커밋
→ 커밋 후 daily-report 재생성
→ amend
→ push retry
→ auto release
→ release docs sync
→ notify flush
→ 상태 기록
```

`run_daily_update.sh` 보강 항목:

- preflight 결과가 치명적이면 본 실행 중단
- dirty 상태가 자동 생성 파일인지 검증
- push 실패 시 원인 기록 및 다음 실행에서 재시도
- 릴리즈 준비 시 README/포털/CHANGELOG/daily-report가 같은 태그 기준으로 생성되도록 유지
- 알림 실패 시 queue에 남기고 flush timer가 재시도

## 7. 운영 안정성 고도화

### 7.1 preflight 검사

신규 파일:

```text
scripts/preflight_automation.py
```

검사 항목:

- git remote 접근 가능 여부
- `HEAD`와 `origin/main` 관계
- `.venv/bin/ruff`, `.venv/bin/bandit`, `.venv/bin/pytest` 존재
- 필수 config 존재
- webhook 설정 여부
- systemd timer 상태
- 디스크 여유 공간
- stale lock 여부
- 최근 성공 실행 시각

### 7.2 self-healing

신규 파일:

```text
scripts/self_heal_automation.py
```

자동 복구 가능 항목:

- stale lock 정리
- notify queue flush 또는 archive
- 누락 리포트 재생성
- 문서 포털 재생성
- user systemd timer 재시작

자동 복구 금지 항목:

- `git reset --hard`
- 강제 push
- 비밀값 생성/변경
- 대량 삭제

### 7.3 watchdog timer

신규 systemd 단위:

```text
goyoonjung-wiki-watchdog.timer
goyoonjung-wiki-watchdog.service
```

주기:

- 30분마다

역할:

- daily, sync, linkhealth, notifyflush timer 상태 점검
- 최근 성공 실행이 36시간 초과하면 경고
- dirty 상태가 오래 지속되면 경고
- GitHub 원격과 불일치하면 경고

## 8. 알림 체계

Discord 알림 유형:

- daily update 성공 요약
- 새 공식 정보 발견
- 미래작 후보 발견
- 검증 큐 증가
- 테스트 실패
- push 실패
- timer 중단
- 링크 BAD 발생
- webhook 실패/queue 누적

notify queue 개선:

- 메시지별 retry count
- 오래된 메시지 archive
- 같은 오류 중복 알림 억제
- webhook 미설정 시 disabled archive
- flush 결과 리포트 기록

## 9. 품질 점수 목표

현재 측정 기준을 다음 목표로 관리한다.

| 점수 | 현재 운영 목표 |
|---|---:|
| `automation_health` | 100 |
| `lint_clean` | 100 |
| `link_health` | 100 |
| `official_work_sync` | 95+ |
| `coverage_readiness` | 85+ |
| `wiki_completeness` | 85+ |

점수 개선 우선순위:

1. 검증 큐 21개 이하 → 5개 이하
2. `검증불가`, `추가 필요`, `미확정`, `참고(2차)` 표현 축소
3. 수상/후보 공식 근거 확보
4. 브랜드 역할 공식 근거 확보
5. SNS 본인 계정 공식 교차확인 전까지 미확정 유지

## 10. 실행 로드맵

### Phase 1. 자동화 안정화

- [x] `scripts/preflight_automation.py` 추가
- [x] `scripts/self_heal_automation.py` 추가
- [x] watchdog timer 추가
- [x] notify queue retry/archive 체계 보강
- [x] timer 상태 리포트 생성
- [x] automation_health 100 유지 검증 체계 연결

완료 기준:

- `bash scripts/check_automation_health.sh` 통과
- `make check` 통과
- `systemctl --user list-timers --all 'goyoonjung-wiki*'`에서 모든 핵심 timer가 next run 보유

### Phase 2. 공식 출처 수집 강화

- [x] 공식 플랫폼 수집기 추가
- [x] 시상식 공식 수집기 추가
- [x] 브랜드/광고 수집기 추가
- [x] 미래작 감지기 추가
- [x] 사실 충돌 감지기 추가

완료 기준:

- `official_work_sync >= 95`
- 공식 근거 없는 미래 정보가 본문에 자동 확정되지 않음
- 검증 큐가 자동 갱신됨

### Phase 3. 구조화 데이터 전환

- [x] `data/facts/*.json` 스키마 도입
- [x] Markdown → facts 추출기 추가
- [x] facts → Markdown 렌더러 추가
- [x] source confidence 계산기 추가
- [x] fact conflict/source report 추가

완료 기준:

- 주요 페이지가 facts에서 재생성 가능
- 동일 사실의 중복/충돌 감지 가능
- 변경 사항이 daily report에 요약됨

### Phase 4. 검증 부채 제거

- [x] 수상/후보 공식 근거 감시 체계 구축 (근거 미확보 항목은 큐 유지)
- [x] 브랜드 역할 공식 근거 감시 체계 구축 (역할 미확정 항목은 큐 유지)
- [x] 프로필 보조 참고 항목 분리 정책 유지
- [x] SNS 공식 확정 조건 유지
- [x] 품질 리포트와 검증 큐 자동 갱신

완료 기준:

- `coverage_readiness >= 85`
- `wiki_completeness >= 85`
- 검증 큐 5개 이하

### Phase 5. 완전 운영 체계

- [x] daily timer
- [x] sync timer
- [x] linkhealth timer
- [x] notifyflush timer
- [x] watchdog timer
- [x] backupcleanup timer
- [x] GitHub release automation
- [x] Discord alert
- [x] health dashboard

완료 기준:

- 7일 연속 무인 실행 성공
- 실패 발생 시 자동 복구 또는 알림 발생
- GitHub 원격이 매일 최신 상태 유지

## 11. 완료 판정 체크리스트

- [x] 공식 출처 기반 수집기가 주요 카테고리를 모두 담당한다.
- [x] 미확정 정보는 본문에 단정되지 않는다.
- [x] 미래 정보는 상태별로 격리된다.
- [x] facts 데이터와 Markdown 산출물이 일관된다.
- [x] 링크 건강검진이 정기 실행된다.
- [x] 품질 리포트, 검증 큐, 공식 커버리지 리포트가 매일 갱신된다.
- [x] `make check`가 통과한다.
- [x] `check_automation_health`가 통과한다.
- [x] 커밋/푸시/릴리즈/알림이 무인으로 완료된다.
- [x] 실패 시 원인 로그와 복구 경로가 남는다.

## 12. 구현 결과 문서

Phase 1~5 구현 결과와 실제 산출물은 다음 문서에서 관리한다.

- [Phase 1~5 구현 결과 보고서](phase5-implementation-report.md)
- [GitHub 자동화 문서](../.github/AUTOMATION.md)
- [운영 가이드](OPERATION_GUIDE.md)
- [릴리즈 정책](RELEASING.md)

## 12. 핵심 원칙

이 프로젝트의 고도화 방향은 “무조건 자동 확정”이 아니다.

정확한 목표는 다음이다.

> 공식 근거가 있는 것은 자동 확정하고, 공식 근거가 부족한 것은 자동으로 격리하며, 누락 가능성이 있는 영역은 계속 감시하고, 검증 가능한 변경만 무인으로 GitHub에 반영한다.

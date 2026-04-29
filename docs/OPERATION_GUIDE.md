# OPERATION GUIDE

이 문서는 고윤정 위키 저장소를 **실제로 운영하는 사람**을 위한 상세 가이드입니다.

문서의 목표는 단순합니다.

- 어떤 자동화가 있는지 이해하고
- 어디를 보면 상태를 판단할 수 있는지 알고
- 문제가 났을 때 빠르게 복구하고
- 문서와 코드가 어긋나지 않게 유지하는 것

---

## 1. 현재 운영 개요

이 저장소는 다음 세 층으로 운영됩니다.

### 1) 수집/정리 층
- 뉴스/기사/인터뷰/화보/영상 관련 링크 수집
- 후보 정리
- 승격/보류/백로그 분기

### 2) 리포트/검증 층
- lint / quality / status / kpi / dashboard 생성
- 링크 상태 확인
- 자동화 health 검사
- 점수 계산

### 3) 배포/이력 층
- git commit / push
- changelog 갱신
- semver 태그 생성
- GitHub Release 발행
- release notes 파일 업로드

---

## 2. 주요 엔트리포인트

### 2-1. daily 실행
```bash
./scripts/run_daily_update.sh
```

이 스크립트가 사실상 메인 러너입니다.

수행 항목 예시:
- 수집기 실행
- 후보/큐 업데이트
- dashboard/status 갱신
- 백업
- Git 반영
- release 자동화

### 2-2. health 확인
```bash
./scripts/check_automation_health.sh
```

확인 포인트:
- 오늘자 news 파일 상태
- 마지막 실행 결과
- working tree 이상 여부
- 자동화 스냅샷 일관성

### 2-3. 점수 확인
```bash
python3 scripts/wiki_score.py
```

현재 대표 출력 예시:
- `wiki_completeness`
- `lint_clean`
- `link_health`
- `automation_health`

---

## 3. 현재 무인 실행 구조

2026-04-29 기준 운영 경로:

```bash
/home/zenith/바탕화면/goyoonjung-wiki
```

사용자 systemd timer 기준:

```bash
systemctl --user list-timers --all | rg 'goyoonjung-wiki'
```

주요 유닛:
- `goyoonjung-wiki-daily.timer`: 매일 09:00 KST 전후 daily update 실행
- `goyoonjung-wiki-sync.timer`: 30분 간격 lightweight remote sync
- `goyoonjung-wiki-sync.path`: 비활성화 상태 유지 권장
- `goyoonjung-wiki-linkhealth.timer`: 주간 링크 상태 점검
- `goyoonjung-wiki-backupcleanup.timer`: 주간 백업 정리

중요: `sync_hub.sh`는 기본적으로 전체 daily update를 실행하지 않습니다. 전체 수집/커밋/푸시는 daily timer 또는 `SYNC_RUN_DAILY_UPDATE=1`을 명시한 수동 실행이 담당합니다.

---

## 4. 운영자가 가장 자주 보는 산출물

### 매일 확인 우선순위
1. `news/YYYY-MM-DD.md`
2. `pages/system_status.md`
3. `pages/daily-report.md`
4. `pages/lint-report.md`
5. `pages/quality-report.md`

### 릴리즈 관련
- `CHANGELOG.md`
- `logs/releases/release-notes-<tag>.md`
- GitHub Releases 페이지

---

## 5. 환경 준비

권장 방식:

```bash
cd /home/zenith/바탕화면/goyoonjung-wiki
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

실행 시 `run_daily_update.sh`는 `.venv`에 필수 런타임 패키지(`requests`, `yaml`)가 있을 때만 `.venv/bin`을 PATH에 포함합니다. 불완전한 `.venv`는 자동으로 무시합니다.

또한 `timeout`이 시스템에 없더라도 fallback이 동작하도록 구성되어 있습니다.

---

## 6. 운영 점검 절차

### 기본 점검
```bash
git status
bash scripts/check_automation_health.sh
python3 scripts/wiki_score.py
```

### 테스트 점검
```bash
make test
```

### 특정 핵심 테스트만 빠르게
```bash
PYTHONPATH=. pytest -q tests/test_project_paths.py tests/test_db_manager.py tests/test_security.py tests/test_wiki_score.py
```

---

## 7. 자주 발생하는 문제와 대응

### 7-1. stale lock
증상:
- “already running” 메시지 반복
- 실제로는 작업이 끝났는데 lock이 남아 있음

대응:
```bash
bash scripts/cleanup_stale_running.sh
```

### 7-2. DB schema 누락
증상:
- `no such table: ...`

현재는 `run_daily_update.sh` 내부에서 `scripts/db_manager.py`를 먼저 실행하도록 보강되어 있습니다.

### 7-3. timeout 명령 없음
증상:
- `timeout: command not found`

현재는 아래 중 하나로 대응됩니다.
- 시스템 `timeout`
- `gtimeout`
- Python fallback wrapper

### 7-4. release/tag 충돌
증상:
- 원격 태그 already exists

현재 `auto_release.sh`는 실행 전 원격 태그를 fetch 하도록 수정되어 있습니다.

---

## 8. 운영 원칙

- 자동화는 “많이 도는 것”보다 “예측 가능하게 도는 것”이 중요합니다.
- 산출물 위치가 바뀌면 문서도 같이 바꿉니다.
- 스코어가 좋아도 health가 나쁘면 운영 품질은 낮다고 봅니다.
- 릴리즈가 된다는 사실 자체보다, 릴리즈 노트가 설명 가능해야 합니다.

---

## 9. 문서와 함께 유지해야 하는 파일

다음 파일이 바뀌면 이 가이드를 같이 확인해야 합니다.

- `scripts/run_daily_update.sh`
- `scripts/check_automation_health.sh`
- `scripts/cleanup_stale_running.sh`
- `scripts/auto_release.sh`
- `scripts/generate_changelog.py`

---

## 10. 운영자의 한 줄 체크리스트

- 오늘자 daily가 돌았는가?
- health가 OK인가?
- score가 비정상 급락하지 않았는가?
- changelog/release가 최신 상태인가?
- 문서가 실제 코드와 일치하는가?

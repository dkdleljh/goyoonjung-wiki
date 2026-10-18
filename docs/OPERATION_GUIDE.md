# OPERATION GUIDE

> 2026-10-11 변경: 기본 사용자 서비스와 Docker 스케줄러는 COLLECT_ONLY=1로 수집합니다. 실제 상태는 `python scripts/operational_status.py`로 확인하세요. 최신 실행·릴리즈 정책은 [수정 및 운영 안내](review-remediation.md)와 [릴리즈 정책](RELEASING.md)을 따릅니다.


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

## 상시 수집 및 장애 복구 (2026-10-18)

- 실행 전용 체크아웃: `~/.local/share/goyoonjung-runtime/goyoonjung-wiki`. 개발 작업 폴더의 수정으로 게시가 막히지 않도록 분리한다. 설치/갱신은 `bash scripts/install_unattended.sh`로 수행한다.
- `goyoonjung-wiki-sync.timer`: 5분마다 뉴스·YouTube 우선 수집. 공식 원문은 10분, 사이트별 검색·잡지·후보 검토·과거 자료는 각 주기에 따라 순환하며, 실행당 추가 작업은 2개로 제한한다. 모든 출처를 매 5분마다 확인한다는 의미는 아니다.
- `goyoonjung-wiki-daily.timer`: 6시간마다 전체 정리. `goyoonjung-wiki-backup.timer`: 매일 04:35에 공개 문서와 수집 DB를 외부 저장소의 `automation-backups` 브랜치에 백업하고 다운로드 복원 검증을 수행한다. 자격 증명과 비공개 파일은 백업하지 않는다.
- `Collector failover` GitHub Actions는 5분 간격으로 예약된다. 주 서버의 기록이 20분 넘게 없거나 전체 실패이면 외부 백업으로 DB를 복원하여 대체 수집한다. 주 서버 복귀 전까지 대체 수집을 계속한다. GitHub 예약 실행은 지연될 수 있으므로 엄격한 실행 시간이나 무중단을 보장하지 않는다.
- `automation-health`는 15분마다 수집 기록과 공개 사이트 응답/자료 신선도를 점검한다. 사이트 자체도 15분마다 저장소 변경을 확인해 배포한다. 주 서버는 수집 게시 후 즉시 배포를 요청한다.
- 수집 실패는 체크포인트를 진전시키지 않는다. 출처별 재시도 시 마지막 성공 시점 전 2일을 겹쳐 조회한다. 과거 잡지/YouTube 수집은 페이지별로 이어가며, 검색으로 관측한 범위를 과거 전체 수집 완료로 표시하지 않는다.
- 샤넬·부쉐론 등의 HTTP 403은 접근 제한 상태로 남긴다. 정상 출처 결과는 계속 저장·게시하지만 전체 결과는 부분 성공으로 표시할 수 있다. 페이지에 접근했다는 사실과 그 내용의 사실 확정은 구분한다.
- 신규 작품은 공식 원문에서 배우·작품·출연 확정 관계를 확인한 주장만 자동 반영한다. 상충하는 주장은 보류하고, 취소·철회되면 검토 상태로 돌린다. 사진이 없는 신규 작품도 안내 영역과 상세 페이지가 정상 생성된다.
- 실측: `pages/automation-measurements.md`, 출처별 결과: `pages/source-collection-status.md`, 백업 검증: `data/reports/remote-backup.json`. 수집률·정확도는 독립 정답 집합이 없어 미측정이며, 점검 점수를 사실 정확도로 해석하지 않는다.

점검 명령:

```bash
systemctl --user list-timers 'goyoonjung-wiki-*'
journalctl --user -u goyoonjung-wiki-sync.service -n 60 --no-pager
# 외부 복구 훈련: 주 서버 수집과 겹치지 않는 시간에 실행
# gh workflow run collector-failover.yml --repo dkdleljh/goyoonjung-wiki -f force=true
```

GitHub Pages 응답의 `Cache-Control: max-age=600`에 따라 문서 주소별 캐시가 최대 10분 남을 수 있다. 배포 CI는 `verify_website_sync.py --artifact-urls`로 실제 배포 파일 전체를 검증하며, 기본 실행은 방문자용 디렉터리 주소까지 엄격하게 확인한다. 두 검증 범위는 결과의 `url_scope`에 명시한다. 5분 수집 주기는 모든 방문자에게 5분 이내 표시됨을 보장하지 않는다.

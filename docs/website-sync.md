# 홈페이지 동기화와 운영

공개 주소: https://dkdleljh.github.io/goyounjung/

## 원본과 실행 경로

- 위키의 유일한 운영 원본은 `/home/zenith/goyoonjung-wiki`다. 수집 데이터, SQLite, 상태, Python 환경과 코드가 함께 있다.
- 과거 `/home/zenith/.local/share/goyoonjung-runtime/goyoonjung-wiki`는 같은 원본을 가리키는 호환 심볼릭 링크다. 별도 복사본을 편집하지 않는다.
- 웹 코드 원본은 `/home/zenith/goyounjung`, 공개 문서 원본은 위키 GitHub main이다. 웹 `.wiki`는 로컬 위키를 가리킨다.
- 원격 소스 변경은 clean main에서 fast-forward로만 받는다. 수동 변경이나 분기는 보존한 채 중단하며 강제 푸시하지 않는다.

## 실행 주기 (한국 시간)

| 작업 | 실제 설정 | 역할 |
|---|---|---|
| 빠른 수집·게시 | 매 5분, `goyoonjung-wiki-sync.timer` | `run_fast_sync.sh`로 주요 뉴스·영상과 순환 수집, 변환, GitHub 게시 |
| 일일 전체 작업 | 00:02·06:02·12:02·18:02 | `collect_and_sync_website.sh`로 전체 수집·인덱스·백업·게시 |
| 원격 백업 | 04:35 | 공개 자료와 SQLite를 별도 GitHub 브랜치로 보내고 다시 내려받아 복원 검증 |
| 로컬 웹 빌드 | 매시 02분부터 5분 간격 | 커밋된 원본으로 격리 빌드·테스트·링크 검사 후 미리보기 교체 |
| 공개 웹 빌드 | 사이트 main push / dispatch / GitHub 15분 예약 | 원본 커밋이 달라졌을 때만 빌드 |

일일 작업은 빠른 수집 잠금이 풀리기를 최대 900초 기다린다. 실제 오류에는 systemd가 5분 뒤 재시도한다. 같은 호스트에서는 단일 OS 파일 잠금으로 수집·게시를 보호한다. 사용자 linger와 Persistent 타이머로 로그인 여부와 놓친 예약을 처리한다. GitHub 예약 실행은 지연될 수 있으며 분 단위 복구 SLA를 의미하지 않는다.

## 상태 판정

- 빠른 작업의 실제 완료 시각과 단계는 `data/reports/heartbeat.json`에 기록한다.
- 일일 작업의 완료 시각, 각 단계 종료 코드, 성공/부분성공/실패는 `data/reports/daily-status.json`에 기록한다. `.locks/last-run-status.txt`도 종료 때 갱신한다.
- 선택 외부 출처의 부분 실패는 경고로 보존하고, 핵심 수집·자료 변환·인덱스·게시 실패는 서비스 실패로 보고한다. 부분성공을 완전 성공으로 쓰지 않는다.
- 원격 health 검사는 빠른 작업뿐 아니라 일일 결과의 실패·노후화도 확인한다.
- GitHub 게시 성공은 곧바로 공개 반영 성공이라는 의미가 아니다. 공개 사이트의 `sync.json`과 Actions 배포 결과로 확인한다.

## 배포 검사와 최신 화면

웹 배포는 단위 검사 → 사진 없는 신규 작품 검사 → 실제 빌드 → 내부 링크 검사 → Chromium 검색·분류·사진·모바일 검사 → Pages 업로드 순서다. 실패하면 기존 공개 사이트를 유지한다.

`sync.json`에는 위키/사이트 커밋, 원본 해시, 빌드 시각, 실제 수집 결과가 있다. `artifact-manifest.json`에는 배포 파일의 SHA-256이 있다. 배포 후 검증은 빌드에 사용한 커밋을 고정해서 수행하며, 검사 도중 새로운 원본 커밋으로 바뀌어도 이전 배포를 잘못 실패시키지 않는다.

디렉터리 주소와 `index.html` 주소는 CDN에서 서로 다른 캐시를 받을 수 있다. 각각의 검사 범위를 구분한다. 페이지 진입 시 최신 배포 정보를 확인해 오래된 화면이면 버전 URL로 한 번 갱신하며, 읽는 중에는 새 자료 안내 링크를 제공한다. 배포 정보 요청이 실패하면 읽을 수 있는 기존 페이지를 유지한다.

로컬 미리보기는 http://127.0.0.1:4322/goyounjung/ 이다. `goyounjung-preview.service`가 검증된 릴리스만 제공한다. 새 빌드가 실패하면 이전 릴리스를 유지한다. 수동으로 Astro preview를 띄운 오래된 프로세스에 의존하지 않는다. 공개 배포와 로컬 빌드는 별도 시점일 수 있으므로 `sync.json`의 원본 커밋으로 대조한다.

웹 의존성의 호환 자동 업데이트는 테스트와 빌드를 통과한 lockfile만 커밋·푸시한다. 다른 편집·원격 분기·예상하지 않은 저장소는 자동 게시하지 않는다. 실패한 푸시는 안전 조건을 다시 검사한 뒤 재시도한다. main push가 전체 웹 배포 검사를 실행한다.

## 콘텐츠 보존과 외부 출처

자동 후보 생성기는 `AUTO-CANDIDATES` 마커 내부만 갱신하고 앞뒤 사진과 수동 설명을 보존한다. 외부 원문은 복제하지 않고 제목·URL·제한된 검증 메타데이터를 사용한다. 개별 사실은 원문 근거로 검토하며 후보·미확정 자료를 확정 사실로 승격하지 않는다.

- XML 파서는 누락된 media namespace와 XML 1.0에서 금지된 제어 바이트만 제한적으로 보정하고 보정 사실을 기록한다. 구조가 깨진 RSS나 HTML 응답은 여전히 실패다.
- 공식 출처가 계속 실패하면 최대 24시간까지 재시도를 늦춘다. 대기 중에는 마지막 실패 시각·횟수·내용을 유지하며 성공이나 새 확인으로 만들지 않는다.
- 실제 404/410 원문은 웹에서 확인 불가 표시로 보존한다. HTTP 403, TLS 오류, 일시 오류를 삭제로 단정하지 않는다. 인증서 검증은 끄지 않는다.
- POST 검색 API는 일반 GET 게시물 링크와 구분한다. 소속사 MAA의 과거 프로필은 종료 근거를 보존한 역사적 출처이며 활성 수집 대상이 아니다.
- Google News·유튜브의 실패는 새 자료 0건과 구분한다. 확인할 수 없는 후보는 검증 대기열에 보존한다.

## 운영 명령

```sh
systemctl --user status goyoonjung-wiki-sync.service goyoonjung-wiki-daily.service
systemctl --user list-timers 'goyoonjung*' 'goyounjung*'
cd /home/zenith/goyoonjung-wiki
.venv/bin/python scripts/operational_status.py --alerts
.venv/bin/python scripts/daily_status.py
# 현재 로컬 원본과 공개 최신 main의 엄격한 대조
.venv/bin/python scripts/verify_website_sync.py --wait 900
# 실제 파일 URL은 별도 캐시 범위로 검사
.venv/bin/python scripts/verify_website_sync.py --artifact-urls --wait 900
```

전체 콘텐츠의 사실 정확도, 모든 인터넷 자료의 수집률, 외부 서비스의 가동을 보장하지 않는다. 기록된 성공은 명시된 검사 범위에 한정한다.

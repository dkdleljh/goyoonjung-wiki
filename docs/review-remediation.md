# 2026-10-11 검토 후 수정

## 출처와 작품 상태

근처에 있는 URL을 다른 작품의 근거로 자동 연결하던 기능을 중단했다. 기존 자동 연결 115곳은 `data/quarantine/legacy-alternative-proofs.json`에 원문과 위치를 보관하고 본문에서 회수했다. 원래 출처는 유지했다.

`suggest_alternative_proofs.py`는 동일 행의 링크만 검토 후보로 제시한다. 접근 가능성이나 사실의 일치를 보증하지 않는다. 승인할 항목은 `data/reviewed_alternative_proofs.json`의 `items`에 복사하고 `claim_id`, `reviewed_by`, ISO 날짜 형식의 `reviewed_at`, `review_status: approved`를 기록한다. `apply_alternative_proofs.py`는 원문 행이 정확하게 한 곳에 남아 있을 때만 적용한다. 후보 재생성은 승인 기록을 덮어쓰지 않는다.

공개 상태는 명시적인 문구를 읽는다. 과거 연도나 플랫폼 이름만으로 공개 또는 공식 확정으로 승격하지 않는다. 미공개·루머·검토는 unknown, 공개 예정은 reported_once, 공개됨·종영 등은 released로 분류한다. 추출은 원문을 구조화하는 작업이며 독립적인 사실 검증은 아니다. 미래 후보는 자동 확정하지 않는다.

## 실측 상태와 링크 검사

`python scripts/operational_status.py`는 실행 기록을 읽기만 하며 부분 실패를 그대로 표시한다. 자동화 알림에는 `--alerts`를 사용한다. 30분 이상 지난 heartbeat·핵심 뉴스/유튜브 수집 성공 기록, 미래 시각, 핵심 수집·변환 실패, 비정상 종료는 실패한다. 선택적 외부 출처 수집의 종료 코드 1은 경고로 표시하고 출처별 실패 기록을 보존한다. `automation-health`는 15분 간격으로 예약되어 있으며 실제 시작은 GitHub 스케줄 지연이 있을 수 있다. 공개 웹사이트 수집 기록도 1시간 이내인지 별도로 검사한다.

배포 검증은 빌드 단계에서 기록한 위키 SHA와 웹사이트 SHA를 고정한다. 배포 중 `main`이 갱신되어도 해당 배포의 전체 원문 목록·해시·공개 산출물을 검사한다. 인자 없이 실행하는 로컬 검증은 계속 최신 `main`과 비교한다. 릴리스의 태그 검색은 출력을 끝까지 읽어 태그 수가 많아져도 SIGPIPE(141)가 발생하지 않도록 한다. 발행기는 GitHub checkout의 `.git` 생략 URL도 허용하되 저장소 소유자·이름은 정확히 검사한다.

대시보드는 기록에 없는 소요 시간·가동률을 null로 표시한다. 성공률은 날짜별 마지막 실행 기록의 표본 비율이다. 호스트 자원과 자동화 상태는 별개다. `/healthz`는 서버 생존 여부이고 `/api/status`의 `automation`은 수집 상태다. 실행 API는 읽기 전용임을 알리는 501 응답을 반환한다. WebSocket은 현재 접속 주소와 HTTPS 여부를 따른다.

HTTP 404/410은 오류, 네트워크 차단은 경고, 스킵 및 검사 한도 밖 주소는 UNCHECKED로 기록한다. 점수는 모든 발견 URL 대비 확인된 OK 비율이며 오류가 있으면 0이다. 오래된 리포트 및 미검사 주소를 정상으로 올려 잡지 않는다. 오류 주석은 Markdown 링크 밖에 붙인다.

404 중 두 주소는 기사 제목·발행일·내용을 대조하여 교체했다. 확인 기록은 `data/quarantine/reviewed-link-repairs.json`에 있다. 나머지 원문은 복원 여부와 인터뷰 대상을 확인할 수 없어 `data/quarantine/unverified-interviews.json`에 원문 기록을 보관하고 본문·자동 목록에서 회수했다. 외부 사이트의 삭제·차단은 코드 수정으로 복구할 수 없다.

## 실행 및 배포

```bash
make venv
COLLECT_ONLY=1 bash scripts/run_daily_update.sh
.venv/bin/python -m uvicorn scripts.web_dashboard:app --host 127.0.0.1 --port 8000
```

로컬 수집 모드는 Git 저장소 없이 동작하며 커밋·푸시·릴리즈·알림 전송을 하지 않는다. 일부 작업 실패는 부분성공 및 종료 코드 1로 남긴다. 수집기 한 단계의 최대 실행 시간은 기본 180초다. 외부 접근 실패가 있으면 실제 원인이 기록되며 성공으로 덮지 않는다.

```bash
docker compose up -d --build wiki
docker compose --profile automation up -d --build scheduler
```

scheduler는 실행 후 6시간 간격으로 로컬 수집을 반복한다. wiki만 실행하면 수집기는 시작되지 않는다. 컨테이너에는 대시보드 의존성과 Markdown 자료가 포함된다. 호스트 타이머와 Docker 스케줄러는 동시에 실행하지 않는다.

호스트 타이머는 `deploy/systemd/goyoonjung-wiki-daily.{service,timer}`를 사용자 systemd 디렉터리에 설치한다. 기본 경로는 `%h/goyoonjung-wiki`이며 다른 위치는 WorkingDirectory를 override한다. 사용자 서비스가 로그아웃 후에도 실행되어야 한다면 해당 호스트의 user service 유지 설정을 확인한다.

릴리즈는 성공한 `ci`의 정확한 SHA에만 태그를 붙인다. 릴리즈 도중 VERSION·문서 생성·커밋·병합을 하지 않는다. 원격 main이 이미 앞섰으면 다음 CI를 기다린다. 수동 릴리즈도 성공한 main CI run ID가 필요하다. 태그 업로드 이후 Release 생성이 실패하면 실패를 반환하며 재시도는 같은 태그를 사용한다. VERSION은 소스 메타데이터이고 실제 배포 버전의 기준은 Git 태그다. 문서·VERSION 변경이 필요하면 CI 실행 전에 변경한다.

## 검증

- 전체 pytest 및 출처·상태·HTTP 오류·대시보드 회귀 테스트
- 임시 로컬 Git 원격에서 CI 불일치, main 경합, 정확한 태그 대상, 게시 실패와 재시도 테스트
- 실제 셸 조정기를 Git 없는 환경에서 실행하여 성공/부분 실패와 푸시·알림 미실행 확인
- Ruff, Bandit, Python 컴파일, ShellCheck
- Docker 이미지 빌드 및 실제 HTTP 대시보드 기동 확인

원격 GitHub에는 아직 이 수정사항을 게시하지 않았다. 코드 검증 통과는 외부 자료의 완전성 또는 모든 수집원의 접근 가능성을 뜻하지 않는다.

## 이 호스트의 실행 확인

2026-10-11 로컬 수집을 실행하여 수집·리포트·백업 단계까지 완료했다. 소속사 접근 시간 초과와 수상 근거 확인 시간 제한을 부분 실패로 기록했다. 사용자 systemd의 daily.timer를 활성화했으며 6시간 간격으로 COLLECT_ONLY=1 모드를 실행한다. 수집기 하나가 실패해도 다른 수집 결과는 보존하고 최종 상태를 부분성공으로 표시한다.

최종 로컬 검증: Python 3.13 전체 294개 통과. Docker Python 3.12 검증과 이미지 빌드·HTTP 기동도 확인했다. 링크 재검사(362 URL)는 OK 294, WARN 4, BAD 0, UNCHECKED 64였다. BAD 0은 격리된 기사 원문의 복구를 뜻하지 않는다.

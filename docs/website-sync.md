# 홈페이지 동기화

- 공개 주소: https://dkdleljh.github.io/goyounjung/
- 홈페이지 소스: https://github.com/dkdleljh/goyounjung
- 콘텐츠 원본: 이 저장소의 `main` 브랜치. 홈페이지에서 내용을 별도로 수정하지 않습니다.

## 자동 경로

이 호스트의 `goyoonjung-wiki-daily.timer`가 6시간마다 수집합니다. `collect_and_sync_website.sh`가 원격 main 확인 → 수집 → 문서 커밋·푸시 → 홈페이지 배포 → 실제 공개 결과 검증을 수행합니다. 별도의 `goyoonjung-wiki-sync.timer`는 15분 간격으로 수동 콘텐츠 편집과 미완료 게시를 재시도합니다. 수집과 게시가 같은 파일 잠금을 사용하며, 잠금 충돌은 종료 코드 75로 다음 실행에 넘깁니다.

호스트가 켜져 있고 인터넷과 기존 `gh` 로그인이 유효해야 합니다. 원격 변경은 로컬이 깨끗하고 fast-forward가 가능할 때만 자동으로 내려받습니다. 로컬 변경과 원격 변경이 동시에 있거나 분기되면 보존한 채 중단합니다. 홈페이지도 GitHub Actions에서 6시간마다 위키 main을 다시 읽습니다.

## 검증 범위

- 로컬 위키 HEAD와 GitHub main, 홈페이지 `sync.json`의 위키·사이트 커밋을 비교합니다. 로컬 홈페이지 체크아웃이 있으면 이 저장소도 깨끗하고 원격 main과 같아야 합니다.
- Git이 추적하는 공개 Markdown 전체와 프로필·작품 JSON의 파일 목록 및 SHA-256을 대조합니다. 작성용 templates/checklists, 실행 DB·로그·비밀 설정은 공개 대상이 아닙니다.
- `artifact-manifest.json`으로 실제 공개 HTML·검색 색인·CSS 등 모든 배포 파일을 다운로드하여 빌드 결과의 SHA-256과 비교합니다. 각 위키 페이지에도 원본 해시를 표시해 출처를 연결합니다.
- 배포가 필요한 게시에서는 최대 15분 동안 실제 반영을 기다립니다. GitHub 배포 작업도 공개 파일을 검증하고 불일치 시 실패합니다. 변경 없는 정기 확인에서는 원본 해시까지만 검사합니다.
- 최신 결과는 `.locks/website-sync-status.json`, 마지막 전수 검사 성공 결과는 `.locks/website-sync-full.json`에 저장됩니다. 검증은 그 시점의 스냅샷을 확인하며 이후 변경까지 보장하지 않습니다.

```sh
# 실제 공개 파일 전수 검사
.venv/bin/python scripts/verify_website_sync.py --wait 120
# 원격 확인, 안전한 콘텐츠 게시 및 필요 시 배포 검증
.venv/bin/python scripts/publish_website_content.py
systemctl --user status goyoonjung-wiki-daily.timer goyoonjung-wiki-sync.timer
journalctl --user -u goyoonjung-wiki-sync.service -n 80
```

## 업로드 조건

수집은 `COLLECT_ONLY=1`로 실행합니다. 게시기는 완료된 성공/부분성공 기록을 확인하고, 지정된 pages/sources/news/data/facts/data/reports 및 index.md/README.md/docs/README.md/alternative_proofs.json 문서만 커밋합니다. 코드 변경, 알 수 없는 파일, 손상 JSON, 진행 중 수집, 원격 분기가 발생하면 업로드를 중단합니다. 삭제도 변경으로 기록됩니다. 강제 푸시 및 알림 전송은 하지 않습니다. 부분성공 시 홈페이지에 그 사실을 표시하고 수집 서비스는 실패 상태를 유지합니다.

수동 코드 변경은 검토·테스트 후 별도 커밋하고 푸시해야 자동 게시가 재개됩니다. 충돌 시 로컬 변경을 보존하고 원격 main과 병합한 뒤 다시 실행하세요. 홈페이지 코드도 로컬에서 자동 커밋하지 않습니다.

GitHub 예약 실행은 지연되거나 장기 비활동 시 중지될 수 있습니다. 웹사이트는 마지막 배포를 계속 제공합니다. 수집 시간이 36시간을 넘으면 화면에 확인 필요 상태를 표시합니다. 사이트 재배포로 수집 시간을 갱신하지 않습니다.

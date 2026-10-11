# 홈페이지 동기화

- 공개 주소: https://dkdleljh.github.io/goyounjung/
- 홈페이지 소스: https://github.com/dkdleljh/goyounjung
- 원본: 이 저장소의 `main` 브랜치. 홈페이지에서 내용을 별도로 수정하지 않습니다.

## 자동 경로

이 호스트의 `goyoonjung-wiki-daily.timer`가 6시간마다 수집하고 `collect_and_sync_website.sh`로 GitHub 업로드 및 홈페이지 배포 요청을 수행합니다. 호스트가 켜져 있고 인터넷과 기존 `gh` 로그인이 유효해야 합니다. 홈페이지도 GitHub Actions에서 6시간마다 원본 main을 다시 읽습니다. 수동 위키 편집을 GitHub에 올렸을 때도 다음 정기 배포에 반영됩니다. 즉시 반영하려면:

```sh
gh workflow run deploy.yml --repo dkdleljh/goyounjung
```

홈페이지 워크플로는 빌드·테스트·내부 링크 검증을 통과한 결과만 Pages로 배포합니다. `/goyounjung/sync.json`의 `revision`으로 반영된 위키 커밋을 확인할 수 있습니다.

## 업로드 조건

수집은 `COLLECT_ONLY=1`로 실행합니다. 별도 게시기가 완료된 성공/부분성공 기록을 확인하고, 지정된 pages/sources/news/data/facts/data/reports 및 index.md/README.md/docs/README.md/alternative_proofs.json 문서만 커밋합니다. 코드 변경, 알 수 없는 파일, 손상 JSON, 진행 중 수집, 원격 분기가 발생하면 업로드를 중단합니다. 삭제도 변경으로 기록됩니다. 강제 푸시 및 알림 전송은 하지 않습니다. 부분성공 시 홈페이지에 그 사실을 표시하고 systemd는 실패 상태를 유지합니다.

수동 코드 변경은 검토·테스트 후 별도 커밋하고 푸시해야 자동 게시가 재개됩니다. 원격 변경이 생기면 로컬 변경을 먼저 보존하고 원격 main과 병합한 뒤 다시 실행하세요. 자동으로 충돌을 덮어쓰지 않습니다.

```sh
systemctl --user status goyoonjung-wiki-daily.timer
journalctl --user -u goyoonjung-wiki-daily.service -n 80
.venv/bin/python scripts/publish_website_content.py
```

GitHub 예약 실행은 지연되거나 장기 비활동 시 중지될 수 있습니다. 웹사이트는 마지막 정상 배포를 계속 제공합니다. 수집 시간이 36시간을 넘으면 화면에 확인 필요 상태를 표시합니다. 새 수집을 수행하지 않은 사이트 재배포로 수집 시간을 갱신하지 않습니다.

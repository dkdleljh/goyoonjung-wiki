# 릴리즈 정책

GitHub Actions의 `ci`가 main 커밋을 검증한 뒤 `release`가 동일한 SHA에 태그와 GitHub Release를 만든다. 릴리즈 작업 자체는 소스, VERSION, 문서, 커밋 이력을 변경하지 않는다.

## 조건

- `RELEASE_SHA`가 현재 checkout의 HEAD와 일치해야 한다. detached checkout도 가능하다.
- 작업 트리는 깨끗해야 한다.
- `CI_RUN_ID`가 가리키는 실행은 `ci`, main, push 또는 workflow_dispatch 실행이며 성공해야 한다.
- CI의 headSha가 RELEASE_SHA와 일치해야 한다.
- 원격 main이 앞섰으면 새 커밋의 CI를 기다린다. 병합하거나 강제 푸시하지 않는다.

수동 실행도 release workflow의 `ci_run_id` 입력이 필요하다. 검증이 없는 수동 태깅 우회 경로는 제공하지 않는다.

## 태그와 노트

`vMAJOR.MINOR.PATCH`를 사용한다. BREAKING CHANGE 또는 `!:`가 있으면 major, 기능·설정 변경은 minor, 나머지는 patch로 올린다. 날짜 형태의 과거 태그는 canonical 기준에서 제외한다.

노트는 임시 파일에 검증 SHA, CI run ID, 변경 커밋 목록을 기록하여 GitHub Release 본문으로 사용한다. 태그는 정확한 검증 커밋을 가리킨다. 노트 파일을 저장소에 커밋하거나 추가 자산으로 업로드하지 않는다.

VERSION, CHANGELOG, 포털 문서의 변경이 필요하면 검증받을 커밋에 미리 포함한다. 실제 배포 버전의 기준은 Git 태그다. 릴리즈 작업 중 메타데이터를 자동 커밋하지 않으므로 검증되지 않은 새 커밋에 태그가 붙지 않는다.

## 실패와 재시도

태그 푸시 또는 Release 생성 실패는 종료 코드에 반영된다. 태그 푸시 후 Release 생성만 실패한 경우 같은 CI 실행으로 재시도하면 이미 해당 커밋에 붙은 태그를 재사용한다. 태그 대상이 충돌하면 강제로 교체하지 않는다.

`run_daily_update.sh`는 릴리즈를 직접 실행하지 않는다. GitHub 게시를 포함하는 일일 수집 모드에서도 태그는 이후 CI가 성공했을 때만 만들어진다. `COLLECT_ONLY=1`은 로컬 수집·자료 갱신만 수행한다.

## 검증

```bash
PYTHONPATH=. .venv/bin/pytest -q tests/test_release_integrity.py
```

테스트는 임시 로컬 Git 원격과 가짜 GitHub CLI를 사용하여 정확한 SHA, CI 불일치, 원격 main 경합, 게시 실패 및 재시도를 검사한다. 실제 GitHub 태그나 Release를 만들지 않는다.

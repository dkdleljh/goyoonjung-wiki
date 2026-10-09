# v1.58.2

- generated_at: 2026-10-10 02:00:33 KST
- bump: patch
- base: v1.58.1
- head: 8e0aed30

## Summary

- bump: **patch**
- base: v1.58.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.58.2
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.58.1...v1.58.2
- expected_scope: collectors / promotion / dashboard / automation pipeline

## Validation

- 릴리즈 준비 시점에 작성된 노트입니다.
- 코드 검증: 해당 커밋의 ci 워크플로우 결과를 확인하세요.
- 게시 결과: GitHub 태그와 Release 페이지의 실제 생성 여부로 확인하세요.

## Risk

- level: medium
- reason: daily automation and release pipeline changes may affect unattended runs

## Rollback

1. git checkout v1.58.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.58.2 if rollback is published separately

## Changes

- fix: persist generated release portals instead of ignoring a missing path (8e0aed30)

## Assets

- release-notes-v1.58.2.md

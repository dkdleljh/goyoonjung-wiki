# v1.28.2

- generated_at: 2026-05-31 03:42:11 KST
- bump: patch
- base: v1.28.1
- head: 33e3417c

## Summary

- bump: **patch**
- base: v1.28.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.28.2
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.28.1...v1.28.2
- expected_scope: collectors / promotion / dashboard / automation pipeline

## Validation

- changelog_sync: OK
- git_push_main: OK
- git_push_tag: OK
- github_release_upsert: OK

## Risk

- level: medium
- reason: daily automation and release pipeline changes may affect unattended runs

## Rollback

1. git checkout v1.28.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.28.2 if rollback is published separately

## Changes

- chore: link health 2026-05-31 (33e3417c)

## Assets

- release-notes-v1.28.2.md

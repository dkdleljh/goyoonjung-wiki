# v1.13.3

- generated_at: 2026-05-17 04:01:04 KST
- bump: patch
- base: v1.13.2
- head: 0f02b42e

## Summary

- bump: **patch**
- base: v1.13.2

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.13.3
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.13.2...v1.13.3
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

1. git checkout v1.13.2
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.13.3 if rollback is published separately

## Changes

- chore: link health 2026-05-17 (0f02b42e)

## Assets

- release-notes-v1.13.3.md

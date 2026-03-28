# v1.5.4

- generated_at: 2026-03-29 03:46:29 KST
- bump: patch
- base: v1.5.3
- head: ba6d948d

## Summary

- bump: **patch**
- base: v1.5.3

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.5.4
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.5.3...v1.5.4
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

1. git checkout v1.5.3
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.5.4 if rollback is published separately

## Changes

- chore: link health 2026-03-29 (ba6d948d)

## Assets

- release-notes-v1.5.4.md

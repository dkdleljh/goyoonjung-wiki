# v1.24.0

- generated_at: 2026-05-26 09:10:20 KST
- bump: minor
- base: v1.23.1
- head: 10b707d2

## Summary

- bump: **minor**
- base: v1.23.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.24.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.23.1...v1.24.0
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

1. git checkout v1.23.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.24.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-26 (10b707d2)
- daily: update 2026-05-26 (c0d0ebfd)

## Assets

- release-notes-v1.24.0.md

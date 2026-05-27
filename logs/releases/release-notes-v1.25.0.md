# v1.25.0

- generated_at: 2026-05-27 09:08:02 KST
- bump: minor
- base: v1.24.1
- head: 9ee2c43f

## Summary

- bump: **minor**
- base: v1.24.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.25.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.24.1...v1.25.0
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

1. git checkout v1.24.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.25.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-27 (9ee2c43f)
- daily: update 2026-05-27 (c4bb7e09)

## Assets

- release-notes-v1.25.0.md

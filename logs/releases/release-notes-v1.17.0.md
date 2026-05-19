# v1.17.0

- generated_at: 2026-05-19 09:12:45 KST
- bump: minor
- base: v1.16.0
- head: 8535b9a8

## Summary

- bump: **minor**
- base: v1.16.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.17.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.16.0...v1.17.0
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

1. git checkout v1.16.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.17.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-19 (8535b9a8)
- daily: update 2026-05-19 (50986112)

## Assets

- release-notes-v1.17.0.md

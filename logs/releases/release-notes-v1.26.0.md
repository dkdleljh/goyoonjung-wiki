# v1.26.0

- generated_at: 2026-05-28 09:08:16 KST
- bump: minor
- base: v1.25.1
- head: 0de829a6

## Summary

- bump: **minor**
- base: v1.25.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.26.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.25.1...v1.26.0
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

1. git checkout v1.25.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.26.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-28 (0de829a6)
- daily: update 2026-05-28 (dd1cff18)

## Assets

- release-notes-v1.26.0.md

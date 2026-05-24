# v1.22.0

- generated_at: 2026-05-24 09:10:05 KST
- bump: minor
- base: v1.21.2
- head: 315d19fc

## Summary

- bump: **minor**
- base: v1.21.2

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.22.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.21.2...v1.22.0
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

1. git checkout v1.21.2
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.22.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-24 (315d19fc)
- daily: update 2026-05-24 (101d40eb)

## Assets

- release-notes-v1.22.0.md

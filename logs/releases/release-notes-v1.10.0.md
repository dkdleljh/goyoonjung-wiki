# v1.10.0

- generated_at: 2026-04-30 15:35:40 KST
- bump: minor
- base: v1.9.0
- head: 9767d2c7

## Summary

- bump: **minor**
- base: v1.9.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.10.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.9.0...v1.10.0
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

1. git checkout v1.9.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.10.0 if rollback is published separately

## Changes

- routine: recommended (coverage+quality) 2026-04-30 (9767d2c7)
- chore: daily update 2026-04-30 (5fd5c837)

## Assets

- release-notes-v1.10.0.md

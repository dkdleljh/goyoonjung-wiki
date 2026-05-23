# v1.21.0

- generated_at: 2026-05-23 09:13:15 KST
- bump: minor
- base: v1.20.1
- head: f2f0d4da

## Summary

- bump: **minor**
- base: v1.20.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.21.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.20.1...v1.21.0
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

1. git checkout v1.20.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.21.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-23 (f2f0d4da)
- daily: update 2026-05-23 (2a869d49)

## Assets

- release-notes-v1.21.0.md

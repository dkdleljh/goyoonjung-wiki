# v1.30.0

- generated_at: 2026-06-01 09:07:58 KST
- bump: minor
- base: v1.29.0
- head: c8eaa6bb

## Summary

- bump: **minor**
- base: v1.29.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.30.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.29.0...v1.30.0
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

1. git checkout v1.29.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.30.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-06-01 (c8eaa6bb)
- daily: update 2026-06-01 (e9326b74)

## Assets

- release-notes-v1.30.0.md

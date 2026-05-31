# v1.29.0

- generated_at: 2026-05-31 09:12:01 KST
- bump: minor
- base: v1.28.2
- head: 9e96f7a0

## Summary

- bump: **minor**
- base: v1.28.2

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.29.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.28.2...v1.29.0
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

1. git checkout v1.28.2
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.29.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-31 (9e96f7a0)
- daily: update 2026-05-31 (229c2874)

## Assets

- release-notes-v1.29.0.md

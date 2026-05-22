# v1.20.0

- generated_at: 2026-05-22 09:12:13 KST
- bump: minor
- base: v1.19.1
- head: d484c71f

## Summary

- bump: **minor**
- base: v1.19.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.20.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.19.1...v1.20.0
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

1. git checkout v1.19.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.20.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-22 (d484c71f)
- daily: update 2026-05-22 (cbc0224b)

## Assets

- release-notes-v1.20.0.md

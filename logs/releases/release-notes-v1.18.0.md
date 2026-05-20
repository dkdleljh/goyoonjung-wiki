# v1.18.0

- generated_at: 2026-05-20 09:14:25 KST
- bump: minor
- base: v1.17.1
- head: 4548737f

## Summary

- bump: **minor**
- base: v1.17.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.18.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.17.1...v1.18.0
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

1. git checkout v1.17.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.18.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-05-20 (4548737f)
- daily: update 2026-05-20 (f0a18075)

## Assets

- release-notes-v1.18.0.md

# v1.5.0

- generated_at: 2026-03-27 18:30:16 KST
- bump: minor
- base: v1.4.1
- head: 7fcbc1c5

## Summary

- bump: **minor**
- base: v1.4.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.5.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.4.1...v1.5.0
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

1. git checkout v1.4.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.5.0 if rollback is published separately

## Changes

- feat(docs): auto-generate wiki doc portals (7fcbc1c5)

## Assets

- release-notes-v1.5.0.md

# v1.8.1

- generated_at: 2026-04-29 17:12:55 KST
- bump: patch
- base: v1.8.0
- head: 2f8e24c9

## Summary

- bump: **patch**
- base: v1.8.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.8.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.8.0...v1.8.1
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

1. git checkout v1.8.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.8.1 if rollback is published separately

## Changes

- docs: refresh release version references (2f8e24c9)

## Assets

- release-notes-v1.8.1.md

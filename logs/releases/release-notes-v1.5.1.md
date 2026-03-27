# v1.5.1

- generated_at: 2026-03-27 18:39:54 KST
- bump: patch
- base: v1.5.0
- head: 526844fd

## Summary

- bump: **patch**
- base: v1.5.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.5.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.5.0...v1.5.1
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

1. git checkout v1.5.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.5.1 if rollback is published separately

## Changes

- feat(docs): expand generated wiki doc indexes (526844fd)

## Assets

- release-notes-v1.5.1.md

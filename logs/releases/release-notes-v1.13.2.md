# v1.13.2

- generated_at: 2026-05-16 09:28:51 KST
- bump: patch
- base: v1.13.1
- head: a45cbf1e

## Summary

- bump: **patch**
- base: v1.13.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.13.2
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.13.1...v1.13.2
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

1. git checkout v1.13.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.13.2 if rollback is published separately

## Changes

- chore: record daily push recovery complete 2026-05-16 (a45cbf1e)

## Assets

- release-notes-v1.13.2.md

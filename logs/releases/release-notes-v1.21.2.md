# v1.21.2

- generated_at: 2026-05-24 03:53:06 KST
- bump: patch
- base: v1.21.1
- head: 4185c560

## Summary

- bump: **patch**
- base: v1.21.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.21.2
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.21.1...v1.21.2
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

1. git checkout v1.21.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.21.2 if rollback is published separately

## Changes

- chore: link health 2026-05-24 (4185c560)

## Assets

- release-notes-v1.21.2.md

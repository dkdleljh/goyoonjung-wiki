# v1.13.1

- generated_at: 2026-05-16 09:28:34 KST
- bump: patch
- base: v1.13.0
- head: 152708a1

## Summary

- bump: **patch**
- base: v1.13.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.13.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.13.0...v1.13.1
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

1. git checkout v1.13.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.13.1 if rollback is published separately

## Changes

- Merge remote-tracking branch 'origin/main' (152708a1)
- chore: record daily push recovery 2026-05-16 (ca2ec114)

## Assets

- release-notes-v1.13.1.md

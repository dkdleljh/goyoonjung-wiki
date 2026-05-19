# v1.17.1

- generated_at: 2026-05-19 09:28:53 KST
- bump: patch
- base: v1.17.0
- head: 3159fe3d

## Summary

- bump: **patch**
- base: v1.17.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.17.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.17.0...v1.17.1
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

1. git checkout v1.17.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.17.1 if rollback is published separately

## Changes

- Merge remote-tracking branch 'origin/main' (3159fe3d)
- fix: skip stale auto release runs (40a46f59)
- chore: prepare release v1.17.0 (af3b822a)

## Assets

- release-notes-v1.17.1.md

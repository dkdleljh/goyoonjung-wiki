# v1.25.1

- generated_at: 2026-05-27 09:08:19 KST
- bump: patch
- base: v1.25.0
- head: 1191dca3

## Summary

- bump: **patch**
- base: v1.25.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.25.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.25.0...v1.25.1
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

1. git checkout v1.25.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.25.1 if rollback is published separately

## Changes

- Merge remote-tracking branch 'refs/remotes/origin/main' (1191dca3)
- chore: prepare release v1.25.0 (b6e14d7f)

## Assets

- release-notes-v1.25.1.md

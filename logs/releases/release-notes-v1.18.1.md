# v1.18.1

- generated_at: 2026-05-20 09:28:17 KST
- bump: patch
- base: v1.18.0
- head: 4325cf09

## Summary

- bump: **patch**
- base: v1.18.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.18.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.18.0...v1.18.1
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

1. git checkout v1.18.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.18.1 if rollback is published separately

## Changes

- Merge remote-tracking branch 'origin/main' (4325cf09)
- fix: recover auto release push races (069c339e)
- chore: prepare release v1.18.0 (bfd0d73c)

## Assets

- release-notes-v1.18.1.md

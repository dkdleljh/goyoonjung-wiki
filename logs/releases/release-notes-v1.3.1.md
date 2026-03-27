# v1.3.1

- generated_at: 2026-03-27 18:08:57 KST
- bump: patch
- base: v1.3.0
- head: 9318ccdc

## Summary

- bump: **patch**
- base: v1.3.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.3.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.3.0...v1.3.1
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

1. git checkout v1.3.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.3.1 if rollback is published separately

## Changes

- feat(release): expand release note template (9318ccdc)

## Assets

- release-notes-v1.3.1.md

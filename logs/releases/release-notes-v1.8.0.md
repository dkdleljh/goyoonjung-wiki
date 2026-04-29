# v1.8.0

- generated_at: 2026-04-29 17:04:57 KST
- bump: minor
- base: v1.7.0
- head: ad93596d

## Summary

- bump: **minor**
- base: v1.7.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.8.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.7.0...v1.8.0
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

1. git checkout v1.7.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.8.0 if rollback is published separately

## Changes

- chore: harden wiki automation and docs (ad93596d)

## Assets

- release-notes-v1.8.0.md

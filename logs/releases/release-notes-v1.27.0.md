# v1.27.0

- generated_at: 2026-05-29 09:11:29 KST
- bump: minor
- base: v1.26.1
- head: f9989c30

## Summary

- bump: **minor**
- base: v1.26.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.27.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.26.1...v1.27.0
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

1. git checkout v1.26.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.27.0 if rollback is published separately

## Changes

- daily: update 2026-05-29 (f9989c30)

## Assets

- release-notes-v1.27.0.md

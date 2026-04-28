# v1.6.0

- generated_at: 2026-04-28 15:34:44 KST
- bump: minor
- base: v1.5.4
- head: d9427418

## Summary

- bump: **minor**
- base: v1.5.4

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.6.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.5.4...v1.6.0
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

1. git checkout v1.5.4
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.6.0 if rollback is published separately

## Changes

- routine: recommended (coverage+quality) 2026-04-28 (d9427418)

## Assets

- release-notes-v1.6.0.md

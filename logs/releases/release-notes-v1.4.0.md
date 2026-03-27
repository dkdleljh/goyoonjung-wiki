# v1.4.0

- generated_at: 2026-03-27 18:24:39 KST
- bump: minor
- base: v1.3.1
- head: 1922ac61

## Summary

- bump: **minor**
- base: v1.3.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.4.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.3.1...v1.4.0
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

1. git checkout v1.3.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.4.0 if rollback is published separately

## Changes

- add github release sync workflow (1922ac61)
- docs: link hubs with status and release docs (1fa94b47)
- docs: refresh automation and release guides (11f12a3c)
- improve automation health and coverage auditing (c18d96b1)

## Assets

- release-notes-v1.4.0.md

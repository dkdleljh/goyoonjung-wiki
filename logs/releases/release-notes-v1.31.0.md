# v1.31.0

- generated_at: 2026-06-02 09:07:05 KST
- bump: minor
- base: v1.30.1
- head: 5e24c4dc

## Summary

- bump: **minor**
- base: v1.30.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.31.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.30.1...v1.31.0
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

1. git checkout v1.30.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.31.0 if rollback is published separately

## Changes

- chore: finalize daily run log 2026-06-02 (5e24c4dc)
- daily: update 2026-06-02 (397a4929)

## Assets

- release-notes-v1.31.0.md

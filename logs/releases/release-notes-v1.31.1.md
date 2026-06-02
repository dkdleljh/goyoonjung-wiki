# v1.31.1

- generated_at: 2026-06-02 09:07:29 KST
- bump: patch
- base: v1.31.0
- head: 81875f29

## Summary

- bump: **patch**
- base: v1.31.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.31.1
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.31.0...v1.31.1
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

1. git checkout v1.31.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.31.1 if rollback is published separately

## Changes

- Merge remote-tracking branch 'refs/remotes/origin/main' (81875f29)
- chore: prepare release v1.31.0 (4a1ba1a8)

## Assets

- release-notes-v1.31.1.md

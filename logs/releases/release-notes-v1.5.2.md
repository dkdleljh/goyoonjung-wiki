# v1.5.2

- generated_at: 2026-03-27 18:45:27 KST
- bump: patch
- base: v1.5.1
- head: 882aee7d

## Summary

- bump: **patch**
- base: v1.5.1

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.5.2
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.5.1...v1.5.2
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

1. git checkout v1.5.1
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.5.2 if rollback is published separately

## Changes

- feat(docs): enrich generated wiki portals with status summaries (882aee7d)

## Assets

- release-notes-v1.5.2.md

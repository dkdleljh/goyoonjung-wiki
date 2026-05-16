# v1.13.0

- generated_at: 2026-05-16 09:27:28 KST
- bump: minor
- base: v1.12.0
- head: f5c047b1

## Summary

- bump: **minor**
- base: v1.12.0

## Impact

- repository: dkdleljh/goyoonjung-wiki
- release_url: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/v1.13.0
- compare_url: https://github.com/dkdleljh/goyoonjung-wiki/compare/v1.12.0...v1.13.0
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

1. git checkout v1.12.0
2. restore release automation scripts if needed
3. edit or delete GitHub Release v1.13.0 if rollback is published separately

## Changes

- Merge remote-tracking branch 'origin/main' (f5c047b1)
- chore: record daily push failure 2026-05-16 (4b8527fc)
- daily: update 2026-05-16 (a2d2a21a)
- daily: update 2026-05-15 (e7c53a5e)
- daily: update 2026-05-14 (7bfc3aab)
- daily: update 2026-05-13 (c53dab79)
- daily: update 2026-05-12 (a6b69790)
- daily: update 2026-05-11 (f95751bc)
- daily: update 2026-05-10 (3f1b26da)
- chore: link health 2026-05-10 (1eb4f0d6)
- daily: update 2026-05-09 (21f34baf)
- daily: update 2026-05-08 (712c8fe0)
- daily: update 2026-05-07 (73034801)
- daily: update 2026-05-06 (524bfc37)
- daily: update 2026-05-05 (e3a990e8)
- daily: update 2026-05-04 (05e3794e)
- daily: update 2026-05-03 (6acb2cb5)
- chore: link health 2026-05-03 (3ee44a61)

## Assets

- release-notes-v1.13.0.md

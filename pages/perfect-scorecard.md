# Perfect Scorecard (auto)

> Updated: 2026-04-30 (Asia/Seoul)

## Snapshot
- pages_total: 106
- urls_total(markdown): 3515
- seen_urls(db): 274
- allowlist_domains(lines): 136
- google_news_sites(lines): 48
- google_news_queries(lines): 20
- magazine_rss(lines): 42
- youtube_feeds(lines): 22

## Scores (0~100)
### A. Perfect wiki coverage system: **96/100**

- channel_diversity: 100  (config presence + i18n + youtube + rss)
- landing: 100  (category landing pages exist)
- detection: 100  (quality/content-gaps reports)
- official_work_sync: 85  (official filmography audit)

### B. Perfect unmanned automation: **100/100**

- pipeline: 100  (run_daily_update + steps)
- resilience: 100  (batching + skip-reason logging)
- observability: 100  (status/daily/lint reports)
- runtime_guards: 100  (ci + timer + health check + e2e presence)

### C. Unbeatable information volume: **100/100**

- C_current: 100  (actual accumulated scale (grows over time))
- C_capacity: 100  (system capacity / coverage potential)
- urls_total: 3515  (markdown URL count)
- seen_urls_db: 274  (dedupe DB size)
- source_width: 100  (allowlist/sites/queries/yt)
- work_pages: 15  (pages/works/*.md)
- i18n: 100  (i18n query support)

### D. Perfect quality: **70/100**

- placeholder: 30  (debt=35)
- link_health: 100  (link-health.md presence)
- lint: 100  (lint-report.md presence)
- provenance: 100  (official vs press vs secondary)
- coverage_readiness: 56  (official coverage audit)

## Top URL-heavy pages (top 10)
- 1282: pages/alternative-proof-candidates.md
- 1016: pages/skipped-link-backlog.md
- 114: pages/interviews.md
- 101: pages/pictorials/editorial.md
- 99: pages/notes/translation-love-filming-locations-google-maps.md
- 68: pages/pictorials/by-year.md
- 55: pages/interviews/by-year.md
- 54: pages/appearances.md
- 44: pages/pictorials/campaign.md
- 44: pages/pictorials/stills-posters.md

## Notes
- ‘Perfect’ here means: the system keeps expanding coverage while staying stable and auditable.
- True 100% completeness cannot be proven; we optimize for long-run capture + low debt + high reliability.

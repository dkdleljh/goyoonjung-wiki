# Operational Scorecard (auto)

> Updated: 2026-10-13 (Asia/Seoul)

## Snapshot
- pages_total: 120
- urls_total(markdown): 479
- seen_urls(db): 163
- allowlist_domains(lines): 136
- google_news_sites(lines): 48
- google_news_queries(lines): 20
- magazine_rss(lines): 42
- youtube_feeds(lines): 22

## Scores (0~100)
### A. Coverage tooling readiness: **85/100**

- channel_diversity: 100  (config presence + i18n + youtube + rss)
- landing: 100  (category landing pages exist)
- detection: 100  (quality/content-gaps reports)
- official_work_sync: 40  (official filmography audit)

### B. Recorded automation health: **0/100**

- pipeline: 100  (run_daily_update + steps)
- resilience: 100  (batching + skip-reason logging)
- observability: 100  (status/daily/lint reports)
- runtime_guards: 100  (file presence only; does not prove deployment)

### C. Content scale heuristic: **69/100**

- C_current: 69  (actual accumulated scale (grows over time))
- C_capacity: 100  (system capacity / coverage potential)
- urls_total: 479  (unique Markdown URLs, not independent facts)
- seen_urls_db: 163  (dedupe DB size)
- source_width: 100  (allowlist/sites/queries/yt)
- work_pages: 17  (pages/works/*.md)
- i18n: 100  (i18n query support)

### D. Content quality heuristic: **47/100**

- placeholder: 0  (debt=73)
- link_health: 81  (measured results and report age)
- lint: 100  (actual findings)
- provenance: 100  (official vs press vs secondary)
- coverage_readiness: 6  (official coverage audit)

## Top URL-heavy pages (top 10)
- 116: pages/promotion-queue.md
- 95: pages/notes/translation-love-filming-locations-google-maps.md
- 79: pages/pictorials/by-year.md
- 68: pages/link-health.md
- 63: pages/official-platform-watch.md
- 62: pages/skipped-link-backlog.md
- 52: pages/alternative-proof-candidates.md
- 49: pages/interviews.md
- 49: pages/pictorials/editorial.md
- 48: pages/interviews/by-year.md

## Notes
- A and B component values describe tooling presence; B headline uses actual run freshness and outcome.
- True 100% completeness cannot be proven; we optimize for long-run capture + low debt + high reliability.

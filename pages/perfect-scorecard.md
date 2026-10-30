# Operational Scorecard (auto)

> Updated: 2026-10-30 (Asia/Seoul)

## Snapshot
- pages_total: 124
- urls_total(markdown): 961
- seen_urls(db): 385
- allowlist_domains: 105
- google_news_sites: 40
- google_news_queries(lines): 20
- magazine_sources: 12
- youtube_channels: 12

점수는 구성 요소와 기록에 따른 내부 지표이며 실제 가동률·정확도·자료 완성률이 아닙니다. [실측 결과](automation-measurements.md)를 함께 확인하세요.

## Scores (0~100)
### A. Coverage tooling readiness: **75/100**

- channel_diversity: 100  (config presence + i18n + youtube + rss)
- landing: 100  (category landing pages exist)
- detection: 100  (quality/content-gaps reports)
- official_work_sync: 0  (official filmography audit)

### B. Recorded automation health: **0/100**

- pipeline: 100  (run_daily_update + steps)
- resilience: 100  (batching + skip-reason logging)
- observability: 100  (status/daily/lint reports)
- runtime_guards: 100  (file presence only; does not prove deployment)

### C. Content scale heuristic: **74/100**

- C_current: 74  (actual accumulated scale (grows over time))
- C_capacity: 100  (system capacity / coverage potential)
- urls_total: 961  (unique Markdown URLs, not independent facts)
- seen_urls_db: 385  (dedupe DB size)
- source_width: 100  (allowlist/sites/queries/yt)
- work_pages: 17  (pages/works/*.md)
- i18n: 100  (i18n query support)

### D. Content quality heuristic: **30/100**

- placeholder: 0  (debt=402)
- link_health: 0  (measured results and report age)
- lint: 100  (actual findings)
- provenance: 100  (official vs press vs secondary)
- coverage_readiness: 0  (official coverage audit)

## Top URL-heavy pages (top 10)
- 241: pages/reviewed-news.md
- 208: pages/pictorials/editorial.md
- 123: pages/pictorials/by-year.md
- 95: pages/notes/translation-love-filming-locations-google-maps.md
- 86: pages/candidate-pool.md
- 80: pages/verification-queue.md
- 79: pages/youtube-archive.md
- 57: pages/interviews.md
- 54: pages/appearances.md
- 53: pages/official-platform-watch.md

## Notes
- A and B component values describe tooling presence; B headline uses actual run freshness and outcome.
- True 100% completeness cannot be proven; we optimize for long-run capture + low debt + high reliability.

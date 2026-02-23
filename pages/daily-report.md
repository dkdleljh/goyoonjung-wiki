# 데일리 리포트

> 갱신: 2026-02-23 10:37 (Asia/Seoul)

## 1) 최신 커밋

- 8e1fcb52 2026-02-23 10:34:42 +0900 fix(kpi): avoid sqlite timeouts; ignore pyc

## 2) 변경 파일(최근 커밋 기준)

- .gitignore
- scripts/__pycache__/__init__.cpython-312.pyc
- scripts/__pycache__/ai_content_generator.cpython-312.pyc
- scripts/__pycache__/append_skip_reason.cpython-312.pyc
- scripts/__pycache__/apply_alternative_proofs.cpython-312.pyc
- scripts/__pycache__/async_performance_optimizer.cpython-312.pyc
- scripts/__pycache__/audit_content_gaps.cpython-312.pyc
- scripts/__pycache__/audit_missing_alternative_proofs.cpython-312.pyc
- scripts/__pycache__/audit_skipped_links.cpython-312.pyc
- scripts/__pycache__/auto_collect_agency.cpython-312.pyc
- scripts/__pycache__/auto_collect_encyclopedia.cpython-312.pyc
- scripts/__pycache__/auto_collect_google_news.cpython-312.pyc
- scripts/__pycache__/auto_collect_google_news_queries.cpython-312.pyc
- scripts/__pycache__/auto_collect_google_news_queries_i18n.cpython-312.pyc
- scripts/__pycache__/auto_collect_google_news_sites.cpython-312.pyc
- scripts/__pycache__/auto_collect_magazine_backfill.cpython-312.pyc
- scripts/__pycache__/auto_collect_magazine_rss.cpython-312.pyc
- scripts/__pycache__/auto_collect_news_links.cpython-312.pyc
- scripts/__pycache__/auto_collect_schedule.cpython-312.pyc
- scripts/__pycache__/auto_collect_visual_links.cpython-312.pyc
- scripts/__pycache__/auto_collect_youtube_feeds.cpython-312.pyc
- scripts/__pycache__/auto_fix_stale_running.cpython-312.pyc
- scripts/__pycache__/autofill_official_links.cpython-312.pyc
- scripts/__pycache__/backfill_missing_alternative_proofs.cpython-312.pyc
- scripts/__pycache__/backup_manager.cpython-312.pyc
- scripts/__pycache__/beautify_markdown.cpython-312.pyc
- scripts/__pycache__/build_promotion_queue.cpython-312.pyc
- scripts/__pycache__/cache.cpython-312.pyc
- scripts/__pycache__/check_links.cpython-312.pyc
- scripts/__pycache__/collect_awards_official_pages.cpython-312.pyc
- scripts/__pycache__/collect_kbs_starbox_candidates.cpython-312.pyc
- scripts/__pycache__/collect_magazine_candidates.cpython-312.pyc
- scripts/__pycache__/collect_reference_sources.cpython-312.pyc
- scripts/__pycache__/collector_batch_state.cpython-312.pyc
- scripts/__pycache__/compute_perfect_scorecard.cpython-312.pyc
- scripts/__pycache__/config_loader.cpython-312.pyc
- scripts/__pycache__/db_manager.cpython-312.pyc
- scripts/__pycache__/domain_policy.cpython-312.pyc
- scripts/__pycache__/emojiify_titles.cpython-312.pyc
- scripts/__pycache__/ensure_pretty_sections.cpython-312.pyc
- scripts/__pycache__/ensure_required_sections.cpython-312.pyc
- scripts/__pycache__/error_handling.cpython-312.pyc
- scripts/__pycache__/fill_overview_sections.cpython-312.pyc
- scripts/__pycache__/final_verification.cpython-312.pyc
- scripts/__pycache__/flush_notify_queue.cpython-312.pyc
- scripts/__pycache__/generate_timeline.cpython-312.pyc
- scripts/__pycache__/insert_toc.cpython-312.pyc
- scripts/__pycache__/lock_manager.cpython-312.pyc
- scripts/__pycache__/logger.cpython-312.pyc
- scripts/__pycache__/migrate_seen_urls.cpython-312.pyc
- scripts/__pycache__/monitor.cpython-312.pyc
- scripts/__pycache__/normalize_alternative_proofs.cpython-312.pyc
- scripts/__pycache__/normalize_url.cpython-312.pyc
- scripts/__pycache__/notify_status.cpython-312.pyc
- scripts/__pycache__/performance_optimizer.cpython-312.pyc
- scripts/__pycache__/promote_appearances_from_news.cpython-312.pyc
- scripts/__pycache__/promote_awards_official_proofs.cpython-312.pyc
- scripts/__pycache__/promote_campaign_dates.cpython-312.pyc
- scripts/__pycache__/promote_dates_from_meta.cpython-312.pyc
- scripts/__pycache__/promote_endorsement_dates.cpython-312.pyc
- scripts/__pycache__/promote_endorsements_announce_fallback.cpython-312.pyc
- scripts/__pycache__/promote_endorsements_from_news.cpython-312.pyc
- scripts/__pycache__/promote_endorsements_official_announcements.cpython-312.pyc
- scripts/__pycache__/promote_interview_summaries_allowlist.cpython-312.pyc
- scripts/__pycache__/promote_interview_summaries_kbs.cpython-312.pyc
- scripts/__pycache__/promote_mv_candidates_from_news.cpython-312.pyc
- scripts/__pycache__/promote_official_tv_ott_candidates.cpython-312.pyc
- scripts/__pycache__/promote_profile_policy_unmanned.cpython-312.pyc
- scripts/__pycache__/promote_safe_metadata.cpython-312.pyc
- scripts/__pycache__/promote_works_from_news.cpython-312.pyc
- scripts/__pycache__/promote_youtube_dates.cpython-312.pyc
- scripts/__pycache__/prune_overview_sections.cpython-312.pyc
- scripts/__pycache__/quality_alerts.cpython-312.pyc
- scripts/__pycache__/rebuild_awards_official_cache.cpython-312.pyc
- scripts/__pycache__/rebuild_endorsements_year_index.cpython-312.pyc
- scripts/__pycache__/rebuild_fixed_lead_blocks.cpython-312.pyc
- scripts/__pycache__/rebuild_group_link_candidates.cpython-312.pyc
- scripts/__pycache__/rebuild_interviews_year_index.cpython-312.pyc
- scripts/__pycache__/rebuild_profile_infobox.cpython-312.pyc
- scripts/__pycache__/rebuild_progress.cpython-312.pyc
- scripts/__pycache__/rebuild_quality_report.cpython-312.pyc
- scripts/__pycache__/rebuild_schedule_highlights.cpython-312.pyc
- scripts/__pycache__/rebuild_tag_index.cpython-312.pyc
- scripts/__pycache__/rebuild_timeline_narrative.cpython-312.pyc
- scripts/__pycache__/rebuild_work_link_candidates.cpython-312.pyc
- scripts/__pycache__/rebuild_works_year_index.cpython-312.pyc
- scripts/__pycache__/rebuild_year_indexes.cpython-312.pyc
- scripts/__pycache__/relevance.cpython-312.pyc
- scripts/__pycache__/remove_legacy_toc.cpython-312.pyc
- scripts/__pycache__/resolve_youtube_channel_ids.cpython-312.pyc
- scripts/__pycache__/sanitize_interview_summaries.cpython-312.pyc
- scripts/__pycache__/sanitize_news_log.cpython-312.pyc
- scripts/__pycache__/secure_config.cpython-312.pyc
- scripts/__pycache__/security.cpython-312.pyc
- scripts/__pycache__/send_discord_daily_summary.cpython-312.pyc
- scripts/__pycache__/suggest_alternative_proofs.cpython-312.pyc
- scripts/__pycache__/suggest_awards_official_proofs.cpython-312.pyc
- scripts/__pycache__/suggest_daily_promotion_task.cpython-312.pyc
- scripts/__pycache__/suggest_encyclopedia_promotions.cpython-312.pyc
- scripts/__pycache__/suggest_lead_paragraphs.cpython-312.pyc
- scripts/__pycache__/summarize_news.cpython-312.pyc
- scripts/__pycache__/sync_media_watch_sources.cpython-312.pyc
- scripts/__pycache__/update_dashboard.cpython-312.pyc
- scripts/__pycache__/update_index_last_updated.cpython-312.pyc
- scripts/__pycache__/update_profile_status.cpython-312.pyc
- scripts/__pycache__/update_readme_today_links.cpython-312.pyc
- scripts/__pycache__/web_dashboard.cpython-312.pyc
- scripts/__pycache__/wiki_score.cpython-312.pyc
- scripts/__pycache__/write_skip_reasons_to_news.cpython-312.pyc
- scripts/db_manager.py
- scripts/generate_kpi_report.py
- scripts/run_daily_update.sh

## 3) 오늘 실행 상태(news/2026-02-23.md)

## 실행 상태
- 실행: 2026-02-23 10:24 (Asia/Seoul)
- 결과: 성공
- 메모: auto: done (indexes:OK,lint:OK,backup:goyoonjung-wiki_2026-02-23_0014.tar.gz), collect:OK, gnews:OK, gnews-sites:OK, gnews-queries:OK, mag-rss:OK, sched:OK, portal-news:OK, san-news:OK, agency:OK, ency:OK, promote-suggest:OK, lead-suggest:OK, awards-proof-suggest:OK, awards-proof-auto:SKIP, promote-safe:OK, endo-dates:OK, interview-sum:OK, work-candidates:OK, status-update:OK, visual:OK, dashboard:OK
## 실행 이력

- 2026-02-23 10:24 (Asia/Seoul) · 성공 · auto: done (indexes:OK,lint:OK,backup:goyoonjung-wiki_2026-02-23_0014.tar.gz), collect:OK, gnews:OK, gnews-sites:OK, gnews-queries:OK, mag-rss:OK, sched:OK, portal-news:OK, san-news:OK, agency:OK, ency:OK, promote-suggest:OK, lead-suggest:OK, awards-proof-suggest:OK, awards-proof-auto:SKIP, promote-safe:OK, endo-dates:OK, interview-sum:OK, work-candidates:OK, status-update:OK, visual:OK, dashboard:OK


<!-- AUTO-BACKLOG-PROGRESS:START -->
- C(완성도 우선) 백로그 진행률: 20/20 (100%)
<!-- AUTO-BACKLOG-PROGRESS:END -->

## 백과사전 승격 제안(자동)
> 목표: 오늘 ‘참고(2차)/보강 필요’ 항목 중 최소 1개를 S/A급(공식/원문) 근거로 승격.

- (현재 자동 스캔으로 잡힌 보강 후보가 없습니다.)

<!-- AUTO-ENCYCLOPEDIA-PROMOTE:END -->

<!-- AUTO-LEAD-DRAFT:START -->
## 리드 문단(초안) 제안(자동)
> 목적: 위키백과 느낌의 ‘소개 문단’을 만들기 위한 초안 후보입니다. (자동 적용하지 않음)

### 한국어 리드문(초안)
- (index/profile 공용)

고윤정(Go Youn-jung, 1996년 4월 22일~)은 대한민국의 배우이다. 주요 출연작으로 *사이코메트리 그녀석*, *보건교사 안은영*, *스위트홈*, *로스쿨*, *환혼*, *환혼 빛과 그림자* 등이 있다. 이 위키는 작품·화보·광고·인터뷰·출연/행사 기록을 링크 중심(저작권 안전)으로 수집·정리한다.

### English lead (draft)
Go Youn-jung (born April 22, 1996) is a South Korean actress. This wiki is a link-first (copyright-safe) archive of her works, pictorials, endorsements, interviews, and appearances/events, with a focus on official and primary sources.

<!-- AUTO-LEAD-DRAFT:END -->

# 2026-02-23 로그

## 뉴스/업데이트
- [Agency] MAA 공식 홈페이지 작품 리스트 확인: 2건 (변동 확인용)
- [Encyclopedia] Wikipedia 업데이트 확인: 2026-02-22T07:16:52Z by ~2026-10455-03 (revid=41402389)
- [Encyclopedia] Namuwiki 접근 가능 (Code: 200)


## 자동화 스킵/실패 사유(무인 로그)
<!-- AUTO-SKIP-REASONS:START -->
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 00:02)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 00:04)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 00:59)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 01:01)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 01:35)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 01:37)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 01:47)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 01:59)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 02:48)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 03:47)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 04:22)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 04:24)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 04:35)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 04:37)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 04:48)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 05:23)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 05:25)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 06:11)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 06:13)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 06:48)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 07:23)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 07:25)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 08:00)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 08:01)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 08:11)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 08:24)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 09:10)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 10:22)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 10:24)
- score:kpi-report: rc=124 · command failed (try 1/2) (2026-02-23 10:35)
- score:kpi-report: rc=124 · command failed (try 2/2) (2026-02-23 10:36)
<!-- AUTO-SKIP-REASONS:END -->

## 4) 권장 체크

- 자동 09시 실행이 잘 됐는지(09:25 모니터 보고)
- 백로그 1개 전진 여부(pages/progress.md)
- 링크 건강검진 주간 실행(pages/link-health.md)

## 5) KPI 스냅샷

## Daily Metrics
- new_urls: 0
- landed_urls: 0
- duplicate_rate: 0.00% (0/2487)
- verified_urls_by_grade:
  - S: 0
  - A: 0
  - B: 0


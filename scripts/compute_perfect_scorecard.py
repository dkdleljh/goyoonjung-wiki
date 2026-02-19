#!/usr/bin/env python3
"""Compute a multi-axis scorecard for the 'perfect wiki' goals.

Axes (0-100):
A) Perfect wiki coverage system (SYSTEM readiness)
B) Perfect unmanned automation (SYSTEM readiness)
C) Unbeatable information volume (CONTENT/scale)
D) Perfect quality (QUALITY)

Note:
- A/B are scored as "system readiness" (can reach 100 when the machine is fully wired).
- C measures actual accumulated content volume, so it will grow over time.

Writes pages/perfect-scorecard.md.

This is heuristic but deterministic and auditable.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
CONFIG = BASE / "config"
DB = BASE / "data" / "wiki.db"
OUT = PAGES / "perfect-scorecard.md"

URL_RE = re.compile(r"https?://[^\s)]+")


@dataclass
class Axis:
    name: str
    score: int
    parts: list[tuple[str, int, str]]


def count_urls_in_pages() -> tuple[int, int, dict[str, int]]:
    per: dict[str, int] = {}
    for p in PAGES.rglob("*.md"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        per[str(p.relative_to(BASE))] = len(URL_RE.findall(t))
    return len(per), sum(per.values()), per


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len([ln for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines()])


def count_non_comment_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len(
        [
            ln
            for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
    )


def count_google_query_lines() -> int:
    split = count_non_comment_lines(CONFIG / "google-news-queries-precise.txt") + count_non_comment_lines(
        CONFIG / "google-news-queries-broad.txt"
    )
    if split > 0:
        return split
    return count_non_comment_lines(CONFIG / "google-news-queries.txt")


def get_seen_urls_count() -> int:
    if not DB.exists():
        return 0
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        cur.execute("select count(*) from seen_urls")
        return int(cur.fetchone()[0])
    except Exception:
        return 0
    finally:
        con.close()


def read_quality_counts() -> dict[str, int]:
    q = PAGES / "quality-report.md"
    out: dict[str, int] = {}
    if not q.exists():
        return out
    for ln in q.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"- `(.+?)`: \*\*(\d+)\*\*", ln.strip())
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def clamp(x: int) -> int:
    return max(0, min(100, x))


def score() -> list[Axis]:
    pages_total, urls_total, per = count_urls_in_pages()
    allowlist = count_lines(CONFIG / "allowlist-domains.txt")
    gsites = count_lines(CONFIG / "google-news-sites.txt")
    gqueries = count_google_query_lines()
    yt = count_lines(CONFIG / "youtube-feeds.yml")
    seen = get_seen_urls_count()

    # A) Coverage system readiness (wiring completeness)
    # We score on presence of key collectors + configs + promotion steps.
    channel_diversity = 0
    required_configs = [
        "google-news-queries.txt",
        "google-news-queries-precise.txt",
        "google-news-queries-broad.txt",
        "google-news-sites.txt",
        "magazine-rss.yml",
        "youtube-feeds.yml",
        "google-news-queries-i18n.txt",
    ]
    for f in required_configs:
        channel_diversity += 20 if (CONFIG / f).exists() else 0
    channel_diversity = clamp(channel_diversity)

    landing = 0
    landing_pages = ["pages/appearances.md", "pages/interviews.md", "pages/pictorials.md", "pages/endorsements.md", "pages/filmography.md"]
    for f in landing_pages:
        landing += 20 if (BASE / f).exists() else 0
    landing = clamp(landing)

    detection = 0
    for f in ("quality-report.md", "content-gaps.md", "link-health.md", "daily-report.md"):
        detection += 25 if (PAGES / f).exists() else 0
    detection = clamp(detection)

    A = clamp(int(round(channel_diversity * 0.40 + landing * 0.35 + detection * 0.25)))

    # B) Automation readiness
    # 100 when the full unmanned loop is wired + protected (locks, debouncing, batching, skip-logging).
    pipeline = 0
    required_scripts = [
        "scripts/run_daily_update.sh",
        "scripts/lock_manager.py",
        "scripts/backup_manager.py",
        "scripts/mark_news_status.sh",
        "scripts/sanitize_news_log.py",
    ]
    for f in required_scripts:
        pipeline += 20 if (BASE / f).exists() else 0
    pipeline = clamp(pipeline)

    resilience = 0
    for f in (
        "scripts/collector_batch_state.py",
        "scripts/append_skip_reason.py",
        "scripts/cleanup_stale_running.sh",
    ):
        resilience += 34 if (BASE / f).exists() else 0
    resilience = clamp(resilience)

    observability = 0
    for f in ("pages/system_status.md", "pages/daily-report.md", "pages/lint-report.md", "pages/quality-report.md"):
        observability += 25 if (BASE / f).exists() else 0
    observability = clamp(observability)

    B = clamp(int(round(pipeline * 0.40 + resilience * 0.30 + observability * 0.30)))

    # C) Information volume
    # We report two numbers:
    # - C_current: actual accumulated scale (grows with time)
    # - C_capacity: system capacity / source coverage potential

    # current scale (urls_total scale: 0..10k)
    c1 = clamp(int(urls_total / 100))
    c1 = clamp(int(c1 * 3.0))

    source_width = clamp(int(min(100, (allowlist / 2) + (gsites * 2) + (gqueries * 2) + (yt * 5))))

    work_pages = len(list((PAGES / "works").glob("*.md"))) if (PAGES / "works").exists() else 0
    depth = clamp(60 + min(30, work_pages))

    i18n = 40 + (30 if (CONFIG / "google-news-queries-i18n.txt").exists() else 0)
    i18n = clamp(i18n)

    C_current = clamp(int(round(c1 * 0.35 + depth * 0.25 + i18n * 0.15 + source_width * 0.25)))

    # capacity score: if we have the full expansion plumbing, it's 100.
    capacity = 0
    for f in (
        "config/google-news-sites.txt",
        "config/google-news-queries.txt",
        "config/google-news-queries-precise.txt",
        "config/google-news-queries-broad.txt",
        "config/magazine-rss.yml",
        "config/youtube-feeds.yml",
        "config/google-news-queries-i18n.txt",
    ):
        capacity += 20 if (BASE / f).exists() else 0
    C_capacity = clamp(capacity)

    C = C_current

    # D) Quality
    qc = read_quality_counts()
    debt = qc.get("교차검증 필요", 0) + qc.get("참고(2차)", 0) + qc.get("요약 보강 필요", 0) + qc.get("(페이지 내 표기 확인 필요)", 0) + qc.get("(확인 필요)", 0)
    placeholder = clamp(100 - debt * 5)
    link_health = 100 if (PAGES / "link-health.md").exists() else 60
    lint = 100 if (PAGES / "lint-report.md").exists() else 60
    # Provenance readiness: do we have explicit mapping/policies to keep sources graded?
    provenance = 0
    for f in (
        "docs/editorial_policy.md",
        "pages/style-guide.md",
        "config/allowlist-domains.txt",
        "config/domain-grades.yml",
        "config/endorsement-brand-map.yml",
    ):
        provenance += 20 if (BASE / f).exists() else 0
    provenance = clamp(provenance)

    D = clamp(int(round(placeholder * 0.35 + link_health * 0.25 + lint * 0.25 + provenance * 0.15)))

    return [
        Axis("A. Perfect wiki coverage system", A, [
            ("channel_diversity", channel_diversity, "config presence + i18n + youtube + rss"),
            ("landing", landing, "category landing pages exist"),
            ("detection", detection, "quality/content-gaps reports"),
        ]),
        Axis("B. Perfect unmanned automation", B, [
            ("pipeline", pipeline, "run_daily_update + steps"),
            ("resilience", resilience, "batching + skip-reason logging"),
            ("observability", observability, "status/daily/lint reports"),
        ]),
        Axis("C. Unbeatable information volume", C, [
            ("C_current", C_current, "actual accumulated scale (grows over time)"),
            ("C_capacity", C_capacity, "system capacity / coverage potential"),
            ("urls_total", urls_total, "markdown URL count"),
            ("seen_urls_db", seen, "dedupe DB size"),
            ("source_width", source_width, "allowlist/sites/queries/yt"),
            ("work_pages", work_pages, "pages/works/*.md"),
            ("i18n", i18n, "i18n query support"),
        ]),
        Axis("D. Perfect quality", D, [
            ("placeholder", placeholder, f"debt={debt}"),
            ("link_health", link_health, "link-health.md presence"),
            ("lint", lint, "lint-report.md presence"),
            ("provenance", provenance, "official vs press vs secondary"),
        ]),
    ]


def write(axes: list[Axis]) -> None:
    pages_total, urls_total, per = count_urls_in_pages()
    top10 = sorted(per.items(), key=lambda kv: kv[1], reverse=True)[:10]

    allowlist = count_lines(CONFIG / "allowlist-domains.txt")
    gsites = count_lines(CONFIG / "google-news-sites.txt")
    gqueries = count_google_query_lines()
    rss = count_lines(CONFIG / "magazine-rss.yml")
    yt = count_lines(CONFIG / "youtube-feeds.yml")
    seen = get_seen_urls_count()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Perfect Scorecard (auto)",
        "",
        f"> Updated: {now} (Asia/Seoul)",
        "",
        "## Snapshot",
        f"- pages_total: {pages_total}",
        f"- urls_total(markdown): {urls_total}",
        f"- seen_urls(db): {seen}",
        f"- allowlist_domains(lines): {allowlist}",
        f"- google_news_sites(lines): {gsites}",
        f"- google_news_queries(lines): {gqueries}",
        f"- magazine_rss(lines): {rss}",
        f"- youtube_feeds(lines): {yt}",
        "",
        "## Scores (0~100)",
    ]

    for ax in axes:
        lines += [
            f"### {ax.name}: **{ax.score}/100**",
            "",
        ]
        for k, v, note in ax.parts:
            lines.append(f"- {k}: {v}  ({note})")
        lines.append("")

    lines += [
        "## Top URL-heavy pages (top 10)",
        *[f"- {cnt}: {p}" for p, cnt in top10],
        "",
        "## Notes",
        "- ‘Perfect’ here means: the system keeps expanding coverage while staying stable and auditable.",
        "- True 100% completeness cannot be proven; we optimize for long-run capture + low debt + high reliability.",
    ]

    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    axes = score()
    write(axes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

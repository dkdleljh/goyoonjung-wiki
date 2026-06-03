#!/usr/bin/env python3
"""Generate source confidence inventory from Markdown URLs."""

from __future__ import annotations

from collections import Counter, defaultdict

try:
    from scripts import domain_policy
    from scripts.automation_common import (
        BASE,
        FACTS,
        PAGES,
        extract_urls,
        host_for_url,
        md_table,
        report_header,
        write_json,
    )
except Exception:  # pragma: no cover
    import domain_policy  # type: ignore
    from automation_common import (  # type: ignore
        BASE,
        FACTS,
        PAGES,
        extract_urls,
        host_for_url,
        md_table,
        report_header,
        write_json,
    )


def scan_pages() -> list[dict[str, object]]:
    policy = domain_policy.load_policy()
    rows: list[dict[str, object]] = []
    for path in sorted(PAGES.rglob("*.md")):
        rel = path.relative_to(BASE).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for url in extract_urls(text):
            host = host_for_url(url)
            grade = policy.grade_for_url(url)
            rows.append({"page": rel, "url": url, "host": host, "grade": grade, "lane": policy.lane_for_url(url)})
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    by_grade = Counter(str(row["grade"]) for row in rows)
    by_host: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_host[str(row["host"])][str(row["grade"])] += 1

    top_hosts = sorted(by_host.items(), key=lambda item: sum(item[1].values()), reverse=True)[:30]
    table_rows = [
        [host, str(sum(counter.values())), ", ".join(f"{g}:{n}" for g, n in sorted(counter.items()))]
        for host, counter in top_hosts
    ]
    lines = report_header("Source Confidence Report (auto)")
    lines += [
        "## Summary",
        f"- total_urls: {len(rows)}",
        f"- S: {by_grade.get('S', 0)}",
        f"- A: {by_grade.get('A', 0)}",
        f"- B: {by_grade.get('B', 0)}",
        f"- BLOCK: {by_grade.get('BLOCK', 0)}",
        "",
        "## Top Hosts",
        md_table(table_rows, ["host", "urls", "grade_counts"]),
        "",
        "## Policy",
        "- S/A 출처는 자동 반영 후보입니다.",
        "- B 출처는 검증 큐 또는 보조 참고입니다.",
        "- BLOCK/미등록 출처는 본문 자동 확정에 쓰지 않습니다.",
    ]
    (PAGES / "source-confidence.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    FACTS.mkdir(parents=True, exist_ok=True)
    rows = scan_pages()
    write_json(FACTS / "sources.json", rows)
    write_report(rows)
    print(f"source_confidence: urls={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

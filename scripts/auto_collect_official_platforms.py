#!/usr/bin/env python3
"""Collect official platform evidence from existing work pages."""

from __future__ import annotations

try:
    from scripts import domain_policy
    from scripts.automation_common import (
        FACTS,
        PAGES,
        extract_urls,
        host_for_url,
        md_table,
        read_text,
        report_header,
        write_json,
    )
except Exception:  # pragma: no cover
    import domain_policy  # type: ignore
    from automation_common import (  # type: ignore
        FACTS,
        PAGES,
        extract_urls,
        host_for_url,
        md_table,
        read_text,
        report_header,
        write_json,
    )

PLATFORM_HOSTS = {
    "maa.co.kr",
    "netflix.com",
    "disneyplus.com",
    "tving.com",
    "jtbc.co.kr",
    "tv.jtbc.co.kr",
    "tvn.cjenm.com",
    "youtube.com",
    "youtu.be",
}


def page_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip(" #🎬") or fallback
        if line.startswith("- 작품:"):
            return line.split(":", 1)[1].strip()
    return fallback


def main() -> int:
    policy = domain_policy.load_policy()
    rows: list[dict[str, object]] = []
    for path in sorted((PAGES / "works").glob("*.md")):
        text = read_text(path)
        title = page_title(text, path.stem)
        for url in extract_urls(text):
            host = host_for_url(url)
            grade = policy.grade_for_url(url)
            if grade == "S" or host in PLATFORM_HOSTS:
                rows.append(
                    {
                        "title": title,
                        "page": path.relative_to(PAGES.parent).as_posix(),
                        "url": url,
                        "host": host,
                        "grade": grade,
                        "status": "official_candidate" if grade == "S" else "platform_candidate",
                    }
                )
    write_json(FACTS / "official_platforms.json", rows)
    table = [[r["title"], r["host"], r["grade"], r["url"]] for r in rows[:80]]
    lines = report_header("Official Platform Watch (auto)")
    lines += [
        "## Summary",
        f"- official_platform_links: {len(rows)}",
        "",
        "## Links",
        md_table(table, ["title", "host", "grade", "url"]),
        "",
        "## Policy",
        "- S급 공식 링크는 본문 자동 확정 후보입니다.",
        "- 플랫폼 후보라도 역할/날짜가 명시되지 않으면 검증 큐를 유지합니다.",
    ]
    (PAGES / "official-platform-watch.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"auto_collect_official_platforms: links={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

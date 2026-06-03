#!/usr/bin/env python3
"""Build an official-awards watch report from awards.md."""

from __future__ import annotations

import re

try:
    from scripts import domain_policy
    from scripts.automation_common import (
        FACTS,
        PAGES,
        extract_urls,
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
        md_table,
        read_text,
        report_header,
        write_json,
    )


def split_row(line: str) -> list[str]:
    return [re.sub(r"<[^>]+>", "", cell).strip() for cell in line.strip().strip("|").split("|")]


def main() -> int:
    policy = domain_policy.load_policy()
    items: list[dict[str, object]] = []
    for line in read_text(PAGES / "awards.md").splitlines():
        if not line.startswith("|") or "---" in line or "연도" in line:
            continue
        cols = split_row(line)
        if len(cols) < 8:
            continue
        year, ceremony, category, work, result, status, proof, note = cols[:8]
        urls = extract_urls(proof)
        grades = [policy.grade_for_url(url) for url in urls]
        items.append(
            {
                "year": year,
                "ceremony": ceremony,
                "category": category,
                "work": work,
                "result": result,
                "status": status,
                "official_urls": urls,
                "grades": grades,
                "action": "keep_confirmed" if "공식확정" in status else "needs_official_proof",
                "note": note,
            }
        )
    write_json(FACTS / "awards_official_watch.json", items)
    unresolved = [x for x in items if x["action"] == "needs_official_proof"]
    table = [[x["year"], x["ceremony"], x["category"], x["result"], x["action"]] for x in items]
    lines = report_header("Awards Official Watch (auto)")
    lines += [
        "## Summary",
        f"- total_awards: {len(items)}",
        f"- needs_official_proof: {len(unresolved)}",
        "",
        "## Items",
        md_table(table, ["year", "ceremony", "category", "result", "action"]),
        "",
        "## Policy",
        "- 공식 수상/후보 페이지 또는 공식 영상이 없으면 자동 확정하지 않습니다.",
    ]
    (PAGES / "awards-official-watch.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"auto_collect_awards_official: items={len(items)} unresolved={len(unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

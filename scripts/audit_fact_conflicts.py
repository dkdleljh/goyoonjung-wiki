#!/usr/bin/env python3
"""Detect duplicate or conflicting structured facts."""

from __future__ import annotations

from collections import defaultdict

try:
    from scripts.automation_common import (
        FACTS,
        PAGES,
        load_json,
        md_table,
        report_header,
        write_json,
    )
except Exception:  # pragma: no cover
    from automation_common import (  # type: ignore
        FACTS,
        PAGES,
        load_json,
        md_table,
        report_header,
        write_json,
    )


def main() -> int:
    works = load_json(FACTS / "works.json", [])
    conflicts: list[dict[str, object]] = []
    by_title: dict[str, list[dict[str, object]]] = defaultdict(list)
    if isinstance(works, list):
        for item in works:
            title = str(item.get("title", "")).strip().lower()
            if title:
                by_title[title].append(item)
    for title, items in by_title.items():
        roles = {str(x.get("role", "")) for x in items if x.get("role")}
        dates = {str(x.get("release_date", x.get("year", ""))) for x in items if x.get("release_date") or x.get("year")}
        if len(roles) > 1 or len(dates) > 1:
            conflicts.append({"title": title, "roles": sorted(roles), "dates": sorted(dates), "count": len(items)})

    conflicts.extend(load_json(FACTS / "claim-conflicts.json", []))
    write_json(FACTS / "fact_conflicts.json", conflicts)
    rows = [[c.get("title", c.get("entity", "")), str(c.get("count", len(c.get("evidence", [])))), ", ".join(c.get("roles", [])), ", ".join(c.get("dates", c.get("values", [])))] for c in conflicts]
    lines = report_header("Fact Conflict Audit (auto)")
    lines += [
        "## Summary",
        f"- conflicts: {len(conflicts)}",
        "",
        "## Conflicts",
        md_table(rows, ["title", "count", "roles", "dates"]) if rows else "- 없음",
        "",
        "## Policy",
        "- 0건은 비교 가능한 근거에서 충돌을 발견하지 않았다는 뜻이며 전체 사실 검증 완료가 아닙니다.",
        "- 공식 등급이 낮은 출처가 높은 등급의 사실을 덮어쓰지 못하게 합니다.",
        "- 충돌이 1개 이상이면 본문 자동 확정 대신 검증 큐로 보냅니다.",
    ]
    (PAGES / "fact-conflicts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"audit_fact_conflicts: conflicts={len(conflicts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

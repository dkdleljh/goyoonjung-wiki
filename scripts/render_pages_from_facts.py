#!/usr/bin/env python3
"""Render facts inventory pages without overwriting editorial pages."""

from __future__ import annotations

try:
    from scripts.automation_common import FACTS, PAGES, load_json, md_table, report_header
except Exception:  # pragma: no cover
    from automation_common import FACTS, PAGES, load_json, md_table, report_header  # type: ignore


def main() -> int:
    works = load_json(FACTS / "works.json", [])
    awards = load_json(FACTS / "awards.json", [])
    profile = load_json(FACTS / "profile.json", {})
    source_rows = []
    if isinstance(works, list):
        source_rows.append(["works", str(len(works)), "data/facts/works.json"])
    if isinstance(awards, list):
        source_rows.append(["awards", str(len(awards)), "data/facts/awards.json"])
    if isinstance(profile, dict):
        source_rows.append(["profile", "1", "data/facts/profile.json"])

    work_rows = []
    for item in works[:30] if isinstance(works, list) else []:
        work_rows.append([item.get("year", ""), item.get("platform", ""), item.get("title", ""), item.get("role", ""), item.get("status", "")])

    lines = report_header("Facts Index (auto)")
    lines += [
        "## 목적",
        "- Markdown에 흩어진 주요 사실을 구조화 데이터로 추출한 결과입니다.",
        "- 이 페이지는 본문을 덮어쓰지 않고 자동화 검증용 색인 역할을 합니다.",
        "",
        "## Fact Files",
        md_table(source_rows, ["domain", "items", "file"]),
        "",
        "## Works Snapshot",
        md_table(work_rows, ["year", "platform", "title", "role", "status"]),
        "",
        "## 운영 원칙",
        "- 공식 근거 없는 정보는 이 색인에 있어도 본문 자동 확정 대상이 아닙니다.",
        "- 충돌 여부는 `pages/fact-conflicts.md`에서 확인합니다.",
    ]
    (PAGES / "facts-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("render_pages_from_facts: pages/facts-index.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

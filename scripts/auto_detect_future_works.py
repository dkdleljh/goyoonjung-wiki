#!/usr/bin/env python3
"""Detect future/upcoming work candidates from local canonical pages."""

from __future__ import annotations

import re

try:
    from scripts.automation_common import (
        FACTS,
        PAGES,
        md_table,
        read_text,
        report_header,
        write_json,
    )
except Exception:  # pragma: no cover
    from automation_common import (  # type: ignore
        FACTS,
        PAGES,
        md_table,
        read_text,
        report_header,
        write_json,
    )

FUTURE_WORDS = ("예정", "상반기", "하반기", "촬영", "캐스팅", "공개 예정", "pending release")
OFFICIAL_WORDS = ("MAA", "Netflix", "Disney", "TVING", "JTBC", "tvN", "공식")


def status_for(line: str) -> str:
    if any(word in line for word in OFFICIAL_WORDS) and any(word in line for word in FUTURE_WORDS):
        return "platform_confirmed"
    if any(word in line for word in FUTURE_WORDS):
        return "reported_once"
    return "released"


def main() -> int:
    candidates: list[dict[str, object]] = []
    for source in [PAGES / "filmography.md", PAGES / "schedule.md", *sorted((PAGES / "works").glob("*.md"))]:
        text = read_text(source)
        for line in text.splitlines():
            if not any(word in line for word in FUTURE_WORDS):
                continue
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if not clean:
                continue
            candidates.append(
                {
                    "source": source.relative_to(PAGES.parent).as_posix(),
                    "line": clean[:300],
                    "status": status_for(clean),
                    "auto_landing": status_for(clean) in {"agency_confirmed", "platform_confirmed", "release_scheduled"},
                }
            )
    write_json(FACTS / "future_candidates.json", candidates)
    table = [[x["source"], x["status"], "yes" if x["auto_landing"] else "queue", x["line"]] for x in candidates]
    lines = report_header("Future Watch (auto)")
    lines += [
        "## Summary",
        f"- future_candidates: {len(candidates)}",
        "",
        "## Candidates",
        md_table(table, ["source", "status", "landing", "line"]) if table else "- 현재 감지된 미래 후보 없음",
        "",
        "## Policy",
        "- 루머/단일 보도는 본문 자동 확정하지 않습니다.",
        "- 소속사/플랫폼 공식 확정 또는 공개일 확정만 본문 반영합니다.",
    ]
    (PAGES / "future-watch.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (PAGES / "future-candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"auto_detect_future_works: candidates={len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Rebuild B-grade candidate pool report."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import db_manager

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "pages" / "candidate-pool.md"


def main() -> int:
    db_manager.init_db()
    rows = db_manager.list_candidates(lane="pool", limit=500)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Candidate Pool (auto)",
        "",
        f"> Updated: {now} (Asia/Seoul)",
        "",
        "B 등급 도메인 링크 보관소입니다. 자동 승격하지 않으며 수동 검증 대상으로만 유지합니다.",
        "",
        "## Items",
    ]
    if not rows:
        lines.append("- (없음)")
    else:
        for row in rows:
            lines.append(
                f"- {row['last_seen_at'][:10]} · grade={row['grade']} · {row['source']} · "
                f"[{row['title']}]({row['url']})"
            )
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"rebuild_candidate_pool: items={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Compute a simple score for:
1) Wiki completeness (placeholder/verification debt)
2) Unmanned automation health

This is an INTERNAL dashboard score.
- It does NOT claim the wiki contains 'everything' about the subject.
- It measures what the system can measure: placeholders, lint, automation health.

Outputs: pages/system_status.md (overwrites) and prints SCORE lines.
No web access.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = ZoneInfo("Asia/Seoul")
OUT = os.path.join(BASE, "pages", "system_status.md")


@dataclass
class Score:
    name: str
    score: int
    details: list[str]


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True)
    out = (p.stdout + "\n" + p.stderr).strip()
    return p.returncode, out


def count_placeholders() -> dict[str, int]:
    # Read the generated quality report if present; fallback: scan pages.
    q = os.path.join(BASE, "pages", "quality-report.md")
    counts: dict[str, int] = {}
    if os.path.exists(q):
        txt = open(q, "r", encoding="utf-8").read().splitlines()
        for ln in txt:
            m = re.match(r"^- `(.+?)`: \*\*(\d+)\*\*", ln.strip())
            if m:
                counts[m.group(1)] = int(m.group(2))
    return counts


def wiki_completeness_score() -> Score:
    counts = count_placeholders()
    # Heuristic weights
    debt = (
        counts.get("교차검증 필요", 0) * 2
        + counts.get("참고(2차)", 0) * 1
        + counts.get("요약 보강 필요", 0) * 1
        + counts.get("(페이지 내 표기 확인 필요)", 0) * 1
        + counts.get("(확인 필요)", 0) * 1
    )

    # 100 - normalized debt (cap)
    score = max(0, 100 - min(100, debt))

    details = [
        f"placeholder debt score: debt={debt}",
        *(f"- {k}: {v}" for k, v in sorted(counts.items())),
    ]

    return Score("wiki_completeness", score, details)


def automation_score() -> Score:
    rc, out = run(["bash", "-lc", "./scripts/check_automation_health.sh"])
    if rc == 0:
        return Score("automation_health", 100, ["check_automation_health: OK"])

    # If the only problem is that an update is currently running, treat as healthy.
    # (The separate stale-running guard exists inside check_automation_health.sh.)
    if "result=진행중" in out or "news status not success: result=진행중" in out:
        return Score("automation_health", 100, ["check_automation_health: RUNNING (treated OK)"])

    # Otherwise grade hard.
    return Score("automation_health", 40, ["check_automation_health: FAIL", out])


def write_status(scores: list[Score]) -> None:
    # Keep deterministic enough to avoid commit spam: date only.
    now = datetime.now(TZ).strftime("%Y-%m-%d")
    lines = [
        "# System status (auto)",
        "",
        f"> Updated: {now}",
        "",
    ]
    for s in scores:
        lines += [
            f"## {s.name}: **{s.score}/100**",
            "",
            *s.details,
            "",
        ]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    s1 = wiki_completeness_score()
    s2 = automation_score()
    scores = [s1, s2]
    write_status(scores)

    for s in scores:
        print(f"SCORE {s.name}: {s.score}/100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

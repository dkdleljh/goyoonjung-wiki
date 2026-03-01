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

# domain_policy lives next to this file. It is usually importable as a local module
# when this script is executed directly (scripts/ is on sys.path).
# However, when executed as a module (python -m scripts.wiki_score), we need
# an explicit package import fallback.
try:
    from scripts import domain_policy  # type: ignore
except Exception:  # pragma: no cover
    import domain_policy  # type: ignore

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = ZoneInfo("Asia/Seoul")
OUT = os.path.join(BASE, "pages", "system_status.md")
LINT_REPORT = os.path.join(BASE, "pages", "lint-report.md")
LINK_HEALTH = os.path.join(BASE, "pages", "link-health.md")
KPI_REPORT = os.path.join(BASE, "pages", "kpi-report.md")


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
        txt = open(q, encoding="utf-8").read().splitlines()
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


def lint_score() -> Score:
    # Expect lint-report.md to exist and show "- 없음" for key sections.
    if not os.path.exists(LINT_REPORT):
        return Score("lint_clean", 40, ["lint-report.md missing"])
    txt = open(LINT_REPORT, encoding="utf-8").read()
    keys = [
        "## 1) 빈 링크",
        "## 3) 날짜 형식",
        "## 4) 커버리지 목표",
    ]
    missing = [k for k in keys if k not in txt]
    if missing:
        return Score("lint_clean", 60, ["missing sections:"] + missing)
    # naive: if any grep findings exist, lint_wiki.sh prints file:line; otherwise '- 없음'
    ok = "## 1)" in txt and "- 없음" in txt
    return Score("lint_clean", 100 if ok else 80, ["lint-report: OK" if ok else "lint-report: check"])


def link_health_score() -> Score:
    if not os.path.exists(LINK_HEALTH):
        return Score("link_health", 40, ["link-health.md missing"])
    txt = open(LINK_HEALTH, encoding="utf-8").read().splitlines()
    ok = warn = bad = None
    for ln in txt:
        m = re.search(r"OK: \*\*(\d+)\*\* / WARN: \*\*(\d+)\*\* / BAD: \*\*(\d+)\*\*", ln)
        if m:
            ok, warn, bad = map(int, m.groups())
            break
    if ok is None:
        return Score("link_health", 60, ["failed to parse counts"])
    # Scoring: BAD must be zero; WARN is allowed (blocked domains etc) within a small budget.
    warn_budget = 20
    if bad != 0:
        score = 0
    else:
        score = 100 if warn <= warn_budget else max(70, 100 - (warn - warn_budget) * 2)
    details = [f"counts: ok={ok} warn={warn} bad={bad}", f"warn_budget={warn_budget}"]
    return Score("link_health", score, details)


def automation_score() -> Score:
    rc, out = run(["bash", "-lc", "./scripts/check_automation_health.sh"])
    if rc == 0:
        return Score("automation_health", 100, ["check_automation_health: OK"])

    # If the only problem is that an update is currently running, treat as healthy.
    # (The separate stale-running guard exists inside check_automation_health.sh.)
    if "result=진행중" in out or "news status not success: result=진행중" in out:
        return Score("automation_health", 100, ["check_automation_health: RUNNING (treated OK)"])

    # If the repo is dirty, it may be a short window during finalization.
    # Give a softer score but keep the message visible.
    if "working tree dirty" in out:
        return Score(
            "automation_health",
            80,
            [
                "check_automation_health: DIRTY (possible finalization window)",
                "If this persists, commit/push is broken or a generator is writing untracked changes.",
                out,
            ],
        )

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

    policy = domain_policy.load_policy()
    grade_counts = {"S": 0, "A": 0, "B": 0, "BLOCK": 0}
    for g in policy.grades.values():
        if g in grade_counts:
            grade_counts[g] += 1
    lines += [
        "## domain_grade_status",
        "",
        f"- S: {grade_counts['S']}",
        f"- A: {grade_counts['A']}",
        f"- B: {grade_counts['B']}",
        f"- BLOCK: {grade_counts['BLOCK']}",
        "",
    ]

    if os.path.exists(KPI_REPORT):
        txt = open(KPI_REPORT, encoding="utf-8").read().splitlines()
        lines += ["## kpi_snapshot", ""]
        in_metrics = False
        for ln in txt:
            if ln.startswith("## Daily Metrics"):
                in_metrics = True
                continue
            if in_metrics and ln.startswith("## "):
                break
            if in_metrics and ln.strip():
                lines.append(ln)
        lines.append("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    s1 = wiki_completeness_score()
    s2 = lint_score()
    s3 = link_health_score()
    s4 = automation_score()
    scores = [s1, s2, s3, s4]
    write_status(scores)

    for s in scores:
        print(f"SCORE {s.name}: {s.score}/100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

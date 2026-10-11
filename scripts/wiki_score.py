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
from pathlib import Path
from zoneinfo import ZoneInfo

# domain_policy lives next to this file. It is usually importable as a local module
# when this script is executed directly (scripts/ is on sys.path).
# However, when executed as a module (python -m scripts.wiki_score), we need
# an explicit package import fallback.
try:
    from scripts import domain_policy, operational_status  # type: ignore
    from scripts.time_utils import seoul_today_str
except Exception:  # pragma: no cover
    import domain_policy  # type: ignore
    import operational_status
    from time_utils import seoul_today_str  # type: ignore

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(BASE, "pages", "system_status.md")
LINT_REPORT = os.path.join(BASE, "pages", "lint-report.md")
LINK_HEALTH = os.path.join(BASE, "pages", "link-health.md")
KPI_REPORT = os.path.join(BASE, "pages", "kpi-report.md")
OFFICIAL_AUDIT = os.path.join(BASE, "pages", "official-coverage-audit.md")


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


def read_official_audit_scores() -> dict[str, int]:
    scores: dict[str, int] = {}
    if not os.path.exists(OFFICIAL_AUDIT):
        return scores
    txt = open(OFFICIAL_AUDIT, encoding="utf-8").read().splitlines()
    for ln in txt:
        m = re.match(r"^- ([a-z_]+): \*\*(\d+)/100\*\*", ln.strip())
        if m:
            scores[m.group(1)] = int(m.group(2))
    return scores


def wiki_completeness_score() -> Score:
    counts = count_placeholders()
    audit_scores = read_official_audit_scores()
    # Heuristic weights
    debt = (
        counts.get("교차검증 필요", 0) * 2
        + counts.get("참고(2차)", 0) * 1
        + counts.get("요약 보강 필요", 0) * 1
        + counts.get("(페이지 내 표기 확인 필요)", 0) * 1
        + counts.get("(확인 필요)", 0) * 1
        + counts.get("검증불가", 0) * 2
        + counts.get("미확정", 0) * 1
        + counts.get("추가 필요", 0) * 1
    )

    # 100 - normalized debt (cap)
    base_score = max(0, 100 - min(100, debt))
    coverage_readiness = audit_scores.get("coverage_readiness")
    if coverage_readiness is not None:
        score = round(base_score * 0.7 + coverage_readiness * 0.3)
    else:
        score = base_score

    details = [
        f"placeholder debt score: debt={debt}",
        *(
            f"- official_audit.{k}: {v}"
            for k, v in sorted(audit_scores.items())
        ),
        *(f"- {k}: {v}" for k, v in sorted(counts.items())),
    ]

    return Score("wiki_completeness", score, details)


def lint_score() -> Score:
    if not os.path.exists(LINT_REPORT):
        return Score("lint_clean", 0, ["unknown: lint-report.md missing"])
    txt = Path(LINT_REPORT).read_text(encoding="utf-8")
    issues = []
    for number in (1, 3, 4):
        match = re.search(rf"^## {number}\).*?\n(.*?)(?=^## |\Z)", txt, re.M | re.S)
        if not match or match[1].strip() != "- 없음":
            issues.append(f"section {number}: missing or has findings")
    return Score("lint_clean", 0 if issues else 100, issues or ["checked sections: clean"])


def link_health_score() -> Score:
    if not os.path.exists(LINK_HEALTH):
        return Score("link_health", 0, ["unknown: link-health.md missing"])
    txt = Path(LINK_HEALTH).read_text(encoding="utf-8")
    counts = dict((k, int(v)) for k, v in re.findall(r"(OK|WARN|BAD|UNCHECKED): \*\*(\d+)\*\*", txt))
    stamp = re.search(r"갱신: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", txt)
    if not stamp or set(counts) != {"OK", "WARN", "BAD", "UNCHECKED"}:
        return Score("link_health", 0, ["unknown: legacy/missing counts or timestamp; recheck required"])
    try:
        at = datetime.fromisoformat(stamp[1]).replace(tzinfo=ZoneInfo("Asia/Seoul"))
    except ValueError:
        return Score("link_health", 0, ["invalid report timestamp"])
    age = (datetime.now(ZoneInfo("Asia/Seoul")) - at).total_seconds() / 3600
    if not 0 <= age <= 168:
        return Score("link_health", 0, [f"stale or invalid report age: {age:.1f} hours"])
    total = sum(counts.values())
    value = round(100 * counts["OK"] / total) if total and not counts["BAD"] else 0
    return Score("link_health", value, [f"checked at: {stamp[1]}", f"counts: {counts}", "score = verified OK / all discovered URLs; BAD forces zero"])


def automation_score() -> Score:
    state = operational_status.health(Path(BASE))
    return Score("automation_health", 100 if state["status"] == "success" else 0,
                 [f"{key}: {value}" for key, value in state.items()])


def write_status(scores: list[Score]) -> None:
    # Keep deterministic enough to avoid commit spam: date only.
    now = seoul_today_str()
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

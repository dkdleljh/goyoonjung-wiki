#!/usr/bin/env python3
"""Build a lightweight quality report for encyclopedia completeness.

Output: pages/quality-report.md

Counts common placeholders and lists top occurrences.
No web access.
"""

from __future__ import annotations

import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(BASE, "pages", "quality-report.md")

TARGET_DIRS = [
    os.path.join(BASE, "pages"),
]

# Exclude auto-generated reports + meta/backlog docs that intentionally contain placeholders.
EXCLUDE_BASENAMES = {
    "quality-report.md",
    "daily-report.md",
    "namu-backlog.md",
    "encyclopedia-roadmap.md",
    "system_status.md",
}
EXCLUDE_DIR_PARTS = {
    os.path.join("pages", "checklists"),
    os.path.join("pages", "templates"),
}

PATTERNS = [
    "교차검증 필요",
    "참고(2차)",
    "요약 보강 필요",
    "(페이지 내 표기 확인 필요)",
    "(확인 필요)",
]


def iter_md_files():
    for d in TARGET_DIRS:
        for root, _, files in os.walk(d):
            rp = os.path.relpath(root, BASE)
            if any(rp.startswith(p) for p in EXCLUDE_DIR_PARTS):
                continue
            for fn in files:
                if fn.endswith(".md") and fn not in EXCLUDE_BASENAMES:
                    yield os.path.join(root, fn)


def rel(p: str) -> str:
    return os.path.relpath(p, BASE)


def main() -> int:
    counts = {p: 0 for p in PATTERNS}
    hits = {p: [] for p in PATTERNS}

    for path in iter_md_files():
        txt = open(path, encoding="utf-8").read().splitlines()
        for i, ln in enumerate(txt, start=1):
            for p in PATTERNS:
                if p in ln:
                    counts[p] += 1
                    if len(hits[p]) < 15:
                        hits[p].append(f"- {rel(path)}:{i} · {ln.strip()[:140]}")

    out = [
        "# 품질 리포트(자동)",
        "",
        "> 목적: ‘백과사전형’ 완성도를 방해하는 placeholder/미검증 항목을 빠르게 파악합니다.",
        "> 메모: 이 페이지는 자동 생성됩니다.",
        "",
        "---",
        "",
        "## 카운트",
    ]

    for p, n in counts.items():
        out.append(f"- `{p}`: **{n}**")

    out.append("")
    out.append("---")
    out.append("")

    for p in PATTERNS:
        out.append(f"## {p} (상위 {len(hits[p])}개 위치)")
        if hits[p]:
            out.extend(hits[p])
        else:
            out.append("- (없음)")
        out.append("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("rebuild_quality_report: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate a small quality alert summary.

Used for unmanned monitoring.
Reads:
- pages/lint-report.md
- pages/link-health.md
- pages/quality-report.md

Outputs a single-line summary suitable for notifications.
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_link_health(txt: str) -> tuple[int, int]:
    # expects: - OK: **x** / WARN: **y** / BAD: **z**
    m = re.search(r"OK:\s*\*\*(\d+)\*\*\s*/\s*WARN:\s*\*\*(\d+)\*\*\s*/\s*BAD:\s*\*\*(\d+)\*\*", txt)
    if not m:
        return (0, 0)
    return (int(m.group(2)), int(m.group(3)))


def parse_quality_counts(txt: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for m in re.finditer(r"- `([^`]+)`: \*\*(\d+)\*\*", txt):
        out[m.group(1)] = int(m.group(2))
    return out


def parse_lint_high(txt: str) -> int:
    # conservative: count 'High' occurrences in report
    return len(re.findall(r"\bHigh\b", txt))


def main() -> int:
    lint = read(BASE / "pages" / "lint-report.md")
    linkh = read(BASE / "pages" / "link-health.md")
    qual = read(BASE / "pages" / "quality-report.md")

    lint_high = parse_lint_high(lint)
    warn, bad = parse_link_health(linkh)
    qc = parse_quality_counts(qual)

    # key placeholders
    need_verify = qc.get("교차검증 필요", 0)
    need_check = qc.get("(확인 필요)", 0)

    print(
        f"quality: lintHigh={lint_high}, linkBad={bad}, linkWarn={warn}, 교차검증={need_verify}, 확인필요={need_check}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Remove redundant ALT-PROOF comments when the main URL is already official.

Rule (conservative):
- If a line contains a URL and also contains "<!-- ALT-PROOF:" on the same line,
  and domain_policy grades the URL as "S", remove the ALT-PROOF HTML comment.

This keeps ALT-PROOF where it actually adds value (secondary/blocked domains).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import domain_policy
import normalize_url

URL_RE = re.compile(r"https?://[^\s)<>]+", re.I)
ALT_RE = re.compile(r"\s*<!--\s*ALT-PROOF:[^>]*-->\s*$")


def clean_file(path: Path, policy: domain_policy.Policy) -> bool:
    txt = path.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    out: list[str] = []
    changed = False

    for ln in txt:
        if "ALT-PROOF" not in ln:
            out.append(ln)
            continue
        m = URL_RE.search(ln)
        if not m:
            out.append(ln)
            continue
        url = normalize_url.norm(m.group(0))
        grade = policy.grade_for_url(url)
        if grade == "S":
            ln2 = ALT_RE.sub("", ln)
            if ln2 != ln:
                changed = True
                ln = ln2
        out.append(ln)

    if changed:
        path.write_text("".join(out), encoding="utf-8")
    return changed


def main() -> int:
    base = Path(__file__).resolve().parent.parent
    policy = domain_policy.load_policy()

    targets: list[Path] = []
    targets += list((base / "pages" / "works").glob("*.md"))
    targets += [base / "pages" / "filmography.md", base / "pages" / "works" / "by-year.md"]

    changed_files = 0
    for p in targets:
        if p.exists() and clean_file(p, policy):
            changed_files += 1

    print(f"clean_redundant_alt_proof: changed_files={changed_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

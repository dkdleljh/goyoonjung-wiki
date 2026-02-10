#!/usr/bin/env python3
"""Apply user-approved promotions from today's news file.

Reads news/YYYY-MM-DD.md and looks for approval lines:
- APPROVE_PROFILE|출생지|<url>
- APPROVE_PROFILE|학력|<url>
- APPROVE_ENDO|<brand>|<url>
- APPROVE_AWARD|<year>|<award>|<url>

Applies best-effort edits:
- profile: add a '근거' line under the section and remove '(교차검증 필요)' marker for that field.
- endorsements: replace '링크(공식 발표): (확인 필요)' with provided url for matching brand.
- awards: fill '근거(공식)' column with provided url for matching (year, award).

Safety:
- Only applies URLs (does not invent facts).
- Leaves content unchanged if match is ambiguous.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TZ = "Asia/Seoul"

PROFILE = os.path.join(BASE, "pages", "profile.md")
AWARDS = os.path.join(BASE, "pages", "awards.md")
ENDO_FILES = [
    os.path.join(BASE, "pages", "endorsements", "beauty.md"),
    os.path.join(BASE, "pages", "endorsements", "fashion.md"),
    os.path.join(BASE, "pages", "endorsements", "lifestyle.md"),
]
NEWS_DIR = os.path.join(BASE, "news")

APPROVE_RE = re.compile(r"^\s*`?(APPROVE_[A-Z_]+\|.+?)`?\s*$")


def today() -> str:
    return os.environ.get("WIKI_TODAY") or os.popen(f"TZ={TZ} date +%Y-%m-%d").read().strip()


def read_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines(True)


def write_lines(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def load_approvals(news_path: str) -> list[str]:
    out = []
    for ln in read_lines(news_path):
        m = APPROVE_RE.match(ln)
        if m:
            out.append(m.group(1).strip())
    # de-dupe preserve order
    seen = set()
    uniq = []
    for a in out:
        if a in seen:
            continue
        seen.add(a)
        uniq.append(a)
    return uniq


def apply_profile(kind: str, url: str) -> bool:
    if not os.path.exists(PROFILE):
        return False
    lines = read_lines(PROFILE)

    changed = False
    if kind == "출생지":
        # find line starting with '- 출생지:'
        for i, ln in enumerate(lines):
            if ln.startswith("- 출생지:"):
                # remove marker
                lines[i] = ln.replace("(교차검증 필요) ", "")
                # insert 근거 line if not present in next few lines
                insert_at = i + 1
                if insert_at < len(lines) and "- 근거:" in lines[insert_at]:
                    return False
                lines.insert(insert_at, f"  - 근거: {url}\n")
                changed = True
                break

    if kind == "학력":
        # under '## 학력' replace '(교차검증 필요)' markers and add one 근거 line at end of section
        in_edu = False
        edu_start = None
        edu_end = None
        for i, ln in enumerate(lines):
            if ln.startswith("## 학력"):
                in_edu = True
                edu_start = i
                continue
            if in_edu and ln.startswith("## "):
                edu_end = i
                break
        if in_edu and edu_start is not None:
            if edu_end is None:
                edu_end = len(lines)
            # replace markers within section
            for j in range(edu_start, edu_end):
                if "(교차검증 필요)" in lines[j]:
                    lines[j] = lines[j].replace("(교차검증 필요) ", "")
                    changed = True
            # add 근거 line near end of section if not already
            already = any("- 근거:" in lines[j] and url in lines[j] for j in range(edu_start, edu_end))
            if not already:
                lines.insert(edu_end, f"- 근거: {url}\n")
                changed = True

    if changed:
        write_lines(PROFILE, lines)
    return changed


def apply_endorsement(brand: str, url: str) -> int:
    changed = 0
    for f in ENDO_FILES:
        if not os.path.exists(f):
            continue
        lines = read_lines(f)
        i = 0
        file_changed = False
        while i < len(lines):
            if lines[i].startswith("- 브랜드/회사명:") and brand in lines[i]:
                # scan until next entry
                j = i + 1
                end = j
                while end < len(lines) and not lines[end].startswith("- 브랜드/회사명:") and not lines[end].startswith("## "):
                    end += 1
                for k in range(i, end):
                    if lines[k].strip() == "- 링크(공식 발표): (확인 필요)":
                        lines[k] = f"  - 링크(공식 발표): {url}\n"
                        file_changed = True
                        changed += 1
                        break
                i = end
            else:
                i += 1
        if file_changed:
            write_lines(f, lines)
    return changed


def apply_award(year: str, award: str, url: str) -> bool:
    if not os.path.exists(AWARDS):
        return False
    lines = read_lines(AWARDS)
    changed = False
    for i, ln in enumerate(lines):
        if not ln.startswith("|"):
            continue
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) < 8:
            continue
        y, a = cols[0], cols[1]
        if y == year and a == award and not cols[6]:
            cols[6] = url
            lines[i] = "| " + " | ".join(cols[:8]) + " |\n"
            changed = True
            break
    if changed:
        write_lines(AWARDS, lines)
    return changed


def main() -> int:
    t = today()
    news_path = os.path.join(NEWS_DIR, f"{t}.md")
    if not os.path.exists(news_path):
        print("apply_approved_promotions: no news file")
        return 0

    approvals = load_approvals(news_path)
    if not approvals:
        print("apply_approved_promotions: none")
        return 0

    applied = 0
    for a in approvals:
        parts = a.split("|")
        if parts[0] == "APPROVE_PROFILE" and len(parts) == 3:
            if apply_profile(parts[1], parts[2]):
                applied += 1
        elif parts[0] == "APPROVE_ENDO" and len(parts) == 3:
            applied += apply_endorsement(parts[1], parts[2])
        elif parts[0] == "APPROVE_AWARD" and len(parts) == 4:
            if apply_award(parts[1], parts[2], parts[3]):
                applied += 1

    print(f"apply_approved_promotions: applied={applied}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

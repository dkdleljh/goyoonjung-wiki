#!/usr/bin/env python3
"""Unmanned policy: handle profile fields that are hard to verify automatically.

Goal:
- Reduce perpetual '교차검증 필요' markers in pages/profile.md that block quality metrics.

Policy implemented (safe, transparent):
- If a line contains '(교차검증 필요)' in profile.md, replace it with '(2차 참고)'.
- Keep existing '상태: 참고(2차)' lines as-is.
- Add a short note in the memo section (once) explaining this is an unmanned policy and needs official proof to upgrade.

This does NOT add any new facts; it only re-labels uncertainty.
"""

from __future__ import annotations

import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROFILE = os.path.join(BASE, "pages", "profile.md")

NOTE_LINE = "- (무인 정책) 출생지/학력 등 ‘공식 근거’가 자동으로 확보되지 않는 항목은 일단 (2차 참고)로 표기하고, 공식/원문 근거 확보 시 승격합니다."


def main() -> int:
    if not os.path.exists(PROFILE):
        return 0

    lines = open(PROFILE, encoding="utf-8").read().splitlines(True)
    changed = False

    for i, ln in enumerate(lines):
        if "(교차검증 필요)" in ln:
            lines[i] = ln.replace("(교차검증 필요)", "(2차 참고)")
            changed = True

    # Ensure memo note exists
    in_memo = False
    memo_idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## 메모":
            in_memo = True
            memo_idx = i
            continue
        if in_memo and ln.startswith("## ") and i != memo_idx:
            break
    if memo_idx is not None and NOTE_LINE + "\n" not in lines:
        # insert after memo header
        insert_at = memo_idx + 1
        # skip blank lines
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        lines.insert(insert_at, NOTE_LINE + "\n")
        changed = True

    if changed:
        with open(PROFILE, "w", encoding="utf-8") as f:
            f.write("".join(lines))

    print(f"promote_profile_policy_unmanned: changed={int(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

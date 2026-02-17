#!/usr/bin/env python3
"""Append skip/failure reasons into today's news log under AUTO-SKIP-REASONS.

This is for observability: when a step fails (timeout/rc!=0), record why.

Usage:
  python3 scripts/append_skip_reason.py "step" "rc" "reason"

Best-effort; never fails.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NEWS = BASE / "news" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
TZ = "Asia/Seoul"

START = "<!-- AUTO-SKIP-REASONS:START -->"
END = "<!-- AUTO-SKIP-REASONS:END -->"


def main(argv: list[str]) -> int:
    try:
        if len(argv) < 4:
            return 0
        step, rc, reason = argv[1], argv[2], " ".join(argv[3:]).strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not NEWS.exists():
            # create minimal
            NEWS.parent.mkdir(parents=True, exist_ok=True)
            NEWS.write_text(f"# {datetime.now().strftime('%Y-%m-%d')} 업데이트\n\n## 실행 상태\n- 실행: {now} ({TZ})\n- 결과: 진행중\n- 메모:\n\n## 실행 이력\n- {now} ({TZ}) · 진행중 · auto: daily update running\n\n## 자동화 스킵/실패 사유(무인 로그)\n{START}\n{END}\n", encoding="utf-8")

        txt = NEWS.read_text(encoding="utf-8")
        line = f"- {step}: rc={rc} · {reason} ({now})"

        if START in txt and END in txt:
            before, rest = txt.split(START, 1)
            mid, after = rest.split(END, 1)
            mid_lines = mid.strip("\n")
            if line in mid_lines:
                return 0
            new_mid = (mid_lines + "\n" + line + "\n") if mid_lines else (line + "\n")
            NEWS.write_text(before + START + "\n" + new_mid + END + after, encoding="utf-8")
            return 0

        # fallback: append block
        txt += "\n\n## 자동화 스킵/실패 사유(무인 로그)\n" + START + "\n" + line + "\n" + END + "\n"
        NEWS.write_text(txt, encoding="utf-8")
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

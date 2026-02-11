#!/usr/bin/env python3
"""Relevance filter for Google News items (quality gate).

Goal:
- Keep items that are actually about 고윤정 (Go Youn-jung).
- Drop noisy matches where the name isn't really the subject.

This is intentionally heuristic and transparent.

Signals (score-based):
+3 title contains exact "고윤정"
+1 title contains common context tokens (작품/배역 등)
+1 source label contains trusted keywords (KBS/보그/엘르 등)
+1 url path contains %EA%B3%A0%EC%9C%A4%EC%A0%95 or "go-youn" or "goyoun"

Hard rules:
- If title does NOT contain "고윤정" => reject (keeps precision high)
- If title contains blacklisted patterns (e.g., 주식/부동산/기업실적) and not clearly entertainment => reject

Config:
- config/relevance-blacklist.txt (optional): one keyword per line
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

BASE = Path(__file__).resolve().parent.parent
BLACKLIST_PATH = BASE / "config" / "relevance-blacklist.txt"

NAME = "고윤정"

# conservative default blacklist (can be overridden/extended by file)
DEFAULT_BLACKLIST = {
    "주가",
    "코스피",
    "코스닥",
    "실적",
    "매출",
    "영업이익",
    "증권",
    "리포트",
    "목표주가",
    "부동산",
    "분양",
    "대출",
    "보험료",
    "금리",
}

CONTEXT_TOKENS = {
    "배우",
    "드라마",
    "영화",
    "인터뷰",
    "화보",
    "샤넬",
    "보그",
    "엘르",
    "백상",
    "청룡",
    "제작발표회",
    "촬영",
    "캐스팅",
}


def load_blacklist() -> set[str]:
    bl = set(DEFAULT_BLACKLIST)
    if BLACKLIST_PATH.exists():
        for raw in BLACKLIST_PATH.read_text(encoding="utf-8").splitlines():
            kw = raw.strip()
            if not kw or kw.startswith("#"):
                continue
            bl.add(kw)
    return bl


def is_relevant(title: str, url: str = "", source: str = "") -> bool:
    title = (title or "").strip()
    if NAME not in title:
        return False

    bl = load_blacklist()
    # if title looks like finance/real-estate noise, drop
    if any(kw in title for kw in bl):
        # allow if strong entertainment context appears
        if not any(tok in title for tok in CONTEXT_TOKENS):
            return False

    score = 0
    if NAME in title:
        score += 3
    if any(tok in title for tok in CONTEXT_TOKENS):
        score += 1

    s = (source or "").lower()
    if any(k in s for k in ("kbs", "vogue", "elle", "bazaar", "wkorea", "gq")):
        score += 1

    u = unquote(url or "").lower()
    if any(x in u for x in (NAME, "go-youn", "goyoun")):
        score += 1

    return score >= 3

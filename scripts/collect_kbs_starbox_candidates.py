#!/usr/bin/env python3
"""Collect candidate KBS Starbox article URLs for Go Youn-jung.

- Fetches KBS Starbox person page (idx=220921)
- Extracts list_view links
- Filters against sources/seen-urls.txt
- Appends to news/YYYY-MM-DD.md as candidates

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
SEEN_TXT = BASE / "sources" / "seen-urls.txt"
NEWS_DIR = BASE / "news"

PERSON_URL = "https://kstar.kbs.co.kr/person_view.html?idx=220921"
TIMEOUT = (5, 20)
UA = "goyoonjung-wiki/1.0 (+https://github.com)"

LINK_RE = re.compile(r"https?://kstar\\.kbs\\.co\\.kr/list_view\\.html\\?idx=\\d+", re.I)


@dataclass
class Candidate:
    url: str
    source: str


def load_seen() -> set[str]:
    if not SEEN_TXT.exists():
        return set()
    return {ln.strip() for ln in SEEN_TXT.read_text(encoding="utf-8").splitlines() if ln.strip()}


def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def append_news(cands: list[Candidate]) -> Path:
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out = NEWS_DIR / f"{today}.md"

    header = f"\n\n## ✅ 자동 수집 후보(KBS 스타박스) — {today}\n"
    lines = [header, f"- 소스: {PERSON_URL}\n", "- 원칙: 링크만 수집(전문 복사 금지) / 확정 반영은 pages에 분류\n"]
    for c in cands[:60]:
        lines.append(f"- {c.url}\n")

    if out.exists():
        txt = out.read_text(encoding="utf-8")
    else:
        txt = f"# {today}\n\n"
    out.write_text(txt + "".join(lines), encoding="utf-8")
    return out


def main() -> None:
    seen = load_seen()
    html = fetch(PERSON_URL)
    if not html:
        print("collect_kbs_starbox_candidates: fetch failed")
        return

    urls = sorted(set(LINK_RE.findall(html)))
    new = [u for u in urls if u not in seen]

    if not new:
        print("collect_kbs_starbox_candidates: no new candidates")
        return

    out = append_news([Candidate(url=u, source=PERSON_URL) for u in new])
    print(f"collect_kbs_starbox_candidates: +{len(new)} -> {out}")


if __name__ == "__main__":
    main()

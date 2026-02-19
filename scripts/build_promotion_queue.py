#!/usr/bin/env python3
"""Build promotion queue from wiki pages.

Generates pages/promotion-queue.md

Rules (recommended, conservative):
- Find blocks with '상태: 보도(2차)' older than 30 days.
- Include link + file + date + hint.
- Also include endorsement entries where '브랜드/캠페인: (자동 분류 필요)' remains.

Link-first; no article text is copied.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import db_manager

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
OUT = PAGES / "promotion-queue.md"

DATE_RE = re.compile(r"^- 날짜:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)
STATUS_RE = re.compile(r"^- 상태:\s*(.+?)\s*$", re.M)
URL_RE = re.compile(r"https?://[^\s]+")
ID_RE = re.compile(r"^- id:\s*(https?://[^\s]+)\s*$", re.M)


@dataclass(frozen=True)
class QueueItem:
    date: str
    file: str
    url: str
    reason: str


def parse_blocks(text: str) -> list[str]:
    # heuristic: blocks start with '- 날짜:' and separated by blank line
    blocks: list[str] = []
    cur: list[str] = []
    for ln in text.splitlines():
        if ln.strip().startswith('- 날짜:') and cur:
            blocks.append("\n".join(cur).strip() + "\n")
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur).strip() + "\n")
    return blocks


def main() -> int:
    cutoff = datetime.now() - timedelta(days=30)
    items: list[QueueItem] = []

    for p in PAGES.rglob('*.md'):
        rel = str(p.relative_to(BASE))
        txt = p.read_text(encoding='utf-8', errors='ignore')
        if '- 상태:' not in txt and '브랜드/캠페인:' not in txt:
            continue

        for b in parse_blocks(txt):
            mdate = re.search(r"^- 날짜:\s*(\d{4}-\d{2}-\d{2})\s*$", b, flags=re.M)
            mstatus = re.search(r"^- 상태:\s*(.+?)\s*$", b, flags=re.M)
            mid = re.search(r"^- id:\s*(https?://[^\s]+)\s*$", b, flags=re.M)
            date_s = mdate.group(1) if mdate else ""
            status = mstatus.group(1).strip() if mstatus else ""
            url = mid.group(1).strip() if mid else ""

            # endorsements: missing brand label
            if '브랜드/캠페인:' in b and '(자동 분류 필요)' in b and url:
                items.append(QueueItem(date=date_s or "(unknown)", file=rel, url=url, reason='endorsement brand label missing'))
                continue

            if status == '보도(2차)' and date_s and url:
                try:
                    dt = datetime.strptime(date_s, '%Y-%m-%d')
                except Exception:
                    continue
                if dt <= cutoff:
                    items.append(QueueItem(date=date_s, file=rel, url=url, reason='보도(2차) 오래됨 → 공식/원문 승격 필요'))

    items = sorted(items, key=lambda x: (x.date, x.file, x.url))
    db_manager.init_db()
    queue_cands = db_manager.list_candidates(lane="queue", limit=200)

    lines = [
        '# Promotion Queue (auto)',
        '',
        f'> Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")} (Asia/Seoul)',
        '',
        '## 대상(승격/정리 필요)',
    ]

    if not items:
        lines.append('- (없음)')
    else:
        for it in items[:300]:
            lines.append(f"- {it.date} · {it.reason} · {it.file} · {it.url}")

    lines += [
        "",
        "## 도메인 A 등급 후보(자동 수집)",
    ]
    if not queue_cands:
        lines.append("- (없음)")
    else:
        for row in queue_cands:
            lines.append(
                f"- {row['last_seen_at'][:10]} · grade={row['grade']} · {row['source']} · "
                f"[{row['title']}]({row['url']})"
            )

    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding='utf-8')
    print(f"build_promotion_queue: items={len(items)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

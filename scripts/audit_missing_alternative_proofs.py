#!/usr/bin/env python3
"""Audit skipped-domain URLs that still lack alternative proof links.

After running:
- scripts/suggest_alternative_proofs.py
- scripts/apply_alternative_proofs.py

some skipped URLs may still have no alternative proof inserted (because none were
found in-file). This script lists those locations for manual or future automated
(backfill) work.

No web fetch.

Outputs
- pages/alternative-proof-missing.md
- data/alternative_proofs_missing.json
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
SOURCES = BASE / "sources"
OUT_MD = PAGES / "alternative-proof-missing.md"
OUT_JSON = BASE / "data" / "alternative_proofs_missing.json"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")

ALT_MARKERS = ("대체 근거(열리는 링크):", "ALT-PROOF:")

SKIP_DOMAINS = {
    "namu.wiki",
    "nc.press",
    "kstarfashion.com",
    "program.tving.com",
    "tving.com",
    "disneyplus.com",
    "disneypluskr.com",
    "chanel.com",
    "boucheron.com",
    "about.netflix.com",
    "yna.co.kr",
    "goodal.com",
    "vodana.co.kr",
    "lensme.co.kr",
    "easytomorrow.co.kr",
}

# Exclude auto-generated/report pages where missing alternatives are expected.
EXCLUDE = {
    "pages/skipped-link-backlog.md",
    "pages/alternative-proof-candidates.md",
    "pages/alternative-proof-missing.md",
    "pages/link-health.md",
    "pages/system_status.md",
    "pages/quality-report.md",
    "pages/content-gaps.md",
    "pages/lint-report.md",
    "pages/daily-report.md",

    # Source lists / auto-generated indexes: missing alternatives are expected.
    "sources/watchlist.md",
}

EXCLUDE_PATTERNS = [
    re.compile(r"^pages/.+/by-year\.md$"),
]


@dataclass(frozen=True)
class Missing:
    file: str
    line: int
    url: str
    host: str


def iter_md_files() -> list[Path]:
    out: list[Path] = []
    for root in (PAGES, SOURCES):
        if root.exists():
            out.extend(root.rglob("*.md"))
    return sorted(out)


def is_skipped(u: str) -> bool:
    host = urlsplit(u).netloc.lower()
    return any(host.endswith(d) for d in SKIP_DOMAINS)


def has_alt_near(lines: list[str], idx0: int, window: int = 4) -> bool:
    # idx0 is 1-indexed line number
    a = max(0, (idx0 - 1))
    b = min(len(lines), (idx0 - 1) + window)
    for j in range(a, b):
        if any(m in lines[j] for m in ALT_MARKERS):
            return True
    return False


def main() -> None:
    missing: list[Missing] = []

    for p in iter_md_files():
        rel = p.relative_to(BASE).as_posix()
        if rel in EXCLUDE:
            continue
        if any(rx.search(rel) for rx in EXCLUDE_PATTERNS):
            continue
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, ln in enumerate(lines, start=1):
            for u in URL_RE.findall(ln):
                if not is_skipped(u):
                    continue
                if has_alt_near(lines, i):
                    continue
                host = urlsplit(u).netloc.lower()
                missing.append(Missing(file=rel, line=i, url=u, host=host))

    # De-dupe
    uniq = {(m.file, m.line, m.url): m for m in missing}
    missing = list(uniq.values())

    # Write JSON
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {"generated": datetime.now().isoformat(), "count": len(missing), "items": [asdict(m) for m in missing]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Write Markdown
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md: list[str] = []
    md.append("# 대체 근거 미확보(스킵 도메인) 백로그")
    md.append("")
    md.append(f"> 갱신: {now} (Asia/Seoul)")
    md.append("")
    md.append("이 목록은 스킵/차단 도메인 URL이 **대체 근거(열리는 링크)** 없이 남아있는 위치입니다.")
    md.append("자동으로 같은 파일 내에서 후보를 찾지 못한 경우이므로, 다음 중 하나로 보강이 필요합니다.")
    md.append("- 공식 YouTube 업로드(티저/예고/메이킹)\n- 방송사/제작사 공식 프로그램 페이지\n- 시상식 공식 결과 페이지\n- 소속사(MAA) 공지/프로필")
    md.append("")
    md.append(f"## 총 {len(missing)}개")
    md.append("")

    by_host: dict[str, list[Missing]] = {}
    for m in sorted(missing, key=lambda x: (x.host, x.file, x.line)):
        by_host.setdefault(m.host, []).append(m)

    for host, arr in by_host.items():
        md.append(f"## {host} ({len(arr)})")
        md.append("")
        for m in arr[:400]:
            md.append(f"- {m.file}:{m.line} · {m.url}")
        md.append("")

    md.append("---")
    md.append("※ 자동 생성 파일입니다. (스크립트: scripts/audit_missing_alternative_proofs.py)")
    md.append("")

    OUT_MD.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    print(f"audit_missing_alternative_proofs: count={len(missing)} -> {OUT_MD}")


if __name__ == "__main__":
    main()

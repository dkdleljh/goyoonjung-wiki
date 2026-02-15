#!/usr/bin/env python3
"""Audit URLs that are skipped in link health checks.

Background
- Some domains are intentionally skipped in scripts/check_links.py because they block bots.
- Those links may still be valid, but we want a *verifiable* alternative proof chain.

Output (auto-generated)
- pages/skipped-link-backlog.md
- data/skipped_links.json

Policy
- Do not remove links.
- Do not fetch the web.
- Provide file+line context so we can add alternative official/primary links later.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE / "pages"
SOURCES_DIR = BASE / "sources"
OUT_MD = PAGES_DIR / "skipped-link-backlog.md"
OUT_JSON = BASE / "data" / "skipped_links.json"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")

# Keep aligned with scripts/check_links.py SKIP_DOMAINS additions.
SKIP_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "chanel.com",
    "boucheron.com",
    "disneyplus.com",
    "disneypluskr.com",
    "tving.com",
    "program.tving.com",
    "yna.co.kr",
    "about.netflix.com",
    "goodal.com",
    "vodana.co.kr",
    "lensme.co.kr",
    "easytomorrow.co.kr",
    "namu.wiki",
    "nc.press",
    "kstarfashion.com",
}


@dataclass(frozen=True)
class Hit:
    file: str
    line: int
    url: str
    host: str


def iter_md_files() -> list[Path]:
    out: list[Path] = []
    for root in (PAGES_DIR, SOURCES_DIR):
        if not root.exists():
            continue
        out.extend(root.rglob("*.md"))
    return sorted(out)


def is_skipped(host: str) -> bool:
    host = host.lower()
    return any(host.endswith(d) for d in SKIP_DOMAINS)


def scan_file(path: Path) -> list[Hit]:
    hits: list[Hit] = []
    rel = path.relative_to(BASE).as_posix()
    for i, ln in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        for u in URL_RE.findall(ln):
            host = urlsplit(u).netloc.lower()
            if not host:
                continue
            if is_skipped(host):
                hits.append(Hit(file=rel, line=i, url=u, host=host))
    return hits


def main() -> None:
    hits: list[Hit] = []
    for p in iter_md_files():
        hits.extend(scan_file(p))

    # De-dupe by (file,line,url)
    uniq = {(h.file, h.line, h.url): h for h in hits}
    hits = list(uniq.values())

    # Group by host
    by_host: dict[str, list[Hit]] = {}
    for h in sorted(hits, key=lambda x: (x.host, x.file, x.line)):
        by_host.setdefault(h.host, []).append(h)

    # Write JSON
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps({"generated": datetime.now().isoformat(), "count": len(hits), "items": [asdict(h) for h in hits]}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    # Write Markdown
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []
    lines.append("# 스킵 도메인 링크 보강 백로그")
    lines.append("")
    lines.append(f"> 갱신: {now} (Asia/Seoul)")
    lines.append("")
    lines.append("이 페이지는 **링크 건강검진에서 스킵 처리되는 도메인**(봇 차단/헤비 JS 등)의 URL들을 모아,")
    lines.append("향후 ‘열리는 1차 근거(공식/원문)’ 링크를 **대체로 병기**하기 위한 백로그입니다.")
    lines.append("")
    lines.append("## 원칙")
    lines.append("- 링크를 삭제하지 않습니다(기록 유지).")
    lines.append("- 대신, 같은 사실을 뒷받침하는 **열리는 공식/1차 링크**를 함께 추가합니다.")
    lines.append("- 예: 공식 YouTube 업로드 / 제작사 보도자료 / 방송사 프로그램 페이지 / 시상식 공식 결과 페이지")
    lines.append("")
    lines.append(f"## 총 {len(hits)}개")
    lines.append("")

    for host, arr in by_host.items():
        lines.append(f"## {host} ({len(arr)})")
        lines.append("")
        for h in arr[:400]:
            lines.append(f"- {h.file}:{h.line} · {h.url}")
        lines.append("")

    lines.append("---")
    lines.append("※ 자동 생성 파일입니다. (스크립트: scripts/audit_skipped_links.py)")
    lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(f"audit_skipped_links: count={len(hits)} -> {OUT_MD}")


if __name__ == "__main__":
    main()

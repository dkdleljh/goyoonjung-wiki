#!/usr/bin/env python3
"""Suggest alternative 'verifiable' proof links for skipped/blocked domains.

We intentionally skip some domains in link-health checks due to bot blocking.
This script helps the wiki become more robust by suggesting *additional* links
that are more likely to be accessible automatically.

Constraints
- No web fetch.
- No fact invention.
- Only suggests links already present in the same page or strongly related pages.

Outputs
- pages/alternative-proof-candidates.md
- data/alternative_proofs.json

Candidates require human review. Proximity is not evidence of the same claim.
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
OUT_MD = PAGES / "alternative-proof-candidates.md"
OUT_JSON = BASE / "data" / "alternative_proofs.json"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
H1_RE = re.compile(r"^#\s+(.+?)\s*$")

# Must match scripts/check_links.py
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
class Suggestion:
    file: str
    title: str
    line: int
    skipped_url: str
    skipped_host: str
    alternatives: list[str]
    review_status: str = "pending"
    claim_id: str = ""
    target_line: str = ""
    reviewed_by: str = ""
    reviewed_at: str = ""


def iter_md_files() -> list[Path]:
    # Canonical claim pages only: generated reports must not feed their own output.
    names = ["profile.md", "filmography.md", "awards.md", "schedule.md", "appearances.md", "interviews.md", "sns.md"]
    out = [PAGES / name for name in names]
    for folder in ("works", "endorsements", "pictorials", "videos", "brands"):
        out.extend((PAGES / folder).glob("*.md"))
    return sorted(p for p in out if p.is_file() and p.name != "by-year.md")


def host_of(url: str) -> str:
    return urlsplit(url).netloc.lower()


def is_skipped_host(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in SKIP_DOMAINS)


def extract_title(lines: list[str]) -> str:
    for ln in lines[:40]:
        m = H1_RE.match(ln.strip())
        if m:
            return m.group(1).strip()
    return "(no title)"


def collect_urls(lines: list[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for i, ln in enumerate(lines, start=1):
        for u in URL_RE.findall(ln):
            out.append((i, u))
    return out


def nearby_alternatives(urls: list[tuple[int, str]], target_line: int, window: int = 30, limit: int = 5) -> list[str]:
    # Prefer URLs close to the skipped URL occurrence.
    alts: list[str] = []
    for ln, u in urls:
        if ln != target_line:
            continue
        h = host_of(u)
        if is_skipped_host(h):
            continue
        if u not in alts:
            alts.append(u)
        if len(alts) >= limit:
            return alts
    return alts




def main() -> None:
    suggestions: list[Suggestion] = []

    for p in iter_md_files():
        rel = p.relative_to(BASE).as_posix()
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        title = extract_title(lines)
        urls = collect_urls(lines)
        if not urls:
            continue

        for ln, u in urls:
            h = host_of(u)
            if not h or not is_skipped_host(h):
                continue
            alts = nearby_alternatives(urls, ln)
            suggestions.append(
                Suggestion(
                    file=rel,
                    title=title,
                    line=ln,
                    skipped_url=u,
                    skipped_host=h,
                    alternatives=alts,
                    target_line=lines[ln - 1],
                )
            )

    # De-dupe by (file,line,url)
    uniq = {(s.file, s.line, s.skipped_url): s for s in suggestions}
    suggestions = list(uniq.values())

    # Write JSON
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "generated": datetime.now().isoformat(),
                "count": len(suggestions),
                "items": [asdict(s) for s in suggestions],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Write Markdown
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md: list[str] = []
    md.append("# 대체 1차 근거 링크 후보(자동)")
    md.append("")
    md.append(f"> 갱신: {now} (Asia/Seoul)")
    md.append("")
    md.append("이 문서는 링크 건강검진에서 스킵되는 도메인(봇 차단/헤비 JS 등)에 대해,")
    md.append("같은 행에 있는 링크만 검토 후보로 제시합니다. 접근 가능성이나 동일 사실의 근거임을 보장하지 않습니다.")
    md.append("")
    md.append("## 사용법")
    md.append("- 원문을 대조해 동일 사실을 확인한 뒤 data/reviewed_alternative_proofs.json에 해당 항목을 복사하고 claim_id, reviewed_by, reviewed_at, review_status=approved를 기록하세요.")
    md.append("- 후보가 비어 있으면: 공식 YouTube 업로드/방송사 페이지/제작사 보도자료 등으로 수동 보강하세요.")
    md.append("")
    md.append(f"## 총 {len(suggestions)}개")
    md.append("")

    for s in sorted(suggestions, key=lambda x: (x.skipped_host, x.file, x.line))[:600]:
        md.append(f"- {s.file}:{s.line} · **{s.title}**")
        md.append(f"  - 스킵 URL: {s.skipped_url}")
        if s.alternatives:
            md.append("  - 대체 후보:")
            for a in s.alternatives:
                md.append(f"    - {a}")
        else:
            md.append("  - 대체 후보: (없음)")
        md.append("")

    md.append("---")
    md.append("※ 자동 생성 파일입니다. (스크립트: scripts/suggest_alternative_proofs.py)")
    md.append("")

    OUT_MD.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    print(f"suggest_alternative_proofs: count={len(suggestions)} -> {OUT_MD}")


if __name__ == "__main__":
    main()

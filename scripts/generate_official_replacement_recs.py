#!/usr/bin/env python3
"""Generate conservative recommendations to replace secondary links with official proofs.

We scan key content pages (interviews/endorsements/pictorials/brands/magazines) for lines that:
- contain an URL, and
- contain an ALT-PROOF list with one or more official(S-grade) domains.

If the main URL is NOT S-grade but the ALT-PROOF contains an S-grade URL, we recommend switching.
This script does not auto-edit; it only outputs a checklist page.
"""

from __future__ import annotations

import re
from pathlib import Path

import domain_policy
import normalize_url

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "pages" / "recommendations" / "official-replacement-candidates.md"

URL_RE = re.compile(r"https?://[^\s)<>]+", re.I)
ALT_RE = re.compile(r"ALT-PROOF:\s*([^>]+?)\s*-->")


OFFICIAL_DOMAINS = {
    # streaming/platform official
    "www.netflix.com",
    "netflix.com",
    "about.netflix.com",
    "www.disneyplus.com",
    "disneyplus.com",
    "www.tving.com",
    "tving.com",
    # broadcaster/program
    "tvn.cjenm.com",
    # agency (kept separate; generally not a replacement for press, but can be proof for cast)
    "maa.co.kr",
}


def host(url: str) -> str:
    m = re.match(r"https?://([^/]+)/", url)
    return (m.group(1).lower() if m else "")


def is_official_url(url: str, policy: domain_policy.Policy) -> bool:
    """Official proof (stricter than S-grade news)."""
    h = host(url)
    if h.startswith("www."):
        h2 = h[4:]
    else:
        h2 = h
    if h in OFFICIAL_DOMAINS or h2 in OFFICIAL_DOMAINS:
        return True
    # fallback: if policy marks as S AND it is one of the official domains list
    try:
        _ = policy.grade_for_url(normalize_url.norm(url))
    except Exception:
        pass
    return False


def main() -> int:
    policy = domain_policy.load_policy()

    targets: list[Path] = []
    for pat in [
        "pages/interviews*.md",
        "pages/endorsements*.md",
        "pages/pictorials*.md",
        "pages/works/*.md",
        "pages/filmography.md",
    ]:
        targets += [Path(p) for p in sorted(BASE.glob(pat))]

    items: list[tuple[str, int, str, str, str]] = []

    for p in targets:
        if not p.exists():
            continue
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, ln in enumerate(lines, 1):
            if "ALT-PROOF" not in ln:
                continue
            m_url = URL_RE.search(ln)
            m_alt = ALT_RE.search(ln)
            if not (m_url and m_alt):
                continue
            main_url = m_url.group(0)
            # If the main link is already official, no recommendation.
            if is_official_url(main_url, policy):
                continue

            alt_blob = m_alt.group(1)
            alt_urls = URL_RE.findall(alt_blob)
            official_alts = [u for u in alt_urls if is_official_url(u, policy)]
            if not official_alts:
                continue

            # Avoid recommending MAA as a generic replacement for non-work content.
            # For works pages, MAA can be used as an interim cast proof.
            if "pages/works/" not in str(p):
                official_alts = [u for u in official_alts if host(u).endswith("netflix.com") or host(u).endswith("disneyplus.com") or host(u).endswith("tving.com") or host(u).endswith("tvn.cjenm.com") or host(u).endswith("about.netflix.com")]
            if not official_alts:
                continue

            items.append((str(p), idx, main_url, official_alts[0], ln.strip()[:180]))

    OUT.parent.mkdir(parents=True, exist_ok=True)

    lines_out: list[str] = []
    lines_out.append("# 공식 근거로 치환 가능 후보(추천)\n")
    lines_out.append("> 규칙: 본문 링크가 S-grade(공식/1차)가 아닌데, 같은 줄 ALT-PROOF에 S-grade가 있으면 ‘치환 후보’로 표기합니다.\n")
    lines_out.append("\n## 치환 후보 목록\n")

    if not items:
        lines_out.append("- (없음)\n")
    else:
        for path, lnno, main_url, s_alt, preview in items:
            lines_out.append(f"- `{path}:{lnno}`")
            lines_out.append(f"  - 현재 링크: {main_url}")
            lines_out.append(f"  - 추천 공식 링크: {s_alt}")
            lines_out.append(f"  - 원문(미리보기): {preview}")
            lines_out.append("")

    OUT.write_text("\n".join(lines_out).rstrip() + "\n", encoding="utf-8")
    print(f"generate_official_replacement_recs: items={len(items)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

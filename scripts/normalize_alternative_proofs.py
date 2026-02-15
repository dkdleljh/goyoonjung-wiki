#!/usr/bin/env python3
"""Normalize how alternative proofs are presented.

We previously inserted alternatives as either:
- a new line: "- 대체 근거(열리는 링크): ..."
- or an inline comment: "<!-- ALT-PROOF: ... -->"

This script standardizes presentation for readability while preserving history.

Rules
- Never remove the original skipped URL.
- Never fetch the web.
- Only transforms formatting.

Behavior
- For markdown files under pages/ and sources/:
  1) If a line contains an ALT-PROOF comment and appears inside a structured entry
     block, convert it to a separate line immediately after the line:
        - 대체 근거(열리는 링크): ...
     and remove the inline comment.
  2) If a structured entry contains a skipped URL line and an alternative line,
     annotate the skipped URL line with "(보조/차단 가능)" when it is a field line.

"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent

ALT_COMMENT_RE = re.compile(r"\s*<!--\s*ALT-PROOF:\s*(.+?)\s*-->\s*$")
ALT_LINE = "- 대체 근거(열리는 링크):"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")

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

ENTRY_FIELD_RE = re.compile(
    r"^\s*-\s*(링크\(원문\)|링크\(공식/원문\)|링크\(공식\)|링크)\s*:\s*"
)
DATE_FIELD_RE = re.compile(r"^\s*-\s*날짜\s*:\s*")
HEADING_RE = re.compile(r"^##\s+")


def host(url: str) -> str:
    return urlsplit(url).netloc.lower()


def is_skipped_url(url: str) -> bool:
    h = host(url)
    return any(h.endswith(d) for d in SKIP_DOMAINS)


def in_entry(lines: list[str], idx: int) -> bool:
    start = max(0, idx - 30)
    for j in range(idx, start - 1, -1):
        if HEADING_RE.match(lines[j].strip()):
            break
        if DATE_FIELD_RE.match(lines[j].strip()):
            return True
    return False


def has_alt_near(lines: list[str], idx: int, window: int = 6) -> bool:
    a = max(0, idx)
    b = min(len(lines), idx + window)
    for j in range(a, b):
        if lines[j].lstrip().startswith(ALT_LINE):
            return True
    return False


def annotate_skipped_field_line(ln: str) -> str:
    if "(보조/차단 가능)" in ln:
        return ln
    if not ENTRY_FIELD_RE.match(ln):
        return ln
    # Insert label just before the URL if possible
    urls = URL_RE.findall(ln)
    if not urls:
        return ln
    u = urls[0]
    if not is_skipped_url(u):
        return ln
    return ln.replace(u, f"{u} (보조/차단 가능)")


def process_file(p: Path) -> bool:
    orig = p.read_text(encoding="utf-8", errors="ignore")
    lines = orig.splitlines()
    changed = False

    i = 0
    while i < len(lines):
        ln = lines[i]

        # Convert ALT-PROOF comment to a separate line when inside an entry.
        m = ALT_COMMENT_RE.search(ln)
        if m and in_entry(lines, i) and not has_alt_near(lines, i):
            alts = m.group(1).strip()
            # Clean the line
            lines[i] = ALT_COMMENT_RE.sub("", ln).rstrip()
            lines.insert(i + 1, f"{ALT_LINE} {alts.replace(' | ', ', ')}")
            changed = True
            i += 2
            continue

        # Annotate skipped field lines when an alt line exists nearby
        if ENTRY_FIELD_RE.match(ln) and in_entry(lines, i) and has_alt_near(lines, i):
            new_ln = annotate_skipped_field_line(ln)
            if new_ln != ln:
                lines[i] = new_ln
                changed = True

        i += 1

    if changed:
        p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return changed


def main() -> None:
    targets = []
    for root in (BASE / "pages", BASE / "sources"):
        if root.exists():
            targets.extend(sorted(root.rglob("*.md")))

    changed = 0
    for p in targets:
        if process_file(p):
            changed += 1

    print(f"normalize_alternative_proofs: changed={changed}")


if __name__ == "__main__":
    main()

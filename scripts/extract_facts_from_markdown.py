#!/usr/bin/env python3
"""Extract structured facts from canonical Markdown pages."""

from __future__ import annotations

import json
import re

try:
    from scripts.automation_common import FACTS, PAGES, extract_urls, read_text, write_json
    from scripts.time_utils import seoul_timestamp_str
    from scripts.work_status import work_status
except Exception:  # pragma: no cover
    from automation_common import FACTS, PAGES, extract_urls, read_text, write_json  # type: ignore
    from time_utils import seoul_timestamp_str  # type: ignore
    from work_status import work_status


def split_table_row(line: str) -> list[str]:
    return [re.sub(r"<[^>]+>", "", cell).strip() for cell in line.strip().strip("|").split("|")]


def extract_works() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in read_text(PAGES / "filmography.md").splitlines():
        if not line.startswith("|") or "---" in line or "연도" in line:
            continue
        cols = split_table_row(line)
        if len(cols) < 6:
            continue
        year, platform, title, role, note, proof = cols[:6]
        rows.append(
            {
                "id": "work-" + re.sub(r"[^0-9a-z가-힣]+", "-", title.lower()).strip("-"),
                "type": "work",
                "year": year,
                "platform": platform,
                "title": title,
                "person": "고윤정",
                "role": role,
                "status": work_status(note),
                "note": note,
                "sources": extract_urls(proof),
                "extracted_at": seoul_timestamp_str(),
            }
        )
    registry_path = PAGES.parent / 'config/work-registry.json'
    discovered_path = FACTS / 'discovered-works.json'
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else []
    registry += json.loads(discovered_path.read_text()) if discovered_path.exists() else []
    overrides_path = FACTS / 'work-evidence-status.json'
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    for row in rows:
        match = next((r for r in registry if row['title'] in r.get('aliases', [r['title']])), None)
        if match:
            row['id'] = match['id']
            row['page'] = f"pages/works/{match['slug']}.md"
        proof = overrides.get(row['title'], {})
        if proof:
            row.update({k:v for k,v in proof.items() if k != 'sources'})
            row['sources'] = list(dict.fromkeys(row['sources'] + proof.get('sources', [])))
        row['verification'] = 'claim_evidence' if proof else 'editorial_record'
    return rows


def extract_awards() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in read_text(PAGES / "awards.md").splitlines():
        if not line.startswith("|") or "---" in line or "연도" in line:
            continue
        cols = split_table_row(line)
        if len(cols) < 8:
            continue
        year, ceremony, category, work, result, status, proof, note = cols[:8]
        rows.append(
            {
                "id": "award-" + re.sub(r"[^0-9a-z가-힣]+", "-", f"{year}-{ceremony}-{category}".lower()).strip("-"),
                "type": "award",
                "year": year,
                "ceremony": ceremony,
                "category": category,
                "work": work,
                "result": result,
                "status": status,
                "note": note,
                "sources": extract_urls(proof),
                "extracted_at": seoul_timestamp_str(),
            }
        )
    return rows


def extract_profile() -> dict[str, object]:
    text = read_text(PAGES / "profile.md")
    profile: dict[str, object] = {"type": "profile", "person": "고윤정", "sources": extract_urls(text)}
    for key in ["이름", "출생", "직업", "활동 기간", "소속사"]:
        match = re.search(rf"^- {re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
        if match:
            profile[key] = match.group(1).strip()
    profile["extracted_at"] = seoul_timestamp_str()
    return profile


def main() -> int:
    FACTS.mkdir(parents=True, exist_ok=True)
    works = extract_works()
    awards = extract_awards()
    profile = extract_profile()
    write_json(FACTS / "works.json", works)
    write_json(FACTS / "awards.json", awards)
    write_json(FACTS / "profile.json", profile)
    print(f"extract_facts: works={len(works)} awards={len(awards)} profile=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

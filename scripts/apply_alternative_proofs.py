#!/usr/bin/env python3
"""Apply explicitly reviewed evidence to an unchanged, unambiguous claim line."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "reviewed_alternative_proofs.json"


def approved(item: dict) -> bool:
    if item.get("review_status") != "approved":
        return False
    if not all(isinstance(item.get(k), str) and item[k].strip()
               for k in ("claim_id", "target_line", "reviewed_by", "reviewed_at", "skipped_url")):
        return False
    try:
        datetime.fromisoformat(item["reviewed_at"])
    except ValueError:
        return False
    alts = item.get("alternatives")
    return isinstance(alts, list) and bool(alts) and all(
        isinstance(url, str) and urlsplit(url).scheme in {"http", "https"}
        and bool(urlsplit(url).hostname) and not any(c in url for c in '<>\n\r" ')
        for url in alts
    )


def apply_item(item: dict) -> bool:
    if not approved(item):
        return False
    path = (BASE / item.get("file", "")).resolve()
    if not any(path.is_relative_to((BASE / root).resolve()) for root in ("pages", "sources")):
        return False
    if path.suffix != ".md" or not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    target = item["target_line"]
    if item["skipped_url"] not in target or lines.count(target) != 1:
        return False
    idx = lines.index(target)
    # JSON metadata is kept in the reviewed input; no untrusted text in the comment.
    lines[idx] += " <!-- REVIEWED-ALT-PROOF: " + " | ".join(item["alternatives"][:5]) + " -->"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main() -> None:
    raw = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}
    changed = sum(apply_item(item) for item in raw.get("items", []) if isinstance(item, dict))
    print(f"apply_alternative_proofs: reviewed_claims_applied={changed}")


if __name__ == "__main__":
    main()

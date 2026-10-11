#!/usr/bin/env python3
"""Idempotently remove unreviewed automatic evidence associations, preserving an audit trail."""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
COMMENT = re.compile(r"\s*<!--\s*ALT-PROOF:.*?-->")
LINE = re.compile(r"^\s*-\s*대체 근거\(열리는 링크\):")


def main() -> None:
    archive = BASE / "data" / "quarantine" / "legacy-alternative-proofs.json"
    records = json.loads(archive.read_text()) if archive.exists() else []
    count = 0
    for root in ("pages", "sources"):
        for path in sorted((BASE / root).rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            lines = []
            for number, line in enumerate(original.splitlines(), 1):
                if LINE.match(line) or COMMENT.search(line):
                    records.append({"file": str(path.relative_to(BASE)), "line": number, "original": line,
                                    "reason": "unreviewed proximity-based association"})
                    count += 1
                if not LINE.match(line):
                    lines.append(COMMENT.sub("", line))
            result = "\n".join(lines) + "\n"
            if result != original:
                path.write_text(result, encoding="utf-8")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"quarantined associations: {count}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Collect brand/endorsement evidence and keep uncertain roles in queue."""

from __future__ import annotations

try:
    from scripts import domain_policy
    from scripts.automation_common import (
        FACTS,
        PAGES,
        extract_urls,
        host_for_url,
        md_table,
        read_text,
        report_header,
        write_json,
    )
except Exception:  # pragma: no cover
    import domain_policy  # type: ignore
    from automation_common import (  # type: ignore
        FACTS,
        PAGES,
        extract_urls,
        host_for_url,
        md_table,
        read_text,
        report_header,
        write_json,
    )


def main() -> int:
    policy = domain_policy.load_policy()
    items: list[dict[str, object]] = []
    paths = [PAGES / "endorsements.md", *sorted((PAGES / "endorsements").glob("*.md"))]
    for path in paths:
        if not path.exists():
            continue
        text = read_text(path)
        for line in text.splitlines():
            urls = extract_urls(line)
            if not urls:
                continue
            lower = line.lower()
            role_uncertain = "확인 필요" in line or "추가" in line or "ambassador" in lower or "앰버서더" in line
            items.append(
                {
                    "page": path.relative_to(PAGES.parent).as_posix(),
                    "line": line.strip()[:240],
                    "urls": urls,
                    "hosts": [host_for_url(url) for url in urls],
                    "grades": [policy.grade_for_url(url) for url in urls],
                    "action": "verify_role" if role_uncertain else "record_evidence",
                }
            )
    write_json(FACTS / "brands.json", items)
    pending = [x for x in items if x["action"] == "verify_role"]
    table = [[x["page"], ", ".join(x["hosts"]), x["action"], x["line"]] for x in items[:80]]
    lines = report_header("Brand Evidence Watch (auto)")
    lines += [
        "## Summary",
        f"- brand_evidence_items: {len(items)}",
        f"- verify_role_items: {len(pending)}",
        "",
        "## Evidence",
        md_table(table, ["page", "hosts", "action", "line"]),
        "",
        "## Policy",
        "- 브랜드 공식 근거 없이 앰버서더/프렌즈/모델 역할을 자동 확정하지 않습니다.",
    ]
    (PAGES / "brand-evidence-watch.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"auto_collect_brands: items={len(items)} pending={len(pending)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

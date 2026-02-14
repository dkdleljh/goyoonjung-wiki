from __future__ import annotations

from pathlib import Path

import scripts.update_readme_today_links as r


def test_updates_quicklink_and_example(tmp_path: Path):
    md = (
        "# README\n\n"
        "- 오늘 로그 → `news/YYYY-MM-DD.md`\n\n"
        "- **오늘 로그(자동 실행/결과)**: `news/YYYY-MM-DD.md` (예: [`news/2099-12-31.md`](news/2099-12-31.md))\n"
    )
    p = tmp_path / "README.md"
    p.write_text(md, encoding="utf-8")

    assert r.update_readme(str(p), "2026-02-14") is True
    out = p.read_text(encoding="utf-8")
    assert "- 오늘 로그 → [`news/2026-02-14.md`](news/2026-02-14.md)" in out
    assert "(예: [`news/2026-02-14.md`](news/2026-02-14.md))" in out

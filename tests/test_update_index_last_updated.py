from __future__ import annotations

from pathlib import Path

import scripts.update_index_last_updated as u


def test_updates_today_log_line_variants(tmp_path: Path):
    md = (
        "# Title\n\n"
        "- 마지막 업데이트: **2099-12-31**\n"
        "- 오늘 로그(자동 실행/성공 여부): [`news/2099-12-31.md`](news/2099-12-31.md)\n"
    )
    p = tmp_path / "index.md"
    p.write_text(md, encoding="utf-8")

    assert u.update_index_md(str(p), "2026-02-14") is True
    out = p.read_text(encoding="utf-8")
    assert "- 마지막 업데이트: **2026-02-14**" in out
    assert "[`news/2026-02-14.md`](news/2026-02-14.md)" in out

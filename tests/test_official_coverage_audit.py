from __future__ import annotations

from pathlib import Path

import scripts.audit_official_coverage as audit


def test_normalize_title_aliases():
    assert audit.normalize_title("He is Psychometric") == "사이코메트리 그녀석"
    assert audit.normalize_title("Can This Love Be Translated?") == "이 사랑 통역 되나요"


def test_extract_maa_titles_dedupes_and_filters():
    html = """
    <li>'He is Psychometric'</li>
    <li>'The School Nurse Files'</li>
    <li>'He is Psychometric'</li>
    <li>'Moving'</li>
    """
    titles = audit.extract_maa_titles(html)
    assert titles == ["He is Psychometric", "The School Nurse Files", "Moving"]


def test_parse_local_filmography_reads_markdown_table():
    md = """
| 연도 | 플랫폼/방송사 | 작품 | 역할 | 비고 | 근거 |
|---:|---|---|---|---|---|
| 2019 | tvN | 사이코메트리 그녀석 | 김소현 | 데뷔작 | [MAA](x) |
| 2026 | Netflix | 이 사랑 통역 되나요? | 차무희 | 공개됨 | [Netflix](x) |
"""
    rows = audit.parse_local_filmography(md)
    assert [row["title"] for row in rows] == ["사이코메트리 그녀석", "이 사랑 통역 되나요?"]


def test_count_upcoming_schedule_items(tmp_path: Path, monkeypatch):
    schedule = tmp_path / "schedule.md"
    schedule.write_text(
        """
## 다가오는 일정 (Upcoming)
- 날짜/시간: 2026-04-01
- 날짜/시간: 2026-04-10
---
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "SCHEDULE_MD", schedule)
    assert audit.count_upcoming_schedule_items() == 2


def test_build_audit_compares_official_and_local(tmp_path: Path, monkeypatch):
    filmography = tmp_path / "filmography.md"
    filmography.write_text(
        """
| 연도 | 플랫폼/방송사 | 작품 | 역할 | 비고 | 근거 |
|---:|---|---|---|---|---|
| 2019 | tvN | 사이코메트리 그녀석 | 김소현 | 데뷔작 | [MAA](x) |
| 2024 | Disney+ | 조명가게 | 장희수 | 특별출연 | [Disney+](x) |
""",
        encoding="utf-8",
    )
    quality = tmp_path / "quality-report.md"
    quality.write_text(
        """
- [pages/awards.md:40] unresolved
- [pages/profile.md:49] unresolved
- [pages/sns.md:14] unresolved
""",
        encoding="utf-8",
    )
    queue = tmp_path / "verification-queue.md"
    queue.write_text("- total_items: 8\n", encoding="utf-8")
    schedule = tmp_path / "schedule.md"
    schedule.write_text("## 다가오는 일정 (Upcoming)\n- (현재 등록된 다가오는 공식 일정이 없습니다.)\n---\n", encoding="utf-8")

    monkeypatch.setattr(audit, "FILMOGRAPHY_MD", filmography)
    monkeypatch.setattr(audit, "QUALITY_MD", quality)
    monkeypatch.setattr(audit, "QUEUE_MD", queue)
    monkeypatch.setattr(audit, "SCHEDULE_MD", schedule)
    monkeypatch.setattr(
        audit,
        "fetch_maa_html",
        lambda timeout=15: "<li>'He is Psychometric'</li><li>'Moving'</li>",
    )

    result = audit.build_audit()

    assert "Moving" in result.missing_from_local
    assert "조명가게" in result.corroborated_extra or "조명가게" in result.extra_in_local
    assert result.unresolved_awards == 1
    assert result.verification_queue_items == 8
    assert result.coverage_readiness < result.official_work_sync


def test_build_audit_marks_corroborated_extra_with_official_work_page(tmp_path: Path, monkeypatch):
    filmography = tmp_path / "filmography.md"
    filmography.write_text(
        """
| 연도 | 플랫폼/방송사 | 작품 | 역할 | 비고 | 근거 |
|---:|---|---|---|---|---|
| 2024 | Disney+ | 조명가게 | 장희수 | 특별출연 | [Disney+](https://www.disneyplus.com/ko-kr/series/light-shop/3x1x2x3x4) |
""",
        encoding="utf-8",
    )
    quality = tmp_path / "quality-report.md"
    quality.write_text("", encoding="utf-8")
    queue = tmp_path / "verification-queue.md"
    queue.write_text("- total_items: 0\n", encoding="utf-8")
    schedule = tmp_path / "schedule.md"
    schedule.write_text("## 다가오는 일정 (Upcoming)\n- (현재 등록된 다가오는 공식 일정이 없습니다.)\n---\n", encoding="utf-8")
    works_dir = tmp_path / "works"
    works_dir.mkdir()
    (works_dir / "light-shop.md").write_text(
        "# 조명가게\n\n- https://www.disneyplus.com/ko-kr/series/light-shop/3x1x2x3x4\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "FILMOGRAPHY_MD", filmography)
    monkeypatch.setattr(audit, "QUALITY_MD", quality)
    monkeypatch.setattr(audit, "QUEUE_MD", queue)
    monkeypatch.setattr(audit, "SCHEDULE_MD", schedule)
    monkeypatch.setattr(audit, "WORKS_DIR", works_dir)
    monkeypatch.setattr(
        audit,
        "fetch_maa_html",
        lambda timeout=15: "<span class=\"ma-history__text\">Disney+ Original Series 'Moving' Jang Hee-Soo</span>",
    )

    result = audit.build_audit()

    assert result.missing_from_local == ["Moving"]
    assert result.corroborated_extra == ["조명가게"]
    assert result.extra_in_local == []

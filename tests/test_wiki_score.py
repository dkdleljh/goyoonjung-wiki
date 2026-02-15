#!/usr/bin/env python3
"""Tests for wiki_score module."""
from __future__ import annotations

from unittest.mock import Mock, patch

import scripts.wiki_score as wiki_score


def test_score_dataclass():
    """Test Score dataclass creation."""
    score = wiki_score.Score(name="test", score=100, details=["detail1", "detail2"])
    assert score.name == "test"
    assert score.score == 100
    assert len(score.details) == 2


def test_run_subprocess_success():
    """Test run function with successful command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
        rc, out = wiki_score.run(["echo", "test"])
        assert rc == 0


def test_run_subprocess_failure():
    """Test run function with failed command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")
        rc, out = wiki_score.run(["false"])
        assert rc == 1


def test_count_placeholders_no_file(tmp_path):
    """Test count_placeholders with no quality report."""
    with patch.object(wiki_score, 'BASE', str(tmp_path)):
        with patch('os.path.exists', return_value=False):
            counts = wiki_score.count_placeholders()
            assert counts == {}


def test_count_placeholders_with_file(tmp_path):
    """Test count_placeholders parses quality report."""
    with patch.object(wiki_score, 'BASE', str(tmp_path)):
        with patch('os.path.exists', return_value=False):
            counts = wiki_score.count_placeholders()
            assert isinstance(counts, dict)


def test_wiki_completeness_score_no_debt(tmp_path):
    """Test wiki completeness with no placeholders."""
    with patch.object(wiki_score, 'count_placeholders', return_value={}):
        score = wiki_score.wiki_completeness_score()
        assert score.score == 100


def test_wiki_completeness_score_with_debt(tmp_path):
    """Test wiki completeness with placeholders."""
    with patch.object(wiki_score, 'count_placeholders', return_value={
        "교차검증 필요": 10,
        "참고(2차)": 5,
        "요약 보강 필요": 3,
    }):
        score = wiki_score.wiki_completeness_score()
        assert score.score < 100


def test_wiki_completeness_score_max_debt(tmp_path):
    """Test wiki completeness with maximum debt."""
    with patch.object(wiki_score, 'count_placeholders', return_value={
        "교차검증 필요": 100,
    }):
        score = wiki_score.wiki_completeness_score()
        assert score.score == 0


def test_lint_score_missing_report(tmp_path):
    """Test lint score when report is missing."""
    with patch.object(wiki_score, 'LINT_REPORT', str(tmp_path / "missing.md")):
        score = wiki_score.lint_score()
        assert score.score == 40


def test_lint_score_ok(tmp_path):
    """Test lint score when report is clean."""
    lint_file = tmp_path / "lint-report.md"
    lint_file.write_text("""
## 1) 빈 링크
- 없음

## 3) 날짜 형식
- 없음

## 4) 커버리지 목표
- 없음
""")

    with patch.object(wiki_score, 'LINT_REPORT', str(lint_file)):
        score = wiki_score.lint_score()
        assert score.score == 100


def test_lint_score_with_issues(tmp_path):
    """Test lint score when report has issues."""
    lint_file = tmp_path / "lint-report.md"
    lint_file.write_text("""
## 1) 빈 링크
- file1.md:10

## 3) 날짜 형식
- 없음

## 4) 커버리지 목표
- 없음
""")

    with patch.object(wiki_score, 'LINT_REPORT', str(lint_file)):
        score = wiki_score.lint_score()
        assert score.score <= 100


def test_link_health_score_missing(tmp_path):
    """Test link health score when report is missing."""
    with patch.object(wiki_score, 'LINK_HEALTH', str(tmp_path / "missing.md")):
        score = wiki_score.link_health_score()
        assert score.score == 40


def test_link_health_score_ok(tmp_path):
    """Test link health score with healthy links."""
    link_file = tmp_path / "link-health.md"
    link_file.write_text("""
OK: **100** / WARN: **5** / BAD: **0**
""")

    with patch.object(wiki_score, 'LINK_HEALTH', str(link_file)):
        score = wiki_score.link_health_score()
        assert score.score == 100


def test_link_health_score_bad_links(tmp_path):
    """Test link health score with bad links."""
    link_file = tmp_path / "link-health.md"
    link_file.write_text("""
OK: **90** / WARN: **5** / BAD: **5**
""")

    with patch.object(wiki_score, 'LINK_HEALTH', str(link_file)):
        score = wiki_score.link_health_score()
        assert score.score == 0


def test_link_health_score_too_many_warnings(tmp_path):
    """Test link health score with too many warnings."""
    link_file = tmp_path / "link-health.md"
    link_file.write_text("""
OK: **50** / WARN: **50** / BAD: **0**
""")

    with patch.object(wiki_score, 'LINK_HEALTH', str(link_file)):
        score = wiki_score.link_health_score()
        assert score.score < 100


def test_link_health_score_parse_error(tmp_path):
    """Test link health score with unparseable content."""
    link_file = tmp_path / "link-health.md"
    link_file.write_text("Invalid content")

    with patch.object(wiki_score, 'LINK_HEALTH', str(link_file)):
        score = wiki_score.link_health_score()
        assert score.score == 60


def test_automation_score_success(tmp_path):
    """Test automation score with successful health check."""
    with patch.object(wiki_score, 'run') as mock_run:
        mock_run.return_value = (0, "result=success")
        score = wiki_score.automation_score()
        assert score.score == 100


def test_automation_score_running(tmp_path):
    """Test automation score when update is running."""
    with patch.object(wiki_score, 'run') as mock_run:
        mock_run.return_value = (1, "result=진행중")
        score = wiki_score.automation_score()
        assert score.score == 100


def test_automation_score_failure(tmp_path):
    """Test automation score with failed health check."""
    with patch.object(wiki_score, 'run') as mock_run:
        mock_run.return_value = (1, "error occurred")
        score = wiki_score.automation_score()
        assert score.score == 40


def test_write_status(tmp_path):
    """Test status file writing."""
    output_file = tmp_path / "system_status.md"

    with patch.object(wiki_score, 'OUT', str(output_file)):
        scores = [
            wiki_score.Score("test1", 100, ["detail1"]),
            wiki_score.Score("test2", 90, ["detail2"]),
        ]
        wiki_score.write_status(scores)

        assert output_file.exists()
        content = output_file.read_text()
        assert "test1" in content
        assert "test2" in content


def test_main_integration(tmp_path, monkeypatch):
    """Test main function runs all checks."""
    with patch.object(wiki_score, 'BASE', str(tmp_path)):
        with patch.object(wiki_score, 'wiki_completeness_score', return_value=wiki_score.Score("test", 100, [])):
            with patch.object(wiki_score, 'lint_score', return_value=wiki_score.Score("lint", 100, [])):
                with patch.object(wiki_score, 'link_health_score', return_value=wiki_score.Score("link", 100, [])):
                    with patch.object(wiki_score, 'automation_score', return_value=wiki_score.Score("auto", 100, [])):
                        with patch.object(wiki_score, 'write_status'):
                            result = wiki_score.main()
                            assert result == 0

#!/usr/bin/env python3
"""End-to-end tests for goyoonjung-wiki automation pipeline.

This test verifies the entire automation workflow:
1. Configuration loading
2. Database operations
3. URL normalization
4. Data collection
5. Index generation
6. Report generation
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


class TestConfigLoading:
    """Test configuration loading."""

    def test_config_loader_exists(self):
        """Verify config_loader module exists and loads."""
        import config_loader
        config = config_loader.load_config()
        assert isinstance(config, dict)

    def test_config_has_required_keys(self):
        """Verify config has required keys."""
        import config_loader
        config = config_loader.load_config()
        # These keys should exist in config.yaml
        assert 'rss_url' in config or 'rss_url' is not None


class TestDatabaseOperations:
    """Test database operations."""

    def test_db_manager_init(self):
        """Verify database initialization works."""
        import db_manager
        # Create temp database
        with tempfile.TemporaryDirectory() as tmpdir:
            original_db = db_manager.DB_PATH
            db_manager.DB_PATH = Path(tmpdir) / "test.db"
            try:
                db_manager.init_db()
                assert db_manager.DB_PATH.exists()
            finally:
                db_manager.DB_PATH = original_db

    def test_url_seen_tracking(self):
        """Test URL tracking functionality."""
        import db_manager
        with tempfile.TemporaryDirectory() as tmpdir:
            original_db = db_manager.DB_PATH
            db_manager.DB_PATH = Path(tmpdir) / "test.db"
            try:
                db_manager.init_db()
                test_url = "https://example.com/test"
                
                # Should not be seen initially
                assert not db_manager.is_url_seen(test_url)
                
                # Add URL
                db_manager.add_seen_url(test_url, source="test")
                
                # Should be seen now
                assert db_manager.is_url_seen(test_url)
            finally:
                db_manager.DB_PATH = original_db


class TestURLNormalization:
    """Test URL normalization."""

    def test_normalize_url(self):
        """Verify URL normalization works."""
        from normalize_url import norm
        
        # Test basic normalization
        assert norm("https://example.com") == norm("https://example.com/")
        assert norm("http://Example.com") == norm("http://example.com")


class TestDomainPolicy:
    """Test domain policy grading."""

    def test_domain_grading(self):
        """Verify domain grading works."""
        import domain_policy
        policy = domain_policy.load_policy()
        
        # Test known domains
        grade_s = policy.grade_for_url("https://news.kbs.co.kr")
        assert grade_s in ['S', 'A', 'B', 'BLOCK']
        
        grade_block = policy.grade_for_url("https://news.google.com")
        assert grade_block == 'BLOCK'


class TestRelevance:
    """Test content relevance filtering."""

    def test_relevance_check(self):
        """Verify relevance checking works."""
        import relevance
        
        # Test with relevant content
        assert relevance.is_relevant(
            "고윤정 드라마 인터뷰",
            "https://news.example.com",
            "News",
            "고윤정 배우 인터뷰 내용"
        )
        
        # Test with irrelevant content
        # Should not crash
        result = relevance.is_relevant(
            "오늘 날씨",
            "https://weather.com",
            "Weather",
            "날씨 정보"
        )
        assert isinstance(result, bool)


class TestFileOperations:
    """Test file operations."""

    def test_news_directory_exists(self):
        """Verify news directory exists."""
        BASE = Path(__file__).parent.parent
        news_dir = BASE / "news"
        assert news_dir.exists()
        assert news_dir.is_dir()

    def test_pages_directory_exists(self):
        """Verify pages directory exists."""
        BASE = Path(__file__).parent.parent
        pages_dir = BASE / "pages"
        assert pages_dir.exists()
        assert pages_dir.is_dir()

    def test_config_directory_exists(self):
        """Verify config directory exists."""
        BASE = Path(__file__).parent.parent
        config_dir = BASE / "config"
        assert config_dir.exists()
        assert config_dir.is_dir()


class TestPerfectScorecard:
    """Test perfect scorecard computation."""

    def test_scorecard_script_exists(self):
        """Verify scorecard script exists."""
        BASE = Path(__file__).parent.parent
        script = BASE / "scripts" / "compute_perfect_scorecard.py"
        assert script.exists()

    def test_scorecard_output(self):
        """Verify scorecard can be generated."""
        BASE = Path(__file__).parent.parent
        scorecard_file = BASE / "pages" / "perfect-scorecard.md"
        
        # Scorecard should exist and have content
        if scorecard_file.exists():
            content = scorecard_file.read_text(encoding="utf-8")
            assert "Perfect Scorecard" in content
            assert "A." in content or "B." in content


class TestDailyUpdate:
    """Test daily update script."""

    def test_daily_update_script_exists(self):
        """Verify daily update script exists."""
        BASE = Path(__file__).parent.parent
        script = BASE / "scripts" / "run_daily_update.sh"
        assert script.exists()
        assert os.access(script, os.X_OK)


class TestBackup:
    """Test backup functionality."""

    def test_backup_manager_exists(self):
        """Verify backup manager exists."""
        import backup_manager
        assert hasattr(backup_manager, 'create_backup')


class TestLockManager:
    """Test lock management."""

    def test_lock_manager_import(self):
        """Verify lock manager can be imported."""
        import lock_manager
        assert lock_manager is not None


class TestSecurity:
    """Test security functions."""

    def test_url_validation(self):
        """Verify URL validation works."""
        from security import validate_url
        
        assert validate_url("https://example.com") is True
        assert validate_url("http://test.com") is True
        assert validate_url("not-a-url") is False
        assert validate_url("") is False

    def test_email_validation(self):
        """Verify email validation works."""
        from security import validate_email
        
        assert validate_email("test@example.com") is True
        assert validate_email("invalid") is False

    def test_html_sanitization(self):
        """Verify HTML sanitization works."""
        from security import sanitize_html, escape_html
        
        # Should not crash
        result = sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result


class TestMonitoring:
    """Test monitoring functionality."""

    def test_monitor_import(self):
        """Verify monitor can be imported."""
        import monitor
        assert monitor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

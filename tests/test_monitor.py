#!/usr/bin/env python3
"""Tests for monitor.py - Monitoring System"""
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from monitor import AlertLevel, MonitoringSystem, SystemMetric  # noqa: E402


class TestSystemMetric:
    """Test SystemMetric dataclass"""

    def test_system_metric_creation(self):
        """Test SystemMetric can be created with valid data"""
        timestamp = datetime.now()
        metric = SystemMetric(
            cpu_percent=50.0,
            memory_percent=70.0,
            disk_usage_gb=100.0,
            active_processes=5,
            timestamp=timestamp
        )
        assert metric.cpu_percent == 50.0
        assert metric.memory_percent == 70.0
        assert metric.disk_usage_gb == 100.0
        assert metric.active_processes == 5
        assert metric.timestamp == timestamp

    def test_system_metric_mutable(self):
        """Test SystemMetric is mutable (not frozen)"""
        timestamp = datetime.now()
        metric = SystemMetric(
            cpu_percent=50.0,
            memory_percent=70.0,
            disk_usage_gb=100.0,
            active_processes=5,
            timestamp=timestamp
        )
        # Verify values
        assert metric.cpu_percent == 50.0
        metric.cpu_percent = 60.0
        assert metric.cpu_percent == 60.0


class TestAlertLevel:
    """Test AlertLevel constants"""

    def test_alert_level_constants(self):
        """Test AlertLevel has correct values"""
        assert AlertLevel.CRITICAL == "critical"
        assert AlertLevel.WARNING == "warning"
        assert AlertLevel.INFO == "info"


class TestMonitoringSystem:
    """Test MonitoringSystem class"""

    @patch('monitor.psutil')
    def test_collect_system_metrics(self, mock_psutil):
        """Test system metrics collection"""
        # Mock psutil
        mock_cpu = Mock()
        mock_cpu.percent = 50.0
        mock_psutil.cpu_percent.return_value = 50.0

        mock_memory = Mock()
        mock_memory.percent = 70.0
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.used = 100 * (1024**3)
        mock_disk.free = 900 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        mock_process = Mock()
        mock_process.info = {'cmdline': ['python3', 'auto_collect_news.py']}
        mock_psutil.process_iter.return_value = [mock_process]

        # Create monitoring system
        monitor = MonitoringSystem()

        # Collect metrics
        with patch('monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            metric = monitor.collect_system_metrics()

        assert metric.cpu_percent == 50.0
        assert metric.memory_percent == 70.0

    def test_monitoring_system_init(self):
        """Test MonitoringSystem initialization"""
        monitor = MonitoringSystem()
        assert monitor.config_file == "config.yaml"
        assert monitor.metrics_history == []
        assert monitor.running is False

    @patch('monitor.psutil')
    def test_check_disk_space_healthy(self, mock_psutil):
        """Test disk space check with healthy status"""
        mock_disk = Mock()
        mock_disk.free = 300 * (1024**3)
        mock_disk.total = 500 * (1024**3)
        mock_disk.used = 200 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        monitor = MonitoringSystem()
        result = monitor._check_disk_space()

        assert result['status'] == 'ok'
        assert result['free_percent'] > 20

    @patch('monitor.psutil')
    def test_check_disk_space_warning(self, mock_psutil):
        """Test disk space check with warning status"""
        mock_disk = Mock()
        mock_disk.free = 80 * (1024**3)
        mock_disk.total = 500 * (1024**3)
        mock_disk.used = 420 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        monitor = MonitoringSystem()
        result = monitor._check_disk_space()

        assert result['status'] == 'warning'

    @patch('monitor.psutil')
    def test_check_disk_space_critical(self, mock_psutil):
        """Test disk space check with critical status"""
        mock_disk = Mock()
        mock_disk.free = 40 * (1024**3)
        mock_disk.total = 500 * (1024**3)
        mock_disk.used = 460 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        monitor = MonitoringSystem()
        result = monitor._check_disk_space()

        assert result['status'] == 'critical'

    def test_check_git_status_clean(self):
        """Test git status check with clean working tree"""
        monitor = MonitoringSystem()

        with patch('monitor.subprocess.run') as mock_run:
            # First call to git rev-parse
            mock_result1 = Mock()
            mock_result1.returncode = 0

            # Second call to git status
            mock_result2 = Mock()
            mock_result2.returncode = 0
            mock_result2.stdout = ""
            mock_run.side_effect = [mock_result1, mock_result2]

            result = monitor._check_git_status()

        assert result['status'] == 'ok'

    def test_check_git_status_dirty(self):
        """Test git status check with dirty working tree"""
        monitor = MonitoringSystem()

        with patch('monitor.subprocess.run') as mock_run:
            # First call to git rev-parse
            mock_result1 = Mock()
            mock_result1.returncode = 0

            # Second call to git status
            mock_result2 = Mock()
            mock_result2.returncode = 0
            mock_result2.stdout = "M modified.txt"
            mock_run.side_effect = [mock_result1, mock_result2]

            result = monitor._check_git_status()

        assert result['status'] == 'dirty'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

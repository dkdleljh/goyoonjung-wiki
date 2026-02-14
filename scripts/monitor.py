#!/usr/bin/env python3
"""
Real-time Monitoring System for goyoonjung-wiki automation
Implements health checks, Discord notifications, and auto-recovery
"""

import json
import logging
import queue
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psutil
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SystemMetric:
    """System metric data structure"""
    cpu_percent: float
    memory_percent: float
    disk_usage_gb: float
    active_processes: int
    timestamp: datetime

@dataclass
class AlertLevel:
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class MonitoringSystem:
    """Real-time monitoring and alerting system"""

    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.metrics_history = []
        self.alerts_queue = queue.Queue()
        self.running = False
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(self.config_file) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}

    def collect_system_metrics(self) -> SystemMetric:
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Count active automation processes
        active_processes = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'goyoonjung-wiki' in cmdline or 'auto_collect' in cmdline:
                    active_processes += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return SystemMetric(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_gb=disk.used / (1024**3),
            active_processes=active_processes,
            timestamp=datetime.now()
        )

    def check_automation_health(self) -> dict:
        """Check health of automation components"""
        health_status = {
            "git_status": self._check_git_status(),
            "lock_status": self._check_lock_status(),
            "backup_status": self._check_backup_status(),
            "log_status": self._check_log_status(),
            "disk_space": self._check_disk_space(),
            "process_status": self._check_process_status()
        }

        return health_status

    def _check_git_status(self) -> dict:
        """Check Git repository status"""
        try:
            # Check if we're in a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                               capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return {"status": "not_repo", "message": "Not a Git repository"}

            # Check working tree status
            result = subprocess.run(['git', 'status', '--porcelain'],
                               capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                changed_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                return {
                    "status": "ok" if changed_files == 0 else "dirty",
                    "changed_files": changed_files,
                    "message": f"{'Clean' if changed_files == 0 else f'{changed_files} files changed'}"
                }
            else:
                return {"status": "error", "message": "Git status check failed"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_lock_status(self) -> dict:
        """Check lock file status"""
        locks_dir = Path(".locks")
        if not locks_dir.exists():
            return {"status": "ok", "message": "No locks directory"}

        lock_count = len([d for d in locks_dir.iterdir() if d.is_dir()])
        return {
            "status": "ok" if lock_count <= 3 else "warning",
            "lock_count": lock_count,
            "message": f"{lock_count} active locks"
        }

    def _check_backup_status(self) -> dict:
        """Check backup system status"""
        backups_dir = Path("backups")
        if not backups_dir.exists():
            return {"status": "warning", "message": "No backups directory"}

        backup_files = list(backups_dir.glob("*.tar.gz"))
        total_size = sum(f.stat().st_size for f in backup_files) / (1024**3)

        # Check if recent backup exists
        recent_backup = None
        if backup_files:
            recent_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            age_hours = (time.time() - recent_backup.stat().st_mtime) / 3600

        return {
            "status": "ok" if recent_backup and age_hours < 48 else "warning",
            "backup_count": len(backup_files),
            "total_size_gb": total_size,
            "latest_backup_hours": age_hours if recent_backup else None,
            "message": f"{len(backup_files)} backups, {total_size:.1f}GB total"
        }

    def _check_log_status(self) -> dict:
        """Check log file status"""
        news_dir = Path("news")
        if not news_dir.exists():
            return {"status": "warning", "message": "No news directory"}

        today = datetime.now().strftime("%Y-%m-%d")
        today_log = news_dir / f"{today}.md"

        if today_log.exists():
            # Check log size and last modified
            stat = today_log.stat()
            size_kb = stat.st_size / 1024
            age_hours = (time.time() - stat.st_mtime) / 3600

            return {
                "status": "ok",
                "today_log_exists": True,
                "log_size_kb": size_kb,
                "age_hours": age_hours,
                "message": f"Today's log: {size_kb:.1f}KB"
            }
        else:
            return {
                "status": "warning",
                "today_log_exists": False,
                "message": "No log file for today"
            }

    def _check_disk_space(self) -> dict:
        """Check disk space availability"""
        disk = psutil.disk_usage('/')
        free_percent = (disk.free / disk.total) * 100
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)

        status = "ok" if free_percent > 20 else "critical" if free_percent < 10 else "warning"

        return {
            "status": status,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "free_percent": free_percent,
            "message": f"{free_percent:.1f}% free ({free_gb:.1f}GB)"
        }

    def _check_process_status(self) -> dict:
        """Check automation process status"""
        automation_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline for keyword in ['auto_collect', 'run_daily_update', 'backup_manager']):
                    automation_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": cmdline[:100],  # Truncate for display
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        status = "ok" if len(automation_processes) <= 5 else "warning"

        return {
            "status": status,
            "process_count": len(automation_processes),
            "processes": automation_processes,
            "message": f"{len(automation_processes)} automation processes running"
        }

    def send_discord_notification(self, level: str, message: str, details: dict = None):
        """Send notification to Discord webhook"""
        webhook_url = self.config.get('discord_webhook_url')
        if not webhook_url:
            logger.debug("No Discord webhook configured")
            return

        color = {
            "critical": 0xFF0000,  # Red
            "warning": 0xFFAA00,    # Orange
            "info": 0x00AA00        # Green
        }.get(level, 0x808080)  # Gray default

        embed = {
            "title": f"goyoonjung-wiki {level.upper()}",
            "description": message,
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Automation Monitor"}
        }

        if details:
            field_value = "\n".join([f"**{k}**: {v}" for k, v in details.items()])
            embed["fields"] = [{"name": "Details", "value": field_value}]

        payload = {"embeds": [embed]}

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 204:
                logger.info(f"Discord notification sent: {level}")
            else:
                logger.warning(f"Discord notification failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    def auto_recovery(self, health_status: dict):
        """Attempt automatic recovery for common issues"""
        recovery_actions = []

        # Recovery for stale locks
        if health_status["lock_status"]["status"] == "warning":
            try:
                result = subprocess.run(['python3', 'scripts/lock_manager.py', '--cleanup'],
                                   capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    recovery_actions.append("Cleaned stale locks")
            except Exception as e:
                logger.error(f"Lock cleanup failed: {e}")

        # Recovery for disk space
        if health_status["disk_space"]["status"] == "critical":
            try:
                result = subprocess.run(['python3', 'scripts/backup_manager.py', '--cleanup'],
                                   capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    recovery_actions.append("Cleaned old backups")
            except Exception as e:
                logger.error(f"Backup cleanup failed: {e}")

        # Recovery for hanging processes
        if health_status["process_status"]["process_count"] > 10:
            try:
                # Kill processes running longer than 2 hours
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'auto_collect' in cmdline:
                            age_hours = (time.time() - proc.info['create_time']) / 3600
                            if age_hours > 2:
                                proc.terminate()
                                recovery_actions.append(f"Terminated hanging process PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except Exception as e:
                logger.error(f"Process cleanup failed: {e}")

        return recovery_actions

    def start_monitoring(self, interval: int = 300):
        """Start continuous monitoring"""
        self.running = True
        logger.info(f"Starting monitoring with {interval}s interval")

        while self.running:
            try:
                # Collect metrics
                metrics = self.collect_system_metrics()
                self.metrics_history.append(metrics)

                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)

                # Check health
                health_status = self.check_automation_health()

                # Check for alerts
                alerts = self._analyze_for_alerts(metrics, health_status)

                # Send notifications for alerts
                for alert in alerts:
                    self.send_discord_notification(alert["level"], alert["message"], alert.get("details"))

                # Attempt auto-recovery
                recovery_actions = self.auto_recovery(health_status)
                if recovery_actions:
                    self.send_discord_notification("info", "Auto-recovery actions performed",
                                              {"actions": ", ".join(recovery_actions)})

                # Sleep until next check
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait before retry

    def _analyze_for_alerts(self, metrics: SystemMetric, health_status: dict) -> list[dict]:
        """Analyze metrics and health for alert conditions"""
        alerts = []

        # CPU alerts
        if metrics.cpu_percent > 90:
            alerts.append({
                "level": "critical",
                "message": f"High CPU usage: {metrics.cpu_percent:.1f}%",
                "details": {"cpu_percent": metrics.cpu_percent}
            })
        elif metrics.cpu_percent > 70:
            alerts.append({
                "level": "warning",
                "message": f"Elevated CPU usage: {metrics.cpu_percent:.1f}%",
                "details": {"cpu_percent": metrics.cpu_percent}
            })

        # Memory alerts
        if metrics.memory_percent > 90:
            alerts.append({
                "level": "critical",
                "message": f"High memory usage: {metrics.memory_percent:.1f}%",
                "details": {"memory_percent": metrics.memory_percent}
            })

        # Disk space alerts
        if health_status["disk_space"]["status"] == "critical":
            alerts.append({
                "level": "critical",
                "message": f"Critical disk space: {health_status['disk_space']['free_percent']:.1f}% free",
                "details": health_status["disk_space"]
            })

        # Process alerts
        if metrics.active_processes > 10:
            alerts.append({
                "level": "warning",
                "message": f"Many automation processes: {metrics.active_processes}",
                "details": {"active_processes": metrics.active_processes}
            })

        # Git status alerts
        if health_status["git_status"]["status"] == "dirty":
            alerts.append({
                "level": "warning",
                "message": f"Git working tree not clean: {health_status['git_status']['changed_files']} files changed",
                "details": health_status["git_status"]
            })

        return alerts

    def get_status_dashboard(self) -> dict:
        """Get comprehensive status dashboard"""
        current_metrics = self.collect_system_metrics()
        health_status = self.check_automation_health()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "cpu_percent": current_metrics.cpu_percent,
                "memory_percent": current_metrics.memory_percent,
                "disk_usage_gb": current_metrics.disk_usage_gb,
                "active_processes": current_metrics.active_processes
            },
            "health_status": health_status,
            "metrics_history_count": len(self.metrics_history)
        }

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Monitoring System')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--status', action='store_true', help='Show current status dashboard')
    parser.add_argument('--health', action='store_true', help='Run health check')
    parser.add_argument('--interval', type=int, default=300, help='Monitoring interval in seconds')

    args = parser.parse_args()

    monitor = MonitoringSystem()

    if args.monitor:
        try:
            monitor.start_monitoring(args.interval)
        except KeyboardInterrupt:
            monitor.stop_monitoring()

    elif args.status:
        dashboard = monitor.get_status_dashboard()
        print(json.dumps(dashboard, indent=2))

    elif args.health:
        health = monitor.check_automation_health()
        print("Health Check Results:")
        for component, status in health.items():
            print(f"  {component}: {status['status']} - {status['message']}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

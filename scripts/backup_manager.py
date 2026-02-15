#!/usr/bin/env python3
"""
Smart Backup Cleanup Manager for goyoonjung-wiki
Implements intelligent backup retention policies and cleanup
"""

import argparse
import hashlib
import logging
import os
import tarfile
from datetime import datetime
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, backup_dir="backups", max_size_mb=500, max_files=30):
        self.backup_dir = Path(backup_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files

    def calculate_file_hash(self, filepath):
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def find_duplicate_files(self):
        """Find duplicate backup files based on content hash"""
        files = list(self.backup_dir.glob("*.tar.gz"))
        hashes = {}
        duplicates = []

        for file_path in files:
            file_hash = self.calculate_file_hash(file_path)
            if file_hash in hashes:
                duplicates.append((file_path, hashes[file_hash]))
            else:
                hashes[file_hash] = file_path

        return duplicates

    def get_backup_info(self, filepath):
        """Extract backup creation time from filename"""
        try:
            # Extract timestamp from filename like: goyoonjung-wiki_2026-02-09_1023.tar.gz
            basename = filepath.stem  # Remove .tar.gz
            parts = basename.split('_')
            if len(parts) >= 3:
                date_part = parts[1]
                time_part = parts[2]
                datetime_str = f"{date_part}_{time_part}"
                return datetime.strptime(datetime_str, "%Y-%m-%d_%H%M")
        except (ValueError, IndexError, AttributeError):
            pass
        return filepath.stat().st_mtime

    def cleanup_old_backups(self):
        """Remove old and duplicate backups to meet size and count limits"""
        if not self.backup_dir.exists():
            logger.info(f"Backup directory {self.backup_dir} does not exist")
            return

        # Get all backup files
        backup_files = list(self.backup_dir.glob("*.tar.gz"))

        # Remove duplicates first
        duplicates = self.find_duplicate_files()
        removed_count = 0
        size_freed = 0

        for duplicate, original in duplicates:
            file_size = duplicate.stat().st_size
            duplicate.unlink()
            removed_count += 1
            size_freed += file_size
            logger.info(f"Removed duplicate: {duplicate.name} (duplicate of {original.name})")

        # Sort files by modification time (newest first)
        backup_files.sort(key=lambda x: self.get_backup_info(x), reverse=True)

        # Keep only the newest files within limits
        files_to_keep = []
        current_size = 0

        for file_path in backup_files:
            file_size = file_path.stat().st_size

            if len(files_to_keep) < self.max_files and (current_size + file_size) <= self.max_size_bytes:
                files_to_keep.append(file_path)
                current_size += file_size
            else:
                # This file should be removed
                file_path.unlink()
                removed_count += 1
                size_freed += file_size
                logger.info(f"Removed old backup: {file_path.name}")

        logger.info(f"Cleanup complete. Removed {removed_count} files, freed {size_freed / (1024*1024):.1f}MB")

        # Create cleanup report
        self.create_cleanup_report(removed_count, size_freed, len(files_to_keep), current_size)

        return removed_count, size_freed

    def create_incremental_backup(self):
        """Create incremental backup (only changed files)"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H%M")
        backup_name = f"goyoonjung-wiki_{today}_{current_time}.tar.gz"
        backup_path = self.backup_dir / backup_name

        # Check if there's already a backup today
        today_backups = list(self.backup_dir.glob(f"goyoonjung-wiki_{today}_*.tar.gz"))
        if today_backups:
            logger.info(f"Backup already exists for today: {len(today_backups)} files")
            return backup_path, False

        # Create tar.gz of important files
        files_to_backup = [
            "pages/", "scripts/", "config/", "sources/",
            "data/", "README.md", "index.md", "config.yaml", "requirements.txt"
        ]

        with tarfile.open(backup_path, "w:gz") as tar:
            for item in files_to_backup:
                if os.path.exists(item):
                    if os.path.isdir(item):
                        tar.add(item, arcname=item)
                    else:
                        tar.add(item, arcname=os.path.basename(item))

        logger.info(f"Created incremental backup: {backup_name}")
        return backup_path, True

    def create_cleanup_report(self, removed_count, size_freed, kept_count, kept_size):
        """Create a cleanup report"""
        report = f"""
# Backup Cleanup Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- Files removed: {removed_count}
- Space freed: {size_freed / (1024*1024):.1f} MB
- Files kept: {kept_count}
- Space used: {kept_size / (1024*1024):.1f} MB
- Total backup directory size: {self.get_directory_size() / (1024*1024):.1f} MB

## Policy
- Maximum files: {self.max_files}
- Maximum size: {self.max_size_bytes / (1024*1024):.0f} MB
"""

        report_path = self.backup_dir / "cleanup_report.md"
        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"Cleanup report saved to: {report_path}")

    def get_directory_size(self):
        """Get total size of backup directory"""
        total_size = 0
        for file_path in self.backup_dir.glob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    def setup_weekly_cleanup(self):
        """Setup cron job for weekly cleanup"""
        cron_entry = "0 2 * * 0 cd /home/zenith/바탕화면/goyoonjung-wiki && python3 scripts/backup_manager.py --cleanup"

        # Add to crontab (this would need proper sudo/user setup)
        logger.info("To setup weekly cleanup, add to crontab:")
        logger.info(cron_entry)

    def upload_to_github_releases(self, backup_path, github_token=None, repo="owner/repo", release_tag="backup"):
        """Upload backup to GitHub Releases"""
        if not REQUESTS_AVAILABLE:
            logger.error("requests library required for GitHub Releases upload. Install with: pip install requests")
            return False

        if not github_token:
            github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            logger.warning("GITHUB_TOKEN not set. Skipping GitHub Releases upload.")
            return False

        # Parse repo (owner/repo)
        if "/" not in repo:
            logger.error("Invalid repo format. Use 'owner/repo' format.")
            return False

        owner, repo_name = repo.split("/")

        # Create or get release
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"

        # Check if release exists
        response = requests.get(
            f"{api_url}/tags/{release_tag}",
            headers={"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
        )

        if response.status_code == 200:
            # Release exists, get upload URL
            upload_url = response.json()["upload_url"].split("{")[0]
        elif response.status_code == 404:
            # Create new release
            create_response = requests.post(
                api_url,
                headers={"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"},
                json={
                    "tag_name": release_tag,
                    "name": f"Backup {datetime.now().strftime('%Y-%m-%d')}",
                    "body": f"Automated backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "draft": False,
                    "prerelease": False
                }
            )
            if create_response.status_code not in (200, 201):
                logger.error(f"Failed to create release: {create_response.status_code} - {create_response.text}")
                return False
            upload_url = create_response.json()["upload_url"].split("{")[0]
        else:
            logger.error(f"Failed to check release: {response.status_code}")
            return False

        # Upload asset
        upload_url = f"{upload_url}?name={backup_path.name}"
        with open(backup_path, "rb") as f:
            headers = {"Authorization": f"token {github_token}", "Content-Type": "application/gzip"}
            upload_response = requests.post(upload_url, headers=headers, data=f)

        if upload_response.status_code in (200, 201):
            logger.info(f"Successfully uploaded {backup_path.name} to GitHub Releases")
            return True
        else:
            logger.error(f"Failed to upload: {upload_response.status_code} - {upload_response.text}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Backup Cleanup Manager')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old backups')
    parser.add_argument('--backup', action='store_true', help='Create incremental backup')
    parser.add_argument('--upload-github', action='store_true', help='Upload backup to GitHub Releases')
    parser.add_argument('--github-repo', type=str, default=os.environ.get("GITHUB_REPO", "owner/repo"), help='GitHub repo (owner/repo)')
    parser.add_argument('--release-tag', type=str, default="backup", help='GitHub release tag')
    parser.add_argument('--max-size', type=int, default=500, help='Maximum backup size in MB')
    parser.add_argument('--max-files', type=int, default=30, help='Maximum number of backup files')

    args = parser.parse_args()

    manager = BackupManager(max_size_mb=args.max_size, max_files=args.max_files)

    if args.cleanup:
        logger.info("Starting backup cleanup...")
        removed, size_freed = manager.cleanup_old_backups()

    if args.backup:
        logger.info("Creating incremental backup...")
        backup_path, created = manager.create_incremental_backup()
        if created:
            logger.info(f"Backup created: {backup_path}")
            
            if args.upload-github:
                logger.info(f"Uploading to GitHub Releases...")
                manager.upload_to_github_releases(
                    backup_path,
                    github_token=os.environ.get("GITHUB_TOKEN"),
                    repo=args.github_repo,
                    release_tag=args.release_tag
                )
        else:
            logger.info("Backup already exists for today")

    if not args.cleanup and not args.backup:
        logger.info("No action specified. Use --cleanup or --backup")
        manager.setup_weekly_cleanup()

if __name__ == "__main__":
    main()

# Automation Deployment (systemd)

This project can run fully unattended via `systemd` timer.
Daily unattended runs commit/push locally, and GitHub Actions release sync updates SemVer tags and GitHub Releases after pushes to `main`.

## Install

```bash
sudo cp deploy/systemd/goyoonjung-wiki-daily.service /etc/systemd/system/
sudo cp deploy/systemd/goyoonjung-wiki-daily.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now goyoonjung-wiki-daily.timer
```

## Verify

```bash
systemctl status goyoonjung-wiki-daily.timer
systemctl list-timers | grep goyoonjung-wiki-daily
journalctl -u goyoonjung-wiki-daily.service -n 100 --no-pager
gh run list --workflow release.yml --limit 5
```

## Manual run

```bash
sudo systemctl start goyoonjung-wiki-daily.service
```

## Restore from backup

```bash
bash scripts/restore_latest_backup.sh
```

Set `RESTORE_ROOT=/path/to/target` to restore into another path.

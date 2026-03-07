# Automation Deployment (systemd)

This project can run fully unattended via `systemd` timer.

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

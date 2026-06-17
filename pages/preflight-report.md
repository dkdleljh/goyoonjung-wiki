# Automation Preflight Report (auto)

> Updated: 2026-06-17 09:10 (Asia/Seoul)

## Summary
- status: OK

## Checks
| check | state | detail |
|---|---|---|
| .venv/bin/python | OK | present |
| .venv/bin/ruff | OK | present |
| .venv/bin/bandit | OK | present |
| .venv/bin/pytest | OK | present |
| git remote origin | OK | git@github.com:dkdleljh/goyoonjung-wiki.git |
| git fetch origin main | OK | reachable |
| HEAD == origin/main | OK | synced |
| working tree | WARN | dirty |
| Discord webhook | OK | configured |
| disk free | OK | 271891 MiB |
| run lock | WARN | present |
| goyoonjung-wiki-daily.timer | WARN | no next run |
| goyoonjung-wiki-sync.timer | WARN | no next run |
| goyoonjung-wiki-linkhealth.timer | OK | next run scheduled |
| goyoonjung-wiki-notifyflush.timer | OK | next run scheduled |
| goyoonjung-wiki-backupcleanup.timer | OK | next run scheduled |
| goyoonjung-wiki-watchdog.timer | OK | next run scheduled |

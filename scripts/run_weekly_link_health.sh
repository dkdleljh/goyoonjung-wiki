#!/usr/bin/env bash
set -euo pipefail

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

git checkout main >/dev/null 2>&1 || true

python3 scripts/check_links.py >/dev/null

git add -A pages/link-health.md >/dev/null 2>&1 || true
if git diff --cached --quiet; then
  echo "No link-health changes."
  exit 0
fi

TODAY=$(TZ='Asia/Seoul' date +"%Y-%m-%d")
git commit -m "chore: link health ${TODAY}" >/dev/null

git push origin main >/dev/null

echo "OK"

#!/usr/bin/env bash
set -euo pipefail
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$BASE"

# Print changed files between last two commits (if possible)
if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
  echo "## Git 변경 파일(직전 커밋 대비)"
  git diff --name-only HEAD~1..HEAD | sed 's/^/- /'
else
  echo "## Git 변경 파일"
  echo "- (이전 커밋이 없어 diff를 만들 수 없습니다.)"
fi

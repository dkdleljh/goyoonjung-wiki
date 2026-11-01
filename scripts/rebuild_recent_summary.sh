#!/usr/bin/env bash
set -euo pipefail
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
NEWS="$BASE/news"
OUT="$NEWS/README.md"

# Find last 7 news files by name (YYYY-MM-DD.md), descending
{
  echo "# news/"
  echo
  echo "날짜별 자동 업데이트 로그입니다. 파일명은 \`YYYY-MM-DD.md\`."
  echo
  echo "## 최근 7일 요약"

  python3 - "$NEWS" <<'PY'
import re
import sys
from pathlib import Path

files = sorted((p for p in Path(sys.argv[1]).glob('*.md')
                if re.fullmatch(r'\d{4}-\d{2}-\d{2}\.md', p.name)), reverse=True)[:7]
for path in files:
    print(f'- [{path.stem}]({path.name})')
if not files:
    print('- (아직 로그가 없습니다.)')
PY
} > "$OUT"

echo "$OUT"

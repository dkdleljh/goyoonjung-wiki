#!/usr/bin/env bash
set -euo pipefail

# Usage: add_seen_url.sh <url>

BASE="/home/zenith/바탕화면/goyoonjung-wiki"
SEEN="$BASE/sources/seen-urls.txt"
URL="${1:-}"

if [ -z "$URL" ]; then
  echo "ERR: missing url" >&2
  exit 2
fi

mkdir -p "$(dirname "$SEEN")"
touch "$SEEN"

NORM=$(python3 "$BASE/scripts/normalize_url.py" "$URL" | head -n 1)

# store normalized url
if ! grep -Fqx "$NORM" "$SEEN"; then
  echo "$NORM" >> "$SEEN"
fi

echo "$NORM"

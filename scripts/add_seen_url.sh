#!/usr/bin/env bash
set -euo pipefail

# Usage: add_seen_url.sh <url>

BASE="/Users/zenith/Documents/goyoonjung-wiki"
SEEN="$BASE/sources/seen-urls.txt"
SEEN_JSONL="$BASE/sources/seen-urls.jsonl"
URL="${1:-}"

if [ -z "$URL" ]; then
  echo "ERR: missing url" >&2
  exit 2
fi

mkdir -p "$(dirname "$SEEN")"
touch "$SEEN"
touch "$SEEN_JSONL"

NORM=$(python3 "$BASE/scripts/normalize_url.py" "$URL" | head -n 1)

# store normalized url (txt)
if ! grep -Fqx "$NORM" "$SEEN"; then
  echo "$NORM" >> "$SEEN"
fi

# store normalized url (jsonl)
# schema: {"norm":"...","added":"YYYY-MM-DD HH:MM","id":"sha1:<hash>"}
ID=$(printf '%s' "$NORM" | sha1sum | awk '{print $1}')
ADDED=$(TZ='Asia/Seoul' date +"%Y-%m-%d %H:%M")
if ! grep -Fq "\"id\":\"sha1:${ID}\"" "$SEEN_JSONL"; then
  printf '{"norm":"%s","added":"%s","id":"sha1:%s"}\n' "$NORM" "$ADDED" "$ID" >> "$SEEN_JSONL"
fi

echo "$NORM"

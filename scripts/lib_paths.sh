#!/usr/bin/env bash
set -euo pipefail

resolve_wiki_base() {
  if [ -n "${GOYOONJUNG_WIKI_BASE:-}" ] && [ -d "${GOYOONJUNG_WIKI_BASE}" ]; then
    printf '%s\n' "$GOYOONJUNG_WIKI_BASE"
    return 0
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  printf '%s\n' "$(cd "$script_dir/.." && pwd)"
}


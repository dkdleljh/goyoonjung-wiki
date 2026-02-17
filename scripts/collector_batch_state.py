#!/usr/bin/env python3
"""Small helper to provide round-robin batch offsets for collectors.

We keep state in .cache/collector_state.json to avoid hammering many sources
in a single run (prevents timeouts/SIGKILL) while still covering the full list
across multiple days.

Usage:
  python3 scripts/collector_batch_state.py get <key> <mod>

Example:
  python3 scripts/collector_batch_state.py get gnews_sites 40

This prints a single integer offset.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
STATE_DIR = BASE / ".cache"
STATE_PATH = STATE_DIR / "collector_state.json"


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_and_bump(key: str, mod: int) -> int:
    state = load_state()
    cur = int(state.get(key, 0) or 0)
    if mod <= 0:
        return 0
    nxt = (cur + 1) % mod
    state[key] = nxt
    save_state(state)
    return cur


def main(argv: list[str]) -> int:
    if len(argv) != 4 or argv[1] != "get":
        print("usage: collector_batch_state.py get <key> <mod>", file=sys.stderr)
        return 2
    key = argv[2]
    mod = int(argv[3])
    off = get_and_bump(key, mod)
    print(off)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

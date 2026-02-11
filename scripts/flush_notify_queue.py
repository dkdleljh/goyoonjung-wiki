#!/usr/bin/env python3
"""Flush queued Discord notifications.

If notify_status.py fails to deliver (network/webhook issues), it writes a JSONL queue
under .locks/notify-queue.jsonl. This script retries sending queued items.

Safe:
- Best-effort; never raises fatal errors
- Keeps items in queue on failure
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
QUEUE = BASE / ".locks" / "notify-queue.jsonl"


def load_queue() -> list[dict[str, Any]]:
    if not QUEUE.exists():
        return []
    out = []
    for raw in QUEUE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append(json.loads(raw))
        except Exception:
            continue
    return out


def write_queue(items: list[dict[str, Any]]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    if not items:
        if QUEUE.exists():
            QUEUE.unlink()
        return
    QUEUE.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in items) + "\n", encoding="utf-8")


def main() -> int:
    items = load_queue()
    if not items:
        print("flush_notify_queue: empty")
        return 0

    # Import send function from notify_status.py
    import sys
    sys.path.append(str((BASE / "scripts").resolve()))
    import notify_status  # type: ignore

    remaining = []
    sent = 0
    for it in items:
        try:
            ok = notify_status.send_discord_message(
                it.get("title", "(no title)"),
                it.get("message", ""),
                it.get("color", "yellow"),
                force=True,
            )
            if ok:
                sent += 1
            else:
                remaining.append(it)
        except Exception:
            remaining.append(it)

    write_queue(remaining)
    print(f"flush_notify_queue: sent={sent} remaining={len(remaining)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

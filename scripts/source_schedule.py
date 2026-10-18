"""Durable per-source checkpoints; failures never advance coverage watermarks."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from source_transport import atomic_write

STATE = Path(__file__).resolve().parents[1] / 'data/reports/source-checkpoints.json'


def load() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def search_window(key: str, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    last = load().get(key, {}).get('last_success')
    try:
        since = min(datetime.fromisoformat(last), now) - timedelta(days=2)
    except (ValueError, TypeError):
        since = now - timedelta(days=30)
    return f'after:{since:%Y-%m-%d}'


def record(key: str, success: bool) -> None:
    state = load()
    old = state.get(key, {})
    now = datetime.now(UTC).isoformat()
    state[key] = {**old, 'last_attempt': now, 'status': 'success' if success else 'failed',
                  'failures': 0 if success else old.get('failures', 0) + 1}
    if success:
        state[key]['last_success'] = now
    atomic_write(STATE, json.dumps(state, ensure_ascii=False, indent=2) + '\n')


def select(items: list, key, limit: int) -> list:
    state = load()
    # Fair retries: oldest attempt first; failed sources retain their old coverage watermark.
    return sorted(items, key=lambda item: state.get(key(item), {}).get('last_attempt', ''))[:limit or len(items)]

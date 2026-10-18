"""Explicit lifecycle policy for the agency profile source."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config/agency-sources.json'


def load_config(path: Path | None = None) -> dict:
    config = json.loads((path or CONFIG_PATH).read_text(encoding='utf-8'))
    state = config.get('lifecycle', 'active')
    if state not in ('active', 'retired'):
        raise ValueError(f'Unknown agency source lifecycle: {state}')
    if not config.get('name') or not config.get('urls'):
        raise ValueError('Agency source name and URLs are required')
    if state == 'retired':
        if not config.get('reason') or not config.get('evidence'):
            raise ValueError('Retirement requires a reason and evidence')
        date.fromisoformat(config['retired_at'])
    return config

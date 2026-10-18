"""Pytest configuration.

This project keeps application code under the `scripts/` package.
In CI and local runs, `pytest` may be invoked without PYTHONPATH set.
Ensure the repository root is importable so `import scripts.*` works.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Collectors imported under either name must never write production cursors in tests.
import importlib
import pytest

if str(REPO_ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / 'scripts'))


@pytest.fixture(autouse=True)
def isolated_source_checkpoints(tmp_path, monkeypatch):
    for name in ('source_schedule', 'scripts.source_schedule'):
        monkeypatch.setattr(importlib.import_module(name), 'STATE', tmp_path / 'source-checkpoints.json')

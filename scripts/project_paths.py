#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


def wiki_base() -> Path:
    override = os.environ.get("GOYOONJUNG_WIKI_BASE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    # The project is self-contained; deployment depth (/app or ~/wiki) is irrelevant.
    return wiki_base()


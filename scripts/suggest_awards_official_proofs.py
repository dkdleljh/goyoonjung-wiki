#!/usr/bin/env python3
"""Suggest award official proof links (placeholder).

This repo previously had a suggest step; the automated apply step is
scripts/promote_awards_official_proofs.py.

To keep the unmanned pipeline stable, this script is a lightweight no-op that
can be expanded later.
"""

from __future__ import annotations


def main() -> int:
    print("suggest_awards_official_proofs: SKIP (not implemented; use promote_awards_official_proofs.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Remove legacy manual TOC blocks when an auto TOC marker exists.

Currently targets README.md only.
Removes the first occurrence of:
  "## 목차" section up to the next "---" separator line.

This avoids duplicated TOC (auto + manual).
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
README = BASE / "README.md"

TOC_START = "<!-- TOC:START -->"


def main() -> None:
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8", errors="ignore")
    if TOC_START not in text:
        return

    # Remove legacy TOC section (best-effort): the one that appears AFTER Quick Links.
    # Keep the auto-generated TOC block between TOC markers.
    new = re.sub(
        r"(## ⚡ Quick Links[\s\S]*?\n---\n)\n## 목차\n\n[\s\S]*?\n---\n",
        r"\1\n",
        text,
        count=1,
        flags=re.M,
    )

    if new != text:
        README.write_text(new.rstrip() + "\n", encoding="utf-8")
        print("remove_legacy_toc: changed")
    else:
        print("remove_legacy_toc: no change")


if __name__ == "__main__":
    main()

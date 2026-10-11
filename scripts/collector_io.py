"""Durable, idempotent news writes before advancing collector deduplication."""
from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path


def append_news_lines(path: Path, lines: list[str]) -> None:
    if not lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding='utf-8') if path.exists() else f"# {datetime.now():%Y-%m-%d} 업데이트\n\n## 뉴스/업데이트\n"
    updated = current
    for line in lines:
        urls = re.findall(r'https?://[^\s)]+', line)
        if line in updated or (urls and any(url in updated for url in urls)):
            continue
        updated += line + '\n'
    if updated == current and path.exists():
        return
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write(updated)
            file.flush()
            os.fsync(file.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

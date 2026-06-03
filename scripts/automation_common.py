#!/usr/bin/env python3
"""Shared helpers for unmanned collection/automation scripts."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

try:
    from scripts.time_utils import seoul_timestamp_str, seoul_today_str
except Exception:  # pragma: no cover
    from time_utils import seoul_timestamp_str, seoul_today_str  # type: ignore

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
DATA = BASE / "data"
FACTS = DATA / "facts"
REPORTS = DATA / "reports"
URL_RE = re.compile(r'https?://[^\s)>"\']+')


@dataclass(frozen=True)
class CommandResult:
    rc: int
    out: str


def run_cmd(cmd: list[str], timeout: int = 20) -> CommandResult:
    try:
        proc = subprocess.run(
            cmd,
            cwd=BASE,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return CommandResult(1, str(exc))
    return CommandResult(proc.returncode, (proc.stdout + proc.stderr).strip())


def ensure_dirs() -> None:
    FACTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def extract_urls(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;\"'")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def host_for_url(url: str) -> str:
    host = urlsplit(url).netloc.lower().split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def md_table(rows: list[list[str]], headers: list[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        safe = [str(cell).replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines)


def report_header(title: str) -> list[str]:
    return [f"# {title}", "", f"> Updated: {seoul_timestamp_str()} (Asia/Seoul)", ""]


def today() -> str:
    return seoul_today_str()

#!/usr/bin/env python3
"""Resolve YouTube channel IDs from channel URLs/handles.

Input: config/youtube-channels.txt (one URL per line)
Output: prints TSV: name\tchannel_id\turl

Best-effort, network dependent.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
INP = BASE / "config" / "youtube-channels.txt"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

CHANNEL_RES = [
    re.compile(r"\"channelId\"\s*:\s*\"(UC[0-9A-Za-z_-]{20,})\""),
    re.compile(r"\"externalId\"\s*:\s*\"(UC[0-9A-Za-z_-]{20,})\""),
    re.compile(r"https://www\.youtube\.com/channel/(UC[0-9A-Za-z_-]{20,})"),
]



def resolve(url: str) -> str | None:
    try:
        r = requests.get(url, headers=UA, timeout=15)
        r.raise_for_status()
        for rx in CHANNEL_RES:
            m = rx.search(r.text)
            if m:
                return m.group(1)
    except Exception:
        return None
    return None


def main() -> int:
    if not INP.exists():
        print("missing config/youtube-channels.txt", file=sys.stderr)
        return 2

    for raw in INP.read_text(encoding="utf-8").splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        # allow: Name<TAB>URL
        name = "YouTube"
        url = ln
        if "\t" in ln:
            name, url = [x.strip() for x in ln.split("\t", 1)]
        cid = resolve(url)
        if not cid:
            continue
        print(f"{name}\t{cid}\t{url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

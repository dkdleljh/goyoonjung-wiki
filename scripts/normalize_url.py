#!/usr/bin/env python3
"""Normalize URLs for dedupe.

Rules:
- lower-case scheme+host
- strip fragments
- drop common tracking params (utm_*, fbclid, gclid, igshid, etc.)
- keep other params (conservative)
"""

import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

DROP_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "spm",
}


def norm(url: str) -> str:
    url = url.strip()
    if not url:
        return url

    sp = urlsplit(url)
    scheme = (sp.scheme or "https").lower()
    netloc = sp.netloc.lower()

    # Some inputs might be missing scheme
    if not netloc and sp.path.startswith("www."):
        sp2 = urlsplit("https://" + url)
        scheme, netloc, sp = sp2.scheme.lower(), sp2.netloc.lower(), sp2

    # Query filtering
    q = []
    for k, v in parse_qsl(sp.query, keep_blank_values=True):
        kl = k.lower()
        if kl.startswith("utm_"):
            continue
        if kl in DROP_KEYS:
            continue
        q.append((k, v))

    query = urlencode(q, doseq=True)

    # strip fragment
    frag = ""

    return urlunsplit((scheme, netloc, sp.path, query, frag))


if __name__ == "__main__":
    data = sys.stdin.read() if not sys.argv[1:] else "\n".join(sys.argv[1:])
    lines = [l for l in data.splitlines() if l.strip()]
    for l in lines:
        print(norm(l))

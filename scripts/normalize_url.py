#!/usr/bin/env python3
"""Normalize URLs for dedupe and canonical identity.

Rules:
- lower-case scheme+host
- strip fragments
- drop common tracking params
- normalize safe mobile/amp host variants
- YouTube canonicalization by video id
"""

import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DROP_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "spm",
    "cmpid",
    "ns_mchannel",
    "ns_source",
    "ns_campaign",
    "ns_linkname",
    "mkt_tok",
    "yclid",
    "dclid",
    "gbraid",
    "wbraid",
    "si",
}

STRIP_HOST_PREFIXES = (
    "m.",
    "mobile.",
)

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}

AMP_PATH_RE = re.compile(r"^/(?:amp/)?(.+?)/amp/?$")


def _strip_amp_path(path: str) -> str:
    if not path:
        return "/"
    m = AMP_PATH_RE.match(path)
    if m:
        return "/" + m.group(1)
    if path.endswith(".amp"):
        return path[:-4]
    return path


def _normalize_host(host: str) -> str:
    host = host.lower().split(":", 1)[0]
    if host.startswith("amp."):
        host = host[4:]
    for pref in STRIP_HOST_PREFIXES:
        if host.startswith(pref):
            host = host[len(pref):]
    return host


def _normalize_youtube(path: str, query_items: list[tuple[str, str]]) -> tuple[str, list[tuple[str, str]]]:
    video_id = ""
    qmap: dict[str, str] = {}
    for k, v in query_items:
        qmap[k.lower()] = v

    if path.startswith("/watch"):
        video_id = qmap.get("v", "")
    elif path.startswith("/shorts/"):
        video_id = path.split("/", 3)[2]
    elif path.startswith("/embed/"):
        video_id = path.split("/", 3)[2]
    elif path and path != "/":
        video_id = path.strip("/").split("/", 1)[0]

    if video_id:
        return "/watch", [("v", video_id)]
    return path or "/", query_items


def norm(url: str) -> str:
    url = url.strip()
    if not url:
        return url

    sp = urlsplit(url)
    scheme = (sp.scheme or "https").lower()
    netloc = _normalize_host(sp.netloc)

    # Some inputs might be missing scheme
    if not netloc and sp.path.startswith("www."):
        sp2 = urlsplit("https://" + url)
        scheme, netloc, sp = sp2.scheme.lower(), _normalize_host(sp2.netloc), sp2

    # Query filtering
    q: list[tuple[str, str]] = []
    for k, v in parse_qsl(sp.query, keep_blank_values=True):
        kl = k.lower()
        if kl.startswith("utm_"):
            continue
        if kl in DROP_KEYS:
            continue
        q.append((k, v))

    # strip fragment
    frag = ""

    path = sp.path or "/"
    path = _strip_amp_path(path)
    # normalize duplicate slashes
    while "//" in path:
        path = path.replace("//", "/")
    # normalize trailing slash (keep root '/')
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    if netloc in YOUTUBE_HOSTS:
        netloc = "www.youtube.com"
        path, q = _normalize_youtube(path, q)

    query = urlencode(q, doseq=True)
    return urlunsplit((scheme, netloc, path, query, frag))


if __name__ == "__main__":
    data = sys.stdin.read() if not sys.argv[1:] else "\n".join(sys.argv[1:])
    lines = [l for l in data.splitlines() if l.strip()]
    for l in lines:
        print(norm(l))

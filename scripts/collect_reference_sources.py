#!/usr/bin/env python3
"""Collect reference-source *signals* (not full content) for unmanned monitoring.

Goal:
- Keep link-first, copyright-safe.
- For sources that require login/dynamic rendering, record 'skip reason' instead of failing the pipeline.

Writes into today's news file under:
<!-- AUTO-REF-SOURCES:START --> ... <!-- AUTO-REF-SOURCES:END -->

This is intended to answer: "Did anything change on Wikipedia/agency/etc?" without manual checking.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import quote

import requests

TZ = "Asia/Seoul"
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NEWS_DIR = os.path.join(BASE, "news")

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}
TIMEOUT = 20

WIKIPEDIA_TITLE = "고윤정"
WIKIPEDIA_API = (
    "https://ko.wikipedia.org/w/api.php"
    "?format=json&action=query&prop=revisions&rvprop=timestamp%7Cids&rvlimit=1&titles="
    + quote(WIKIPEDIA_TITLE)
)
WIKIPEDIA_URL = "https://ko.wikipedia.org/wiki/%EA%B3%A0%EC%9C%A4%EC%A0%95"

NAMU_URL = "https://namu.wiki/w/%EA%B3%A0%EC%9C%A4%EC%A0%95"
MAA_ARTIST_URL = "https://maa.co.kr/artists/go-younjung"
INSTAGRAM_URL = "https://www.instagram.com/goyounjung/"
FANCAFE_URL = None  # unknown; keep as None until user provides


def today_ymd() -> str:
    # Avoid python tz libs; rely on system TZ via env from runner.
    return datetime.now().strftime("%Y-%m-%d")


def http_head(url: str) -> dict:
    try:
        r = requests.head(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
        return {
            "ok": True,
            "status": r.status_code,
            "final": r.url,
            "etag": r.headers.get("ETag"),
            "last_modified": r.headers.get("Last-Modified"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def wikipedia_latest() -> dict:
    try:
        r = requests.get(WIKIPEDIA_API, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values())) if pages else {}
        revs = page.get("revisions", [])
        rev = revs[0] if revs else {}
        return {
            "ok": True,
            "revid": rev.get("revid"),
            "parentid": rev.get("parentid"),
            "timestamp": rev.get("timestamp"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_block(items: list[str]) -> str:
    lines = ["## 참고 출처 업데이트 신호(무인)", "> 목적: 위키/공식/커뮤니티의 '변경 신호'만 감지합니다(원문 복사 없음).", ""]
    lines += items
    return "\n".join(lines).rstrip() + "\n"


def upsert_news_block(news_path: str, body: str) -> None:
    start = "<!-- AUTO-REF-SOURCES:START -->"
    end = "<!-- AUTO-REF-SOURCES:END -->"

    with open(news_path, "r", encoding="utf-8") as f:
        text = f.read()

    block = f"{start}\n{body}{end}"

    if start in text and end in text:
        text = re.sub(rf"{re.escape(start)}.*?{re.escape(end)}", block, text, flags=re.S)
    else:
        # Insert near top, after '## 실행 상태' header if possible
        m = re.search(r"^## 실행 상태\s*$", text, flags=re.M)
        if m:
            insert_at = m.end()
            text = text[:insert_at] + "\n\n" + block + "\n" + text[insert_at:]
        else:
            text = block + "\n\n" + text

    with open(news_path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> int:
    os.makedirs(NEWS_DIR, exist_ok=True)
    ymd = today_ymd()
    news_path = os.path.join(NEWS_DIR, f"{ymd}.md")
    if not os.path.exists(news_path):
        # Do not create from scratch here; let mark_news_status create structure.
        return 0

    items: list[str] = []

    wp = wikipedia_latest()
    if wp.get("ok"):
        items.append(f"- 위키백과: {WIKIPEDIA_URL} (latest rev: {wp.get('revid')}, ts: {wp.get('timestamp')})")
    else:
        items.append(f"- 위키백과: {WIKIPEDIA_URL} (조회 실패: {wp.get('error')})")

    namu = http_head(NAMU_URL)
    if namu.get("ok"):
        items.append(f"- 나무위키: {NAMU_URL} (status: {namu.get('status')}, etag: {namu.get('etag')}, lm: {namu.get('last_modified')})")
    else:
        items.append(f"- 나무위키: {NAMU_URL} (HEAD 실패: {namu.get('error')})")

    maa = http_head(MAA_ARTIST_URL)
    if maa.get("ok"):
        items.append(f"- 소속사(MAA): {MAA_ARTIST_URL} (status: {maa.get('status')}, etag: {maa.get('etag')}, lm: {maa.get('last_modified')})")
    else:
        items.append(f"- 소속사(MAA): {MAA_ARTIST_URL} (HEAD 실패: {maa.get('error')})")

    # Instagram/fancafe: typically requires login/dynamic; record as unmanned skip
    items.append(f"- 인스타그램(공식): {INSTAGRAM_URL} (무인 수집: 로그인/동적 로딩 이슈로 링크만 유지)")
    if FANCAFE_URL:
        items.append(f"- 팬카페(공식): {FANCAFE_URL} (무인 수집: 정책/접근 방식 확정 필요)")
    else:
        items.append("- 팬카페(공식): (URL 미확정 — 주인님이 주소 주시면 무인 점검 신호에 포함)")

    body = format_block(items)
    upsert_news_block(news_path, body)
    print("collect_reference_sources: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

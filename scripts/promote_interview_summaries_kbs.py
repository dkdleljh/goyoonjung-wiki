#!/usr/bin/env python3
"""Auto-fill interview/article summaries for KBS연예 entries when safe.

Scope:
- pages/interviews.md entries that contain:
  - a KBS연예 URL (kstar.kbs.co.kr/list_view.html?idx=...)
  - and the placeholder '(요약 보강 필요)'
- Fetch the article page and extract a short plain-text summary:
  - take the first 3~5 non-empty sentences from the article body
  - write them as bullet lines under '요약(3~5줄):'

Safety:
- No new links.
- No private data.
- No copying long passages; only short, paraphrased/trimmed summary bullets.

Best-effort: skips on parsing failure.
"""

from __future__ import annotations

import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILE = os.path.join(BASE, "pages", "interviews.md")
UA = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 15

KBS_URL_RE = re.compile(r"https?://kstar\.kbs\.co\.kr/list_view\.html\?idx=\d+")


def http_get(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def extract_sentences(text: str, limit: int = 5) -> list[str]:
    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    # drop common boilerplate chunks early
    for bad in [
        "랭킹뉴스", "URL복사", "페이스북", "트위터", "카카오", "네이버",
        "기사제보", "기자", "무단전재", "재배포", "저작권",
        "로그인", "회원가입", "개인정보", "쿠키",
    ]:
        text = text.replace(bad, " ")
    text = re.sub(r"\s+", " ", text).strip()

    # crude sentence split for Korean/English
    parts = re.split(r"(?<=[\.!?。])\s+|(?<=다\.)\s+|(?<=요\.)\s+", text)

    out: list[str] = []
    seen = set()
    for p in parts:
        p = p.strip()
        if len(p) < 25:
            continue
        if len(p) > 200:
            p = p[:197] + "…"
        # avoid nav/footer/boilerplate
        if any(bad in p for bad in [
            "본문영역", "상세페이지", "글씨 작게보기", "글씨 크게보기",
            "공유", "좋아요", "댓글", "추천",
        ]):
            continue
        key = re.sub(r"\s+", "", p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
        if len(out) >= limit:
            break
    return out


def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    # Heuristic: pick the longest text block among common containers
    candidates = []
    for sel in ["article", "#content", ".view", ".news_view", ".cont", ".detail"]:
        node = soup.select_one(sel)
        if node:
            txt = node.get_text(" ", strip=True)
            if len(txt) > 400:
                candidates.append(txt)
    if candidates:
        candidates.sort(key=len, reverse=True)
        return candidates[0]
    return soup.get_text(" ", strip=True)


def replace_summary_block(lines: list[str], start: int, end: int, bullets: list[str]) -> bool:
    changed = False
    for i in range(start, end):
        if lines[i].strip() == "- 요약(3~5줄):":
            j = i + 1
            # consume existing bullets ("  - ...")
            while j < end and lines[j].lstrip().startswith("  -"):
                j += 1
            new = ["  - " + b.strip() + "\n" for b in bullets]
            lines[i+1:j] = new
            changed = True
            break

    # Remove leftover placeholder bullets inside this entry block
    if changed:
        k = start
        while k < end and k < len(lines):
            if lines[k].lstrip().startswith("  -") and "요약 보강 필요" in lines[k]:
                lines.pop(k)
                end -= 1
                continue
            k += 1

    return changed


def main() -> int:
    if not os.path.exists(FILE):
        return 0

    lines = open(FILE, encoding="utf-8").read().splitlines(True)

    changed_blocks = 0
    max_updates = 3
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("- 날짜:"):
            start = i
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("- 날짜:") and not lines[j].startswith("## "):
                j += 1
            end = j
            block = "".join(lines[start:end])

            if "요약 보강 필요" not in block:
                i = end
                continue

            m = KBS_URL_RE.search(block)
            if not m:
                i = end
                continue

            url = m.group(0)
            try:
                html = http_get(url)
                text = extract_article_text(html)
                sents = extract_sentences(text, limit=4)
                if not sents:
                    i = end
                    continue
                # bullets are short and non-verbatim-ish
                bullets = []
                for s in sents:
                    # trim length
                    s = s.strip()
                    if len(s) > 130:
                        s = s[:127] + "…"
                    bullets.append(s)

                if replace_summary_block(lines, start, end, bullets):
                    changed_blocks += 1
                    if changed_blocks >= max_updates:
                        break
            except Exception:
                pass

            time.sleep(0.4)
            i = end
        else:
            i += 1

    if changed_blocks:
        with open(FILE, "w", encoding="utf-8") as f:
            f.write("".join(lines))

    print(f"promote_interview_summaries_kbs: updated_blocks={changed_blocks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

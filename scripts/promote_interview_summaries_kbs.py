#!/usr/bin/env python3
"""Auto-fill interview/article summaries for KBS연예 entries when safe.

Scope:
- pages/interviews.md entries that contain:
  - a KBS연예 URL (kstar.kbs.co.kr/list_view.html?idx=...)
  - and the placeholder '(요약 보강 필요)'
- Fetch the article page and generate a SHORT, non-verbatim summary:
  - 2~3 bullets maximum
  - keyword-centric, template-based phrasing (avoid copying sentences)
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


STOPWORDS = {
    # very common / boilerplate
    "기자",
    "기사",
    "인터뷰",
    "영상",
    "사진",
    "제공",
    "무단전재",
    "재배포",
    "저작권",
    "랭킹뉴스",
    "URL복사",
    "페이스북",
    "트위터",
    "카카오",
    "네이버",
    "로그인",
    "회원가입",
    "개인정보",
    "쿠키",
    # subject name is allowed but shouldn't dominate keywords
    "고윤정",
}


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    for bad in [
        "랭킹뉴스",
        "URL복사",
        "페이스북",
        "트위터",
        "카카오",
        "네이버",
        "기사제보",
        "무단전재",
        "재배포",
        "저작권",
        "로그인",
        "회원가입",
        "개인정보",
        "쿠키",
    ]:
        text = text.replace(bad, " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    """Extract simple Korean/English keywords without NLP libraries."""
    text = normalize_text(text)
    # grab Hangul/English tokens, prefer Hangul chunks
    tokens = re.findall(r"[가-힣]{2,8}|[A-Za-z]{3,12}", text)
    freq: dict[str, int] = {}
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if t in STOPWORDS:
            continue
        # drop ultra-generic terms
        if t in {"대한민국", "배우", "드라마", "시리즈", "작품", "방송", "공개"}:
            continue
        freq[t] = freq.get(t, 0) + 1

    # rank by frequency then length (slight preference for informative tokens)
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))
    out: list[str] = []
    for w, _ in ranked:
        if w not in out:
            out.append(w)
        if len(out) >= limit:
            break
    return out


def extract_titles(text: str, limit: int = 4) -> list[str]:
    """Extract quoted short titles (very conservative)."""
    text = normalize_text(text)
    titles: list[str] = []
    for m in re.findall(r"[\"'“”‘’《》<>「」『』]([^\"'“”‘’《》<>「」『』]{2,20})[\"'“”‘’《》<>「」『』]", text):
        t = m.strip()
        if not t or t in titles:
            continue
        # avoid obviously non-title junk
        if any(x in t for x in ["http", "www", "kbs"]):
            continue
        titles.append(t)
        if len(titles) >= limit:
            break
    return titles


def is_too_verbatim(bullet: str, article_text: str) -> bool:
    """Guardrail: do not write bullets that appear verbatim (or near-verbatim) in the article."""
    b = re.sub(r"\s+", " ", bullet).strip()
    t = re.sub(r"\s+", " ", article_text).strip()
    if len(b) >= 20 and b in t:
        return True
    # check any 20-char chunk is present in the article
    if len(b) >= 40:
        for i in range(0, len(b) - 20, 5):
            chunk = b[i : i + 20]
            if chunk in t:
                return True
    return False


def build_safe_bullets(article_text: str) -> list[str]:
    """Return 2~3 paraphrase-like bullets; if not enough signal, return []."""
    article_text = normalize_text(article_text)
    if len(article_text) < 200:
        return []

    kw = extract_keywords(article_text, limit=8)
    titles = extract_titles(article_text, limit=4)

    bullets: list[str] = []

    if kw:
        bullets.append("주제 키워드: " + ", ".join(kw[:5]))

    if titles:
        bullets.append("언급된 작품/프로젝트(표기 확인 필요): " + ", ".join(titles[:3]))

    bullets.append("핵심 포인트: 고윤정 관련 근황/활동 맥락을 정리한 인터뷰(자세한 내용은 원문 링크 참고).")

    # Keep 2~3 bullets
    bullets = [b for b in bullets if b.strip()]
    if len(bullets) < 2:
        return []
    bullets = bullets[:3]

    # Similarity guard
    safe: list[str] = []
    for b in bullets:
        if is_too_verbatim(b, article_text):
            continue
        # length guard
        if len(b) > 140:
            b = b[:137] + "…"
        safe.append(b)

    return safe if len(safe) >= 2 else []


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
                bullets = build_safe_bullets(text)
                if not bullets:
                    i = end
                    continue

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

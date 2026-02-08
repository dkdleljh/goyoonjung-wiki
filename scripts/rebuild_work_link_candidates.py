#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

BASE = Path("/home/zenith/바탕화면/goyoonjung-wiki")
PAGES = BASE / "pages"
WORKS_DIR = PAGES / "works"

WORKS = {
    "moving.md": {
        "title": "무빙",
        "keywords": ["무빙", "장희수", "Disney+", "디즈니+"],
    },
    "alchemy-of-souls.md": {
        "title": "환혼: 빛과 그림자",
        "keywords": ["환혼", "빛과 그림자", "진부연", "낙수", "tvN"],
    },
    "law-school.md": {
        "title": "로스쿨",
        "keywords": ["로스쿨", "전예슬", "JTBC"],
    },
    "sweethome.md": {
        "title": "스위트홈",
        "keywords": ["스위트홈", "스위트 홈", "박유리", "Netflix", "넷플릭스"],
    },
    "hunt.md": {
        "title": "헌트",
        "keywords": ["헌트", "조유정"],
    },
}

# Files to scan for links/mentions
SCAN_FILES = [
    PAGES / "interviews.md",
    PAGES / "appearances.md",
    PAGES / "endorsements" / "beauty.md",
    PAGES / "endorsements" / "fashion.md",
    PAGES / "endorsements" / "lifestyle.md",
    PAGES / "pictorials" / "cover.md",
    PAGES / "pictorials" / "editorial.md",
    PAGES / "pictorials" / "campaign.md",
    PAGES / "pictorials" / "making.md",
]

URL_RE = re.compile(r"https?://[^\s)]+")

START = "<!-- AUTO-CANDIDATES:START -->"
END = "<!-- AUTO-CANDIDATES:END -->"


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def extract_candidate_blocks(text: str):
    """Return list of (block_text, url) pairs for entries that contain urls.
    Heuristic: split by lines starting with '- 날짜:' (our template) or '---'.
    """
    # Normalize line endings
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    blocks = []
    cur = []

    def flush():
        nonlocal cur
        if not cur:
            return
        b = "\n".join(cur).strip()
        if b:
            urls = URL_RE.findall(b)
            if urls:
                # pick first url as representative
                blocks.append((b, urls[0]))
        cur = []

    for ln in lines:
        if ln.startswith("- 날짜:") and cur:
            flush()
        if ln.strip() == "---":
            flush()
            continue
        cur.append(ln)

    flush()
    return blocks


def block_title(block: str) -> str:
    # Try to find '제목:' line, else first non-empty line
    for ln in block.split("\n"):
        if ln.strip().startswith("- 제목"):
            t = ln.split(":", 1)[-1].strip()
            if t:
                return t
        if ln.strip().startswith("- 프로그램/행사명"):
            t = ln.split(":", 1)[-1].strip()
            if t:
                return t
        if ln.strip().startswith("- 브랜드/회사명"):
            t = ln.split(":", 1)[-1].strip()
            if t:
                return t
        if ln.strip().startswith("- 매체/브랜드"):
            t = ln.split(":", 1)[-1].strip()
            if t:
                return t
    for ln in block.split("\n"):
        ln = ln.strip("- ").strip()
        if ln:
            return ln[:80]
    return "(제목 미상)"


def mentioned(block: str, keywords) -> bool:
    return any(k in block for k in keywords)


def build_candidates():
    # Pre-extract blocks per file
    file_blocks = []
    for f in SCAN_FILES:
        txt = read_text(f)
        if not txt:
            continue
        for b, url in extract_candidate_blocks(txt):
            file_blocks.append((f, b, url))

    per_work = {k: [] for k in WORKS.keys()}
    for work_file, meta in WORKS.items():
        kws = meta["keywords"]
        for f, b, url in file_blocks:
            if mentioned(b, kws):
                per_work[work_file].append((f, block_title(b), url))

    return per_work


def update_work_file(work_path: Path, items):
    txt = read_text(work_path)
    if not txt:
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Deduplicate by url
    seen = set()
    cleaned = []
    for f, title, url in items:
        if url in seen:
            continue
        seen.add(url)
        rel = f.relative_to(PAGES)
        cleaned.append((str(rel), title, url))

    # Limit to top N to avoid spam
    cleaned = cleaned[:20]

    auto = []
    auto.append("## 관련 링크(자동 후보)\n")
    auto.append(f"> 생성: {now} (Asia/Seoul) — 키워드 매칭 기반 자동 후보이며, 최종 반영은 사람이 검토합니다.\n")
    if not cleaned:
        auto.append("- (후보 없음)\n")
    else:
        for rel, title, url in cleaned:
            auto.append(f"- [{title}]({url})  _(출처: {rel})_\n")

    auto_block = "\n".join([START, "\n".join(auto).rstrip(), END])

    if START in txt and END in txt:
        new_txt = re.sub(re.escape(START) + r".*?" + re.escape(END), auto_block, txt, flags=re.S)
    else:
        # Insert before 링크 박스 if present, else append
        if "## 링크 박스" in txt:
            new_txt = txt.replace("## 링크 박스", auto_block + "\n\n## 링크 박스", 1)
        else:
            new_txt = txt.rstrip() + "\n\n" + auto_block + "\n"

    if new_txt != txt:
        work_path.write_text(new_txt, encoding="utf-8")
        return True
    return False


def main():
    per_work = build_candidates()
    changed = False
    for filename in WORKS.keys():
        wp = WORKS_DIR / filename
        changed |= update_work_file(wp, per_work.get(filename, []))

    # Print changed status for shell usage
    print("CHANGED" if changed else "NO_CHANGES")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

BASE = Path("/home/zenith/바탕화면/goyoonjung-wiki")
PAGES = BASE / "pages"
WORKS_DIR = PAGES / "works"

CONFIG_YML = BASE / "config" / "works-keywords.yml"

# Fallback defaults (used only if config file is missing)
DEFAULT_WORKS = {
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


def parse_works_keywords_yml(yml_text: str):
    """Tiny, purpose-built parser for config/works-keywords.yml.

    Supported format:

    works:
      filename.md:
        title: "..."
        keywords: ["a", "b"]

    This is NOT a general YAML parser.
    """
    works = {}
    cur_file = None

    for raw in yml_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "works:" or line.startswith("works:"):
            continue

        m_file = re.match(r"^([A-Za-z0-9_.-]+\.md):\s*$", line)
        if m_file:
            cur_file = m_file.group(1)
            works[cur_file] = {"title": cur_file.replace(".md", ""), "keywords": []}
            continue

        if cur_file is None:
            continue

        # title: "..."
        if line.startswith("title:"):
            val = line.split(":", 1)[1].strip()
            val = val.strip('"').strip("'")
            works[cur_file]["title"] = val
            continue

        # keywords: ["a", "b"]
        if line.startswith("keywords:"):
            val = line.split(":", 1)[1].strip()
            # Expect [ ... ]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                if inner:
                    # split by commas not inside quotes (simple)
                    parts = [p.strip() for p in inner.split(",")]
                    kws = []
                    for p in parts:
                        p = p.strip()
                        p = p.strip('"').strip("'")
                        if p:
                            kws.append(p)
                    works[cur_file]["keywords"] = kws
            continue

    return works


def load_works_config():
    if CONFIG_YML.exists():
        try:
            text = CONFIG_YML.read_text(encoding="utf-8")
            cfg = parse_works_keywords_yml(text)
            # Basic validation
            if cfg:
                return cfg
        except Exception:
            pass
    return DEFAULT_WORKS


WORKS = load_works_config()

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

# S-tier domains (official / primary sources) for auto recommendations
S_TIER_DOMAINS = (
    "netflix.com",
    "disneyplus.com",
    "disneyplus.kr",
    "tvn.cjenm.com",
    "jtbc.co.kr",
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "maac.co.kr",
    "marieclairekorea.com",
    "vogue.co.kr",
    "elle.co.kr",
    "wkorea.com",
    "harpersbazaar.co.kr",
    "gqkorea.co.kr",
    "esquirekorea.co.kr",
)

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


def existing_candidate_urls(txt: str):
    if START not in txt or END not in txt:
        return None
    block = re.search(re.escape(START) + r"(.*?)" + re.escape(END), txt, flags=re.S)
    if not block:
        return None
    b = block.group(1)
    # Extract urls only from bullet lines to avoid picking up unrelated URLs
    urls = []
    for ln in b.splitlines():
        ln = ln.strip()
        if not ln.startswith("-"):
            continue
        m = re.search(r"\((https?://[^\s)]+)\)", ln)
        if m:
            urls.append(m.group(1))
    return urls


def is_s_tier(url: str) -> bool:
    try:
        host = re.sub(r"^www\\.", "", url.split("//", 1)[1].split("/", 1)[0].lower())
    except Exception:
        return False
    return any(host == d or host.endswith("." + d) for d in S_TIER_DOMAINS)


def update_work_file(work_path: Path, items):
    txt = read_text(work_path)
    if not txt:
        return False

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

    new_urls = [u for _, _, u in cleaned]
    old_urls = existing_candidate_urls(txt)

    # If the auto-candidate block exists and URLs didn't change, do nothing
    if old_urls is not None and old_urls == new_urls:
        return False

    # Otherwise, rebuild block with a fresh timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # split recommendations (S-tier) vs the rest
    rec = [(rel, title, url) for rel, title, url in cleaned if is_s_tier(url)][:5]
    rest = [(rel, title, url) for rel, title, url in cleaned if (rel, title, url) not in rec]

    auto = []
    auto.append("## 관련 링크(자동 후보)\n")
    auto.append(f"> 생성: {now} (Asia/Seoul) — 키워드 매칭 기반 자동 후보이며, 최종 반영은 사람이 검토합니다.\n")

    if not cleaned:
        auto.append("- (후보 없음)\n")
    else:
        if rec:
            auto.append("### 자동 추천(S급 우선)\n")
            for rel, title, url in rec:
                auto.append(f"- ⭐ [{title}]({url})  _(출처: {rel})_\n")
            auto.append("\n")

        auto.append("### 전체 후보\n")
        for rel, title, url in (rec + rest):
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

#!/usr/bin/env python3
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAGES = BASE / "pages"
CONFIG_DIR = BASE / "config"

START = "<!-- AUTO-CANDIDATES:START -->"
END = "<!-- AUTO-CANDIDATES:END -->"

URL_RE = re.compile(r"https?://[^\s)]+")

SCAN_FILES = [
    PAGES / "interviews.md",
    PAGES / "appearances.md",
    PAGES / "schedule.md",
    PAGES / "endorsements" / "beauty.md",
    PAGES / "endorsements" / "fashion.md",
    PAGES / "endorsements" / "lifestyle.md",
    PAGES / "pictorials" / "cover.md",
    PAGES / "pictorials" / "editorial.md",
    PAGES / "pictorials" / "campaign.md",
    PAGES / "pictorials" / "making.md",
]


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def parse_simple_keywords_yml(path: Path, root_key: str):
    """Tiny YAML-ish parser.

    Expected:
      root_key:
        group_id:
          title: "..."
          keywords: ["a", "b"]

    Returns dict[group_id] = {title:str, keywords:list[str]}
    """
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    groups = {}
    cur = None
    in_root = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith(root_key + ":"):
            in_root = True
            continue
        if not in_root:
            continue

        m_group = re.match(r"^([A-Za-z0-9_.-]+):\s*$", line)
        if m_group:
            cur = m_group.group(1)
            groups[cur] = {"title": cur, "keywords": []}
            continue
        if cur is None:
            continue

        if line.startswith("title:"):
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
            groups[cur]["title"] = val
            continue
        if line.startswith("keywords:"):
            val = line.split(":", 1)[1].strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                if inner:
                    parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
                    groups[cur]["keywords"] = [p for p in parts if p]
            continue

    return groups


def extract_candidate_blocks(text: str):
    # split by '- 날짜:' or '---'
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
    for ln in block.split("\n"):
        for key in ("- 제목:", "- 프로그램/행사명:", "- 매체/브랜드:", "- 브랜드/회사명:"):
            if ln.strip().startswith(key):
                t = ln.split(":", 1)[-1].strip()
                if t:
                    return t
    for ln in block.split("\n"):
        s = ln.strip("- ").strip()
        if s:
            return s[:80]
    return "(제목 미상)"


def existing_urls_in_auto_block(txt: str):
    if START not in txt or END not in txt:
        return None
    m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), txt, flags=re.S)
    if not m:
        return None
    b = m.group(1)
    urls = []
    for ln in b.splitlines():
        ln = ln.strip()
        if not ln.startswith("-"):
            continue
        mm = re.search(r"\((https?://[^\s)]+)\)", ln)
        if mm:
            urls.append(mm.group(1))
    return urls


def update_page(page: Path, title: str, items):
    txt = read_text(page)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # dedupe by url
    seen = set()
    cleaned = []
    for src_rel, t, url in items:
        if url in seen:
            continue
        seen.add(url)
        cleaned.append((src_rel, t, url))
    cleaned = cleaned[:30]

    new_urls = [u for _, _, u in cleaned]
    old_urls = existing_urls_in_auto_block(txt)
    if old_urls is not None and old_urls == new_urls:
        return False

    lines = []
    lines.append(f"# {title}\n")
    lines.append("> 자동 후보 링크 페이지입니다. (키워드 매칭 기반)\n")
    lines.append(f"> 갱신: {now} (Asia/Seoul)\n")

    auto = []
    auto.append("## 관련 링크(자동 후보)\n")
    if not cleaned:
        auto.append("- (후보 없음)\n")
    else:
        for src_rel, t, url in cleaned:
            auto.append(f"- [{t}]({url})  _(출처: {src_rel})_\n")

    content = "\n".join([START, "\n".join(auto).rstrip(), END])

    # Keep any manual notes below markers if present
    if START in txt and END in txt:
        # keep everything after END
        after = re.split(re.escape(END), txt, maxsplit=1, flags=0)
        tail = after[1] if len(after) == 2 else "\n"
        new_txt = "\n".join(lines).rstrip() + "\n\n" + content + "\n" + tail
    else:
        new_txt = "\n".join(lines).rstrip() + "\n\n" + content + "\n"

    if new_txt != txt:
        page.write_text(new_txt, encoding="utf-8")
        return True
    return False


def main():
    # Pre-extract blocks
    file_blocks = []
    for f in SCAN_FILES:
        txt = read_text(f)
        if not txt:
            continue
        rel = f.relative_to(PAGES)
        for b, url in extract_candidate_blocks(txt):
            file_blocks.append((str(rel), b, url))

    changed = False

    # Brands
    brands = parse_simple_keywords_yml(CONFIG_DIR / "brands-keywords.yml", "brands")
    for gid, meta in brands.items():
        kws = meta.get("keywords", [])
        items = []
        for rel, block, url in file_blocks:
            if any(k in block for k in kws):
                items.append((rel, block_title(block), url))
        page = PAGES / "brands" / f"{gid}.md"
        changed |= update_page(page, meta.get("title", gid), items)

    # Magazines
    mags = parse_simple_keywords_yml(CONFIG_DIR / "magazines-keywords.yml", "magazines")
    for gid, meta in mags.items():
        kws = meta.get("keywords", [])
        items = []
        for rel, block, url in file_blocks:
            if any(k in block for k in kws):
                items.append((rel, block_title(block), url))
        page = PAGES / "magazines" / f"{gid}.md"
        changed |= update_page(page, meta.get("title", gid), items)

    print("CHANGED" if changed else "NO_CHANGES")


if __name__ == "__main__":
    main()

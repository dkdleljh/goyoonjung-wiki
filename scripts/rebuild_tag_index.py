#!/usr/bin/env python3
import os
import sys
from collections import defaultdict
from pathlib import Path

# Base directory: parent of scripts/
BASE = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE / "pages"
OUT_FILE = PAGES_DIR / "index-by-tag.md"

def main():
    if not PAGES_DIR.exists():
        print(f"Pages directory not found: {PAGES_DIR}")
        sys.exit(1)

    tag_map = defaultdict(set)

    # Walk through pages directory
    for root, _dirs, files in os.walk(PAGES_DIR):
        for file in files:
            if not file.endswith(".md"):
                continue

            file_path = Path(root) / file

            # Skip the index file itself to avoid self-reference loops or clutter
            if file_path.resolve() == OUT_FILE.resolve():
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("키워드:"):
                            # valid keyword line found
                            content = line[len("키워드:"):].strip()
                            if not content:
                                continue

                            keywords = [k.strip() for k in content.split(",")]
                            rel_path = file_path.relative_to(PAGES_DIR)

                            for k in keywords:
                                if k:
                                    tag_map[k].add(str(rel_path))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Generate Output
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        out.write("# 태그 인덱스\n\n")
        out.write("> 자동 생성 파일입니다. (스크립트: scripts/rebuild_tag_index.py)\n\n")
        out.write("## 공식 링크\n")
        out.write("- (S) 소속사(MAA) 프로필(기준): https://maa.co.kr/artists/go-younjung\n")
        out.write("- (내부) 생성 스크립트: scripts/rebuild_tag_index.py\n\n")
        out.write("## 출처\n")
        out.write("- docs/editorial_policy.md\n\n")
        out.write("## 태그 목록\n\n")

        # Sort tags alphabetically
        sorted_tags = sorted(tag_map.keys())

        if not sorted_tags:
            out.write("(태그가 없습니다.)\n")

        for tag in sorted_tags:
            out.write(f"### {tag}\n")
            # Sort files for each tag
            sorted_files = sorted(tag_map[tag])
            for rel_path in sorted_files:
                name = Path(rel_path).stem
                # Markdown link
                out.write(f"- [{name}]({rel_path})\n")
            out.write("\n")

    print(f"Generated {OUT_FILE}")

if __name__ == "__main__":
    main()

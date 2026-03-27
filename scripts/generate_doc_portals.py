#!/usr/bin/env python3
"""Generate lightweight documentation portals for goyoonjung-wiki."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path


SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def sh(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def latest_tags(repo: Path, limit: int = 3) -> list[str]:
    out = subprocess.check_output(["git", "tag", "--sort=-creatordate"], cwd=repo, text=True)
    tags: list[str] = []
    for line in out.splitlines():
        tag = line.strip()
        if SEMVER_RE.match(tag):
            tags.append(tag)
        if len(tags) >= limit:
            break
    return tags


def main() -> int:
    repo = Path(sh(["git", "rev-parse", "--show-toplevel"], Path.cwd()))
    today = datetime.now().strftime("%Y-%m-%d")
    tags = latest_tags(repo, 3)
    latest_tag = tags[0] if tags else "(none)"
    tag_lines = []
    for tag in tags:
        tag_lines.append(f"- `{tag}`")
        tag_lines.append(f"  - GitHub Release: https://github.com/dkdleljh/goyoonjung-wiki/releases/tag/{tag}")
        tag_lines.append(f"  - 로컬 노트: `logs/releases/release-notes-{tag}.md`")

    files: dict[Path, str] = {
        repo / "README.md": f"""# 고윤정 위키 (Go Youn-jung Wiki)

> 자동 생성 포털 문서 · 마지막 갱신: {today}

이 저장소는 **링크 중심 위키**이면서 동시에 **무인 자동화 운영 저장소**입니다.

## 빠른 시작
- 메인 인덱스: [`index.md`](index.md)
- 허브: [`pages/hub.md`](pages/hub.md)
- 문서 포털: [`docs/README.md`](docs/README.md)
- 운영 가이드: [`docs/OPERATION_GUIDE.md`](docs/OPERATION_GUIDE.md)
- 릴리즈 정책: [`docs/RELEASING.md`](docs/RELEASING.md)
- 시스템 상태: [`pages/system_status.md`](pages/system_status.md)
- Perfect Scorecard: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)

## 현재 자동화 범위
- daily update
- automation health 검사
- stale lock 정리
- changelog 생성
- semver 태그/릴리즈
- release notes 자산 업로드

## 최신 릴리즈
{chr(10).join(tag_lines) if tag_lines else "- 아직 릴리즈 태그가 없습니다."}

## 자주 쓰는 명령
```bash
bash scripts/check_automation_health.sh
python3 scripts/wiki_score.py
python3 scripts/generate_doc_portals.py
FORCE=1 ./scripts/run_daily_update.sh
```

## 메모
- 이 README는 `scripts/generate_doc_portals.py`로 자동 생성됩니다.
- 상세 설명형 문서는 `docs/OPERATION_GUIDE.md`, `docs/RELEASING.md`에서 관리합니다.
""",
        repo / "index.md": f"""# 고윤정 위키 인덱스

> 자동 생성 인덱스 · 마지막 갱신: {today}

## 바로 가기
- [README.md](README.md)
- [docs/README.md](docs/README.md)
- [docs/OPERATION_GUIDE.md](docs/OPERATION_GUIDE.md)
- [docs/RELEASING.md](docs/RELEASING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [pages/hub.md](pages/hub.md)
- [pages/system_status.md](pages/system_status.md)
- [pages/perfect-scorecard.md](pages/perfect-scorecard.md)

## 최신 릴리즈
- 최신 태그: `{latest_tag}`
- 자세한 내용: [CHANGELOG.md](CHANGELOG.md)
""",
        repo / "docs" / "README.md": f"""# docs/ 문서 포털

> 자동 생성 문서 인덱스 · 마지막 갱신: {today}

## 핵심 문서
- [OPERATION_GUIDE.md](OPERATION_GUIDE.md)
- [RELEASING.md](RELEASING.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [scoring.md](scoring.md)
- [ux-automation-system.md](ux-automation-system.md)

## 연결 문서
- [루트 README](../README.md)
- [메인 인덱스](../index.md)
- [허브](../pages/hub.md)
- [시스템 상태](../pages/system_status.md)
- [Perfect Scorecard](../pages/perfect-scorecard.md)
""",
        repo / "CHANGELOG.md": f"""# CHANGELOG

> 자동 생성 요약 changelog · 마지막 갱신: {today}

## 최신 릴리즈
{chr(10).join(tag_lines) if tag_lines else "- 아직 릴리즈 태그가 없습니다."}

## 상세 확인 위치
- GitHub Releases: https://github.com/dkdleljh/goyoonjung-wiki/releases
- 로컬 release notes: `logs/releases/`
- 릴리즈 정책: [`docs/RELEASING.md`](docs/RELEASING.md)
""",
        repo / "pages" / "hub.md": f"""# 🧭 고윤정 위키 허브

> 자동 생성 허브 · 마지막 갱신: {today}

## 운영/문서 링크
- [프로젝트 README](../README.md)
- [문서 포털](../docs/README.md)
- [운영 가이드](../docs/OPERATION_GUIDE.md)
- [릴리즈 정책](../docs/RELEASING.md)
- [CHANGELOG](../CHANGELOG.md)
- [시스템 상태](system_status.md)
- [Perfect Scorecard](perfect-scorecard.md)

## 콘텐츠 핵심 링크
- [프로필](profile.md)
- [필모그래피](filmography.md)
- [타임라인](timeline.md)
- [인터뷰](interviews.md)
- [화보](pictorials.md)
- [광고](endorsements.md)
- [스케줄](schedule.md)
""",
        repo / "pages" / "hub.en.md": f"""# 🧭 Go Youn-jung Wiki Hub

> Auto-generated hub · last updated: {today}

## Ops / Docs
- [Project README](../README.md)
- [Docs portal](../docs/README.md)
- [Operation guide](../docs/OPERATION_GUIDE.md)
- [Releasing guide](../docs/RELEASING.md)
- [CHANGELOG](../CHANGELOG.md)
- [System status](system_status.md)
- [Perfect Scorecard](perfect-scorecard.md)

## Core content
- [Profile](profile.md)
- [Filmography](filmography.md)
- [Timeline](timeline.md)
- [Interviews](interviews.md)
- [Pictorials](pictorials.md)
- [Endorsements](endorsements.md)
- [Schedule](schedule.md)
""",
    }

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

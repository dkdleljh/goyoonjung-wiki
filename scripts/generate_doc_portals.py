#!/usr/bin/env python3
"""Generate lightweight documentation portals for goyoonjung-wiki."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

OWNER = "dkdleljh"
REPO_NAME = "goyoonjung-wiki"
REPO_URL = f"https://github.com/{OWNER}/{REPO_NAME}"
SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def sh(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def latest_tags(repo: Path, limit: int = 3) -> list[str]:
    out = subprocess.check_output(["git", "tag", "--sort=-creatordate"], cwd=repo, text=True)
    tags: list[str] = []
    for line in out.splitlines():
        tag = line.strip()
        match = SEMVER_RE.match(tag)
        if match and int(match.group(1)) < 1000:
            tags.append(tag)
        if len(tags) >= limit:
            break
    return tags


def recent_commits(repo: Path, limit: int = 5) -> list[tuple[str, str]]:
    out = subprocess.check_output(
        ["git", "log", "--pretty=format:%h%x09%s", f"-n{limit}"], cwd=repo, text=True
    )
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        if "\t" in line:
            sha, subject = line.split("\t", 1)
            rows.append((sha.strip(), subject.strip()))
    return rows


def recent_changed_files(repo: Path, limit: int = 8) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"], cwd=repo, text=True
    )
    return [line.strip() for line in out.splitlines() if line.strip()][:limit]


def md_links(paths: list[Path], base: Path, current: Path) -> list[str]:
    lines: list[str] = []
    for p in sorted(paths):
        label = p.relative_to(base).as_posix()
        target = p.relative_to(current.parent).as_posix()
        lines.append(f"- [`{label}`]({target})")
    return lines


def commit_url(sha: str) -> str:
    return f"{REPO_URL}/commit/{sha}"


def bullets(lines: list[str], empty: str) -> str:
    return "\n".join(lines) if lines else empty


def toc(title_pairs: list[tuple[str, str]]) -> str:
    return "\n".join(f"- [{title}](#{anchor})" for title, anchor in title_pairs)


def main() -> int:
    repo = Path(sh(["git", "rev-parse", "--show-toplevel"], Path.cwd()))
    today = datetime.now().strftime("%Y-%m-%d")
    head = sh(["git", "rev-parse", "--short", "HEAD"], repo)
    tags = latest_tags(repo, 3)
    latest_tag = tags[0] if tags else "(none)"
    docs_dir = repo / "docs"
    docs_files = [p for p in docs_dir.glob("*.md") if p.name != "README.md"]
    key_pages = [
        repo / "pages" / "hub.md",
        repo / "pages" / "hub.en.md",
        repo / "pages" / "system_status.md",
        repo / "pages" / "perfect-scorecard.md",
        repo / "pages" / "daily-report.md",
        repo / "pages" / "lint-report.md",
        repo / "pages" / "quality-report.md",
    ]
    recent = recent_commits(repo, 5)
    changed_files = recent_changed_files(repo, 8)

    tag_lines = [
        f"- `{tag}`\n  - GitHub Release: {REPO_URL}/releases/tag/{tag}\n  - 로컬 노트: `logs/releases/release-notes-{tag}.md`"
        for tag in tags
    ]
    recent_lines = [f"- [`{sha}`]({commit_url(sha)}) — {subject}" for sha, subject in recent]
    changed_file_lines = [f"- `{path}`" for path in changed_files]

    status_rows = [
        "| 항목 | 값 |",
        "|---|---|",
        f"| 최신 커밋 | `{head}` |",
        f"| 최신 릴리즈 태그 | `{latest_tag}` |",
        f"| docs 문서 수 | `{len(docs_files)}` |",
        f"| 운영 페이지 수 | `{len([p for p in key_pages if p.exists()])}` |",
        "| 문서 생성기 | `scripts/generate_doc_portals.py` |",
        "| daily update | `scripts/run_daily_update.sh` |",
    ]
    operating_contract = [
        "- 목표: 과거/현재/미래 정보를 링크 중심으로 계속 확장한다.",
        "- 증명 한계: ‘모든 정보 100%’는 증명할 수 없으므로 공식 근거, 누락 탐지, 검증 큐로 관리한다.",
        "- 무인 운영: daily timer, health check, retry, lock, backup, commit/push, release notes를 자동화한다.",
        "- 안전 원칙: 루머/사생활/비공식 단정은 금지하고, 미확정 항목은 검증 큐에 남긴다.",
        "- 현재 판정: `bash scripts/check_automation_health.sh`와 `make check` 통과를 운영 기준으로 삼는다.",
    ]

    badge_block = " ".join(
        [
            f"![Repo](https://img.shields.io/badge/repo-{REPO_NAME}-111827?style=flat-square)",
            f"![Latest Tag](https://img.shields.io/badge/latest-{latest_tag}-2563eb?style=flat-square)",
            f"![Docs](https://img.shields.io/badge/docs-{len(docs_files)}-059669?style=flat-square)",
            "![Automation](https://img.shields.io/badge/automation-daily__update-7c3aed?style=flat-square)",
        ]
    )

    readme_toc = toc([
        ("빠른 시작", "빠른-시작"),
        ("상태 요약", "상태-요약"),
        ("현재 자동화 범위", "현재-자동화-범위"),
        ("최신 릴리즈", "최신-릴리즈"),
        ("최근 변경 요약", "최근-변경-요약"),
        ("최근 변경 파일", "최근-변경-파일"),
        ("자주 쓰는 명령", "자주-쓰는-명령"),
    ])

    files: dict[Path, str] = {
        repo / "README.md": f"""# 고윤정 위키 (Go Youn-jung Wiki)

{badge_block}

> 자동 생성 포털 문서 · 마지막 갱신: {today}

이 저장소는 **링크 중심 위키**이면서 동시에 **무인 자동화 운영 저장소**입니다.

## 문서 목차
{readme_toc}

## 빠른 시작
- 메인 인덱스: [`index.md`](index.md)
- 허브: [`pages/hub.md`](pages/hub.md)
- 문서 포털: [`docs/README.md`](docs/README.md)
- 운영 가이드: [`docs/OPERATION_GUIDE.md`](docs/OPERATION_GUIDE.md)
- 릴리즈 정책: [`docs/RELEASING.md`](docs/RELEASING.md)
- 시스템 상태: [`pages/system_status.md`](pages/system_status.md)
- Perfect Scorecard: [`pages/perfect-scorecard.md`](pages/perfect-scorecard.md)

## 상태 요약
{chr(10).join(status_rows)}

## 현재 자동화 범위
- daily update
- automation health 검사
- stale lock 정리
- changelog 생성
- semver 태그/릴리즈
- release notes 자산 업로드

## 운영 계약
{chr(10).join(operating_contract)}

## 최신 릴리즈
{bullets(tag_lines, '- 아직 릴리즈 태그가 없습니다.')}

## 최근 변경 요약
{bullets(recent_lines, '- 최근 커밋 정보가 없습니다.')}

## 최근 변경 파일
{bullets(changed_file_lines, '- 직전 커밋의 변경 파일 정보가 없습니다.')}

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

## 최근 변경 5개
{bullets(recent_lines, '- 최근 커밋 정보가 없습니다.')}

## 직전 변경 파일
{bullets(changed_file_lines, '- 직전 커밋의 변경 파일 정보가 없습니다.')}
""",
        repo / "docs" / "README.md": f"""# docs/ 문서 포털

> 자동 생성 문서 인덱스 · 마지막 갱신: {today}

## 문서 목차
- [핵심 문서](#핵심-문서)
- [문서 상태 요약](#문서-상태-요약)
- [연결 문서](#연결-문서)
- [전체 docs 목록](#전체-docs-목록)

## 핵심 문서
- [OPERATION_GUIDE.md](OPERATION_GUIDE.md)
- [RELEASING.md](RELEASING.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [scoring.md](scoring.md)
- [ux-automation-system.md](ux-automation-system.md)

## 문서 상태 요약
- docs 문서 수: `{len(docs_files)}`
- 운영 핵심 페이지 수: `{len([p for p in key_pages if p.exists()])}`
- 최신 릴리즈 태그: `{latest_tag}`

## 운영 계약
{chr(10).join(operating_contract)}

## 연결 문서
- [루트 README](../README.md)
- [메인 인덱스](../index.md)
- [허브](../pages/hub.md)
- [시스템 상태](../pages/system_status.md)
- [Perfect Scorecard](../pages/perfect-scorecard.md)

## 전체 docs 목록
{bullets(md_links(docs_files, repo, repo / 'docs' / 'README.md'), '- 문서가 없습니다.')}
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

## 운영 상태표
{chr(10).join(status_rows)}

## 운영 계약
{chr(10).join(operating_contract)}

## 콘텐츠 핵심 링크
- [프로필](profile.md)
- [필모그래피](filmography.md)
- [타임라인](timeline.md)
- [인터뷰](interviews.md)
- [화보](pictorials.md)
- [광고](endorsements.md)
- [스케줄](schedule.md)

## 최근 변경 파일
{bullets(changed_file_lines[:5], '- 직전 커밋의 변경 파일 정보가 없습니다.')}

## 운영 핵심 페이지
{bullets(md_links([p for p in key_pages if p.exists()], repo, repo / 'pages' / 'hub.md'), '- 문서가 없습니다.')}
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

## Status table
{chr(10).join(status_rows)}

## Core content
- [Profile](profile.md)
- [Filmography](filmography.md)
- [Timeline](timeline.md)
- [Interviews](interviews.md)
- [Pictorials](pictorials.md)
- [Endorsements](endorsements.md)
- [Schedule](schedule.md)

## Recently changed files
{bullets(changed_file_lines[:5], '- No changed files found from the previous commit.')}

## Ops pages
{bullets(md_links([p for p in key_pages if p.exists()], repo, repo / 'pages' / 'hub.en.md'), '- No documents found.')}
""",
    }

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

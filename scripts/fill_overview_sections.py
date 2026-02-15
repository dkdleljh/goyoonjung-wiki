#!/usr/bin/env python3
"""Fill '## 한눈에 보기' blocks on core pages.

Policy
- Do not invent facts.
- Use only internal navigation links and already-present official links.
- Keep the overview concise and consistent.

Edits
- Replaces the 3 placeholder lines under '## 한눈에 보기' with curated defaults.

"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Core pages we keep the overview on.
CORE = [
    "README.md",
    "index.md",
    "index.en.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "pages/hub.md",
    "pages/hub.en.md",
    "pages/profile.md",
    "pages/filmography.md",
    "pages/awards.md",
    "pages/timeline.md",
    "pages/works-characters.md",
    "pages/pictorials.md",
    "pages/endorsements.md",
    "pages/interviews.md",
    "pages/appearances.md",
    "pages/sns.md",
    "pages/schedule.md",
    "docs/OPERATION_GUIDE.md",
    "docs/README.md",
]

# Curated content. Keep one-line fields.
DATA: dict[str, dict[str, str]] = {
    "README.md": {
        "summary": "고윤정 위키의 사용법/규칙/자동화 운영을 한 페이지에서 안내합니다.",
        "links": "허브(pages/hub.md) · 인덱스(index.md) · 오늘 로그(news/YYYY-MM-DD.md) · 일일 리포트(pages/daily-report.md)",
        "status": "운영 문서(S/A 링크 기반) · 자동화 동작 기준점",
    },
    "index.md": {
        "summary": "링크 중심(저작권 안전)으로 작품·화보·광고·인터뷰·행사를 누적하는 메인 인덱스입니다.",
        "links": "허브(pages/hub.md) · 프로필(pages/profile.md) · 필모(pages/filmography.md) · 타임라인(pages/timeline.md) · 오늘 로그(news/YYYY-MM-DD.md)",
        "status": "핵심 탐색 페이지(S/A 우선, 자동 섹션 포함)",
    },
    "index.en.md": {
        "summary": "English entry point for the wiki (link-first, copyright-safe).",
        "links": "Hub(pages/hub.md) · Profile(pages/profile.md) · Filmography(pages/filmography.md) · Timeline(pages/timeline.md)",
        "status": "Core navigation (primary/official links preferred)",
    },
    "pages/hub.md": {
        "summary": "가장 빠른 탐색용 포털(허브)입니다. 오늘/최근 + 핵심 정리 + 아카이브로 바로 이동합니다.",
        "links": "프로필(profile.md) · 필모(filmography.md) · 타임라인(timeline.md) · 인터뷰(interviews.md) · 화보(pictorials.md) · 광고(endorsements.md)",
        "status": "탐색 허브(내부 링크 중심, 자동 인덱스 참조)",
    },
    "pages/hub.en.md": {
        "summary": "Quick navigation hub (English) for core pages and archives.",
        "links": "Profile(profile.md) · Filmography(filmography.md) · Timeline(timeline.md) · Interviews(interviews.md) · Pictorials(pictorials.md)",
        "status": "Navigation hub (link-first)",
    },
    "pages/profile.md": {
        "summary": "공식/검증 가능한 근거로 고윤정의 핵심 프로필 정보를 유지하는 페이지입니다.",
        "links": "소속사(MAA) https://maa.co.kr/artists/go-younjung · 필모(pages/filmography.md) · 타임라인(pages/timeline.md)",
        "status": "S/A 우선(일부 항목은 보조 참고로 분리 운영)",
    },
    "pages/filmography.md": {
        "summary": "작품 축(드라마/시리즈 중심)을 공식 링크 기반으로 정리한 표입니다.",
        "links": "소속사(MAA) https://maa.co.kr/artists/go-younjung · 작품별(pages/works/*.md) · 타임라인(pages/timeline.md)",
        "status": "S/A 우선(플랫폼/방송사 링크 보강 지속)",
    },
    "pages/awards.md": {
        "summary": "수상/노미네이트를 공식 근거로 승격해 나가는 페이지입니다.",
        "links": "블루드래곤시리즈어워즈(공식) · 타임라인(pages/timeline.md)",
        "status": "승격형(S/A 확보 시 확정) · 루머/추측 배제",
    },
    "pages/timeline.md": {
        "summary": "연도 흐름으로 작품/행사/인터뷰/화보를 빠르게 훑는 타임라인입니다(자동 생성 포함).",
        "links": "필모(pages/filmography.md) · 인터뷰(pages/interviews/by-year.md) · 화보(pages/pictorials/by-year.md)",
        "status": "자동 생성(덮어쓰기) + 공식 링크/출처 섹션 포함",
    },
    "pages/works-characters.md": {
        "summary": "작품별로 캐릭터/링크를 묶어 보는 탐색 페이지입니다.",
        "links": "작품 인덱스(pages/works/by-year.md) · 각 작품(pages/works/*.md)",
        "status": "탐색용(링크 박스는 공식 근거 중심으로 보강)",
    },
    "pages/pictorials.md": {
        "summary": "화보/커버/캠페인/메이킹/행사 사진 링크를 카테고리별로 모은 목차입니다.",
        "links": "연도별(pages/pictorials/by-year.md) · 커버(pages/pictorials/cover.md) · 에디토리얼(pages/pictorials/editorial.md)",
        "status": "링크 아카이브(이미지 저장/재배포 금지) · 공식/원문 우선",
    },
    "pages/endorsements.md": {
        "summary": "광고/엠버서더(브랜드/캠페인) 링크를 카테고리·연도별로 정리합니다.",
        "links": "연도별(pages/endorsements/by-year.md) · 뷰티/패션/라이프(pages/endorsements/*)",
        "status": "링크 아카이브(공식/원문 우선) · 날짜/근거 자동 보강",
    },
    "pages/interviews.md": {
        "summary": "인터뷰/기사 원문 링크 + 짧은 요약(3~5줄)로 누적하는 아카이브입니다.",
        "links": "연도별(pages/interviews/by-year.md) · 허브(pages/hub.md)",
        "status": "원문 링크 기반(저작권 안전) · 요약/키워드 지속 보강",
    },
    "pages/appearances.md": {
        "summary": "방송/예능/제작발표회/시사회 등 출연·행사 기록을 링크로 누적합니다.",
        "links": "연도별(pages/appearances/by-year.md) · 타임라인(pages/timeline.md)",
        "status": "공식/원문 근거 우선 · 행사/프로그램 단위로 누적",
    },
    "pages/sns.md": {
        "summary": "공식 채널(소속사/작품/플랫폼 등)로 연결되는 SNS/영상 링크 허브입니다.",
        "links": "MAA(소속사) · 공식 YouTube/Instagram(가능한 범위) · 타임라인(pages/timeline.md)",
        "status": "공식 채널 우선(차단 도메인은 대체 1차 근거 병기)",
    },
    "pages/schedule.md": {
        "summary": "공식 공개 일정(공개/방영/행사)을 확정 근거로만 기록하는 캘린더입니다.",
        "links": "오늘/이번주(자동) · 지난 일정(연도별) · 출연/행사(pages/appearances.md)",
        "status": "확정 일정만(공식/검증 링크 필수) · 지나면 Past로 이동",
    },
    "docs/OPERATION_GUIDE.md": {
        "summary": "무인 자동화 운영/점검/복구 절차를 정리한 운영 가이드입니다.",
        "links": "daily runner(scripts/run_daily_update.sh) · 상태(pages/system_status.md) · 리포트(pages/daily-report.md)",
        "status": "운영 문서(자동화 기준선)",
    },
    "docs/README.md": {
        "summary": "문서 모음의 목차(정책/로드맵/운영)를 제공하는 docs 포털입니다.",
        "links": "편집 정책(docs/editorial_policy.md) · 점수(docs/scoring.md) · 로드맵(docs/ROADMAP_EXECUTION.md)",
        "status": "운영 문서",
    },
    "CHANGELOG.md": {
        "summary": "주요 변경 이력을 기록합니다(자동화/문서/데이터 변경 포함).",
        "links": "최근 변경은 git log 및 news/YYYY-MM-DD.md 참고",
        "status": "운영 기록",
    },
    "CONTRIBUTING.md": {
        "summary": "문서/데이터 추가 시 지켜야 할 규칙과 작업 흐름을 안내합니다.",
        "links": "편집 규칙(pages/style-guide.md) · 저작권(pages/legal.md)",
        "status": "운영 문서",
    },
}

OVERVIEW_BLOCK_RE = re.compile(
    r"(^##\s+한눈에\s+보기\s*$\n\n)"  # header
    r"(^-\s+한\s+줄\s+요약:\s*.*$\n)"
    r"(^-\s+핵심\s+링크:\s*.*$\n)"
    r"(^-\s+상태:\s*.*$)\n",
    re.M,
)


def fill(path: Path) -> bool:
    rel = path.relative_to(BASE).as_posix()
    if rel not in DATA:
        return False

    txt = path.read_text(encoding="utf-8", errors="ignore")
    m = OVERVIEW_BLOCK_RE.search(txt)
    if not m:
        return False

    d = DATA[rel]
    replacement = (
        m.group(1)
        + f"- 한 줄 요약: {d['summary']}\n"
        + f"- 핵심 링크: {d['links']}\n"
        + f"- 상태: {d['status']}\n"
    )

    new = OVERVIEW_BLOCK_RE.sub(replacement, txt, count=1)
    if new != txt:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = 0
    scanned = 0
    for rel in CORE:
        p = BASE / rel
        if not p.exists():
            continue
        scanned += 1
        if fill(p):
            changed += 1
    print(f"fill_overview_sections: scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()

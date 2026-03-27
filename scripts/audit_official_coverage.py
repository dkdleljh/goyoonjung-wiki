#!/usr/bin/env python3
"""Audit high-signal completeness against official coverage anchors.

This audit is intentionally narrow:
- Compare local filmography against the agency's official filmography page.
- Summarize critical unresolved verification debt from local pages.
- Expose a deterministic markdown report for dashboards/scorecards.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import requests

try:
    from scripts.time_utils import seoul_timestamp_str
except Exception:  # pragma: no cover
    from time_utils import seoul_timestamp_str  # type: ignore

BASE = Path(__file__).resolve().parent.parent
FILMOGRAPHY_MD = BASE / "pages" / "filmography.md"
QUALITY_MD = BASE / "pages" / "quality-report.md"
QUEUE_MD = BASE / "pages" / "verification-queue.md"
SCHEDULE_MD = BASE / "pages" / "schedule.md"
OUT = BASE / "pages" / "official-coverage-audit.md"
MAA_URL = "https://maa.co.kr/artists/go-younjung"
WORKS_DIR = BASE / "pages" / "works"
URL_RE = re.compile(r"https?://[^\s)]+")
OFFICIAL_HOST_SUFFIXES = {
    "maa.co.kr",
    "netflix.com",
    "about.netflix.com",
    "disneyplus.com",
    "tving.com",
    "tv.jtbc.co.kr",
    "jtbc.co.kr",
    "tvn.cjenm.com",
    "bsa.blueaward.co.kr",
    "blueaward.co.kr",
    "baeksangawards.co.kr",
    "daejong.or.kr",
    "plusm-ent.com",
}

TITLE_ALIASES = {
    "he is psychometric": "사이코메트리 그녀석",
    "사이코메트리 그녀석": "사이코메트리 그녀석",
    "the school nurse files": "보건교사 안은영",
    "보건교사 안은영": "보건교사 안은영",
    "law school": "로스쿨",
    "로스쿨": "로스쿨",
    "alchemy of souls": "환혼",
    "환혼": "환혼",
    "alchemy of souls light and shadow": "환혼 빛과 그림자",
    "환혼 빛과 그림자": "환혼 빛과 그림자",
    "deaths game": "이재 곧 죽습니다",
    "death s game": "이재 곧 죽습니다",
    "이재 곧 죽습니다": "이재 곧 죽습니다",
    "resident playbook": "언젠가는 슬기로울 전공의생활",
    "언젠가는 슬기로울 전공의생활": "언젠가는 슬기로울 전공의생활",
    "can this love be translated": "이 사랑 통역 되나요",
    "이 사랑 통역 되나요": "이 사랑 통역 되나요",
    "moving": "무빙",
    "무빙": "무빙",
    "hunt": "헌트",
    "헌트": "헌트",
    "sweet home": "스위트홈",
    "스위트홈": "스위트홈",
    "sweet home 2": "스위트홈 2",
    "스위트홈 2": "스위트홈 2",
    "light shop": "조명가게",
    "조명가게": "조명가게",
}


@dataclass
class AuditResult:
    official_work_sync: int
    coverage_readiness: int
    official_titles: list[str]
    local_titles: list[str]
    missing_from_local: list[str]
    extra_in_local: list[str]
    corroborated_extra: list[str]
    unresolved_awards: int
    unresolved_profile: int
    unresolved_sns: int
    verification_queue_items: int
    upcoming_schedule_items: int
    notes: list[str]


def normalize_title(title: str) -> str:
    t = html.unescape(title).strip().lower()
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return TITLE_ALIASES.get(t, t)


def fetch_maa_html(timeout: int = 15) -> str:
    res = requests.get(
        MAA_URL,
        timeout=timeout,
        headers={"User-Agent": "goyoonjung-wiki-audit/1.0"},
    )
    res.raise_for_status()
    return res.text


def is_official_url(url: str) -> bool:
    try:
        host = urlsplit(url).netloc.lower()
    except Exception:
        return False
    if host.startswith("www."):
        host = host[4:]
    return any(host == suffix or host.endswith("." + suffix) for suffix in OFFICIAL_HOST_SUFFIXES)


def extract_maa_titles(page_html: str) -> list[str]:
    titles: list[str] = []
    span_hits = re.findall(r'<span class="ma-history__text">([^<]+)</span>', page_html)
    if not span_hits:
        for raw in re.findall(r"[\"'‘’]([^\"'‘’]{2,120})[\"'‘’]", page_html):
            cleaned = html.unescape(raw).strip()
            if cleaned:
                titles.append(cleaned)
        span_hits = []

    for raw in span_hits:
        cleaned = html.unescape(raw).strip()
        if not cleaned or cleaned == "Drama (pending release)":
            continue

        m = re.search(r"'(.+)'", cleaned)
        if not m:
            m = re.search(r"‘(.+)’", cleaned)
        if not m:
            m = re.search(r'"(.+)"', cleaned)
        if m:
            title = m.group(1).strip()
        else:
            parts = cleaned.split()
            if len(parts) < 2:
                continue
            title = " ".join(parts[:-1]).strip()

        normalized = normalize_title(title)
        if normalized in {"go youn jung", "maa", "ad"}:
            continue
        titles.append(title)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for title in titles:
        key = normalize_title(title)
        if key in seen:
            continue
        seen.add(key)
        out.append(title)
    return out


def parse_local_filmography(md_text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in md_text.splitlines():
        if not line.startswith("|"):
            continue
        cols = [col.strip() for col in line.strip().strip("|").split("|")]
        if len(cols) < 6 or cols[0] == "연도" or set("".join(cols)) <= {"-", ":"}:
            continue
        title = re.sub(r"[*_`]", "", cols[2]).strip()
        if title:
            rows.append({"title": title, "urls": URL_RE.findall(cols[5])})
    return rows


def build_work_page_evidence() -> dict[str, set[str]]:
    evidence: dict[str, set[str]] = {}
    if not WORKS_DIR.exists():
        return evidence
    for path in WORKS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        title = path.stem.replace("-", " ")
        for line in text.splitlines():
            if line.startswith("# "):
                title = line.removeprefix("# ").strip()
                break
            if line.startswith("- 작품:"):
                title = line.split(":", 1)[1].strip()
                break
        key = normalize_title(title)
        urls = set(URL_RE.findall(text))
        if urls:
            evidence.setdefault(key, set()).update(urls)
    return evidence


def read_quality_text() -> str:
    if not QUALITY_MD.exists():
        return ""
    return QUALITY_MD.read_text(encoding="utf-8", errors="ignore")


def count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def count_verification_queue_items() -> int:
    if not QUEUE_MD.exists():
        return 0
    txt = QUEUE_MD.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"- total_items:\s*(\d+)", txt)
    if m:
        return int(m.group(1))
    return len(re.findall(r"^- \[", txt, flags=re.MULTILINE))


def count_upcoming_schedule_items() -> int:
    if not SCHEDULE_MD.exists():
        return 0
    txt = SCHEDULE_MD.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"## 다가오는 일정 \(Upcoming\)(.*?)---", txt, flags=re.S)
    if not m:
        return 0
    block = m.group(1)
    if "(현재 등록된 다가오는 공식 일정이 없습니다.)" in block:
        return 0
    return count_pattern(block, r"^- 날짜/시간:")


def build_audit() -> AuditResult:
    notes: list[str] = []

    local_rows = parse_local_filmography(FILMOGRAPHY_MD.read_text(encoding="utf-8"))
    local_titles = [str(row["title"]) for row in local_rows]
    local_map = {normalize_title(str(row["title"])): str(row["title"]) for row in local_rows}
    local_evidence = {normalize_title(str(row["title"])): set(row["urls"]) for row in local_rows}
    work_page_evidence = build_work_page_evidence()

    official_titles: list[str] = []
    missing_from_local: list[str] = []
    extra_in_local: list[str] = []
    corroborated_extra: list[str] = []

    try:
        official_titles = extract_maa_titles(fetch_maa_html())
        official_map = {normalize_title(title): title for title in official_titles}
        missing_from_local = [official_map[key] for key in sorted(set(official_map) - set(local_map))]
        notes.append("MAA official filmography fetched successfully.")
    except Exception as exc:  # pragma: no cover - network depends on runtime
        notes.append(f"MAA fetch failed: {exc}")
        official_work_sync = 40
    else:
        all_extra_keys = sorted(set(local_map) - set(official_map))
        for key in all_extra_keys:
            evidence_urls = set()
            evidence_urls.update(local_evidence.get(key, set()))
            evidence_urls.update(work_page_evidence.get(key, set()))
            if any(is_official_url(url) for url in evidence_urls):
                corroborated_extra.append(local_map[key])
            else:
                extra_in_local.append(local_map[key])
        official_work_sync = max(
            0,
            100 - (len(missing_from_local) * 20) - (len(corroborated_extra) * 5) - (len(extra_in_local) * 15),
        )

    quality_text = read_quality_text()
    unresolved_awards = count_pattern(quality_text, r"pages/awards\.md:")
    unresolved_profile = count_pattern(quality_text, r"pages/profile\.md:")
    unresolved_sns = count_pattern(quality_text, r"pages/sns\.md:")
    verification_queue_items = count_verification_queue_items()
    upcoming_schedule_items = count_upcoming_schedule_items()

    critical_category_debt = sum(
        1
        for value in (unresolved_awards, unresolved_profile, unresolved_sns)
        if value > 0
    )
    queue_penalty = min(25, verification_queue_items // 4)
    debt_penalty = critical_category_debt * 8 + queue_penalty
    coverage_readiness = max(0, official_work_sync - debt_penalty)

    if corroborated_extra:
        notes.append("Some works are absent from MAA but corroborated by other official platform pages.")
    if extra_in_local:
        notes.append("Local filmography has titles not confirmed by the current MAA page.")
    if missing_from_local:
        notes.append("Local filmography is missing at least one title currently listed by MAA.")
    if unresolved_awards:
        notes.append("Awards page still contains unresolved official-proof debt.")
    if unresolved_sns:
        notes.append("SNS page still contains an unresolved official account.")

    return AuditResult(
        official_work_sync=official_work_sync,
        coverage_readiness=coverage_readiness,
        official_titles=official_titles,
        local_titles=local_titles,
        missing_from_local=missing_from_local,
        extra_in_local=extra_in_local,
        corroborated_extra=corroborated_extra,
        unresolved_awards=unresolved_awards,
        unresolved_profile=unresolved_profile,
        unresolved_sns=unresolved_sns,
        verification_queue_items=verification_queue_items,
        upcoming_schedule_items=upcoming_schedule_items,
        notes=notes,
    )


def write_report(result: AuditResult) -> None:
    updated = seoul_timestamp_str()
    lines = [
        "# Official Coverage Audit (auto)",
        "",
        f"> Updated: {updated} (Asia/Seoul)",
        "",
        "## Scores",
        f"- official_work_sync: **{result.official_work_sync}/100**",
        f"- coverage_readiness: **{result.coverage_readiness}/100**",
        "",
        "## Official Filmography Sync",
        f"- official_titles: {len(result.official_titles)}",
        f"- local_titles: {len(result.local_titles)}",
        f"- missing_from_local: {len(result.missing_from_local)}",
        f"- corroborated_extra: {len(result.corroborated_extra)}",
        f"- extra_in_local: {len(result.extra_in_local)}",
        "",
    ]

    if result.missing_from_local:
        lines.append("### Missing From Local")
        lines.extend(f"- {title}" for title in result.missing_from_local)
        lines.append("")

    if result.corroborated_extra:
        lines.append("### Corroborated Extra")
        lines.extend(f"- {title}" for title in result.corroborated_extra)
        lines.append("")

    if result.extra_in_local:
        lines.append("### Extra In Local")
        lines.extend(f"- {title}" for title in result.extra_in_local)
        lines.append("")

    lines += [
        "## Critical Verification Debt",
        f"- unresolved_awards: {result.unresolved_awards}",
        f"- unresolved_profile: {result.unresolved_profile}",
        f"- unresolved_sns: {result.unresolved_sns}",
        f"- verification_queue_items: {result.verification_queue_items}",
        "",
        "## Future Coverage",
        f"- upcoming_schedule_items: {result.upcoming_schedule_items}",
        "",
        "## Notes",
    ]

    if result.notes:
        lines.extend(f"- {note}" for note in result.notes)
    else:
        lines.append("- No noteworthy findings.")

    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    result = build_audit()
    write_report(result)
    print(
        "official_coverage_audit: "
        f"coverage_readiness={result.coverage_readiness} "
        f"official_work_sync={result.official_work_sync}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

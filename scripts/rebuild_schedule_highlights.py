#!/usr/bin/env python3
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path("/Users/zenith/Documents/goyoonjung-wiki")
SCHEDULE = BASE / "pages" / "schedule.md"

START = "<!-- AUTO-SCHEDULE-HIGHLIGHTS:START -->"
END = "<!-- AUTO-SCHEDULE-HIGHLIGHTS:END -->"
TZ_NAME = "Asia/Seoul"

DATE_RE = re.compile(r"^- 날짜/시간:\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?")
TITLE_RE = re.compile(r"^- 제목:\s*(.*)")
TYPE_RE = re.compile(r"^- 구분:\s*(.*)")
TARGET_RE = re.compile(r"^- 대상:\s*(.*)")
STATUS_RE = re.compile(r"^- 상태:\s*(.*)")
LINK_RE = re.compile(r"^- 링크\(공식/원문\):\s*(.*)")
ID_RE = re.compile(r"^- id:\s*(.*)")


def parse_items(text: str):
    """Parse schedule items from the Upcoming section using the existing template lines."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    in_upcoming = False
    cur = {}
    items = []

    def flush():
        nonlocal cur
        if cur.get("date"):
            items.append(cur)
        cur = {}

    for ln in lines:
        if ln.startswith("## 다가오는 일정"):
            in_upcoming = True
            continue
        if ln.startswith("## 지난 일정"):
            if in_upcoming:
                flush()
            in_upcoming = False
        if not in_upcoming:
            continue

        m = DATE_RE.match(ln)
        if m:
            flush()
            cur["date"] = m.group(1)
            cur["time"] = m.group(2)
            continue

        for rx, key in [
            (TYPE_RE, "type"),
            (TITLE_RE, "title"),
            (TARGET_RE, "target"),
            (STATUS_RE, "status"),
            (LINK_RE, "link"),
            (ID_RE, "id"),
        ]:
            mm = rx.match(ln)
            if mm:
                cur[key] = mm.group(1).strip()
                break

    flush()
    return items


def within_7_days(date_str: str, today: datetime):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return False
    return today.date() <= d.date() <= (today + timedelta(days=7)).date()


def build_block(items, today: datetime):
    header = [
        "## 오늘/이번주 일정 (자동)",
        f"> 기준: {today.strftime('%Y-%m-%d')} ~ {(today + timedelta(days=7)).strftime('%Y-%m-%d')} ({TZ_NAME})",
        "",
    ]

    if not items:
        header.append("- (7일 내 등록된 공식 일정이 없습니다.)")
        return "\n".join(header).rstrip()

    # sort by date then time
    def key(it):
        t = it.get("time") or "99:99"
        return (it.get("date"), t)

    out = header[:]
    for it in sorted(items, key=key):
        date = it.get("date")
        time = it.get("time")
        when = f"{date} {time}" if time else date
        title = it.get("title") or "(제목 미상)"
        typ = it.get("type") or ""
        status = it.get("status") or ""
        link = it.get("link") or it.get("id") or ""
        meta = " · ".join([x for x in [typ, status] if x])
        if link:
            if meta:
                out.append(f"- **{when}** — {title} ({meta}) — {link}")
            else:
                out.append(f"- **{when}** — {title} — {link}")
        else:
            if meta:
                out.append(f"- **{when}** — {title} ({meta})")
            else:
                out.append(f"- **{when}** — {title}")

    return "\n".join(out).rstrip()


def main():
    if not SCHEDULE.exists():
        print("MISSING")
        return

    text = SCHEDULE.read_text(encoding="utf-8")

    # Asia/Seoul day boundaries are handled by the scheduler; here we use local time.
    today = datetime.now()

    items = parse_items(text)
    week_items = [it for it in items if within_7_days(it["date"], today)]

    block = "\n".join([START, build_block(week_items, today), END])

    if START in text and END in text:
        new_text = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
    else:
        # Insert after title and intro lines (after first blank line)
        parts = text.split("\n\n", 1)
        if len(parts) == 2:
            new_text = parts[0] + "\n\n" + block + "\n\n" + parts[1]
        else:
            new_text = text.rstrip() + "\n\n" + block + "\n"

    if new_text != text:
        SCHEDULE.write_text(new_text, encoding="utf-8")
        print("CHANGED")
    else:
        print("NO_CHANGES")


if __name__ == "__main__":
    main()

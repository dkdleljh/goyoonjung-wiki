#!/usr/bin/env python3
"""Generate Mermaid Timeline from Schedule.
- Reads `pages/schedule.md`
- Extracts "Upcoming" and "Past" events.
- Generates `pages/timeline.md` with a Mermaid chart.
"""
# noqa: E701

from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCHEDULE_MD = BASE / 'pages' / 'schedule.md'
TIMELINE_MD = BASE / 'pages' / 'timeline.md'

def parse_date(date_str):
    # Handles YYYY-MM-DD
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except (ValueError, TypeError, AttributeError):
        return None

def extract_events():
    if not SCHEDULE_MD.exists():
        return []

    content = SCHEDULE_MD.read_text(encoding='utf-8')
    events = []

    # Simple regex to find "- 날짜/시간: YYYY-MM-DD ... - 제목: ..." blocks
    # This is a bit loose, but fits the markdown structure

    # Split by "- 날짜/시간:" to isolate entries
    for chunk in content.split("- 날짜/시간:")[1:]:
        lines = chunk.strip().splitlines()
        if not lines: continue

        date_line = lines[0].split("(")[0].strip() # Remove (Estimated)

        title = "Unknown"
        category = "Event"

        for line in lines:
            if line.strip().startswith("- 제목:"):
                title = line.split(":", 1)[1].strip()
            if line.strip().startswith("- 구분:"):
                category = line.split(":", 1)[1].strip()

        dt = parse_date(date_line)
        if dt:
            events.append({
                "date": dt,
                "title": title,
                "category": category
            })

    # Sort by date
    events.sort(key=lambda x: x['date'])
    return events

def generate_mermaid(events):
    # Limit to last 5 and next 5 for cleanliness? Or yearly sections.
    # Let's do a "Yearly" timeline for the current and next year.

    # Show from 2019 (Debut) onwards
    target_events = [e for e in events if e['date'].year >= 2019]

    mermaid = "```mermaid\ntimeline\n    title Go Yoon-jung Activity Timeline\n"

    # Group by Year-Month
    grouped = {}
    for e in target_events:
        ym = e['date'].strftime("%Y-%m")
        if ym not in grouped: grouped[ym] = []
        # Escape title for mermaid
        safe_title = e['title'].replace(":", " ").replace("(", "").replace(")", "").replace('"', "")
        if len(safe_title) > 20: safe_title = safe_title[:20] + ".."
        grouped[ym].append(safe_title)

    sorted_ym = sorted(grouped.keys())

    for ym in sorted_ym:
        mermaid += f"    {ym} : " + " : ".join(grouped[ym]) + "\n"

    mermaid += "```\n"
    return mermaid

def main():
    print("Generating Timeline...")
    events = extract_events()
    print(f"Found {len(events)} events.")

    if not events:
        print("No events to visualize.")
        return

    mermaid_chart = generate_mermaid(events)

    doc = f"""# Activity Timeline
> Auto-generated from schedule.md

{mermaid_chart}

[Back to Schedule](schedule.md)
"""

    TIMELINE_MD.write_text(doc, encoding='utf-8')
    print(f"Generated {TIMELINE_MD}")

if __name__ == "__main__":
    main()

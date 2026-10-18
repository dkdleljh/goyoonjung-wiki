"""Resume official magazine pagination without inventing historical completeness."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from auto_collect_magazine_rss import (
    CONF_PATH,
    EDITORIAL_MD,
    INTERVIEWS_MD,
    apply_entries,
    collect_feed,
    make_entry,
    parse_simple_yml,
)
from official_evidence import BASE, load
from source_transport import atomic_write, save_report


def main() -> int:
    target = BASE/'data/reports/archive-progress.json'
    state = load(target, {})
    feeds = parse_simple_yml(CONF_PATH.read_text())['feeds']
    now = datetime.now(UTC)
    eligible = [f for f in feeds if state.get(f['name'], {}).get('next_scan', '') <= now.isoformat()]
    eligible.sort(key=lambda f: state.get(f['name'], {}).get('checked_at', ''))
    reports = []
    for feed in eligible[:3]:
        old = state.get(feed['name'], {})
        page = old.get('page', 1)
        rows, report = collect_feed({**feed, 'page': page}, '고윤정')
        report['scope'] = f'historical pagination page {page}'
        if report['status'] == 'success':
            entries = [make_entry(row, feed) for row in rows]
            added = apply_entries(EDITORIAL_MD, [e for e in entries if e.target == 'editorial'])
            added += apply_entries(INTERVIEWS_MD, [e for e in entries if e.target == 'interviews'])
            repeated = report.get('page_fingerprint') in old.get('fingerprints', [])
            end = report['fetched'] == 0 or repeated
            state[feed['name']] = {'page': 1 if end else page + 1, 'checked_at': now.isoformat(),
                'next_scan': (now + timedelta(days=7)).isoformat() if end else now.isoformat(),
                'status': 'pagination_repeated' if repeated else 'end_of_results' if end else 'in_progress',
                'fingerprints': [] if end else (old.get('fingerprints', []) + [report['page_fingerprint']])[-500:],
                'items_added': old.get('items_added', 0) + added,
                'years_observed': sorted(set(old.get('years_observed', []) + [e.year for e in entries if e.year])),
                'coverage': '검색으로 관측한 범위이며 과거 전체 수집 완료를 의미하지 않음'}
        else:
            state[feed['name']] = {**old, 'page': page, 'checked_at': now.isoformat(), 'status': 'retry_pending',
                                  'next_scan': (now + timedelta(hours=1)).isoformat()}
        reports.append(report)
        atomic_write(target, json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    if reports:
        save_report('archive', reports)
    return int(any(r['status'] != 'success' for r in reports))


if __name__ == '__main__':
    raise SystemExit(main())

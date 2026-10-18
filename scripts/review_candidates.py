"""Consume news candidates as attributed links; metadata is not factual confirmation."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import db_manager
from collector_io import append_news_lines
from domain_policy import load_policy
from official_evidence import BASE, fetch_document, load
from relevance import is_relevant
from source_transport import atomic_write


def main() -> int:
    db_manager.init_db()
    state_path = BASE/'data/reports/candidate-reviews.json'
    state = load(state_path, {})
    policy = load_policy()
    now = datetime.now(UTC)
    candidates = [dict(row) for row in db_manager.list_candidates(limit=1000)]
    due = [row for row in candidates if policy.grade_for_url(row['url']) in {'S', 'A'} and state.get(row['norm_url'], {}).get('next_check', '') <= now.isoformat()]
    due.sort(key=lambda row: state.get(row['norm_url'], {}).get('checked_at', ''))
    page = BASE/'pages/reviewed-news.md'
    if not page.exists():
        atomic_write(page, '# 원문 확인 뉴스 링크\n\n제목·인물 관련성과 원문 접근을 확인한 보도입니다. 보도 내용 전체를 공식 사실로 확정했다는 뜻은 아닙니다.\n\n')
    for row in due[:6]:
        url = row['url']
        if policy.grade_for_url(url) not in {'S', 'A'}:
            continue
        source = {'domain': (urlsplit(url).hostname or '').removeprefix('www.'), 'category':'news', 'first_party':False}
        old = state.get(row['norm_url'], {})
        try:
            result = fetch_document(url, source, old.get('metadata'))
            relevant = is_relevant(result['title'], url, row['source'], result['excerpt'])
            status = 'metadata_verified' if relevant else 'irrelevant'
            if relevant:
                title = result['title'].replace('[', '［').replace(']', '］').replace('\n', ' ')
                append_news_lines(page, [f'- [{title}]({url}) · {row["source"]} · 내용은 원문 보도 기준'])
            with db_manager.get_db_connection() as con:
                con.execute('UPDATE url_candidates SET lane=? WHERE norm_url=?', ('reviewed' if relevant else 'discard', row['norm_url']))
            state[row['norm_url']] = {'status':status, 'checked_at':now.isoformat(), 'first_seen_at':row['first_seen_at'],
                'next_check':(now+timedelta(days=7)).isoformat(), 'metadata':result}
        except Exception as exc:
            state[row['norm_url']] = {**old, 'status':'retry_pending', 'checked_at':now.isoformat(),
                'next_check':(now+timedelta(hours=6)).isoformat(), 'error':str(exc)[:160]}
        atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    print(f'candidate reviews: {len(state)} recorded')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

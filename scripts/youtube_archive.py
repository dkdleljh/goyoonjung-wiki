"""Paginate public official uploads metadata; never download video or audio."""
from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from auto_collect_youtube_feeds import CONF_PATH, parse_simple_yml
from collector_io import append_news_lines
from official_evidence import ACTOR, BASE, load
from source_transport import atomic_write
from yt_dlp import YoutubeDL


def main() -> int:
    target = BASE/'data/reports/youtube-archive-progress.json'
    state = load(target, {})
    now = datetime.now(UTC)
    feeds = parse_simple_yml(CONF_PATH.read_text())['feeds']
    due = [feed for feed in feeds if state.get(feed['name'], {}).get('next_scan', '') <= now.isoformat()]
    if not due:
        return 0
    feed = min(due, key=lambda f: state.get(f['name'], {}).get('checked_at', ''))
    old = state.get(feed['name'], {})
    start = old.get('next_item', 1)
    channel = parse_qs(urlsplit(feed['url']).query)['channel_id'][0]
    options = {'extract_flat': True, 'skip_download': True, 'quiet': True, 'no_warnings': True,
               'playliststart': start, 'playlistend': start+99, 'socket_timeout': 15,
               'retries': 1, 'extractor_retries': 1, 'ignoreerrors': False, 'noplaylist': False}
    try:
        with YoutubeDL(options) as client:
            data = client.extract_info('https://www.youtube.com/playlist?list=UU'+channel[2:], download=False)
        if data.get('channel_id') != channel:
            raise ValueError('Playlist owner is not the configured channel')
        entries = list(data.get('entries', []))
        lines = []
        for item in entries:
            if not item or not ACTOR.search(item.get('title', '')) or not re.fullmatch(r'[\w-]{11}', item.get('id', '')):
                continue
            title = item['title'].replace('[', '［').replace(']', '］').replace('\n', ' ')
            lines.append(f'- [YouTube/{feed["name"]}] [{title}](https://www.youtube.com/watch?v={item["id"]}) · 과거 업로드, 게시일 확인 필요')
        page = BASE/'pages/youtube-archive.md'
        if not page.exists():
            atomic_write(page, '# 공식 채널 과거 영상\n\n공식 채널 공개 업로드 목록에서 제목과 링크만 수집합니다.\n\n')
        append_news_lines(page, lines)
        state[feed['name']] = {'checked_at': now.isoformat(), 'next_item': start + len(entries) if entries else 1,
            'status': 'in_progress' if entries else 'end_of_results', 'last_batch_size': len(entries),
            'next_scan': now.isoformat() if entries else (now+timedelta(days=7)).isoformat(),
            'matched': old.get('matched', 0)+len(lines)}
        rc = 0
    except Exception as exc:
        state[feed['name']] = {**old, 'checked_at': now.isoformat(), 'status': 'retry_pending',
            'error': str(exc)[:200], 'next_scan': (now+timedelta(hours=1)).isoformat()}
        rc = 1
    atomic_write(target, json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(state[feed['name']], ensure_ascii=False))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())

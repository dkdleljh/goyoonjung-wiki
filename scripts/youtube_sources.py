"""Validate official channel feeds, falling back to their public uploads playlist."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlsplit

from source_transport import SourceError, request

ATOM = '{http://www.w3.org/2005/Atom}'
YT = '{http://www.youtube.com/xml/schemas/2015}'


def find_nodes(value, key):
    if isinstance(value, dict):
        if key in value:
            yield value[key]
        for child in value.values():
            yield from find_nodes(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from find_nodes(child, key)


def parse_atom(data: bytes, channel_id: str | None) -> list[dict]:
    if not data:
        raise SourceError('Empty YouTube feed', 'network', True)
    root = ET.fromstring(data)
    if root.tag != ATOM + 'feed':
        raise SourceError('Expected YouTube Atom feed, received another document')
    if channel_id:
        # YouTube currently omits the UC prefix in yt:channelId on some feeds.
        # Also verify the full author URI, so normalization cannot mix channels.
        author_uri = root.findtext(ATOM + 'author/' + ATOM + 'uri')
        if root.findtext(YT + 'channelId') not in {channel_id, channel_id[2:]} or author_uri != f'https://www.youtube.com/channel/{channel_id}':
            raise SourceError('YouTube feed channel identity mismatch')
    rows = []
    for entry in root.findall(ATOM + 'entry')[:15]:
        title = entry.findtext(ATOM + 'title')
        video_id = entry.findtext(YT + 'videoId')
        if not title or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id or ''):
            raise SourceError('YouTube entry missing title or valid video ID')
        rows.append({'title': title, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                     'date': entry.findtext(ATOM + 'published', '')})
    return rows


def parse_uploads(html: bytes, channel_id: str) -> list[dict]:
    match = re.search(r'(?:var\s+ytInitialData|window\["ytInitialData"\])\s*=\s*', html.decode('utf-8'))
    if not match:
        raise SourceError('Public uploads data missing; consent/error page is not success')
    data = json.JSONDecoder().raw_decode(html.decode('utf-8')[match.end():])[0]
    playlist_id = 'UU' + channel_id[2:]
    headers = list(find_nodes(data.get('header', {}), 'playlistHeaderRenderer'))
    if not any(header.get('playlistId') == playlist_id and
               header.get('ownerEndpoint', {}).get('browseEndpoint', {}).get('browseId') == channel_id
               for header in headers):
        raise SourceError('Uploads playlist owner/identity mismatch')
    # Only selected playlist contents: never sidebar recommendations or menu actions.
    tabs = [tab['content'] for tab in find_nodes(data.get('contents', {}), 'tabRenderer')
            if tab.get('selected') and 'content' in tab]
    rows = {}
    for tab in tabs:
        for video in find_nodes(tab, 'playlistVideoRenderer'):
            title_data = video.get('title', {})
            title = title_data.get('simpleText') or ''.join(r.get('text', '') for r in title_data.get('runs', []))
            rows[video.get('videoId')] = title
        for video in find_nodes(tab, 'lockupViewModel'):
            if video.get('contentType') != 'LOCKUP_CONTENT_TYPE_VIDEO':
                continue
            rows[video.get('contentId')] = video.get('metadata', {}).get('lockupMetadataViewModel', {}).get('title', {}).get('content')
    if not rows:
        raise SourceError('Uploads playlist contains no recognized videos; needs review')
    result = []
    for video_id, title in rows.items():
        if not title or not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id or ''):
            raise SourceError('Uploads item missing a title or valid video ID')
        # Relative dates are not fabricated into absolute publication dates.
        result.append({'title': title, 'url': 'https://www.youtube.com/watch?v=' + video_id, 'date': ''})
    return result


def collect_source(feed: dict, fetch=request) -> tuple[list[dict], dict]:
    url = feed['url']
    channel_id = parse_qs(urlsplit(url).query).get('channel_id', [None])[0]
    report = {'name': feed['name'], 'url': url, 'scope': 'recent_uploads_feed', 'status': 'failed'}
    try:
        rows = parse_atom(fetch(url), channel_id)
        report.update(status='success', fetched=len(rows))
        return rows, report
    except (SourceError, ET.ParseError, ValueError) as exc:
        first_error = str(exc)
        # A denied request is not a reason to bypass an access restriction.
        if 'HTTP 403' in first_error or not channel_id or not re.fullmatch(r'UC[A-Za-z0-9_-]{22}', channel_id):
            report.update(error=first_error, kind=getattr(exc, 'kind', 'parse'), retryable=getattr(exc, 'retryable', False))
            return [], report
    playlist_url = 'https://www.youtube.com/playlist?list=UU' + channel_id[2:]
    try:
        rows = parse_uploads(fetch(playlist_url), channel_id)
        report.update(status='success', fetched=len(rows), url=playlist_url,
                      scope='recent_uploads_playlist', warnings=[f'RSS unavailable: {first_error}; verified official uploads playlist instead'])
        return rows, report
    except (SourceError, ValueError, KeyError, TypeError) as exc:
        report.update(error=f'RSS: {first_error}; uploads playlist: {exc}',
                      kind=getattr(exc, 'kind', 'parse'), retryable=getattr(exc, 'retryable', False))
        return [], report

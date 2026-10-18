"""Measured runs and explicit coverage limits, independent of editorial scores."""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from source_transport import atomic_write

BASE = Path(__file__).resolve().parents[1]
HISTORY = BASE / 'data/reports/run-history.json'


def read(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def record(kind: str, started: float, rc: int, steps: list | None = None) -> dict:
    now = datetime.now(UTC)
    rows = read(HISTORY, [])
    row = {'kind': kind, 'executor': 'github-actions' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'primary', 'started_at': datetime.fromtimestamp(started, UTC).isoformat(),
           'timestamp': now.isoformat(), 'duration_seconds': round(now.timestamp() - started, 2),
           'status': 'success' if rc == 0 else 'partial' if rc == 1 else 'failure', 'steps': steps or []}
    rows.append(row)
    atomic_write(HISTORY, json.dumps(rows[-2000:], ensure_ascii=False, indent=2) + '\n')
    if kind == 'fast':
        atomic_write(BASE / 'data/reports/heartbeat.json', json.dumps(row, ensure_ascii=False, indent=2) + '\n')
    return row


def report() -> dict:
    rows = read(HISTORY, [])
    durations = sorted(r['duration_seconds'] for r in rows)
    fast = [r for r in rows if r['kind'] == 'fast']
    checkpoints = read(BASE / 'data/reports/source-checkpoints.json', {})
    ages = [(datetime.now(UTC) - datetime.fromisoformat(r['last_success'])).total_seconds() / 60
            for r in checkpoints.values() if r.get('last_success')]
    evidence = read(BASE/'data/facts/evidence.json', [])
    reviews = read(BASE/'data/reports/candidate-reviews.json', {})
    observations = evidence + [r['metadata'] for r in reviews.values() if r.get('metadata')]
    lags = []
    for item in observations:
        try:
            published = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
            discovered = datetime.fromisoformat(item.get('first_seen', item['collected_at']))
            if published.tzinfo is None:
                continue
            lag = (discovered-published).total_seconds()
            if lag >= 0:
                lags.append(lag)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    lags.sort()
    data = {'publication_to_first_fetch_samples':len(lags),
            'publication_to_first_fetch_p50_seconds':lags[len(lags)//2] if lags else None,
            'publication_to_first_fetch_p95_seconds':lags[max(0,math.ceil(len(lags)*.95)-1)] if lags else None,
            'sample_count': len(rows), 'avg_execution_seconds': round(mean(durations), 2) if durations else None,
            'execution_p95_seconds': durations[max(0, math.ceil(len(durations)*.95)-1)] if durations else None,
            'fast_run_success_percent': round(100*sum(r['status'] == 'success' for r in fast)/len(fast), 2) if fast else None,
            'oldest_source_success_age_minutes': round(max(ages), 1) if ages else None,
            'monitored_sources': len(checkpoints), 'recall': None, 'precision': None,
            'limits': '게시부터 최초 조회 지연은 날짜가 확인된 원문 표본만 계산하며 과거 자료도 포함합니다. 정확도·전체 자료 대비 수집률은 독립 정답 집합이 없어 미측정. 실행 성공률은 가동률이나 사실 정확도가 아님.'}
    atomic_write(BASE / 'data/reports/measured-quality.json', json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 자동 수집 실측', '', data['limits'], '', '| 지표 | 실측 |', '|---|---|']
    lines += [f'| {k} | {v if v is not None else "미측정"} |' for k, v in data.items() if k != 'limits']
    atomic_write(BASE / 'pages/automation-measurements.md', '\n'.join(lines)+'\n')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind')
    parser.add_argument('--started', type=float)
    parser.add_argument('--rc', type=int, default=0)
    args = parser.parse_args()
    if args.kind:
        record(args.kind, args.started, args.rc)
    print(json.dumps(report(), ensure_ascii=False))

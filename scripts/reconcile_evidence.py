"""Turn supported, nonconflicting claims into work pages; keep uncertainty visible."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import UTC, datetime

from official_evidence import BASE, EVIDENCE, load
from source_transport import atomic_write


def normalize(value: str) -> str:
    return re.sub(r'[^0-9a-z가-힣]', '', value.lower())


def audit_claims(evidence: list[dict]) -> tuple[list, list]:
    groups = defaultdict(list)
    for source in evidence:
        for claim in source.get('claims', []):
            groups[(normalize(claim['entity']), claim['field'])].append({**claim,
                'url': source['url'], 'publisher': source['publisher'],
                'first_party': source.get('first_party', False), 'collected_at': source['collected_at'],
                'published_at': source.get('published_at'), 'source_hash': source['content_hash']})
    accepted, conflicts = [], []
    for (entity, field), rows in groups.items():
        values = {row['value'] for row in rows}
        if len(values) > 1:
            conflicts.append({'entity': entity, 'field': field, 'values': sorted(values), 'evidence': rows})
        elif any(row['first_party'] for row in rows):
            accepted.append({**rows[0], 'evidence': rows, 'status': 'verified'})
    return accepted, conflicts


def main() -> int:
    evidence = load(EVIDENCE, [])
    accepted, conflicts = audit_claims(evidence)
    atomic_write(BASE/'data/facts/claim-conflicts.json', json.dumps(conflicts, ensure_ascii=False, indent=2)+'\n')
    atomic_write(BASE/'data/facts/verified-claims.json', json.dumps(accepted, ensure_ascii=False, indent=2)+'\n')
    registry = load(BASE/'config/work-registry.json', []) + load(BASE/'data/facts/discovered-works.json', [])
    known = {normalize(alias): row for row in registry for alias in row.get('aliases', [row['title']])}
    discovered = load(BASE/'data/facts/discovered-works.json', [])
    overrides = {}
    filmography = BASE/'pages/filmography.md'
    text = filmography.read_text()
    for claim in accepted:
        key = normalize(claim['entity'])
        row = known.get(key)
        if row is None and claim['field'] == 'cast':
            title = re.sub(r'[\n\r|<>\[\]]', '', claim['entity']).strip()
            if not title:
                continue
            slug = 'work-'+hashlib.sha256(key.encode()).hexdigest()[:12]
            row = {'id': slug, 'title': title, 'slug': slug, 'aliases': [title], 'role': '미공개', 'platform': '미공개'}
            discovered.append(row)
            known[key] = row
            page = BASE/'pages/works'/f'{slug}.md'
            # Idempotent creation: never replace an existing editorial page.
            if not page.exists():
                atomic_write(page, f'# {title}\n\n## 작품 정보\n\n- 출연: 고윤정\n- 상태: 출연 확정, 공개일 미정\n- 배역: 미공개\n\n## 출처\n\n- [공식 출연 발표]({claim["url"]})\n')
            if '\n## 자동 확인 작품\n' not in text:
                text += '\n## 자동 확인 작품\n\n| 연도 | 플랫폼/방송사 | 작품 | 역할 | 비고 | 근거 |\n|---|---|---|---|---|---|\n'
            if f'| {title} |' not in text:
                text += f'| 미정 | 미공개 | {title} | 미공개 | 출연 확정·공개일 미정 | [공식 발표]({claim["url"]}) |\n'
        if row:
            item = overrides.setdefault(row['title'], {'page': f'pages/works/{row["slug"]}.md', 'sources': []})
            item['sources'].append(claim['url'])
            if claim['field'] == 'cast':
                item.setdefault('status', 'confirmed')
            if claim['field'] == 'release_date':
                date = claim['value']
                item.update(release_date=date, status='released' if date <= datetime.now(UTC).date().isoformat() else 'scheduled')
    # An automatically added cast claim can be withdrawn or disappear on revision.
    # Preserve its history, but stop presenting the old assertion as confirmed.
    accepted_cast = {normalize(c['entity']) for c in accepted if c['field'] == 'cast'}
    for row in discovered:
        if normalize(row['title']) not in accepted_cast:
            overrides[row['title']] = {'page':f"pages/works/{row['slug']}.md", 'status':'review_required', 'sources':[]}
        status = overrides.get(row['title'], {}).get('status', 'review_required')
        note = {'confirmed':'출연 확정·공개일 미정', 'scheduled':'공개 예정', 'released':'공개 완료',
                'review_required':'근거 변경·확인 필요'}.get(status, '확인 필요')
        lines = []
        for line in text.splitlines():
            cells = line.split('|')
            if len(cells) >= 8 and cells[3].strip() == row['title']:
                cells[5] = ' '+note+' '
                date = overrides.get(row['title'], {}).get('release_date')
                if date:
                    cells[1] = ' '+date[:4]+' '
                line = '|'.join(cells)
            lines.append(line)
        text = '\n'.join(lines)+'\n'
        path = BASE/'pages/works'/f"{row['slug']}.md"
        if path.exists():
            content = re.sub(r'^- 상태:.*$', '- 상태: '+note, path.read_text(), flags=re.M)
            atomic_write(path, content)
    atomic_write(filmography, text)
    atomic_write(BASE/'data/facts/discovered-works.json', json.dumps(discovered, ensure_ascii=False, indent=2)+'\n')
    atomic_write(BASE/'data/facts/work-evidence-status.json', json.dumps(overrides, ensure_ascii=False, indent=2)+'\n')
    queue = [{'url': e['url'], 'title': e['title'], 'first_seen': e.get('first_seen', e['collected_at']),
              'status': 'verified' if any(c['url'] == e['url'] for c in accepted) else 'needs_evidence',
              'reason': '원문에서 개별 사실을 확정할 구조화 근거가 부족함'} for e in evidence]
    atomic_write(BASE/'data/reports/evidence-queue.json', json.dumps(queue, ensure_ascii=False, indent=2)+'\n')
    print(f'evidence: verified={len(accepted)} conflicts={len(conflicts)} queue={len(queue)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

BASE = Path('/home/zenith/바탕화면/goyoonjung-wiki')
PAGES = BASE / 'pages'

BACKLOG = PAGES / 'namu-backlog.md'
LINT = PAGES / 'lint-report.md'
OUT = PAGES / 'progress.md'


def parse_checkboxes(md: str):
    items = []
    for line in md.splitlines():
        m = re.match(r'^- \[( |x)\] (.+)$', line.strip())
        if m:
            done = (m.group(1) == 'x')
            items.append((done, m.group(2).strip()))
    return items


def extract_lint_summary(md: str):
    # crude extraction: take the first section until a blank line after coverage block
    lines = md.splitlines()
    out = []
    take = False
    for ln in lines:
        if ln.strip() == '## 0) 커버리지(요약)':
            take = True
            out.append(ln)
            continue
        if take:
            out.append(ln)
            # stop when next section starts
            if ln.startswith('## ') and ln.strip() != '## 0) 커버리지(요약)':
                out.pop()  # remove the next header
                break
    return '\n'.join(out).strip()


def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    backlog_text = BACKLOG.read_text(encoding='utf-8') if BACKLOG.exists() else ''
    items = parse_checkboxes(backlog_text)
    total = len(items)
    done = sum(1 for d, _ in items if d)
    pct = (done / total * 100.0) if total else 0.0

    lint_text = LINT.read_text(encoding='utf-8') if LINT.exists() else ''
    lint_snip = extract_lint_summary(lint_text)

    lines = []
    lines.append('# 완성도 대시보드')
    lines.append('')
    lines.append(f'> 갱신: {now} (Asia/Seoul)')
    lines.append('')
    lines.append('## 1) 백로그 진행률(과거 이력 보강)')
    lines.append('')
    lines.append(f'- 완료: **{done}/{total}** (**{pct:.1f}%**)')
    lines.append('')
    if items:
        lines.append('### 항목')
        for d, title in items:
            lines.append(f"- [{'x' if d else ' '}] {title}")
        lines.append('')

    if lint_snip:
        lines.append('## 2) 커버리지(요약)')
        lines.append('')
        lines.append(lint_snip)
        lines.append('')

    lines.append('## 3) 권장 운영')
    lines.append('')
    lines.append('- 매일: 백로그 1개 전진(공식 링크 확보 → 해당 페이지 착지)')
    lines.append('- 주간: 링크 건강검진(link-health) + 린트 리포트 High 우선 처리')
    lines.append('')

    OUT.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

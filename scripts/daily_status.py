"""Report a completed daily run separately from optional source warnings."""
import json
from datetime import UTC, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OPTIONAL = {'RC_COLLECT', 'RC_GNEWS_SITES', 'RC_GNEWS_QUERIES', 'RC_MAG_RSS',
            'RC_PORTAL_NEWS', 'RC_AGENCY', 'RC_ENCY', 'RC_VISUAL', 'RC_LINK',
            'RC_AWARD_PROOF', 'RC_AWARD_PROOF_AUTO', 'RC_YT_DATES', 'RC_ENDO_DATES',
            'RC_INT_SUM', 'RC_GNEWS_I18N'}


def classify(row):
    errors, warnings = [], []
    age = (datetime.now(UTC) - datetime.fromisoformat(row['timestamp'])).total_seconds()
    if not -300 <= age <= 8 * 3600:
        errors.append('Daily result is stale or future-dated')
    if row['status'] not in {'success', 'partial'}:
        errors.append('Daily execution did not complete')
    for step in row.get('steps', []):
        rc = step['returncode']
        if rc:
            (warnings if step['name'] in OPTIONAL and rc == 1 else errors).append(f"{step['name']} exited {rc}")
    if row['status'] == 'partial' and not errors and not warnings:
        errors.append('Partial result without step diagnostics')
    return {'status': 'failure' if errors else 'partial' if warnings else 'success', 'errors': errors, 'warnings': warnings}


def main():
    try:
        row = json.loads((BASE/'data/reports/daily-status.json').read_text())
        result = classify(row)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {'status': 'failure', 'errors': [str(exc)], 'warnings': []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())

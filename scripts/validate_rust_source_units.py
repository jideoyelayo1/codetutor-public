"""Validate bounded source-unit claims against current compiler receipts.

This checks evidence consistency, not teaching quality or exhaustive coverage.
"""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate(root=ROOT):
    rules = json.loads((root / 'scripts/rust_source_units.json').read_text())
    receipt = json.loads((root / 'docs/rust-guide-validation.json').read_text())
    if receipt['selectedLessons'] is not None or receipt['failed']:
        raise ValueError('A passing full Rust guide receipt is required')
    for path in ('CodingTeacher/curriculum.json', 'scripts/rust_guide_content.json'):
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if receipt.get('inputSHA256', {}).get(path) != actual:
            raise ValueError('Stale or unbound compiler receipt: ' + path)
    audit = json.loads((root / 'docs/offline-rust-coverage.json').read_text())
    pages = {p['id']: p for d in audit['documents'] for p in d['pages']}
    lessons = {l['id'] for l in json.loads((root / 'CodingTeacher/curriculum.json').read_text())['lessons']}
    checks = {(c['id'], c['variant']): c for c in receipt['cases']}
    seen = set()
    for source in rules['sources']:
        page = pages[source['pageID']]
        if page['originalSHA256'] != source['originalSHA256']:
            raise ValueError('Source edition changed: ' + source['pageID'])
        anchors = {h['anchor'] for h in page['headings']}
        if source['fullyAdapted']:
            raise ValueError('This bounded audit cannot certify full source adaptation')
        for unit in source['units']:
            if unit['id'] in seen:
                raise ValueError('Duplicate source-unit ID')
            seen.add(unit['id'])
            if unit['anchor'] not in anchors or unit['lessonID'] not in lessons:
                raise ValueError('Unknown heading or lesson: ' + unit['id'])
            if not unit['checks']:
                raise ValueError('Source unit needs executable evidence')
            for label in unit['checks']:
                if not checks[(unit['lessonID'], label)]['passed']:
                    raise ValueError('Source unit check failed: ' + label)
    return dict(checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                compilerReceiptChecked=receipt['checked'], sourcePages=len(rules['sources']),
                locallyCheckedUnits=len(seen), fullyAdapted=False,
                scope='Evidence consistency for explicitly listed source units; no exhaustive source, Windows, hosted execution or mastery claim',
                sources=rules['sources'])


if __name__ == '__main__':
    report = validate()
    (ROOT / 'docs/rust-source-unit-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Validated {report['locallyCheckedUnits']} bounded source units")

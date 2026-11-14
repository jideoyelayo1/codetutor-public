"""Check the OCaml source ledger against the guide: every page has an honest status and real lessons."""
import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ocaml_guide import LESSONS, PARTS

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {'taught', 'partial', 'reading', 'gap'}


def cited_urls():
    """Every URL a lesson cites, with the lesson keys that cite it."""
    cited = {}
    for lesson in LESSONS:
        urls = [lesson['sourceURL']] + [r['url'] for r in lesson.get('additionalReadings', [])]
        for url in urls:
            cited.setdefault(url.split('#')[0], set()).add(lesson['key'])
    return cited


def validate(root=ROOT, write=False):
    ledger = json.loads((root / 'scripts/ocaml_source_ledger.json').read_text())
    keys = {lesson['key'] for lesson in LESSONS}
    cited = cited_urls()
    summary, seen_urls = {}, set()
    for source in ledger['sources']:
        counts = dict.fromkeys(sorted(STATUSES), 0)
        paths = [page['path'] for page in source['pages']]
        if len(set(paths)) != len(paths):
            raise ValueError(f"Duplicate page in ledger source {source['id']}")
        for page in source['pages']:
            where = f"{source['id']}:{page['path']}"
            if page['status'] not in STATUSES:
                raise ValueError(f'{where} has unknown status {page["status"]!r}')
            unknown = set(page['lessons']) - keys
            if unknown:
                raise ValueError(f'{where} names lessons that do not exist: {sorted(unknown)}')
            if page['status'] in ('taught', 'partial') and not page['lessons']:
                raise ValueError(f'{where} is {page["status"]} but names no lesson')
            if page['status'] == 'gap' and page['lessons']:
                raise ValueError(f'{where} is a gap but names lessons; promote it to partial or taught')
            if page['status'] == 'partial' and not page.get('note'):
                raise ValueError(f'{where} is partial without a recorded reason')
            if page['status'] == 'reading' and not page.get('note'):
                raise ValueError(f'{where} is reading-only without a reason')
            url = source['base'] + page['path']
            seen_urls.add(url)
            # A citation of a ledgered page must be reflected in the ledger.
            missing = cited.get(url, set()) - set(page['lessons'])
            if missing:
                raise ValueError(f'{where} is cited by {sorted(missing)} but the ledger does not list them')
            # A page called taught must actually be cited by a lesson that is listed for it.
            if page['status'] == 'taught' and not cited.get(url, set()) & set(page['lessons']):
                raise ValueError(f'{where} is taught but none of its lessons cites the page')
            counts[page['status']] += 1
        summary[source['id']] = dict(pages=len(source['pages']), **counts)
    totals = {s: sum(v[s] for v in summary.values()) for s in sorted(STATUSES)}
    report = dict(
        checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        guideLessons=len(LESSONS), sources=summary, totals=totals,
        # A page-level ledger cannot certify subsection or exercise coverage, so it never claims exhaustiveness.
        exhaustive=False,
        completePageStatuses=totals['gap'] == 0 and totals['partial'] == 0,
        scope='Page-level ledger: a floor, not a ceiling. Chapters of the manual contain many sections; page status does not certify subsection or exercise coverage.')
    if write:
        (root / 'docs/ocaml-source-ledger-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = validate(write=True)
    print(json.dumps({k: v for k, v in result.items() if k != 'checked'}, indent=2))

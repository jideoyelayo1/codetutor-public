"""The source ledger must stay honest: real lessons, recorded reasons, reflected citations."""
import json
from pathlib import Path
import tempfile
import unittest

from ocaml_guide import LESSONS
from validate_ocaml_source_ledger import ROOT, validate

LESSON_KEYS = [lesson['key'] for lesson in LESSONS]


def mutated(change):
    """Validate a copy of the ledger after applying [change] to its parsed JSON."""
    ledger = json.loads((ROOT / 'scripts/ocaml_source_ledger.json').read_text())
    change(ledger)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'scripts').mkdir()
        (root / 'scripts/ocaml_source_ledger.json').write_text(json.dumps(ledger))
        return validate(root)


def first_page(ledger, status):
    return next(p for s in ledger['sources'] for p in s['pages'] if p['status'] == status and p['lessons'])


class SourceLedgerTests(unittest.TestCase):
    def test_committed_ledger_is_valid_and_never_claims_false_completeness(self):
        report = validate(ROOT)
        totals = report['totals']
        self.assertIs(report['exhaustive'], False)
        self.assertEqual(sum(totals.values()), sum(s['pages'] for s in report['sources'].values()))

    def test_unknown_lessons_are_rejected(self):
        with self.assertRaises(ValueError):
            mutated(lambda l: first_page(l, 'taught')['lessons'].append('no-such-lesson'))

    def test_partial_pages_need_a_recorded_reason(self):
        with self.assertRaises(ValueError):
            mutated(lambda l: first_page(l, 'partial').pop('note'))

    def test_a_cited_page_must_list_the_citing_lesson(self):
        def swap(ledger):
            page = first_page(ledger, 'taught')
            page['lessons'] = [l for l in LESSON_KEYS if l not in page['lessons']][:1]
        with self.assertRaisesRegex(ValueError, 'does not list'):
            mutated(swap)

    def test_a_taught_page_must_be_cited_by_a_listed_lesson(self):
        with self.assertRaisesRegex(ValueError, 'none of its lessons cites'):
            mutated(lambda l: first_page(l, 'taught').update(path=first_page(l, 'taught')['path'] + '?uncited'))

    def test_gap_pages_cannot_name_lessons(self):
        def make_gap(ledger):
            page = first_page(ledger, 'taught')
            page['status'] = 'gap'
        with self.assertRaises(ValueError):
            mutated(make_gap)


if __name__ == '__main__':
    unittest.main()

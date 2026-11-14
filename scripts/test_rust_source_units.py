"""Source evidence must reject stale content and missing practice checks."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from validate_rust_source_units import validate


class SourceUnitEvidenceTests(unittest.TestCase):
    def test_rejects_stale_and_unchecked_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def write(path, value):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(value))
            write('CodingTeacher/curriculum.json', {'lessons': [{'id': 'lesson'}]})
            write('scripts/rust_guide_content.json', [])
            receipt = dict(selectedLessons=None, failed=0, checked='fixture',
                           inputSHA256={p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                                        for p in ('CodingTeacher/curriculum.json', 'scripts/rust_guide_content.json')},
                           cases=[dict(id='lesson', variant='test', passed=True)])
            rules = dict(sources=[dict(pageID='page', originalSHA256='source-hash', fullyAdapted=False,
                                      units=[dict(id='unit', anchor='heading', lessonID='lesson', checks=['test'])])])
            write('docs/offline-rust-coverage.json', dict(documents=[dict(pages=[dict(id='page', originalSHA256='source-hash', headings=[dict(anchor='heading')])])]))
            write('scripts/rust_source_units.json', rules)
            write('docs/rust-guide-validation.json', receipt)
            self.assertEqual(validate(root)['locallyCheckedUnits'], 1)
            for field in ('selectedLessons', 'failed', 'inputSHA256', 'cases'):
                with self.subTest(field=field):
                    bad = copy.deepcopy(receipt)
                    bad[field] = {'selectedLessons': ['lesson'], 'failed': 1,
                                  'inputSHA256': {}, 'cases': []}[field]
                    write('docs/rust-guide-validation.json', bad)
                    with self.assertRaises((ValueError, KeyError)):
                        validate(root)
            write('docs/rust-guide-validation.json', receipt)
            write('CodingTeacher/curriculum.json', {'lessons': [{'id': 'changed'}]})
            with self.assertRaisesRegex(ValueError, 'Stale'):
                validate(root)


if __name__ == '__main__':
    unittest.main()

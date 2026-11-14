"""Guard the Go guide receipt and the authoring rules the validator relies on."""
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from owned_process import run_owned

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts'))
from go_guide import LESSONS, tabs  # noqa: E402
from validate_go_guide import schema_errors, write_files  # noqa: E402


class GoGuideValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'.build').mkdir(exist_ok=True)

    def test_focused_validation_cannot_replace_full_receipt(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.build') as directory:
            # A broken guard must not damage the real acceptance receipt.
            fixture = Path(directory)/'repo'
            (fixture/'scripts').mkdir(parents=True); (fixture/'docs').mkdir()
            for name in ["validate_go_guide.py", "go_guide.py", "guide_builder.py", "owned_process.py", "go_coverage.py", "go_guide_inventory.json"]:
                (fixture/'scripts'/name).write_bytes((ROOT/'scripts'/name).read_bytes())
            shutil.copytree(ROOT/'scripts/go_guide_content', fixture/'scripts/go_guide_content')
            full = fixture/'docs/go-guide-validation.json'; full.write_text('{"full":true}\n')
            before = hashlib.sha256(full.read_bytes()).hexdigest()
            link = Path(directory)/'report.json'; link.symlink_to(full)
            hard = Path(directory)/'hard.json'; os.link(full, hard)
            for target in [None, Path('docs/go-guide-validation.json'), full, link, hard]:
                with self.subTest(target=target):
                    command = [sys.executable, str(fixture/'scripts/validate_go_guide.py'), '--lesson', 'first-program']
                    if target: command += ['--report', str(target)]
                    result = run_owned(command, cwd=fixture, timeout=30)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(hashlib.sha256(full.read_bytes()).hexdigest(), before)

    def test_bundled_guide_satisfies_schema(self):
        self.assertEqual(schema_errors(LESSONS), [])
        self.assertGreaterEqual(len(LESSONS), 130)
        stages = [l['stage'] for l in LESSONS]
        self.assertEqual(stages, sorted(stages), 'stage files must load in curriculum order')

    def test_schema_rejects_broken_entries(self):
        good = dict(LESSONS[0])
        cases = {
            'duplicate lesson keys': [good, good],
            'needs at least three': [dict(good, body=['one'])],
            'two distinct distractors': [dict(good, wrong=[good['correct'], 'x'])],
            'distinct distractors': [dict(good, wrong=['same', 'same'])],
            'https URL': [dict(good, sourceURL='http://example.com')],
            'Go-specific instructions': [dict(good, project=[{'path': 'go.mod', 'content': ''}], projectInstructions='', projectChecks=[{}])],
        }
        for fragment, lessons in cases.items():
            with self.subTest(fragment=fragment):
                self.assertTrue(any(fragment in e for e in schema_errors(lessons)), schema_errors(lessons))

    def test_guide_is_exhaustive_against_the_inventory(self):
        from go_coverage import report
        r = report(LESSONS)
        for gap in ['unknownLessonKeys', 'unknownSections', 'missingSections', 'missingPackages', 'missingCommands']:
            with self.subTest(gap=gap):
                self.assertEqual(r[gap], [])
        self.assertEqual(r['totals'], dict(sections=159, packages=180, commands=19))

    def test_import_detection(self):
        from go_coverage import imports
        self.assertEqual(imports('package p\n\nimport "fmt"\n'), {'fmt'})
        self.assertEqual(imports('import (\n\t"a/b"\n\t_ "c"\n\tx "d"\n)\n'), {'a/b', 'c', 'd'})
        self.assertEqual(imports('import _ "embed"\n'), {'embed'})
        quoted = 'package main\n\nimport "fmt"\n\nconst src = `package x\nimport "net/rpc"\n`\n'
        self.assertEqual(imports(quoted), {'fmt'})
        self.assertEqual(imports('import (\n\t"fmt" // see (x)\n\t"os"\n)\n'), {'fmt', 'os'})

    def test_uncompiled_files_and_failing_commands_do_not_count(self):
        from go_coverage import compiled_here, report
        self.assertFalse(compiled_here('plat_linux.go', 'package main\n'))
        self.assertFalse(compiled_here('gen.go', '//go:build ignore\n\npackage main\n'))
        self.assertFalse(compiled_here('testdata/x.go', 'package x\n'))
        self.assertTrue(compiled_here('main.go', 'package main\n'))
        lesson = dict(LESSONS[0], key='probe', project=[], projectChecks=[dict(name='usage error', args=['telemetry', 'bogus'], exit=2)])
        self.assertIn('telemetry', report([lesson])['missingCommands'])
        self.assertIn('bug', report([lesson])['missingCommands'])

    def test_indentation_becomes_gofmt_tabs(self):
        self.assertEqual(tabs('func f() {\n    if x {\n        y()\n    }\n}\n'), 'func f() {\n\tif x {\n\t\ty()\n\t}\n}\n')
        self.assertEqual(tabs('a := `    raw`\n'), 'a := `    raw`\n')
        # Documented limit: continuation lines of raw strings are rewritten too.
        self.assertEqual(tabs('s := `x\n    y`\n'), 's := `x\n\ty`\n')

    def test_project_paths_cannot_escape(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.build') as directory:
            with self.assertRaises(ValueError):
                write_files(Path(directory), [{'path': '../escape.go', 'content': ''}])


if __name__ == '__main__': unittest.main()

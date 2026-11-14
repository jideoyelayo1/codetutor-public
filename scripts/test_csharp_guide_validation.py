"""Fast structural checks for the C# guide and its validator; no SDK required."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import csharp_guide
from csharp_guide import LESSONS, apply

ROOT = Path(__file__).resolve().parent.parent


class CSharpGuideValidationTests(unittest.TestCase):
    def test_focused_validation_cannot_replace_full_receipt(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/validate_csharp_guide.py'), '--lesson', LESSONS[0]['key'],
                                 '--report', str(ROOT/'docs/csharp-guide-validation.json')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot replace the full guide report', result.stderr)

    def test_every_lesson_is_checkable(self):
        for lesson in LESSONS:
            with self.subTest(lesson=lesson['key']):
                self.assertTrue(lesson['code'] or lesson['project'], 'needs a program or a project')
                if lesson['code']:
                    self.assertTrue(lesson['expectedStdout'] and lesson['solution'] and lesson['solutionStdout'])
                if lesson['project']:
                    self.assertTrue(lesson['projectSolutionFiles'] and lesson['projectChecks'])
                    self.assertTrue(any(c.get('mutations') for c in lesson['projectChecks']), 'a project must prove its tests catch a bug')
                for rejection in lesson.get('rejected', []):
                    self.assertTrue((lesson['folder']/rejection['file']).exists())
                    self.assertRegex(rejection['diagnostic'], r'^CS\d{4}$')
                self.assertNotIn(lesson['correct'], lesson['wrong'])
                self.assertTrue(lesson['sourceURL'].startswith('https://'))

    def test_generator_appends_without_touching_existing_records(self):
        existing = dict(id='csharp.linq', trackID='csharp')
        content = apply(dict(lessons=[existing], cards=[], sourceCourses=[]))
        self.assertIs(content['lessons'][0], existing)
        guide = content['lessons'][1:]
        self.assertEqual([l['order'] for l in guide], list(range(2, len(LESSONS)+2)))
        self.assertEqual(len(content['cards']), 2*len(LESSONS))
        for lesson in guide:
            self.assertEqual(lesson['options'][lesson['answerIndex']], next(e['correct'] for e in LESSONS if 'guide.csharp.'+e['key'] == lesson['id']))
        course = content['sourceCourses'][0]
        self.assertEqual(course['kind'], 'Language guide')
        self.assertEqual(sum(len(c['lessonIDs']) for c in course['chapters']), len(LESSONS))

    def test_bundled_curriculum_matches_sources(self):
        bundled = {l['id']: l for l in json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())['lessons']}
        for lesson in LESSONS:
            actual = bundled['guide.csharp.'+lesson['key']]
            self.assertEqual(actual['code'], lesson['code'])
            self.assertEqual(actual['solution'], lesson['solution'])
            self.assertEqual(actual.get('projectFiles'), lesson['project'])
            self.assertEqual(actual.get('projectSolutionFiles'), lesson['projectSolutionFiles'])

    def test_displayed_text_does_not_leak_answers_or_markup(self):
        content = apply(dict(lessons=[], cards=[], sourceCourses=[]))
        for lesson, entry in zip(content['lessons'], LESSONS):
            self.assertFalse(any('`' in p for p in lesson['body']), 'source-study prose renders as plain text')
            self.assertNotIn(entry['reasoning'], lesson['workedExample'])
            if entry['expectedStdout']: self.assertNotIn(entry['expectedStdout'], lesson['workedExample'])
            self.assertIn(lesson['challenge'], lesson['practiceAnswer'])
            for text in [lesson['question'], lesson['challenge'], lesson['explanation'], *lesson['options']]:
                self.assertNotIn('`', text)
        for card in content['cards']:
            self.assertNotIn('`', card['prompt'] + card['answer'])

    def test_build_output_in_project_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'src/obj/cache.json'
            path.parent.mkdir(parents=True); path.write_text('{}')
            with self.assertRaises(ValueError):
                csharp_guide.tree(Path(directory))


if __name__ == '__main__':
    unittest.main()

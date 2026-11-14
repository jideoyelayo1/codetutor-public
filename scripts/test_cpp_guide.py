"""Semantic data and actual runtime ownership-regression checks for C++ authoring."""
import copy
import json
import os
from pathlib import Path
import platform
import shutil
import unittest
from owned_process import run_owned
from cpp_guide import ALL_UNITS
from validate_cpp_guide import run_project

ROOT=Path(__file__).resolve().parent.parent


class CppContentTests(unittest.TestCase):
    def setUp(self):
        self.content=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())

    def test_generation_is_reproducible_without_sources_or_network(self):
        result=run_owned(['python3','scripts/make_content.py','--check'],cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)

    def test_existing_records_and_source_locators_are_preserved(self):
        base=run_owned(['git','show','origin/HEAD:CodingTeacher/curriculum.json'],cwd=ROOT)
        self.assertEqual(base.returncode,0,base.stderr)
        baseline=json.loads(base.stdout)
        for field in ['tracks','lessons','cards','books']:
            current={r['id']:r for r in self.content[field]}
            for previous in baseline[field]:self.assertEqual(previous,current[previous['id']],previous['id'])
        courses={c['id']:c for c in self.content['sourceCourses']}
        for course in baseline['sourceCourses']:
            actual=courses[course['id']]
            self.assertEqual({k:v for k,v in course.items() if k!='chapters'},{k:v for k,v in actual.items() if k!='chapters'})
            for old,new in zip(course['chapters'],actual['chapters']):
                self.assertEqual({k:v for k,v in old.items() if k!='lessonIDs'},{k:v for k,v in new.items() if k!='lessonIDs'})
                self.assertTrue(set(old['lessonIDs']).issubset(new['lessonIDs']))

    def test_prediction_cards_include_the_program_and_answers_agree(self):
        lessons={l['id']:l for l in self.content['lessons']}
        cards={c['id']:c for c in self.content['cards']}
        entries={e['key']:e for e in ALL_UNITS}
        for problem in self.content['problems']:
            if '.drill.' in problem['id'] or problem['kind']=='Source exercise':continue
            lesson=lessons[problem['lessonID']]
            self.assertIn(problem['quizExplanation'],lesson['explanation'])
            if problem['starter']:self.assertIn(problem['starter'],cards[lesson['id']+'.1']['prompt'])
            if problem['kind']=='Predict output':
                entry=entries[lesson['id'].removeprefix('guide.cpp.')]
                self.assertEqual(problem['options'][problem['answerIndex']],repr(entry['expectedStdout']))

    def test_quizzes_have_distinct_reachable_questions_and_placement_is_untimed(self):
        ids={p['id'] for p in self.content['problems']}
        for quiz in self.content['quizzes']:
            self.assertEqual(len(set(quiz['questionIDs'])),len(quiz['questionIDs']))
            self.assertTrue(set(quiz['questionIDs']).issubset(ids))
            self.assertEqual(quiz['passPercent'],80)
            kind='book' if quiz['id'].startswith('quiz.cpp.book.') else quiz['id'].split('.')[-1].split('-')[0]
            shape={'placement':(0,20),'stage':(900,10),'drills':(900,15),'mock':(1800,25),'book':(900,10)}[kind]
            self.assertEqual((quiz['durationSeconds'],len(quiz['questionIDs'])),shape,quiz['id'])
            if quiz['id'].startswith('quiz.cpp.drills-') or quiz['id'].startswith('quiz.cpp.mock-'):
                self.assertTrue(all('.drill.' in q for q in quiz['questionIDs']))

    def test_drills_are_unique_attached_and_answer_their_stated_check(self):
        from cpp_drills import DRILLS
        problems={p['id']:p for p in self.content['problems']}
        lessons={l['id'] for l in self.content['lessons']}
        self.assertEqual(len({d['id'] for d in DRILLS}),len(DRILLS))
        for drill in DRILLS:
            problem=problems[drill['id']]
            self.assertIn(problem['lessonID'],lessons)
            self.assertEqual(problem['options'][problem['answerIndex']],drill['correct'])
            self.assertEqual(len(set(problem['options'])),len(problem['options']),drill['id'])
            if drill['check']=='reasoning':self.assertIn('no executable claim',problem['hints'][1])
        from cpp_drills import PLATFORM_SPECIFIC,PLATFORM_PREFIX
        for key in PLATFORM_SPECIFIC:self.assertTrue(problems['problem.cpp.drill.'+key]['question'].startswith(PLATFORM_PREFIX),key)

    def test_lesson_prose_keeps_cpp_operators_and_three_paragraphs(self):
        units={e['key']:e for e in ALL_UNITS}
        for entry in ALL_UNITS:
            if not entry.get('projectFiles'):self.assertEqual(len(entry['body']),3,entry['key'])
        self.assertIn('&& and ||',units['expressions']['body'][1])
        self.assertIn('flags |= mask',units['bit-and-compound-ops']['body'][1])
        self.assertIn('async | deferred',units['async-launch-policy']['body'][0])

    def test_drill_validator_rejects_a_wrong_stated_answer(self):
        from validate_cpp_guide import run_drill
        env=os.environ.copy()
        if platform.system()!='Darwin':self.skipTest('validator compiler resolution is exercised on macOS')
        env['DEVELOPER_DIR']='/Applications/Xcode.app/Contents/Developer'
        compiler=run_owned(['xcrun','--sdk','macosx','--find','clang++'],env=env).stdout.strip()
        env['SDKROOT']=run_owned(['xcrun','--sdk','macosx','--show-sdk-path'],env=env).stdout.strip()
        base=dict(id='problem.cpp.drill.selftest.1',code='#include <iostream>\nint main(){std::cout<<7/2<<"\\n";}\n',check='output',diagnostic=None)
        self.assertTrue(run_drill(dict(base,correct='3'),17,env,compiler)['passed'])
        self.assertFalse(run_drill(dict(base,correct='3.5'),17,env,compiler)['passed'])
        self.assertFalse(run_drill(dict(base,correct='3',check='reject'),17,env,compiler)['passed'])

    def test_cpp14_reference_capture_sequences_mutation_before_observation(self):
        lesson=next(l for l in self.content['lessons'] if l['id']=='guide.cpp.lambda-captures')
        problem=next(p for p in self.content['problems'] if p['lessonID']==lesson['id'])
        # In C++14 a chained insertion may read n before next() mutates it, so call next() first.
        for program in [problem['starter'],problem['solution']]:
            self.assertIn('const int result = next();\n',program)
            self.assertIn('std::cout << result << " " << n',program)
            self.assertNotIn('std::cout << next()',program)

class CppOwnershipMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment=os.environ.copy()
        if platform.system()=='Darwin':
            cls.environment['DEVELOPER_DIR']='/Applications/Xcode.app/Contents/Developer'
            cls.environment['SDKROOT']=run_owned(['xcrun','--sdk','macosx','--show-sdk-path'],env=cls.environment).stdout.strip()
            cls.compiler=run_owned(['xcrun','--sdk','macosx','--find','clang++'],env=cls.environment).stdout.strip()
        else:cls.compiler=shutil.which(os.environ.get('CXX','g++'))
        if not cls.compiler:raise RuntimeError('A compiler is required for ownership mutation checks')

    def reject_mutation(self,key,before,after):
        content=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
        actual=copy.deepcopy(next(l for l in content['lessons'] if l['id']=='guide.cpp.'+key))
        header=next(f for f in actual['projectFiles'] if f['path']=='lesson.hpp')
        self.assertEqual(header['content'].count(before),1)
        header['content']=header['content'].replace(before,after)
        entry=next(e for e in ALL_UNITS if e['key']==key)
        result=run_project(entry,'missing-ownership-regression','normal',actual,self.environment,self.compiler)
        self.assertFalse(result['passed'])
        self.assertIn('project check failed',result['diagnostics'])

    def test_ring_checks_detect_missing_storage_release(self):
        self.reject_mutation('allocator-ring-project','if (items_) alloc_.deallocate(items_, Capacity);','/* deliberate missing storage release */')

    def test_generator_checks_detect_abandoned_frame(self):
        self.reject_mutation('coroutine-project','~Generator() { if (handle_) handle_.destroy(); }','~Generator() {}')


if __name__=='__main__':unittest.main()

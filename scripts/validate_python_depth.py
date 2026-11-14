"""Verify appended Python source-depth material and exact displayed transfer answers."""
import hashlib
import io
import json
import contextlib
import platform
import re
from pathlib import Path
import subprocess
from python_guide_depth import DEPTH, transfer_program
from python_guide import DOC_PREFIXES, TOPICS, guide_lesson_id, guide_track
from validate_python_guide import close, extends, foreign_guide
from python_guide_book_topics import SPECS as BOOK_TOPICS

# (stage, spec) for every optional source supplement, in registration order.
SUPPLEMENTS = [(t['stage'], t) for t in TOPICS if t.get('supplemental')]

def order_shift(stage):
    return sum(s < stage for s, _ in SUPPLEMENTS)

ROOT = Path(__file__).resolve().parent.parent
BASELINE = 'a82e421219558930c99b042fd3826d6e6fd7b830'

def observe(code):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(code, '<authored-transfer>', 'exec'), {})
    return json.loads(output.getvalue())

def main():
    curriculum_path = ROOT/'CodingTeacher/curriculum.json'
    curriculum = json.loads(curriculum_path.read_text())
    baseline = json.loads(subprocess.check_output(['git','show',BASELINE+':CodingTeacher/curriculum.json'],cwd=ROOT))
    # Other merged guides may add tracks and books, or append their track IDs to a shared book; nothing earlier may change.
    for field, same in (('tracks', lambda a, b: a == b), ('books', extends)):
        now = {r['id']: r for r in curriculum[field]}
        assert all(same(r, now[r['id']]) for r in baseline[field]), ('unexpected structural change', field)
    current = {l['id']:l for l in curriculum['lessons']}
    old = {l['id']:l for l in baseline['lessons']}
    new_ids = {'guide.python.'+s['key'] for _, s in SUPPLEMENTS}
    # Other guides add lessons only to their own tracks; every new Python-family lesson is a depth supplement.
    assert {i for i in set(current)-set(old) if current[i]['trackID'] in ('python','numpy','pandas','sklearn','pytorch')} == new_ids
    assert set(old) <= set(current)
    courses = {c['id']: c for c in curriculum['sourceCourses']}
    for previous in baseline['sourceCourses']:
        if foreign_guide(previous): continue
        course = courses[previous['id']]
        assert course.keys() == previous.keys()
        for field,value in previous.items():
            if field!='chapters':
                assert course[field] == value, ('course metadata changed',course['id'],field)
                continue
            # Other guides (C++ appendices) may append chapters; earlier chapters keep their order and no Python lesson moves there.
            assert len(course[field]) >= len(value)
            assert not any(i.startswith('guide.python.') for chapter in course[field][len(value):] for i in chapter['lessonIDs'])
            for chapter,earlier in zip(course[field],value):
                assert chapter.keys() == earlier.keys(), ('chapter fields changed',course['id'],chapter['id'])
                for attr,prior in earlier.items():
                    # Only the combined and Python-focused guides list Python supplements.
                    match = re.fullmatch(r'guide\.python-ml\.(?:python\.)?stage-(\d\d)', chapter['id'])
                    if attr in ('lessonIDs','sections') and match:
                        expected = ['guide.python.'+s['key'] if attr=='lessonIDs' else s['title'] for n, s in SUPPLEMENTS if n == int(match[1])]
                        assert chapter[attr] == prior+expected, ('source supplement ordering',course['id'],attr)
                    elif attr in ('lessonIDs','sections'):
                        # Other guides (C++) append their own lessons to shared source chapters.
                        assert extends(prior, chapter[attr]), ('chapter changed',course['id'],chapter['id'],attr)
                        assert attr == 'sections' or not any(i.startswith('guide.python.') for i in chapter[attr][len(prior):])
                    else:
                        assert chapter[attr] == prior, ('chapter changed',course['id'],chapter['id'],attr)

    for identifier, previous in old.items():
        lesson = current[identifier]
        key = identifier.split('.',2)[2] if identifier.startswith('guide.') else None
        if key not in DEPTH or identifier != guide_lesson_id(key):
            expected = dict(previous)
            if identifier.startswith('guide.python.'):
                expected['order'] += order_shift(int(previous['summary'][:2]))
            assert lesson == expected, ('unrelated lesson changed', identifier)
            continue
        for field, value in previous.items():
            if field in ('body','reading','quiz','exercises'):
                assert lesson[field][:len(value)] == value, ('old material changed',identifier,field)
            elif field=='order' and identifier.startswith('guide.python.'):
                assert lesson[field] == value+order_shift(int(previous['summary'][:2]))
            else:
                assert lesson[field] == value, ('old field changed',identifier,field)
    cards = {c['id']:c for c in curriculum['cards']}
    assert all(cards[c['id']] == c for c in baseline['cards']), 'old recall changed'
    rows = []
    for key, detail in DEPTH.items():
        identifier = guide_lesson_id(key)
        lesson = current[identifier]
        spec = detail['transfer']
        exercise = next(e for e in lesson['exercises'] if e['id'] == identifier+'.transfer')
        assert exercise['solution'] == transfer_program(spec)
        assert len(set(q['id'] for q in lesson['quiz'])) == len(lesson['quiz'])
        assert detail['url'].startswith(DOC_PREFIXES[guide_track(key)]) and '#' in detail['url'], (key,'unversioned or unanchored locator')
        mutated_failures = 0
        for n, (data, expected) in enumerate(spec['cases']):
            # Substitute only the declared input in the actual displayed solution.
            marker = 'data = '+repr(spec['cases'][0][0])+'\n'
            assert exercise['solution'].count(marker) == 1
            actual_program = exercise['solution'].replace(marker,'data = '+repr(data)+'\n',1)
            assert actual_program == transfer_program(spec,n)
            assert close(observe(actual_program),expected), (key,n,'solution mismatch')
            bad = actual_program.replace(*spec['mutation'],1)
            compile(bad,'<semantic-counterexample>','exec')
            try:
                wrong = observe(bad)
                mutated_failures += not close(wrong,expected)
            except Exception:
                mutated_failures += 1
        assert mutated_failures, (key,'semantic mutation survived')
        assert close(json.loads(exercise['expectedOutput']), spec['cases'][0][1])
        quiz = next(q for q in lesson['quiz'] if q['id'] == identifier+'.q.transfer-boundary')
        assert quiz['code'] == exercise['solution']
        assert close(observe(quiz['code']),json.loads(quiz['options'][quiz['answerIndex']]))
        # Every distractor must disagree semantically, not just have different whitespace.
        for i, option in enumerate(quiz['options']):
            if i != quiz['answerIndex']:
                assert not close(json.loads(option),spec['cases'][0][1]), (key,'ambiguous distractor')
        assert len(spec['hints']) == 3 and len(set(spec['hints'])) == 3
        assert cards[identifier+'.3']['prompt'] == detail['recall'][0]
        rows.append(dict(lessonID=identifier,sourceURL=detail['url'],locator=detail['locator'],
                         scope='Bounded original instruction and transfer practice; not exhaustive section adaptation',
                         fullyAdapted=False,exerciseID=exercise['id'],
                         quizIDs=[identifier+'.q.reasoning',quiz['id']],cardID=identifier+'.3',
                         fixtureCases=len(spec['cases']),mutationRejected=True))
    report = dict(scope='Exact appended transfer solutions, semantic mutations, quiz outputs and append-only compatibility. Trusted local CPU execution; not hosted learner grading or exhaustive source adaptation.',
                  baseline=BASELINE,python=platform.python_version(),
                  curriculumSHA256=hashlib.sha256(curriculum_path.read_bytes()).hexdigest(),
                  authoringSHA256=hashlib.sha256((ROOT/'scripts/python_guide_depth.py').read_bytes()).hexdigest(),
                  authoringHashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'scripts').glob('python_guide*.py'))},
                  supplementalLessons=len(SUPPLEMENTS),preservationScope='Existing IDs/content/attempt contracts retained; each stage guide list appends its optional source supplements, and later Python lessons shift display order by the supplements before them',
                  enrichedLessons=len(rows),fixtureCases=sum(r['fixtureCases'] for r in rows),
                  mutationsRejected=len(rows),displayedAnswers=len(rows),displayedQuizPrograms=len(rows),
                  addedProblems=len(rows),addedQuizItems=2*len(rows),addedRecallCards=len(rows),units=rows)
    (ROOT/'docs/python-depth-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))

if __name__ == '__main__':
    main()

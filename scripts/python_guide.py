"""Deterministic, additive Python/ML learning content. No execution during generation."""
import hashlib
import json
from pathlib import Path
from python_guide_topics import TOPICS
from python_guide_depth import enrich

STAGES = [
("python", "First steps", "https://docs.python.org/3.13/tutorial/introduction.html"),
("python", "Everyday programs", "https://docs.python.org/3.13/tutorial/controlflow.html"),
("python", "Collections and algorithms", "https://docs.python.org/3.13/tutorial/datastructures.html"),
("python", "Functions and modules", "https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions"),
("python", "Files and reliable errors", "https://docs.python.org/3.13/tutorial/errors.html"),
("python", "Objects and protocols", "https://docs.python.org/3.13/reference/datamodel.html"),
("python", "Advanced language", "https://docs.python.org/3.13/reference/index.html"),
("python", "Professional Python", "https://docs.python.org/3.13/library/development.html"),
("python", "Concurrency and ownership", "https://docs.python.org/3.13/library/asyncio.html"),
("python", "Mathematics for ML", "https://docs.python.org/3.13/library/statistics.html"),
("numpy", "NumPy foundations", "https://numpy.org/doc/2.2/user/basics.html"),
("numpy", "NumPy advanced", "https://numpy.org/doc/2.2/reference/index.html"),
("pandas", "pandas foundations", "https://pandas.pydata.org/pandas-docs/version/2.3/user_guide/index.html"),
("pandas", "pandas advanced", "https://pandas.pydata.org/pandas-docs/version/2.3/user_guide/index.html"),
("sklearn", "ML framing and evaluation", "https://scikit-learn.org/1.7/model_selection.html"),
("sklearn", "Supervised machine learning", "https://scikit-learn.org/1.7/supervised_learning.html"),
("sklearn", "Model selection and unsupervised ML", "https://scikit-learn.org/1.7/unsupervised_learning.html"),
("pytorch", "PyTorch foundations", "https://docs.pytorch.org/docs/2.8/index.html"),
("pytorch", "Reliable deep learning", "https://docs.pytorch.org/docs/2.8/notes/randomness.html"),
("pytorch", "Vision, sequences and NLP", "https://docs.pytorch.org/docs/2.8/nn.html"),
("pytorch", "Advanced ML specializations", "https://docs.pytorch.org/docs/2.8/nn.html"),
("pytorch", "Efficient ML systems", "https://docs.pytorch.org/docs/2.8/index.html"),
("sklearn", "Production ML engineering", "https://scikit-learn.org/1.7/model_persistence.html"),
("python", "Integrated capstones", "https://docs.python.org/3.13/library/unittest.html"),
]
VERSIONS = "Python 3.13 · NumPy 2.2.6 · pandas 2.3.3 · scikit-learn 1.7.2 · PyTorch 2.8.0 · CPU"

# Versioned official documentation each depth locator must cite, by guide track.
DOC_PREFIXES = {'python':'https://docs.python.org/3.13/','numpy':'https://numpy.org/doc/2.2/',
                'pandas':'https://pandas.pydata.org/pandas-docs/version/2.3/','sklearn':'https://scikit-learn.org/1.7/',
                'pytorch':'https://docs.pytorch.org/docs/2.8/'}

def guide_track(key):
    return STAGES[next(e['stage'] for e in TOPICS if e['key'] == key)-1][0]

def guide_lesson_id(key):
    return 'guide.'+guide_track(key)+'.'+key

def source(entry):
    prefix = "import json\n" + entry['imports'] + "\n"
    stage = entry['stage']
    if stage in (11,12): prefix += "import numpy as np\n"
    if stage in (13,14): prefix += "import pandas as pd\n"
    if 18 <= stage <= 22: prefix += "import torch\nimport numpy as np\ntorch.set_num_threads(1)\n"
    return prefix

def program(entry, case=0, mutated=False, starter=False):
    body = entry['body']
    if mutated: body = body.replace(*entry['mutation'], 1)
    if starter: body = "# Implement the documented contract for data.\nresult = None"
    return source(entry) + 'data = ' + repr(entry['cases'][case][0]) + '\n' + body + '\nprint(json.dumps(result, sort_keys=True))\n'

def question(identifier, key, prompt, correct, wrong, explanation, code=None):
    options = list(dict.fromkeys([correct] + wrong))
    assert len(options) >= 3, (identifier,key)
    shift = int(hashlib.sha256((identifier+key).encode()).hexdigest()[:8],16) % len(options)
    options = options[shift:] + options[:shift]
    return dict(id=identifier+'.q.'+key, question=prompt, options=options, answerIndex=options.index(correct), explanation=explanation, **({'code':code} if code else {}))

def apply(content):
    previous = None
    chapters = []
    projects = json.loads(Path(__file__).with_name('python_projects.json').read_text()) if Path(__file__).with_name('python_projects.json').exists() else {}
    for stage, (track, title, url) in enumerate(STAGES, 1):
        stage_entries = [e for e in TOPICS if e['stage'] == stage]
        optional_previous = None
        ids = []
        for entry in stage_entries:
            identifier = 'guide.'+track+'.'+entry['key']
            ids.append(identifier)
            expected = [json.dumps(c[1],sort_keys=True) for c in entry['cases']]
            meaning = entry['explanation']; pitfall = entry['pitfall']
            trace = f"For input {entry['cases'][0][0]!r}, the worked computation produces {expected[0]}. Trace the intermediate values in the code and check the contract again with the other supplied cases."
            quizzes = [
                question(identifier,'contract','Which statement is correct for '+entry['title']+'?',meaning.split('. ')[0].rstrip('.')+'.',
                         ['The following concern can always be ignored: '+pitfall, 'One passing input proves the implementation works for all inputs.'], meaning),
                question(identifier,'trace','What result does this program produce?',expected[0],
                         ['null','"The input is always returned unchanged"','"An exception is required"'],trace,code=program(entry)),
                question(identifier,'transfer','What result does this changed input produce?',expected[-1],
                         ['"No result is possible"','"The input determines the type but never the value"','null'], meaning,code=program(entry,len(entry['cases'])-1)),
                question(identifier,'bug','Which proposed edit introduces the demonstrated defect?',
                         'Replace '+repr(entry['mutation'][0])+' with '+repr(entry['mutation'][1])+'.',
                         ['Add a regression for the documented boundary input.','Compare actual results with the supplied contract.','Run in the documented dependency environment.'],pitfall),
                question(identifier,'evidence','Does this faulty implementation satisfy all documented input/output pairs?\nCases: '+repr(entry['cases']),
                         'No. At least one of the documented cases violates the contract.',
                         ['Yes. The edit preserves every documented case.','Yes. Valid syntax guarantees the same results.','The expected results can be discarded because the program runs.'],pitfall+' Compare each result with its stated input/output pair.',code=program(entry,mutated=True)),
            ]
            contract = '\n'.join('Input '+repr(a)+' → '+json.dumps(b,sort_keys=True) for a,b in entry['cases'])
            exercises = [
                dict(id=identifier+'.implement',kind='Implement',title='Implement: '+entry['title'],
                     prompt=meaning+'\nAssign result from data, preserving this contract for all listed inputs.\n'+contract,
                     starter=program(entry, min(1,len(entry['cases'])-1),starter=True),
                     solution=program(entry,min(1,len(entry['cases'])-1)),
                     hints=['State the input and output contracts before choosing an operation.', meaning, 'Compare the smallest and boundary cases: '+contract],
                     explanation=meaning+' '+pitfall, expectedOutput=expected[min(1,len(expected)-1)]),
                dict(id=identifier+'.predict',kind='Predict',title='Trace: '+entry['title'],
                     prompt='Predict the result before running the code. Explain intermediate values and why the documented defect would change the contract.',
                     starter=program(entry,len(entry['cases'])-1),solution=expected[-1],
                     hints=[meaning,pitfall],explanation=trace+' '+meaning,expectedOutput=expected[-1]),
                dict(id=identifier+'.debug',kind='Debug',title='Repair: '+entry['title'],
                     prompt='Repair the implementation to satisfy every listed input/output pair. Identify the semantic mistake and add a regression.\n'+contract,
                     starter=program(entry,0,mutated=True),solution=program(entry,0),hints=[pitfall,meaning],
                     explanation='The faulty replacement is '+repr(entry['mutation'][0])+' → '+repr(entry['mutation'][1])+'. '+meaning,
                     expectedOutput=expected[0]),
            ]
            prerequisite = (optional_previous or previous) if entry.get('supplemental') and not entry.get('independent') else previous
            lesson=dict(id=identifier,trackID=track,title=entry['title'],summary=f'{stage:02}. {title}',body=entry.get('introParagraphs',[])+[meaning,trace,'Common mistake: '+pitfall],
                        code=program(entry),solution=program(entry, min(1,len(entry['cases'])-1)),challenge=exercises[0]['prompt'],
                        question=quizzes[0]['question'],options=quizzes[0]['options'],answerIndex=quizzes[0]['answerIndex'],explanation=meaning,
                        minutes=20,order=sum(l['trackID']==track for l in content['lessons'])+1,sourceURL=url,isSourceStudy=True,
                        workedExample=trace,practiceAnswer=meaning+' '+pitfall,learningObjectives=[meaning,'Diagnose the documented counterexample and justify the input/output contract.'],
                        prerequisiteIDs=[prerequisite] if prerequisite else [],exercises=exercises,quiz=quizzes,
                        reading=[dict(title='Versioned official documentation',url=url,section=entry['title'],note='Original reinforcement; this topic is not an exhaustive adaptation of the linked reference.')])
            if entry['key'] in projects:
                lesson.update({k:v for k,v in projects[entry['key']].items() if k!='validationMutation'})
            depth_card = enrich(lesson, entry, question)
            content['lessons'].append(lesson)
            for n,(prompt,answer) in enumerate([(quizzes[0]['question'],meaning),('What mistake must you avoid in '+entry['title'].lower()+'?',pitfall)],1):
                content['cards'].append(dict(id=identifier+'.'+str(n),trackID=track,lessonID=identifier,prompt=prompt,answer=answer,sourceURL=url))
            if depth_card is not None:
                content['cards'].append(depth_card)
            if entry.get('independent'):
                pass
            elif entry.get('supplemental'):
                optional_previous = identifier
            else:
                previous=identifier
        if ids:
            chapters.append(dict(id=f'guide.python-ml.stage-{stage:02}',title=f'{stage:02}. {title}',coverage='Original executable reinforcement; full reference/source adaptation remains under audit.',
                                 note='Recommended prerequisites are visible in each lesson. Reading, quiz scores, code runs and self-review remain separate.',sections=[e['title'] for e in stage_entries],lessonIDs=ids,
                                 reading=dict(title='Stage reference',url=url,section=title)))
    content['sourceCourses'].append(dict(id='guide.python-ml',title='Python: complete beginner to ML engineering',kind='Language guide',trackIDs=['python','numpy','pandas','sklearn','pytorch'],sourceURL=STAGES[0][2],edition=VERSIONS,
        scope='Ordered original lessons, examples, implementation/prediction/debugging problems, quizzes, recall and local projects. Each micro-lab is a bounded contract; full source adaptation and hosted grading remain open.',chapters=chapters))
    for track in ['python','numpy','pandas','sklearn','pytorch']:
        selected=[c for c in chapters if any(l['id'] in c['lessonIDs'] and l['trackID']==track for l in content['lessons'])]
        content['sourceCourses'].append(dict(id='guide.python-ml.'+track,title=next(t['name'] for t in content['tracks'] if t['id']==track)+' focused guide',kind='Language guide',trackIDs=[track],sourceURL=next(STAGES[i-1][2] for i in range(1,25) if STAGES[i-1][0]==track),edition=VERSIONS,
            scope='A library entry point into the same Python-to-ML lessons. Shared IDs preserve progress across guides; inspect cross-track prerequisites.',chapters=[dict(c, id=c['id'].replace('guide.python-ml.', 'guide.python-ml.'+track+'.')) for c in selected]))
    return content

"""Trusted original acceptance snippets. Never executes learner submissions locally."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.source_snippets import SNIPPETS
from scripts.rust_guide import LESSONS as RUST_GUIDE
from scripts.ocaml_guide import LESSONS as OCAML_GUIDE
from scripts.lean_guide import LESSONS as LEAN_GUIDE
from runtime_contract import ALIASES, ML_VERSIONS

@dataclass(frozen=True)
class Case:
    id: str
    language: str
    source: str
    expected: str | None = None
    succeeds: bool = True
    stdin: str = ''
    diagnostic: str | None = None
    json_result: bool = False

# Assertions supplement unchanged bundled programs, including random outputs.
ML_ASSERTIONS = {
 'numpy.broadcasting': (
  'np.testing.assert_array_equal(a+b, [[0,1,2,3],[1,2,3,4],[2,3,4,5]])',
  'np.testing.assert_allclose(x-x.mean(axis=0, keepdims=True), [[-1,-2],[1,2]])'),
 'numpy.views': ('assert a.tolist() == [0,99,2,3,4] and np.shares_memory(a,b)',
                 'assert a.tolist() == [0,1,2,3,4] and b.tolist() == [99,2] and not np.shares_memory(a,b)'),
 'numpy.axes': ('assert x.sum(axis=0).tolist() == [4,6] and x.sum(axis=1).tolist() == [3,7]',
                'np.testing.assert_allclose((x/x.sum(axis=1,keepdims=True)).sum(axis=1), [1,1])'),
 'pandas.indexing': ('assert s.loc[200] == 20 and s.iloc[1] == 20', 'assert df["flag"].tolist() == [False,True,True]'),
 'pandas.joins': ('assert len(a.merge(b,on="id")) == 4',
                  'assert events.merge(accounts,on="id",validate="many_to_one")["name"].tolist() == ["A","A","B"]'),
 'pandas.groups': ('assert df["centered"].tolist() == [-1.,1.,0.]', 'assert df["total"].tolist() == [4,4,9]'),
 'sklearn.leakage': ('assert [type(step).__name__ for step in model.named_steps.values()] == ["StandardScaler","LogisticRegression"]',
                     'assert make_pipeline(SimpleImputer(strategy="median"),LogisticRegression()).steps[0][1].strategy == "median"'),
 'sklearn.metrics': ('assert precision_score(y,p) == .5 and recall_score(y,p) == .5',
                     'assert recall_score([1,1,1,0],[1,0,0,0]) == 1/3'),
 'sklearn.validation': ('assert [(a.tolist(),b.tolist()) for a,b in TimeSeriesSplit(n_splits=3).split(np.arange(8))] == [([0,1],[2,3]),([0,1,2,3],[4,5]),([0,1,2,3,4,5],[6,7])]',
                        'assert GroupKFold(n_splits=3).n_splits == 3'),
 'pytorch.gradients': ('assert x.grad.item() == 12.', 'assert x.grad.item() == 6.'),
 'pytorch.evaluation': ('assert not model.training\nwith torch.no_grad():\n    assert torch.equal(model(torch.ones(4)),torch.ones(4))',
                       'assert not model.training\nwith torch.inference_mode():\n    result=model(torch.ones(1,2))\n    assert result.shape == (1,1) and torch.isfinite(result).all() and not result.requires_grad'),
 'pytorch.shapes': ('assert layer(x).shape == (4,2)', 'assert torch.nn.Linear(4,1)(x).shape == (5,1)'),
}

ML_SMOKE = """import numpy as np, pandas as pd, torch
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
assert np.arange(6).reshape(2,3).sum(axis=0).tolist() == [3,5,7]
assert pd.DataFrame({'g':['a','a','b'],'v':[1,3,9]}).groupby('g')['v'].sum().to_dict() == {'a':4,'b':9}
X=np.array([[0.,0.],[0.,1.],[2.,2.],[2.,3.]])
y=np.array([0,0,1,1])
model=make_pipeline(StandardScaler(),LogisticRegression(random_state=0)).fit(X,y)
assert model.predict(X).tolist() == y.tolist()
torch.set_num_threads(1)
torch.manual_seed(7)
x=torch.tensor([[-1.],[0.],[1.],[2.]])
target=2*x+1
network=torch.nn.Linear(1,1)
optimizer=torch.optim.SGD(network.parameters(),lr=0.1)
network.train()
initial=torch.nn.functional.mse_loss(network(x),target).item()
for _ in range(30):
    optimizer.zero_grad(set_to_none=True)
    loss=torch.nn.functional.mse_loss(network(x),target)
    loss.backward()
    optimizer.step()
network.eval()
with torch.inference_mode():
    final=torch.nn.functional.mse_loss(network(x),target).item()
    assert final < initial*0.01 and torch.isfinite(network(x)).all()
print('ml-smoke-ok')
"""

VERSION_PROBE = ("import json, platform, importlib.metadata\n"
                 "print(json.dumps({'python':platform.python_version(), 'packages':"
                 "{p:importlib.metadata.version(p) for p in " + repr(sorted(ML_VERSIONS)) + "}}))\n")


def all_cases():
    curriculum=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    pack=json.loads((ROOT/'scripts/learning_pack.json').read_text())
    expectations={x['id']:x for x in pack['lessons']}
    guide_expectations={'guide.rust.'+x['key']:x for x in RUST_GUIDE}
    guide_expectations.update({'guide.ocaml.'+x['key']:x for x in OCAML_GUIDE})
    guide_expectations.update({'guide.lean.'+x['key']:x for x in LEAN_GUIDE})
    cases=[]
    for lesson in curriculum['lessons']:
        language='python-ml' if lesson['trackID'] in ['numpy','pandas','sklearn','pytorch'] else lesson['trackID']
        if language not in ALIASES: continue
        for i,variant in enumerate(['code','solution']):
            source=lesson.get(variant,'')
            if not source.strip(): continue
            # The hosted runner checks single files without Mathlib; those lessons are verified in the authoring project.
            if language=='lean' and 'import Mathlib' in source: continue
            expected=None
            json_result=False
            if lesson['id'] in expectations:
                expected=expectations[lesson['id']]['expectedStdout' if variant=='code' else 'solutionStdout']
            if lesson['id'] in guide_expectations:
                guide=guide_expectations[lesson['id']]
                if source != guide[variant]: raise ValueError('Guide example changed without its expectation')
                expected=guide['expectedStdout' if variant=='code' else 'solutionStdout']
            if lesson['id'].startswith('source.') and variant=='code':
                authored,expected=SNIPPETS[lesson['id'].removeprefix('source.')]
                if authored != source: raise ValueError('Source companion changed without its expectation')
            if lesson.get('exercises') is not None:
                # Guide fixtures are validated locally against the exact bundled output.
                exercise=next(e for e in lesson['exercises'] if e['kind']==('Debug' if variant=='code' else 'Implement'))
                expected=exercise['expectedOutput']
                if expected is None: raise ValueError('Guide case needs an explicit expectation')
                json_result=True
            if language=='python-ml' and not json_result:
                source += '\n'+ML_ASSERTIONS[lesson['id']][i]+'\n'
            cases.append(Case(lesson['id']+'.'+variant,language,source,expected,json_result=json_result))
    for lesson in curriculum['lessons']:
        if lesson['trackID'] not in ['python','numpy','pandas','sklearn','pytorch']: continue
        for exercise in lesson.get('exercises',[]):
            if not exercise['id'].endswith('.transfer'): continue
            expected=exercise.get('expectedOutput')
            if expected is None: raise ValueError('Transfer case needs an explicit expectation')
            language='python' if lesson['trackID']=='python' else 'python-ml'
            cases.append(Case(exercise['id']+'.solution',language,exercise['solution'],expected,json_result=True))
    cases.extend([
        Case('feature.cpp20','cpp','#include <map>\n#include <iostream>\nint main(){std::map<int,int> m{{1,2}};std::cout<<m.contains(1)<<"\\n";}','1\n'),
        Case('stdin.python','python','print(input())','input-ok\n',stdin='input-ok\n'),
        Case('ml.smoke','python-ml',ML_SMOKE,'ml-smoke-ok\n'),
        Case('lean.no-main','lean','example (n : Nat) : n = n := by rfl\n#eval 6 * 7','42\n'),
        Case('lean.type-error','lean','def broken : Nat := "wrong"',succeeds=False,diagnostic='error'),
        Case('lean.tactic-error','lean','example : False := by rfl',succeeds=False,diagnostic='error'),
        Case('lean.sorry','lean','theorem unfinished : False := by sorry',succeeds=False,diagnostic='sorry'),
    ])
    return cases


def json_close(actual,expected):
    if isinstance(actual,(int,float)) and not isinstance(actual,bool) and isinstance(expected,(int,float)) and not isinstance(expected,bool):
        return math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual,expected,rel_tol=1e-5,abs_tol=1e-6)
    if isinstance(actual,list) and isinstance(expected,list):
        return len(actual)==len(expected) and all(json_close(a,b) for a,b in zip(actual,expected))
    if isinstance(actual,dict) and isinstance(expected,dict):
        return actual.keys()==expected.keys() and all(json_close(actual[k],expected[k]) for k in actual)
    return type(actual) is type(expected) and actual==expected


def result_passes(case, result):
    expected_output=True
    if case.expected is not None:
        if case.json_result:
            try: expected_output=json_close(json.loads(result.stdout),json.loads(case.expected))
            except (ValueError,TypeError):expected_output=False
        else:expected_output=result.stdout==case.expected
    return ((result.exitCode == 0) == case.succeeds and expected_output
            and (case.diagnostic is None or case.diagnostic in
                 (result.stdout+result.stderr+(result.diagnostics or '')).lower()))

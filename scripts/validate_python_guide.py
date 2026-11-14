"""Execute exact displayed Python/ML examples, answers and semantic counterexamples locally."""
import argparse
import hashlib
import json
import math
import inspect
import os
from pathlib import Path
import subprocess
import sys
import time
from python_guide_topics import TOPICS
from python_guide import program, apply

ROOT = Path(__file__).resolve().parent.parent

def close(a,b):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
        return math.isclose(a,b,rel_tol=1e-5,abs_tol=1e-6)
    if isinstance(a,list) and isinstance(b,list): return len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict): return a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
    return type(a) is type(b) and a==b

def extends(old,new):
    """True when new equals old except that lists may have grown at the end: other merged guides append, never rewrite."""
    if isinstance(old,dict): return isinstance(new,dict) and old.keys()==new.keys() and all(extends(old[k],new[k]) for k in old)
    if isinstance(old,list): return isinstance(new,list) and len(new)>=len(old) and all(extends(x,y) for x,y in zip(old,new))
    return old==new

def foreign_guide(record):
    """Another merged guide's own course (e.g. guide.rust); its validator covers it."""
    return record['id'].startswith(('guide.','concept.')) and not record['id'].startswith('guide.python')

def check_entry(entry):
    good=[]; bad=[]
    for case,(data,expected) in enumerate(entry['cases']):
        for mutation,rows in [(False,good),(True,bad)]:
            namespace={}
            try:
                # No print harness: test the same authored computation for every documented input.
                prefix=program(entry,case,mutated=mutation).rsplit('print(json.dumps',1)[0]
                exec(compile(prefix,entry['key'],'exec'),namespace)
                # JSON round-trip rejects non-portable values and normalizes tuple/list representation.
                value=json.loads(json.dumps(namespace['result'],allow_nan=False))
                rows.append(close(value,expected))
            except Exception as error:
                rows.append(False)
                if not mutation: raise AssertionError((entry['key'],case,type(error).__name__,str(error))) from error
    assert all(good),(entry['key'],'valid computation failed',good)
    assert not all(bad),(entry['key'],'mutation survived',bad)
    return dict(key=entry['key'],cases=len(good),mutationRejected=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',type=int)
    p.add_argument('--report',type=Path,default=ROOT/'docs/python-guide-validation.json')
    args=p.parse_args()
    if args.worker is not None:
        print(json.dumps([check_entry(e) for e in TOPICS if e['stage']==args.worker]));return
    c=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    # Additive preservation is checked against the branch's exact pre-expansion baseline.
    baseline=json.loads(subprocess.check_output(['git','show','05e1505:CodingTeacher/curriculum.json'],cwd=ROOT))
    for field in ['tracks','lessons','cards','books','sourceCourses']:
        by_id={e['id']:e for e in c[field]}
        # Earlier tracks, lessons and cards stay identical; shared books/courses may only gain entries other guides append.
        same=extends if field in ('books','sourceCourses') else (lambda old,new:old==new)
        assert all(same(e,by_id[e['id']]) for e in baseline[field] if field!='sourceCourses' or not foreign_guide(e)),('changed legacy',field)
        assert len(by_id)==len(c[field]),('duplicate',field)
    all_ids={l['id'] for l in c['lessons']}
    lessons=[l for l in c['lessons'] if l.get('exercises') is not None]
    assert len(lessons)==len(TOPICS)
    for l in lessons:
        assert set(l.get('prerequisiteIDs',[]))<=all_ids
        for q in l['quiz']:
            assert 0<=q['answerIndex']<len(q['options']) and len(set(q['options']))==len(q['options'])
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    rows=[]
    for stage in sorted({e['stage'] for e in TOPICS}):
        started=time.monotonic()
        completed=subprocess.run([sys.executable,__file__,'--worker',str(stage)],env=env,capture_output=True,text=True,timeout=90)
        if completed.returncode: raise AssertionError((stage,completed.stdout,completed.stderr))
        batch=json.loads(completed.stdout)
        rows+=batch
        print(f'Stage {stage:02}: {len(batch)} contracts and their mutations passed ({time.monotonic()-started:.1f}s)',flush=True)
    # Run the actual bundled code/answers; compare observed output with their authored contracts.
    import tempfile
    by_key={e['key']:e for e in TOPICS}
    displayed_count=0
    with tempfile.TemporaryDirectory(prefix='python-guide-') as directory:
        for stage in sorted({e['stage'] for e in TOPICS}):
            group=[l for l in lessons if l['summary'].startswith(f'{stage:02}.')]
            code='import contextlib,io,json,math\n'+inspect.getsource(close)+'\n'
            for lesson in group:
                entry=by_key[lesson['id'].split('.',2)[2]]
                examples=[('code',lesson['code'],entry['cases'][0][1]),
                          ('solution',lesson['solution'],entry['cases'][1][1]),
                          ('implement',lesson['exercises'][0]['solution'],entry['cases'][1][1]),
                          ('debug',lesson['exercises'][2]['solution'],entry['cases'][0][1])]
                assert lesson['exercises'][1]['solution']==json.dumps(entry['cases'][-1][1],sort_keys=True)
                for field,program_text,expected in examples:
                    code+='buffer=io.StringIO()\nwith contextlib.redirect_stdout(buffer):\n    exec('+repr(program_text)+',{})\n'
                    code+='actual=json.loads(buffer.getvalue())\nassert close(actual,'+repr(expected)+'),'+repr((lesson['id'],field))+'\n'
                    displayed_count+=1
            completed=subprocess.run([sys.executable,'-c',code],cwd=directory,env=env,capture_output=True,text=True,timeout=90)
            assert completed.returncode==0,(stage,completed.stderr)
    import numpy,pandas,sklearn,torch,platform
    report=dict(scope='Trusted authored CPU micro-labs on macOS; not a deployed sandbox, GPU, distributed run or universal correctness proof.',
                versions=dict(python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,sklearn=sklearn.__version__,torch=torch.__version__),
                topics=len(TOPICS),cases=sum(r['cases'] for r in rows),mutationsRejected=len(rows),displayedPrograms=displayed_count,
                sourceSHA256=hashlib.sha256(b''.join(p.name.encode()+b'\n'+p.read_bytes() for p in sorted((ROOT/'scripts').glob('python_guide*.py')))).hexdigest(),
                authoringHashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'scripts').glob('python_guide*.py'))},
                curriculumSHA256=hashlib.sha256((ROOT/'CodingTeacher/curriculum.json').read_bytes()).hexdigest(),casesByTopic=rows)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='casesByTopic'},indent=2))

if __name__=='__main__':main()

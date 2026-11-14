"""Check exact bundled project files, displayed answers, counterexamples and wheel builds."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import time
import tempfile
from owned_process import run_owned

ROOT=Path(__file__).resolve().parent.parent

def materialize(directory,files):
    directory.mkdir(parents=True,exist_ok=True)
    seen=set()
    for file in files:
        relative=Path(file['path'])
        assert not relative.is_absolute() and '..' not in relative.parts and relative not in seen
        seen.add(relative)
        path=directory/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(file['content'])

def digest(files):
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=ROOT/'docs/python-project-validation.json')
    args=parser.parse_args()
    curriculum=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    authored=json.loads((ROOT/'scripts/python_projects.json').read_text())
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PIP_DISABLE_PIP_VERSION_CHECK='1')
    rows=[]
    workspace=ROOT/'.build/python-projects'
    workspace.mkdir(parents=True,exist_ok=True)
    run_root=Path(tempfile.mkdtemp(prefix="run-",dir=workspace))
    for lesson in curriculum['lessons']:
        if not lesson['id'].startswith('guide.python.capstone-'):continue
        key=lesson['id'].removeprefix('guide.python.')
        baseline=lesson['projectFiles'];answers=lesson['projectSolutionFiles']
        assert set(f['path'] for f in answers)<=set(f['path'] for f in baseline)
        for mode in ['base','answer','mutation']:
            directory=run_root/key/mode
            # New versioned directories avoid stale files from a prior materialization.
            directory=directory/digest(baseline+answers)[:12]
            files=[dict(f) for f in baseline]
            if mode=='answer':
                replacements={f['path']:f['content'] for f in answers}
                files=[dict(f,content=replacements.get(f['path'],f['content'])) for f in files]
            if mode=='mutation':
                mutation=authored[key]['validationMutation']
                file=next(f for f in files if f['path']==mutation['path'])
                assert mutation['old'] in file['content']
                file['content']=file['content'].replace(mutation['old'],mutation['new'],1)
            materialize(directory,files)
            started=time.monotonic()
            command=[sys.executable,'-m','unittest','discover','-s','tests','-v']
            result=run_owned(command,cwd=directory,env=env,timeout=90,input='')
            (directory/'test.log').write_text(result.stdout+result.stderr)
            match=re.search(r'Ran (\d+) tests?',result.stderr)
            assert match,(key,mode,'no executed tests',result.stderr)
            if mode=='mutation':
                assert result.returncode!=0 and ('FAIL:' in result.stderr or 'ERROR:' in result.stderr),(key,'mutation survived',result.stderr)
            else:assert result.returncode==0,(key,mode,result.stderr)
            wheel=False
            if mode!='mutation':
                wheels=directory/'wheels'
                wheel_result=run_owned([sys.executable,'-m','pip','wheel','--no-index','--no-deps','--no-build-isolation','--wheel-dir',str(wheels),'.'],cwd=directory,env=env,timeout=60,input='')
                (directory/'wheel.log').write_text(wheel_result.stdout+wheel_result.stderr)
                assert wheel_result.returncode==0,(key,mode,'wheel failed',wheel_result.stdout,wheel_result.stderr)
                wheel=bool(list(wheels.glob('*.whl')))
                assert wheel
            rows.append(dict(id=key,variant=mode,tests=int(match[1]),passed=result.returncode==0,
                             mutationRejected=mode=='mutation' and result.returncode!=0,wheelBuilt=wheel,
                             seconds=round(time.monotonic()-started,3),filesSHA256=digest(files)))
            print(key,mode,'PASS' if mode!='mutation' else 'REJECTED',match[1],'tests',flush=True)
    assert len(rows)==24,len(rows)
    import numpy,pandas,sklearn,torch
    report=dict(scope='Eight original trusted local CPU projects: displayed base/answer tests and wheels, deliberate semantic mutations, real loopback HTTP and scoped teardown. Not deployed sandbox, GPU/distributed training, production security or exhaustive source adaptation.',
                versions=dict(python=platform.python_version(),numpy=numpy.__version__,pandas=pandas.__version__,sklearn=sklearn.__version__,torch=torch.__version__),
                projects=8,successfulVariants=16,mutationsRejected=8,wheelsBuilt=sum(r['wheelBuilt'] for r in rows),
                successfulTestCases=sum(r['tests'] for r in rows if r['variant']!='mutation'),
                curriculumSHA256=hashlib.sha256((ROOT/'CodingTeacher/curriculum.json').read_bytes()).hexdigest(),results=rows)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))

if __name__=='__main__':main()

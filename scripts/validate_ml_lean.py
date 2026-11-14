"""Check trusted original ML snippets and the Lean wrapper locally, with per-process measurements."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'backend'))
from runtime_cases import all_cases, VERSION_PROBE, result_passes
from gateway import normalize
from runtime_contract import ML_VERSIONS, ML_PYTHON_VERSION
from scripts.owned_process import run_owned


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=ROOT/'.build/ml-lean-validation.json')
    args=parser.parse_args()
    environment=os.environ.copy()
    environment.update(ELAN_HOME=str(ROOT/'.build/toolchains/elan'),OMP_NUM_THREADS='1',
                       OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
    lean=ROOT/'.build/toolchains/elan/bin/lean'
    environment['PATH']=str(lean.parent)+os.pathsep+environment['PATH']
    version=subprocess.run([sys.executable,'-c',VERSION_PROBE],text=True,capture_output=True,env=environment,check=True)
    versions=json.loads(version.stdout)
    if versions['python'] != ML_PYTHON_VERSION or {k:v.removesuffix('+cpu') for k,v in versions['packages'].items()} != ML_VERSIONS:
        parser.error('Install the pinned ML lockfile before running this check')
    versions['lean']=subprocess.run([str(lean),'--version'],text=True,capture_output=True,env=environment,check=True).stdout.strip()
    rows=[]
    for case in all_cases():
        if case.language not in ['python-ml','lean']: continue
        directory=ROOT/'.build/runtime-cases'/case.id
        directory.mkdir(parents=True,exist_ok=True)
        path=directory/('main.py' if case.language=='python-ml' else 'Main.lean')
        path.write_text(case.source)
        command=[sys.executable,str(path)] if case.language=='python-ml' else ['bash',str(ROOT/'backend/runtimes/lean4/run'),str(path)]
        measured=sys.platform=='darwin'
        started=time.monotonic()
        try:
            completed=run_owned((['/usr/bin/time','-l'] if measured else [])+command,
                                cwd=directory,env=environment,timeout=30,input=case.stdin)
            stderr=completed.stderr
            rss=None
            if measured:
                lines=stderr.splitlines(keepends=True)
                index=next((i for i,line in enumerate(lines) if re.match(r'^\s*[\d.]+ real\s+[\d.]+ user\s+[\d.]+ sys',line)),len(lines))
                measurement=''.join(lines[index:])
                match=re.search(r'(\d+)\s+maximum resident set size',measurement)
                rss=int(match[1]) if match else None
                stderr=''.join(lines[:index])
            result=normalize({'run':{'stdout':completed.stdout,'stderr':stderr,'code':completed.returncode}},versions.get(case.language,case.language),case.language)
            row={'id':case.id,'language':case.language,'passed':result_passes(case,result),
                 'seconds':round(time.monotonic()-started,3),'peakRSSBytes':rss,**result.model_dump()}
        except Exception as error:
            row={'id':case.id,'language':case.language,'passed':False,'error':str(error)}
        rows.append(row)
        print(case.id+': '+('PASS' if row['passed'] else 'FAIL '+str(row)),flush=True)
    report={'checked':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'scope':'Trusted original code on macOS arm64; not Piston sandbox, Linux CPU-wheel, phone, or general leak validation',
            'versions':versions,'total':len(rows),'passed':sum(r['passed'] for r in rows),'cases':rows}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['total'] and report['passed']==report['total'] else 1


if __name__=='__main__':
    raise SystemExit(main())

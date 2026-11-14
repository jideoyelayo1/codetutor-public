"""Run trusted curriculum cases through a private Piston engine; issue a scoped record."""
import argparse
import datetime
import json
import os
from pathlib import Path
import tempfile
import httpx
from gateway import normalize
from runtime_cases import all_cases, VERSION_PROBE, result_passes
from runtime_contract import ALIASES, LINUX_ML_VERSIONS, ML_PYTHON_VERSION, candidates, execution_payload
from runtime_verification import engine_url, checks_digest


def atomic_json(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    # A verification record is host configuration, excluded from Git.
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'w') as output:
            json.dump(value,output,indent=2); output.write('\n')
            output.flush(); os.fsync(output.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)


def evaluate(client, case, runtime):
    response=client.post('execute',json=execution_payload(case.language,case.source,runtime,case.stdin))
    response.raise_for_status()
    return normalize(response.json(),runtime['language']+' '+runtime['version'],case.language)


def verify_runtime(client, language, runtime, cases):
    rows=[]; packages=[]
    if language=='python-ml':
        try:
            response=client.post('execute',json=execution_payload(language,VERSION_PROBE,runtime))
            response.raise_for_status()
            result=normalize(response.json(),runtime['version'],language)
            versions=json.loads(result.stdout)
            actual=versions['packages']
            if (result.exitCode or versions['python'] != runtime['version'] or versions['python'] != ML_PYTHON_VERSION
                    or actual != LINUX_ML_VERSIONS):
                raise ValueError('Interpreter/library versions do not match the ML profile')
            packages=[k+'=='+v for k,v in actual.items()]
        except Exception as error:
            return None, [{'id':'ml.versions','passed':False,'error':str(error)}]
    for case in cases:
        try:
            result=evaluate(client,case,runtime)
            row={'id':case.id,'passed':result_passes(case,result),**result.model_dump()}
        except (httpx.HTTPError,ValueError,TypeError) as error:
            row={'id':case.id,'passed':False,'error':str(error)}
        # Gateway HTTPException is also an invalid engine result; leave no certificate.
        except Exception as error:
            row={'id':case.id,'passed':False,'error':str(error)}
        rows.append(row)
    if not cases or not all(r['passed'] for r in rows): return None,rows
    return {'id':language,'language':runtime['language'],'version':runtime['version'],
            'packages':packages,'caseCount':len(cases),'passed':True},rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine-url',default='http://127.0.0.1:2000/api/v2')
    parser.add_argument('--languages',default=','.join(ALIASES))
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    url=engine_url(args.engine_url)
    languages=list(dict.fromkeys(args.languages.split(',')))
    if not languages or any(x not in ALIASES for x in languages): parser.error('Unknown language selection')
    checks=all_cases()
    manifest={'schemaVersion':1,'engineURL':url,'checksDigest':checks_digest(),
              'checked':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtimes':[]}
    # Revoke old records before testing, including interrupted/failed reruns.
    atomic_json(args.verification,manifest)
    report={'scope':'Actual private Piston runs of trusted original snippets; not phone, isolation, or proof-grading certification',
            'engineURL':url,'checksDigest':manifest['checksDigest'],'checked':manifest['checked'],'attempts':[]}
    with httpx.Client(base_url=url+'/',timeout=30,trust_env=False) as client:
        response=client.get('runtimes'); response.raise_for_status()
        installed=response.json()
        for language in languages:
            selected=None
            for runtime in candidates(language,installed):
                record,rows=verify_runtime(client,language,runtime,[c for c in checks if c.language==language])
                report['attempts'].append({'id':language,'language':runtime['language'],'version':runtime['version'],'cases':rows})
                if record:
                    selected=record
                    manifest['runtimes'].append(record)
                    break
            print(language+': '+('verified '+selected['version'] if selected else 'FAILED / unavailable'),flush=True)
    atomic_json(args.report,report)
    atomic_json(args.verification,manifest)
    return 0 if len(manifest['runtimes'])==len(languages) else 1


if __name__=='__main__':
    raise SystemExit(main())

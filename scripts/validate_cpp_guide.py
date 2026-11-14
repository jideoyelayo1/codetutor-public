"""Validate actual bundled C++ examples/answers and CMake project files, locally."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from owned_process import run_owned
from cpp_guide import ALL_UNITS
from cpp_drills import DRILLS

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / '.build/cpp-guide-checks'


def file_path(directory, name):
    path = directory / name
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Project paths must remain relative: '+name)
    return path


def run_case(entry, variant, actual, env, compiler):
    directory = WORK / ('book/'+entry['source'] if 'source' in entry else '') / entry['key'] / variant
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    source = directory / 'main.cpp'
    source.write_text(actual[variant])
    executable = directory / 'program'
    command = [compiler, '-std=c++'+str(entry['standard']), '-Wall', '-Wextra', '-pedantic-errors', '-pthread', str(source), '-o', str(executable)]
    compiled = run_owned(command, env=env, timeout=60)
    diagnostic = entry.get('expectedDiagnostic') if variant == 'code' else None
    if diagnostic:
        passed = compiled.returncode != 0 and diagnostic in compiled.stderr
        return dict(id=actual['id'],variant=variant,passed=passed,kind='expected rejection',command=command,stderr=compiled.stderr)
    expected = entry['expectedStdout' if variant == 'code' else 'solutionStdout']
    result = run_owned([str(executable)],cwd=directory,env=env,timeout=15) if compiled.returncode == 0 else compiled
    return dict(id=actual['id'],variant=variant,passed=compiled.returncode==0 and result.returncode==0 and result.stdout==expected,
                kind='compiled and executed',command=command,compileExit=compiled.returncode,exit=result.returncode,
                stdout=result.stdout,expectedStdout=expected,stderr=compiled.stderr+result.stderr)


SANITIZER_MARK={'ubsan':'runtime error','asan':'AddressSanitizer','tsan':'ThreadSanitizer'}


def run_drill(drill, standard, env, compiler):
    """Check the stated answer of an executable drill against a real compile/run."""
    directory = WORK / 'drills' / drill['id']
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    source = directory / 'main.cpp'
    source.write_text(drill['code'])
    executable = directory / 'program'
    check = drill['check']
    flags = ['-fsanitize='+{'ubsan':'undefined','asan':'address','tsan':'thread'}[check],'-g','-O0'] if check in SANITIZER_MARK else []
    if check == 'ubsan': flags.append('-fno-sanitize-recover=all')
    command = [compiler, '-std=c++'+str(standard), '-Wall', '-Wextra', '-pedantic-errors', '-pthread', *flags, str(source), '-o', str(executable)]
    compiled = run_owned(command, env=env, timeout=60)
    base = dict(id=drill['id'], variant='drill', kind='drill '+check, command=command, compileExit=compiled.returncode)
    if check == 'reject':
        passed = compiled.returncode != 0 and (not drill['diagnostic'] or drill['diagnostic'] in compiled.stderr)
        return dict(base, passed=passed, stderr=compiled.stderr[-1500:])
    if compiled.returncode:
        return dict(base, passed=False, stderr=compiled.stderr[-1500:])
    result = run_owned([str(executable)], cwd=directory, env=env, timeout=30)
    if check in SANITIZER_MARK:
        passed = SANITIZER_MARK[check] in result.stderr
    elif check == 'compiles':
        passed = result.returncode == 0
    else:
        stdout = result.stdout[:-1] if result.stdout.endswith('\n') else result.stdout
        passed = result.returncode == 0 and stdout == drill['correct']
    return dict(base, passed=passed, exit=result.returncode, stdout=result.stdout[-1500:],
                expected=drill['correct'], stderr=result.stderr[-1500:])


def run_project(entry, variant, profile, actual, env, compiler):
    directory = WORK / entry['key'] / (variant+'-'+profile)
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    files = {f['path']:f['content'] for f in actual['projectFiles']}
    if variant == 'answer': files.update({f['path']:f['content'] for f in actual['projectSolutionFiles']})
    for name, content in files.items():
        path=file_path(directory,name);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    commands = [['cmake','-S','.','-B','build','-DCMAKE_BUILD_TYPE=Debug','-DCMAKE_CXX_COMPILER='+compiler]]
    if platform.system() == 'Darwin': commands[0].append('-DCMAKE_OSX_SYSROOT='+env['SDKROOT'])
    if profile == 'asan': commands[0].append('-DGUIDE_ASAN=ON')
    if profile == 'tsan': commands[0].append('-DGUIDE_TSAN=ON')
    commands += [['cmake','--build','build','--parallel','2'],['ctest','--test-dir','build','--output-on-failure']]
    passed=True; logs=[]
    for command in commands:
        result=run_owned(command,cwd=directory,env=env,timeout=120)
        if result.returncode:
            passed=False;logs.append(result.stdout+result.stderr);break
    if passed:
        # Both displayed executables must run; parser also checks the actual CLI error path.
        result=run_owned([str(directory/'build/guide_demo')],env=env,timeout=15)
        expected={'parser-project':'0\n','value-project':'10\n','allocator-ring-project':'7\n','pipeline-project':'55\n','coroutine-project':'0\n1\n2\n','design-project':'12\n'}[entry['key']]
        passed=result.returncode==0 and result.stdout==expected
        if not passed: logs.append(result.stdout+result.stderr)
        if entry['key']=='parser-project':
            ok=run_owned([str(directory/'build/guide_demo'),'2','-3','7'],env=env,timeout=15)
            bad=run_owned([str(directory/'build/guide_demo'),'3x'],env=env,timeout=15)
            passed=passed and ok.returncode==0 and ok.stdout=='6\n' and bad.returncode==2 and not bad.stdout
    return dict(id=actual['id'],variant=variant,profile=profile,kind='CMake project',passed=passed,commands=commands,diagnostics='\n'.join(logs))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=4)
    parser.add_argument('--sanitizers',action='store_true')
    parser.add_argument('--report',type=Path,default=None)
    parser.add_argument('--only',nargs='*',default=None,help='Lesson keys (unit or drill lesson) to check; writes the report under .build/')
    args=parser.parse_args()
    if args.report is None:
        args.report=ROOT/('.build/cpp-guide-partial-validation.json' if args.only is not None else 'docs/cpp-guide-validation.json')
    selected=lambda key: args.only is None or key in args.only
    env=os.environ.copy()
    if platform.system()=='Darwin':
        env['DEVELOPER_DIR']='/Applications/Xcode.app/Contents/Developer'
        env['SDKROOT']=run_owned(['xcrun','--sdk','macosx','--show-sdk-path'],env=env).stdout.strip()
        compiler=run_owned(['xcrun','--sdk','macosx','--find','clang++'],env=env).stdout.strip()
        env['ASAN_OPTIONS']='detect_leaks=0:halt_on_error=1'
    else:
        compiler=shutil.which(os.environ.get('CXX','g++'))
        env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1'
    if not compiler: raise RuntimeError('A real C++ compiler is required')
    env['UBSAN_OPTIONS']='halt_on_error=1'
    curriculum=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    bundled={l['id']:l for l in curriculum['lessons']}
    jobs=[];references=[]
    for entry in ALL_UNITS:
        if not selected(entry['key']): continue
        actual=bundled['guide.cpp.'+entry['key']]
        for field in ('code','solution','projectFiles','projectSolutionFiles'):
            if actual.get(field) != entry.get(field): raise ValueError('Bundle mismatch: '+actual['id']+' '+field)
        if entry.get('referenceOnly'):
            references.append(dict(id=actual['id'],status='reference only; no executable support claim'));continue
        for variant in ('code','solution'):
            if actual[variant]: jobs.append((run_case,(entry,variant,actual,env,compiler)))
        if actual.get('projectFiles'):
            profiles=['normal']+(['asan'] if args.sanitizers else [])+(['tsan'] if args.sanitizers and entry['key']=='pipeline-project' else [])
            for variant in ('starter','answer'):
                for profile in profiles: jobs.append((run_project,(entry,variant,profile,actual,env,compiler)))
    problems={p['id']:p for p in curriculum.get('problems',[])}
    reasoning=[]
    for drill in DRILLS:
        if not selected(drill['lesson']): continue
        bundled_problem=problems[drill['id']]
        if bundled_problem['starter']!=drill['code'] or bundled_problem['options'][bundled_problem['answerIndex']]!=drill['correct']:
            raise ValueError('Bundle mismatch: '+drill['id'])
        if drill['check']=='reasoning': reasoning.append(drill['id']); continue
        jobs.append((run_drill,(drill,bundled_problem['standard'],env,compiler)))
    def owned_job(job):
        function,params=job
        try: return function(*params)
        except (subprocess.TimeoutExpired,OSError) as error:
            return dict(id=params[0].get('id') or 'guide.cpp.'+params[0]['key'],variant=params[1] if 'key' in params[0] else 'drill',passed=False,diagnostics=str(error))
    with ThreadPoolExecutor(max_workers=max(1,min(args.jobs,8))) as pool:
        results=list(pool.map(owned_job,jobs))
    paths=['CodingTeacher/curriculum.json','scripts/cpp_guide.py','scripts/cpp_lessons.py','scripts/cpp_expert.py','scripts/cpp23_lessons.py','scripts/cpp_projects.py','scripts/cpp_source_links.py','scripts/cpp_drills.py','scripts/cpp_more_basics.py','scripts/cpp_more_ownership.py','scripts/cpp_more_generic.py','scripts/cpp_more_library.py','scripts/cpp_more_expert.py','scripts/validate_cpp_guide.py']
    report=dict(checkedAt=datetime.now(timezone.utc).isoformat(),platform=platform.platform(),
                compiler=run_owned([compiler,'--version'],env=env).stdout.strip(),sdk=env.get('SDKROOT'),
                inputSHA256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                scope='Trusted local authored programs and displayed CMake files only; no remote grading, exhaustive source-completion or universal leak claim. macOS ASan leak detection disabled; ownership counts and scoped sanitizers are separate evidence.',
                passed=sum(r['passed'] for r in results),total=len(results),referenceOnly=references,reasoningDrills=reasoning,cases=results)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(f'{report["passed"]}/{report["total"]} C++ checks passed; {len(references)} reference-only units; {len(reasoning)} reasoning-only drills/exercises')
    for result in results:
        if not result['passed']: print('FAIL',result['id'],result.get('variant'),result.get('profile',''),result.get('diagnostics',result.get('stderr',''))[-1800:])
    raise SystemExit(0 if report['passed']==report['total'] else 1)


if __name__=='__main__': main()

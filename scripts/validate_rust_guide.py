"""Check original Rust guide programs, solutions, diagnostics and Cargo workspace."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import argparse
from owned_process import run_owned
from rust_guide import LESSONS

ROOT = Path(__file__).resolve().parent.parent
TOOLCHAIN = ROOT / '.build/toolchains/rustup/toolchains/1.99.0-aarch64-apple-darwin/bin'
WORK = ROOT / '.build/rust-guide-checks'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson',action='append',choices=[l['key'] for l in LESSONS])
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if args.lesson and not args.report: parser.error('--lesson requires a separate --report path')
    if args.lesson and args.report.resolve()==(ROOT/'docs/rust-guide-validation.json').resolve():
        parser.error('focused validation cannot replace the full guide report')
    inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [ROOT/'CodingTeacher/curriculum.json', ROOT/'scripts/rust_guide_content.json']}
    lessons=[l for l in LESSONS if not args.lesson or l['key'] in args.lesson]
    rustc = str(TOOLCHAIN / 'rustc')
    cargo = str(TOOLCHAIN / 'cargo')
    environment = os.environ.copy()
    environment.update(RUSTC=rustc, RUSTDOC=str(TOOLCHAIN/'rustdoc'),
                       CARGO_HOME=str(ROOT/'.build/toolchains/cargo'))
    version = run_owned([rustc, '--version'], env=environment).stdout.strip()
    if not version.startswith('rustc 1.99.0 '):
        raise ValueError('Rust 1.99.0 is required for these checks')
    curriculum = json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    bundled = {l['id']:l for l in curriculum['lessons']}
    results = []
    for lesson in lessons:
        identifier = 'guide.rust.' + lesson['key']
        actual = bundled[identifier]
        for variant in ['code', 'solution']:
            if not lesson[variant]:
                continue
            if actual[variant] != lesson[variant]:
                raise ValueError(f'Bundled example differs: {identifier} {variant}')
            directory = WORK / lesson['key'] / variant
            directory.mkdir(parents=True, exist_ok=True)
            source = directory/'main.rs'; source.write_text(lesson[variant])
            binary = directory/'program'
            compiled = run_owned([rustc,'--edition=2024',str(source),'-o',str(binary)], env=environment, timeout=30)
            executed = run_owned([str(binary)], env=environment, timeout=10) if compiled.returncode == 0 else compiled
            expected = lesson['expectedStdout' if variant=='code' else 'solutionStdout']
            passed = compiled.returncode == 0 and executed.returncode == 0 and executed.stdout == expected
            results.append(dict(id=identifier,variant=variant,passed=passed,compileExit=compiled.returncode,
                                exit=executed.returncode,stdout=executed.stdout,expectedStdout=expected,
                                stderr=compiled.stderr+executed.stderr))
        if lesson['project']:
            if actual.get('projectFiles') != lesson['project']:
                raise ValueError(f'Bundled project differs: {identifier}')
            directory = WORK/lesson['key']/'workspace'
            if directory.exists(): shutil.rmtree(directory)
            for file in actual['projectFiles']:
                path=directory/file['path']; path.parent.mkdir(parents=True,exist_ok=True);path.write_text(file['content'])
            if lesson.get('projectChecks'):
                if actual.get('projectSolutionFiles') != lesson.get('projectSolutionFiles'):
                    raise ValueError(f'Bundled project solution differs: {identifier}')
                for check in lesson['projectChecks']:
                    # Compile the answer the app displays, not a second copy that could diverge.
                    for file in actual.get('projectSolutionFiles',[]) if check.get('useSolution') else []:
                        path=directory/file['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text(file['content'])
                    case_environment=environment.copy()
                    for key,value in check.get('environment',{}).items():
                        if value is None:case_environment.pop(key,None)
                        else:case_environment[key]=value
                    originals={}
                    try:
                        for mutation in check.get('mutations',[]):
                            if mutation['path'] not in {f['path'] for f in actual['projectFiles']}:
                                raise ValueError('Mutation must target a bundled project file')
                            path=directory/mutation['path'];text=path.read_text()
                            if text.count(mutation['find'])!=1:raise ValueError('Mutation must match exactly once')
                            originals.setdefault(path,text)
                            path.write_text(text.replace(mutation['find'],mutation['replace'],1))
                        result=run_owned([cargo]+check['args'],cwd=directory,env=case_environment,timeout=check.get('timeout',60))
                    finally:
                        for path,text in originals.items():path.write_text(text)
                    passed=result.returncode==check.get('exit',0)
                    if 'stdout' in check: passed=passed and result.stdout==check['stdout']
                    if 'stderr' in check: passed=passed and result.stderr==check['stderr']
                    if 'stderrContains' in check: passed=passed and check['stderrContains'] in result.stderr
                    for text in check.get('stdoutContains',[]): passed=passed and text in result.stdout
                    results.append(dict(id=identifier,variant=check['name'],passed=passed,exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
                continue
            result=run_owned([cargo,'run','--offline','--quiet','-p','guide-demo'],cwd=directory,env=environment,timeout=60)
            results.append(dict(id=identifier,variant='Cargo workspace',passed=result.returncode==0 and result.stdout==lesson['expectedStdout'],exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
            main=directory/'demo/src/main.rs'; main.write_text(main.read_text().replace('answer!()', 'answer!(unexpected)'))
            result=run_owned([cargo,'check','--offline','--quiet','-p','guide-demo'],cwd=directory,env=environment,timeout=30)
            results.append(dict(id=identifier,variant='invalid macro input',passed=result.returncode!=0 and 'answer expects no tokens' in result.stderr,exit=result.returncode,stderr=result.stderr))
            main.write_text(next(f['content'] for f in lesson['project'] if f['path']=='demo/src/main.rs'))
            macro=directory/'lesson-macros/src/lib.rs';macro.write_text(macro.read_text().replace('"42".parse()', '"64".parse()'))
            result=run_owned([cargo,'run','--offline','--quiet','-p','guide-demo'],cwd=directory,env=environment,timeout=60)
            results.append(dict(id=identifier,variant='Cargo practice solution',passed=result.returncode==0 and result.stdout=='64\n',exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
    rejected = [
        ('moved-owner','fn main() { let a = String::from("x"); let b = a; println!("{a} {b}"); }','E0382'),
        ('conflicting-loans','fn main() { let mut a = String::from("x"); let r = &a; a.push_str("y"); println!("{r}"); }','E0502'),
        ('expired-local','fn bad() -> &\'static str { let a = String::from("x"); &a } fn main() {}','E0515'),
        ('private-helper','mod m { fn helper() {} } fn main() { m::helper(); }','E0603'),
        ('extern-edition','extern "C" { fn abs(x: i32) -> i32; } fn main() {}','extern blocks must be unsafe'),
    ]
    for name,source,diagnostic in rejected if not args.lesson else []:
        directory=WORK/'negative'/name;directory.mkdir(parents=True,exist_ok=True)
        path=directory/'main.rs';path.write_text(source)
        result=run_owned([rustc,'--edition=2024',str(path),'-o',str(directory/'program')],env=environment,timeout=30)
        results.append(dict(id=name,variant='expected compiler rejection',passed=result.returncode!=0 and diagnostic in result.stderr,exit=result.returncode,stderr=result.stderr))
    for path,digest in inputs.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Validation input changed during checks: '+path)
    report=dict(inputSHA256=inputs,checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),compiler=version,edition='2024',lessons=len(lessons),
                cargoProjects=sum(bool(l['project']) for l in lessons),selectedLessons=args.lesson,
                total=len(results),passed=sum(r['passed'] for r in results),failed=sum(not r['passed'] for r in results),
                scope='Local trusted guide programs, answers and Cargo projects; full runs include five expected diagnostics; no hosted sandbox or mastery grading',cases=results)
    (args.report or ROOT/'docs/rust-guide-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in results:
        if not r['passed']: print(json.dumps(r,indent=2),file=sys.stderr)
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    return bool(report['failed'])


if __name__ == '__main__': sys.exit(main())

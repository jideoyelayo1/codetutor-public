"""Check original Go guide programs, answers, expected rejections and module projects with Go 1.27."""
import argparse
import re
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from owned_process import run_owned
from go_guide import CONTENT, LESSONS
from go_coverage import report as coverage_report

ROOT = Path(__file__).resolve().parent.parent
GOVERSION = 'go1.27.2'
TOOLS = ROOT / '.build/toolchains/go'
WORK = ROOT / '.build/go-guide-checks'
MODULE = 'module guide.example/lesson\n\ngo 1.27\n'
FULL_REPORT = ROOT / 'docs/go-guide-validation.json'


def environment():
    env = os.environ.copy()
    for key in ['GOFLAGS', 'GOROOT', 'GOWORK', 'GOEXPERIMENT', 'GODEBUG']: env.pop(key, None)
    # Examples are standard-library only; the network is needed just once to fetch the pinned toolchain.
    env.update(GOTOOLCHAIN=GOVERSION, GOPATH=str(TOOLS), GOMODCACHE=str(TOOLS/'mod'), GOCACHE=str(TOOLS/'cache'),
               GOFLAGS='-modcacherw', GOPROXY=env.get('GOPROXY', 'https://proxy.golang.org'), GOWORK='off', CGO_ENABLED='1')
    return env


def write_files(directory, files):
    for file in files:
        path = (directory/file['path']).resolve()
        if directory.resolve() not in path.parents: raise ValueError('Project path escapes its directory: '+file['path'])
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(file['content'])


def go(args, cwd, env, timeout=120, input=None):
    return run_owned(['go']+args, cwd=cwd, env=env, timeout=timeout, input=input)


def scrub(text, passed):
    """Keep the committed receipt free of local paths, and short for passing cases."""
    text = text.replace(str(WORK), '$WORK').replace(str(TOOLS), '$TOOLS').replace(str(ROOT), '$ROOT')
    return text[-400:] if passed else text[-4000:]


def check_program(identifier, key, variant, source, expected, stdin, env, race=False):
    directory = WORK/key/variant
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    (directory/'go.mod').write_text(MODULE); (directory/'main.go').write_text(source)
    formatted = go(['fmt', './...'], directory, env, timeout=30)
    canonical = (directory/'main.go').read_text() == source
    vetted = go(['vet', './...'], directory, env)
    executed = go(['run', '-race', '.'] if race else ['run', '.'], directory, env, input=stdin) if vetted.returncode == 0 else None
    run_stderr = executed.stderr if executed else ''
    executed = executed or vetted
    passed = formatted.returncode == 0 and canonical and vetted.returncode == 0 and executed.returncode == 0 and executed.stdout == expected
    return dict(id=identifier, variant=variant, passed=passed, race=race, gofmtCanonical=canonical, vetExit=vetted.returncode,
                exit=executed.returncode, stdout=executed.stdout, expectedStdout=expected, stderr=scrub(vetted.stderr+run_stderr, passed))


def check_rejection(identifier, key, number, rejection, env):
    directory = WORK/key/f'rejected-{number}'
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    (directory/'go.mod').write_text(MODULE); (directory/'main.go').write_text(rejection['source'])
    command = rejection.get('args', ['build', '-o', os.devnull, '.'])
    result = go(command, directory, env)
    passed = result.returncode != 0 and rejection['diagnostic'] in result.stderr
    return dict(id=identifier, variant=f'expected rejection {number}', passed=passed, exit=result.returncode,
                expectedDiagnostic=rejection['diagnostic'], stderr=scrub(result.stderr, passed))


def overlay(env, changes):
    env = env.copy()
    for name, value in changes.items():
        if value is None: env.pop(name, None)
        else: env[name] = value
    return env


def check_project(identifier, lesson, actual, env, gofmt):
    results = []
    env = overlay(env, lesson.get('projectEnvironment', {}))
    for variant, files in [('project', actual['projectFiles']), ('project answer', actual['projectFiles'])]:
        directory = WORK/lesson['key']/variant.replace(' ', '-')
        if directory.exists(): shutil.rmtree(directory)
        write_files(directory, files)
        if variant == 'project answer':
            write_files(directory, actual.get('projectSolutionFiles') or [])
        for name in ['vet', 'gofmt'] if lesson.get('projectVet') != [] else ['gofmt']:
            if name == 'vet': result = go(lesson.get('projectVet', ['vet', './...']), directory, env)
            else: result = run_owned([gofmt, '-l', '.'], cwd=directory, env=env)
            ok = result.returncode == 0 and (name == 'vet' or result.stdout == '')
            results.append(dict(id=identifier, variant=f'{variant} {name}', passed=ok, exit=result.returncode, stdout=scrub(result.stdout, ok), stderr=scrub(result.stderr, ok)))
        for check in lesson.get('projectChecks', []):
            if bool(check.get('useSolution')) != (variant == 'project answer'): continue
            case_env = overlay(env, {k: v.replace('{dir}', str(directory)) if isinstance(v, str) else v
                                     for k, v in check.get('environment', {}).items()})
            originals = {}
            try:
                for mutation in check.get('mutations', []):
                    path = directory/mutation['path']; text = path.read_text()
                    if text.count(mutation['find']) != 1: raise ValueError(f"Mutation must match exactly once: {identifier} {check['name']}")
                    originals.setdefault(path, text); path.write_text(text.replace(mutation['find'], mutation['replace'], 1))
                result = go(check['args'], directory/check.get('dir', '.'), case_env, timeout=check.get('timeout', 180), input=check.get('stdin'))
            finally:
                for path, text in originals.items(): path.write_text(text)
            passed = result.returncode == check.get('exit', 0)
            if 'stdout' in check: passed = passed and result.stdout == check['stdout']
            for text in check.get('stdoutContains', []): passed = passed and text in result.stdout
            for text in check.get('outputContains', []): passed = passed and text in result.stdout+result.stderr
            if 'stderrContains' in check: passed = passed and check['stderrContains'] in result.stderr
            results.append(dict(id=identifier, variant=check['name'], passed=passed, exit=result.returncode, stdout=scrub(result.stdout, passed), stderr=scrub(result.stderr, passed)))
    return results


def schema_errors(lessons):
    errors = []
    keys = [l['key'] for l in lessons]
    if len(keys) != len(set(keys)): errors.append('duplicate lesson keys')
    for l in lessons:
        name = l['key']
        if len(l['body']) < 3: errors.append(f'{name}: needs at least three explanatory paragraphs')
        if l['correct'] in l['wrong'] or len(l['wrong']) < 2 or len(set(l['wrong'])) != len(l['wrong']): errors.append(f'{name}: checkpoint needs two distinct distractors')
        if not l['challenge'].strip() or not l['reasoning'].strip(): errors.append(f'{name}: challenge and reasoning are required')
        if not l['sourceURL'].startswith('https://'): errors.append(f'{name}: primary source must be an https URL')
        if l['project'] and not l.get('projectInstructions'): errors.append(f'{name}: projects need Go-specific instructions')
        if l['project'] and not l.get('projectChecks'): errors.append(f'{name}: projects need checks')
        if not l['project'] and (not l['code'] or not l['solution']): errors.append(f'{name}: example and answer programs are required')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', action='append', choices=[l['key'] for l in LESSONS])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.lesson and not args.report: parser.error('--lesson requires a separate --report path')
    if args.lesson and (args.report.resolve() == FULL_REPORT.resolve() or (args.report.exists() and FULL_REPORT.exists() and os.path.samefile(args.report, FULL_REPORT))):
        parser.error('focused validation cannot replace the full guide report')
    errors = schema_errors(LESSONS)
    if errors: raise ValueError('Guide schema errors:\n'+'\n'.join(errors))
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [ROOT/'CodingTeacher/curriculum.json', ROOT/'scripts/go_guide.py', ROOT/'scripts/guide_builder.py',
                        ROOT/'scripts/go_coverage.py', ROOT/'scripts/go_guide_inventory.json',
                        Path(__file__).resolve(), *sorted(CONTENT.glob('stage_*.py'))]}
    env = environment()
    version = go(['version'], ROOT, env).stdout.strip()
    if not version.startswith(f'go version {GOVERSION} '): raise ValueError(f'{GOVERSION} is required for these checks: {version}')
    env['GOPROXY'] = 'off'  # the toolchain is now cached; every example must build offline
    gofmt = str(Path(go(['env', 'GOROOT'], ROOT, env).stdout.strip())/'bin/gofmt')
    drift, drift_cases = 0, []
    if not args.lesson:
        inventory = json.loads((ROOT/'scripts/go_guide_inventory.json').read_text())
        std = [p for p in go(['list', 'std'], ROOT, env).stdout.split() if not re.search(r'(^|/)internal(/|$)|^vendor/|^cmd/', p)]
        help_text = go(['help'], ROOT, env).stdout
        commands = re.findall(r'^\t(\w+)\s', help_text.split('The commands are:')[1].split('Use "go help')[0], re.M)
        for name, live, recorded in [('std', std, inventory['std']['packages']), ('commands', commands, inventory['commands']['names'])]:
            if live != recorded:
                drift += 1
                drift_cases.append(dict(id='inventory', variant=name, passed=False, live=live, recorded=recorded))
    bundled = {l['id']: l for l in json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())['lessons']}
    results = drift_cases
    for lesson in [l for l in LESSONS if not args.lesson or l['key'] in args.lesson]:
        identifier = 'guide.go.'+lesson['key']
        actual = bundled.get(identifier)
        if actual is None: raise ValueError(f'Regenerate the curriculum: {identifier} is missing')
        for variant, stdout in [('code', 'expectedStdout'), ('solution', 'solutionStdout')]:
            if actual[variant] != lesson[variant]: raise ValueError(f'Bundled example differs: {identifier} {variant}')
            if lesson[variant]:
                results.append(check_program(identifier, lesson['key'], variant, lesson[variant], lesson[stdout], lesson.get('stdin'), env, lesson.get('race', False)))
        for number, rejection in enumerate(lesson.get('rejections', []), 1):
            results.append(check_rejection(identifier, lesson['key'], number, rejection, env))
        if lesson['project']:
            if actual.get('projectFiles') != lesson['project'] or actual.get('projectSolutionFiles') != lesson.get('projectSolutionFiles'):
                raise ValueError(f'Bundled project differs: {identifier}')
            results += check_project(identifier, lesson, actual, env, gofmt)
    for path, digest in inputs.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest: raise ValueError('Validation input changed during checks: '+path)
    selected = [l for l in LESSONS if not args.lesson or l['key'] in args.lesson]
    coverage = None if args.lesson else coverage_report(LESSONS)  # exhaustiveness is only meaningful for a full run
    gaps = sum(len(v) for k, v in (coverage or {}).items() if k != 'totals') + drift
    report = dict(inputSHA256=inputs, checked=datetime.datetime.now(datetime.timezone.utc).isoformat(), compiler=version,
                  goDirective='1.27', lessons=len(selected), moduleProjects=sum(bool(l['project']) for l in selected),
                  selectedLessons=args.lesson, total=len(results), passed=sum(r['passed'] for r in results),
                  failed=sum(not r['passed'] for r in results) + gaps,
                  scope='Local trusted authoring checks: gofmt-canonical source, go vet, exact stdout, expected compiler/vet rejections, '
                        'and module projects with go test -race; no app or hosted Go execution and no mastery grading',
                  coverage=coverage,
                  cases=results)
    (args.report or FULL_REPORT).write_text(json.dumps(report, indent=2)+'\n')
    for r in results:
        if not r['passed']: print(json.dumps(r, indent=2), file=sys.stderr)
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
    return bool(report['failed'])


if __name__ == '__main__': sys.exit(main())

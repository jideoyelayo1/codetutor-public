"""Check original Bash guide scripts, answers and projects with Bash 5.3 and ShellCheck."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
from owned_process import run_owned
from bash_guide import LESSONS

ROOT = Path(__file__).resolve().parent.parent
BASH = '/opt/homebrew/bin/bash'
LEGACY_BASH = '/bin/bash'
SHELLCHECK = '/opt/homebrew/bin/shellcheck'
WORK = ROOT / '.build/bash-guide-checks'
# Learners run scripts in a clean shell: no inherited functions, aliases, locale or HOME state.
BASE_ENVIRONMENT = dict(PATH='/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C', TERM='dumb')


def shellcheck_codes(paths, cwd):
    result = run_owned([SHELLCHECK, '-s', 'bash', '-x', '-f', 'json'] + [str(p) for p in paths], cwd=cwd, timeout=30)
    if result.returncode not in (0, 1):
        raise RuntimeError('ShellCheck failed to run: ' + result.stderr)
    findings = json.loads(result.stdout or '[]')
    return sorted({f'SC{f["code"]}' for f in findings}), findings


def environment(home):
    return dict(BASE_ENVIRONMENT, HOME=str(home), TMPDIR=str(home))


def run_script(bash, directory, source, stdin, timeout):
    home = directory.with_name(directory.name+'-home')
    for stale in (directory, home):
        if stale.exists(): shutil.rmtree(stale)
    directory.mkdir(parents=True); home.mkdir()
    script = directory/'main.sh'
    script.write_text(source)
    # Run from an empty sibling so globs and listings never see the script itself.
    work = directory/'work'; work.mkdir()
    return script, run_owned([bash, '../main.sh'], cwd=work, env=environment(home), timeout=timeout, input=stdin)


def check_variant(lesson, actual, variant, results):
    identifier = 'guide.bash.' + lesson['key']
    if actual[variant] != lesson[variant]:
        raise ValueError(f'Bundled example differs: {identifier} {variant}')
    directory = WORK/lesson['key']/variant
    stdin = lesson.get('stdin', '')
    script, executed = run_script(BASH, directory, lesson[variant], stdin, lesson.get('timeout', 10))
    # bash -n never runs shopt, so pre-enable extglob when the script turns it on before use.
    parse_options = ['-O', 'extglob'] if 'shopt -s extglob' in lesson[variant] else []
    syntax = run_owned([BASH, *parse_options, '-n', str(script)], timeout=10)
    expected_codes = sorted(lesson.get('shellcheckExpected', [])) if variant == 'code' else []
    codes, findings = shellcheck_codes([script], directory)
    expected = lesson['expectedStdout' if variant == 'code' else 'solutionStdout']
    expected_exit = lesson.get('expectedExit' if variant == 'code' else 'solutionExit', 0)
    passed = (syntax.returncode == 0 and codes == expected_codes and executed.returncode == expected_exit
              and executed.stdout == expected)
    if 'expectedStderrContains' in lesson and variant == 'code':
        passed = passed and lesson['expectedStderrContains'] in executed.stderr
    results.append(dict(id=identifier, variant=variant, passed=passed, syntaxExit=syntax.returncode, exit=executed.returncode, expectedExit=expected_exit,
                        stdout=executed.stdout, expectedStdout=expected, stderr=executed.stderr,
                        shellcheck=codes, expectedShellcheck=expected_codes,
                        shellcheckMessages=[f'SC{f["code"]} line {f["line"]}: {f["message"]}' for f in findings]))
    # A \"5.3+\" lesson must fail on macOS Bash 3.2; this shows it needs a newer Bash, not that 5.3 is the minimum.
    if variant == 'code' and lesson.get('minimumBash') and Path(LEGACY_BASH).exists():
        _, legacy = run_script(LEGACY_BASH, WORK/lesson['key']/'legacy', lesson['code'], stdin, 10)
        results.append(dict(id=identifier, variant=f'differs on Bash 3.2 (marked {lesson["minimumBash"]}+)', exit=legacy.returncode,
                            passed=legacy.returncode != expected_exit or legacy.stdout != expected,
                            stdout=legacy.stdout, stderr=legacy.stderr))


def check_project(lesson, actual, results):
    identifier = 'guide.bash.' + lesson['key']
    if actual.get('projectFiles') != lesson['project'] or actual.get('projectSolutionFiles') != lesson.get('projectSolutionFiles'):
        raise ValueError(f'Bundled project differs: {identifier}')
    for check in lesson['projectChecks']:
        directory = WORK/lesson['key']/'project'/check['name'].replace(' ', '-')
        home = directory.with_name(directory.name+'-home')
        for stale in (directory, home):
            if stale.exists(): shutil.rmtree(stale)
        files = {f['path']: f['content'] for f in lesson['project']}
        if check.get('useSolution'):
            files.update({f['path']: f['content'] for f in lesson['projectSolutionFiles']})
        for mutation in check.get('mutations', []):
            text = files[mutation['path']]
            if text.count(mutation['find']) != 1: raise ValueError('Mutation must match exactly once')
            files[mutation['path']] = text.replace(mutation['find'], mutation['replace'], 1)
        for path, content in files.items():
            target = directory/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content)
            if path.endswith('.sh') or content.startswith('#!'): target.chmod(0o755)
        home.mkdir(parents=True)
        scripts = sorted(directory/p for p, c in files.items() if p.endswith('.sh') or c.startswith('#!/usr/bin/env bash'))
        codes, findings = shellcheck_codes(scripts, directory) if not check.get('mutations') else ([], [])
        result = run_owned([BASH] + check['args'], cwd=directory, env=environment(home), timeout=check.get('timeout', 30),
                           input=check.get('stdin', ''))
        passed = result.returncode == check.get('exit', 0) and not codes
        if 'stdout' in check: passed = passed and result.stdout == check['stdout']
        for text in check.get('stdoutContains', []): passed = passed and text in result.stdout
        for text in check.get('stderrContains', []): passed = passed and text in result.stderr
        results.append(dict(id=identifier, variant=check['name'], passed=passed, exit=result.returncode,
                            stdout=result.stdout, stderr=result.stderr, shellcheck=codes,
                            shellcheckMessages=[f'{f["file"]}:{f["line"]} SC{f["code"]}: {f["message"]}' for f in findings]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', action='append', choices=[l['key'] for l in LESSONS])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.lesson and not args.report: parser.error('--lesson requires a separate --report path')
    if args.lesson and args.report.resolve() == (ROOT/'docs/bash-guide-validation.json').resolve():
        parser.error('focused validation cannot replace the full guide report')
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
              [ROOT/'CodingTeacher/curriculum.json', ROOT/'scripts/bash_guide_content.json']}
    version = run_owned([BASH, '--version'], timeout=10).stdout.splitlines()[0]
    if 'version 5.3.' not in version:
        raise ValueError('GNU Bash 5.3 is required for these checks: ' + version)
    checker = run_owned([SHELLCHECK, '--version'], timeout=10).stdout.split('version: ')[1].split()[0]
    bundled = {l['id']: l for l in json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())['lessons']}
    lessons = [l for l in LESSONS if not args.lesson or l['key'] in args.lesson]
    results = []
    for lesson in lessons:
        actual = bundled['guide.bash.' + lesson['key']]
        for variant in ['code', 'solution']:
            if lesson[variant]: check_variant(lesson, actual, variant, results)
        if lesson['project']: check_project(lesson, actual, results)
    for path, digest in inputs.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Validation input changed during checks: ' + path)
    report = dict(inputSHA256=inputs, checked=datetime.datetime.now(datetime.timezone.utc).isoformat(), shell=version,
                  shellcheck=checker, lessons=len(lessons), projects=sum(bool(l['project']) for l in lessons),
                  selectedLessons=args.lesson, total=len(results), passed=sum(r['passed'] for r in results),
                  failed=sum(not r['passed'] for r in results),
                  scope='Local trusted guide scripts, answers and projects under a clean environment; exact stdout/exit, '
                        'bash -n, ShellCheck findings and macOS Bash 3.2 counter-checks for lessons marked 5.3+ (not an exact-minimum proof). No hosted sandbox or mastery grading.',
                  cases=results)
    (args.report or ROOT/'docs/bash-guide-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    for r in results:
        if not r['passed']: print(json.dumps(r, indent=2), file=sys.stderr)
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
    return bool(report['failed'])


if __name__ == '__main__': sys.exit(main())

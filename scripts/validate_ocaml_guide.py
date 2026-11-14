"""Check original OCaml guide programs, solutions, diagnostics and Dune projects."""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from owned_process import run_owned
from ocaml_guide import LESSONS, PARTS

ROOT = Path(__file__).resolve().parent.parent
OPAM_ROOT = ROOT / '.build/toolchains/opam/root'
OPAM = ROOT / '.build/toolchains/opam/bin/opam'
SWITCH = '5.5.1'
WORK = ROOT / '.build/ocaml-guide-checks'
REPORT = ROOT / 'docs/ocaml-guide-validation.json'


def clean(text):
    """Keep machine-specific absolute paths out of committed receipts."""
    home = str(Path.home())
    for prefix in (str(ROOT), str(ROOT).replace(home, '~', 1)):
        text = text.replace(prefix, '<repo>')
    return text.replace(home, '~')


def input_digests():
    """Bind the receipt to OCaml-owned inputs, so other guides' curriculum records cannot make it stale."""
    curriculum = json.loads((ROOT / 'CodingTeacher/curriculum.json').read_text())
    owned = {key: [r for r in curriculum.get(key, []) if r['id'] == 'guide.ocaml' or r['id'].startswith('guide.ocaml.')]
             for key in ('lessons', 'cards', 'sourceCourses')}
    digests = {'CodingTeacher/curriculum.json#guide.ocaml':
               hashlib.sha256(json.dumps(owned, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
    digests.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in PARTS})
    return digests


def switch(command):
    """Run inside the pinned local opam switch; nothing global is touched."""
    return [str(OPAM), 'exec', '--root', str(OPAM_ROOT), '--switch', SWITCH, '--'] + command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', action='append', choices=[l['key'] for l in LESSONS])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.lesson and not args.report: parser.error('--lesson requires a separate --report path')
    # resolve() catches symlinks and relative paths; samefile() also catches hard links.
    if args.lesson and (args.report.resolve() == REPORT.resolve()
                        or (args.report.exists() and REPORT.exists() and os.path.samefile(args.report, REPORT))):
        parser.error('focused validation cannot replace the full guide report')
    inputs = input_digests()
    lessons = [l for l in LESSONS if not args.lesson or l['key'] in args.lesson]
    environment = os.environ.copy()
    environment.update(OPAMROOT=str(OPAM_ROOT), OPAMYES='1', DUNE_CACHE='disabled', NO_COLOR='1')
    version = run_owned(switch(['ocamlc', '-version']), env=environment).stdout.strip()
    if version != '5.5.1':
        raise ValueError('OCaml 5.5.1 is required for these checks')
    packages = run_owned([str(OPAM), 'list', '--root', str(OPAM_ROOT), '--switch', SWITCH, '--installed',
                          '--columns=name,version'], env=environment).stdout
    # Lines are "name version"; comment lines start with '#'. Record name.version.
    packages = ['.'.join(line.split()[:2]) for line in packages.splitlines() if line.strip() and not line.startswith('#')]
    curriculum = json.loads((ROOT / 'CodingTeacher/curriculum.json').read_text())
    bundled = {l['id']: l for l in curriculum['lessons']}
    results = []
    for lesson in lessons:
        identifier = 'guide.ocaml.' + lesson['key']
        actual = bundled[identifier]
        for variant in ['code', 'solution']:
            if not lesson[variant]:
                continue
            if actual[variant] != lesson[variant]:
                raise ValueError(f'Bundled example differs: {identifier} {variant}')
            directory = WORK / lesson['key'] / variant
            if directory.exists(): shutil.rmtree(directory)
            directory.mkdir(parents=True)
            source = directory / 'main.ml'; source.write_text(lesson[variant])
            binary = directory / 'program'
            compiled = run_owned(switch(['ocamlfind', 'ocamlopt', str(source), '-o', str(binary)]), env=environment, timeout=60)
            executed = run_owned([str(binary)], env=environment, timeout=10) if compiled.returncode == 0 else compiled
            expected = lesson['expectedStdout' if variant == 'code' else 'solutionStdout']
            passed = compiled.returncode == 0 and executed.returncode == 0 and executed.stdout == expected
            results.append(dict(id=identifier, variant=variant, passed=passed, compileExit=compiled.returncode,
                                exit=executed.returncode, stdout=executed.stdout, expectedStdout=expected,
                                stderr=compiled.stderr + executed.stderr))
        if lesson['project']:
            if actual.get('projectFiles') != lesson['project']:
                raise ValueError(f'Bundled project differs: {identifier}')
            if actual.get('projectSolutionFiles') != lesson.get('projectSolutionFiles'):
                raise ValueError(f'Bundled project solution differs: {identifier}')
            directory = WORK / lesson['key'] / 'workspace'
            if directory.exists(): shutil.rmtree(directory)
            for file in actual['projectFiles']:
                path = directory / file['path']; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(file['content'])
            if not lesson.get('projectChecks'):
                raise ValueError(f'Project lesson has no checks: {identifier}')
            solution_applied = False
            for check in lesson['projectChecks']:
                # The workspace keeps a written solution, so later checks must declare they ignore the starter.
                if check.get('useSolution'): solution_applied = True
                elif solution_applied and not check.get('independentOfSolution'):
                    raise ValueError(f'Check {check["name"]!r} follows a solution check in {identifier} but is not marked independentOfSolution')
                # Run the answer displayed by the app, not a second copy that could diverge.
                for file in actual.get('projectSolutionFiles', []) if check.get('useSolution') else []:
                    path = directory / file['path']; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(file['content'])
                case_environment = environment.copy()
                for key, value in check.get('environment', {}).items():
                    if value is None: case_environment.pop(key, None)
                    else: case_environment[key] = value
                # Only race- or timer-dependent checks may retry; the attempt count is recorded in the receipt.
                for attempt in range(1 + check.get('retries', 0)):
                    originals = {}
                    try:
                        for mutation in check.get('mutations', []):
                            if mutation['path'] not in {f['path'] for f in actual['projectFiles']}:
                                raise ValueError('Mutation must target a bundled project file')
                            path = directory / mutation['path']; text = path.read_text()
                            if text.count(mutation['find']) != 1: raise ValueError('Mutation must match exactly once')
                            originals.setdefault(path, text)
                            path.write_text(text.replace(mutation['find'], mutation['replace'], 1))
                        result = run_owned(switch(check['command']), cwd=directory, env=case_environment, timeout=check.get('timeout', 180), input=check.get('input'))
                    finally:
                        for path, text in originals.items(): path.write_text(text)
                    passed = result.returncode == check.get('exit', 0)
                    if 'stdout' in check: passed = passed and result.stdout == check['stdout']
                    if 'stderrContains' in check: passed = passed and check['stderrContains'] in result.stderr
                    for text in check.get('stdoutContains', []): passed = passed and text in result.stdout
                    if passed: break
                results.append(dict(id=identifier, variant=check['name'], passed=passed, exit=result.returncode,
                                    stdout=result.stdout, stderr=result.stderr, attempts=attempt + 1))
    rejected = [
        ('type-mismatch', 'let x : int = "one"', ['This constant has type string']),
        ('partial-match', 'let f = function Some x -> x', ['partial-match']),
        ('weak-type', 'let r = ref []', ['non-generalizable']),
        ('signature-mismatch', 'module M : sig val x : int end = struct let x = "a" end', ['Signature mismatch']),
        ('abstraction-leak', 'module M : sig type t val make : int -> t end = struct type t = int let make x = x end\nlet _ = M.make 1 + 1', ['This expression has type M.t']),
        ('gadt-refinement', 'type _ t = I : int t | B : bool t\nlet f : type a. a t -> a = function I -> true | B -> true', ['should not be a boolean literal']),
    ]
    for name, source, fragments in rejected if not args.lesson else []:
        directory = WORK / 'negative' / name
        if directory.exists(): shutil.rmtree(directory)
        directory.mkdir(parents=True)
        path = directory / 'main.ml'; path.write_text(source + '\n')
        result = run_owned(switch(['ocamlfind', 'ocamlopt', '-w', '+8', '-warn-error', '+8', str(path), '-o', str(directory / 'program')]), env=environment, timeout=60)
        results.append(dict(id=name, variant='expected compiler rejection',
                            passed=result.returncode != 0 and all(f in result.stderr for f in fragments),
                            exit=result.returncode, stderr=result.stderr))
    if input_digests() != inputs:
        raise ValueError('Validation inputs changed during checks')
    report = dict(inputSHA256=inputs, checked=datetime.datetime.now(datetime.timezone.utc).isoformat(), compiler='OCaml ' + version,
                  packages=sorted(packages), lessons=len(lessons),
                  duneProjects=sum(bool(l['project']) for l in lessons), selectedLessons=args.lesson,
                  total=len(results), passed=sum(r['passed'] for r in results), failed=sum(not r['passed'] for r in results),
                  scope='Local trusted guide programs, answers and Dune projects; full runs include six expected diagnostics; no hosted sandbox or mastery grading',
                  cases=[{k: clean(v) if isinstance(v, str) else v for k, v in r.items()} for r in results])
    target = args.report or REPORT
    if report['failed'] and target.resolve() == REPORT.resolve():
        # A failing run must never replace the committed passing receipt.
        target = ROOT / '.build/ocaml-guide-failed-report.json'
        target.parent.mkdir(exist_ok=True)
        print(f'Checks failed; the committed receipt was left alone. Report: {target}', file=sys.stderr)
    target.write_text(json.dumps(report, indent=2) + '\n')
    for r in results:
        if not r['passed']: print(json.dumps(r, indent=2), file=sys.stderr)
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'packages')}, indent=2))
    return bool(report['failed'])


if __name__ == '__main__': sys.exit(main())

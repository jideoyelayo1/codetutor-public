"""Compile/check bundled original Rust, OCaml and Lean examples locally.

This is a development check for repository-authored snippets, not a production
execution sandbox or a learner-facing proof grader. New pack cases also check
expected stdout; earlier seed cases check compilation/execution success.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def run(command, directory, environment, timeout=30):
    return subprocess.run(command, cwd=directory, env=environment, text=True,
                          capture_output=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rustc', default=shutil.which('rustc') or 'rustc')
    parser.add_argument('--ocamlc', default=shutil.which('ocamlc') or 'ocamlc')
    lean_local = ROOT / '.build/toolchains/elan/bin/lean'
    parser.add_argument('--lean', default=str(lean_local) if lean_local.exists() else (shutil.which('lean') or 'lean'))
    parser.add_argument('--report', type=Path, default=ROOT / '.build/snippet-validation.json')
    args = parser.parse_args()
    environment = os.environ.copy()
    if Path(args.lean).resolve() == lean_local.resolve():
        environment['ELAN_HOME'] = str(ROOT / '.build/toolchains/elan')
    tools = {'rust': args.rustc, 'ocaml': args.ocamlc, 'lean': args.lean}
    versions = {}
    for language, executable in tools.items():
        flag = '-version' if language == 'ocaml' else '--version'
        try:
            result = run([executable, flag], ROOT, environment)
        except (OSError, subprocess.TimeoutExpired) as error:
            parser.error(f'{language} compiler unavailable: {error}')
        if result.returncode != 0:
            parser.error(f'{language} compiler unavailable: {result.stderr.strip()}')
        versions[language] = result.stdout.strip()
    curriculum = json.loads((ROOT / 'CodingTeacher/curriculum.json').read_text())
    pack = json.loads((ROOT / 'scripts/learning_pack.json').read_text())
    expectations = {entry['id']: entry for entry in pack['lessons']}
    results = []
    workspace = ROOT / '.build/snippets'
    for lesson in curriculum['lessons']:
        language = lesson['trackID']
        if language not in tools or lesson.get('isSourceStudy'):
            continue
        for variant in ['code', 'solution']:
            if not lesson[variant].strip(): continue
            directory = workspace / lesson['id'] / variant
            directory.mkdir(parents=True, exist_ok=True)
            extension = {'rust': 'rs', 'ocaml': 'ml', 'lean': 'lean'}[language]
            source = directory / ('Main.lean' if language == 'lean' else f'main.{extension}')
            source.write_text(lesson[variant])
            entry = {'lessonID': lesson['id'], 'variant': variant, 'language': language,
                     'outputChecked': lesson['id'] in expectations}
            try:
                if language == 'lean':
                    if re.search(r'\b(?:sorry|admit|axiom)\b', lesson[variant]):
                        raise ValueError('Authored proof contains a placeholder/axiom declaration')
                    checked = run([tools[language], '-DwarningAsError=true', str(source)], directory, environment)
                    compiled = checked
                else:
                    executable = directory / 'program'
                    command = ([tools[language], '--edition=2021', str(source), '-o', str(executable)]
                               if language == 'rust' else
                               [tools[language], '-o', str(executable), str(source)])
                    compiled = run(command, directory, environment)
                    checked = run([str(executable)], directory, environment) if compiled.returncode == 0 else compiled
                entry.update(compileExitCode=compiled.returncode, exitCode=checked.returncode,
                             stdout=checked.stdout, stderr=checked.stderr)
                passed = compiled.returncode == 0 and checked.returncode == 0
                if entry['outputChecked']:
                    expectation = expectations[lesson['id']]
                    if lesson[variant] != expectation[variant]:
                        raise ValueError('Bundled code differs from the authored expectation source')
                    expected = expectation['expectedStdout' if variant == 'code' else 'solutionStdout']
                    entry['expectedStdout'] = expected
                    passed = passed and checked.stdout == expected
                entry['passed'] = passed
            except (OSError, subprocess.TimeoutExpired, ValueError) as error:
                entry.update(passed=False, error=str(error))
            results.append(entry)
            if not entry['passed']:
                print(f"FAIL {lesson['id']} {variant}: " +
                      str(entry.get('error') or entry.get('stderr') or entry.get('stdout')), file=sys.stderr)
    summary = {'checked': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'scope': 'Local authored Rust/OCaml/Lean snippets; not remote execution or grading',
               'versions': versions, 'total': len(results),
               'passed': sum(entry['passed'] for entry in results),
               'outputChecked': sum(entry['outputChecked'] for entry in results),
               'cases': results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: summary[key] for key in ['versions', 'total', 'passed', 'outputChecked']}, indent=2))
    return 0 if all(entry['passed'] for entry in results) and results else 1


if __name__ == '__main__':
    raise SystemExit(main())

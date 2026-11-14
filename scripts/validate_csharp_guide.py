"""Compile and run every C# guide program, answer, expected rejection and project with pinned SDKs.

This is an author-side check. The app's C# runner stays excluded.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from owned_process import run_owned
from csharp_guide import CONTENT_DIR, LESSONS

ROOT = Path(__file__).resolve().parent.parent
DOTNET = ROOT/'.build/toolchains/dotnet/dotnet'
WORK = ROOT/'.build/csharp-guide-checks'
FULL_REPORT = ROOT/'docs/csharp-guide-validation.json'
KNOWN_CHECK_KEYS = {'name', 'args', 'useSolution', 'exit', 'stdout', 'stdoutContains', 'stderr', 'stderrContains', 'stdin', 'mutations'}
SDKS = {'10': ('10.0.402', 'net10.0', '14'), '11': ('11.0.100-rc.2.26504.105', 'net11.0', '15')}


def environment():
    env = os.environ.copy()
    env.update(DOTNET_ROOT=str(DOTNET.parent), DOTNET_MULTILEVEL_LOOKUP='0', DOTNET_CLI_TELEMETRY_OPTOUT='1',
               DOTNET_NOLOGO='1', DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1', NUGET_PACKAGES=str(ROOT/'.build/nuget-packages'),
               # Culture-dependent formatting would make expected stdout machine-specific.
               DOTNET_SYSTEM_GLOBALIZATION_INVARIANT='1', MSBUILDDISABLENODEREUSE='1')
    return env


def project_file(lesson):
    sdk, framework, language = SDKS[lesson.get('sdk', '10')]
    language = lesson.get('langVersion', language)   # e.g. 'preview' for features not yet in the released version
    unsafe = '<AllowUnsafeBlocks>true</AllowUnsafeBlocks>' if lesson.get('unsafe') else ''
    warnings = '' if lesson.get('allowWarnings') else '<TreatWarningsAsErrors>true</TreatWarningsAsErrors>'
    return (f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>{framework}</TargetFramework>'
            f'<LangVersion>{language}</LangVersion><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>'
            f'<AssemblyName>program</AssemblyName>{unsafe}{warnings}</PropertyGroup></Project>\n'), sdk


def pin_sdk(directory, sdk):
    (directory/'global.json').write_text(json.dumps(dict(sdk=dict(version=sdk, rollForward='disable')))+'\n')


def build_and_run(lesson, variant, source, env):
    directory = WORK/lesson['key']/variant
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    text, sdk = project_file(lesson)
    (directory/'program.csproj').write_text(text); pin_sdk(directory, sdk)
    (directory/'Program.cs').write_text(source)
    built = run_owned([str(DOTNET), 'build', '-nologo', '-v', 'q', '-o', 'out'], cwd=directory, env=env, timeout=180)
    return directory, built


def check_program(lesson, variant, env):
    expected = lesson['expectedStdout' if variant == 'code' else 'solutionStdout']
    directory, built = build_and_run(lesson, variant, lesson[variant], env)
    executed = run_owned([str(DOTNET), str(directory/'out/program.dll')], cwd=directory, env=env, timeout=30,
                         input=lesson.get('stdin')) if built.returncode == 0 else built
    passed = built.returncode == 0 and executed.returncode == 0 and executed.stdout == expected
    return dict(id='guide.csharp.'+lesson['key'], variant=variant, passed=passed, buildExit=built.returncode,
                exit=executed.returncode, stdout=executed.stdout if built.returncode == 0 else '', expectedStdout=expected,
                diagnostics=(built.stdout+built.stderr)[-4000:] if not passed else '', stderr=executed.stderr if not passed else '')


def check_rejection(lesson, rejection, env):
    source = (lesson['folder']/rejection['file']).read_text()
    _, built = build_and_run(lesson, 'reject-'+Path(rejection['file']).stem, source, env)
    output = built.stdout+built.stderr
    passed = built.returncode != 0 and rejection['diagnostic'] in output
    return dict(id='guide.csharp.'+lesson['key'], variant='expected rejection '+rejection['diagnostic'], passed=passed,
                buildExit=built.returncode, diagnostics='' if passed else output[-4000:])


def check_project(lesson, env):
    results = []
    sdk = SDKS[lesson.get('sdk', '10')][0]
    for answer in [False, True]:
        directory = WORK/lesson['key']/('project-solution' if answer else 'project-start')
        if directory.exists(): shutil.rmtree(directory)
        for file in lesson['project']+(lesson['projectSolutionFiles'] or [] if answer else []):
            path = directory/file['path']; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(file['content'])
        shipped = json.loads((directory/'global.json').read_text()) if (directory/'global.json').exists() else None
        if shipped is None: pin_sdk(directory, sdk)
        elif shipped.get('sdk', {}).get('version') != sdk: raise ValueError(f"{lesson['key']}: global.json must pin SDK {sdk}")
        start_paths = {f['path'] for f in lesson['project']}
        for check in lesson['projectChecks']:
            if unknown := set(check) - KNOWN_CHECK_KEYS: raise ValueError(f"{lesson['key']}: unknown check keys {sorted(unknown)}")
            if check.get('useSolution', False) != answer: continue
            originals = {}
            try:
                # A mutation proves the tests detect a deliberately injected bug.
                for mutation in check.get('mutations', []):
                    if mutation['path'] not in start_paths: raise ValueError('Mutation must target a bundled start-project file')
                    path = directory/mutation['path']; text = path.read_text()
                    if text.count(mutation['find']) != 1: raise ValueError(f"Mutation must match exactly once: {mutation['path']}")
                    originals.setdefault(path, text)
                    path.write_text(text.replace(mutation['find'], mutation['replace'], 1))
                result = run_owned([str(DOTNET)]+check['args'], cwd=directory, env=env, timeout=600, input=check.get('stdin'))
            finally:
                for path, text in originals.items(): path.write_text(text)
            passed = result.returncode == check.get('exit', 0)
            if 'stdout' in check: passed = passed and result.stdout == check['stdout']
            for text in check.get('stdoutContains', []): passed = passed and text in result.stdout
            if 'stderr' in check: passed = passed and result.stderr == check['stderr']
            if 'stderrContains' in check: passed = passed and check['stderrContains'] in result.stderr
            results.append(dict(id='guide.csharp.'+lesson['key'], variant=check['name'], passed=passed, exit=result.returncode,
                                stdout=result.stdout[-4000:], stderr=result.stderr[-2000:]))
    return results


def check_lesson(lesson, bundled, env):
    actual = bundled['guide.csharp.'+lesson['key']]
    for field, source in [('code', 'code'), ('solution', 'solution'), ('projectFiles', 'project'), ('projectSolutionFiles', 'projectSolutionFiles')]:
        if actual.get(field) != (lesson[source] or None if field.startswith('project') else lesson[source]):
            raise ValueError(f"Bundled {field} differs from source content: {lesson['key']} (rerun make_content.py)")
    results = [check_program(lesson, variant, env) for variant in ['code', 'solution'] if lesson[variant]]
    results += [check_rejection(lesson, rejection, env) for rejection in lesson.get('rejected', [])]
    if lesson['project']:
        results += check_project(lesson, env)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', action='append', choices=[l['key'] for l in LESSONS])
    parser.add_argument('--report', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.lesson and not args.report: parser.error('--lesson requires a separate --report path')
    if args.lesson and args.report.resolve() == FULL_REPORT.resolve():
        parser.error('focused validation cannot replace the full guide report')
    # Hash the generator and this validator too, so a logic change makes an old receipt visibly stale.
    sources = [ROOT/'CodingTeacher/curriculum.json', ROOT/'scripts/csharp_guide.py', Path(__file__).resolve()]+sorted(p for p in CONTENT_DIR.rglob('*') if p.is_file() and p.name != '.DS_Store')
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    env = environment()
    installed = run_owned([str(DOTNET), '--list-sdks'], env=env).stdout
    for sdk, _, _ in SDKS.values():
        if sdk not in installed: raise ValueError(f'.NET SDK {sdk} is required under {DOTNET.parent}')
    curriculum = json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    bundled = {l['id']: l for l in curriculum['lessons']}
    lessons = [l for l in LESSONS if not args.lesson or l['key'] in args.lesson]
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        results = [r for batch in pool.map(lambda l: check_lesson(l, bundled, env), lessons) for r in batch]
    for path, digest in inputs.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Validation input changed during checks: '+path)
    report = dict(inputSHA256=inputs, checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  sdks={major: dict(sdk=sdk, targetFramework=tfm, langVersion=lang) for major, (sdk, tfm, lang) in SDKS.items()},
                  lessons=len(lessons), projects=sum(bool(l['project']) for l in lessons), selectedLessons=args.lesson,
                  total=len(results), passed=sum(r['passed'] for r in results), failed=sum(not r['passed'] for r in results),
                  scope='Local trusted author-side builds with warnings as errors, invariant globalization and exact stdout; expected compiler rejections; project build/test runs. No app C# runner, hosted sandbox or mastery grading.',
                  cases=results)
    (args.report or FULL_REPORT).write_text(json.dumps(report, indent=2)+'\n')
    for r in results:
        if not r['passed']: print(json.dumps(r, indent=2), file=sys.stderr)
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'inputSHA256')}, indent=2))
    return bool(report['failed'])


if __name__ == '__main__': sys.exit(main())

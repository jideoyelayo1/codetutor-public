"""Check the original Lean 4 guide: core and Mathlib programs, proof axioms, diagnostics and Lake projects.

Authoring: `validate_lean_guide.py --fill FRAGMENT.json` compiles every entry of a fragment and writes the real
stdout into expectedStdout/solutionStdout. Acceptance: no flags; compares the committed content with the compiler.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from owned_process import run_owned

ROOT = Path(__file__).resolve().parent.parent
ELAN = ROOT / '.build/toolchains/elan'
MATHLIB = ROOT / '.build/lean-mathlib'
WORK = ROOT / '.build/lean-guide-checks'
CONTENT = ROOT / 'scripts/lean_guide_content.json'
REPORT = ROOT / 'docs/lean-guide-validation.json'
LEAN_VERSION = 'Lean (version 4.35.0,'
MATHLIB_REV = 'v4.35.0'
ALLOWED_AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}
PLACEHOLDER = re.compile(r'\b(sorry|admit)\b')
AXIOM_DECL = re.compile(r'^\s*axiom\b', re.M)
THEOREM = re.compile(r'^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?(?:theorem|lemma)\s+([A-Za-z_][\w.\'?!]*)', re.M)
REQUIRED = ['key', 'stage', 'title', 'body', 'code', 'expectedStdout', 'challenge', 'solution', 'solutionStdout',
            'question', 'correct', 'wrong', 'reasoning', 'sourceURL', 'project']
NEGATIVES = {
    'type-error': ('def x : Nat := "text"\n', False),
    'tactic-error': ('example : 2 + 2 = 5 := by\n  decide\n', False),
    'sorry-placeholder': ('theorem t : 1 = 2 := by\n  sorry\n', False),
    'valid-proof': ('theorem t : 2 + 2 = 4 := rfl\n#print axioms t\n', True),
}


def environment():
    env = os.environ.copy()
    env.update(ELAN_HOME=str(ELAN), PATH=f'{ELAN/"bin"}{os.pathsep}{env["PATH"]}')
    return env


def uses_mathlib(source):
    return re.search(r'^\s*import\s+Mathlib', source, re.M) is not None


def compile_source(directory, source, name='Main.lean', timeout=None):
    """Return (CompletedProcess, mode). Mathlib files run inside the pinned authoring Lake project."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name; path.write_text(source)
    if uses_mathlib(source):
        return run_owned([str(ELAN/'bin/lake'), 'env', 'lean', '-DwarningAsError=true', str(path)],
                         cwd=MATHLIB, env=environment(), timeout=timeout or 240), 'mathlib'
    return run_owned([str(ELAN/'bin/lean'), '-DwarningAsError=true', str(path)],
                     cwd=directory, env=environment(), timeout=timeout or 90), 'core'


def axiom_report(directory, source):
    """Return the set of axioms used by the file's theorems, or None when it declares none."""
    names = THEOREM.findall(source)
    if not names:
        return None
    probe = source + '\n' + ''.join(f'#print axioms {n}\n' for n in names)
    done, _ = compile_source(directory, probe, 'Axioms.lean')
    if done.returncode != 0:
        return {'compile-failed'}
    used = set()
    for listed in re.findall(r"depends on axioms: \[([^\]]*)\]", done.stdout):
        used.update(a.strip() for a in listed.split(','))
    return used - {''}


def check_source(identifier, variant, source, expected, allow_axiom):
    where = WORK / identifier / variant
    problems = []
    if PLACEHOLDER.search(source): problems.append('contains sorry/admit')
    if AXIOM_DECL.search(source) and not allow_axiom: problems.append('declares an axiom')
    done, mode = compile_source(where, source)
    if done.returncode != 0: problems.append('compile failed')
    if expected is not None and done.stdout != expected: problems.append('stdout differs')
    used = axiom_report(where, source) if done.returncode == 0 and not allow_axiom else None
    if used and not used <= ALLOWED_AXIOMS: problems.append(f'unexpected axioms {sorted(used - ALLOWED_AXIOMS)}')
    return dict(id=identifier, variant=variant, mode=mode, passed=not problems, problems=problems, exit=done.returncode,
                stdout=done.stdout, expectedStdout=expected, axioms=sorted(used) if used else [], stderr=done.stderr[-2000:])


def write_project(directory, files):
    for item in files:
        target = directory / item['path']; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item['content'])


def check_project(entry, identifier):
    """Starter must build (warnings allowed); solution must build warning-free and match projectExpected."""
    results = []
    base = WORK / identifier / 'project'
    for variant, files in (('starter', entry['project']), ('solution', entry['project'])):
        if variant == 'solution' and not entry.get('projectSolutionFiles'): continue
        directory = base / variant
        shutil.rmtree(directory, ignore_errors=True); directory.mkdir(parents=True)
        write_project(directory, files)
        if variant == 'solution': write_project(directory, entry['projectSolutionFiles'])
        args = ['build'] + (['--wfail'] if variant == 'solution' else [])
        built = run_owned([str(ELAN/'bin/lake')] + args, cwd=directory, env=environment(), timeout=600)
        problems = [] if built.returncode == 0 else ['lake build failed']
        stdout = built.stdout
        if variant == 'solution':
            text = '\n'.join(f['content'] for f in directory_files(directory))
            if PLACEHOLDER.search(text): problems.append('solution contains sorry/admit')
            if entry.get('projectExe') and not problems:
                ran = run_owned([str(ELAN/'bin/lake'), 'exe', entry['projectExe']], cwd=directory, env=environment(), timeout=60)
                stdout = ran.stdout
                if ran.returncode != 0 or ran.stdout != entry['projectExpected']: problems.append('exe output differs')
        results.append(dict(id=identifier, variant='project-' + variant, mode='lake', passed=not problems, problems=problems,
                            exit=built.returncode, stdout=stdout, expectedStdout=entry.get('projectExpected'), stderr=built.stderr[-2000:]))
    return results


def directory_files(directory):
    for path in sorted(directory.rglob('*.lean')):
        if '.lake' not in path.parts: yield dict(path=str(path), content=path.read_text())


def schema_problems(entry):
    problems = [f'missing {k}' for k in REQUIRED if k not in entry]
    if problems: return problems
    if len(entry['body']) < 3: problems.append('body needs at least three paragraphs')
    if len(entry['wrong']) != 3 or entry['correct'] in entry['wrong']: problems.append('need exactly three distinct wrong options')
    if not re.match(r'^\d\d · ', entry['stage']): problems.append('stage must look like "NN · Title"')
    if not entry['sourceURL'].startswith('https://'): problems.append('sourceURL must be https')
    for k in ('title', 'challenge', 'question', 'reasoning'):
        if not entry[k].strip(): problems.append(f'empty {k}')
    return problems


def check_entry(entry):
    identifier = 'guide.lean.' + entry['key']
    results = []
    allow = bool(entry.get('allowAxiom'))
    for variant, expected in (('code', entry['expectedStdout']), ('solution', entry['solutionStdout'])):
        if entry[variant].strip(): results.append(check_source(identifier, variant, entry[variant], expected, allow))
    if entry['project']: results += check_project(entry, identifier)
    return results


def fill(path):
    """Authoring only: record the compiler's real stdout. The author reads it against the lesson's reasoning."""
    entries = json.loads(path.read_text())
    seen = set()
    for entry in entries:
        assert entry['key'] not in seen, f'duplicate key {entry["key"]}'; seen.add(entry['key'])
        entry.setdefault('project', [])
        entry.setdefault('expectedStdout', ''); entry.setdefault('solutionStdout', '')
        bad = schema_problems(entry)
        for variant, field in (('code', 'expectedStdout'), ('solution', 'solutionStdout')):
            if not entry[variant].strip(): continue
            r = check_source('guide.lean.' + entry['key'], variant, entry[variant], None, bool(entry.get('allowAxiom')))
            if not r['passed']: bad.append(f'{variant}: {r["problems"]} {r["stderr"][:400]} {r["stdout"][:400]}')
            entry[field] = r['stdout']
        if entry['project']: bad += [f'{r["variant"]}: {r["problems"]} {r["stderr"][:400]}' for r in check_entry(entry) if not r['passed']]
        print(('FAIL ' if bad else 'ok   ') + entry['key']); [print('     ', b) for b in bad]
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + '\n')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fill', type=Path, help='authoring: compile a fragment and record real stdout')
    parser.add_argument('--lesson', action='append')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.lesson and not args.report: parser.error('--lesson requires a separate --report path')
    if args.lesson and args.report.resolve() == REPORT.resolve(): parser.error('focused validation cannot replace the full guide report')
    version = run_owned([str(ELAN/'bin/lean'), '--version'], env=environment()).stdout.strip()
    if not version.startswith(LEAN_VERSION): raise ValueError('Lean 4.35.0 is required for these checks')
    if args.fill: return fill(args.fill)
    lessons = json.loads(CONTENT.read_text())
    selected = [l for l in lessons if not args.lesson or l['key'] in args.lesson]
    curriculum = {l['id']: l for l in json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())['lessons']}
    results, schema = [], []
    for entry in selected:
        problems = schema_problems(entry)
        bundled = curriculum.get('guide.lean.' + entry['key'])
        if bundled is None: problems.append('not bundled in curriculum.json')
        elif not problems and any(bundled[v] != entry[v] for v in ('code', 'solution')): problems.append('bundled example differs')
        schema += [dict(id='guide.lean.' + entry['key'], problems=problems)] if problems else []
        if not problems: results += check_entry(entry)
    negatives = []
    for name, (source, should_pass) in NEGATIVES.items():
        done, _ = compile_source(WORK / 'negatives' / name, source)
        negatives.append(dict(name=name, expectedPass=should_pass, passed=(done.returncode == 0) == should_pass, exit=done.returncode))
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
              [ROOT/'CodingTeacher/curriculum.json', CONTENT]}
    ok = all(r['passed'] for r in results) and all(n['passed'] for n in negatives) and not schema
    report = dict(validatedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), toolchain=version,
                  mathlib=MATHLIB_REV, platform=sys.platform, inputs=inputs, lessons=len(selected), checks=len(results) + len(negatives),
                  passed=sum(r['passed'] for r in results) + sum(n['passed'] for n in negatives), schemaProblems=schema,
                  negatives=negatives, results=results)
    (args.report or REPORT).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f'{report["passed"]}/{report["checks"]} checks passed across {report["lessons"]} lessons')
    for r in results:
        if not r['passed']: print('FAIL', r['id'], r['variant'], r['problems'])
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

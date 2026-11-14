"""Original, versioned Go guide; stage modules are authored offline and generation is offline."""
import importlib
from pathlib import Path
import re
import sys

CONTENT = Path(__file__).with_name('go_guide_content')
SPEC = 'https://go.dev/ref/spec'
COURSE = dict(id='guide.go', title='Go: from first program to mastery', kind='Language guide',
    edition='Go 1.27 · checked with go1.27.2 on 16 October 2026',
    scope='An ordered guide with explanations, checked examples, practice, answers, checkpoints, recall and tested Go module projects, '
          'from first program through generics, iterators, concurrency, the memory model, runtime performance, networking, unsafe and tooling. '
          'Read-and-predict only: the app does not execute Go. Exhaustive specification/standard-library depth remains under audit.',
    trackIDs=['go'],
    sourceURL=SPEC)


def tabs(source):
    """Stage modules indent Go with four spaces; gofmt-canonical Go uses tabs."""
    # shortcut: also rewrites leading spaces inside multi-line raw strings; author those with \t, and the validator's exact-stdout check catches mistakes
    return re.sub(r'^((?:    )+)', lambda m: '\t' * (len(m.group(1)) // 4), source, flags=re.M)


def _normalise(entry):
    for field in ['code', 'solution']:
        if entry.get(field): entry[field] = tabs(entry[field])
    for field in ['project', 'projectSolutionFiles']:
        for file in entry.get(field) or []:
            if file['path'].endswith('.go'): file['content'] = tabs(file['content'])
    for check in entry.get('projectChecks', []):
        for mutation in check.get('mutations', []):
            if mutation['path'].endswith('.go'):
                mutation['find'], mutation['replace'] = tabs(mutation['find']), tabs(mutation['replace'])
    entry.setdefault('project', None)
    if entry['project'] and not entry.get('expectedStdout'):
        entry['expectedStdout'] = 'Every command in the project instructions produces the output listed there.\n'
    return entry


def _load():
    sys.path.insert(0, str(CONTENT.parent))
    lessons = []
    for path in sorted(CONTENT.glob('stage_*.py')):
        module = importlib.import_module(f'go_guide_content.{path.stem}')
        lessons += [_normalise(dict(entry)) for entry in module.LESSONS]
    return lessons


LESSONS = _load()


def apply(content):
    """Append the Go guide without editing or renumbering any previous record."""
    # Imported here so the backend can load this module as scripts.go_guide for LESSONS alone.
    from guide_builder import apply_guide
    return apply_guide(content, LESSONS, 'go', 'Go 1.27 reference and learning sources', 'Go 1.27 source reference',
        'Original guided lessons and checked examples; reference-level depth audit ongoing', COURSE)

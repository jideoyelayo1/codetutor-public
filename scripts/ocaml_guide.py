"""Original, versioned OCaml guide; content is preformatted and generation is offline."""
import hashlib
import json
from pathlib import Path

CONTENT_DIR = Path(__file__).with_name("ocaml_guide_content")
PROJECTS = CONTENT_DIR / "projects"
BOOK = "https://ocaml.org/manual/5.5/index.html"


def tree(directory):
    """Project files as {path, content} records, sorted so the bundle is stable."""
    files = [p for p in sorted(directory.rglob('*')) if p.is_file() and p.name != '.DS_Store']
    for p in files:
        parts = p.relative_to(directory).parts
        # Running dune inside a start/ or solution/ tree must not ship its output.
        if '_build' in parts or '.git' in parts or p.name == '.merlin' or p.suffix == '.install':
            raise ValueError(f'Build artifact in project tree: {p}')
    return [dict(path=str(p.relative_to(directory)), content=p.read_text()) for p in files]


def load_project(directory):
    """A project lesson is lesson.json plus start/ (shown files) and solution/ (files the answer replaces)."""
    entry = json.loads((directory / 'lesson.json').read_text())
    if 'n' not in entry:
        raise ValueError(f"Project lesson needs an explicit order 'n': {entry['key']}")
    entry.setdefault('code', ''); entry.setdefault('solution', '')
    entry.setdefault('expectedStdout', ''); entry.setdefault('solutionStdout', '')
    entry['project'] = tree(directory / 'start')
    entry['projectSolutionFiles'] = tree(directory / 'solution')
    return entry


PARTS = sorted(CONTENT_DIR.glob("*.json")) + sorted(p for p in PROJECTS.rglob("*") if p.is_file() and p.name != '.DS_Store')
listed = [(entry, index) for part in sorted(CONTENT_DIR.glob("*.json")) for index, entry in enumerate(json.loads(part.read_text()), 1)]
projects = [(load_project(path.parent), 0) for path in sorted(PROJECTS.glob("*/lesson.json"))]
# Order within a stage follows an explicit "n" when present, else the position in its file.
ordered = sorted(listed + projects, key=lambda item: (item[0]['stage'], item[0].get('n', item[1])))
LESSONS = [entry for entry, index in ordered]

# Two lessons sharing a position in a stage would be ordered by accident, not by design.
positions = [(entry['stage'], entry.get('n', index)) for entry, index in ordered]
if len(set(positions)) != len(positions):
    raise ValueError('Two OCaml guide lessons share a position within a stage')

if len({entry['key'] for entry in LESSONS}) != len(LESSONS):
    raise ValueError('Duplicate OCaml guide lesson key')


def apply(content):
    """Append a new guide without editing or renumbering any previous record."""
    chapters = []
    stages = sorted(dict.fromkeys(entry['stage'] for entry in LESSONS))
    for number, stage in enumerate(stages, 1):
        records = [entry for entry in LESSONS if entry['stage'] == stage]
        chapters.append(dict(id=f'guide.ocaml.stage-{number:02}', title=stage,
            coverage='Original guided lessons and checked examples; reference-level depth audit ongoing',
            note='Work through explanations and examples, solve the practice before revealing its answer, then complete the checkpoint and review the cards.',
            sections=[r['title'] for r in records], lessonIDs=['guide.ocaml.' + r['key'] for r in records],
            reading=dict(title='OCaml manual, CS 3110, Real World OCaml and Jane Street sources', url=records[0]['sourceURL'], section=stage)))
    for entry in LESSONS:
        identifier = 'guide.ocaml.' + entry['key']
        correct = entry['correct']; options = [correct] + entry['wrong']
        shift = int(hashlib.sha256(identifier.encode()).hexdigest()[:8], 16) % len(options)
        options = options[shift:] + options[:shift]
        lesson = dict(id=identifier, trackID='ocaml', title=entry['title'], summary=entry['stage'], body=entry['body'],
            code=entry['code'], solution=entry['solution'], challenge=entry['challenge'], question=entry['question'],
            options=options, answerIndex=options.index(correct), explanation=entry['reasoning'],
            workedExample=(f"Expected output:\n{entry['expectedStdout']}\n{entry['reasoning']}"
                           if entry['expectedStdout'] else entry['reasoning']),
            practiceAnswer=entry['reasoning'], isSourceStudy=True, minutes=entry.get('minutes', 20),
            order=sum(l['trackID'] == 'ocaml' for l in content['lessons']) + 1, sourceURL=entry['sourceURL'],
            reading=[dict(title='OCaml source reference', url=entry['sourceURL'], section=entry['title'])] + entry.get('additionalReadings', []))
        if entry['project']: lesson['projectFiles'] = entry['project']
        if entry.get('projectInstructions'): lesson['projectInstructions'] = entry['projectInstructions']
        if entry.get('projectSolutionFiles'): lesson['projectSolutionFiles'] = entry['projectSolutionFiles']
        content['lessons'].append(lesson)
        for n, (prompt, answer) in enumerate([(entry['question'], correct + ' ' + entry['reasoning']),
                ('What should you check when using ' + entry['title'].lower() + '?', entry['body'][-1])], 1):
            content['cards'].append(dict(id=f'{identifier}.{n}', trackID='ocaml', lessonID=identifier, prompt=prompt, answer=answer, sourceURL=entry['sourceURL']))
    content['sourceCourses'].append(dict(id='guide.ocaml', title='OCaml: from first program to Jane Street-style systems',
        kind='Language guide', edition='OCaml 5.5 · Dune 3 · Jane Street v0.17 libraries',
        scope='An ordered guide with explanations, runnable examples, practice, answers, checkpoints, recall and tested Dune projects. Complete manual/book and source-exercise depth coverage remains under audit.',
        trackIDs=['ocaml'], sourceURL=BOOK, chapters=chapters))
    return content

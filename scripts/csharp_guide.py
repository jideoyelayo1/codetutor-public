"""Original, versioned C# guide; content is preformatted and generation is offline.

Layout: csharp_guide_content/NN-stage/stage.json names a stage; each MM-key/ lesson folder holds
lesson.json, code.cs, solution.cs and, for projects, start/ (shown files) and solution/ (answer files).
"""
import hashlib
import json
from pathlib import Path

CONTENT_DIR = Path(__file__).with_name("csharp_guide_content")
GUIDE = "https://learn.microsoft.com/en-us/dotnet/csharp/"


def tree(directory):
    """Project files as {path, content} records, sorted so the bundle is stable."""
    if not directory.exists():
        return None
    files = [p for p in sorted(directory.rglob('*')) if p.is_file() and p.name != '.DS_Store']
    for p in files:
        if {'bin', 'obj'} & set(p.relative_to(directory).parts):
            raise ValueError(f'Build output in project tree: {p}')
    return [dict(path=str(p.relative_to(directory)), content=p.read_text()) for p in files]


def load():
    lessons = []
    for stage_dir in sorted(p for p in CONTENT_DIR.iterdir() if p.is_dir()):
        stage = json.loads((stage_dir/'stage.json').read_text())['title']
        for folder in sorted(p for p in stage_dir.iterdir() if p.is_dir()):
            entry = json.loads((folder/'lesson.json').read_text())
            entry['stage'] = stage
            entry['folder'] = folder
            for variant in ['code', 'solution']:
                path = folder/f'{variant}.cs'
                entry[variant] = path.read_text() if path.exists() else ''
            entry['project'] = tree(folder/'start')
            entry['projectSolutionFiles'] = tree(folder/'solution')
            lessons.append(entry)
    keys = [entry['key'] for entry in lessons]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate C# guide lesson key')
    return lessons


LESSONS = load()


def plain(text):
    """Lesson prose, checkpoints and cards render as plain text, so drop Markdown code-span backticks."""
    return text.replace('`', '')


def apply(content):
    """Append the guide without editing or renumbering any previous record."""
    chapters = []
    for number, stage in enumerate(dict.fromkeys(entry['stage'] for entry in LESSONS), 1):
        records = [entry for entry in LESSONS if entry['stage'] == stage]
        chapters.append(dict(id=f'guide.csharp.stage-{number:02}', title=stage,
            coverage='Original guided lessons with compiled and executed examples; reference-level depth audit ongoing',
            note='Read the explanation, predict the example output, solve the practice before revealing its answer, then complete the checkpoint and review the cards.',
            sections=[r['title'] for r in records], lessonIDs=['guide.csharp.'+r['key'] for r in records],
            reading=dict(title='Microsoft C# documentation', url=records[0]['sourceURL'], section=stage)))
    for entry in LESSONS:
        identifier = 'guide.csharp.'+entry['key']
        correct = plain(entry['correct']); options = [correct]+[plain(w) for w in entry['wrong']]
        shift = int(hashlib.sha256(identifier.encode()).hexdigest()[:8], 16) % len(options)
        options = options[shift:]+options[:shift]
        # Shown before the checkpoint, so it must not reveal the example's output or the checkpoint answer.
        worked = ('Work through the project files below, run its commands, then attempt the practice before revealing the answer files.'
                  if entry['project'] else
                  'Read the example line by line and write down exactly what it prints before revealing the solution, which shows the expected output.')
        if entry['project']:
            answer = f"Worked answer for: {plain(entry['challenge'])} The replacement files below build and pass the project's checks."
        else:
            answer = (f"Expected output of the example:\n{entry['expectedStdout']}\nWorked answer for: {plain(entry['challenge'])}\n"
                      f"Its output:\n{entry['solutionStdout']}")
        lesson = dict(id=identifier, trackID='csharp', title=entry['title'], summary=entry['stage'],
            # Source-study prose renders as plain text, so drop Markdown code-span backticks.
            body=[plain(paragraph) for paragraph in entry['body']],
            code=entry['code'], solution=entry['solution'], challenge=plain(entry['challenge']), question=plain(entry['question']),
            options=options, answerIndex=options.index(correct), explanation=plain(entry['reasoning']),
            workedExample=worked, practiceAnswer=answer, isSourceStudy=True,
            minutes=entry.get('minutes', 20), order=sum(l['trackID'] == 'csharp' for l in content['lessons'])+1,
            sourceURL=entry['sourceURL'],
            reading=[dict(title='Microsoft C# reference', url=entry['sourceURL'], section=entry['title'])]+entry.get('additionalReadings', []))
        for field, value in [('projectFiles', entry['project']), ('projectInstructions', entry.get('projectInstructions')),
                             ('projectSolutionFiles', entry['projectSolutionFiles'])]:
            if value: lesson[field] = value
        content['lessons'].append(lesson)
        for n, (prompt, answer) in enumerate([(plain(entry['question']), correct+' '+plain(entry['reasoning'])),
                                              (f"What should you check when applying '{entry['title']}'?", plain(entry.get('recallAnswer', entry['body'][-1])))], 1):
            content['cards'].append(dict(id=f'{identifier}.{n}', trackID='csharp', lessonID=identifier, prompt=prompt, answer=answer, sourceURL=entry['sourceURL']))
    content['sourceCourses'].append(dict(id='guide.csharp', title='C#: from first program to advanced .NET', kind='Language guide',
        edition='C# 14 · .NET 10 LTS (SDK 10.0.402), plus a C# 15 · .NET 11 RC 2 stage · checked 16 October 2026',
        scope='An ordered guide with explanations, compiled examples, practice, answers, checkpoints, recall and tested multi-file projects. The C# runner stays excluded: examples are verified by the author toolchain, not executed in the app. Complete language/runtime/library depth remains under audit.',
        trackIDs=['csharp'], sourceURL=GUIDE, chapters=chapters))
    return content

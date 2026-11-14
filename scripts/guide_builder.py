"""Shared builder for original ordered language and concept guides; appends without renumbering existing records."""
import hashlib


def apply_guide(content, lessons, track_id, chapter_reading, lesson_reading, chapter_coverage, course, prefix='guide.', chapter_key=None):
    prefix = f'{prefix}{track_id}.'
    chapters = []
    stages = sorted(dict.fromkeys(entry['stage'] for entry in lessons))
    for number, stage in enumerate(stages, 1):
        records = [entry for entry in lessons if entry['stage'] == stage]
        chapters.append(dict(id=prefix+(chapter_key(stage) if chapter_key else f'stage-{number:02}'), title=stage, coverage=chapter_coverage,
            note='Work through explanations and examples, solve the practice before revealing its answer, then complete the checkpoint and review the cards.',
            sections=[r['title'] for r in records], lessonIDs=[prefix+r['key'] for r in records],
            reading=dict(title=chapter_reading, url=records[0]['sourceURL'], section=stage)))
    for entry in lessons:
        identifier=prefix+entry['key']
        correct=entry['correct']; options=[correct]+entry['wrong']
        shift=int(hashlib.sha256(identifier.encode()).hexdigest()[:8],16)%len(options)
        options=options[shift:]+options[:shift]
        lesson=dict(id=identifier, trackID=track_id, title=entry['title'], summary=entry['stage'], body=entry['body'],
            code=entry['code'], solution=entry['solution'], challenge=entry['challenge'], question=entry['question'],
            options=options, answerIndex=options.index(correct), explanation=entry['reasoning'],
            workedExample=f"Expected output:\n{entry['expectedStdout']}\n{entry['reasoning']}",
            practiceAnswer=entry['reasoning'], isSourceStudy=True, minutes=entry.get('minutes',20),
            order=sum(l['trackID']==track_id for l in content['lessons'])+1, sourceURL=entry['sourceURL'],
            reading=[dict(title=lesson_reading,url=entry['sourceURL'],section=entry['title'])]+entry.get('additionalReadings',[]))
        extra=[]
        for number,quiz in enumerate(entry.get('quiz',[]),1):
            choices=[quiz['correct']]+quiz['wrong']
            turn=int(hashlib.sha256(f'{identifier}.q{number}'.encode()).hexdigest()[:8],16)%len(choices)
            choices=choices[turn:]+choices[:turn]
            extra.append(dict(question=quiz['question'],options=choices,answerIndex=choices.index(quiz['correct']),explanation=quiz['reasoning']))
        if extra: lesson['extraQuizzes']=extra
        if entry['project']: lesson['projectFiles']=entry['project']
        if entry.get('projectInstructions'): lesson['projectInstructions']=entry['projectInstructions']
        if entry.get('projectSolutionFiles'): lesson['projectSolutionFiles']=entry['projectSolutionFiles']
        content['lessons'].append(lesson)
        for n,(prompt,answer) in enumerate([(entry['question'],correct+' '+entry['reasoning']),('What should you check when using '+entry['title'].lower()+'?',entry['body'][-1])],1):
            content['cards'].append(dict(id=f'{identifier}.{n}',trackID=track_id,lessonID=identifier,prompt=prompt,answer=answer,sourceURL=entry['sourceURL']))
        # Extra checkpoint questions also become recall cards, numbered after the two standard cards.
        for n,quiz in enumerate(extra,3):
            content['cards'].append(dict(id=f'{identifier}.{n}',trackID=track_id,lessonID=identifier,prompt=quiz['question'],answer=quiz['options'][quiz['answerIndex']]+' '+quiz['explanation'],sourceURL=entry['sourceURL']))
    content['sourceCourses'].append({**course, 'chapters': chapters})
    return content

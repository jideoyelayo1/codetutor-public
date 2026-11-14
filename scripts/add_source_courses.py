"""Deterministic source-course expansion using original material and metadata only."""
import hashlib,json
from pathlib import Path
from source_topics import records
from source_snippets import SNIPPETS

def apply(content):
    courses=json.loads(Path(__file__).with_name('source_catalog.json').read_text())
    content['sourceCourses']=courses
    references={}
    for course in courses:
        for chapter in course['chapters']:
            for key in chapter['lessonIDs']:
                references.setdefault(key,[]).append(chapter['reading'])
    for topic in records():
        id='source.'+topic['key'];track=topic['trackID']
        readings=references.get(id,[])
        # Prefer the course's public link, else the track's first resource.
        public=next((r['url'] for r in readings if r.get('url')),None)
        public=public or next(t for t in content['tracks'] if t['id']==track)['resources'][0]['url']
        correct=topic['options'][0]
        shift=int(hashlib.sha256(id.encode()).hexdigest()[:8],16)%3
        options=topic['options'][shift:]+topic['options'][:shift]
        lesson=dict(id=id,trackID=track,title=topic['title'],summary='Source practice · '+topic['title'],body=topic['body'],workedExample=topic['workedExample'],code='',challenge=topic['challenge'],solution='',practiceAnswer=topic['solution'],question=topic['question'],options=options,answerIndex=options.index(correct),explanation=topic['solution'],minutes=15,order=sum(l['trackID']==track for l in content['lessons'])+1,sourceURL=public,isSourceStudy=True,reading=readings[:3])
        if topic['key'] in SNIPPETS:
            lesson['code']=SNIPPETS[topic['key']][0]
        content['lessons'].append(lesson)
        for n,(prompt,answer) in enumerate(topic['recall']):
            content['cards'].append(dict(id=f'{id}.{n+1}',trackID=track,lessonID=id,prompt=prompt,answer=answer,sourceURL=public))
    return content

"""Explicit reinforcement links; mappings do not establish exhaustive adaptation."""
COMPANIONS = {
    'cpp.raii':['raii','unique-ownership'],
    'cpp.move':['move-semantics','forwarding'],
    'cpp.races':['mutex-invariants','release-acquire'],
    'source.cpp-build':['first-program','odr-and-linkage'],
    'source.cpp-types':['initialization','conversions','scope-and-const'],
    'source.cpp-sequences':['vector-values','sequence-containers','iterator-invalidation'],
    'source.cpp-classes':['class-invariants','const-members','destruction-order'],
    'source.cpp-streams':['stream-state','stream-format-state'],
    'source.cpp-algorithms':['algorithm-erase','ordering-contracts','iterator-categories'],
    'source.cpp-copy':['rule-of-zero','move-semantics','guaranteed-elision'],
    'source.cpp-operators':['operator-design','hidden-friends'],
    'source.cpp-index-call':['span','invoke','reference-qualified-members'],
    'source.cpp-exceptions':['error-paths','exception-guarantees','raii'],
    'source.cpp-files':['filesystem','binary-encoding'],
    'source.cpp-namespaces':['odr-and-linkage','hidden-friends','dependent-names'],
    'source.cpp-macros':['preprocessor'],
    'source.cpp-templates':['function-templates','deduction-and-auto','specialization','sfinae','variadic-templates','detection-idiom'],
    'source.cpp-polymorphism':['inheritance-and-slicing','virtual-destruction'],
    'source.cpp-work-pools':['pipeline-project','jthread-stop'],
    'source.cpp-constexpr':['constexpr','consteval'],
    'source.cpp-allocation-functions':['alignment-and-allocation','pmr-resources','allocator-ring-project'],
    'source.cpp-formatting':['stream-format-state','formatting'],
    'source.cpp-file-position':['filesystem','binary-encoding'],
}


def apply_links(content, problems):
    import json
    lessons={l['id']:l for l in content['lessons']}
    for course in content['sourceCourses']:
        if 'cpp' not in course['trackIDs'] or course['kind']=='Language guide':continue
        for chapter in course['chapters']:
            additions=[]
            for original in list(chapter['lessonIDs']):
                for key in COMPANIONS.get(original,[]):
                    id='guide.cpp.'+key
                    if id not in additions:additions.append(id)
            for id in additions:
                lesson=lessons[id]
                if id not in chapter['lessonIDs']:chapter['lessonIDs'].append(id)
                reading=chapter['reading']
                if json.dumps(reading,sort_keys=True) not in {json.dumps(r,sort_keys=True) for r in lesson['reading']}:
                    lesson['reading'].append(reading.copy())
                if course['id'] not in lesson['requirements']['sourceIDs']:lesson['requirements']['sourceIDs'].append(course['id'])
    for problem in problems:problem['sourceIDs']=lessons[problem['lessonID']]['requirements']['sourceIDs'].copy()

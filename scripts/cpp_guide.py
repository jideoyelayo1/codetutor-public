"""Append original version-labelled C++ guide/practice without changing earlier IDs."""
import hashlib
from collections import defaultdict
from cpp_lessons import UNITS
from cpp_projects import PROJECTS
import cpp_expert  # Registers additional original units with the same authoring contract.
import cpp23_lessons
import cpp_more_basics, cpp_more_ownership, cpp_more_generic, cpp_more_library, cpp_more_expert  # noqa: F401 (register units/drills)
from cpp_drills import DRILLS, PLATFORM_SPECIFIC, PLATFORM_PREFIX

ALL_UNITS = sorted(UNITS + PROJECTS, key=lambda entry: entry['stage'])
COSTS = {
    'resize-overwrite23':'The displayed callback writes n characters in O(n) work. Capacity management and allocation are separate string implementation costs.',
    'ranges-to23':'Materializing n integer results performs linear traversal and element construction with O(n) owned result storage, excluding allocator-specific costs.',
    'zip23':'A complete traversal visits min(n,m) pairs. The view itself does not materialize an independent result container.',
    'flat-map23':'Lookup uses logarithmic key comparisons, while an insertion can move a linear number of stored elements. Check operation-specific iterator invalidation.',
    'optional-monadic23':'Only the engaged branch invokes the successful-value callbacks. Account for each callback and any constructed value; absence bypasses those calls.',
    'expected-monadic23':'Success and error branches invoke different callbacks. Type-level composition does not eliminate callback, copying, or error-reporting costs.',
    'vector-values':'Appending is amortized constant time; a growth reallocation can move or copy all existing elements. Storage is linear in capacity.',
    'initializer-list-selection':'Both vector constructions are linear in the number of constructed elements; different overloads construct different element counts.',
    'string-values':'Copying an n-element string is linear in n. Mutation and append can reallocate; no small-string allocation policy is assumed.',
    'control-flow':'The traversal is O(n) time with a constant-size accumulator, subject to integer-range preconditions.',
    'recursion':'The recursive version uses O(n) calls and O(n) call-stack depth; the answer loop uses O(n) work and O(1) auxiliary state for the bounded input domain.',
    'iterator-invalidation':'Repeated vector erasures can make the full loop quadratic because later elements shift. Compare a single erase-remove pass for large inputs.',
    'algorithm-erase':'The remove pass and tail erasure perform linear work in the original element count, excluding element-operation costs.',
    'ordering-contracts':'std::sort requires O(n log n) comparisons; comparator correctness is a precondition, independent of that bound.',
    'ordered-and-hashed':'The displayed ordered-map lookups and insertions use logarithmic key comparisons. Hash-container average and worst-case contracts differ.',
    'sets-and-duplicates':'Ordered lookup uses logarithmic comparisons, while enumerating k equivalent entries adds output-sensitive work.',
    'priority-queues':'top is constant time; heap maintenance for push/pop is logarithmic in element count, excluding backing-container allocation.',
    'ranges-pipelines':'A complete traversal inspects the source elements and applies predicates/transforms as needed. Laziness avoids an output container but does not eliminate source traversal.',
    'numeric-algorithms':'accumulate traverses n elements and applies n reduction steps; representation range and floating evaluation order still matter.',
    'from-chars':'Parsing examines a bounded input range. Whole-token validation must check the returned position as well as the error code.',
    'performance-contracts':'Binary search on this random-access vector uses logarithmically many comparisons. Maintaining sorted input is a separate cost.',
    'regex':'No general small worst-case runtime is claimed: cost depends on pattern, input, grammar, and implementation. Bound input and consider a direct parser.',
    'parser-project':'The line answer scans input tokens with linear input traversal and constant-sized numeric state. It borrows token views only during the call.',
    'value-project':'Successful checked fixed-width arithmetic uses constant-sized work and storage. Error reporting can have separate allocation and exception costs.',
    'allocator-ring-project':'push/pop use constant index work plus element operations. Storage is O(Capacity), destruction is O(size), and allocator costs belong to the resource policy.',
    'pipeline-project':'Pending work is bounded by queue capacity; scheduling and waiting have no promised real-time bound. Every accepted integer must be processed before finish returns.',
    'coroutine-project':'The sample counter performs linear work in yielded values and retains constant-sized frame state. Frame allocation may be implementation-dependent.',
    'design-project':'Each displayed area operation performs a fixed amount of scalar work. The closed variant stores its selected alternative directly; extending the type set changes its interface.',
}


def apply(content):
    problems, quizzes, chapters = [], [], []
    grouped = defaultdict(list)
    previous = None
    for number, entry in enumerate(ALL_UNITS, 1):
        identifier = 'guide.cpp.' + entry['key']
        stage = entry['stage']
        grouped[stage].append(identifier)
        options = [entry['correct']] + entry['wrong']
        shift = int(hashlib.sha256(identifier.encode()).hexdigest()[:8], 16) % len(options)
        options = options[shift:] + options[:shift]
        level = int(stage[:2])
        difficulty = 'Beginner' if level <= 2 else 'Intermediate' if level in (3,4,7) else 'Expert' if level in (8,9,11) else 'Advanced'
        reference = entry.get('referenceOnly', False)
        support = ('Reference-only exercise; executable support has not been verified. Consult the linked adopted specification and current compiler/library tables.' if reference else
                   'Intentional compile rejection; compare its diagnostic with the repaired answer.' if entry.get('expectedDiagnostic') else
                   'Local toolchain validation is recorded separately. Remote compiler flags and library support are chosen by the configured server.')
        support = entry.get('support', support)
        command = ('cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug && cmake --build build && ctest --test-dir build --output-on-failure' if entry.get('projectFiles') else
                   'Reference and design exercise; no executable claim.' if reference else
                   f'DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun --sdk macosx clang++ -std=c++{entry["standard"]} -Wall -Wextra -pedantic-errors -pthread main.cpp -o main && ./main')
        requirements = dict(standard=entry['standard'], difficulty=difficulty, topics=entry['topics'],
                            prerequisiteLessonIDs=[previous] if previous else [], sourceIDs=entry['sourceIDs'].copy(),
                            support=support, compileCommand=command,
                            serverDefaultCompatible=entry['standard'] == 14 and bool(entry['code']) and not entry.get('expectedDiagnostic'))
        lesson = dict(id=identifier, trackID='cpp', title=entry['title'], summary=stage, body=entry['body'],
                      code=entry['code'], challenge=entry['challenge'], solution=entry['solution'],
                      question=entry['question'], options=options, answerIndex=options.index(entry['correct']),
                      explanation=entry['reasoning'], practiceAnswer=entry['practiceAnswer'],
                      workedExample=('Expected compiler diagnostic contains: ' + entry['expectedDiagnostic'] if entry.get('expectedDiagnostic') else
                                     'Expected stdout: ' + repr(entry['expectedStdout']) if entry['code'] else entry['practiceAnswer']),
                      minutes=entry.get('minutes',20), order=sum(l['trackID']=='cpp' for l in content['lessons'])+1,
                      sourceURL=entry['sourceURL'], isSourceStudy=True, requirements=requirements,
                      reading=[dict(title='C++ specification companion',url=entry['sourceURL'],section=entry['title'])])
        for field in ('projectFiles','projectInstructions','projectSolutionFiles'):
            if field in entry: lesson[field] = entry[field]
        content['lessons'].append(lesson)
        recall_context = entry['title']+'\n'+entry['question']+ ('\n\nProgram:\n'+entry['code'] if entry['code'] else '')
        for n, (prompt, answer) in enumerate([(recall_context,entry['correct']+' '+entry['reasoning']),
                                              ('Explain the safety boundary in '+entry['title']+'.',entry['body'][-1])],1):
            content['cards'].append(dict(id=f'{identifier}.{n}',trackID='cpp',lessonID=identifier,prompt=prompt,answer=answer,sourceURL=entry['sourceURL']))
        problem = dict(id='problem.cpp.'+entry['key'],lessonID=identifier,title=entry['title'],prompt=entry['challenge'],
                       kind=entry.get('kind') or ('Design' if reference else 'Project' if entry.get('projectFiles') else 'Debugging' if entry.get('expectedDiagnostic') else 'Implementation'),
                       difficulty=difficulty,standard=entry['standard'],topics=entry['topics'],sourceIDs=entry['sourceIDs'],
                       hints=[entry['body'][0],entry['body'][-1]], starter=entry['code'],solution=entry['solution'],
                       explanation=entry['practiceAnswer'],quizExplanation=entry['reasoning'],rubric=[entry['practiceAnswer'], 'Explain why the checkpoint answer is correct: '+entry['reasoning']],
                       edgeCases=[entry['body'][-1]],
                       complexity=COSTS.get(entry['key'],'This is an interface or language-rule exercise without a claimed asymptotic algorithm bound. Explain the specific copies, allocations, and lifetime requirements before drawing performance conclusions.'),
                       question=entry['question'],options=options,answerIndex=options.index(entry['correct']))
        problems.append(problem)
        previous = identifier
    for number, (stage, ids) in enumerate(grouped.items(),1):
        stage_id=f'guide.cpp.stage-{number:02}'
        chapters.append(dict(id=stage_id,title=stage,coverage='Original guided teaching and checked practice; exhaustive source adaptation is tracked separately.',
                             note='Prerequisites are recommendations. Read, solve, explain, then complete the checkpoint and revisit the recall cards.',
                             sections=[next(x['title'] for x in ALL_UNITS if 'guide.cpp.'+x['key']==id) for id in ids],lessonIDs=ids,
                             reading=dict(title='C++ standards and teaching companions',url='https://isocpp.org/std',section=stage)))
        chosen=[p['id'] for p in problems if p['lessonID'] in ids][:10]
        # A short project/reference stage supplements its own questions with prerequisite checks.
        for p in reversed(problems):
            if len(chosen) == 10: break
            if p['kind'] != 'Project' and p['id'] not in chosen: chosen.append(p['id'])
        quizzes.append(dict(id=f'quiz.cpp.stage-{number:02}',title=stage+' · revision quiz',stageID=stage_id,
                            questionIDs=chosen,durationSeconds=900,passPercent=80))
    lesson_problem={p['lessonID']:p for p in problems}
    drills=[]
    for entry in DRILLS:
        base=lesson_problem['guide.cpp.'+entry['lesson']]
        options=[entry['correct']]+entry['wrong']
        shift=int(hashlib.sha256(entry['id'].encode()).hexdigest()[:8],16)%len(options)
        options=options[shift:]+options[:shift]
        lesson=next(l for l in content['lessons'] if l['id']==base['lessonID'])
        support=('Checked locally: '+entry['check']+'.' if entry['check']!='reasoning' else
                 'Reasoning drill; no executable claim. Layout answers assume arm64 LP64 macOS with Apple clang.')
        question=(PLATFORM_PREFIX if entry['id'].split('.drill.')[1] in PLATFORM_SPECIFIC else '')+entry['question']
        drills.append(dict(id=entry['id'],lessonID=base['lessonID'],title=entry['title'],prompt=question,
                           kind=entry['kind'],difficulty=entry['difficulty'] or base['difficulty'],
                           standard=entry['standard'] or base['standard'],topics=base['topics'],sourceIDs=base['sourceIDs'],
                           hints=[lesson['body'][0],support],starter=entry['code'],solution='',
                           explanation=entry['explanation'],quizExplanation=entry['explanation'],
                           rubric=['State the answer and the rule that decides it: '+entry['explanation']],
                           edgeCases=[lesson['body'][-1]],complexity=entry['complexity'] or base['complexity'],
                           question=question,options=options,answerIndex=options.index(entry['correct'])))
    assert len({d['id'] for d in drills})==len(drills)
    stage_of={l:number for number,ids in enumerate(grouped.values(),1) for l in ids}
    def ranked(pool):
        return sorted(pool,key=lambda p:hashlib.sha256(p['id'].encode()).hexdigest())
    for number,ids in enumerate(grouped.values(),1):
        pool=[d for d in drills if d['lessonID'] in ids]
        if len(pool)>=15:
            quizzes.append(dict(id=f'quiz.cpp.drills-stage-{number:02}',title=f'{list(grouped)[number-1]} · drill quiz',
                                stageID=f'guide.cpp.stage-{number:02}',questionIDs=[d['id'] for d in ranked(pool)[:15]],
                                durationSeconds=900,passPercent=80))
    mocks=[('beginner','Beginner',(1,2)),('intermediate','Intermediate',(3,4,6,7)),('expert','Expert',(5,9,10)),('low-latency','Low-latency and performance',(8,11))]
    for slug,label,stages in mocks:
        pool=[d for d in drills if stage_of[d['lessonID']] in stages]
        if len(pool)>=25:
            quizzes.append(dict(id=f'quiz.cpp.mock-{slug}',title=f'C++ mock interview · {label}',stageID=None,
                                questionIDs=[d['id'] for d in ranked(pool)[:25]],durationSeconds=1800,passPercent=80))
    placement=[]
    for ids in list(grouped.values())[:10]:
        eligible=[p['id'] for p in problems if p['lessonID'] in ids]
        placement += eligible[:2]
    quizzes.insert(0,dict(id='quiz.cpp.placement',title='C++ placement · choose where to begin',stageID=None,
                          questionIDs=placement,durationSeconds=0,passPercent=80))
    from cpp_source_links import apply_links
    apply_links(content, problems)
    content['problems']=(content.get('problems') or [])+problems+drills
    content['quizzes']=(content.get('quizzes') or [])+quizzes
    content['sourceCourses'].append(dict(id='guide.cpp',title='C++14+: from first program to advanced systems',kind='Language guide',
        edition='C++14 / 17 / 20 / 23; separate reference-only C++26 material',
        scope='An original progressive guide with offline practice, quizzes, recall, and six CMake projects. Open any stage. Complete subsection and exercise adaptation of the supplied books and playlists remains tracked separately; this guide is not an exhaustive source-completion claim.',
        trackIDs=['cpp'],sourceURL='https://isocpp.org/std',chapters=chapters))
    return content

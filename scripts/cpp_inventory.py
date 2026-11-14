"""Reproducible gap inventory; header use is never labelled full API coverage."""
from collections import Counter
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
# Header names checked against the working draft [headers] on 15 October 2026.
HEADERS='''algorithm any array atomic barrier bit bitset charconv chrono compare complex concepts
condition_variable contracts coroutine debugging deque exception execution expected filesystem flat_map flat_set
format forward_list fstream functional future generator hazard_pointer hive initializer_list inplace_vector
iomanip ios iosfwd iostream istream iterator latch limits linalg list locale map mdspan memory memory_resource
meta mutex new numbers numeric optional ostream print queue random ranges ratio rcu regex scoped_allocator
semaphore set shared_mutex simd source_location span spanstream sstream stack stacktrace stdexcept stdfloat
stop_token streambuf string string_view syncstream system_error text_encoding thread tuple type_traits
typeindex typeinfo unordered_map unordered_set utility valarray variant vector version cassert cctype cerrno
cfenv cfloat cinttypes climits clocale cmath csetjmp csignal cstdarg cstddef cstdint cstdio cstdlib cstring ctime
cuchar cwchar cwctype'''.split()


def main():
    content=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
    lessons=[l for l in content['lessons'] if l['id'].startswith('guide.cpp.')]
    used={h:[] for h in HEADERS}
    for lesson in lessons:
        code=lesson['code']+lesson['solution']+'\n'.join(f['content'] for f in lesson.get('projectFiles',[])+lesson.get('projectSolutionFiles',[]))
        for header in set(re.findall(r'#include\s*<([^>]+)>',code)):
            if header in used:used[header].append(lesson['id'])
    report=dict(checked='2026-10-16',scope='Original-guide inventory and explicit gaps. Neither use of a header nor a passing program establishes complete language, API, or source-exercise adaptation.',
                sources=['https://eel.is/c++draft/headers','https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/n5051.html','https://gcc.gnu.org/projects/cxx-status.html','https://clang.llvm.org/cxx_status.html'],
                exhaustiveLanguageVerified=False,exhaustiveLibraryVerified=False,exhaustiveSourceAdaptationVerified=False,
                originalGuideLessons=len(lessons),
                drills=dict(total=sum('.drill.' in p['id'] for p in content.get('problems',[])),
                            byKind=dict(Counter(p['kind'] for p in content.get('problems',[]) if '.drill.' in p['id']))),
                quizzes=len([q for q in content.get('quizzes',[]) if q['id'].startswith('quiz.cpp.')]),originalGuideCards=sum(c['lessonID'].startswith('guide.cpp.') for c in content['cards']),
                minimumStandardDistribution=dict(Counter(str(l['requirements']['standard']) for l in lessons)),
                stages=[dict(id=c['id'],title=c['title'],originalUnitIDs=c['lessonIDs'],exhaustiveDepthVerified=False) for c in next(c for c in content['sourceCourses'] if c['id']=='guide.cpp')['chapters']],
                draftHeaderChecklist=[dict(header=h,usedInOriginalExamples=used[h],fullAPIAdaptationVerified=False) for h in sorted(HEADERS)],
                remaining=['Watch all playlist videos and inventory substantive internal examples, timestamps, and practice beyond video titles.',
                           'Audit every remaining semantic subclause and named requirement. Original units now introduce value categories, lookup corners, allocation propagation, placement/launder lifetime, noexcept and a deprecated/removed-feature catalogue; these are teaching units, not a clause-by-clause audit.',
                           'Adapt APIs and exercises for headers without examples and expand depth within headers already used; inspect older-standard and deprecated headers separately from the current draft checklist.',
                           'Complete C++26 feature and feature-macro audit and verify runnable examples on appropriate compilers/libraries; the five current units remain reference-only.',
                           'Validate module dependency builds, additional library implementations, actual remote profiles, and Linux GCC; the local macOS run does not establish them.'])
    (ROOT/'docs/cpp-language-inventory.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()

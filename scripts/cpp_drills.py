"""Original short C++ drills (prediction, UB, compiles?, layout, complexity, concurrency).

Each drill attaches to a guide lesson key. IDs are problem.cpp.drill.<lesson>.<n> in
registration order per lesson, so new drills must be appended, never inserted.
"""
DRILLS = []
# Output drills whose answer depends on the implementation (sizes, layout, capacity, float encoding).
PLATFORM_SPECIFIC = {'span.1', 'counting-operator-new.4', 'binary-encoding.2', 'hot-cold-splitting.1',
                     'inline-static-members.3', 'strict-aliasing-rule.2'}
PLATFORM_PREFIX = 'On arm64 macOS with Apple clang and libc++: '
CHECKS = ('output', 'compiles', 'reject', 'ubsan', 'asan', 'tsan', 'reasoning')
KINDS = ('Predict output', 'Undefined behavior', 'Compiles?', 'Copies and moves', 'Layout',
         'Complexity', 'Concurrency', 'Code review', 'Concept')


def drill(lesson, kind, title, code, question, correct, wrong, explanation,
          check='output', standard=None, difficulty=None, diagnostic=None, complexity=None):
    """check semantics (validated by validate_cpp_guide.py):
    output    compile+run; stdout without its final newline must equal `correct`.
    compiles  must compile cleanly and exit 0 (answer to "does it compile?" is yes).
    reject    must fail to compile; stderr must contain `diagnostic` when given.
    ubsan/asan/tsan  the sanitizer must report on a run.
    reasoning no executable claim (layout facts are stated for arm64 LP64 macOS)."""
    assert kind in KINDS, kind
    assert check in CHECKS, check
    assert len(wrong) >= 2 and correct not in wrong, (lesson, title)
    assert check == 'reasoning' or code, (lesson, title)
    n = 1 + sum(d['lesson'] == lesson for d in DRILLS)
    DRILLS.append(dict(id=f'problem.cpp.drill.{lesson}.{n}', lesson=lesson, kind=kind, title=title,
                       code=code, question=question, correct=correct, wrong=list(wrong),
                       explanation=explanation, check=check, standard=standard,
                       difficulty=difficulty, diagnostic=diagnostic, complexity=complexity))


def main_program(body, headers='iostream', declarations=''):
    """Convenience: a complete program printing via std::cout."""
    includes = ''.join('#include <' + h + '>\n' for h in headers.split())
    return includes + declarations + ('\n' if declarations else '') + 'int main() {\n' + body + '\n}\n'

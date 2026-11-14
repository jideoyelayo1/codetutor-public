"""Additional original C++ units and drills for stages 01-02."""
from cpp_lessons import unit, program
from cpp_drills import drill, main_program

# Drills for existing stage-01 lessons
drill('integer-limits','Undefined behavior','Signed overflow in a loop bound',
      main_program('    int x = std::numeric_limits<int>::max();\n    x = x + 1;\n    std::cout << x << "\\n";','iostream limits'),
      'What does the C++ standard say about this program?','It has undefined behavior: signed int overflow',
      ['It prints INT_MIN because signed arithmetic wraps','It prints 0'],
      'Signed integer overflow is undefined. UBSan reports it; an optimizer may assume it never happens.',check='ubsan')
drill('conversions','Predict output','Integer division before conversion',
      main_program('    double d = 7 / 2;\n    std::cout << d << "\\n";'),
      'What does this print?','3',['3.5','4'],
      'Both operands are int, so 7 / 2 evaluates to 3 before the result converts to double.')
drill('initialization','Compiles?','Narrowing in braces',
      main_program('    double d = 2.5;\n    int n{d};\n    std::cout << n << "\\n";'),
      'Does this program compile?','No: brace initialization rejects the narrowing double-to-int conversion',
      ['Yes, and it prints 2','Yes, and it prints 3'],
      'List-initialization forbids narrowing conversions from a non-constant double to int.',check='reject',diagnostic='narrowing')
drill('vector-values','Layout','sizeof an empty vector',
      '','On arm64 macOS with libc++, what is sizeof(std::vector<int>)?','24 bytes: three pointers',
      ['4 bytes: one int','It depends on the number of elements'],
      'libc++ stores begin, end and capacity-end pointers. sizeof is a compile-time property and never depends on the element count.',check='reasoning')

# New stage-01 lessons
S='01 First programs, types, and expressions'
unit(S,'istream-input-checks','Reading input means checking every extraction',14,
     'std::cin is an object of type std::istream, so a function that accepts std::istream& can read the keyboard, a file stream, or an in-memory string stream. Writing the reader against the stream type keeps parsing testable without a terminal.|Formatted extraction skips leading whitespace, reads as many characters as form a value, and stops. If no digits can be read, the stream sets failbit and, since C++11, stores 0 in the destination. Reading "12x" succeeds with 12 and leaves x unread for the next extraction.|Never use a value before testing the stream. A range check such as value >= 0 is a separate decision from a successful parse, and trailing characters after a valid prefix need an explicit policy.',
     program('sstream', '    std::istringstream input("x12");\n    int count = -1;\n    const bool ok = read_count(input, count);\n    std::cout << ok << " " << count << "\\n";',
             'bool read_count(std::istream& in, int& out) {\n    int value = 0;\n    if (!(in >> value) || value < 0) return false;\n    out = value;\n    return true;\n}\n'),'0 -1\n',
     ('Give the reader the valid input 12.', '"x12"', '"12"', '1 12\n', 'Extraction succeeds and the nonnegative check passes, so the function writes the output parameter. With x12 the extraction fails first and count keeps its sentinel.'),
     'After a failed std::cin >> n on the input abc, what holds since C++11?', 'n is 0 and failbit is set', ['n keeps its previous value and no flag changes','The program throws std::invalid_argument'], 'Failed numeric extraction stores zero and sets failbit. Streams do not throw unless exceptions() was configured.', 'istream.formatted')
unit(S,'auto-deduction','auto deduces a type from its initializer',14,
     'auto asks the compiler to deduce a variable type from its initializer using template argument deduction rules. It saves repetition of long names but the variable still has one fixed static type.|Plain auto drops top-level const and references: auto copy = limit makes a mutable int copy. Write auto& or const auto& when you want a reference. auto x = {1, 2} deduces std::initializer_list<int>, which is a frequent surprise.|auto does not mean dynamic typing, and it can hide a proxy type such as std::vector<bool>::reference. Spell the type when the exact representation is part of the reasoning.',
     program('', '    const int limit = 10;\n    auto copy = limit;\n    copy += 5;\n    const auto& ref = limit;\n    std::cout << copy << " " << ref << "\\n";'),'15 10\n',
     ('Deduce copy from the floating expression limit / 4.0.', 'auto copy = limit;', 'auto copy = limit / 4.0;', '7.5 10\n', 'limit / 4.0 has type double, so copy is a double holding 2.5; adding five gives 7.5. The reference still observes limit.'),
     'What type does auto x = {1, 2}; deduce?', 'std::initializer_list<int>', ['int','std::vector<int>'], 'Copy-list-initialization with auto deduces an initializer_list. Only direct-list auto x{1} deduces int in C++17.', 'dcl.spec.auto')
unit(S,'fixed-std-array','std::array keeps a fixed extent with value semantics',14,
     'std::array<T, N> wraps a built-in array of N elements in a class type. The extent is part of the type, size() is available, and the elements live inside the object with no heap allocation.|Unlike a built-in array, std::array copies and assigns as a value and does not decay to a pointer when passed to a function. at() checks the index and throws std::out_of_range; operator[] does not check.|Passing a large std::array by value copies every element. Use const std::array<T, N>& for read-only access, and remember that the extent is fixed at compile time.',
     program('array', '    std::array<int, 3> a{1, 2, 3};\n    std::array<int, 3> b = a;\n    b[0] = 9;\n    std::cout << a[0] << " " << b[0] << " " << a.size() << "\\n";'),'1 9 3\n',
     ('Modify a instead of b after the copy.', 'b[0] = 9;', 'a[0] = 9;', '9 1 3\n', 'b was copied before the write, so the change to a does not reach it. The extent remains part of the type.'),
     'What happens when a std::array<int, 3> is passed by value?', 'All three elements are copied into the parameter', ['Only a pointer to the first element is passed','The array decays and loses its size'], 'std::array is a class type with value semantics; only built-in arrays decay to pointers.', 'array.overview')
unit(S,'string-view-borrow','string_view borrows characters it does not own',17,
     'std::string_view is a pointer and a length describing characters owned by something else. Passing it by value is cheap and accepts std::string, string literals, and character ranges without copying.|remove_prefix and remove_suffix shrink the view without touching the characters. A view need not be null-terminated, so do not pass data() to a C function expecting a terminated string.|The owner must outlive every view. Binding a view to a temporary std::string or keeping a view across a modification that reallocates the string leaves it dangling.',
     program('string string_view', '    const std::string line = "to be or not";\n    std::string_view word = line;\n    word.remove_prefix(3);\n    std::cout << word << " " << count_spaces(word) << "\\n";',
             'std::size_t count_spaces(std::string_view text) {\n    std::size_t spaces = 0;\n    for (char c : text) if (c == \' \') ++spaces;\n    return spaces;\n}\n'),'be or not 2\n',
     ('Also drop the last four characters from the view.', 'word.remove_prefix(3);', 'word.remove_prefix(3);\n    word.remove_suffix(4);', 'be or 1\n', 'remove_suffix(4) drops " not". The underlying string is unchanged; only the view shrinks.'),
     'Is std::string_view v = std::string("hi"); safe to read afterwards?', 'No; the temporary string is destroyed and v dangles', ['Yes, string_view copies the characters','Yes, the temporary lives as long as v'], 'A view does not extend the lifetime of what it refers to. The temporary dies at the end of the full-expression.', 'string.view')
unit(S,'bit-and-compound-ops','Bitwise, compound, and increment operators',14,
     'The bitwise operators &, |, ^ and ~ act on each bit of an integer; << and >> shift. Unsigned types are the usual choice for flag sets because their bit patterns and wrapping are fully specified.|Compound assignment such as flags |= mask reads, combines and stores once. Postfix i++ yields the old value and prefix ++i yields the updated object. Small operands such as unsigned char are promoted to int before bitwise operators apply.|Shifting by a negative count or by at least the width of the promoted type is undefined. == binds tighter than &, so x & 1 == 0 means x & (1 == 0); parenthesize mask tests.',
     program('', '    unsigned flags = 0u;\n    flags |= 1u << 2;\n    flags |= 1u;\n    flags &= ~1u;\n    int i = 5;\n    const int post = i++;\n    const int pre = ++i;\n    std::cout << flags << " " << (flags ^ 6u) << " " << post << " " << pre << "\\n";'),'4 2 5 7\n',
     ('Replace the clearing step with flags ^= 3u.', 'flags &= ~1u;', 'flags ^= 3u;', '6 0 5 7\n', 'Before the change flags is 5 (binary 101). XOR with 011 gives 110, which is 6, and 6 ^ 6 is 0.'),
     'How does x & 1 == 0 group?', 'x & (1 == 0)', ['(x & 1) == 0','It is a syntax error'], 'Equality has higher precedence than bitwise AND, so the comparison happens first.', 'expr.shift')
unit(S,'struct-aggregates','Structs group named members',14,
     'A struct defines a class type whose members are public by default. A simple struct with public data members and no user-provided constructors is an aggregate and can be initialized with braces in member order.|Since C++14 an aggregate may have default member initializers. Members omitted from a brace list take their default initializer, or are value-initialized if there is none. Copying a struct copies every member.|Brace initialization rejects narrowing and extra initializers. Members are laid out in declaration order with possible padding, so do not assume sizeof equals the sum of member sizes.',
     program('', '    Point a;\n    Point b{3, -4};\n    Point c = b;\n    c.x = 1;\n    std::cout << a.x << " " << manhattan(b) << " " << b.x << "\\n";',
             'struct Point {\n    int x = 0;\n    int y = 0;\n};\n\nint manhattan(Point p) {\n    return (p.x < 0 ? -p.x : p.x) + (p.y < 0 ? -p.y : p.y);\n}\n'),'0 7 3\n',
     ('Initialize b with only its first member, 3.', 'Point b{3, -4};', 'Point b{3};', '0 3 3\n', 'The omitted y uses its default member initializer 0, so the distance is 3. c is still an independent copy.'),
     'Given struct Point { int x = 0; int y = 0; }; what is b.y after Point b{3};?', '0', ['3','Indeterminate'], 'Omitted aggregate members use their default member initializers.', 'dcl.init.aggr')
unit(S,'header-source-split','Headers declare; source files define',14,
     'Larger programs put declarations in a header and definitions in a source file. Each .cpp that needs the interface includes the header; the compiler checks calls against the declarations and the linker connects calls to the single definition.|#include pastes text, so the same header can arrive twice in one translation unit. An include guard (#ifndef NAME, #define NAME, #endif) makes the second copy expand to nothing. #pragma once is a widely supported but nonstandard alternative. The example shows both copies inline in one file.|A non-inline function or variable definition in a header included by two source files violates the one-definition rule and usually fails at link time. Put definitions in one .cpp, or mark them inline.',
     program('', '    std::cout << area(Size{3, 4}) << "\\n";',
             '// size.h, as it would appear after being included twice\n#ifndef SIZE_H\n#define SIZE_H\nstruct Size { int w; int h; };\nint area(Size s);\n#endif\n#ifndef SIZE_H\n#define SIZE_H\nstruct Size { int w; int h; };\nint area(Size s);\n#endif\n\n// size.cpp\nint area(Size s) { return s.w * s.h; }\n'),'12\n',
     ('Define perimeter in the source part and print it after the area.', [('int area(Size s) { return s.w * s.h; }', 'int area(Size s) { return s.w * s.h; }\nint perimeter(Size s) { return 2 * (s.w + s.h); }'), ('area(Size{3, 4}) << "\\n"', 'area(Size{3, 4}) << " " << perimeter(Size{3, 4}) << "\\n"')], None, '12 14\n', 'The new definition lives once in the source part. The guard still removes the second struct definition, which would otherwise be a redefinition error.'),
     'Why does a header containing int twice(int x) { return 2 * x; } fail when included by two .cpp files?', 'Two translation units define the same non-inline function, violating the one-definition rule', ['Include guards are missing','Functions cannot be defined in headers under any circumstances'], 'Include guards work per translation unit only. Each .cpp gets its own copy of the definition, and the linker sees two.', 'basic.def.odr')
unit(S,'char-and-escapes','Characters are small integers with escapes',14,
     'char holds one code unit. Character literals such as \'A\' have type char in C++, and arithmetic on a char promotes it to int, so printing letter + 2 prints a number unless it is converted back.|Escape sequences encode characters that are hard to type: \\n newline, \\t tab, \\\\ backslash, \\" quote, \\0 null, plus octal and \\x hexadecimal forms. The standard guarantees that the digits 0 to 9 are contiguous, so c - \'0\' converts a digit character.|Letters are not guaranteed contiguous, and whether plain char is signed is implementation-defined. Use std::isdigit and friends with a value converted to unsigned char.',
     program('', '    const char letter = \'A\';\n    const char next = static_cast<char>(letter + 2);\n    std::cout << next << " " << static_cast<int>(next) << " " << (\'7\' - \'0\') << "\\n";\n    std::cout << "tab:\\t|quote:\\"|slash:\\\\" << "\\n";'),'C 67 7\ntab:\t|quote:"|slash:\\\n',
     ('Start from the lowercase letter x instead.', "const char letter = 'A';", "const char letter = 'x';", 'z 122 7\ntab:\t|quote:"|slash:\\\n', 'In ASCII x is 120, so adding two gives z with code 122. The digit conversion and escaped line are unchanged.'),
     'Which property does the standard guarantee for the basic character set?', 'The digits 0 to 9 have consecutive values', ['The letters a to z have consecutive values','char is signed'], 'Only decimal digit contiguity is guaranteed; letter contiguity is an ASCII property and char signedness is implementation-defined.', 'lex.charset')
unit(S,'type-alias-using','Type aliases rename a type, they do not create one',14,
     'using Name = Type; introduces another name for an existing type; typedef Type Name; is the older equivalent. Aliases shorten long spellings and document intent.|An alias is the same type as its target. Two aliases of double are interchangeable, overloads cannot be distinguished by alias, and a const applied to a pointer alias makes the pointer itself const.|An alias does not prevent mixing units. If the argument order of meters and seconds matters, a distinct struct type is needed to make the compiler reject a swap.',
     program('', '    const Meters distance = 100.0;\n    const Seconds time = 8.0;\n    std::cout << speed(time, distance) << "\\n";',
             'using Meters = double;\ntypedef double Seconds;\n\ndouble speed(Meters d, Seconds t) { return d / t; }\n'),'0.08\n',
     ('Fix the swapped arguments.', 'speed(time, distance)', 'speed(distance, time)', '12.5\n', 'Both aliases name double, so the swapped call compiled silently. Passing distance first computes 100 / 8.'),
     'Does using Meters = double; stop a Seconds value being passed where Meters is expected?', 'No; both are the type double', ['Yes; aliases are distinct types','Only with braces'], 'An alias declaration introduces a name, not a new type.', 'dcl.typedef')

# New stage-02 lessons
S='02 Control flow, functions, and boundaries'
unit(S,'switch-and-fallthrough','switch dispatches on integral values',17,
     'switch evaluates an integral or enumeration condition once and jumps to the matching case label, or to default. Case labels must be constant expressions with distinct values.|Execution continues through following labels until a break or the end of the switch. C++17 [[fallthrough]] marks an intentional fall-through so compilers that warn on implicit fall-through stay quiet. The attribute documents intent; it does not change behavior.|A jump to a case label may not skip the initialization of a variable still in scope. Put such declarations inside braces. Strings cannot be switched on directly.',
     program('', '    std::cout << score(\'A\') << " " << score(\'B\') << " " << score(\'Z\') << "\\n";',
             'int score(char grade) {\n    int points = 0;\n    switch (grade) {\n    case \'A\':\n        points += 2;\n        [[fallthrough]];\n    case \'B\':\n        points += 1;\n        break;\n    case \'C\':\n        break;\n    default:\n        points = -1;\n    }\n    return points;\n}\n'),'3 1 -1\n',
     ('Stop grade A from falling into the B case.', 'points += 2;\n        [[fallthrough]];', 'points += 2;\n        break;', '2 1 -1\n', 'break leaves the switch after the A case, so A earns two points instead of three.'),
     'If [[fallthrough]] is removed but no break is added, does case A still continue into case B?', 'Yes; the attribute only documents intent', ['No; C++17 stops at the next label','It becomes a compile error'], 'Fall-through is the default switch behavior. The attribute affects diagnostics only.', 'dcl.attr.fallthrough')
unit(S,'loop-exits','do-while, break, continue, and nested exits',14,
     'A do-while loop runs its body before testing the condition, so the body executes at least once. A for loop tests first and may run zero times.|continue skips to the next iteration: in a for loop the increment runs next, and in a while or do-while loop the condition is tested next. break leaves only the innermost loop or switch.|To leave nested loops, use a flag tested by the outer condition, return from a helper function, or restructure. A loop that edits its own counter or relies on break to stop needs an argument that it terminates.',
     program('', '    int attempts = 0;\n    do {\n        ++attempts;\n    } while (attempts < 0);\n    int found_row = -1, found_col = -1;\n    for (int r = 0; r < 3 && found_row < 0; ++r) {\n        for (int c = 0; c < 3; ++c) {\n            if (c == r) continue;\n            if (r * 3 + c == 5) { found_row = r; found_col = c; break; }\n        }\n    }\n    std::cout << attempts << " " << found_row << " " << found_col << "\\n";'),'1 1 2\n',
     ('Search for the cell numbered 7.', 'r * 3 + c == 5', 'r * 3 + c == 7', '1 2 1\n', 'Row 2, column 1 has number 7. The break stops the inner loop and the found_row flag stops the outer one.'),
     'Which loop does break exit when it appears inside two nested for loops?', 'Only the innermost loop', ['Both loops','The enclosing function'], 'break transfers control to the end of the smallest enclosing loop or switch.', 'stmt.break')
unit(S,'function-pointer-basics','Function pointers select behavior at run time',14,
     'A function name converts to a pointer to that function. A pointer such as int (*)(int, int) can be stored, passed and called, letting a caller choose an operation at run time. A type alias makes the declarator readable.|Calls through a function pointer look like ordinary calls; op(a, b) and (*op)(a, b) mean the same. A lambda with no captures converts to a matching function pointer; a capturing lambda does not.|Calling a null function pointer is undefined. The pointer type must match exactly; casting to a different function type and calling through it is undefined.',
     program('', '    const int values[] = {2, 3, 4};\n    BinaryOp op = &add;\n    std::cout << fold(values, values + 3, 0, op) << " " << fold(values, values + 3, 1, mul) << "\\n";',
             'int add(int a, int b) { return a + b; }\nint mul(int a, int b) { return a * b; }\nusing BinaryOp = int (*)(int, int);\n\nint fold(const int* first, const int* last, int init, BinaryOp op) {\n    for (; first != last; ++first) init = op(init, *first);\n    return init;\n}\n'),'9 24\n',
     ('Add max_of and fold with it instead of add.', [('int mul(int a, int b) { return a * b; }', 'int mul(int a, int b) { return a * b; }\nint max_of(int a, int b) { return a < b ? b : a; }'), ('BinaryOp op = &add;', 'BinaryOp op = &max_of;')], None, '4 24\n', 'max_of has the same signature, so it fits BinaryOp. Folding from zero keeps the largest element, 4.'),
     'Can [k](int x) { return x + k; } convert to int (*)(int)?', 'No; only captureless lambdas convert to function pointers', ['Yes, captures are copied into the pointer','Yes, with static_cast'], 'A function pointer has no storage for captured state.', 'conv.func')
unit(S,'static-local-state','Static locals persist across calls',14,
     'A local variable declared static has static storage duration: it is initialized the first time control passes through its declaration and keeps its value between calls until program end.|Since C++11, that first initialization is thread-safe; concurrent callers wait for it to finish. Later reads and writes are ordinary accesses and need synchronization if threads share them.|Hidden state makes a function harder to test and reason about. Prefer passing state explicitly unless a lazily built, program-lifetime value is truly intended.',
     program('', '    next_id();\n    next_id();\n    const int third = next_id();\n    std::cout << third << "\\n";',
             'int next_id() {\n    static int counter = 0;\n    return ++counter;\n}\n'),'3\n',
     ('Start the counter at 100.', 'static int counter = 0;', 'static int counter = 100;', '103\n', 'The initializer runs once; three increments follow it.'),
     'In C++11 and later, which part of a function-local static is automatically thread-safe?', 'Its first initialization', ['Every later read and write','Nothing; it always needs a mutex'], 'The standard requires concurrent initialization to wait; subsequent accesses are not synchronized.', 'stmt.dcl')
unit(S,'argv-parsing','Command-line arguments are an array of C strings',14,
     'A hosted program may declare int main(int argc, char* argv[]). argv holds argc pointers to null-terminated strings, followed by argv[argc], which is a null pointer. argv[0] usually names the program and may be empty.|Compare C strings with std::strcmp or by constructing std::string; == on two char pointers compares addresses. Writing the parser against (argc, argv) parameters lets a test pass a fixed array, as the example does.|Validate every argument: count, flags, and numeric conversion. std::atoi returns 0 for garbage with no error indication, so prefer a checked conversion.',
     program('cstring', '    const char* const fake[] = {"tool", "-v", "input.txt", "-v", nullptr};\n    const int argc = 4;\n    std::cout << count_flag(argc, fake) << "\\n";',
             'int count_flag(int argc, const char* const argv[]) {\n    int seen = 0;\n    for (int i = 1; i < argc; ++i) {\n        if (std::strcmp(argv[i], "-v") == 0) ++seen;\n    }\n    return seen;\n}\n'),'2\n',
     ('Count the arguments that are not flags instead.', 'if (std::strcmp(argv[i], "-v") == 0) ++seen;', "if (argv[i][0] != '-') ++seen;", '1\n', 'Starting at index one skips the program name; only input.txt does not begin with a dash.'),
     'What is argv[argc] in a hosted program?', 'A null pointer', ['The last argument','An empty string'], 'The argument array is terminated by a null pointer after the last argument.', 'basic.start.main')
unit(S,'handler-order','Catch handlers are tried in order',14,
     'When an exception is thrown, the handlers of the enclosing try block are tested from top to bottom, and the first whose type matches is chosen. A handler for a base class matches derived exceptions.|Order handlers from most derived to least derived: std::out_of_range before std::logic_error before std::exception. Catch by const reference so derived information is not sliced away and no copy is made.|A base handler placed first makes later derived handlers unreachable. catch (...) catches everything and belongs last; use throw; inside a handler to rethrow the original exception.',
     program('stdexcept', '    for (int i = 0; i < 2; ++i) {\n        try {\n            fail(i);\n        } catch (const std::out_of_range& e) {\n            std::cout << "range:" << e.what() << "\\n";\n        } catch (const std::logic_error& e) {\n            std::cout << "logic:" << e.what() << "\\n";\n        } catch (const std::exception& e) {\n            std::cout << "other:" << e.what() << "\\n";\n        }\n    }',
             'void fail(int which) {\n    if (which == 0) throw std::out_of_range("index");\n    throw std::runtime_error("io");\n}\n'),'range:index\nother:io\n',
     ('Throw std::invalid_argument for the second case.', 'throw std::runtime_error("io");', 'throw std::invalid_argument("io");', 'range:index\nlogic:io\n', 'invalid_argument derives from logic_error, not out_of_range, so the second handler is the first match.'),
     'Why must catch (const std::exception&) follow catch (const std::out_of_range&)?', 'Handlers are tried in order and the base handler would match first', ['The compiler reorders them by specificity','Only the last handler is ever selected'], 'Handler selection takes the first match, not the best match.', 'except.handle')
unit(S,'assert-checks','assert checks at run time; static_assert at compile time',14,
     'static_assert(condition, message) evaluates a constant expression during compilation and rejects the program if it is false. It costs nothing at run time and suits assumptions about types and sizes. C++17 makes the message optional.|assert(condition) from <cassert> checks a run-time condition and calls std::abort with a diagnostic if it fails. Defining NDEBUG before including <cassert> removes the check entirely.|Because assert can disappear, never put required side effects inside it, and do not use it to validate untrusted input. Assertions document internal assumptions; input errors need real error handling.',
     program('cassert', '    std::cout << average(10, 4) << "\\n";',
             'static_assert(sizeof(int) >= 2, "int must hold at least 16 bits");\n\nint average(int total, int count) {\n    assert(count > 0 && "count must be positive");\n    return total / count;\n}\n'),'2\n',
     ('Require a 64-bit long long at compile time and average 9 over 3.', [('static_assert(sizeof(int) >= 2, "int must hold at least 16 bits");', 'static_assert(sizeof(int) >= 2, "int must hold at least 16 bits");\nstatic_assert(sizeof(long long) * 8 >= 64, "long long must hold 64 bits");'), ('average(10, 4)', 'average(9, 3)')], None, '3\n', 'The new static_assert is checked by the compiler and produces no code. The run-time assert still guards the division.'),
     'With NDEBUG defined, what happens to assert(check())?', 'check() is not called at all', ['check() runs but failures are ignored','The program fails to compile'], 'The assert macro expands to a no-op expression when NDEBUG is defined.', 'dcl.pre')
unit(S,'exit-versus-return','std::exit skips automatic destructors',14,
     'Returning from main destroys main\'s local objects, then calls std::exit with the return value. std::exit destroys objects with static storage duration and flushes C streams, but it never returns to unwind the caller\'s stack.|An std::exit call deep in a function therefore skips destructors of every automatic object still alive, including locks, file wrappers and buffers. std::quick_exit and std::_Exit skip even more cleanup.|Prefer returning an error to main or throwing an exception that main handles. Reserve std::exit for situations where skipping local cleanup is acceptable.',
     program('cstdlib', '    finish(false);\n    std::cout << "end\\n";',
             'struct Logger {\n    const char* name;\n    ~Logger() { std::cout << "close " << name << "\\n"; }\n};\n\nLogger global{"global"};\n\nvoid finish(bool early) {\n    Logger local{"local"};\n    if (early) std::exit(0);\n}\n'),'close local\nend\nclose global\n',
     ('Call finish(true) instead.', 'finish(false);', 'finish(true);', 'close global\n', 'std::exit runs static destructors, so global closes, but local is never destroyed and end is never printed.'),
     'Does std::exit run destructors for automatic objects of the calling functions?', 'No; only static-storage objects are destroyed', ['Yes, it unwinds the stack like an exception','No destructors of any kind run'], 'std::exit performs static destruction and stream flushing, not stack unwinding.', 'support.start.term')
unit(S,'inline-odr','inline is about definitions, not speed',14,
     'Marking a function inline permits an identical definition to appear in every translation unit that uses it, which is what lets a header define small functions. Functions defined inside a class body and constexpr functions are implicitly inline.|The compiler decides independently whether to expand a call in place; inline is at most a hint for that. C++17 extends the same multiple-definition permission to inline variables.|All definitions of an inline entity must be token-for-token identical with the same meaning. Differing definitions in different translation units are an ODR violation that needs no diagnostic.',
     program('', '    std::cout << square(7) << "\\n";',
             '// Could live in a header included by many source files.\ninline int square(int x) { return x * x; }\n'),'49\n',
     ('Add an inline cube built on square and print cube(3).', [('inline int square(int x) { return x * x; }', 'inline int square(int x) { return x * x; }\ninline int cube(int x) { return x * square(x); }'), ('square(7)', 'cube(3)')], None, '27\n', 'Both functions may be defined in a shared header. Whether either call is expanded in place is an optimizer decision.'),
     'What does inline guarantee for a function in modern C++?', 'An identical definition may appear in multiple translation units', ['Every call is expanded in place','The function cannot be recursive'], 'The guaranteed meaning concerns the one-definition rule; call expansion is not required.', 'dcl.inline')

# Drills: three or more per stage-01/02 lesson
M = main_program
drill('first-program','Predict output','Adjacent literals',
      M('    std::cout << "a" "b" << 1 + 2 << \'\\n\';'),
      'What does this print?','ab3',['a b3','ab12'],
      'Adjacent string literals are concatenated during translation, and 1 + 2 is evaluated as an int before formatting.')
drill('first-program','Compiles?','Header that does not declare cout',
      M('    std::cout << 1 << "\\n";','string'),
      'Does this program compile?','No: std::cout is not declared without <iostream>',
      ['Yes, every standard header declares std::cout','Yes, but it prints nothing'],
      'A name must be declared before use. <string> does not promise to declare std::cout; include the header that documents it.',check='reject',diagnostic="no member named 'cout'")
drill('first-program','Code review','Declared but never defined',
      M('    std::cout << helper() << "\\n";',declarations='int helper();'),
      'Which build step fails for this program?','Linking: helper is declared but no definition exists',
      ['Compilation: helper is an undeclared identifier','Nothing; helper returns 0 by default'],
      'The declaration satisfies the compiler; the linker must find a definition and reports an undefined symbol.',check='reject',diagnostic='Undefined symbols')
drill('first-program','Compiles?','main without return',
      M('    std::cout << "done\\n";'),
      'main has no return statement. Does the program compile and exit with status 0?','Yes; flowing off the end of main returns 0',
      ['No; a non-void function needs a return','It compiles but the exit status is unspecified'],
      'main is special: reaching its closing brace is equivalent to return 0.',check='compiles')
drill('initialization','Predict output','Parentheses versus braces for vector',
      M('    std::vector<int> a(3, 1);\n    std::vector<int> b{3, 1};\n    std::cout << a.size() << " " << b.size() << "\\n";','iostream vector'),
      'What does this print?','3 2',['3 3','2 2'],
      'Parentheses select the count-and-value constructor. Braces prefer the initializer_list constructor, so b holds the elements 3 and 1.')
drill('initialization','Predict output','Static storage starts at zero',
      M('    std::cout << counter << "\\n";',declarations='static int counter;'),
      'What does this print?','0',['An indeterminate value','1'],
      'Objects with static storage duration are zero-initialized before any other initialization.')
drill('conversions','Predict output','Signed and unsigned comparison',
      M('    unsigned u = 1;\n    int i = -1;\n    std::cout << (i < u) << "\\n";'),
      'What does this print?','0',['1','It does not compile'],
      'The usual arithmetic conversions turn -1 into a large unsigned value before comparing, so the test is false.')
drill('conversions','Predict output','Floating to integer truncates',
      M('    std::cout << static_cast<int>(-2.7) << " " << static_cast<int>(2.7) << "\\n";'),
      'What does this print?','-2 2',['-3 2','-3 3'],
      'Floating-to-integer conversion discards the fractional part, truncating toward zero.')
drill('conversions','Predict output','char arithmetic promotes',
      M('    char c = \'A\';\n    std::cout << c + 1 << "\\n";'),
      'What does this print on an ASCII system?','66',['B','A1'],
      'c + 1 promotes c to int, so the int overload of operator<< prints the number 66.')
drill('integer-limits','Predict output','unsigned char wraps',
      M('    unsigned char c = 255;\n    c += 1;\n    std::cout << static_cast<int>(c) << "\\n";'),
      'What does this print (8-bit char)?','0',['256','255'],
      'The sum 256 is computed as int and converted back to unsigned char, which reduces it modulo 256.')
drill('integer-limits','Predict output','Unsigned decrement below zero',
      M('    unsigned x = 0;\n    x -= 1;\n    std::cout << (x == std::numeric_limits<unsigned>::max()) << "\\n";','iostream limits'),
      'What does this print?','1',['0','It has undefined behavior'],
      'Unsigned arithmetic is modular, so 0 - 1 wraps to the maximum value.')
drill('integer-limits','Undefined behavior','Negating INT_MIN',
      M('    int x = std::numeric_limits<int>::min();\n    x = -x;\n    std::cout << x << "\\n";','iostream limits'),
      'What does the standard say about this program?','Undefined behavior: -INT_MIN is not representable in int',
      ['It prints INT_MIN because two\'s complement wraps','It prints INT_MAX'],
      'In two\'s complement the magnitude of the minimum exceeds the maximum; signed overflow is undefined.',check='ubsan')
drill('floating-point','Predict output','Exact equality of a decimal sum',
      M('    std::cout << (0.1 + 0.2 == 0.3) << "\\n";'),
      'What does this print with IEEE-754 doubles?','0',['1','It does not compile'],
      'Neither 0.1 nor 0.2 is exactly representable; the rounded sum differs from the double nearest 0.3.')
drill('floating-point','Predict output','NaN is unequal to itself',
      M('    const double n = std::nan("");\n    std::cout << (n == n) << " " << std::isnan(n) << "\\n";','iostream cmath'),
      'What does this print?','0 1',['1 1','1 0'],
      'Every comparison involving NaN except != is false; use std::isnan to test for it.')
drill('floating-point','Predict output','Float runs out of integer precision',
      M('    float f = 16777216.0f;\n    f += 1.0f;\n    std::cout << std::fixed << std::setprecision(0) << f << "\\n";','iostream iomanip'),
      'What does this print with IEEE-754 binary32 float?','16777216',['16777217','16777218'],
      'binary32 has a 24-bit significand; 2^24 + 1 is not representable and rounds to even, back to 2^24.')
drill('expressions','Predict output','Precedence groups multiplication first',
      M('    int a = 2, b = 3;\n    std::cout << a + b * 2 << " " << (a + b) * 2 << "\\n";'),
      'What does this print?','8 10',['10 10','8 8'],
      'Multiplication binds tighter than addition; parentheses change grouping.')
drill('expressions','Predict output','Left-to-right grouping and remainder sign',
      M('    int i = 7;\n    std::cout << i / 2 * 2 << " " << i % -3 << "\\n";'),
      'What does this print?','6 1',['7 -1','7 1'],
      'Multiplicative operators group left to right, so (7 / 2) * 2 truncates first. Since C++11 the remainder takes the sign of the dividend.')
drill('expressions','Predict output','Short-circuit avoids division by zero',
      M('    int n = 0;\n    const bool r = (n != 0) && (10 / n > 1);\n    std::cout << r << "\\n";'),
      'What does this print?','0',['It has undefined behavior: division by zero','1'],
      'Built-in && does not evaluate its right operand when the left is false, so the division never happens.')
drill('expressions','Predict output','Assignment sequencing in C++17',
      M('    int i = 1;\n    i = i++ + 1;\n    std::cout << i << "\\n";'),
      'Compiled as C++17, what does this print?','2',['3','It has undefined behavior in C++17'],
      'C++17 sequences the right operand of = before the assignment, so i++ completes (leaving 2 and yielding 1) and then i is assigned 1 + 1. In C++14 the same statement is undefined.',standard=17)
drill('enumerations','Compiles?','Scoped enum to int',
      M('    enum class Color { red };\n    int x = Color::red;\n    std::cout << x << "\\n";'),
      'Does this compile?','No: a scoped enumerator does not convert implicitly to int',
      ['Yes, it prints 0','Yes, it prints 1'],
      'enum class values require static_cast to reach their underlying integer.',check='reject',diagnostic="cannot initialize a variable of type 'int'")
drill('enumerations','Predict output','Implicit enumerator values',
      M('    enum Level { low = 1, mid, high = 10, top };\n    std::cout << mid << " " << top << "\\n";'),
      'What does this print?','2 11',['1 3','2 3'],
      'An enumerator without an initializer is one more than the previous enumerator.')
drill('enumerations','Layout','Fixed underlying type',
      M('    enum class Small : unsigned char { a, b };\n    std::cout << sizeof(Small) << " " << static_cast<int>(Small::b) << "\\n";'),
      'What does this print?','1 1',['4 1','1 2'],
      'Specifying unsigned char as the underlying type fixes the size at sizeof(unsigned char), which is always 1.')
drill('string-values','Predict output','Append and substr',
      M('    std::string s = "abc";\n    s += \'d\';\n    std::cout << s.size() << " " << s.substr(1, 2) << "\\n";','iostream string'),
      'What does this print?','4 bc',['4 bcd','3 bc'],
      'substr(pos, count) copies count characters starting at pos.')
drill('string-values','Predict output','Lexicographic comparison',
      M('    std::string a = "10", b = "9";\n    std::cout << (a < b) << "\\n";','iostream string'),
      'What does this print?','1',['0','It does not compile'],
      'Strings compare character by character; \'1\' is less than \'9\', so "10" sorts first.')
drill('string-values','Undefined behavior','Pointer kept across reassignment',
      M('    std::string s(50, \'a\');\n    const char* p = s.c_str();\n    s = std::string(500, \'z\');\n    std::cout << p[0] << "\\n";','iostream string'),
      'Is reading p[0] valid?','No: the old heap buffer was released, so p dangles',
      ['Yes, it prints a','Yes, it prints z'],
      'Pointers from c_str() are invalidated by any operation that may reallocate or replace the buffer.',check='asan')
drill('vector-values','Predict output','reserve changes capacity, not size',
      M('    std::vector<int> v;\n    v.reserve(10);\n    std::cout << v.size() << " " << (v.capacity() >= 10) << "\\n";','iostream vector'),
      'What does this print?','0 1',['10 1','0 0'],
      'reserve allocates storage but creates no elements.')
drill('vector-values','Undefined behavior','Reference kept across push_back',
      M('    std::vector<int> v{1, 2, 3};\n    int& first = v[0];\n    for (int i = 0; i < 100; ++i) v.push_back(i);\n    std::cout << first << "\\n";','iostream vector'),
      'Is reading first valid after the loop?','No: reallocation invalidated the reference',
      ['Yes, it prints 1','Yes, vector never moves existing elements'],
      'Growing past capacity moves elements to new storage and invalidates references, pointers and iterators.',check='asan')
drill('scope-and-const','Predict output','Shadowing in an inner block',
      M('    int x = 1;\n    {\n        int x = 2;\n        x += 1;\n    }\n    std::cout << x << "\\n";'),
      'What does this print?','1',['3','2'],
      'The inner declaration introduces a different object that hides the outer x until the block ends.')
drill('scope-and-const','Compiles?','Assigning to a const',
      M('    const int n = 3;\n    n = 4;\n    std::cout << n << "\\n";'),
      'Does this compile?','No: n is const-qualified',['Yes, it prints 4','Yes, it prints 3'],
      'A const object cannot be modified through its own name.',check='reject',diagnostic='const-qualified')
drill('scope-and-const','Predict output','Lifetime extension by const reference',
      M('    const int& r = 2 + 3;\n    std::cout << r << "\\n";'),
      'What does this print?','5',['It has undefined behavior: the temporary is gone','0'],
      'Binding a temporary directly to a const reference extends the temporary to the reference\'s lifetime.')
drill('control-flow','Predict output','Stepped loop',
      M('    int s = 0;\n    for (int i = 0; i < 10; i += 3) s += i;\n    std::cout << s << "\\n";'),
      'What does this print?','18',['30','9'],
      'i takes 0, 3, 6 and 9; 12 fails the condition.')
drill('control-flow','Predict output','Unsigned countdown',
      M('    unsigned count = 0;\n    for (unsigned i = 3; i < 10; --i) ++count;\n    std::cout << count << "\\n";'),
      'What does this print?','4',['3','The loop never ends'],
      'After i reaches 0, --i wraps to the maximum unsigned value, which fails i < 10 and ends the loop after 3, 2, 1, 0.')
drill('control-flow','Predict output','Range-for over copies',
      M('    std::vector<int> v{1, 2, 3};\n    for (int x : v) x *= 2;\n    std::cout << v[0] + v[1] + v[2] << "\\n";','iostream vector'),
      'What does this print?','6',['12','It does not compile'],
      'int x declares a copy of each element; use int& x to modify the vector.')
drill('function-contracts','Predict output','Default arguments',
      M('    std::cout << f(1) << " " << f(1, 2) << "\\n";',declarations='int f(int a, int b = 10) { return a + b; }'),
      'What does this print?','11 3',['1 3','11 12'],
      'A default argument is supplied by the caller only when the argument is omitted.')
drill('function-contracts','Undefined behavior','Missing return path',
      M('    std::cout << sign(0) << "\\n";',declarations='int sign(int x) {\n    if (x > 0) return 1;\n    if (x < 0) return -1;\n}'),
      'What happens when sign(0) is called?','Undefined behavior: control reaches the end of a non-void function',
      ['It returns 0','It returns the last value returned'],
      'Flowing off the end of a value-returning function other than main is undefined.',check='ubsan')
drill('function-contracts','Compiles?','Call before declaration',
      'int main() {\n    return later();\n}\n\nint later() { return 0; }\n',
      'Does this compile?','No: later is not declared at the point of the call',
      ['Yes, the compiler searches the whole file','Yes, but it returns an indeterminate value'],
      'Unqualified names must be declared before use; add a prototype above main.',check='reject',diagnostic="undeclared identifier 'later'")
drill('reference-parameters','Predict output','By value versus by reference',
      M('    int n = 0;\n    bump(n);\n    bump_ref(n);\n    std::cout << n << "\\n";',declarations='void bump(int x) { ++x; }\nvoid bump_ref(int& x) { ++x; }'),
      'What does this print?','1',['2','0'],
      'Only the reference parameter aliases the caller\'s object.')
drill('reference-parameters','Compiles?','Literal to non-const reference',
      M('    f(5);',declarations='void f(int& x) { ++x; }'),
      'Does this compile?','No: a non-const lvalue reference cannot bind to a literal',
      ['Yes, a temporary int is created','Yes, but the increment is lost'],
      'Only const lvalue references and rvalue references bind to prvalues.',check='reject',diagnostic='expects an lvalue')
drill('reference-parameters','Predict output','Aliased in and out parameters',
      M('    int a = 3;\n    add_twice(a, a);\n    std::cout << a << "\\n";',declarations='void add_twice(int& out, const int& in) {\n    out += in;\n    out += in;\n}'),
      'What does this print?','12',['9','6'],
      'in and out refer to the same object, so the second addition reads the already-updated 6.')
drill('overload-resolution','Predict output','char argument',
      M('    f(\'a\');',declarations='void f(int) { std::cout << "int\\n"; }\nvoid f(double) { std::cout << "double\\n"; }'),
      'Which overload is called?','int',['double','The call is ambiguous'],
      'char to int is a promotion, which ranks above the char to double conversion.')
drill('overload-resolution','Compiles?','long argument',
      M('    g(1L);',declarations='void g(int) {}\nvoid g(double) {}'),
      'Does this compile?','No: the call is ambiguous',['Yes, g(int) is chosen','Yes, g(double) is chosen'],
      'long to int and long to double are both conversions of the same rank, so neither is better.',check='reject',diagnostic='ambiguous')
drill('overload-resolution','Predict output','float argument',
      M('    h(3.0f);',declarations='void h(long) { std::cout << "long\\n"; }\nvoid h(double) { std::cout << "double\\n"; }'),
      'Which overload is called?','double',['long','The call is ambiguous'],
      'float to double is a floating-point promotion, which beats the floating-integral conversion to long.')
drill('recursion','Predict output','Base case of one',
      M('    std::cout << f(10) << "\\n";',declarations='int f(int n) { return n <= 1 ? 1 : f(n - 1) + f(n - 2); }'),
      'What does this print?','89',['55','144'],
      'f(0) = f(1) = 1, so f(n) is the Fibonacci number shifted by one: 1, 1, 2, 3, 5, ... f(10) = 89.')
drill('recursion','Complexity','Counting naive calls',
      M('    const int r = fib(5);\n    std::cout << r << " " << calls << "\\n";',declarations='int calls = 0;\nint fib(int n) {\n    ++calls;\n    return n <= 1 ? n : fib(n - 1) + fib(n - 2);\n}'),
      'What does this print?','5 15',['5 5','5 9'],
      'Calls satisfy C(n) = 1 + C(n-1) + C(n-2) with C(0) = C(1) = 1, which grows exponentially; C(5) = 15.')
drill('recursion','Undefined behavior','No terminating measure',
      M('    std::cout << down(1) << "\\n";',declarations='int down(int n) {\n    volatile char pad[64];\n    pad[0] = 0;\n    return down(n - 1) + pad[0];\n}'),
      'What happens at run time?','The stack is exhausted: unbounded recursion',['It returns 0','The compiler turns it into a loop that ends'],
      'Without a base case every call allocates another frame until the stack overflows.',check='asan')
drill('lambda-captures','Predict output','Copy versus reference capture',
      M('    int x = 1;\n    auto by_value = [x] { return x; };\n    auto by_ref = [&x] { return x; };\n    x = 5;\n    std::cout << by_value() << by_ref() << "\\n";'),
      'What does this print?','15',['55','11'],
      'A copy capture snapshots x when the lambda is created; a reference capture reads the current value.')
drill('lambda-captures','Compiles?','Assigning a copied capture',
      M('    int x = 1;\n    auto f = [x] { x = 2; };\n    f();'),
      'Does this compile?','No: copied captures are const unless the lambda is mutable',
      ['Yes, and the outer x becomes 2','Yes, and only the copy changes'],
      'The call operator of a non-mutable lambda is const, so members holding copies cannot be assigned.',check='reject',diagnostic='captured by copy in a non-mutable lambda')
drill('lambda-captures','Predict output','mutable keeps state in the closure',
      M('    int n = 0;\n    auto f = [n]() mutable { return ++n; };\n    f();\n    f();\n    const int third = f();\n    std::cout << third << " " << n << "\\n";'),
      'What does this print?','3 0',['1 0','3 3'],
      'The closure owns its copy of n and keeps it between calls; the outer n is untouched.')
drill('pointer-contracts','Predict output','Pointer arithmetic',
      M('    int a[] = {10, 20, 30};\n    int* p = a;\n    p += 2;\n    std::cout << *p << " " << p - a << "\\n";'),
      'What does this print?','30 2',['30 8','20 2'],
      'Pointer arithmetic counts elements, not bytes.')
drill('pointer-contracts','Undefined behavior','Null dereference',
      M('    int* p = nullptr;\n    std::cout << *p << "\\n";'),
      'What does the standard say?','Undefined behavior: dereferencing a null pointer',
      ['It prints 0','It throws std::bad_alloc'],
      'A null pointer points to no object; reading through it is undefined.',check='ubsan')
drill('pointer-contracts','Undefined behavior','Write one past a new[] block',
      M('    int* p = new int[3];\n    p[3] = 1;\n    delete[] p;'),
      'Is the write valid?','No: index 3 is past the end of the allocation',
      ['Yes, new[] rounds up the allocation','Yes, one-past-the-end is a valid position'],
      'A one-past-the-end pointer may be formed and compared but not dereferenced.',check='asan')
drill('array-bounds','Layout','sizeof before and after decay',
      M('    int a[5] = {};\n    std::cout << sizeof(a) / sizeof(a[0]) << " ";\n    show(a);',declarations='void show(int x[5]) { std::cout << sizeof(x) << "\\n"; }'),
      'On arm64 macOS (LP64), what does this print?','5 8',['5 20','5 5'],
      'Inside main a is an array of 5 ints. The parameter int x[5] is adjusted to int*, whose size is 8 on LP64.')
drill('array-bounds','Undefined behavior','Off-by-one read',
      M('    int a[3] = {};\n    int i = 3;\n    std::cout << a[i] << "\\n";'),
      'Is a[i] valid?','No: index 3 is outside an array of 3 elements',['Yes, it reads 0','Yes, arrays have a sentinel element'],
      'Valid indices are 0 to 2; reading a[3] is undefined behavior.',check='asan')
drill('array-bounds','Compiles?','Compile-time index into std::array',
      M('    std::array<int, 3> a{};\n    std::cout << std::get<3>(a) << "\\n";','iostream array'),
      'Does this compile?','No: std::get checks the index at compile time',['Yes, and it throws std::out_of_range','Yes, with undefined behavior at run time'],
      'std::get<I> on std::array requires I < N and rejects the program otherwise.',check='reject',diagnostic='out of bounds')
drill('error-paths','Predict output','Destructors run during unwinding',
      M('    try {\n        Guard g;\n        throw 1;\n    } catch (int) {\n        std::cout << "c";\n    }\n    std::cout << "\\n";',declarations='struct Guard {\n    ~Guard() { std::cout << "d"; }\n};'),
      'What does this print?','dc',['cd','c'],
      'Leaving the try block by exception destroys its locals before the handler runs.')
drill('error-paths','Predict output','stoi accepts a valid prefix',
      M('    std::size_t pos = 0;\n    const int v = std::stoi("12abc", &pos);\n    std::cout << v << " " << pos << "\\n";','iostream string'),
      'What does this print?','12 2',['It throws std::invalid_argument','12 5'],
      'stoi throws only when no conversion is possible; pos reports how many characters were consumed so the caller can reject trailing text.')
drill('error-paths','Predict output','stoi with no digits',
      M('    try {\n        std::stoi("abc");\n    } catch (const std::invalid_argument&) {\n        std::cout << "invalid\\n";\n    } catch (const std::out_of_range&) {\n        std::cout << "range\\n";\n    }','iostream string stdexcept'),
      'What does this print?','invalid',['range','Nothing; it returns 0'],
      'stoi throws invalid_argument when no conversion can be performed and out_of_range when the value does not fit.')
drill('stream-state','Predict output','Failed second extraction',
      M('    std::istringstream in("42 abc");\n    int a = 0, b = 7;\n    in >> a >> b;\n    std::cout << a << " " << b << " " << in.fail() << "\\n";','iostream sstream'),
      'What does this print?','42 0 1',['42 7 1','42 7 0'],
      'Since C++11 a failed numeric extraction stores 0 and sets failbit.')
drill('stream-state','Predict output','clear does not skip the bad token',
      M('    std::istringstream in("abc 5");\n    int x = 9;\n    in >> x;\n    in.clear();\n    in >> x;\n    std::cout << x << " " << in.fail() << "\\n";','iostream sstream'),
      'What does this print?','0 1',['5 0','9 1'],
      'clear resets flags only; abc is still next, so the second extraction fails the same way.')
drill('stream-state','Predict output','Reading an int from 3.9',
      M('    std::istringstream in("3.9");\n    int n = 0;\n    in >> n;\n    std::cout << n << " " << in.fail() << " " << in.peek() << "\\n";','iostream sstream'),
      'What does this print on an ASCII system?','3 0 46',['4 0 -1','3 1 46'],
      'Integer extraction stops at the dot without failing; peek returns the next character, \'.\' (46).')
drill('istream-input-checks','Predict output','Value too large for int',
      M('    std::istringstream in("99999999999");\n    int n = 5;\n    in >> n;\n    std::cout << (n == std::numeric_limits<int>::max()) << " " << in.fail() << "\\n";','iostream sstream limits'),
      'What does this print (32-bit int)?','1 1',['0 0','0 1'],
      'On overflow, extraction stores the nearest limit and sets failbit, so the value cannot be trusted.')
drill('istream-input-checks','Predict output','EOF without failure',
      M('    std::istringstream in("5");\n    int n = 0;\n    in >> n;\n    std::cout << in.eof() << " " << static_cast<bool>(in) << "\\n";','iostream sstream'),
      'What does this print?','1 1',['0 1','1 0'],
      'Parsing 5 reached the end of input, setting eofbit, but the extraction succeeded so failbit is clear and the stream tests true.')
drill('istream-input-checks','Code review','Looping on eof()',
      M('    std::istringstream in("1 2\\n");\n    int n = 0, count = 0;\n    while (!in.eof()) {\n        in >> n;\n        ++count;\n    }\n    std::cout << count << "\\n";','iostream sstream'),
      'What does this print?','3',['2','The loop never ends'],
      'eof is only set after a read tries to go past the end. The trailing newline lets a third, failing extraction run; test the extraction itself instead.')
drill('istream-input-checks','Predict output','Leading whitespace and sign',
      M('    std::istringstream in("   -7");\n    int n = 0;\n    in >> n;\n    std::cout << n << "\\n";','iostream sstream'),
      'What does this print?','-7',['0','7'],
      'Formatted extraction skips leading whitespace by default and accepts a sign.')
drill('auto-deduction','Compiles?','auto& to a const object',
      M('    const int c = 1;\n    auto& r = c;\n    r = 2;'),
      'Does this compile?','No: auto& deduces const int&',['Yes, auto drops const','Yes, and c becomes 2'],
      'Reference deduction preserves the const of the referenced object; only plain auto drops top-level const.',check='reject',diagnostic='const-qualified')
drill('auto-deduction','Predict output','Deduced unsigned',
      M('    auto x = 5u - 6;\n    std::cout << (x > 0) << "\\n";'),
      'What does this print?','1',['0','It does not compile'],
      '5u - 6 has type unsigned int and wraps to a large value; auto faithfully deduces unsigned.')
drill('auto-deduction','Predict output','auto with a vector<bool> proxy',
      M('    std::vector<bool> v{true};\n    auto b = v[0];\n    v[0] = false;\n    std::cout << b << "\\n";','iostream vector'),
      'What does this print?','0',['1','It does not compile'],
      'vector<bool>::operator[] returns a proxy object; auto copies the proxy, which still refers to the bit.')
drill('auto-deduction','Compiles?','auto without an initializer',
      M('    auto x;\n    x = 3;'),
      'Does this compile?','No: auto needs an initializer to deduce from',['Yes, x becomes int','Yes, x becomes a variant'],
      'A placeholder type is deduced only from an initializer.',check='reject',diagnostic='requires an initializer')
drill('fixed-std-array','Predict output','Value-initialized std::array',
      M('    std::array<int, 4> a{};\n    std::cout << a[3] << " " << a.size() << "\\n";','iostream array'),
      'What does this print?','0 4',['An indeterminate value and 4','0 0'],
      'Empty braces value-initialize every element; size() is the fixed extent.')
drill('fixed-std-array','Predict output','Passing by value copies',
      M('    std::array<int, 2> a{1, 2};\n    change(a);\n    std::cout << a[0] << "\\n";','iostream array',declarations='void change(std::array<int, 2> a) { a[0] = 9; }'),
      'What does this print?','1',['9','It does not compile'],
      'std::array does not decay; the parameter is an independent copy.')
drill('fixed-std-array','Compiles?','Too many initializers',
      M('    std::array<int, 2> a{1, 2, 3};\n    std::cout << a[0] << "\\n";','iostream array'),
      'Does this compile?','No: three initializers for two elements',['Yes, the extra value is dropped','Yes, the array grows to three'],
      'Aggregate initialization rejects more initializers than elements.',check='reject',diagnostic='excess elements')
drill('fixed-std-array','Predict output','at checks the index',
      M('    std::array<int, 2> a{};\n    try {\n        std::cout << a.at(5) << "\\n";\n    } catch (const std::out_of_range&) {\n        std::cout << "out_of_range\\n";\n    }','iostream array stdexcept'),
      'What does this print?','out_of_range',['0','Undefined behavior'],
      'at() validates the index and throws std::out_of_range; operator[] performs no check.')
drill('string-view-borrow','Predict output','substr and find on a view',
      M('    std::string_view v = "hello world";\n    std::cout << v.substr(6) << " " << v.find(\'o\') << "\\n";','iostream string_view'),
      'What does this print?','world 4',['world 7','hello 4'],
      'substr returns another view; find returns the index of the first match.')
drill('string-view-borrow','Undefined behavior','View of a temporary string',
      M('    std::string_view v = std::string(40, \'x\');\n    std::cout << v[0] << "\\n";','iostream string string_view'),
      'Is reading v[0] valid?','No: the temporary string was destroyed and its buffer freed',
      ['Yes, it prints x','Yes, string_view copied the characters'],
      'The temporary dies at the end of the full-expression; the view keeps a dangling pointer.',check='asan')
drill('string-view-borrow','Predict output','Embedded null characters',
      M('    std::string_view a = "a\\0b";\n    std::string_view b("a\\0b", 3);\n    std::cout << a.size() << " " << b.size() << "\\n";','iostream string_view'),
      'What does this print?','1 3',['3 3','1 1'],
      'Constructing from a const char* alone uses the traits length, which stops at the first null; the pointer-and-length constructor does not.')
drill('bit-and-compound-ops','Predict output','Basic bit operators',
      M('    std::cout << (6 & 3) << " " << (6 | 3) << " " << (6 ^ 3) << " " << (1 << 4) << "\\n";'),
      'What does this print?','2 7 5 16',['2 7 9 16','3 7 5 8'],
      '110 & 011 = 010, 110 | 011 = 111, 110 ^ 011 = 101, and shifting 1 left by 4 gives 16.')
drill('bit-and-compound-ops','Predict output','Mask test without parentheses',
      M('    int x = 4;\n    std::cout << (x & 1 == 0) << "\\n";'),
      'What does this print?','0',['1','4'],
      '== binds tighter than &, so this is x & 0.')
drill('bit-and-compound-ops','Undefined behavior','Shift by the full width',
      M('    int s = 32;\n    int v = 1 << s;\n    std::cout << v << "\\n";'),
      'What does the standard say for a 32-bit int?','Undefined behavior: the shift count equals the width',
      ['It prints 0','It prints 1'],
      'A shift count must be less than the width of the promoted left operand.',check='ubsan')
drill('bit-and-compound-ops','Predict output','Complement after promotion',
      M('    unsigned char c = 0x0F;\n    std::cout << (~c) << "\\n";'),
      'What does this print?','-16',['240','15'],
      'c is promoted to int before ~, so the result is the int ~15, which is -16, not an 8-bit 240.')
drill('bit-and-compound-ops','Predict output','Postfix yields the old value',
      M('    int i = 1;\n    const int j = i++ + 10;\n    std::cout << i << " " << j << "\\n";'),
      'What does this print?','2 11',['2 12','1 11'],
      'i++ produces 1 and increments i as a side effect.')
drill('struct-aggregates','Predict output','Default member initializer',
      M('    P p{1};\n    std::cout << p.x << p.y << "\\n";',declarations='struct P {\n    int x;\n    int y = 5;\n};'),
      'What does this print?','15',['10','It does not compile in C++14'],
      'Since C++14 aggregates may have default member initializers; omitted members use them.')
drill('struct-aggregates','Layout','Member order and padding',
      M('    std::cout << sizeof(A) << " " << sizeof(B) << "\\n";',declarations='struct A { char c; int i; char d; };\nstruct B { int i; char c; char d; };'),
      'On arm64 macOS (4-byte aligned int), what does this print?','12 8',['6 6','8 8'],
      'Members keep declaration order. In A each char needs padding to align i and the total size; in B the chars share the tail padding.')
drill('struct-aggregates','Predict output','Struct copies are independent',
      M('    P a{1, 2};\n    P b = a;\n    b.x = 9;\n    std::cout << a.x << "\\n";',declarations='struct P { int x; int y; };'),
      'What does this print?','1',['9','It does not compile'],
      'Copy-initialization copies each member; b and a are separate objects.')
drill('struct-aggregates','Compiles?','Too many initializers',
      M('    P p{1, 2};\n    std::cout << p.x << "\\n";',declarations='struct P { int x; };'),
      'Does this compile?','No: there are more initializers than members',['Yes, 2 is ignored','Yes, p.x becomes 2'],
      'Aggregate initialization rejects excess initializers.',check='reject',diagnostic='excess elements')
drill('header-source-split','Compiles?','Unguarded header included twice',
      M('    return 0;',declarations='struct Size { int w; };\nstruct Size { int w; };'),
      'A header defining struct Size without a guard is included twice in one file. Does it compile?','No: Size is redefined',
      ['Yes, identical definitions are merged','Yes, but the linker reports a duplicate'],
      'Within one translation unit a class may be defined only once; include guards prevent the second textual copy.',check='reject',diagnostic="redefinition of 'Size'")
drill('header-source-split','Compiles?','Repeated declarations',
      M('    return twice(0);',declarations='int twice(int x);\nint twice(int x);\nint twice(int x) { return 2 * x; }'),
      'Does this compile and exit 0?','Yes; a function may be declared many times but defined once',
      ['No; the declarations conflict','No; the definition must come first'],
      'Redeclarations are allowed; only a second definition is an error.',check='compiles')
drill('header-source-split','Predict output','Guard removes the second copy',
      '#include <iostream>\n#ifndef GUARD_H\n#define GUARD_H\nint value = 1;\n#endif\n#ifndef GUARD_H\nint value = 2;\n#endif\nint main() {\n    std::cout << value << "\\n";\n}\n',
      'What does this print?','1',['2','It does not compile: value is redefined'],
      'GUARD_H is defined by the first block, so the preprocessor drops the second block.')
drill('header-source-split','Code review','Non-inline definition in a header',
      '','A header contains int twice(int x) { return 2 * x; } (not inline). a.cpp and b.cpp both include it and are linked together. What happens?','The link fails with a duplicate symbol for twice',
      ['It works because of the include guard','The linker silently picks one definition'],
      'Include guards act per translation unit. Each object file defines twice, violating the ODR; marking it inline or moving it to one .cpp fixes it.',check='reasoning')
drill('char-and-escapes','Predict output','sizeof a character literal',
      M('    std::cout << sizeof(\'a\') << " " << sizeof("a") << "\\n";'),
      'What does this print?','1 2',['4 2','1 1'],
      'In C++ \'a\' has type char. "a" is const char[2] including the terminating null.')
drill('char-and-escapes','Predict output','Arithmetic on letters',
      M('    std::cout << (\'a\' + 1) << " " << static_cast<char>(\'a\' + 1) << "\\n";'),
      'What does this print on an ASCII system?','98 b',['b b','98 98'],
      'The sum is an int and prints as a number; converting back to char prints the character.')
drill('char-and-escapes','Predict output','Counting escaped characters',
      M('    std::string s = "a\\tb\\\\n";\n    std::cout << s.size() << "\\n";','iostream string'),
      'What does this print?','5',['4','6'],
      'The literal holds a, tab, b, backslash and n: \\\\ is one backslash, so the n is an ordinary letter.')
drill('char-and-escapes','Predict output','Octal and hex escapes',
      M('    std::cout << std::string("\\x41\\101") << "\\n";','iostream string'),
      'What does this print on an ASCII system?','AA',['A101','x41A'],
      '\\x41 is hexadecimal 65 and \\101 is octal 65; both are A.')
drill('type-alias-using','Predict output','Alias and typedef name the same type',
      M('    std::cout << std::is_same<Id, Code>::value << "\\n";','iostream type_traits',declarations='using Id = int;\ntypedef int Code;'),
      'What does this print?','1',['0','It does not compile'],
      'Both declarations introduce names for int.')
drill('type-alias-using','Compiles?','Overloading on aliases',
      M('    f(1.0);',declarations='using Meters = double;\nusing Feet = double;\nvoid f(Meters) {}\nvoid f(Feet) {}'),
      'Does this compile?','No: both functions have the signature void(double)',
      ['Yes, overloads are chosen by alias','Yes, the call is resolved to f(Meters)'],
      'Aliases do not create types, so the second definition redefines f.',check='reject',diagnostic="redefinition of 'f'")
drill('type-alias-using','Predict output','const applied to a pointer alias',
      M('    int x = 1;\n    const Ptr p = &x;\n    *p = 5;\n    std::cout << x << "\\n";',declarations='using Ptr = int*;'),
      'What does this print?','5',['1','It does not compile: *p is const'],
      'const Ptr is int* const: the pointer is const, not the int it points to.')
drill('switch-and-fallthrough','Predict output','Fall-through without break',
      M('    int x = 2, n = 0;\n    switch (x) {\n    case 1: n += 1;\n    case 2: n += 2;\n    case 3: n += 3; break;\n    default: n += 100;\n    }\n    std::cout << n << "\\n";'),
      'What does this print?','5',['2','105'],
      'Execution enters at case 2 and continues through case 3 until break.')
drill('switch-and-fallthrough','Compiles?','Jumping past an initialization',
      M('    int x = 1;\n    switch (x) {\n    case 1:\n        int y = 5;\n        std::cout << y << "\\n";\n        break;\n    case 2:\n        std::cout << "two\\n";\n    }'),
      'Does this compile?','No: case 2 would jump past the initialization of y',
      ['Yes, y is simply uninitialized in case 2','Yes, because case 2 never uses y'],
      'A jump may not bypass a declaration with initialization while the name remains in scope; add braces around case 1.',check='reject',diagnostic='cannot jump from switch statement to this case label')
drill('switch-and-fallthrough','Compiles?','Switching on a string',
      M('    std::string s = "a";\n    switch (s) {\n    default: break;\n    }','iostream string'),
      'Does this compile?','No: the condition must have integral or enumeration type',
      ['Yes, cases compare with ==','Yes, since C++17'],
      'switch requires an integral, enumeration, or contextually convertible class type; std::string is none of these.',check='reject',diagnostic='integer type')
drill('switch-and-fallthrough','Predict output','default placed first',
      M('    switch (5) {\n    default: std::cout << "d";\n    case 1: std::cout << "1"; break;\n    case 2: std::cout << "2";\n    }\n    std::cout << "\\n";'),
      'What does this print?','d1',['d','d12'],
      'default may appear anywhere; control enters there and falls into case 1 until break.')
drill('loop-exits','Predict output','do-while runs once',
      M('    int n = 10;\n    do {\n        ++n;\n    } while (n < 5);\n    std::cout << n << "\\n";'),
      'What does this print?','11',['10','5'],
      'The body executes before the first test.')
drill('loop-exits','Predict output','continue in a for loop',
      M('    int s = 0;\n    for (int i = 0; i < 5; ++i) {\n        if (i % 2) continue;\n        s += i;\n    }\n    std::cout << s << "\\n";'),
      'What does this print?','6',['4','The loop never ends'],
      'continue still runs the increment, so even i values 0, 2 and 4 are summed.')
drill('loop-exits','Predict output','break leaves only the inner loop',
      M('    int count = 0;\n    for (int i = 0; i < 3; ++i)\n        for (int j = 0; j < 3; ++j) {\n            if (j == 1) break;\n            ++count;\n        }\n    std::cout << count << "\\n";'),
      'What does this print?','3',['1','9'],
      'Each outer iteration counts j = 0 and then breaks the inner loop only.')
drill('loop-exits','Predict output','continue in do-while goes to the condition',
      M('    int i = 0, s = 0;\n    do {\n        ++i;\n        if (i == 2) continue;\n        s += i;\n    } while (i < 4);\n    std::cout << s << "\\n";'),
      'What does this print?','8',['10','1'],
      'continue jumps to the loop condition, so 2 is skipped and 1 + 3 + 4 is summed.')
drill('function-pointer-basics','Predict output','Two call syntaxes',
      M('    int (*f)(int) = twice;\n    std::cout << f(3) << (*f)(4) << "\\n";',declarations='int twice(int x) { return 2 * x; }'),
      'What does this print?','68',['6 8','It does not compile'],
      'A function name decays to a pointer, and f(3) and (*f)(4) are equivalent calls.')
drill('function-pointer-basics','Compiles?','Capturing lambda to pointer',
      M('    int k = 1;\n    int (*f)(int) = [k](int x) { return x + k; };\n    return f(0);'),
      'Does this compile?','No: a capturing lambda has no conversion to a function pointer',
      ['Yes, k is copied into the pointer','Yes, but k is ignored'],
      'Only captureless lambdas provide the conversion function.',check='reject',diagnostic='no viable conversion')
drill('function-pointer-basics','Predict output','Captureless lambda converts',
      M('    int (*f)(int) = [](int x) { return x * x; };\n    std::cout << f(5) << "\\n";'),
      'What does this print?','25',['5','It does not compile'],
      'A lambda without captures converts implicitly to a pointer with the same signature.')
drill('function-pointer-basics','Predict output','Dispatch table',
      M('    int (*ops[])(int, int) = {add, sub};\n    std::cout << ops[1](5, 2) << "\\n";',declarations='int add(int a, int b) { return a + b; }\nint sub(int a, int b) { return a - b; }'),
      'What does this print?','3',['7','It does not compile'],
      'ops is an array of function pointers; index 1 selects sub.')
drill('static-local-state','Predict output','Initializer runs once',
      M('    const int a = g(10);\n    const int b = g(50);\n    std::cout << a << " " << b << "\\n";',declarations='int g(int start) {\n    static int n = start;\n    return n++;\n}'),
      'What does this print?','10 11',['10 50','11 51'],
      'The static is initialized on the first call only; the second argument is ignored.')
drill('static-local-state','Predict output','Static in a loop body',
      M('    for (int i = 0; i < 3; ++i) {\n        static int s = 0;\n        int a = 0;\n        ++s;\n        ++a;\n        if (i == 2) std::cout << s << a << "\\n";\n    }'),
      'What does this print?','31',['11','33'],
      'The static is shared by every iteration; the automatic a is recreated each time.')
drill('static-local-state','Predict output','Lazy construction',
      M('    use(false);\n    std::cout << "x,";\n    use(true);\n    use(true);\n    std::cout << "\\n";',declarations='struct T {\n    T() { std::cout << "ctor"; }\n};\n\nvoid use(bool b) {\n    if (b) {\n        static T t;\n    }\n}'),
      'What does this print?','x,ctor',['ctorx,','x,ctorctor'],
      'A block-scope static is constructed when control first passes its declaration, and only once.')
drill('argv-parsing','Predict output','Program run with no arguments',
      '#include <iostream>\nint main(int argc, char* argv[]) {\n    std::cout << argc << " " << (argv[argc] == nullptr) << "\\n";\n}\n',
      'The program is launched with no command-line arguments. What does it print?','1 1',['0 1','1 0'],
      'argv[0] holds the program name, so argc is 1, and argv[argc] is always a null pointer.')
drill('argv-parsing','Predict output','atoi hides errors',
      M('    const char* args[] = {"prog", "42", "x"};\n    std::cout << std::atoi(args[1]) + std::atoi(args[2]) << "\\n";','iostream cstdlib'),
      'What does this print?','42',['It throws std::invalid_argument','It has undefined behavior'],
      'atoi returns 0 when no conversion is possible, indistinguishable from a real 0.')
drill('argv-parsing','Predict output','Comparing C strings with ==',
      M('    char flag[] = "-v";\n    const char* expected = "-v";\n    std::cout << (flag == expected) << " " << (std::strcmp(flag, expected) == 0) << "\\n";','iostream cstring'),
      'What does this print?','0 1',['1 1','0 0'],
      '== compares the addresses of two distinct arrays; strcmp compares characters.')
drill('handler-order','Predict output','Catch by value slices',
      M('    try {\n        throw Derived{};\n    } catch (Base b) {\n        std::cout << b.name() << "\\n";\n    }',declarations='struct Base {\n    virtual ~Base() = default;\n    virtual const char* name() const { return "base"; }\n};\nstruct Derived : Base {\n    const char* name() const override { return "derived"; }\n};'),
      'What does this print?','base',['derived','It does not compile'],
      'Catching by value copy-initializes a Base from the Derived exception, slicing off the derived part.')
drill('handler-order','Predict output','Base handler first',
      M('    try {\n        throw std::out_of_range("x");\n    } catch (const std::exception&) {\n        std::cout << "exception\\n";\n    } catch (const std::out_of_range&) {\n        std::cout << "range\\n";\n    }','iostream stdexcept'),
      'What does this print?','exception',['range','Both lines'],
      'The first matching handler wins; a base-class handler matches derived exceptions.')
drill('handler-order','Predict output','Rethrow the same object',
      M('    try {\n        try {\n            throw 7;\n        } catch (int& e) {\n            e = 8;\n            throw;\n        }\n    } catch (int e) {\n        std::cout << e << "\\n";\n    }'),
      'What does this print?','8',['7','It terminates'],
      'throw; rethrows the existing exception object, which was modified through the reference.')
drill('handler-order','Predict output','No arithmetic conversion in handlers',
      M('    try {\n        throw 1;\n    } catch (long) {\n        std::cout << "long\\n";\n    } catch (int) {\n        std::cout << "int\\n";\n    }'),
      'What does this print?','int',['long','It terminates'],
      'Handler matching allows derived-to-base and qualification conversions, not int to long.')
drill('assert-checks','Predict output','NDEBUG removes the call',
      '#define NDEBUG\n#include <cassert>\n#include <iostream>\nint calls = 0;\nbool check() {\n    ++calls;\n    return true;\n}\nint main() {\n    assert(check());\n    std::cout << calls << "\\n";\n}\n',
      'What does this print?','0',['1','It does not compile'],
      'With NDEBUG defined before <cassert>, assert expands to nothing that evaluates its argument.')
drill('assert-checks','Compiles?','A false static_assert',
      M('    return 0;',declarations='static_assert(sizeof(char) == 2, "char must be two bytes");'),
      'Does this compile?','No: sizeof(char) is always 1',['Yes, but it aborts at run time','Yes, the message is a warning'],
      'static_assert is evaluated during compilation and rejects the program when false.',check='reject',diagnostic='static assertion failed')
drill('assert-checks','Compiles?','static_assert on a run-time value',
      M('    int n = 3;\n    static_assert(n > 0, "positive");\n    return 0;'),
      'Does this compile?','No: the condition is not a constant expression',['Yes, n is known to be 3','Yes, it becomes a run-time check'],
      'static_assert needs a constant expression; a non-const local is not one.',check='reject',diagnostic='not an integral constant expression')
drill('exit-versus-return','Predict output','exit skips locals',
      M('    D d;\n    std::cout << "A";\n    std::exit(0);','iostream cstdlib',declarations='struct D {\n    ~D() { std::cout << "D"; }\n};'),
      'What does this print?','A',['AD','DA'],
      'std::exit does not unwind main\'s stack, so the automatic d is never destroyed.')
drill('exit-versus-return','Predict output','exit still destroys statics',
      M('    std::cout << "M";\n    std::exit(0);','iostream cstdlib',declarations='struct S {\n    ~S() { std::cout << "S"; }\n};\nS s;'),
      'What does this print?','MS',['M','SM'],
      'std::exit runs static-storage destructors after it is called.')
drill('exit-versus-return','Predict output','Return destroys locals then statics',
      M('    T l{"l"};\n    std::cout << "m";\n    return 0;',declarations='struct T {\n    const char* n;\n    ~T() { std::cout << n; }\n};\nT g{"g"};'),
      'What does this print?','mlg',['mgl','m'],
      'Returning from main destroys locals first, then std::exit destroys statics.')
drill('inline-odr','Concept','What inline promises',
      '','Does marking a function inline force the compiler to expand every call in place?','No; it permits identical definitions in several translation units',
      ['Yes, otherwise compilation fails','Yes, but only for functions under ten lines'],
      'The required meaning of inline concerns the one-definition rule; call expansion is an optimizer decision.',check='reasoning')
drill('inline-odr','Predict output','One inline variable',
      M('    bump();\n    bump();\n    std::cout << counter << "\\n";',declarations='inline int counter = 0;\nvoid bump() { ++counter; }'),
      'Compiled as C++17, what does this print?','2',['0','It does not compile'],
      'An inline variable is a single object even if its definition appears in many translation units.',standard=17)
drill('inline-odr','Compiles?','Two inline definitions in one file',
      M('    return f();',declarations='inline int f() { return 0; }\ninline int f() { return 0; }'),
      'Does this compile?','No: f is defined twice in one translation unit',['Yes, inline allows repeated definitions anywhere','Yes, because the bodies match'],
      'inline allows one definition per translation unit, not two in the same one.',check='reject',diagnostic="redefinition of 'f'")

"""Additional original C++ units and drills for stages 09-11."""
from cpp_lessons import unit, program, UNITS
from cpp_drills import drill, main_program

# Stage 09: undefined behavior, deprecations, library contracts
S='09 Toolchains, evolution, and expert boundaries'
unit(S,'strict-aliasing-rule','Inspect object bytes without breaking the aliasing rule',14,
     'The aliasing rule in the core language lists the glvalue types through which an object may be accessed: its own type (with cv and signedness variations), char, unsigned char, and std::byte, among a few others. Reading a float through an unsigned integer lvalue is not on that list, so the access has undefined behavior even when the sizes match.|Copy the object representation instead. std::memcpy into a separate integer object is well defined for trivially copyable types and compilers usually lower a small fixed-size copy to a single register move. C++20 adds std::bit_cast for the same conversion as a constant-expressible value operation.|Optimizers use the rule to assume that stores through an int pointer cannot modify a float object, so a type-punned read can observe a stale value or be reordered. -fno-strict-aliasing disables that assumption on clang and GCC but does not make the program portable; fix the access instead of relying on a flag.',
     program('cstdint cstring', '    const float value = 1.0f;\n    std::uint32_t bits = 0;\n    std::memcpy(&bits, &value, sizeof bits);\n    std::cout << std::hex << bits << "\\n";', 'static_assert(sizeof(float) == sizeof(std::uint32_t), "32-bit float expected");\n'),'3f800000\n',
     ('Inspect the bits of -2.0f with the same well-defined copy.', 'const float value = 1.0f;', 'const float value = -2.0f;', 'c0000000\n', 'The sign bit is set, the biased exponent is 128 and the fraction is zero, giving 0xc0000000 in IEEE 754 binary32. memcpy copies the representation without accessing the float through an unrelated type.'),
     'Why is *reinterpret_cast<std::uint32_t*>(&value) wrong for a float object?', 'It accesses a float through an unrelated glvalue type, which the aliasing rule makes undefined', ['It is fine because both types are four bytes','It only fails on big-endian machines'], 'Matching sizes do not create a permitted access type. Copy the representation with memcpy or std::bit_cast.', 'basic.lval')
unit(S,'signed-overflow-assumptions','Optimizers may assume signed overflow never happens',14,
     'When a signed arithmetic result is not representable, behavior is undefined. Compilers therefore treat expressions such as x + 1 > x as always true for int x and can delete overflow checks written after the arithmetic.|Check the operands before computing: for y > 0 the sum overflows exactly when x > max - y, and for y < 0 exactly when x < min - y. Those subtractions cannot overflow under their guards. Unsigned arithmetic is defined modulo 2^N, and compiler builtins such as __builtin_add_overflow are another option on clang and GCC.|-fwrapv makes signed overflow wrap on clang and GCC, but it is a dialect flag, not standard C++. UBSan (-fsanitize=signed-integer-overflow) reports overflow at run time on exercised paths; it cannot prove that untested inputs are safe.',
     program('limits', '    std::cout << add_overflows(std::numeric_limits<int>::max(), 1) << " " << add_overflows(5, 1) << "\\n";', 'bool add_overflows(int x, int y) {\n    return y > 0 && x > std::numeric_limits<int>::max() - y;\n}\n'),'1 0\n',
     ('Extend the check to negative y and test INT_MIN + (-1).', [('return y > 0 && x > std::numeric_limits<int>::max() - y;', 'return (y > 0 && x > std::numeric_limits<int>::max() - y) || (y < 0 && x < std::numeric_limits<int>::min() - y);'), ('add_overflows(5, 1) << "\\n";', 'add_overflows(5, 1) << " " << add_overflows(std::numeric_limits<int>::min(), -1) << "\\n";')], '', '1 0 1\n', 'For negative y, min - y is representable and the sum underflows exactly when x is below it. No operation in the check itself can overflow.'),
     'Why may a compiler fold x + 1 < x to false for int x?', 'Signed overflow is undefined, so it may assume x + 1 does not wrap', ['Because int arithmetic saturates','Because the comparison is evaluated at compile time only'], 'Assuming no undefined behavior, x + 1 is mathematically larger than x, so the comparison is false on every valid execution.', 'expr.pre')
unit(S,'uninitialized-reads','Reading an indeterminate value is not a random number',14,
     'A default-initialized automatic scalar has an indeterminate value. Up to C++23 reading it (other than as unsigned char or std::byte in narrow cases) has undefined behavior; C++26 reclassifies such reads of automatic variables as erroneous behavior with an implementation-chosen value, which is still a bug.|Value-initialization with {} zeroes scalars and arrays. An aggregate initializer that lists fewer elements than the array value-initializes the remaining elements. Default member initializers make each constructor start from a defined state.|Do not test for uninitialized reads by printing a value: a debug build may show zero by accident. Use compiler warnings such as -Wuninitialized, a sanitizer where available (MemorySanitizer is not supported on Apple platforms), or hardening options such as -ftrivial-auto-var-init=zero while still fixing the source.',
     program('', '    int buckets[4]{};\n    buckets[2] = 5;\n    std::cout << buckets[0] + buckets[2] << "\\n";'),'5\n',
     ('Initialize only the first bucket to one and predict the sum.', 'int buckets[4]{};', 'int buckets[4]{1};', '6\n', 'The listed element becomes 1 and the remaining three are value-initialized to zero, so buckets[0] + buckets[2] is 1 + 5.'),
     'What does int buckets[4]{1}; contain?', '1, 0, 0, 0', ['1, 1, 1, 1','1 followed by three indeterminate values'], 'Elements without an explicit initializer in aggregate initialization are value-initialized, which zeroes ints.', 'dcl.init.aggr')
unit(S,'sanitizer-workflow','Sanitizers turn silent undefined behavior into reports',14,
     'AddressSanitizer (-fsanitize=address) detects out-of-bounds and use-after-free accesses on heap, stack and globals. UndefinedBehaviorSanitizer (-fsanitize=undefined) checks operations such as signed overflow, invalid shifts and misaligned pointers. ThreadSanitizer (-fsanitize=thread) detects data races between unsynchronized accesses.|Build with -g and a low optimization level for readable reports, and use -fno-sanitize-recover=all when any report should fail the run. ASan and TSan cannot be combined in one binary; run separate configurations. On Apple platforms ASan leak detection is not supported, so ownership tests need explicit counting.|A clean sanitizer run only covers the executed paths and inputs. Sanitizers change memory layout and timing, so they complement tests, fuzzing and code review rather than proving absence of undefined behavior.',
     program('vector', '    std::vector<int> values{1, 2, 3};\n    std::size_t index = 3;\n    std::cout << (index < values.size() ? values[index] : -1) << "\\n";'),'-1\n',
     ('Read the last valid element through the same guard.', 'std::size_t index = 3;', 'std::size_t index = 2;', '3\n', 'The guard compares against size before indexing. Without it, values[3] would be an out-of-bounds read that ASan reports as a heap-buffer-overflow.'),
     'Which tool reports a heap-buffer-overflow when values[3] is read without the guard?', 'AddressSanitizer', ['ThreadSanitizer','The -Wall warning set'], 'ASan instruments memory accesses with shadow memory. TSan looks for races and -Wall cannot see run-time indices.', 'defns.undefined')
unit(S,'removed-features-migration','Removed C++98 facilities and their replacements',17,
     'C++17 removed several long-deprecated features: std::auto_ptr (use std::unique_ptr), the register storage class, dynamic exception specifications such as throw(int) (use noexcept), trigraphs, std::bind1st/bind2nd/ptr_fun/mem_fun (use lambdas, std::bind or std::mem_fn), and std::random_shuffle (use std::shuffle with an explicit generator). C++20 removed throw() as a spelling as well.|The replacements are not just renames. unique_ptr transfers ownership only by explicit move, so it cannot be silently emptied by copying the way auto_ptr was. std::shuffle takes a uniform random bit generator, which makes the randomness source and seed explicit.|Some standard libraries keep removed names behind opt-in compatibility macros. Do not depend on them in new code: migrate the code, compile with the target -std, and treat deprecation warnings as a migration list rather than noise.',
     program('algorithm memory random vector', '    std::vector<int> values{1, 2, 3, 4, 5};\n    std::mt19937 generator{42};\n    std::shuffle(values.begin(), values.end(), generator);\n    std::unique_ptr<int> owner = std::make_unique<int>(7);\n    auto large = std::count_if(values.begin(), values.end(), [](int x) { return x > 2; });\n    std::cout << large << " " << *owner << "\\n";'),'3 7\n',
     ('Count the values greater than four with the same lambda predicate.', 'return x > 2;', 'return x > 4;', '1 7\n', 'The shuffle changes element order but not membership, so exactly one value exceeds four. The lambda replaces a removed std::bind2nd(std::greater<int>(), 4) adaptor.'),
     'What replaces std::random_shuffle, removed in C++17?', 'std::shuffle with an explicit uniform random bit generator', ['std::sort with a random comparator','std::rand() inside a loop over std::swap'], 'std::shuffle makes the generator explicit. A random comparator violates the strict weak ordering requirement of std::sort.', 'diff.cpp14')
unit(S,'deprecated-cpp20-features','Recognize C++17 to C++23 deprecations and their replacements',20,
     'C++20 deprecated implicit capture of this through [=]; write [=, this] to share the object or [*this] to copy it. It also deprecated increment, decrement and compound assignment on volatile objects; C++23 restored the bitwise compound forms but += and ++ remain deprecated. std::iterator was deprecated in C++17 in favor of declaring the five member types directly.|C++23 deprecated std::aligned_storage and std::aligned_union because they are easy to misuse; an alignas(T) std::byte array of sizeof(T) bytes says the same thing directly. Comma expressions inside a subscript were deprecated in C++20 and became multi-argument subscripts in C++23.|Deprecated features still compile, usually with a warning, and may be removed later. Fix them when you raise the language standard so the migration diff stays small and does not hide behavior changes.',
     program('cstddef', '    volatile int reg = 4;\n    reg = reg + 1;\n    alignas(double) std::byte storage[sizeof(double)];\n    std::cout << Counter{}.adder()(2) << " " << reg << " " << sizeof(storage) << "\\n";', 'struct Counter {\n    int value = 1;\n    auto adder() { return [=, this](int n) { return value + n; }; }\n};\n'),'3 5 8\n',
     ('Start the counter at ten and predict the result through the explicitly captured this.', 'int value = 1;', 'int value = 10;', '12 5 8\n', 'The lambda reads value through the captured this pointer. [=, this] is the C++20 spelling that states the capture instead of relying on the deprecated implicit form.'),
     'Under C++20, what is wrong with [=] that uses a data member inside a member function?', 'Implicitly capturing this through [=] is deprecated; write [=, this] or [*this]', ['It copies the whole object, which is ill-formed','It is a hard error in C++20'], 'The capture default still captures this by pointer, which looks like a copy but is not. C++20 deprecates that implicit form.', 'depr.capture.this')
unit(S,'named-requirements-hash','Named requirements carry semantic obligations',17,
     'The library specifies named requirements such as Hash, Allocator and LegacyIterator. A type passed where a requirement is expected must provide the listed expressions and also satisfy semantic rules that the compiler cannot check.|For Hash, equal keys under the container equality predicate must produce equal hash values; the reverse is not required. C++20 concepts express the syntactic part of some requirements, for example std::forward_iterator, while named requirements still state the semantic part in prose.|A hash that ignores a field used by equality is valid but may collide heavily. A hash that uses a field equality ignores breaks the requirement and can put equal keys in different buckets, so lookups and duplicate detection fail.',
     program('cstddef functional unordered_set', '    std::unordered_set<Point, PointHash> points{{1, 2}, {1, 2}, {2, 1}};\n    std::cout << points.size() << "\\n";', 'struct Point {\n    int x, y;\n    bool operator==(const Point& other) const { return x == other.x && y == other.y; }\n};\nstruct PointHash {\n    std::size_t operator()(const Point& p) const noexcept { return std::hash<int>{}(p.x) * 31u + std::hash<int>{}(p.y); }\n};\n'),'2\n',
     ('Insert a third distinct point and predict the size.', '{2, 1}};', '{2, 1}, {3, 4}};', '3\n', 'The duplicate {1, 2} compares equal and hashes equally, so it is stored once. {2, 1} and {3, 4} are distinct keys.'),
     'For a Hash h and keys a == b, what must hold?', 'h(a) == h(b)', ['h(a) != h(b) whenever a != b','h must be a constexpr function'], 'Equal keys must hash equally. Distinct keys may collide, which costs time but not correctness.', 'hash.requirements')
unit(S,'allocator-propagation-traits','Allocator propagation traits decide where storage lives after assignment',17,
     'std::allocator_traits exposes propagate_on_container_copy_assignment, propagate_on_container_move_assignment and propagate_on_container_swap, plus is_always_equal. Containers consult them to decide whether the destination adopts the source allocator during assignment and swap.|std::allocator moves with the container and is always equal. std::pmr::polymorphic_allocator propagates on none of these operations, so a pmr container keeps its own memory resource; copy construction uses select_on_container_copy_construction, which yields the default resource for pmr.|When move assignment does not propagate and the allocators compare unequal, the container cannot steal the source buffer; it moves elements one by one into its own storage. Swapping containers with unequal, non-propagating allocators has undefined behavior.',
     program('memory memory_resource', '    using A = std::allocator_traits<std::allocator<int>>;\n    using P = std::allocator_traits<std::pmr::polymorphic_allocator<int>>;\n    std::cout << A::propagate_on_container_move_assignment::value << A::is_always_equal::value << " " << P::propagate_on_container_move_assignment::value << P::is_always_equal::value << "\\n";'),'11 00\n',
     ('Inspect the copy-assignment propagation trait of std::allocator instead.', 'A::propagate_on_container_move_assignment::value', 'A::propagate_on_container_copy_assignment::value', '01 00\n', 'std::allocator does not propagate on copy assignment, but because all instances compare equal the choice has no observable effect on storage ownership.'),
     'Move assignment between pmr vectors with different resources: what happens?', 'Elements are moved individually into storage from the destination resource', ['The source buffer is always stolen','It throws std::bad_alloc'], 'polymorphic_allocator does not propagate and unequal resources cannot free each other\'s memory, so the buffer cannot transfer.', 'allocator.traits')
unit(S,'noexcept-operator','noexcept is a queryable contract that terminates when violated',17,
     'A noexcept specification may be conditional: noexcept(expr) takes a constant boolean. The noexcept operator asks, without evaluating its operand, whether an expression is declared not to throw. Together they let a template promise exactly what its operations promise.|Containers use this information. vector reallocation calls std::move_if_noexcept, so a type whose move constructor may throw and that can be copied is copied during growth to keep the strong exception guarantee.|If an exception leaves a noexcept function, std::terminate is called and stack unwinding may not happen. Mark functions noexcept when failure is impossible or fatal, not to make code look faster.',
     program('type_traits', '    int a = 1, b = 2;\n    Throwing x, y;\n    std::cout << noexcept(swap_values(a, b)) << noexcept(swap_values(x, y)) << "\\n";', 'template <class T>\nvoid swap_values(T& a, T& b) noexcept(std::is_nothrow_move_constructible<T>::value && std::is_nothrow_move_assignable<T>::value) {\n    T t = std::move(a);\n    a = std::move(b);\n    b = std::move(t);\n}\nstruct Throwing {\n    Throwing() = default;\n    Throwing(Throwing&&) {}\n    Throwing& operator=(Throwing&&) { return *this; }\n};\n'),'10\n',
     ('Declare both Throwing move operations noexcept and predict the result.', [('Throwing(Throwing&&) {}', 'Throwing(Throwing&&) noexcept {}'), ('Throwing& operator=(Throwing&&) {', 'Throwing& operator=(Throwing&&) noexcept {')], '', '11\n', 'The conditional specification is computed from both traits, so it becomes true only when both move operations are noexcept.'),
     'What happens if an exception escapes a noexcept function?', 'std::terminate is called, possibly without unwinding the stack', ['The exception is converted to std::bad_exception and rethrown','It is undefined behavior that usually continues'], 'The noexcept boundary is enforced at run time by termination; whether the stack is unwound first is implementation-defined.', 'except.spec')
unit(S,'static-init-order','Function-local statics avoid initialization order dependencies',14,
     'Variables with static storage duration are first zero- or constant-initialized; dynamic initialization follows. Within one translation unit, ordered dynamic initialization follows declaration order, but across translation units the order is unspecified, so one global constructor may read another global before it is initialized.|A function-local static is initialized the first time control passes through its declaration, and since C++11 that initialization is thread-safe. Returning it by reference from an accessor turns an ordering problem into an on-demand initialization. C++20 constinit requires constant initialization and rejects a dynamic initializer.|Destruction happens in reverse order of completed construction, so a static destroyed early can still be used by a later destructor. Long-lived registries are sometimes intentionally leaked; document that choice instead of relying on accidental order.',
     program('', '    std::cout << registry_count() << "\\n";', 'int& registry_count() {\n    static int count = 0;\n    return count;\n}\nstruct Registrar { Registrar() { ++registry_count(); } };\nRegistrar first, second;\n'),'2\n',
     ('Add a third registrar object and predict the count.', 'Registrar first, second;', 'Registrar first, second, third;', '3\n', 'Each global constructor calls the accessor, which initializes the local static on first use, so no constructor reads an uninitialized counter.'),
     'Why does the accessor avoid the static initialization order problem?', 'Its local static is initialized the first time control passes through the declaration', ['Function-local statics are initialized before main in declaration order','The linker sorts globals by dependency'], 'Initialization on first use guarantees the counter exists before any caller reads it, regardless of translation-unit order.', 'stmt.dcl')
unit(S,'inline-namespace-abi','Inline namespaces version an ABI without changing spelling',14,
     'Members of an inline namespace are also members of the enclosing namespace for lookup and specialization. lib::version names lib::v2::version when v2 is inline, so client source does not mention the version.|The inline namespace name is part of mangled symbols. If a library changes a type layout and moves it to a new inline namespace, objects compiled against different versions fail to link instead of silently mixing incompatible layouts. libc++ places std entities in std::__1 for this reason.|Only one version should be inline for a given name, or unqualified references become ambiguous. Inline namespaces do not fix ODR violations within one build; they make mismatches between separately built components visible.',
     program('', '    std::cout << lib::version() << " " << lib::v1::version() << "\\n";', 'namespace lib {\ninline namespace v2 { int version() { return 2; } }\nnamespace v1 { int version() { return 1; } }\n}\n'),'2 1\n',
     ('Call the current version through its explicit name.', 'lib::v1::version()', 'lib::v2::version()', '2 2\n', 'lib::version and lib::v2::version name the same function. Qualifying with v1 selects the old version deliberately.'),
     'Why do inline namespaces help ABI versioning?', 'The version name is part of mangled symbols, so mismatched builds fail to link', ['They make every function inline','They let two layouts share one symbol safely'], 'Mangling includes the inline namespace, so lib::v2::version and lib::v1::version are different link-time names.', 'namespace.def')
unit(S,'feature-test-macros','Select code with feature-test macros, not compiler names',17,
     'Each library facility has a __cpp_lib_* macro defined in <version> and in its own header, and language features have __cpp_* macros predefined by the compiler. The values are dates, so a newer revision of a feature has a larger number. __has_include, standardized in C++17, checks whether a header can be included.|__cplusplus states the selected language mode, but a library can lag behind the compiler, and individual features are adopted separately. Testing the specific macro keeps a fallback correct across compilers and standard libraries.|A macro check only tells you what the implementation claims. Keep the fallback compiled and tested on at least one configuration, and avoid using __has_include alone as proof that the facility inside the header is enabled in the current mode.',
     program('', '#ifdef __cpp_lib_optional\n    std::cout << "optional " << (__cpp_lib_optional >= 201606L) << "\\n";\n#else\n    std::cout << "no optional\\n";\n#endif', '#if __has_include(<version>)\n#include <version>\n#endif\n'),'optional 1\n',
     ('Test for std::expected the same way while compiling as C++17.', [('__cpp_lib_optional', '__cpp_lib_expected'), ('"optional "', '"expected "'), ('"no optional\\n"', '"no expected\\n"')], '', 'no expected\n', 'std::expected is a C++23 facility, so its macro is not defined in C++17 mode and the fallback branch runs.'),
     'Why test __cpp_lib_optional rather than only __cplusplus?', 'A standard library can lack a facility even when the compiler accepts the language mode', ['__cplusplus is not defined in C++17','Feature-test macros are evaluated at run time'], 'Language mode and library support evolve separately; the facility macro reports the specific library feature.', 'version.syn')

# Stage 11: performance and low-latency C++
S='11 Performance and low-latency C++'
L=[]
unit(S,'cache-line-locality','Traverse memory in the order it is laid out',17,
     'Caches move memory in fixed-size lines, commonly 64 bytes on x86-64; Apple silicon reports 128-byte lines. Accessing consecutive addresses reuses each fetched line and lets the hardware prefetcher stream ahead, while large strides tend to waste most of each line.|A two-dimensional grid stored row-major in one vector places each row contiguously. Iterating rows in the outer loop and columns in the inner loop walks memory sequentially; swapping the loops produces a stride of one full row per access.|Locality effects depend on data size relative to each cache level, the hardware, and what else runs. Small grids that fit in L1 show little difference. Measure with representative sizes and hardware counters before restructuring code.',
     program('numeric vector', '    constexpr int rows = 3, cols = 4;\n    std::vector<int> grid(rows * cols);\n    std::iota(grid.begin(), grid.end(), 0);\n    long sum = 0;\n    for (int r = 0; r < rows; ++r)\n        for (int c = 0; c < cols; ++c) sum += grid[r * cols + c];\n    std::cout << sum << "\\n";'),'66\n',
     ('Swap the loops so the traversal is column by column, and predict the result.', 'for (int r = 0; r < rows; ++r)\n        for (int c = 0; c < cols; ++c)', 'for (int c = 0; c < cols; ++c)\n        for (int r = 0; r < rows; ++r)', '66\n', 'The sum is unchanged, but each inner step now jumps cols * sizeof(int) bytes. For grids larger than cache this tends to touch a new line on most accesses.'),
     'Why is row-by-row traversal of a row-major grid usually faster for large grids?', 'Consecutive accesses share cache lines and suit hardware prefetching', ['Because the compiler skips bounds checks only in row order','Because column order changes the arithmetic result'], 'Both orders compute the same value; row order touches memory sequentially and uses each fetched line fully.', 'intro.memory',L)
unit(S,'aos-vs-soa','Structure of arrays streams only the fields a loop uses',17,
     'An array of structures stores each record contiguously, which suits code that reads whole records. A structure of arrays stores each field in its own contiguous array, so a loop over one field reads only that field\'s bytes and is easier for the compiler to vectorize.|Padding also counts: a record of three doubles and an int occupies 32 bytes on LP64 targets, so a loop summing x reads 32 bytes per element in AoS form but 8 bytes in SoA form. Field order changes padding and therefore memory traffic.|SoA makes record insertion and whole-record access touch several arrays and keeps parallel arrays in sync by convention. Choose the layout from the dominant access pattern and measure; hybrid layouts (arrays of small field blocks) are common.',
     program('numeric vector', '    ParticlesSoA p{{1, 2, 3}, {0, 0, 0}, {0, 0, 0}, {7, 8, 9}};\n    double sx = std::accumulate(p.x.begin(), p.x.end(), 0.0);\n    std::cout << sizeof(ParticleAoS) << " " << sx << "\\n";', 'struct ParticleAoS { double x, y, z; int id; };\nstruct ParticlesSoA { std::vector<double> x, y, z; std::vector<int> id; };\n'),'32 6\n',
     ('Sum the id column instead of x.', 'std::accumulate(p.x.begin(), p.x.end(), 0.0)', 'std::accumulate(p.id.begin(), p.id.end(), 0.0)', '32 24\n', 'The id array is contiguous on its own, so this loop reads only four-byte ids. The AoS record size is unaffected.'),
     'A hot loop reads only x from a million particles. Which layout moves fewer bytes through the cache?', 'SoA: about 8 bytes per particle instead of whole 32-byte records', ['AoS, because records are contiguous','They move the same bytes because sizeof is identical'], 'In AoS form each fetched line also carries y, z, id and padding that the loop never uses.', 'class.mem',L)
unit(S,'branch-likelihood','[[likely]] and [[unlikely]] are layout hints, not guarantees',20,
     'Modern CPUs predict branch directions and speculatively execute ahead; a misprediction discards that work and typically costs on the order of tens of cycles. Branches that follow a pattern are cheap, while data-dependent branches on random input are expensive.|C++20 [[likely]] and [[unlikely]] attach to a statement or label and hint which path is more frequent, mostly influencing code layout and block ordering. They do not change program semantics or teach the hardware predictor anything at run time.|Wrong hints can make code slower, and profile-guided optimization usually does better than hand annotations. Measure with hardware counters (branch-misses with perf on Linux, CPU counters in Instruments on macOS) and keep hints on genuinely rare paths such as error handling.',
     program('', '    int total = 0;\n    for (int v : {3, 4, -1, 5}) total += classify(v);\n    std::cout << total << "\\n";', 'int classify(int v) {\n    if (v < 0) [[unlikely]] {\n        return -1;\n    }\n    return v % 3;\n}\n'),'2\n',
     ('Return zero for negative values instead of -1.', 'return -1;', 'return 0;', '3\n', 'The attribute only hints at frequency; the result changes because the returned value changed. 0 + 1 + 0 + 2 is 3.'),
     'What does [[unlikely]] change about program semantics?', 'Nothing; it is an optimization hint', ['It makes the branch evaluate lazily','It removes the branch when the condition is false'], 'Likelihood attributes affect optimization only. Correct programs behave the same with or without them.', 'dcl.attr.likelihood',L)
unit(S,'final-devirtualization','final lets the compiler devirtualize calls',17,
     'A virtual call normally loads the vtable pointer and calls through it, which blocks inlining. If the static type of the object expression is a class marked final, or the function is marked final, no further override can exist and the compiler may call the known function directly and inline it.|Devirtualization also happens when the dynamic type is visible, for example a local object, and link-time optimization can prove that a hierarchy is closed. Alternatives for hot paths include CRTP static polymorphism and std::variant with std::visit.|final is a design commitment: it forbids future derivation or overriding. The optimization is permitted, not guaranteed; check the generated assembly or optimization remarks before relying on it, and measure whether the call was hot.',
     program('', '    Square square{4};\n    std::cout << total(square) << "\\n";', 'struct Shape {\n    virtual ~Shape() = default;\n    virtual int area() const = 0;\n};\nstruct Square final : Shape {\n    int side;\n    explicit Square(int s) : side(s) {}\n    int area() const override { return side * side; }\n};\nint total(const Square& s) { return s.area(); }\n'),'16\n',
     ('Measure a side of five through the same final type.', 'Square square{4};', 'Square square{5};', '25\n', 'The parameter type is const Square&. Because Square is final, Square::area is the only possible target and the call may be made directly.'),
     'Why may a call through const Square& be devirtualized when Square is final?', 'No class can derive from Square, so the dynamic target of area is known', ['final makes area a static function','Virtual calls through references are never dynamic'], 'Without further derivation, the static type determines the final overrider.', 'class.virtual',L)
unit(S,'small-string-capacity','Short strings fit inline: observing libc++ small-string storage',17,
     'std::string implementations commonly keep short strings inside the object itself, avoiding a heap allocation. The standard does not require this or fix the inline capacity. libc++ on 64-bit targets uses a 24-byte string with 22 inline characters; libstdc++ uses a 32-byte string with 15.|capacity() reveals the policy: a default or short libc++ string reports 22. Once the content exceeds the inline buffer, the string allocates and capacity grows. Moving a long string transfers its heap buffer; moving a short string copies its inline characters.|The output of this example is libc++-specific; libstdc++ prints different numbers. Do not hard-code inline capacities in production logic, and remember that string_view or pointers into a short string refer to the string object itself, not to a stable heap block.',
     program('string', '    std::string small = "short";\n    std::string large(40, \'x\');\n    std::cout << sizeof(std::string) << " " << small.capacity() << " " << (large.capacity() >= 40) << "\\n";'),'24 22 1\n',
     ('Assign exactly 22 characters to the short string and predict its capacity on libc++.', '"short"', '"exactly-twenty-two-chr"', '24 22 1\n', 'Twenty-two characters plus the terminator still fit in the inline buffer, so libc++ reports the same capacity and no allocation is needed.'),
     'On libc++ with 64-bit pointers, how many characters fit in std::string without allocating?', '22', ['15 on every implementation','0, because std::string always allocates'], 'libc++ uses 23 inline bytes including the terminator; libstdc++ uses 15 characters. The standard leaves this unspecified.', 'basic.string',L)
UNITS[-1]['support'] = 'Expected output is libc++-specific (Apple clang); libstdc++ reports a 32-byte string with 15 inline characters.'
unit(S,'monotonic-arena','A monotonic buffer resource turns allocations into pointer bumps',17,
     'std::pmr::monotonic_buffer_resource hands out memory by advancing a position in a buffer and never reuses freed memory. Allocation is a few instructions and deallocate does nothing; everything is released at once when the resource is destroyed or release() is called.|Pass a stack or preallocated buffer and an upstream resource. With std::pmr::null_memory_resource() as upstream, running out of the buffer throws std::bad_alloc instead of silently reaching the heap, which makes an allocation budget testable. pmr containers propagate the resource to nested pmr elements through uses-allocator construction.|Memory freed by growing containers is not reused, so repeated vector growth wastes old blocks; reserve up front. The resource is not thread-safe, and every object using it must be destroyed before the buffer goes out of scope.',
     program('array cstddef memory_resource new numeric vector', '    std::array<std::byte, 1024> buffer;\n    std::pmr::monotonic_buffer_resource arena{buffer.data(), buffer.size(), std::pmr::null_memory_resource()};\n    std::pmr::vector<int> values{&arena};\n    values.reserve(8);\n    for (int i = 0; i < 8; ++i) values.push_back(i);\n    std::cout << std::accumulate(values.begin(), values.end(), 0) << "\\n";'),'28\n',
     ('Try to reserve 300 ints, more than the 1024-byte buffer, and report the failure.', 'values.reserve(8);', 'try { values.reserve(300); } catch (const std::bad_alloc&) { std::cout << "exhausted\\n"; }', 'exhausted\n28\n', 'Twelve hundred bytes do not fit and the null upstream refuses, so bad_alloc is thrown. The following pushes still fit in the remaining buffer.'),
     'What does deallocate do on a monotonic_buffer_resource?', 'Nothing; memory is reclaimed only by release() or destruction', ['It returns the block for reuse by the next allocation','It forwards the block to the upstream resource'], 'Monotonic means the allocation position only moves forward; individual frees are ignored.', 'mem.res.monotonic.buffer',L)
unit(S,'benchmark-pitfalls','A benchmark must keep its work observable',17,
     'Optimizers remove computations whose results are unused, hoist loop-invariant work, and fold constants. A timed loop that produces nothing observable may measure an empty loop. Feed inputs the compiler cannot predict and consume results, for example by accumulating a checksum that is printed or checked.|Use std::chrono::steady_clock, which never goes backwards; system_clock can jump when the wall clock is adjusted. Run warmup iterations to fault in pages and warm caches and predictors, repeat many samples, and report a median or distribution rather than one number.|Record compiler flags, hardware, CPU frequency behavior and input sizes. Timing values are not deterministic, so tests should check correctness and keep timing output out of compared stdout. Libraries such as Google Benchmark provide DoNotOptimize and statistics; still verify the result being timed.',
     program('chrono', '    auto start = std::chrono::steady_clock::now();\n    long long checksum = 0;\n    for (int rep = 0; rep < 3; ++rep)\n        for (int i = 0; i < 1000; ++i) checksum += i % 7;\n    auto elapsed = std::chrono::steady_clock::now() - start;\n    std::cout << checksum << " " << (elapsed.count() >= 0) << "\\n";'),'8991 1\n',
     ('Run five repetitions instead of three.', 'rep < 3', 'rep < 5', '14985 1\n', 'Each pass adds 2997 (142 full cycles of 0..6 plus 0..5), so five passes give 14985. steady_clock is monotonic, so the elapsed duration is never negative.'),
     'Why accumulate and print a checksum of the measured work?', 'So the optimizer cannot delete the computation as dead code', ['Because printing makes the loop run faster','Because steady_clock requires output'], 'Only observable behavior must be preserved. An unused result lets the compiler remove the timed work.', 'time.clock.steady',L)
unit(S,'branchless-select','Branchless selection trades a branch for data dependencies',17,
     'A comparison yields a bool that converts to 0 or 1. Adding it counts matches without a conditional jump, and negating it gives an all-zero or all-ones mask for selecting a value with &. The work is the same for every input, so there is nothing to mispredict.|Compilers often emit conditional-select instructions (csel on arm64, cmov on x86-64) for simple ternaries already, so hand-written masks may not change the generated code. Inspect the assembly before and after.|Branchless code always computes both sides and lengthens the dependency chain. When the branch is predictable, a branch is often faster. Keep the readable version unless measurement on representative data shows a win.',
     program('vector', '    std::vector<int> data{5, -3, 8, -1, 0, 7};\n    int positives = 0;\n    long long sum = 0;\n    for (int v : data) {\n        positives += (v > 0);\n        sum += v & -static_cast<int>(v > 0);\n    }\n    std::cout << positives << " " << sum << "\\n";'),'3 20\n',
     ('Count and sum the non-negative values instead.', '(v > 0)', '(v >= 0)', '4 20\n', 'Zero now passes the test, so the count rises to four while the sum is unchanged. Both occurrences of the comparison are replaced.'),
     'When does branchless code tend to win?', 'When the branch depends on unpredictable data', ['Always, because branches are slow','When the branch is almost always taken'], 'A predictable branch costs little; branchless code pays for both sides on every element.', 'conv.prom',L)
unit(S,'pow2-mask-popcount','Power-of-two masks and bit counts replace division and loops',20,
     'For unsigned x and a power of two n, x % n equals x & (n - 1), because n - 1 masks the low bits. Ring buffers choose power-of-two capacities so index wrapping is a single AND. C++20 <bit> provides std::has_single_bit, std::bit_ceil, std::popcount, std::countr_zero and related functions.|These functions usually compile to single instructions where the target has them, such as a count-trailing-zeros instruction, and to short sequences otherwise. Compilers already rewrite unsigned % by a constant power of two, so the mask matters most when n is a runtime value.|The identity fails for signed negative operands: -3 % 8 is -3 in C++, while -3 & 7 is 5. Keep indices unsigned, assert the power-of-two precondition, and prefer the <bit> functions to hand-written loops.',
     program('bit', '    constexpr unsigned capacity = 16;\n    static_assert(std::has_single_bit(capacity));\n    unsigned index = 45;\n    std::cout << (index & (capacity - 1)) << " " << (index % capacity) << " " << std::popcount(0b1011\'0110u) << " " << std::countr_zero(capacity) << "\\n";'),'13 13 5 4\n',
     ('Use a capacity of eight and predict every value.', 'capacity = 16;', 'capacity = 8;', '5 5 5 3\n', '45 is 0b101101; masking with 7 keeps 0b101. The popcount literal is unchanged, and eight has three trailing zero bits.'),
     'For unsigned x, why does x & (n - 1) equal x % n only when n is a power of two?', 'Only then is n - 1 a mask of the low log2(n) bits', ['Because & rounds toward zero','It holds for every n greater than one'], 'For n = 6, n - 1 is 0b101, which does not select a contiguous low bit range.', 'bit.count',L)
unit(S,'memory-order-cost','Memory-order cost differs between x86 and ARM',17,
     'x86-64 has a strong (TSO) memory model: ordinary loads already behave like acquire and ordinary stores like release, so acquire and release atomics compile to plain moves; only sequentially consistent stores need an extra fence or exchange. ARMv8 is weaker and uses dedicated instructions such as LDAR or LDAPR for acquire and STLR for release.|Relaxed operations are still atomic and are the right choice for counters whose final total is read after a synchronizing operation. Release and acquire pair to publish ordinary data: everything sequenced before the release store is visible after an acquire load that reads it.|Code missing an acquire often appears to work on x86 because the hardware already orders it, then fails on ARM machines including Apple silicon. Reason from the C++ memory model, test on weakly ordered hardware, and use ThreadSanitizer; do not infer correctness from one architecture.',
     program('atomic thread', '    std::atomic<int> hits{0};\n    std::atomic<bool> ready{false};\n    int payload = 0;\n    std::thread producer([&] {\n        for (int i = 0; i < 1000; ++i) hits.fetch_add(1, std::memory_order_relaxed);\n        payload = 42;\n        ready.store(true, std::memory_order_release);\n    });\n    while (!ready.load(std::memory_order_acquire)) {}\n    std::cout << payload << " " << hits.load(std::memory_order_relaxed) << "\\n";\n    producer.join();'),'42 1000\n',
     ('Count two thousand events before publishing.', 'i < 1000', 'i < 2000', '42 2000\n', 'The relaxed increments are sequenced before the release store, so the acquire load that sees true also guarantees every increment and the payload are visible.'),
     'Why can a missing acquire go unnoticed on x86 but fail on ARM?', 'x86 hardware already orders ordinary loads like acquire, while ARM may reorder them', ['ARM does not support atomics','x86 compilers ignore memory orders'], 'The language bug exists on both; only the hardware reordering that exposes it differs.', 'atomics.order',L)
unit(S,'hot-cold-splitting','Keep hot fields together and move cold data out of line',17,
     'A hot path that touches only a few fields should not drag rarely used data through the cache. Hot/cold splitting keeps frequently accessed fields in a compact record and moves cold fields, such as descriptions and audit data, behind a pointer or into a parallel structure.|The same idea applies to code: marking error handling as cold or moving it into a separate non-inlined function keeps the hot instruction stream compact. Clang and GCC accept [[gnu::cold]] and [[gnu::noinline]] as extensions for that purpose.|Splitting adds an indirection and an allocation when cold data is needed, and it can complicate ownership. Measure the record size with sizeof, count how many hot records fit in a cache line on the target, and confirm the win on the real access pattern.',
     program('array cstdint memory string', '    std::cout << sizeof(Order) << " " << (sizeof(Order) <= 64) << "\\n";', 'struct Cold { std::string description; std::array<char, 64> audit{}; };\nstruct Order {\n    std::uint64_t id;\n    std::int64_t price;\n    std::int32_t quantity;\n    std::unique_ptr<Cold> cold;\n};\n'),'32 1\n',
     ('Store the cold data inline instead of behind a pointer.', 'std::unique_ptr<Cold> cold;', 'Cold cold;', '112 0\n', 'The inline Cold block adds a 24-byte libc++ string and 64 audit bytes, so the record grows from 32 to 112 bytes on LP64 libc++ and no longer fits a 64-byte line.'),
     'Why move rarely used fields behind a pointer?', 'More hot records fit per cache line, at the cost of an indirection for cold access', ['It removes the need to allocate cold data','It makes the cold fields faster to read'], 'The hot loop reads fewer bytes per record; cold access pays one extra load.', 'class.mem',L)
unit(S,'counting-operator-new','Count allocations by replacing global operator new',17,
     'A program may replace the global operator new and operator delete. A replacement that increments a counter and forwards to malloc makes allocation counts observable in tests, which is more stable than timing for catching regressions such as a missing reserve.|vector growth multiplies capacity, so n push_back calls perform about log n allocations; libc++ and libstdc++ double from one. reserve(n) allocates once and later insertions within capacity never allocate.|Define the sized and unsized delete forms as well, since compilers call sized delete by default in C++14 and later. The counter is global and not thread-safe here; use an atomic for multithreaded tests, and remember that the standard library or the runtime may allocate on its own before main.',
     program('cstdlib new vector', '    allocations = 0;\n    std::vector<int> grown;\n    for (int i = 0; i < 100; ++i) grown.push_back(i);\n    const std::size_t without_reserve = allocations;\n    allocations = 0;\n    std::vector<int> reserved;\n    reserved.reserve(100);\n    for (int i = 0; i < 100; ++i) reserved.push_back(i);\n    const std::size_t with_reserve = allocations;\n    std::cout << without_reserve << " " << with_reserve << "\\n";', 'static std::size_t allocations = 0;\nvoid* operator new(std::size_t size) {\n    ++allocations;\n    if (void* p = std::malloc(size ? size : 1)) return p;\n    throw std::bad_alloc{};\n}\nvoid operator delete(void* p) noexcept { std::free(p); }\nvoid operator delete(void* p, std::size_t) noexcept { std::free(p); }\n'),'8 1\n',
     ('Reserve only fifty elements before the hundred insertions.', 'reserved.reserve(100);', 'reserved.reserve(50);', '8 2\n', 'Capacity 50 covers the first fifty insertions; the fifty-first grows to 100 (double the capacity), which holds the rest. Growth without reserve passes 1, 2, 4, ..., 128: eight allocations.'),
     'Why is reserve(100) followed by 100 push_back calls exactly one allocation?', 'The reserved capacity covers every insertion, so no reallocation occurs', ['push_back always allocates one node per element','reserve is only a hint that may be ignored'], 'reserve guarantees capacity of at least n; insertions that do not exceed capacity do not reallocate.', 'new.delete.single',L)


# Drills: existing stage-09 lessons
LIMITS = 'struct Limits { static constexpr int cap = 5; };\n'
drill('odr-and-linkage','Compiles?','A static constexpr member bound to a reference in C++14',
      main_program('    std::cout << std::max(Limits::cap, 1) << "\\n";','algorithm iostream',LIMITS),
      'Does this build as C++14 at -O0?','No: std::max binds a reference, odr-using Limits::cap, which has no definition, so linking fails',
      ['Yes, and it prints 5','No: constexpr members cannot be passed to std::max'],
      'Before C++17 a static constexpr data member declared in the class is not a definition. Binding const int& odr-uses it, so the linker needs an out-of-class definition.',
      check='reject',standard=14,diagnostic='Undefined symbols')
drill('odr-and-linkage','Predict output','The same program as C++17',
      main_program('    std::cout << std::max(Limits::cap, 1) << "\\n";','algorithm iostream',LIMITS),
      'Compiled as C++17, what does this print?','5',['It fails to link','1'],
      'C++17 makes static constexpr data members implicitly inline, so the in-class declaration is a definition and the odr-use links.',standard=17)
drill('odr-and-linkage','Compiles?','Declared but never defined',
      main_program('    std::cout << helper(2) << "\\n";','iostream','int helper(int);'),
      'Does this program build?','No: it compiles, but the linker reports an undefined symbol for helper',
      ['Yes, helper returns 0 by default','No: the compiler rejects the call before linking'],
      'A declaration is enough to compile the call. The missing definition is detected only when the linker resolves symbols.',check='reject',diagnostic='Undefined symbols')
drill('odr-and-linkage','Undefined behavior','Two different inline definitions',
      '','a.cpp defines inline int limit() { return 1; } and b.cpp defines inline int limit() { return 2; }. Both link into one program. What does the standard say?',
      'The program is ill-formed, no diagnostic required: an ODR violation',
      ['The linker always reports a duplicate symbol','Each translation unit sees its own definition, which is well defined'],
      'Inline functions may be defined in several translation units only if every definition is the same token sequence with the same meaning. The linker usually keeps one copy silently.',check='reasoning')
drill('c-linkage','Compiles?','Overloading two C-linkage functions',
      main_program('','iostream','extern "C" int area(int w) { return w; }\nextern "C" int area(int w, int h) { return w * h; }'),
      'Does this compile?','No: two functions with C language linkage cannot share a name',
      ['Yes: overloads are distinguished by mangling','Yes, but only the first can be called'],
      'C linkage uses the unmangled name, so at most one function with that name may have C linkage. Clang reports conflicting types.',check='reject',diagnostic='conflicting types')
drill('c-linkage','Predict output','One C function among C++ overloads',
      main_program('    std::cout << area(3) << " " << area(2, 5) << "\\n";','iostream','extern "C" int area(int side) { return side * side; }\nint area(int w, int h) { return w * h; }'),
      'Does this compile, and what does it print?','9 10',['It does not compile: extern "C" names cannot be overloaded','9 9'],
      'Only one of the overloads has C linkage; the C++ overload is mangled with its parameter types, so both coexist.')
drill('c-linkage','Code review','An exception crossing a C callback',
      '','A C library calls your extern "C" callback, and the callback can throw std::runtime_error. What is the correct fix?',
      'Catch every exception inside the callback and translate it to the C error convention',
      ['Mark the callback noexcept and let it throw','Nothing: exceptions propagate through C frames portably'],
      'Unwinding through C frames is not portable and C code cannot clean up its state. The boundary must convert exceptions into return codes or stored errors.',check='reasoning')
drill('compile-diagnostics','Compiles?','A temporary passed to a non-const reference',
      main_program('    f(3);','iostream','void f(int& x) { ++x; }'),
      'Does this compile?','No: a non-const lvalue reference cannot bind to the prvalue 3',
      ['Yes: a temporary int is created and incremented','Yes, with a narrowing warning'],
      'Only const lvalue references and rvalue references bind to temporaries, so the call has no viable candidate.',check='reject',diagnostic='no matching function')
drill('compile-diagnostics','Compiles?','Binding int& to a literal',
      main_program('    int& r = 5;\n    std::cout << r << "\\n";'),
      'Does this compile?','No: non-const lvalue reference cannot bind to a temporary',
      ['Yes, and it prints 5','Yes, but reading r is undefined'],
      'The rule is the same for local references and parameters. const int& r = 5 would extend the temporary lifetime.',check='reject',diagnostic='non-const lvalue reference')
drill('compile-diagnostics','Predict output','Lifetime extension through a const reference',
      main_program('    const std::string& s = std::string("ab") + "c";\n    std::cout << s.size() << "\\n";','iostream string'),
      'What does this print?','3',['Undefined: the temporary is destroyed at the semicolon','2'],
      'Binding a temporary directly to a const reference local extends its lifetime to that of the reference.')
drill('performance-contracts','Predict output','lower_bound versus upper_bound',
      main_program('    std::vector<int> v{1, 3, 3, 5};\n    std::cout << (std::lower_bound(v.begin(), v.end(), 3) - v.begin()) << " " << (std::upper_bound(v.begin(), v.end(), 3) - v.begin()) << "\\n";','algorithm iostream vector'),
      'What does this print?','1 3',['1 2','2 3'],
      'lower_bound finds the first element not less than 3; upper_bound finds the first element greater than 3. The distance between them is the count of 3s.')
drill('performance-contracts','Complexity','Erasing inside a loop',
      '','A loop calls v.erase(it) for every even element of a std::vector of n ints. What is the worst-case cost, and the standard fix?',
      'O(n^2) element moves; use std::erase_if or erase-remove for one O(n) pass',
      ['O(n) because erase is constant time','O(n log n) because erase rebalances'],
      'Each vector erase shifts all later elements. A single remove pass moves each kept element at most once.',check='reasoning',complexity='Quadratic loop versus linear remove pass.')
drill('performance-contracts','Code review','A benchmark that measures nothing',
      '','At -O2, a benchmark times for (int i = 0; i < n; ++i) compute(data[i]); and discards every result. compute is inline and has no side effects. What is the likely problem?',
      'The optimizer may delete the loop, so the timer measures almost nothing',
      ['The loop runs slower because results are discarded','Nothing: optimizers never remove timed code'],
      'Only observable behavior must be preserved. Consume the results, for example with a checksum or a DoNotOptimize barrier.',check='reasoning')
drill('alignment-and-allocation','Layout','An over-aligned type',
      main_program('    std::cout << alignof(V) << " " << sizeof(V) << "\\n";','iostream','struct alignas(32) V { float f[4]; };'),
      'What does this print?','32 32',['16 16','32 16'],
      'alignas raises the alignment to 32, and sizeof is always a multiple of alignment so arrays of V stay aligned.',standard=17)
drill('alignment-and-allocation','Layout','Padding between mixed members',
      main_program('    std::cout << sizeof(A) << " " << alignof(A) << "\\n";','iostream','struct A { char c; double d; char e; };'),
      'On arm64 macOS, what does this print?','24 8',['10 8','16 8'],
      'd needs 8-byte alignment, so 7 padding bytes follow c, and 7 trailing bytes round the size up to a multiple of 8. Reordering to d, c, e would give 16.')
drill('alignment-and-allocation','Predict output','new for an over-aligned type in C++17',
      main_program('    V* p = new V;\n    std::cout << (reinterpret_cast<std::uintptr_t>(p) % 32 == 0) << "\\n";\n    delete p;','cstdint iostream','struct alignas(32) V { float f[4]; };'),
      'Compiled as C++17, what does this print?','1',['0','It depends on malloc, so it is unspecified'],
      'C++17 new-expressions call operator new(std::size_t, std::align_val_t) for over-aligned types, so the result honours alignof(V).',standard=17)
drill('cpp14-evolution','Predict output','A generic lambda',
      main_program('    auto add = [](auto a, auto b) { return a + b; };\n    std::cout << add(1, 2.5) << " " << add(std::string("a"), "b") << "\\n";','iostream string'),
      'What does this print?','3.5 ab',['3 ab','It does not compile: auto parameters need C++20'],
      'C++14 generic lambdas have a templated call operator; each call deduces its own parameter types.')
drill('cpp14-evolution','Copies and moves','Init-capture moves ownership',
      main_program('    auto p = std::make_unique<int>(4);\n    auto f = [q = std::move(p)] { return *q * 2; };\n    std::cout << f() << " " << (p == nullptr) << "\\n";','iostream memory utility'),
      'What does this print?','8 1',['8 0','It does not compile: unique_ptr cannot be captured'],
      'The init-capture move-constructs q from p, leaving p null. The closure now owns the int.')
drill('cpp14-evolution','Predict output','Binary literals and digit separators',
      main_program("    std::cout << 0b1010'0000 << \" \" << 1'000'000 / 1'000 << \"\\n\";"),
      'What does this print?','160 1000',['10100000 1000','A0 1000'],
      'Digit separators are ignored by the value; 0b10100000 is 128 + 32 = 160, printed in decimal.')
drill('cpp14-evolution','Compiles?','A generic lambda compiled as C++11',
      main_program('    auto f = [](auto a) { return a; };\n    std::cout << f(1) << "\\n";'),
      'Compiled with -std=c++11, does this compile?','No: auto lambda parameters require C++14',
      ['Yes, it prints 1','Yes, with a deprecation warning'],
      'Clang rejects auto in a lambda parameter list before C++14.',check='reject',standard=11,diagnostic="'auto' not allowed in lambda parameter")
drill('cpp17-evolution','Predict output','if constexpr selects per instantiation',
      main_program('    std::cout << describe(21) << " " << describe(std::string("abc")) << "\\n";','iostream string type_traits',
                   'template <class T> auto describe(T v) {\n    if constexpr (std::is_integral_v<T>) return v * 2;\n    else return v.size();\n}'),
      'What does this print?','42 3',['It does not compile: int has no size()','42 6'],
      'The discarded branch of if constexpr is not instantiated, so v.size() is never checked for int and v * 2 is never checked for string.')
drill('cpp17-evolution','Predict output','Structured bindings over a map',
      main_program('    std::map<std::string, int> m{{"b", 2}, {"a", 1}};\n    for (const auto& [key, value] : m) std::cout << key << value;\n    std::cout << "\\n";','iostream map string'),
      'What does this print?','a1b2',['b2a1','ab12'],
      'std::map iterates in key order; each element is a pair whose members are bound to key and value.')
drill('cpp17-evolution','Compiles?','std::optional compiled as C++14',
      main_program('    std::optional<int> o;\n    std::cout << o.has_value() << "\\n";','iostream optional'),
      'With libc++ and -std=c++14, does this compile?','No: std::optional is not declared before C++17',
      ['Yes, it prints 0','Yes, but has_value is missing'],
      'The header exists, but libc++ only declares std::optional in C++17 and later modes.',check='reject',standard=14,diagnostic="no member named 'optional'")
drill('cpp17-evolution','Predict output','Class template argument deduction',
      main_program('    std::pair p{1, 2.5};\n    std::vector v{1, 2, 3};\n    std::cout << sizeof(p.second) << v.size() << "\\n";','iostream utility vector'),
      'What does this print?','83',['43','It does not compile: template arguments are missing'],
      'CTAD deduces pair<int, double> and vector<int>, so p.second is an 8-byte double.')
drill('cpp20-evolution','Predict output','A defaulted three-way comparison',
      main_program('    std::cout << (P{1, 2} < P{1, 3}) << (P{2, 0} > P{1, 9}) << "\\n";','compare iostream','struct P { int x, y; auto operator<=>(const P&) const = default; };'),
      'What does this print?','11',['10','01'],
      'Defaulted <=> compares members lexicographically in declaration order, and the relational operators are rewritten in terms of it.')
drill('cpp20-evolution','Compiles?','A spaceship operator compiled as C++17',
      main_program('','iostream','struct P { int x; auto operator<=>(const P&) const = default; };'),
      'Compiled with -std=c++17, does this compile?','No: <=> is not a token before C++20, so the declaration does not parse',
      ['Yes: it defines all six comparisons','Yes, with a warning only'],
      'In C++17, <=> lexes as <= followed by >, which makes the member declaration invalid.',check='reject',standard=17,diagnostic="cannot be the name of a variable")
drill('cpp20-evolution','Predict output','Designated initializers keep defaults',
      main_program('    Opt o{.h = 5};\n    std::cout << o.w << o.h << "\\n";','iostream','struct Opt { int w = 1; int h = 2; };'),
      'What does this print?','15',['05','12'],
      'Members not named in a designated initializer use their default member initializers.')
drill('cpp20-evolution','Compiles?','A standard concept compiled as C++17',
      main_program('    std::cout << twice(2) << "\\n";','concepts iostream','template <std::integral T> T twice(T x) { return 2 * x; }'),
      'With libc++ and -std=c++17, does this compile?','No: std::integral is not declared before C++20',
      ['Yes, it prints 4','Yes: constrained parameters are a C++17 feature'],
      'The <concepts> library and constrained template parameters are C++20 facilities.',check='reject',standard=17,diagnostic="no type named 'integral'")
drill('cpp23-evolution','Predict output','to_underlying and contains',
      main_program('    std::cout << std::to_underlying(E::a) << " " << std::string("hello").contains("ell") << "\\n";','iostream string utility','enum class E : int { a = 3 };'),
      'What does this print?','3 1',['a 1','3 true'],
      'std::to_underlying converts the enumerator to int, and std::string::contains returns bool, printed as 1.')
drill('cpp23-evolution','Predict output','optional::and_then',
      main_program('    std::optional<int> o{4};\n    auto r = o.and_then([](int x) -> std::optional<int> { return x > 3 ? std::optional<int>{x * 10} : std::nullopt; });\n    std::cout << r.value_or(-1) << "\\n";','iostream optional'),
      'What does this print?','40',['4','-1'],
      'and_then calls the function with the contained value and returns its optional result directly.')
drill('cpp23-evolution','Compiles?','std::expected compiled as C++20',
      main_program('    std::expected<int, int> e{1};\n    std::cout << *e << "\\n";','expected iostream'),
      'With libc++ and -std=c++20, does this compile?','No: std::expected is a C++23 facility',
      ['Yes, it prints 1','Yes, but * is unavailable'],
      'libc++ declares std::expected only in C++23 mode.',check='reject',standard=20,diagnostic="no member named 'expected'")
drill('cpp23-evolution','Undefined behavior','Reaching std::unreachable',
      '','A switch ends with default: std::unreachable(); and an unexpected enum value arrives at run time. What happens?',
      'Undefined behavior: the optimizer may assume that path never executes',
      ['std::terminate is called','A std::logic_error is thrown'],
      'std::unreachable is an optimization promise, not a check. Use an assertion or explicit error path when the value can occur.',check='reasoning')
drill('modules','Concept','Macros across a named module import',
      '','A module interface unit defines #define LIMIT 10 and exports a function. Does import m; make LIMIT visible to the importer?',
      'No: importing a named module does not import its macros',
      ['Yes: every directive in the interface is exported','Only if LIMIT is declared export'],
      'Named modules export declarations, not preprocessor state. Header units are the exception and do make macros available.',check='reasoning')
drill('modules','Concept','Build order with module interfaces',
      '','Why must a build system compile a module interface before the units that import it?',
      'Importers need the compiled module interface (BMI) that the interface produces',
      ['Because the linker resolves imports','It does not; modules can be compiled in any order like headers'],
      'Unlike textual inclusion, import reads a compiler-produced interface artifact, so the dependency graph determines compile order.',check='reasoning')
drill('modules','Concept','A non-exported function in an interface unit',
      '','A module interface declares int helper(); without export. Can a translation unit that imports the module call helper?',
      'No: it has module linkage and is visible only inside the module',
      ['Yes: every function in the interface is exported','Yes, but only through ADL'],
      'Only exported declarations become visible to importers; non-exported names stay attached to the module.',check='reasoning')
drill('reflection26','Concept','What a reflection value represents',
      '','In the C++26 reflection design, what does ^^int produce?',
      'A std::meta::info value that represents the type, usable during constant evaluation',
      ['A runtime std::type_info object','A string containing the type name'],
      'Reflection values are compile-time handles; queries on them run in consteval contexts and splicing turns them back into code.',check='reasoning')
drill('reflection26','Concept','Runtime cost of reflection queries',
      '','A program enumerates a struct\'s members with reflection to generate a printer. Where do the member queries run?',
      'At compile time, during constant evaluation; only the generated code runs',
      ['At program start-up, from embedded metadata','On every call, by scanning a symbol table'],
      'Static reflection does not require runtime metadata; std::meta::info values cannot exist at run time.',check='reasoning')
drill('reflection26','Code review','Shipping reflection code today',
      '','A team wants to ship code that uses C++26 reflection with their current production compiler. What must they check first?',
      'Whether that compiler and library version actually implements the adopted reflection features',
      ['Nothing: adoption into the working draft makes it available everywhere','Only that -std=c++2c is accepted'],
      'Acceptance of a language-mode flag does not imply a feature is implemented. Check the compiler status tables and feature-test macros.',check='reasoning')
drill('contracts26','Concept','Contract evaluation semantics',
      '','Which C++26 contract evaluation semantic checks the predicate and continues after reporting a violation?',
      'observe',['ignore','enforce'],
      'ignore does not check, enforce reports and terminates, and observe reports and continues. The semantic is chosen by the implementation or build, not the source.',check='reasoning')
drill('contracts26','Code review','Side effects in a precondition',
      '','A precondition is written pre(log_and_check(x)), where log_and_check increments a counter. What is the problem?',
      'The predicate may be evaluated zero, one or more times, so the side effect is unreliable',
      ['Nothing: preconditions are evaluated exactly once','The counter is incremented only in release builds'],
      'Contract predicates should be free of required side effects because evaluation count and semantic depend on the build configuration.',check='reasoning')
drill('contracts26','Concept','pre versus contract_assert',
      '','How does pre(x > 0) on a function declaration differ from contract_assert(x > 0) in its body?',
      'pre is part of the function interface that callers can see; contract_assert is a statement inside the implementation',
      ['They are identical spellings','contract_assert is checked at compile time only'],
      'Preconditions document a caller obligation on the declaration, while an assertion checks a condition at a point in the body.',check='reasoning')
drill('execution26','Concept','When a sender starts work',
      '','In std::execution, what happens when you create a sender with just(1) | then(f)?',
      'Nothing runs yet; work starts only after connecting to a receiver and starting the operation state',
      ['f runs immediately on the calling thread','f runs on a background thread pool'],
      'Senders describe work lazily. connect produces an operation state and start begins execution.',check='reasoning')
drill('execution26','Concept','Completion channels',
      '','Which three completion signals can a sender deliver to a receiver?',
      'set_value, set_error and set_stopped',
      ['then, upon_error and on','return, throw and terminate'],
      'Success, failure and cancellation are separate channels so cancellation is not disguised as an error.',check='reasoning')
drill('execution26','Code review','Moving a started operation state',
      '','Code stores an operation state in a std::vector and keeps pushing new elements after calling start on it. What is the risk?',
      'Reallocation moves the started operation state, but it must stay at a stable address until completion',
      ['None: operation states are cheap to copy','The vector will deadlock'],
      'Operation states are typically immovable and may be referenced by pending callbacks; store them where their address is stable.',check='reasoning')
drill('inplace-vector26','Concept','Pushing beyond capacity',
      '','std::inplace_vector<int, 4> already holds four elements. What does push_back(5) do?',
      'It throws std::bad_alloc',['It reallocates on the heap','It silently overwrites the last element'],
      'Capacity is fixed in the object. try_push_back reports failure without throwing, and unchecked_push_back makes room a precondition.',check='reasoning')
drill('inplace-vector26','Layout','Where inplace_vector stores elements',
      '','Where are the elements of a local std::inplace_vector<double, 8> stored?',
      'Inside the inplace_vector object itself, so this one lives on the stack',
      ['In a heap block owned by the object','In static storage shared by all instances'],
      'The storage is embedded like std::array, but only the first size() elements are alive.',check='reasoning')
drill('inplace-vector26','Concept','Element lifetime in fixed storage',
      '','How does std::inplace_vector<std::string, 4> differ from std::array<std::string, 4> right after default construction?',
      'The inplace_vector has size 0 and constructs no strings; the array constructs four',
      ['Both construct four empty strings','Neither constructs any string'],
      'inplace_vector constructs elements on insertion and destroys them on removal, like vector, despite its inline storage.',check='reasoning')
drill('simd26','Concept','Lane count',
      '','What determines std::simd<float>::size() for the default ABI tag?',
      'The implementation and target, so code must not assume a fixed lane count',
      ['It is always 4','It is always 8'],
      'Width depends on the target vector registers and implementation choices. Write loops in terms of size().',check='reasoning')
drill('simd26','Code review','Forgetting the remainder',
      '','A loop processes an array of 1003 floats in steps of std::simd<float>::size() and stops when fewer than size() remain. What is the bug?',
      'The tail elements are never processed; a scalar or masked remainder loop is needed',
      ['None: simd pads the array automatically','It reads out of bounds on every iteration'],
      'Unless n is a multiple of the width, a remainder policy is required for correctness.',check='reasoning')
drill('simd26','Concept','Element-wise semantics',
      '','For simd values a and b, what does a < b produce?',
      'A mask with one boolean per lane',['A single bool comparing the first lanes','A single bool true only when every lane is less'],
      'Operations are element-wise. Reductions such as all_of or any_of convert a mask to one bool.',check='reasoning')
drill('preprocessor','Predict output','An unparenthesized macro argument',
      main_program('    std::cout << SQUARE(1 + 2) << "\\n";','iostream','#define SQUARE(x) x * x'),
      'What does this print?','5',['9','3'],
      'The tokens expand to 1 + 2 * 1 + 2, which is 5. Parenthesize parameters and the whole body, or use a constexpr function.')
drill('preprocessor','Predict output','Double evaluation in a MAX macro',
      main_program('    int i = 1, j = 0;\n    int m = MAX(i++, j);\n    std::cout << m << " " << i << "\\n";','iostream','#define MAX(a, b) ((a) > (b) ? (a) : (b))'),
      'What does this print?','2 3',['1 2','2 2'],
      'The argument i++ appears twice in the expansion: the condition reads 1 and increments to 2, then the selected branch yields 2 and increments to 3.')
drill('preprocessor','Predict output','Stringizing with and without indirection',
      main_program('    std::cout << STR(N) << " " << XSTR(N) << "\\n";','iostream','#define N 42\n#define STR(x) #x\n#define XSTR(x) STR(x)'),
      'What does this print?','N 42',['42 42','N N'],
      'The # operator stringizes its argument without expanding it first. XSTR expands N while substituting, then STR stringizes 42.')
drill('namespace-lookup','Predict output','Argument-dependent lookup beats an ellipsis',
      main_program('    std::cout << describe(geo::P{}) << "\\n";','iostream','namespace geo { struct P {}; int describe(P) { return 1; } }\nint describe(...) { return 0; }'),
      'What does this print?','1',['0','It does not compile: the call is ambiguous'],
      'ADL adds geo::describe to the candidates, and an exact match beats an ellipsis conversion.')
drill('namespace-lookup','Predict output','Unqualified lookup from inside a namespace',
      main_program('    std::cout << inner::get() << ::value << "\\n";','iostream','int value = 1;\nnamespace inner { int value = 2; int get() { return value; } }'),
      'What does this print?','21',['11','22'],
      'Lookup inside inner finds inner::value first; ::value explicitly names the global.')
drill('namespace-lookup','Compiles?','Two using-directives with the same name',
      main_program('    std::cout << f() << "\\n";','iostream','namespace a { int f() { return 1; } }\nnamespace b { int f() { return 2; } }\nusing namespace a;\nusing namespace b;'),
      'Does this compile?','No: the call to f is ambiguous',['Yes, it prints 2','Yes, it prints 1'],
      'Both using-directives make their f visible as if declared in the global namespace; neither is preferred.',check='reject',diagnostic="call to 'f' is ambiguous")
drill('manual-union-lifetime','Predict output','Assignment changes the active member',
      main_program('    U u;\n    u.f = 2.5f;\n    std::cout << u.f << "\\n";','iostream','union U { int i; float f; U() : i(1) {} };'),
      'What does this print?','2.5',['1','Undefined: i is the active member'],
      'Assigning to a member with a trivial default constructor and trivial assignment begins its lifetime and makes it active. Reading f is then valid.')
drill('manual-union-lifetime','Compiles?','A union with a std::string member',
      main_program('    U u;\n    (void)u;','iostream string','union U { std::string s; int i; };'),
      'Does this compile?','No: the union\'s default constructor is implicitly deleted',
      ['Yes: the string member is constructed first','Yes, but the destructor leaks'],
      'A non-trivial member deletes the union\'s implicit default constructor and destructor; the owner must construct and destroy the active member explicitly.',check='reject',diagnostic='implicitly-deleted')
drill('manual-union-lifetime','Code review','Switching away from a string member',
      '','A tagged union holds an active std::string and the code switches to the int member with u.i = 3; without other steps. What is wrong?',
      'The string is never destroyed, so its heap buffer leaks; call the destructor before switching',
      ['Nothing: assignment destroys the previous member automatically','The int assignment is ill-formed'],
      'Unions do not track the active member. Destroy the old member (s.~basic_string() or std::destroy_at) before starting another member\'s lifetime.',check='reasoning')
drill('custom-deleter','Layout','Deleter state in unique_ptr',
      main_program('    std::cout << sizeof(std::unique_ptr<int, Closer>) << " " << sizeof(std::unique_ptr<int, void (*)(int*)>) << "\\n";','iostream memory',
                   'struct Closer { void operator()(int* p) const { delete p; } };'),
      'On arm64 macOS with libc++, what does this print?','8 16',['8 8','16 16'],
      'An empty deleter is stored with no space overhead, while a function-pointer deleter must store the pointer next to the managed pointer.')
drill('custom-deleter','Predict output','Deleter calls on reset and destruction',
      main_program('    std::unique_ptr<int, Logger> a(new int(1));\n    a.reset(new int(2));\n    std::cout << "|";','iostream memory',
                   'struct Logger { void operator()(int* p) const { std::cout << *p; delete p; } };'),
      'What does this print?','1|2',['|12','2|1'],
      'reset deletes the old pointer immediately; the destructor deletes the second one when a leaves scope at the end of main.')
drill('custom-deleter','Compiles?','shared_ptr erases the deleter type',
      main_program('    std::shared_ptr<int> a(new int(1), Closer{});\n    std::shared_ptr<int> b(new int(2), close_fn);\n    a = b;\n    std::cout << *a << "\\n";','iostream memory',
                   'struct Closer { void operator()(int* p) const { delete p; } };\nvoid close_fn(int* p) { delete p; }'),
      'Does this compile?','Yes: the deleter is stored in the control block, so both are shared_ptr<int>',
      ['No: the deleters have different types','No: shared_ptr cannot take a function pointer deleter'],
      'Unlike unique_ptr, shared_ptr\'s deleter is not part of its type.',check='compiles')
drill('explicit-object23','Predict output','Overloading on the explicit object category',
      main_program('    S s;\n    std::cout << s.get() << std::move(s).get() << "\\n";','iostream utility',
                   'struct S {\n    int get(this const S&) { return 1; }\n    int get(this S&&) { return 2; }\n};'),
      'What does this print?','12',['11','22'],
      'The explicit object parameter participates in overload resolution like an ordinary parameter, so the rvalue selects S&&.')
drill('explicit-object23','Predict output','A recursive lambda through deducing this',
      main_program('    auto fact = [](this auto self, int n) -> int { return n <= 1 ? 1 : n * self(n - 1); };\n    std::cout << fact(5) << "\\n";'),
      'What does this print?','120',['It does not compile: a lambda cannot name itself','24'],
      'The explicit object parameter gives the lambda a name for itself, so recursion needs no std::function.')
drill('explicit-object23','Compiles?','Using this with an explicit object parameter',
      main_program('    S s;\n    std::cout << s.get() << "\\n";','iostream','struct S { int v = 1; int get(this const S& self) { return this->v; } };'),
      'Does this compile?','No: this cannot be used in a function with an explicit object parameter',
      ['Yes, and it prints 1','Yes, but self is ignored'],
      'An explicit object member function has no implicit this; access members through the named parameter.',check='reject',diagnostic="invalid use of 'this'")
drill('forward-like23','Predict output','Value category and constness from forward_like',
      main_program('    int x = 0;\n    std::cout << std::is_rvalue_reference_v<decltype(std::forward_like<int&&>(x))> << std::is_const_v<std::remove_reference_t<decltype(std::forward_like<const int&>(x))>> << "\\n";','iostream type_traits utility'),
      'What does this print?','11',['01','10'],
      'forward_like takes the reference kind and constness from its template argument and applies them to the forwarded object.')
drill('forward-like23','Copies and moves','Forwarding a member from a deduced receiver',
      main_program('    Box b;\n    std::cout << b.take() << " " << std::move(b).take() << "\\n";','iostream string utility',
                   'const char* sink(const std::string&) { return "copy"; }\nconst char* sink(std::string&&) { return "move"; }\nstruct Box {\n    std::string s{"x"};\n    template <class Self> const char* take(this Self&& self) { return sink(std::forward_like<Self>(self.s)); }\n};'),
      'What does this print?','copy move',['move move','copy copy'],
      'For an lvalue receiver Self is Box&, so the member is forwarded as an lvalue; for std::move(b) it is forwarded as an rvalue.')
drill('forward-like23','Concept','Why not std::forward<decltype(self.s)>',
      '','Inside take(this Self&& self), why is std::forward<decltype(self.s)>(self.s) wrong for forwarding the member?',
      'decltype(self.s) is the declared member type, so it ignores whether the receiver was an rvalue',
      ['It is equivalent to forward_like<Self>','It always produces a const reference'],
      'The member should inherit the receiver\'s category; forward_like<Self> encodes that dependency.',check='reasoning')
drill('static-call23','Predict output','A static call operator',
      main_program('    std::cout << Add{}(2, 3) << " " << Add::operator()(4, 5) << "\\n";','iostream','struct Add { static int operator()(int a, int b) { return a + b; } };'),
      'What does this print?','5 9',['5 5','It does not compile: operator() cannot be static'],
      'C++23 allows a static operator(), callable with an object or by qualified name, with no implicit this.')
drill('static-call23','Predict output','A static lambda',
      main_program('    auto f = [](int x) static { return x * 2; };\n    std::cout << f(4) << "\\n";'),
      'What does this print?','8',['4','It does not compile'],
      'A captureless lambda may be declared static, which makes its call operator static.')
drill('static-call23','Compiles?','A static lambda with a capture',
      main_program('    int k = 1;\n    auto f = [k](int x) static { return x + k; };\n    std::cout << f(1) << "\\n";'),
      'Does this compile?','No: a static lambda cannot have captures',['Yes, it prints 2','Yes, k becomes static'],
      'Captures live in the closure object, and a static call operator has no object to read them from.',check='reject',diagnostic='static lambda cannot have any captures')
drill('multi-subscript23','Predict output','A two-index subscript',
      main_program('    Grid g;\n    std::cout << g[1, 2] << "\\n";','iostream','struct Grid {\n    int cols = 3;\n    int data[6]{0, 1, 2, 3, 4, 5};\n    int operator[](int r, int c) const { return data[r * cols + c]; }\n};'),
      'What does this print?','5',['2','3'],
      'C++23 passes both indices to operator[]; row 1, column 2 is element 1 * 3 + 2.')
drill('multi-subscript23','Compiles?','A two-parameter operator[] in C++20',
      main_program('    Grid g;\n    std::cout << g[1, 2] << "\\n";','iostream','struct Grid { int operator[](int r, int c) const { return r + c; } };'),
      'Compiled with -std=c++20, does this compile?','No: operator[] must have exactly one parameter before C++23',
      ['Yes, it prints 3','Yes, but the comma is a deprecated comma operator'],
      'Multi-parameter subscript operators are new in C++23; C++20 only deprecated comma expressions in subscripts.',check='reject',standard=20,diagnostic="cannot have more than one parameter")
drill('multi-subscript23','Predict output','A parenthesized comma in a built-in subscript',
      main_program('    int arr[3]{10, 20, 30};\n    std::cout << arr[(0, 2)] << "\\n";'),
      'What does this print?','30',['10','It does not compile in C++23'],
      'The parentheses make (0, 2) a comma expression whose value is 2. Only an unparenthesized comma is reinterpreted as multiple indices.')
drill('auto-copy23','Predict output','Erasing all copies of the front value',
      main_program('    std::vector<int> v{1, 2, 1, 3};\n    std::erase(v, auto(v.front()));\n    for (int x : v) std::cout << x;\n    std::cout << "\\n";','iostream vector'),
      'What does this print?','23',['213','3'],
      'auto(v.front()) copies the value 1 before erase starts. Passing v.front() directly would bind a reference to an element that the algorithm overwrites.')
drill('auto-copy23','Predict output','The type of auto(x)',
      main_program('    int x = 5;\n    std::cout << std::is_same_v<decltype(auto(x)), int> << std::is_same_v<decltype((x)), int&> << "\\n";','iostream type_traits'),
      'What does this print?','11',['01','10'],
      'auto(x) is a prvalue copy of type int; (x) is an lvalue expression, so decltype gives int&.')
drill('auto-copy23','Compiles?','auto(expr) compiled as C++20',
      main_program('    std::vector<int> v{1, 2, 1};\n    std::erase(v, auto(v.front()));\n    std::cout << v.size() << "\\n";','iostream vector'),
      'Compiled with -std=c++20, does this compile?','No: auto as a functional cast is C++23',
      ['Yes, it prints 1','Yes, but it erases nothing'],
      'Clang rejects auto(expression) before C++23; write a named copy instead.',check='reject',standard=20,diagnostic="'auto' not allowed here")


# Drills: new stage-09 lessons
def argc_main(body, headers='iostream', declarations=''):
    """A program whose runtime values depend on argc, so the optimizer cannot fold them."""
    return main_program(body, headers, declarations).replace('int main() {', 'int main(int argc, char**) {')


drill('strict-aliasing-rule','Undefined behavior','Reading a float through an int pointer',
      '','float f = 1.0f; std::uint32_t u = *reinterpret_cast<std::uint32_t*>(&f); Which statement is correct?',
      'The read is undefined behavior; copy with std::memcpy or std::bit_cast instead',
      ['It is well defined because the sizes match','It is implementation-defined and prints 0x3f800000 everywhere'],
      'The aliasing rule permits access through the object\'s own type, char, unsigned char and std::byte, not an unrelated integer type. UBSan does not check this, so tests can pass while optimized code misbehaves.',check='reasoning')
drill('strict-aliasing-rule','Predict output','The bits of negative zero',
      main_program('    float f = -0.0f;\n    std::uint32_t u;\n    std::memcpy(&u, &f, sizeof u);\n    std::cout << std::hex << u << "\\n";','cstdint cstring iostream'),
      'What does this print?','80000000',['0','ffffffff'],
      'IEEE 754 negative zero has only the sign bit set, so the copied representation is 0x80000000.')
drill('strict-aliasing-rule','Predict output','Inspecting bytes through unsigned char',
      main_program('    std::uint32_t v = 0x01020304;\n    const unsigned char* bytes = reinterpret_cast<const unsigned char*>(&v);\n    std::cout << static_cast<int>(bytes[0]) << "\\n";','cstdint iostream'),
      'On little-endian arm64, what does this print?','4',['1','It is undefined behavior'],
      'unsigned char may alias any object, and a little-endian target stores the least significant byte first.')
drill('strict-aliasing-rule','Predict output','bit_cast and the exponent field',
      main_program('    std::cout << (std::bit_cast<std::uint32_t>(1.0f) >> 23) << "\\n";','bit cstdint iostream'),
      'What does this print?','127',['1','0'],
      'For 1.0f the sign is 0, the biased exponent is 127 and the fraction is 0, so shifting out the 23 fraction bits leaves 127.',standard=20)
drill('signed-overflow-assumptions','Undefined behavior','An overflow check written after the overflow',
      argc_main('    int x = std::numeric_limits<int>::max() - argc + 1;\n    if (x + 1 < x) std::cout << "overflow\\n";\n    else std::cout << "fine\\n";','iostream limits'),
      'Run with no arguments under UBSan. What happens?','UBSan reports signed integer overflow at x + 1',
      ['It prints overflow because the value wraps','It prints fine and nothing is reported'],
      'x is INT_MAX at run time, so x + 1 overflows. The check is useless: an optimizer may fold x + 1 < x to false.',check='ubsan')
drill('signed-overflow-assumptions','Code review','Which check can the optimizer delete',
      '','bool f(int x) { if (x + 100 < x) return false; return true; } At -O2, what may clang do with the if?',
      'Remove it, because for valid programs x + 100 < x is always false',
      ['Keep it, because overflow checks are never optimized','Turn it into an exception'],
      'Assuming no signed overflow, the comparison has a constant result. Check x > INT_MAX - 100 before adding.',check='reasoning')
drill('signed-overflow-assumptions','Predict output','Unsigned decrement below zero',
      main_program('    unsigned u = 0;\n    --u;\n    std::cout << (u == std::numeric_limits<unsigned>::max()) << "\\n";','iostream limits'),
      'What does this print?','1',['0','It is undefined behavior'],
      'Unsigned arithmetic is defined modulo 2^N, so 0 - 1 wraps to the maximum value.')
drill('signed-overflow-assumptions','Undefined behavior','Negating INT_MIN',
      argc_main('    int a = std::numeric_limits<int>::min() + argc - 1;\n    a = -a;\n    std::cout << a << "\\n";','iostream limits'),
      'Run with no arguments under UBSan. What happens?','UBSan reports that negating INT_MIN cannot be represented',
      ['It prints 2147483648','It prints INT_MIN and the result is well defined'],
      'Two\'s complement int has no positive counterpart of INT_MIN, so the negation overflows. std::abs(INT_MIN) has the same problem.',check='ubsan')
drill('uninitialized-reads','Predict output','Partial aggregate initialization',
      main_program('    int a[5]{7};\n    int sum = 0;\n    for (int v : a) sum += v;\n    std::cout << sum << "\\n";'),
      'What does this print?','7',['35','Undefined: four elements are uninitialized'],
      'Elements without an initializer in a braced aggregate initialization are value-initialized to zero.')
drill('uninitialized-reads','Predict output','Value-initialization of an aggregate and a vector',
      main_program('    P p{};\n    std::vector<int> v(3);\n    std::cout << p.x << " " << v[0] + v[1] + v[2] << "\\n";','iostream vector','struct P { int x; };'),
      'What does this print?','0 0',['Undefined: p.x is indeterminate','0 3'],
      'P{} value-initializes and zeroes x, and vector(3) value-initializes three ints.')
drill('uninitialized-reads','Undefined behavior','Testing an uninitialized local',
      '','int total; if (debug) total = 0; total += 5; A test in a debug build prints 5. What does that prove?',
      'Nothing: reading the indeterminate total when debug is false is undefined (erroneous in C++26)',
      ['The code is correct because the debug build printed 5','Locals are zero-initialized in debug builds by the standard'],
      'A lucky value is not a guarantee. Initialize at declaration; MemorySanitizer is not available on Apple platforms, so rely on warnings and hardening too.',check='reasoning')
drill('sanitizer-workflow','Undefined behavior','Reading one past a vector\'s storage',
      main_program('    std::vector<int> v(3);\n    int* p = v.data();\n    std::cout << p[3] << "\\n";','iostream vector'),
      'Run under AddressSanitizer. What happens?','ASan reports a heap-buffer-overflow read',
      ['It prints 0','ThreadSanitizer is needed to see this'],
      'The vector allocated exactly three ints; reading the fourth is outside the heap block.',check='asan')
drill('sanitizer-workflow','Undefined behavior','Using memory after delete',
      main_program('    int* p = new int(1);\n    delete p;\n    std::cout << *p << "\\n";'),
      'Run under AddressSanitizer. What happens?','ASan reports a heap-use-after-free',
      ['It prints 1, which proves the read is safe','UBSan reports it; ASan does not'],
      'ASan quarantines freed blocks and poisons them, so the stale read is caught.',check='asan')
drill('sanitizer-workflow','Undefined behavior','Shifting by the full width',
      argc_main('    int s = 31 + argc;\n    int v = 1 << s;\n    std::cout << v << "\\n";'),
      'Run with no arguments under UBSan. What happens?','UBSan reports that the shift exponent 32 is too large for int',
      ['It prints 0','It prints 1'],
      'Shifting by at least the bit width is undefined. Hardware may mask the count, so silent results vary.',check='ubsan')
drill('sanitizer-workflow','Concurrency','An unsynchronized counter',
      main_program('    int counter = 0;\n    std::thread a([&] { for (int i = 0; i < 1000; ++i) ++counter; });\n    std::thread b([&] { for (int i = 0; i < 1000; ++i) ++counter; });\n    a.join();\n    b.join();\n    std::cout << counter << "\\n";','iostream thread'),
      'Run under ThreadSanitizer. What happens?','TSan reports a data race on counter',
      ['It always prints 2000, so there is no bug','ASan is the right tool for this'],
      'Two threads modify the same non-atomic int without synchronization; that is a data race and undefined behavior even if the total looks right.',check='tsan')
drill('removed-features-migration','Compiles?','auto_ptr in C++17',
      main_program('    std::auto_ptr<int> p(new int(1));\n    std::cout << *p << "\\n";','iostream memory'),
      'With libc++ and -std=c++17, does this compile?','No: std::auto_ptr was removed in C++17',
      ['Yes, with a deprecation warning','Yes: auto_ptr is an alias of unique_ptr'],
      'auto_ptr was deprecated in C++11 and removed in C++17. Use std::unique_ptr with explicit std::move.',check='reject',diagnostic="no member named 'auto_ptr'")
drill('removed-features-migration','Compiles?','The register keyword in C++17',
      main_program('    register int x = 1;\n    std::cout << x << "\\n";'),
      'With -std=c++17, does this compile?','No: register is no longer a storage class specifier',
      ['Yes; register is an ignored hint','Yes, but x cannot have its address taken'],
      'C++17 removed the register storage class and kept the keyword reserved. Clang treats the use as an error.',check='reject',diagnostic="does not allow 'register'")
drill('removed-features-migration','Compiles?','A dynamic exception specification',
      main_program('    std::cout << "ok\\n";','iostream','void parse() throw(int);'),
      'With -std=c++17, does this compile?','No: dynamic exception specifications were removed in C++17',
      ['Yes, it limits parse to throwing int','Yes, with a warning only'],
      'Use noexcept or no specification. Only throw() survived C++17, as a deprecated synonym for noexcept, and C++20 removed it too.',check='reject',diagnostic='does not allow dynamic exception specifications')
drill('removed-features-migration','Predict output','throw() in C++17',
      main_program('    std::cout << noexcept(g()) << "\\n";','iostream','void g() throw() {}'),
      'With -std=c++17, what does this print?','1',['0','It does not compile in C++17'],
      'In C++17 throw() is a deprecated spelling of noexcept(true). It was removed in C++20.')
drill('removed-features-migration','Compiles?','random_shuffle in C++17',
      main_program('    std::vector<int> v{1, 2, 3};\n    std::random_shuffle(v.begin(), v.end());\n    std::cout << v.size() << "\\n";','algorithm iostream vector'),
      'With libc++ and -std=c++17, does this compile?','No: std::random_shuffle was removed in C++17',
      ['Yes, it prints 3','Yes, but it uses std::rand'],
      'Use std::shuffle with an explicit generator such as std::mt19937.',check='reject',diagnostic="no member named 'random_shuffle'")
drill('removed-features-migration','Predict output','A trigraph after C++17',
      main_program('    std::cout << "what??!" << "\\n";'),
      'With -std=c++17, what does this print?','what??!',['what|','It does not compile'],
      'Trigraphs were removed in C++17, so ??! stays three characters. Clang warns that the trigraph is ignored.')
drill('removed-features-migration','Predict output','The same trigraph in C++14',
      main_program('    std::cout << "what??!" << "\\n";'),
      'With -std=c++14 (ISO mode), what does this print?','what|',['what??!','It does not compile'],
      'Before C++17, ??! is a trigraph for | and is replaced in the first translation phase, even inside string literals.',standard=14)
drill('deprecated-cpp20-features','Compiles?','Implicit this capture in C++20',
      main_program('    std::cout << W{}.f()() << "\\n";','iostream','struct W { int v = 3; auto f() { return [=] { return v; }; } };'),
      'With -std=c++20, does this compile?','Yes, with a deprecation warning; write [=, this] or [*this]',
      ['No: implicit this capture was removed in C++20','Yes, and [=] copies the whole object'],
      'C++20 deprecated, but did not remove, implicit capture of this via [=]. The lambda still captures the pointer.',check='compiles')
drill('deprecated-cpp20-features','Predict output','Compound assignment on volatile',
      main_program('    volatile int v = 1;\n    v += 1;\n    std::cout << v << "\\n";'),
      'With -std=c++20, what does this print?','2',['1','It does not compile'],
      'Compound assignment to a volatile int is deprecated in C++20 and warns, but still performs a read and a write.')
drill('deprecated-cpp20-features','Compiles?','aligned_storage in C++23',
      main_program('    std::aligned_storage_t<sizeof(double), alignof(double)> raw;\n    std::cout << sizeof(raw) << "\\n";','iostream type_traits'),
      'With libc++ and -std=c++23, does this compile?','Yes, with a deprecation warning; prefer alignas(T) std::byte[sizeof(T)]',
      ['No: aligned_storage was removed in C++23','Yes, and it is the recommended C++23 form'],
      'C++23 deprecated std::aligned_storage and std::aligned_union; deprecated facilities remain available.',check='compiles',standard=23)
drill('deprecated-cpp20-features','Predict output','A std::iterator base in C++17',
      main_program('    std::cout << std::is_same_v<std::iterator_traits<It>::value_type, int> << "\\n";','iostream iterator type_traits',
                   'struct It : std::iterator<std::forward_iterator_tag, int> {};'),
      'With -std=c++17, what does this print?','1',['0','It does not compile: std::iterator was removed in C++17'],
      'std::iterator is deprecated in C++17 but still provides the member types. Declare value_type and the others directly instead.',standard=17)
drill('named-requirements-hash','Code review','A hash that ignores a field',
      '','Point equality compares x and y, but the hash uses only x. Is the hash valid?',
      'Valid: equal points still hash equally, but points sharing x collide',
      ['Invalid: every field used by equality must be hashed','Invalid: the container will store duplicates'],
      'The requirement is one-directional: a == b implies h(a) == h(b). Ignoring a field costs performance, not correctness.',check='reasoning')
drill('named-requirements-hash','Code review','A hash that uses an ignored field',
      '','Equality on Name ignores case, but the hash hashes the exact characters. What breaks?',
      'Equal keys such as "Ann" and "ann" can hash differently, so lookups and duplicate detection fail',
      ['Nothing: equality decides membership on its own','Only iteration order changes'],
      'Unordered containers only compare keys within one bucket. The hash must be computed from the same normalized key that equality uses.',check='reasoning')
drill('named-requirements-hash','Predict output','Iterator categories of standard containers',
      main_program('    std::cout << std::is_same_v<std::iterator_traits<std::list<int>::iterator>::iterator_category, std::bidirectional_iterator_tag> << std::is_same_v<std::iterator_traits<std::forward_list<int>::iterator>::iterator_category, std::forward_iterator_tag> << "\\n";','forward_list iostream iterator list type_traits'),
      'What does this print?','11',['01','10'],
      'list iterators meet the bidirectional iterator requirements and forward_list iterators the forward iterator requirements.')
drill('named-requirements-hash','Compiles?','An unordered_set of a type without a hash',
      main_program('    std::unordered_set<Point> s;\n    s.insert({1, 2});\n    std::cout << s.size() << "\\n";','iostream unordered_set',
                   'struct Point { int x, y; bool operator==(const Point& o) const { return x == o.x && y == o.y; } };'),
      'Does this compile?','No: std::hash<Point> is not provided, so the Hash requirement is not met',
      ['Yes: the container hashes the object bytes','Yes, but every element lands in one bucket'],
      'The primary std::hash template is disabled for user types. Provide a hasher or specialize std::hash<Point>.',check='reject',diagnostic='Hash requirements')
drill('allocator-propagation-traits','Predict output','Copy assignment keeps the destination resource',
      main_program('    std::pmr::monotonic_buffer_resource r1, r2;\n    std::pmr::vector<int> a({1, 2}, &r1);\n    std::pmr::vector<int> b(&r2);\n    b = a;\n    std::cout << (b.get_allocator().resource() == &r2) << "\\n";','iostream memory_resource vector'),
      'What does this print?','1',['0','It does not compile: allocators differ'],
      'polymorphic_allocator does not propagate on copy assignment, so b copies the elements into memory from r2.')
drill('allocator-propagation-traits','Predict output','Copy construction selects the default resource',
      main_program('    std::pmr::monotonic_buffer_resource r1;\n    std::pmr::vector<int> a({1, 2}, &r1);\n    std::pmr::vector<int> c(a);\n    std::cout << (c.get_allocator().resource() == std::pmr::get_default_resource()) << "\\n";','iostream memory_resource vector'),
      'What does this print?','1',['0, because c copies a\'s resource','It does not compile'],
      'Copy construction uses select_on_container_copy_construction, which for polymorphic_allocator returns a default-constructed allocator using the default resource.')
drill('allocator-propagation-traits','Undefined behavior','Swapping containers with unequal allocators',
      '','Two std::pmr::vector<int> objects use different monotonic resources. What does a.swap(b) do?',
      'Undefined behavior: propagate_on_container_swap is false and the allocators are unequal',
      ['It swaps the buffers and the resources','It copies elements across, like assignment'],
      'Swap is constant time and cannot move elements, so the standard makes equal allocators a precondition when they do not propagate.',check='reasoning')
drill('noexcept-operator','Predict output','Querying exception specifications',
      main_program('    std::cout << noexcept(f()) << noexcept(g()) << noexcept(1 + 1) << "\\n";','iostream','void f();\nvoid g() noexcept;'),
      'What does this print?','011',['010','000'],
      'noexcept does not evaluate its operand. f may throw, g is declared noexcept, and built-in arithmetic cannot throw.')
drill('noexcept-operator','Copies and moves','Growth with a throwing move constructor',
      main_program('    std::vector<M> v;\n    v.reserve(1);\n    v.emplace_back();\n    v.emplace_back();\n    std::cout << "\\n";','iostream vector',
                   'struct M {\n    M() = default;\n    M(const M&) { std::cout << "c"; }\n    M(M&&) { std::cout << "m"; }\n};'),
      'What does this print?','c',['m','cm'],
      'Reallocation uses move_if_noexcept. Because the move constructor may throw and a copy constructor exists, the existing element is copied to keep the strong guarantee.')
drill('noexcept-operator','Predict output','An exception escaping noexcept',
      main_program('    std::set_terminate([] { std::cout << "terminate" << std::endl; std::_Exit(0); });\n    try { f(); } catch (...) { std::cout << "caught\\n"; }','cstdlib exception iostream','void f() noexcept { throw 1; }'),
      'What does this print?','terminate',['caught','Nothing; the exception is ignored'],
      'The noexcept boundary calls std::terminate; the catch block in main is never reached.')
drill('noexcept-operator','Predict output','A conditional noexcept',
      main_program('    std::cout << noexcept(h<char>()) << noexcept(h<double>()) << "\\n";','iostream','template <class T> void h() noexcept(sizeof(T) > 4) {}'),
      'What does this print?','01',['10','11'],
      'noexcept(expr) takes a constant expression. sizeof(char) is 1 and sizeof(double) is 8.')
drill('static-init-order','Predict output','Initialization on first use',
      main_program('    get();\n    get();\n    std::cout << "done\\n";','iostream','struct Widget { Widget() { std::cout << "init "; } };\nWidget& get() { static Widget w; return w; }'),
      'What does this print?','init done',['init init done','done'],
      'A function-local static is initialized once, the first time control passes through its declaration.')
drill('static-init-order','Predict output','Destruction order of local statics',
      main_program('    b();\n    a();\n    std::cout << "-";','iostream','struct Tag { char c; ~Tag() { std::cout << c; } };\nTag& a() { static Tag t{\'a\'}; return t; }\nTag& b() { static Tag t{\'b\'}; return t; }'),
      'What does this print?','-ab',['-ba','ab-'],
      'Static objects are destroyed after main returns, in reverse order of completed construction: a was constructed last, so it is destroyed first.')
drill('static-init-order','Undefined behavior','A global reading a later global',
      '','In one file: int read_a(); int b = read_a() + 1; int a = forty_one(); int read_a() { return a; } where forty_one() is a non-constexpr function returning 41. What values can b have?',
      '1 or 42: a is zero-initialized first, but the implementation may initialize a statically',
      ['Always 42','Always 1'],
      'Dynamic initialization follows declaration order, so a is still zero when b is initialized, unless the implementation uses its permission to perform a\'s initialization statically.',check='reasoning')
drill('static-init-order','Compiles?','constinit with a dynamic initializer',
      main_program('    std::cout << x << "\\n";','iostream','int f() { return 1; }\nconstinit int x = f();'),
      'With -std=c++20, does this compile?','No: constinit requires a constant initializer',
      ['Yes, x is initialized at start-up','Yes, but only in a single translation unit'],
      'constinit asserts static initialization. A call to a non-constexpr function makes the initializer dynamic.',check='reject',standard=20,diagnostic='does not have a constant initializer')
drill('inline-namespace-abi','Predict output','A type through an inline namespace',
      main_program('    std::cout << std::is_same<lib::Widget, lib::v2::Widget>::value << "\\n";','iostream type_traits','namespace lib { inline namespace v2 { struct Widget {}; } }'),
      'What does this print?','1',['0','It does not compile: Widget is not in lib'],
      'Members of an inline namespace are members of the enclosing namespace for lookup, so both names denote the same type.')
drill('inline-namespace-abi','Compiles?','Two inline versions of one function',
      main_program('    std::cout << lib::f() << "\\n";','iostream','namespace lib {\ninline namespace v1 { int f() { return 1; } }\ninline namespace v2 { int f() { return 2; } }\n}'),
      'Does this compile?','No: lib::f is ambiguous',['Yes, it prints 2','Yes, it prints 1'],
      'Both inline namespaces contribute f to lib, so only one version may be inline at a time.',check='reject',diagnostic="call to 'f' is ambiguous")
drill('inline-namespace-abi','Concept','Linking against a different library version',
      '','A plugin compiled against lib::v1 (inline) links into a program built with lib::v2 inline. The plugin calls lib::parse. What happens?',
      'The plugin references lib::v1::parse, so it fails to link unless v1 is still provided',
      ['It silently calls lib::v2::parse','The linker merges the two versions'],
      'The inline namespace is part of the mangled name, which turns layout mismatches into link errors.',check='reasoning')
drill('feature-test-macros','Predict output','__cplusplus in C++17 mode',
      main_program('    std::cout << __cplusplus << "\\n";'),
      'With -std=c++17, what does this print?','201703',['201402','17'],
      '__cplusplus is a date-like value: 201703L for C++17.')
drill('feature-test-macros','Compiles?','__has_include in an expression',
      main_program('    std::cout << __has_include(<optional>) << __has_include(<no_such_header_xyz>) << "\\n";'),
      'Does this compile?','No: __has_include may only appear in #if and #elif conditions',['Yes, it prints 10','Yes, it prints 11'],
      '__has_include is a preprocessor operator, not an expression usable in ordinary code. Test it in a directive and define a constant from the result.',
      check='reject',diagnostic='must be used within a preprocessing directive')
drill('feature-test-macros','Predict output','__has_include in a directive',
      main_program('#if __has_include(<optional>)\n    std::cout << 1;\n#else\n    std::cout << 0;\n#endif\n#if __has_include(<no_such_header_xyz>)\n    std::cout << 1 << "\\n";\n#else\n    std::cout << 0 << "\\n";\n#endif'),
      'With -std=c++17, what does this print?','10',['11','00'],
      '__has_include reports whether a header can be found. It says nothing about whether the facility inside is enabled in the current mode.')
drill('feature-test-macros','Predict output','A language feature macro in C++17',
      main_program('#ifdef __cpp_concepts\n    std::cout << (__cpp_concepts >= 201907L) << "\\n";\n#else\n    std::cout << 0 << "\\n";\n#endif'),
      'With -std=c++17, what does this print?','0',['1','It does not compile'],
      'The compiler defines __cpp_concepts only in modes that support concepts, so the C++17 build takes the fallback.')


# Drills: stage-11 performance lessons (layout answers assume arm64 LP64 macOS, Apple clang, libc++)
COUNTING_NEW = ('static std::size_t allocations = 0;\n'
                'void* operator new(std::size_t size) {\n    ++allocations;\n    if (void* p = std::malloc(size ? size : 1)) return p;\n    throw std::bad_alloc{};\n}\n'
                'void operator delete(void* p) noexcept { std::free(p); }\n'
                'void operator delete(void* p, std::size_t) noexcept { std::free(p); }')
drill('cache-line-locality','Complexity','Row versus column traversal',
      '','A 4096 x 4096 int matrix is stored row-major in one vector. Loop A sums with the column index innermost; loop B with the row index innermost. Which tends to be faster on arm64 macOS?',
      'Loop A: it reads consecutive addresses and uses every fetched cache line fully',
      ['Loop B: column order lets the hardware vectorize better','They perform the same because both are O(n^2)'],
      'Both do the same arithmetic. Loop B strides 16 KiB per access, touching a new line (and often a new page) each time. Measure to confirm on the target.',check='reasoning')
drill('cache-line-locality','Concurrency','False sharing between counters',
      '','Two threads each increment their own std::atomic<long> in struct { std::atomic<long> a; std::atomic<long> b; }. Why can this scale badly, and what is the fix?',
      'Both counters share a cache line that bounces between cores; align each to its own line (128 bytes on Apple silicon)',
      ['Atomics always serialize all threads, so nothing helps','The counters must be made non-atomic'],
      'Coherence works per line, so independent writes to the same line contend. alignas with the destructive interference size (or 128 on Apple silicon, 64 on most x86) separates them.',check='reasoning')
drill('cache-line-locality','Layout','A cache-line aligned slot',
      main_program('    std::cout << sizeof(Padded) << " " << alignof(Padded) << "\\n";','atomic iostream','struct alignas(64) Padded { std::atomic<int> value; };'),
      'What does this print?','64 64',['4 64','64 4'],
      'alignas(64) raises the alignment, and sizeof is rounded up to a multiple of it so adjacent array elements never share a 64-byte line.')
drill('aos-vs-soa','Layout','Field order and padding',
      main_program('    std::cout << sizeof(Loose) << " " << sizeof(Tight) << "\\n";','iostream',
                   'struct Loose { char flag; double value; char tag; };\nstruct Tight { double value; char flag; char tag; };'),
      'On arm64 macOS, what does this print?','24 16',['10 10','16 16'],
      'In Loose each char is followed by padding to keep value and the whole struct 8-byte aligned. Grouping the small fields leaves one 6-byte tail pad.')
drill('aos-vs-soa','Complexity','Bytes read by a single-field scan',
      '','A loop sums price over 1,000,000 orders. Each AoS Order is 64 bytes; the SoA form stores prices in a separate std::vector<double>. Roughly how much memory does each scan stream?',
      'About 64 MB for AoS versus 8 MB for SoA',
      ['8 MB for both, because only price is read','64 MB for both, because cache lines are fixed'],
      'In AoS each price drags its whole 64-byte record into the cache. The SoA array is contiguous 8-byte values.',check='reasoning')
drill('aos-vs-soa','Code review','When AoS is the better choice',
      '','An order book mostly inserts, deletes and reads whole orders by id. A reviewer proposes converting it to SoA. What is the main concern?',
      'Whole-record operations would touch several arrays and keep them in sync, so AoS likely suits this access pattern better',
      ['SoA cannot store integers','SoA always wins, so there is no concern'],
      'SoA helps field-wise scans. When access is record-at-a-time, contiguous records keep each operation on fewer cache lines.',check='reasoning')
drill('branch-likelihood','Predict output','Attributes do not change results',
      main_program('    int odd = 0;\n    for (int v = 0; v < 10; ++v) {\n        if (v % 2) [[likely]] ++odd;\n        else [[unlikely]] --odd;\n    }\n    std::cout << odd << "\\n";'),
      'What does this print?','0',['5','10'],
      'Five odd values increment and five even values decrement. Likelihood attributes, even wrong ones, never change the computed result.')
drill('branch-likelihood','Complexity','Sorted versus random input',
      '','The same loop sums elements with if (x >= 128) over 1,000,000 random bytes, once unsorted and once after sorting. Which tends to run faster on modern CPUs (excluding sort time)?',
      'The sorted input, because the branch becomes highly predictable',
      ['The unsorted input, because sorting adds cache misses','Neither: the work is identical'],
      'After sorting, the branch is false for a long run and then true; the predictor learns it. Compilers may also emit a branchless select, which removes the difference, so measure.',check='reasoning')
drill('branch-likelihood','Compiles?','[[likely]] on a case label',
      main_program('    int x = 1;\n    switch (x) {\n    [[likely]] case 1: std::cout << "one\\n"; break;\n    default: std::cout << "other\\n";\n    }'),
      'With -std=c++20, does this compile?','Yes: likelihood attributes may appertain to labels and statements',
      ['No: [[likely]] only applies to if statements','No: attributes cannot precede case'],
      'The C++20 attributes apply to a statement or label; case labels are a common use in hot dispatch switches.',check='compiles')
drill('final-devirtualization','Compiles?','Deriving from a final class',
      main_program('','iostream','struct Square final {};\nstruct Big : Square {};'),
      'Does this compile?','No: Square is marked final',['Yes, final only affects virtual functions','Yes, with a warning'],
      'A final class cannot be used as a base class. That restriction is what lets the compiler know no override exists.',check='reject',standard=17,diagnostic="marked 'final'")
drill('final-devirtualization','Compiles?','Overriding a final member',
      main_program('','iostream','struct A { virtual ~A() = default; virtual int area() const final { return 1; } };\nstruct B : A { int area() const override { return 2; } };'),
      'Does this compile?','No: B::area overrides a final function',['Yes: override wins over final','Yes, but the call always uses A::area'],
      'A virtual function marked final cannot be overridden in any derived class.',check='reject',standard=17,diagnostic="overrides a 'final' function")
drill('final-devirtualization','Predict output','Virtual calls during construction',
      main_program('    Derived d;\n    std::cout << " " << d.name() << "\\n";','iostream',
                   'struct Base {\n    Base() { std::cout << name(); }\n    virtual ~Base() = default;\n    virtual const char* name() const { return "Base"; }\n};\nstruct Derived final : Base { const char* name() const override { return "Derived"; } };'),
      'What does this print?','Base Derived',['Derived Derived','Base Base'],
      'While the Base constructor runs, the object\'s dynamic type is Base, so the virtual call resolves to Base::name.')
drill('small-string-capacity','Layout','Default std::string capacity on libc++',
      main_program('    std::string s;\n    std::cout << s.capacity() << " " << sizeof(s) << "\\n";','iostream string'),
      'With libc++ on arm64 macOS, what does this print?','22 24',['15 32','0 24'],
      'libc++ keeps up to 22 characters inline in a 24-byte object. libstdc++ would print 15 32; the standard fixes neither.')
drill('small-string-capacity','Copies and moves','Counting allocations of short and long strings',
      main_program('    allocations = 0;\n    std::string a("short");\n    const std::size_t short_count = allocations;\n    std::string b(40, \'x\');\n    std::cout << short_count << " " << allocations - short_count << "\\n";','cstdlib iostream new string',COUNTING_NEW),
      'With libc++, what does this print?','0 1',['1 1','0 0'],
      'Five characters fit in the inline buffer; forty characters require one heap allocation.')
drill('small-string-capacity','Undefined behavior','A view into a moved-from short string',
      '','std::string a = "hi"; std::string_view v = a; std::string b = std::move(a); std::cout << v; What is the problem?',
      'v still points into a\'s inline buffer, whose contents the move may have changed; the view no longer refers to b\'s characters',
      ['None: the move transfers the characters and v follows them','It is fine for short strings and only fails for long ones'],
      'For short strings the characters are copied and a is left valid but unspecified; for long strings the heap buffer moves to b. A view must not outlive or ignore modifications of its source either way.',check='reasoning')
drill('monotonic-arena','Predict output','Exhausting a buffer with a null upstream',
      main_program('    alignas(16) std::byte buffer[16];\n    std::pmr::monotonic_buffer_resource arena{buffer, sizeof buffer, std::pmr::null_memory_resource()};\n    void* first = arena.allocate(8, 8);\n    bool threw = false;\n    try { arena.allocate(16, 8); } catch (const std::bad_alloc&) { threw = true; }\n    std::cout << (first != nullptr) << threw << "\\n";','cstddef iostream memory_resource new'),
      'What does this print?','11',['10','01'],
      'The first eight bytes come from the buffer. Sixteen more do not fit, and the null upstream resource throws bad_alloc instead of reaching the heap.')
drill('monotonic-arena','Complexity','Vector growth inside an arena',
      '','A std::pmr::vector<int> grows one push_back at a time to 1,000,000 elements inside a monotonic_buffer_resource. Roughly how much arena memory is consumed?',
      'About twice the final buffer, because every abandoned smaller buffer stays allocated',
      ['Exactly the final buffer size, because deallocate returns old blocks','About log n bytes'],
      'Geometric growth abandons blocks whose sizes sum to roughly the final capacity, and the monotonic resource never reuses them. Reserve first.',check='reasoning')
drill('monotonic-arena','Predict output','Nested pmr strings use the same arena',
      main_program('    std::pmr::monotonic_buffer_resource arena;\n    std::pmr::vector<std::pmr::string> v{&arena};\n    v.emplace_back("a string long enough to need a heap block");\n    std::cout << (v[0].get_allocator().resource() == &arena) << "\\n";','iostream memory_resource string vector'),
      'What does this print?','1',['0','It does not compile'],
      'pmr containers use uses-allocator construction, so the element string receives the vector\'s resource.')
drill('benchmark-pitfalls','Predict output','Is steady_clock steady',
      main_program('    std::cout << std::chrono::steady_clock::is_steady << "\\n";','chrono iostream'),
      'What does this print?','1',['0','It depends on NTP'],
      'steady_clock is required to be monotonic. system_clock follows the wall clock and may jump backwards.')
drill('benchmark-pitfalls','Predict output','duration_cast truncates',
      main_program('    std::cout << std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::nanoseconds(1999)).count() << "\\n";','chrono iostream'),
      'What does this print?','1',['2','1999'],
      'duration_cast truncates toward zero. Use std::chrono::round or keep nanoseconds when reporting short intervals.')
drill('benchmark-pitfalls','Code review','The first sample is the slowest',
      '','A benchmark reports the time of a single run that includes the first call to a function on freshly allocated data. What is wrong?',
      'It includes page faults and cold caches and predictors; add warmup and report a distribution over many samples',
      ['Nothing; the first run is the most realistic','It must use system_clock for a single run'],
      'Cold-start effects dominate one sample. Separate warmup from measurement and report median and spread.',check='reasoning')
drill('benchmark-pitfalls','Code review','Benchmarking a debug build',
      '','A team compares two hash maps using a -O0 build with AddressSanitizer enabled. What is the problem with the conclusion?',
      'Instrumentation and missing optimization change the relative costs, so the result may not hold for the release build',
      ['None: relative rankings never change between builds','ASan makes every operation cost the same'],
      'Benchmark the build configuration you ship. Sanitizers add shadow-memory checks to every access.',check='reasoning')
drill('branchless-select','Predict output','Branchless absolute value',
      main_program('    int x = -5;\n    int mask = x >> 31;\n    std::cout << ((x ^ mask) - mask) << "\\n";'),
      'With -std=c++20, what does this print?','5',['-5','4'],
      'C++20 defines >> on negative values as arithmetic, so mask is -1 (all ones). x ^ -1 is ~x = 4, and 4 - (-1) is 5.',standard=20)
drill('branchless-select','Predict output','Branchless minimum',
      main_program('    int a = 7, b = 3;\n    int m = b ^ ((a ^ b) & -static_cast<int>(a < b));\n    std::cout << m << "\\n";'),
      'What does this print?','3',['7','0'],
      'a < b is false, so the mask is 0 and the expression is b ^ 0. When a < b is true the mask is all ones and b ^ a ^ b gives a.')
drill('branchless-select','Undefined behavior','Branchless abs of INT_MIN',
      argc_main('    int x = std::numeric_limits<int>::min() + argc - 1;\n    int mask = x >> 31;\n    std::cout << ((x ^ mask) - mask) << "\\n";','iostream limits'),
      'Run with no arguments under UBSan (-std=c++20). What happens?','UBSan reports signed overflow in the subtraction',
      ['It prints 2147483648','It prints INT_MIN and is well defined'],
      'x ^ mask is INT_MAX, and INT_MAX - (-1) overflows. Branchless tricks keep the same range preconditions as std::abs.',check='ubsan',standard=20)
drill('pow2-mask-popcount','Predict output','Bit counting functions',
      main_program('    std::cout << std::popcount(255u) << " " << std::bit_width(255u) << " " << std::countl_zero(1u) << "\\n";','bit iostream'),
      'With a 32-bit unsigned, what does this print?','8 8 31',['8 7 31','8 8 0'],
      '255 has eight set bits and needs eight bits to represent; 1 has 31 leading zero bits in a 32-bit unsigned.')
drill('pow2-mask-popcount','Predict output','Signed modulo versus mask',
      main_program('    int i = -3;\n    std::cout << (i % 8) << " " << (i & 7) << "\\n";'),
      'What does this print?','-3 5',['5 5','-3 -3'],
      'C++ integer division truncates toward zero, so -3 % 8 is -3. In two\'s complement -3 is ...11111101, and masking keeps 101.')
drill('pow2-mask-popcount','Predict output','Rounding up to a power of two',
      main_program('    std::cout << std::bit_ceil(17u) << " " << std::has_single_bit(64u) << "\\n";','bit iostream'),
      'What does this print?','32 1',['16 1','32 0'],
      'bit_ceil returns the smallest power of two not less than its argument; 64 has exactly one set bit.')
drill('pow2-mask-popcount','Predict output','Clearing the lowest set bit',
      main_program('    unsigned x = 44;\n    int n = 0;\n    while (x) { x &= x - 1; ++n; }\n    std::cout << n << "\\n";'),
      'What does this print?','3',['6','44'],
      'x & (x - 1) clears the lowest set bit, so the loop runs once per set bit; 44 is 0b101100.')
drill('memory-order-cost','Concurrency','A relaxed flag publishing data',
      main_program('    std::atomic<bool> ready{false};\n    int payload = 0;\n    std::thread t([&] { payload = 42; ready.store(true, std::memory_order_relaxed); });\n    while (!ready.load(std::memory_order_relaxed)) {}\n    std::cout << payload << "\\n";\n    t.join();','atomic iostream thread'),
      'Run under ThreadSanitizer. What happens?','TSan reports a data race on payload',
      ['It always prints 42, so the code is correct','TSan cannot see races involving atomics'],
      'Relaxed operations create no happens-before edge, so the write and read of payload race. Use release on the store and acquire on the load.',check='tsan')
drill('memory-order-cost','Concurrency','Relaxed counters still count',
      main_program('    std::atomic<int> hits{0};\n    std::vector<std::thread> threads;\n    for (int t = 0; t < 4; ++t) threads.emplace_back([&] { for (int i = 0; i < 1000; ++i) hits.fetch_add(1, std::memory_order_relaxed); });\n    for (auto& t : threads) t.join();\n    std::cout << hits.load() << "\\n";','atomic iostream thread vector'),
      'What does this print?','4000',['A value up to 4000 that varies','0'],
      'Every fetch_add is atomic regardless of ordering. join synchronizes with each thread, so the final load sees every increment.')
drill('memory-order-cost','Concept','What acquire costs on x86-64',
      '','On x86-64, what does a std::memory_order_acquire load of an int typically compile to?',
      'An ordinary MOV load, because x86 loads already have acquire ordering',
      ['A load followed by MFENCE','A LOCK-prefixed instruction'],
      'The compiler must still not reorder around it, but no extra instruction is needed. A seq_cst store, in contrast, uses XCHG or MOV plus MFENCE.',check='reasoning')
drill('memory-order-cost','Concept','Acquire and release on arm64',
      '','On arm64 (including Apple silicon), how are acquire loads and release stores usually implemented?',
      'With dedicated ordered instructions such as LDAR or LDAPR and STLR',
      ['With ordinary LDR and STR, because ARM is strongly ordered','With a full DMB barrier around every relaxed access'],
      'ARMv8 provides load-acquire and store-release instructions; relaxed atomics can use plain loads and stores (or LSE atomics for read-modify-write).',check='reasoning')
drill('hot-cold-splitting','Layout','A compact hot record',
      main_program('    std::cout << sizeof(Hot) << "\\n";','cstdint iostream','struct Hot { std::uint32_t id; float price; std::uint16_t qty; char side; };'),
      'What does this print?','12',['11','16'],
      'The members occupy 11 bytes; the struct is padded to a multiple of its 4-byte alignment.')
drill('hot-cold-splitting','Layout','Reordering removes padding',
      main_program('    std::cout << sizeof(Bad) << " " << sizeof(Good) << "\\n";','cstdint iostream',
                   'struct Bad { char a; std::int64_t b; char c; std::int64_t d; };\nstruct Good { std::int64_t b; std::int64_t d; char a; char c; };'),
      'On arm64 macOS, what does this print?','32 24',['18 18','32 32'],
      'Each char before an int64 costs 7 padding bytes. Placing the wide members first leaves only a 6-byte tail pad.')
drill('hot-cold-splitting','Layout','Hot records per cache line',
      '','A hot record is 32 bytes and 32-byte aligned. How many fit in one cache line on Apple silicon (128-byte lines) and on a typical x86-64 core (64-byte lines)?',
      '4 and 2',['2 and 1','8 and 4'],
      'Line size divided by record size. Shrinking the hot record raises the count and the useful bytes per memory transfer.',check='reasoning')
drill('counting-operator-new','Copies and moves','Allocations while pushing ten ints',
      main_program('    allocations = 0;\n    std::vector<int> v;\n    for (int i = 0; i < 10; ++i) v.push_back(i);\n    std::cout << allocations << "\\n";','cstdlib iostream new vector',COUNTING_NEW),
      'With libc++, what does this print?','5',['10','4'],
      'Capacity grows 1, 2, 4, 8, 16, one allocation each. libstdc++ doubles the same way; MSVC grows by 1.5x and would differ.')
drill('counting-operator-new','Copies and moves','Copying versus moving a long string',
      main_program('    std::string s(100, \'x\');\n    allocations = 0;\n    std::string t = s;\n    std::string u = std::move(s);\n    std::cout << allocations << "\\n";','cstdlib iostream new string utility',COUNTING_NEW),
      'What does this print?','1',['2','0'],
      'The copy allocates a new 100-character buffer. The move steals s\'s heap buffer and allocates nothing.')
drill('counting-operator-new','Copies and moves','make_shared versus new',
      main_program('    allocations = 0;\n    auto a = std::make_shared<int>(1);\n    const std::size_t one = allocations;\n    std::shared_ptr<int> b(new int(2));\n    std::cout << one << " " << allocations - one << "\\n";','cstdlib iostream memory new',COUNTING_NEW),
      'What does this print?','1 2',['2 2','1 1'],
      'make_shared places the int and the control block in one allocation. Constructing from new int allocates the int, then a separate control block.')
drill('counting-operator-new','Copies and moves','Reserving less than the current capacity',
      main_program('    allocations = 0;\n    std::vector<int> v;\n    v.reserve(10);\n    v.reserve(5);\n    std::cout << allocations << " " << v.capacity() << "\\n";','cstdlib iostream new vector',COUNTING_NEW),
      'What does this print?','1 10',['2 5','1 5'],
      'reserve never shrinks capacity; a request below the current capacity does nothing.')

# Drills: stage-10 project review
drill('parser-project','Predict output','from_chars stops at the first invalid character',
      main_program('    const std::string s = "12x";\n    int value = -1;\n    auto res = std::from_chars(s.data(), s.data() + s.size(), value);\n    std::cout << (res.ec == std::errc{}) << " " << (res.ptr - s.data()) << " " << value << "\\n";','charconv iostream string system_error'),
      'What does this print?','1 2 12',['0 0 -1','1 3 12'],
      'from_chars succeeds on the prefix 12 and points at x. A whole-token parser must also check that ptr reached the end.',standard=17)
drill('parser-project','Predict output','from_chars on out-of-range input',
      main_program('    const std::string s = "99999999999";\n    int value = -1;\n    auto res = std::from_chars(s.data(), s.data() + s.size(), value);\n    std::cout << (res.ec == std::errc::result_out_of_range) << " " << value << "\\n";','charconv iostream string system_error'),
      'What does this print?','1 -1',['0 2147483647','1 2147483647'],
      'On overflow from_chars reports result_out_of_range and leaves the output value unmodified.',standard=17)
drill('parser-project','Code review','CLI error contract',
      '','The parser CLI prints an error for invalid input but still prints a partial result to stdout and exits 0. What does the project contract expect instead?',
      'Write nothing to stdout, report the error on stderr and exit with a nonzero status (2)',
      ['Print the partial result, since the error is logged','Exit 0 so scripts keep running'],
      'Scripts rely on the exit status and on stdout carrying only valid results. The validator checks that bad input exits 2 with empty stdout.',check='reasoning')
drill('value-project','Predict output','A compiler overflow builtin',
      main_program('    int r = 0;\n    bool overflow = __builtin_add_overflow(std::numeric_limits<int>::max(), 1, &r);\n    std::cout << overflow << "\\n";','iostream limits'),
      'With clang, what does this print?','1',['0','It is undefined behavior'],
      'The clang and GCC builtin computes the sum in infinite precision and reports whether it fits, so no undefined overflow occurs.',standard=14)
drill('value-project','Code review','A checked add that checks too late',
      '','Checked<int>::add computes int sum = a + b; then returns an error if (b > 0 && sum < a). What is wrong?',
      'The overflow already happened, which is undefined, so the check can be optimized away; test a > max - b before adding',
      ['Nothing: the wrapped sum reveals the overflow','It only fails for negative b'],
      'Signed overflow is undefined, so the sum is not guaranteed to wrap. Validate with the operands first.',check='reasoning')
drill('allocator-ring-project','Code review','Masking a non-power-of-two capacity',
      '','A ring buffer computes next = (head + 1) & (Capacity - 1) and is instantiated with Capacity = 6. What happens?',
      'Indices skip slots and the buffer misbehaves; static_assert that Capacity is a power of two or use %',
      ['It wraps correctly at 6','It fails to compile automatically'],
      'For 6, Capacity - 1 is 0b101, so 2 & 5 is 0, 3 & 5 is 1 and 6 & 5 is 4: indices skip slots and repeat instead of cycling 0..5. Only power-of-two capacities make the mask equal to modulo.',check='reasoning')
drill('allocator-ring-project','Code review','Popping without destroying',
      '','pop() copies the front element out and advances head, but never destroys the element in raw storage. With std::string elements, what is the consequence?',
      'Each popped string\'s heap buffer leaks because its destructor never runs',
      ['Nothing: the slot is overwritten later','The program fails to compile'],
      'Raw storage separates lifetime from memory. pop must call std::destroy_at (or allocator_traits::destroy) on the slot before reusing it.',check='reasoning')
drill('pipeline-project','Code review','Waiting without a predicate',
      '','A consumer calls cv.wait(lock) and then pops, without checking whether the queue is non-empty or closed. What can go wrong?',
      'Spurious or missed wakeups make it pop an empty queue or block forever after close',
      ['Nothing: notify_one guarantees exactly one wakeup per item','It only matters on single-core machines'],
      'Use cv.wait(lock, [&] { return closed || !queue.empty(); }) so the shared state, not the notification, decides progress.',check='reasoning')
drill('pipeline-project','Concurrency','Notifying after close',
      '','The producer sets closed = true without holding the mutex and calls cv.notify_all(). Consumers wait with a predicate that reads closed under the mutex. What is the bug?',
      'A data race on closed and a possible lost wakeup; set it while holding the mutex (or make it atomic and still lock before notifying)',
      ['No bug: notify_all wakes everyone','The consumers will spin'],
      'If the flag changes between a consumer checking the predicate and blocking, the notification can be missed. Updating under the mutex prevents that window.',check='reasoning')
drill('coroutine-project','Code review','A copyable generator handle',
      '','A Generator stores a std::coroutine_handle and destroys it in its destructor, but keeps the implicit copy constructor. What happens when a Generator is copied?',
      'Both copies destroy the same frame, a double destroy; delete copying and implement a move that nulls the source',
      ['Each copy gets its own frame','Nothing, coroutine_handle reference-counts the frame'],
      'coroutine_handle is a non-owning pointer-like value. Ownership must be unique, as in the project.',check='reasoning')
drill('coroutine-project','Code review','final_suspend returning suspend_never',
      '','A generator\'s promise returns std::suspend_never from final_suspend, and the owner calls handle.destroy() in its destructor. What is the issue?',
      'The frame destroys itself at completion, so the owner\'s destroy is a double free',
      ['Nothing; destroy on a finished coroutine is a no-op','The coroutine never finishes'],
      'With suspend_never the frame is freed when the coroutine completes. Owners that destroy explicitly need suspend_always at the final point.',check='reasoning')
drill('design-project','Predict output','Visiting closed alternatives',
      main_program('    std::vector<std::variant<Square, Rect>> shapes{Square{2}, Rect{2, 4}};\n    int total = 0;\n    for (const auto& s : shapes) total += std::visit(overloaded{[](Square q) { return q.side * q.side; }, [](Rect r) { return r.w * r.h; }}, s);\n    std::cout << total << "\\n";','iostream variant vector',
                   'template <class... F> struct overloaded : F... { using F::operator()...; };\ntemplate <class... F> overloaded(F...) -> overloaded<F...>;\nstruct Square { int side; };\nstruct Rect { int w, h; };'),
      'What does this print?','12',['8','6'],
      'Each alternative selects its own lambda: 2 * 2 + 2 * 4 is 12.',standard=17)
drill('design-project','Compiles?','A visitor that misses an alternative',
      main_program('    std::variant<Square, Rect> s{Rect{2, 4}};\n    std::cout << std::visit(overloaded{[](Square q) { return q.side; }}, s) << "\\n";','iostream variant',
                   'template <class... F> struct overloaded : F... { using F::operator()...; };\ntemplate <class... F> overloaded(F...) -> overloaded<F...>;\nstruct Square { int side; };\nstruct Rect { int w, h; };'),
      'Does this compile?','No: std::visit requires the visitor to accept every alternative',
      ['Yes, and it throws bad_variant_access for Rect','Yes, and it returns 0 for Rect'],
      'Exhaustiveness is checked at compile time; adding an alternative forces every visitor to handle it.',check='reject',standard=17,diagnostic='is_invocable_v')

"""Additional original C++ units and drills for stages 07-08."""
from cpp_lessons import unit, program
from cpp_drills import drill, main_program

S7 = '07 Standard-library vocabulary and systems facilities'
S8 = '08 Concurrency, synchronization, and coroutines'


def M(body, headers='', decls=''):
    """Complete program; bodies/declarations are raw C++ text so escapes stay literal."""
    return main_program(body.strip('\n'), ' '.join(['iostream'] + headers.split()), decls.strip('\n'))


def line_of(code, text):
    return str(code.splitlines().index(text) + 1)


def R(lesson, title, question, correct, wrong, explanation, kind='Concept'):
    drill(lesson, kind, title, '', question, correct, wrong, explanation, check='reasoning')


# Stage 07: new lessons
unit(S7, 'function-wrapper-cost', 'std::function erases a copyable callable', 17,
     'std::function<R(Args...)> stores any copy-constructible callable whose call signature fits, then calls it through an indirect, type-erased path. The wrapper owns its target: copying the wrapper copies the stored callable, including a lambda\'s captured state.|Implementations keep small targets in an internal buffer and allocate larger ones on the heap; the buffer size is not specified, so do not design around it. Calling through the wrapper usually prevents inlining. Calling an empty wrapper throws std::bad_function_call.|Because the target must be copy-constructible, a lambda that captures a unique_ptr cannot be stored. Prefer a template parameter or a function reference when the callable does not need to be stored, and std::move_only_function (C++23) where it is available for move-only targets.',
     program('functional', r'''    int n = 0;
    std::function<int()> f = [n]() mutable { return ++n; };
    f();
    f();
    auto g = f;
    std::cout << f() << " " << g() << " " << g() << "\n";'''), '3 3 4\n',
     ('Make g call the same stored lambda as f instead of an independent copy.', 'auto g = f;', 'auto g = std::ref(f);', '3 4 5\n',
      'g is now a std::reference_wrapper to f, so it forwards each call to f\'s target. The counter is shared: f() yields 3, then both g() calls advance the same state to 4 and 5.'),
     'What happens when you copy a std::function that holds a stateful mutable lambda?', 'The stored lambda, including its captured state, is copied',
     ['Both wrappers share one lambda object', 'The copy is empty until it is assigned'],
     'std::function has value semantics. Its copy constructor copies the target, so later calls through each wrapper advance separate state.', 'func.wrap.func')

unit(S7, 'reference-wrapper', 'reference_wrapper passes a reference through copying APIs', 17,
     'Several library facilities decay-copy their arguments: std::bind, std::thread, std::make_pair and std::make_tuple store values, not references. std::ref and std::cref wrap an lvalue in a copyable std::reference_wrapper that converts back to T&.|A reference_wrapper is rebindable on assignment, so it can be stored in containers such as std::vector<std::reference_wrapper<T>>. std::bind evaluates and copies its bound arguments when the binder is created; a lambda states captures and the call explicitly and is usually clearer and easier to inline.|The wrapper does not extend lifetime. A std::ref passed to a thread or stored in a callback dangles if the referent is destroyed first, so join or deregister before the object leaves scope.',
     program('functional', r'''    int a = 0;
    auto byValue = std::bind(bump, a);
    byValue();
    byValue();
    auto byReference = std::bind(bump, std::ref(a));
    byReference();
    std::cout << a << "\n";''', 'void bump(int& x) { ++x; }\n'), '1\n',
     ('Make the first binder also modify a.', 'std::bind(bump, a)', 'std::bind(bump, std::ref(a))', '3\n',
      'Without std::ref the binder increments its own stored copy of a. With std::ref both binders forward the original a, so three calls produce 3.'),
     'Why does std::thread(f, x) fail to compile when f takes int&?', 'thread decay-copies its arguments and passes them as rvalues, which cannot bind to int&',
     ['std::thread forbids reference parameters entirely', 'x must be declared volatile'],
     'std::thread stores decayed copies and invokes the function with rvalues. std::ref(x) supplies a wrapper that converts to int&.', 'refwrap')

unit(S7, 'math-helpers20', 'numbers, midpoint, lerp and clamp state numeric intent', 20,
     'C++20 adds std::numbers constants such as pi and e as variable templates, std::midpoint for integers, floating values and pointers, and std::lerp for linear interpolation. std::clamp (C++17) bounds a value between a low and a high limit.|std::midpoint(a, b) does not overflow where (a + b) / 2 would, and for integers it rounds toward the first argument. std::lerp(a, b, 1) returns exactly b. The numbers constants are typed: std::numbers::pi_v<float> avoids a double-to-float conversion.|std::clamp requires lo <= hi; violating that precondition is undefined. It returns a reference to one of its arguments, so binding the result of clamp(x, 0, 10) to a const reference dangles when a temporary argument is selected.',
     program('algorithm cmath iomanip numbers numeric', r'''    const int big = 2'000'000'000;
    std::cout << std::midpoint(big, big - 2) << " "
              << std::lerp(10.0, 20.0, 0.25) << " "
              << std::clamp(17, 0, 10) << " "
              << std::setprecision(6) << std::numbers::pi << "\n";'''), '1999999999 12.5 10 3.14159\n',
     ('Compute the midpoint of big - 3 and big, putting the smaller value first.', 'std::midpoint(big, big - 2)', 'std::midpoint(big - 3, big)', '1999999998 12.5 10 3.14159\n',
      'The exact midpoint is 1999999998.5. Integer midpoint rounds toward its first argument, which is now the smaller value, giving 1999999998 without overflowing int.'),
     'Why prefer std::midpoint(a, b) over (a + b) / 2 for large ints?', 'The sum can overflow int, which is undefined; midpoint cannot',
     ['midpoint is always faster', 'Division by two is implementation-defined for int'],
     'Signed overflow in a + b is undefined behavior. midpoint computes the result without forming the overflowing sum.', 'numeric.ops.midpoint')

unit(S7, 'to-chars-roundtrip', 'to_chars writes the shortest round-tripping text', 17,
     'std::to_chars converts a number into a caller-provided character range without allocation, locale or a null terminator. For floating types without a format argument it writes the shortest representation that from_chars parses back to the identical value.|The result has ptr (one past the last character written) and ec. On success ec is a value-initialized std::errc. If the buffer is too small, ec is std::errc::value_too_large and the contents of the range are unspecified. Explicit chars_format and precision select fixed or scientific output.|Do not treat the buffer as a C string unless you write the terminator yourself. A fixed precision is a presentation choice; it may no longer round-trip.',
     program('charconv string_view', r'''    const double value = 0.1 + 0.2;
    char buffer[32];
    const auto [end, ec] = std::to_chars(buffer, buffer + sizeof buffer, value);
    double back = 0;
    std::from_chars(buffer, end, back);
    std::cout << std::string_view(buffer, end - buffer) << " " << (ec == std::errc{}) << " " << (back == value) << "\n";'''),
     '0.30000000000000004 1 1\n',
     ('Format the value in fixed notation with two decimal places.', 'std::to_chars(buffer, buffer + sizeof buffer, value)',
      'std::to_chars(buffer, buffer + sizeof buffer, value, std::chars_format::fixed, 2)', '0.30 1 0\n',
      'Two fixed decimals succeed but discard information, so parsing "0.30" yields 0.3, which differs from the computed 0.1 + 0.2.'),
     'What does to_chars write after the last digit?', 'Nothing; it returns ptr and never adds a null terminator',
     ['A null terminator if space remains', 'A newline'],
     'to_chars writes only the characters of the number. Use [buffer, ptr) or add a terminator explicitly.', 'charconv.to.chars')

unit(S7, 'quoted-io', 'quoted round-trips strings containing spaces', 14,
     'Plain operator>> for a string stops at whitespace. std::quoted wraps a string in delimiters on output and escapes any delimiter or escape character inside it; on input it reads the delimited text and removes the escapes, so the original value comes back.|The defaults are a double-quote delimiter and a backslash escape; both can be changed. If the input does not begin with the delimiter, quoted input falls back to ordinary whitespace-delimited extraction.|quoted is a small round-trip tool for streams written by the same convention. It is not a CSV or JSON parser and does not validate an unterminated quote in hostile input.',
     program('iomanip sstream string', r'''    std::stringstream stream;
    stream << std::quoted("New York") << ' ' << 7;
    std::string city;
    int count = 0;
    stream >> std::quoted(city) >> count;
    std::cout << city << "|" << count << "|" << stream.str() << "\n";'''), 'New York|7|"New York" 7\n',
     ('Round-trip a value that contains quotation marks.', '"New York"', r'"say \"hi\""', 'say "hi"|7|"say \\"hi\\"" 7\n',
      'Output escapes each embedded quote with a backslash; input removes those escapes, so city regains the exact original text.'),
     'What does stream >> s read from the text "New York" 7 when s is a std::string and quoted is not used?', 'The token "New, including the opening quote',
     ['New York', 'The whole line'],
     'Plain string extraction skips leading whitespace and stops at the next whitespace; it does not interpret quotes.', 'quoted.manip')

unit(S7, 'stream-sync-tie', 'sync_with_stdio and tie trade ordering for speed', 14,
     'By default the standard C++ streams are synchronized with C stdio, so printf and std::cout output interleave in program order. std::ios::sync_with_stdio(false) removes that guarantee and lets the streams buffer independently; it returns the previous setting.|std::cin is tied to std::cout: before each input operation, cout is flushed so a prompt appears before the program blocks. cin.tie(nullptr) removes the flush. std::cerr is also tied to cout and is unit-buffered.|Call sync_with_stdio before any I/O; calling it later has implementation-defined effects. After disabling synchronization, do not mix C and C++ output on the same stream, and after untying, flush prompts explicitly.',
     program('', r'''    const bool wasSynced = std::ios::sync_with_stdio(false);
    const bool tiedToCout = std::cin.tie() == &std::cout;
    std::cin.tie(nullptr);
    std::cout << wasSynced << " " << tiedToCout << " " << (std::cin.tie() == nullptr) << "\n";'''), '1 1 1\n',
     ('Restore the tie before printing.', 'std::cin.tie(nullptr);', 'std::cin.tie(nullptr);\n    std::cin.tie(&std::cout);', '1 1 0\n',
      'tie(&std::cout) reinstates the flush-before-input relationship, so cin.tie() is no longer null.'),
     'After sync_with_stdio(false), what does mixing printf and std::cout on stdout guarantee about order?', 'Nothing; the relative order is not guaranteed',
     ['Output still appears in program order', 'All printf output appears first'],
     'Disabling synchronization allows independent buffering, so interleaving is no longer specified.', 'ios.members.static')

unit(S7, 'hash-combining', 'Custom hashes must agree with equality', 17,
     'An unordered container needs a hash function and an equality predicate. The requirement is one-directional: keys that compare equal must produce equal hashes. Different keys may collide, at a performance cost.|To hash a struct, hash each field and mix the results. XOR alone is symmetric, so (1, 2) and (2, 1) always collide; the widely used seed ^= h + 0x9e3779b9 + (seed << 6) + (seed >> 2) step mixes order into the result.|std::hash values are not stable across implementations or program runs and must not be persisted or sent over a network. Hashing attacker-controlled keys with a predictable function can force worst-case linear buckets.',
     program('functional unordered_set', r'''    std::unordered_set<Point, PointHash> seen{{1, 2}, {2, 1}, {1, 2}};
    std::cout << seen.size() << " " << seen.count({2, 1}) << "\n";''',
             r'''struct Point { int x; int y; };
bool operator==(const Point& a, const Point& b) { return a.x == b.x && a.y == b.y; }
struct PointHash {
    std::size_t operator()(const Point& p) const noexcept {
        std::size_t seed = std::hash<int>{}(p.x);
        seed ^= std::hash<int>{}(p.y) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        return seed;
    }
};
'''), '2 1\n',
     ('Look up a point that was never inserted.', 'seen.count({2, 1})', 'seen.count({3, 3})', '2 0\n',
      'Duplicates were removed by equality, leaving two keys. A missing key hashes to some bucket, fails the equality check and counts 0.'),
     'Which property must a custom hash satisfy?', 'Equal keys must produce equal hash values',
     ['Different keys must produce different hash values', 'Hash values must be stable across program runs'],
     'Collisions are allowed. If equal keys hashed differently, lookups would miss stored elements and duplicates could appear.', 'unord.hash')

unit(S7, 'exchange-idiom', 'exchange replaces a value and returns the old one', 14,
     'std::exchange(obj, new_value) assigns new_value to obj and returns the previous value. It expresses "take the old value and leave a known replacement" in one expression.|It is the usual way to write a move constructor that steals a resource and leaves the source in a valid empty state, for example fd(std::exchange(other.fd, -1)). It also shortens state machines and sequence updates.|std::exchange is ordinary non-atomic code. For a value shared between threads use std::atomic<T>::exchange, which performs the read and write as one atomic operation.',
     program('', r'''    Handle a(7);
    Handle b(std::move(a));
    std::cout << a.fd << " " << b.fd << "\n";''',
             r'''struct Handle {
    int fd;
    explicit Handle(int f) : fd(f) {}
    Handle(Handle&& other) noexcept : fd(std::exchange(other.fd, -1)) {}
};
'''), '-1 7\n',
     ('Use 0 as the moved-from sentinel.', 'std::exchange(other.fd, -1)', 'std::exchange(other.fd, 0)', '0 7\n',
      'exchange stores the new sentinel in the source and returns 7 to initialize b.fd.'),
     'Is std::exchange safe to call concurrently on a shared int?', 'No; it is a plain read and write, so concurrent use is a data race',
     ['Yes; exchange is always atomic', 'Yes, if the new value is a constant'],
     'Only std::atomic<T>::exchange is atomic. std::exchange in <utility> is ordinary code.', 'utility.exchange')

unit(S7, 'fixed-bitset', 'bitset is a fixed-size set of bits with checked and unchecked access', 14,
     'std::bitset<N> stores exactly N bits, with N fixed at compile time. It supports set, reset, flip, count, any, all and none, shifts and bitwise operators, and conversion to string, unsigned long and unsigned long long.|Bit 0 is the least significant bit, but the string constructor and stream output use most-significant-first order. test(i) checks its index and throws std::out_of_range; operator[] does not check. to_ulong throws std::overflow_error if any set bit does not fit.|Constructing from a string containing characters other than 0 and 1 throws std::invalid_argument. Use std::vector<bool> or a dynamic bitset when the size is known only at run time.',
     program('bitset', r'''    std::bitset<8> flags("00101100");
    flags.set(0).flip(2);
    std::cout << flags << " " << flags.count() << " " << flags.to_ulong() << "\n";'''), '00101001 3 41\n',
     ('Report whether bit 3 is set instead of the count.', 'flags.count()', 'flags.test(3)', '00101001 1 41\n',
      'Bit 3 (value 8) is still set after setting bit 0 and clearing bit 2. test returns bool, printed as 1.'),
     'What does bitset<8>::test(9) do?', 'Throws std::out_of_range',
     ['Returns false', 'Has undefined behavior'],
     'test validates its index. operator[] with an out-of-range index would be undefined.', 'template.bitset')

# Stage 08: new lessons
unit(S8, 'shared-mutex-readers', 'shared_mutex admits many readers or one writer', 17,
     'std::shared_mutex has two modes. std::shared_lock acquires shared ownership, and any number of threads may hold it together; std::unique_lock acquires exclusive ownership and excludes all readers and writers.|Mark the mutex mutable so const read methods can lock it. A shared lock only makes concurrent reads safe: modifying shared state while holding a shared lock is still a data race. Whether waiting writers block new readers is not specified, so writer starvation is possible.|There is no upgrade from shared to exclusive. Locking the same shared_mutex again from a thread that already owns it, in either mode, is undefined and in practice deadlocks. For short critical sections a plain std::mutex is often faster.',
     program('atomic map shared_mutex string thread vector', r'''    Config config;
    config.set("port", 80);
    std::atomic<int> total{0};
    std::vector<std::thread> readers;
    for (int i = 0; i < 4; ++i)
        readers.emplace_back([&] { total += config.get("port"); });
    for (auto& reader : readers) reader.join();
    std::cout << total << "\n";''',
             r'''class Config {
    mutable std::shared_mutex mutex_;
    std::map<std::string, int> values_;
public:
    void set(const std::string& key, int value) {
        std::unique_lock lock(mutex_);
        values_[key] = value;
    }
    int get(const std::string& key) const {
        std::shared_lock lock(mutex_);
        const auto found = values_.find(key);
        return found == values_.end() ? -1 : found->second;
    }
};
'''), '320\n',
     ('Have every reader look up a key that was never set.', 'config.get("port")', 'config.get("host")', '-4\n',
      'Each of the four readers finds no entry and contributes -1. The shared locks still allow the lookups to run together.'),
     'A thread holds a shared_lock and then constructs a unique_lock on the same shared_mutex. What happens?', 'Undefined behavior; in practice it deadlocks waiting for itself',
     ['The shared lock is upgraded atomically', 'unique_lock throws std::system_error immediately'],
     'shared_mutex has no upgrade operation, and acquiring it again while already owning it is a precondition violation.', 'thread.sharedmutex.class')

unit(S8, 'call-once-init', 'call_once runs an initializer exactly once', 17,
     'std::call_once(flag, f) runs f on the first call for a given std::once_flag. Concurrent callers wait until that call completes, and its effects happen before every caller returns.|If f exits with an exception, the flag stays unset, the exception propagates, and a later call tries again. A function-local static is initialized with the same guarantee and is often simpler for a lazily created singleton.|Do not replace call_once with double-checked locking on a plain bool: the unlocked read races with the locked write. Calling call_once recursively on the same flag from inside f deadlocks.',
     program('atomic mutex thread vector', r'''    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i)
        threads.emplace_back([] { std::call_once(flag, init); });
    for (auto& thread : threads) thread.join();
    std::cout << inits << "\n";''',
             r'''std::once_flag flag;
std::atomic<int> inits{0};
void init() { ++inits; }
'''), '1\n',
     ('Call init directly from each thread to compare.', 'std::call_once(flag, init)', 'init()', '4\n',
      'Without the once_flag every thread runs init, and the atomic counter records all four calls.'),
     'What happens if the callable passed to call_once throws?', 'The exception propagates and a later call_once on that flag runs a callable again',
     ['The flag is marked done and the exception is swallowed', 'std::terminate is called'],
     'Only a normal return completes the once_flag. An exceptional exit leaves it ready for another attempt.', 'thread.once.callonce')

unit(S8, 'thread-local-storage', 'thread_local gives each thread its own object', 17,
     'A variable declared thread_local has thread storage duration: every thread that uses it gets a separate instance, constructed on first use in that thread (or at thread start) and destroyed when that thread exits.|thread_local suits per-thread caches, counters and random engines because no synchronization is needed for each thread\'s own instance. A static local declared thread_local is initialized once per thread.|thread_local does not prevent a data race if a pointer to the object escapes to another thread, and that pointer dangles once the owning thread exits. Thread pools reuse threads, so state can leak between tasks, and a coroutine resumed on another thread sees that thread\'s instance.',
     program('thread', r'''    int a = 0;
    int b = 0;
    std::thread first([&] { a = work(3); });
    std::thread second([&] { b = work(5); });
    first.join();
    second.join();
    std::cout << a << " " << b << " " << calls << "\n";''',
             r'''thread_local int calls = 0;
int work(int n) {
    for (int i = 0; i < n; ++i) ++calls;
    return calls;
}
'''), '3 5 0\n',
     ('Let the main thread call work(2) before printing.', 'std::cout << a', 'const int mine = work(2);\n    std::cout << mine << " " << a', '2 3 5 2\n',
      'The main thread has its own calls instance, untouched by the workers, so work(2) returns 2 and main\'s instance then holds 2.'),
     'Two threads increment the same thread_local variable by name. Is that a data race?', 'No; each thread increments its own instance',
     ['Yes; thread_local only changes initialization', 'Only if the variable is not atomic'],
     'The name refers to a different object in each thread. A race needs two threads to access the same memory location.', 'basic.stc.thread')

unit(S8, 'relaxed-seqcst-fences', 'Relaxed, sequentially consistent and fence orderings', 17,
     'memory_order_relaxed guarantees atomicity and a single modification order for that one variable, but no ordering with other memory. It is enough for a statistics counter that is read after join, because join itself synchronizes.|memory_order_seq_cst, the default, adds a single total order over all seq_cst operations, which rules out outcomes such as both threads reading 0 in a store-buffering test. A release fence before a relaxed store, paired with an acquire fence after a relaxed load that reads that store, synchronizes like a release store and acquire load.|A relaxed flag does not publish other data: reading the payload afterwards is a data race. A fence orders nothing by itself; it needs an atomic operation that observes the other thread\'s write.',
     program('atomic thread vector', r'''    int seen = 0;
    std::thread reader([&] { seen = consumer(); });
    std::thread writer(producer);
    std::vector<std::thread> counters;
    for (int i = 0; i < 4; ++i)
        counters.emplace_back([] { for (int j = 0; j < 1000; ++j) hits.fetch_add(1, std::memory_order_relaxed); });
    for (auto& counter : counters) counter.join();
    reader.join();
    writer.join();
    std::cout << seen << " " << hits.load(std::memory_order_relaxed) << "\n";''',
             r'''int payload = 0;
std::atomic<bool> ready{false};
std::atomic<int> hits{0};

void producer() {
    payload = 42;
    std::atomic_thread_fence(std::memory_order_release);
    ready.store(true, std::memory_order_relaxed);
}

int consumer() {
    while (!ready.load(std::memory_order_relaxed)) {}
    std::atomic_thread_fence(std::memory_order_acquire);
    return payload;
}
'''), '42 4000\n',
     ('Replace both fences with a release store and an acquire load.',
      [('std::atomic_thread_fence(std::memory_order_release);\n    ready.store(true, std::memory_order_relaxed);', 'ready.store(true, std::memory_order_release);'),
       ('while (!ready.load(std::memory_order_relaxed)) {}\n    std::atomic_thread_fence(std::memory_order_acquire);', 'while (!ready.load(std::memory_order_acquire)) {}')],
      '', '42 4000\n',
      'The acquire load that reads the release store synchronizes with it, giving the same happens-before edge as the fence pair.'),
     'Which order is sufficient for a hit counter that is only read after all threads are joined?', 'memory_order_relaxed',
     ['memory_order_acquire on every increment', 'memory_order_seq_cst is required for any counter'],
     'fetch_add is atomic in every order, and join provides the synchronization for the final read.', 'atomics.fences')

unit(S8, 'false-sharing', 'False sharing costs time, not correctness', 17,
     'Caches move memory in lines. When two threads write different variables that share one line, each write invalidates the other core\'s copy, and the line bounces between cores. The program stays correct but can slow down sharply.|Aligning each hot per-thread object to std::hardware_destructive_interference_size puts it on its own line. Apple clang 21 with libc++ provides the constant; on this arm64 Mac it is 256, while the constructive size is 64, so the lesson checks only a portable lower bound.|The constant is a compile-time estimate and can differ from the real line size of the machine running the binary. Measure before and after padding: padding increases memory use and can reduce cache locality.',
     program('atomic new thread', r'''    PaddedCounter counters[2];
    auto work = [&](int index) {
        for (int i = 0; i < 100000; ++i) counters[index].value.fetch_add(1, std::memory_order_relaxed);
    };
    std::thread a(work, 0);
    std::thread b(work, 1);
    a.join();
    b.join();
    std::cout << (sizeof(PaddedCounter) >= 64) << " " << counters[0].value + counters[1].value << "\n";''',
             r'''struct alignas(std::hardware_destructive_interference_size) PaddedCounter {
    std::atomic<long> value{0};
};
'''), '1 200000\n',
     ('Check the distance between the two counters instead of the type size.', '(sizeof(PaddedCounter) >= 64)',
      '(static_cast<std::size_t>(reinterpret_cast<char*>(&counters[1]) - reinterpret_cast<char*>(&counters[0])) >= std::hardware_destructive_interference_size)', '1 200000\n',
      'Array elements are sizeof apart, and alignas rounds sizeof up to the alignment, so neighbouring counters are at least one interference size apart.'),
     'Two threads update adjacent atomics on the same cache line. What changes compared with padded atomics?', 'Only performance; the results are identical',
     ['The counts become nondeterministic', 'It is a data race'],
     'Each atomic is a separate memory location, so there is no race. Sharing a line only adds coherence traffic.', 'hardware.interference')

unit(S8, 'spsc-ring-buffer', 'A single-producer single-consumer ring needs only two atomics', 17,
     'In an SPSC ring only the producer writes tail and only the consumer writes head. The producer writes a slot and then publishes it with a release store of tail; the consumer\'s acquire load of tail makes the slot contents visible. The consumer releases head to hand the slot back.|One slot stays empty so that head == tail means empty and next(tail) == head means full; capacity is N - 1. Each side may read its own index relaxed because no other thread writes it.|The design relies on exactly one producer and one consumer. A second producer races on the slot and tail. Spinning on a full or empty ring burns a core; add backoff or a wait strategy for real use.',
     program('array atomic cstddef thread', r'''    SpscRing<int, 8> ring;
    long sum = 0;
    std::thread consumer([&] {
        int value = 0;
        for (int got = 0; got < 100;)
            if (ring.pop(value)) { sum += value; ++got; }
    });
    for (int i = 1; i <= 100; ++i)
        while (!ring.push(i)) {}
    consumer.join();
    std::cout << sum << "\n";''',
             r'''template <typename T, std::size_t N>
class SpscRing {
    std::array<T, N> slots_{};
    std::atomic<std::size_t> head_{0};
    std::atomic<std::size_t> tail_{0};
public:
    bool push(const T& value) {
        const auto tail = tail_.load(std::memory_order_relaxed);
        const auto next = (tail + 1) % N;
        if (next == head_.load(std::memory_order_acquire)) return false;
        slots_[tail] = value;
        tail_.store(next, std::memory_order_release);
        return true;
    }
    bool pop(T& out) {
        const auto head = head_.load(std::memory_order_relaxed);
        if (head == tail_.load(std::memory_order_acquire)) return false;
        out = slots_[head];
        head_.store((head + 1) % N, std::memory_order_release);
        return true;
    }
};
'''), '5050\n',
     ('Transfer the values 1 to 1000.', [('got < 100', 'got < 1000'), ('i <= 100', 'i <= 1000')], '', '500500\n',
      'Both loop bounds change together. The ring keeps at most seven values in flight, and every pushed value is popped exactly once.'),
     'Why may push load tail_ with memory_order_relaxed?', 'Only the producer writes tail_, so it always reads its own latest value',
     ['Relaxed loads are always sufficient for indices', 'The consumer never reads tail_'],
     'A thread observes its own writes in program order. The cross-thread edges come from release stores paired with acquire loads.', 'atomics.order')

unit(S8, 'cas-loops-aba', 'compare_exchange loops and the ABA problem', 17,
     'compare_exchange_strong(expected, desired) atomically replaces the value with desired if it equals expected and returns true; otherwise it returns false and writes the current value into expected. compare_exchange_weak may also fail spuriously even when the values match.|Use weak inside a retry loop, where a spurious failure just causes another iteration and can be cheaper on load-linked/store-conditional hardware such as ARM. Use strong when a single attempt decides what to do next.|CAS compares values, not history. In a pointer-based lock-free stack, a node can be popped, freed and reallocated at the same address between a thread\'s read and its CAS, so the CAS succeeds on stale assumptions. Tagged counters, hazard pointers, epoch reclamation or a mutex avoid this ABA problem.',
     program('atomic thread vector', r'''    std::atomic<int> x{5};
    int expected = 3;
    const bool swapped = x.compare_exchange_strong(expected, 9);
    std::cout << swapped << " " << expected << " " << x.load() << " ";
    std::atomic<int> best{0};
    std::vector<std::thread> threads;
    for (int t = 0; t < 4; ++t)
        threads.emplace_back([&best, t] { for (int i = 0; i < 25; ++i) update_max(best, t * 25 + i); });
    for (auto& thread : threads) thread.join();
    std::cout << best.load() << "\n";''',
             r'''void update_max(std::atomic<int>& target, int value) {
    int current = target.load(std::memory_order_relaxed);
    while (current < value && !target.compare_exchange_weak(current, value, std::memory_order_relaxed)) {}
}
'''), '0 5 5 99\n',
     ('Start with the expected value that x actually holds.', 'int expected = 3;', 'int expected = 5;', '1 5 9 99\n',
      'The comparison now succeeds, so x becomes 9 and expected keeps the 5 it already held.'),
     'What does a failed compare_exchange do to its expected argument?', 'Overwrites it with the value currently stored',
     ['Leaves it unchanged', 'Sets it to desired'],
     'Updating expected lets a retry loop recompute desired from the latest value without a separate load.', 'atomics.types.operations')

unit(S8, 'atomic-flag-spinlock', 'atomic_flag builds a spinlock, which rarely beats a mutex', 20,
     'std::atomic_flag is the one atomic type guaranteed to be lock-free. test_and_set with acquire ordering takes the lock and clear with release ordering releases it, so writes inside one critical section happen before the next. Since C++20 a default-constructed flag is clear and test() reads it without writing.|Spinning on test() (test-and-test-and-set) before retrying test_and_set keeps the cache line shared while waiting. A class with lock and unlock satisfies BasicLockable, so std::lock_guard and std::scoped_lock work with it.|A spinning thread wastes CPU while the owner is descheduled and can suffer priority inversion. Prefer std::mutex unless the critical section is tiny, threads are not oversubscribed, and measurement shows a benefit.',
     program('atomic mutex thread vector', r'''    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i)
        threads.emplace_back([] {
            for (int j = 0; j < 10000; ++j) {
                std::lock_guard<Spinlock> guard(spin);
                ++total;
            }
        });
    for (auto& thread : threads) thread.join();
    std::cout << total << "\n";''',
             r'''class Spinlock {
    std::atomic_flag locked_;
public:
    void lock() {
        while (locked_.test_and_set(std::memory_order_acquire))
            while (locked_.test(std::memory_order_relaxed)) {}
    }
    void unlock() { locked_.clear(std::memory_order_release); }
};
Spinlock spin;
long total = 0;
'''), '40000\n',
     ('Run two worker threads instead of four.', 'i < 4', 'i < 2', '20000\n',
      'Each thread still performs 10000 protected increments, so two threads total 20000.'),
     'Why does lock use memory_order_acquire on test_and_set?', 'So writes made by the previous holder before its release clear are visible inside the critical section',
     ['Because test_and_set requires acquire', 'To make the spin loop faster'],
     'A lock must create a happens-before edge from unlock to the next lock. Relaxed ordering would leave the protected data racing.', 'atomics.flag')

unit(S8, 'async-launch-policy', 'async launch policies and the blocking future', 17,
     'std::launch::async runs the task as if on a new thread. std::launch::deferred runs it lazily on the thread that first calls get or wait. The default policy, async | deferred, lets the implementation choose.|A deferred task never runs if no one waits for it, and wait_for on it returns future_status::deferred immediately, so a polling loop with the default policy may never finish. The future returned by std::async is special: its destructor blocks until an async task completes.|Discarding the result of std::async therefore makes the call synchronous, and a future destroyed at the end of a scope waits there. Use std::launch::async explicitly when concurrency is required.',
     program('future thread', r'''    auto lazy = std::async(std::launch::deferred, [] { return std::this_thread::get_id(); });
    auto eager = std::async(std::launch::async, [] { return std::this_thread::get_id(); });
    const auto mainId = std::this_thread::get_id();
    std::cout << (lazy.get() == mainId) << " " << (eager.get() == mainId) << "\n";'''), '1 0\n',
     ('Report the deferred status before running the lazy task.', 'std::cout << (lazy.get() == mainId)',
      'std::cout << (lazy.wait_for(std::chrono::seconds(0)) == std::future_status::deferred) << " " << (lazy.get() == mainId)', '1 1 0\n',
      'wait_for on a deferred task does not start it; it reports deferred. get then runs it on the main thread.'),
     'What does std::async(std::launch::async, f); do when its result is discarded?', 'It blocks until f finishes, because the temporary future\'s destructor waits',
     ['It runs f in the background and returns immediately', 'It never runs f'],
     'Futures created by std::async with the async policy join their task in the destructor of the last shared-state owner.', 'futures.async')

unit(S8, 'packaged-task-promise', 'packaged_task and promise are the write side of a future', 17,
     'A std::promise<T> is the producer end of a shared state: set_value or set_exception stores the result, and the future obtained from get_future reads it. A std::packaged_task<R(Args...)> wraps a callable and stores its return value or exception in its shared state when invoked.|Both are move-only and are often moved into a thread. future::get waits, returns the value or rethrows the exception, and can be called only once; afterwards valid() is false. std::shared_future allows several readers.|Destroying a promise or packaged_task without providing a result stores a future_error with broken_promise. Setting a value twice throws future_error with promise_already_satisfied.',
     program('future string thread', r'''    std::packaged_task<int(int, int)> task([](int a, int b) { return a * b; });
    std::future<int> product = task.get_future();
    std::thread worker(std::move(task), 6, 7);
    std::promise<std::string> promise;
    std::future<std::string> label = promise.get_future();
    std::thread announcer([p = std::move(promise)]() mutable { p.set_value("answer"); });
    std::cout << label.get() << " " << product.get() << "\n";
    worker.join();
    announcer.join();'''), 'answer 42\n',
     ('Make the task add its arguments.', 'return a * b;', 'return a + b;', 'answer 13\n',
      'The worker invokes the packaged task with 6 and 7, and the sum becomes the shared-state value read by get.'),
     'What does future::get report if the promise was destroyed without a value?', 'It throws std::future_error with code broken_promise',
     ['It returns a value-initialized T', 'It blocks forever'],
     'The promise destructor stores broken_promise in an unsatisfied shared state so waiters are released.', 'futures.promise')

unit(S8, 'custom-awaitable', 'An awaiter controls suspension with three functions', 20,
     'co_await expr obtains an awaiter and calls await_ready. If it returns false, the coroutine suspends and await_suspend receives its handle; when the coroutine is resumed, await_resume supplies the value of the co_await expression.|await_suspend may return void (stay suspended), bool (false resumes immediately) or another coroutine handle to resume next (symmetric transfer). Storing the handle somewhere is how a scheduler, timer or I/O completion resumes the coroutine later.|Once the handle is published another thread may resume or destroy the frame, so do not touch awaiter or frame state after publishing it. Resuming a finished coroutine or a destroyed frame is undefined, and reference parameters may dangle across a suspension.',
     program('coroutine exception', r'''    std::coroutine_handle<> pending;
    Task task = run(&pending);
    std::cout << "suspended ";
    pending.resume();
    std::cout << "done=" << task.handle.done() << "\n";''',
             r'''struct Task {
    struct promise_type {
        Task get_return_object() { return Task{std::coroutine_handle<promise_type>::from_promise(*this)}; }
        std::suspend_never initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };
    explicit Task(std::coroutine_handle<promise_type> h) : handle(h) {}
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;
    ~Task() { if (handle) handle.destroy(); }
    std::coroutine_handle<promise_type> handle;
};

struct Pause {
    std::coroutine_handle<>* slot;
    bool await_ready() const noexcept { return false; }
    void await_suspend(std::coroutine_handle<> h) const noexcept { *slot = h; }
    int await_resume() const noexcept { return 7; }
};

Task run(std::coroutine_handle<>* slot) {
    std::cout << "start ";
    const int value = co_await Pause{slot};
    std::cout << "resumed " << value << " ";
}
'''), 'start suspended resumed 7 done=1\n',
     ('Make the awaiter ready so the coroutine never suspends, and guard the resume.',
      [('bool await_ready() const noexcept { return false; }', 'bool await_ready() const noexcept { return true; }'),
       ('    pending.resume();', '    if (pending) pending.resume();')],
      '', 'start resumed 7 suspended done=1\n',
      'A ready awaiter skips await_suspend, so the handle is never stored and the body runs to final suspension before run returns.'),
     'What does await_suspend returning false mean?', 'Do not suspend; resume the current coroutine immediately',
     ['Destroy the coroutine frame', 'Suspend and never resume'],
     'The bool form lets an awaiter decide at the last moment that the result is already available.', 'expr.await')

# Stage 07 drills
O, U, C, CM, L, CC, CR = 'Predict output', 'Undefined behavior', 'Compiles?', 'Copies and moves', 'Layout', 'Concurrency', 'Code review'

drill('optional', O, 'value_or on an empty optional', M(r'''
    std::optional<int> o;
    std::cout << o.value_or(5) << " " << o.has_value() << "\n";''', 'optional'),
      'What does this print?', '5 0', ['0 0', '5 1'],
      'value_or returns the fallback without engaging the optional, so has_value() stays false.')
drill('optional', O, 'value() on an empty optional', M(r'''
    std::optional<int> o;
    try {
        std::cout << o.value() << "\n";
    } catch (const std::bad_optional_access&) {
        std::cout << "caught\n";
    }''', 'optional'),
      'What does this print?', 'caught', ['0', 'Nothing; the program has undefined behavior'],
      'value() checks engagement and throws std::bad_optional_access. Only operator* on an empty optional is undefined.')
drill('optional', O, 'optional<bool> in a condition', M(r'''
    std::optional<bool> flag = false;
    std::cout << (flag ? "engaged" : "empty") << " " << *flag << "\n";''', 'optional'),
      'What does this print?', 'engaged 0', ['empty 0', 'empty 1'],
      'Contextual conversion of an optional tests has_value(), not the contained bool. The optional holds false, so it is engaged.')

drill('variant', O, 'Converting a string literal into variant<bool, string>', M(r'''
    std::variant<bool, std::string> v = "hi";
    std::cout << v.index() << "\n";''', 'string variant'),
      'With C++20 converting-constructor rules (applied by libc++ in C++17 mode), what does this print?', '1', ['0', 'It does not compile'],
      'P0608 excludes the pointer-to-bool conversion from the variant converting constructor, so std::string is the only viable alternative.')
drill('variant', O, 'get with the wrong alternative', M(r'''
    std::variant<int, std::string> v = std::string("text");
    try {
        std::cout << std::get<int>(v) << "\n";
    } catch (const std::bad_variant_access&) {
        std::cout << "bad access " << v.index() << "\n";
    }''', 'string variant'),
      'What does this print?', 'bad access 1', ['0', 'bad access 0'],
      'std::get<T> checks the active alternative and throws bad_variant_access; the variant still holds the string at index 1.')
drill('variant', O, 'Default-constructed variant', M(r'''
    std::variant<int, double> v;
    std::cout << v.index() << std::get<0>(v) << "\n";''', 'variant'),
      'What does this print?', '00', ['Undefined: no alternative is active', '10'],
      'A default-constructed variant value-initializes its first alternative.')
drill('variant', O, 'Visiting with an overload set', M(r'''
    std::variant<int, std::string> v = std::string("abc");
    std::visit(Overloaded{[](int i) { std::cout << "int " << i << "\n"; },
                          [](const std::string& s) { std::cout << "string " << s.size() << "\n"; }}, v);''', 'string variant', r'''
template <class... Ts> struct Overloaded : Ts... { using Ts::operator()...; };
template <class... Ts> Overloaded(Ts...) -> Overloaded<Ts...>;'''),
      'What does this print?', 'string 3', ['int 3', 'It does not compile: lambdas cannot be inherited'],
      'visit calls the overload matching the active alternative. Overloaded inherits each lambda\'s call operator into one overload set.')

drill('any', O, 'any_cast with a different integer type', M(r'''
    std::any a = 42L;
    try {
        std::cout << std::any_cast<int>(a) << "\n";
    } catch (const std::bad_any_cast&) {
        std::cout << "bad_any_cast\n";
    }''', 'any'),
      'What does this print?', 'bad_any_cast', ['42', '0'],
      'any_cast requires the exact stored type. A long is stored, and no conversion to int is attempted.')
drill('any', O, 'Pointer form of any_cast', M(r'''
    std::any a = 3.5;
    int* p = std::any_cast<int>(&a);
    std::cout << (p == nullptr) << "\n";''', 'any'),
      'What does this print?', '1', ['0', 'It throws bad_any_cast'],
      'The pointer overload reports a type mismatch by returning nullptr instead of throwing.')
drill('any', O, 'Storing a string literal in any', M(r'''
    std::any a = "text";
    std::cout << (a.type() == typeid(const char*)) << "\n";''', 'any typeinfo'),
      'What does this print?', '1', ['0, because it stores std::string', '0, because it stores const char[5]'],
      'std::any stores a decayed copy, so the array decays to const char*.')

drill('expected', O, 'Error state accessors', M(r'''
    std::expected<int, std::string> e = std::unexpected("bad");
    std::cout << e.has_value() << " " << e.error() << " " << e.value_or(-1) << "\n";''', 'expected string'),
      'What does this print?', '0 bad -1', ['1 bad -1', '0 bad 0'],
      'unexpected constructs the error state. value_or returns the fallback when no value is held.')
drill('expected', O, 'value() on an error', M(r'''
    std::expected<int, std::string> e = std::unexpected("disk full");
    try {
        std::cout << e.value() << "\n";
    } catch (const std::bad_expected_access<std::string>& error) {
        std::cout << error.error() << "\n";
    }''', 'expected string'),
      'What does this print?', 'disk full', ['0', 'It terminates: bad_expected_access is not catchable'],
      'value() throws bad_expected_access<E> carrying a copy of the error.')
drill('expected', C, 'Implicit conversion to the error type', M(r'''
    std::expected<int, std::string> e = "bad";
    std::cout << e.has_value() << "\n";''', 'expected string'),
      'Does this compile?', 'No: an error must be wrapped in std::unexpected', ['Yes; it stores the error "bad"', 'Yes; it stores the value 0'],
      'The converting constructor targets the value type only. int cannot be constructed from const char*, and the error type is never selected implicitly.',
      check='reject', diagnostic='no viable conversion')

drill('tuple-binding', CM, 'auto structured binding copies', M(r'''
    std::pair<int, int> p{1, 2};
    auto [a, b] = p;
    a = 9;
    std::cout << p.first << " " << b << "\n";''', 'utility'),
      'What does this print?', '1 2', ['9 2', '1 9'],
      'auto [a, b] introduces names for members of a hidden copy of p, so assigning a does not change p.')
drill('tuple-binding', CM, 'auto& structured binding aliases', M(r'''
    std::pair<int, int> p{1, 2};
    auto& [a, b] = p;
    a = 9;
    std::cout << p.first << " " << b << "\n";''', 'utility'),
      'What does this print?', '9 2', ['1 2', '9 9'],
      'With auto& the hidden object is a reference to p, so a names p.first.')
drill('tuple-binding', O, 'tie with ignore', M(r'''
    int x = 0;
    std::tie(x, std::ignore) = std::make_tuple(3, 4);
    std::cout << x << " " << (std::make_tuple(1, 'b') < std::make_tuple(1, 'c')) << "\n";''', 'tuple'),
      'What does this print?', '3 1', ['0 1', '3 0'],
      'tie assigns through references and ignore discards. Tuple comparison is lexicographic: first elements tie, then b < c.')

drill('filesystem', O, 'filename, extension and stem', M(r'''
    std::filesystem::path p = "/a/b/file.tar.gz";
    std::cout << p.filename().string() << " " << p.extension().string() << " " << p.stem().string() << "\n";''', 'filesystem'),
      'What does this print?', 'file.tar.gz .gz file.tar', ['file.tar.gz .tar.gz file', 'file .gz file.tar'],
      'extension is the last dot suffix of the filename; stem is the filename without that suffix.')
drill('filesystem', O, 'Appending an absolute path', M(r'''
    std::filesystem::path p = std::filesystem::path("/usr") / "/etc";
    std::cout << p.string() << "\n";''', 'filesystem'),
      'What does this print on macOS?', '/etc', ['/usr/etc', '/usr//etc'],
      'operator/ with an absolute right operand replaces the left path. Validate untrusted relative components before joining.')
drill('filesystem', O, 'Lexical normalization', M(r'''
    std::cout << std::filesystem::path("a/./b/../c").lexically_normal().string() << "\n";''', 'filesystem'),
      'What does this print?', 'a/c', ['a/b/c', 'a/./c'],
      'lexically_normal removes dot and dot-dot components textually, without consulting the file system or symlinks.')

drill('formatting', O, 'Alignment and fill', M(r'''
    std::cout << std::format("[{:>6}|{:<4}|{:^5}]", 42, "ab", 'x') << "\n";''', 'format'),
      'What does this print?', '[    42|ab  |  x  ]', ['[42    |  ab|x    ]', '[    42|  ab|  x  ]'],
      '> right-aligns, < left-aligns and ^ centres within the given width, padding with spaces.')
drill('formatting', O, 'Zero padding with precision', M(r'''
    std::cout << std::format("{:08.3f}", 3.14159) << "\n";''', 'format'),
      'What does this print?', '0003.142', ['3.142000', '00003.14'],
      'Width 8 counts every character including the point; precision 3 rounds to three decimals; 0 pads with leading zeros.')
drill('formatting', C, 'Format specifier mismatch', M(r'''
    std::cout << std::format("{:d}", "text") << "\n";''', 'format'),
      'Does this compile?', 'No: the format string is checked at compile time and d is invalid for a string', ['Yes; it prints text', 'Yes; it throws format_error at run time'],
      'std::format takes a basic_format_string whose consteval constructor validates each specifier against its argument type.',
      check='reject', diagnostic='consteval')

drill('chrono', O, 'Implicit lossless conversion', M(r'''
    std::chrono::milliseconds ms = std::chrono::seconds(2);
    std::cout << ms.count() << " " << (std::chrono::minutes(1) == std::chrono::seconds(60)) << "\n";''', 'chrono'),
      'What does this print?', '2000 1', ['2 1', '2000 0'],
      'Coarse-to-fine conversion is exact and implicit. Comparison converts both durations to a common type.')
drill('chrono', C, 'Implicit lossy conversion', M(r'''
    std::chrono::seconds s = std::chrono::milliseconds(1500);
    std::cout << s.count() << "\n";''', 'chrono'),
      'Does this compile?', 'No: converting to a coarser integral duration requires duration_cast', ['Yes; it prints 1', 'Yes; it prints 2'],
      'Implicit duration conversion is allowed only when it cannot lose information.', check='reject', diagnostic='no viable conversion')
drill('chrono', O, 'duration_cast versus round', M(r'''
    using namespace std::chrono;
    std::cout << duration_cast<seconds>(milliseconds(1999)).count() << " "
              << round<seconds>(milliseconds(1999)).count() << " "
              << floor<seconds>(milliseconds(-500)).count() << "\n";''', 'chrono'),
      'What does this print?', '1 2 -1', ['2 2 0', '1 2 0'],
      'duration_cast truncates toward zero, round rounds to nearest, and floor rounds toward negative infinity.', standard=17)

drill('randomness', O, 'The mandated mt19937 value', M(r'''
    std::mt19937 engine;
    engine.discard(9999);
    std::cout << engine() << "\n";''', 'random'),
      'What does this print on every conforming implementation?', '4123659995', ['An implementation-specific value', '0'],
      'The standard fixes the 10000th output of a default-seeded mt19937 as 4123659995, so the engine sequence is portable.')
drill('randomness', O, 'Same seed, same engine sequence', M(r'''
    std::mt19937 a(42);
    std::mt19937 b(42);
    a();
    std::cout << (a() == b()) << " " << (a() == b()) << "\n";''', 'random'),
      'What does this print?', '0 0', ['1 1', '0 1'],
      'Both engines produce the same sequence, but a is one step ahead, so each comparison pairs different positions.')
R('randomness', 'Portability of distributions',
  'Two standard libraries run uniform_int_distribution<int>(1, 6) on identically seeded mt19937 engines. Must the outputs match?',
  'No; engine sequences are specified, distribution algorithms are not', ['Yes; the seed fixes everything', 'Only on the same CPU architecture'],
  'The standard specifies engine algorithms but leaves distribution algorithms to the implementation. Reproducible output across platforms needs your own mapping.')

drill('regex', O, 'match versus search', M(r'''
    const std::regex digits("\\d+");
    std::cout << std::regex_match("abc123", digits) << std::regex_search("abc123", digits) << "\n";''', 'regex'),
      'What does this print?', '01', ['11', '10'],
      'regex_match requires the whole input to match; regex_search succeeds on any matching subsequence.')
drill('regex', O, 'Invalid pattern', M(r'''
    try {
        std::regex broken("(");
        std::cout << "built\n";
    } catch (const std::regex_error&) {
        std::cout << "regex_error\n";
    }''', 'regex'),
      'What does this print?', 'regex_error', ['built', 'It does not compile'],
      'Patterns are compiled at run time by the regex constructor, which throws regex_error for invalid syntax.')
drill('regex', C, 'match_results from a temporary string', M(r'''
    std::smatch m;
    const std::regex r("(\\d)");
    std::regex_match(std::string("7"), m, r);
    std::cout << m[1] << "\n";''', 'regex string'),
      'Does this compile?', 'No: the overload taking an rvalue string with smatch is deleted', ['Yes; it prints 7', 'Yes, but m dangles'],
      'smatch stores iterators into the string. The library deletes the rvalue-string overload so they cannot dangle.',
      check='reject', diagnostic='deleted')

drill('system-errors', O, 'error_code compared with errc', M(r'''
    const std::error_code ec = std::make_error_code(std::errc::no_such_file_or_directory);
    std::cout << (ec == std::errc::no_such_file_or_directory) << " " << ec.category().name() << "\n";''', 'system_error'),
      'What does this print?', '1 generic', ['1 system', '0 generic'],
      'make_error_code(errc) uses the generic category, and comparing with an errc goes through error_condition equivalence.')
drill('system-errors', O, 'Default error_code', M(r'''
    std::error_code ec;
    std::cout << static_cast<bool>(ec) << " " << ec.value() << "\n";''', 'system_error'),
      'What does this print?', '0 0', ['1 0', '0 -1'],
      'A default error_code has value 0 in the system category, which means success and converts to false.')
drill('system-errors', O, 'Catching system_error', M(r'''
    try {
        throw std::system_error(std::make_error_code(std::errc::invalid_argument), "parse");
    } catch (const std::system_error& e) {
        std::cout << (e.code() == std::errc::invalid_argument) << "\n";
    }''', 'system_error'),
      'What does this print?', '1', ['0', 'parse'],
      'system_error carries the error_code it was constructed with; code() returns it for comparison.')

drill('mdspan', O, 'Row-major indexing', M(r'''
    int data[6] = {0, 1, 2, 3, 4, 5};
    std::mdspan grid(data, 2, 3);
    std::cout << grid[1, 2] << " " << grid.extent(0) << grid.extent(1) << grid.size() << "\n";''', 'mdspan'),
      'What does this print?', '5 236', ['5 326', '4 236'],
      'The default layout_right is row-major: [1, 2] maps to 1 * 3 + 2. extents are 2 and 3, size 6.')
drill('mdspan', O, 'Column-major layout', M(r'''
    int data[6] = {0, 1, 2, 3, 4, 5};
    std::mdspan<int, std::dextents<std::size_t, 2>, std::layout_left> grid(data, 2, 3);
    std::cout << grid[1, 0] << grid[0, 1] << "\n";''', 'mdspan'),
      'What does this print?', '12', ['31', '10'],
      'layout_left is column-major: [i, j] maps to i + j * 2, so [1, 0] is 1 and [0, 1] is 2.')
R('mdspan', 'mdspan ownership',
  'An mdspan is returned from a function that built it over a local std::vector. What is wrong?',
  'The mdspan dangles: it never owns its elements', ['Nothing; mdspan copies the elements', 'Only the extents are lost'],
  'mdspan is a non-owning view of a pointer plus a mapping. The vector is destroyed when the function returns.')

drill('printing', O, 'print and println', M(r'''
    std::print("{}-", 1);
    std::println("{:x}", 255);''', 'print'),
      'What does this print?', '1-ff', ['1-255', '1-\nff'],
      'print writes exactly the formatted text; println adds a single newline after it. x selects lowercase hexadecimal.')
drill('printing', C, 'Missing format argument', M(r'''
    std::print("{} {}\n", 1);''', 'print'),
      'Does this compile?', 'No: the format string needs two arguments and the check is compile time', ['Yes; it prints "1 "', 'Yes; it throws format_error'],
      'print takes a format_string, whose consteval constructor counts replacement fields against the arguments.',
      check='reject', diagnostic='consteval')
drill('printing', O, 'Printing to a FILE stream', M(r'''
    std::print(stderr, "err ");
    std::print("out\n");''', 'print cstdio'),
      'What appears on standard output?', 'out', ['err out', 'err'],
      'The FILE* overload writes to that stream. Only the second call targets stdout.')

_sl1 = M(r'''
    const int first = report();
    const int second = report();
    std::cout << first << " " << second << "\n";''', 'source_location', r'''
int report(std::source_location where = std::source_location::current()) {
    return static_cast<int>(where.line());
}''')
drill('source-location', O, 'current() as a default argument', _sl1,
      'What does this print?', line_of(_sl1, '    const int first = report();') + ' ' + line_of(_sl1, '    const int second = report();'),
      [' '.join([line_of(_sl1, 'int report(std::source_location where = std::source_location::current()) {')] * 2), '0 0'],
      'A default argument is evaluated at each call site, so current() records the caller\'s line.')
_sl2 = M(r'''
    std::cout << (here() == here()) << " " << here() << "\n";''', 'source_location', r'''
int here() {
    return static_cast<int>(std::source_location::current().line());
}''')
drill('source-location', O, 'current() inside the callee', _sl2,
      'What does this print?', '1 ' + line_of(_sl2, '    return static_cast<int>(std::source_location::current().line());'),
      ['0 ' + line_of(_sl2, '    std::cout << (here() == here()) << " " << here() << "\\n";'), '1 ' + line_of(_sl2, '    std::cout << (here() == here()) << " " << here() << "\\n";')],
      'Called in a function body, current() records that body\'s location, which is the same for every call.')
R('source-location', 'function_name portability',
  'Can a test compare source_location::function_name() against an exact string across compilers?',
  'No; its contents are implementation-defined', ['Yes; it is the unqualified function name', 'Yes; it is the mangled name'],
  'The standard only says function_name returns an implementation-defined description of the function, if any.')

drill('three-way-comparison', O, 'NaN is unordered', M(r'''
    const double nan = std::nan("");
    std::cout << ((1 <=> 2) < 0) << " " << ((nan <=> 1.0) == std::partial_ordering::unordered) << " " << (nan == nan) << "\n";''', 'compare cmath'),
      'What does this print?', '1 1 0', ['1 0 0', '1 1 1'],
      'int comparison yields strong_ordering; double yields partial_ordering, where NaN compares unordered and is not equal to itself.')
drill('three-way-comparison', O, 'Defaulted <=> is memberwise lexicographic', M(r'''
    Version a{1, 9};
    Version b{2, 0};
    std::cout << (a < b) << " " << (a == Version{1, 9}) << "\n";''', 'compare', r'''
struct Version {
    int major;
    int minor;
    auto operator<=>(const Version&) const = default;
};'''),
      'What does this print?', '1 1', ['0 1', '1 0'],
      'A defaulted <=> compares members in declaration order, and a defaulted <=> also declares a defaulted ==.')
drill('three-way-comparison', C, 'Strength cannot be gained', M(r'''
    std::strong_ordering order = 1.0 <=> 2.0;
    std::cout << (order < 0) << "\n";''', 'compare'),
      'Does this compile?', 'No: partial_ordering does not convert to strong_ordering', ['Yes; it prints 1', 'Yes, with a narrowing warning'],
      'Comparison categories convert only from stronger to weaker. double <=> double is partial.', check='reject', diagnostic='no viable conversion')

drill('locale-and-characters', O, 'toupper returns int', M(r'''
    std::cout << std::toupper(static_cast<unsigned char>('a')) << " "
              << static_cast<char>(std::tolower(static_cast<unsigned char>('Q'))) << "\n";''', 'cctype'),
      'What does this print in the C locale?', '65 q', ['A q', '65 113'],
      'The <cctype> functions return int, so streaming the result prints a number unless you convert it back to char.')
R('locale-and-characters', 'Negative char arguments', 
  'char is signed and c holds a byte above 127. What is std::isalpha(c)?',
  'Undefined behavior: the argument must be EOF or representable as unsigned char', ['false', 'true for Latin-1 letters'],
  'A negative char converts to a negative int other than EOF. Cast to unsigned char before calling <cctype> classifiers.', kind=U)
drill('locale-and-characters', O, 'Classification results are nonzero, not 1', M(r'''
    std::cout << (std::isdigit('7') != 0) << (std::isspace('\t') != 0) << (std::isalpha('_') != 0) << "\n";''', 'cctype'),
      'What does this print?', '110', ['111', '100'],
      'Tab is whitespace and underscore is not alphabetic. Compare with 0, because true results are only guaranteed nonzero.')

drill('binary-encoding', O, 'Big-endian field encoding', M(r'''
    const std::uint32_t value = 0x01020304;
    unsigned char bytes[4];
    for (int i = 0; i < 4; ++i) bytes[i] = static_cast<unsigned char>(value >> (24 - 8 * i));
    std::cout << +bytes[0] << +bytes[1] << +bytes[2] << +bytes[3] << "\n";''', 'cstdint'),
      'What does this print on any host?', '1234', ['4321', 'It depends on host endianness'],
      'Shifts operate on values, not memory layout, so the encoding is the same on little- and big-endian hosts.')
drill('binary-encoding', O, 'Promotion of uint8_t in a shift', M(r'''
    const std::uint8_t b = 0x80;
    auto shifted = b << 1;
    std::cout << shifted << " " << sizeof(shifted) << "\n";''', 'cstdint'),
      'What does this print?', '256 4', ['0 1', '256 1'],
      'Integral promotion turns uint8_t into int before the shift, so the result is a 4-byte int that keeps the high bit.')
drill('binary-encoding', U, 'Shift by the full width', M(r'''
    volatile int amount = 32;
    const unsigned value = 1u << amount;
    std::cout << value << "\n";'''),
      'What does the standard say about this program?', 'Undefined behavior: the shift count equals the width of the promoted type',
      ['It prints 0', 'It prints 1 because the count is masked'],
      'A shift count that is negative or at least the operand width is undefined, even for unsigned types. UBSan reports it.', check='ubsan')

drill('from-chars', O, 'Trailing characters are not an error', M(r'''
    const std::string_view text = "42abc";
    int value = 0;
    const auto [ptr, ec] = std::from_chars(text.data(), text.data() + text.size(), value);
    std::cout << value << " " << (ec == std::errc{}) << " " << ptr << "\n";''', 'charconv string_view'),
      'What does this print?', '42 1 abc', ['0 0 42abc', '42 0 abc'],
      'from_chars stops at the first non-digit and reports success. Whole-token validation must also check ptr == end.')
drill('from-chars', O, 'Leading space and plus sign', M(r'''
    int value = 0;
    const char a[] = " 7";
    const char b[] = "+7";
    const auto ra = std::from_chars(a, a + 2, value);
    const auto rb = std::from_chars(b, b + 2, value);
    std::cout << (ra.ec == std::errc::invalid_argument) << (rb.ec == std::errc::invalid_argument) << value << "\n";''', 'charconv'),
      'What does this print?', '110', ['007', '117'],
      'from_chars accepts neither leading whitespace nor a plus sign, and leaves value unchanged on failure.')
drill('from-chars', O, 'Out of range keeps the old value', M(r'''
    int value = 5;
    const char text[] = "99999999999";
    const auto result = std::from_chars(text, text + 11, value);
    std::cout << (result.ec == std::errc::result_out_of_range) << " " << value << "\n";''', 'charconv'),
      'What does this print?', '1 5', ['1 2147483647', '0 5'],
      'On overflow from_chars reports result_out_of_range, consumes the digits, and does not modify value.')

drill('stream-format-state', O, 'setw applies once', M(r'''
    std::cout << std::setw(4) << 1 << 2 << "|\n";''', 'iomanip'),
      'What does this print?', '   12|', ['   1   2|', '12  |'],
      'Width is reset to 0 after the next formatted output, so only 1 is padded.')
drill('stream-format-state', O, 'hex is sticky', M(r'''
    std::cout << std::hex << 255 << " " << 16 << std::dec << " " << 16 << "\n";''', 'iomanip'),
      'What does this print?', 'ff 10 16', ['ff 16 16', 'ff 10 10'],
      'The basefield flag persists until changed, unlike width.')
drill('stream-format-state', O, 'Precision with and without fixed', M(r'''
    std::cout << std::setprecision(3) << 3.14159 << " " << std::fixed << 3.14159 << "\n";''', 'iomanip'),
      'What does this print?', '3.14 3.142', ['3.142 3.142', '3.14 3.14'],
      'In default notation precision counts significant digits; in fixed notation it counts digits after the point.')

drill('complex-numbers', O, 'i squared', M(r'''
    const std::complex<double> i(0, 1);
    std::cout << i * i << " " << std::abs(std::complex<double>(3, 4)) << "\n";''', 'complex'),
      'What does this print?', '(-1,0) 5', ['-1 5', '(-1,0) 25'],
      'complex streams as (real,imag); abs is the magnitude sqrt(3*3 + 4*4).')
drill('complex-numbers', O, 'Square root of a negative number', M(r'''
    const std::complex<double> z(0, 2);
    std::cout << z * z << " " << std::sqrt(-4.0) << "\n";''', 'complex cmath'),
      'What does this print?', '(-4,0) nan', ['(4,0) nan', '(-4,0) (0,2)'],
      'Squaring 2i gives -4 exactly. The real sqrt overload has no real result for -4 and returns NaN; only the complex overload has a root.')
drill('complex-numbers', O, 'Polar construction', M(r'''
    const auto z = std::polar(2.0, 0.0);
    std::cout << z.real() << " " << std::arg(z) << " " << std::norm(z) << "\n";''', 'complex'),
      'What does this print?', '2 0 4', ['2 0 2', '1 0 4'],
      'polar(r, theta) gives r at angle theta. norm is the squared magnitude, not the magnitude.')

drill('calendar-dates', O, 'Leap-day validity', M(r'''
    using namespace std::chrono;
    std::cout << year_month_day{2023y / February / 29}.ok() << year_month_day{2024y / February / 29}.ok() << "\n";''', 'chrono'),
      'What does this print?', '01', ['11', '00'],
      'Constructing the fields never validates; ok() checks that day 29 exists in that February.')
drill('calendar-dates', O, 'Last day of a month', M(r'''
    using namespace std::chrono;
    const year_month_day_last end = 2024y / February / last;
    std::cout << static_cast<unsigned>(end.day()) << "\n";''', 'chrono'),
      'What does this print?', '29', ['28', '31'],
      'year_month_day_last computes the last day from the year, and 2024 is a leap year.')
drill('calendar-dates', O, 'Days between dates', M(r'''
    using namespace std::chrono;
    const auto days_between = sys_days{2024y / March / 1} - sys_days{2024y / January / 1};
    std::cout << days_between.count() << "\n";''', 'chrono'),
      'What does this print?', '60', ['59', '61'],
      'Converting to sys_days gives a day count; January has 31 days and February 2024 has 29.')

drill('utf8-code-units', O, 'Size of a UTF-8 string', M(r'''
    const std::u8string_view s = u8"\u00e9t\u00e9";
    std::cout << s.size() << "\n";''', 'string_view'),
      'What does this print?', '5', ['3', '6'],
      'Each U+00E9 encodes as two UTF-8 code units, plus one for t. size counts code units.')
drill('utf8-code-units', C, 'u8 literal to const char*', M(r'''
    const char* p = u8"x";
    std::cout << p << "\n";'''),
      'Does this compile as C++20?', 'No: u8 literals have type const char8_t[]', ['Yes; it prints x', 'Yes, with a deprecation warning'],
      'C++20 introduced char8_t, so a u8 literal no longer converts to const char*.', check='reject', diagnostic='cannot initialize')
drill('utf8-code-units', O, 'Reversing bytes breaks UTF-8', M(r'''
    std::string s = "a\u00e9";
    std::reverse(s.begin(), s.end());
    std::cout << s.size() << " " << (static_cast<unsigned char>(s[0]) >= 0x80) << "\n";''', 'algorithm string'),
      'What does this print?', '3 1', ['2 0', '3 0'],
      'The two code units of U+00E9 are reversed independently, leaving a continuation byte first and an invalid sequence.')

drill('bit-cast', O, 'Bits of 1.0f', M(r'''
    std::cout << std::hex << std::bit_cast<std::uint32_t>(1.0f) << "\n";''', 'bit cstdint'),
      'What does this print with IEEE-754 float?', '3f800000', ['1', '00000001'],
      'bit_cast copies the object representation: sign 0, biased exponent 127, zero mantissa.')
drill('bit-cast', C, 'bit_cast between different sizes', M(r'''
    std::cout << std::bit_cast<std::uint64_t>(1.0f) << "\n";''', 'bit cstdint'),
      'Does this compile?', 'No: bit_cast requires equal sizes', ['Yes; the high bits are zero', 'Yes, but it is undefined'],
      'bit_cast is constrained on sizeof(To) == sizeof(From) and trivially copyable types.', check='reject', diagnostic='no matching function')
drill('bit-cast', O, 'bit_cast in a constant expression', M(r'''
    constexpr auto bits = std::bit_cast<std::uint64_t>(1.0);
    static_assert(bits != 0);
    std::cout << (bits >> 52) << "\n";''', 'bit cstdint'),
      'What does this print?', '1023', ['1', '0'],
      'bit_cast is constexpr for suitable types. The exponent field of 1.0 is the bias, 1023, and the sign bit is 0.')

drill('bit-utilities', O, 'Counting bits', M(r'''
    std::cout << std::popcount(0xF0u) << " " << std::countr_zero(8u) << " " << std::bit_width(5u) << "\n";''', 'bit'),
      'What does this print?', '4 3 3', ['4 3 2', '8 3 3'],
      'popcount counts ones, countr_zero counts trailing zeros, and bit_width is the number of bits needed to represent the value.')
drill('bit-utilities', C, 'popcount of a signed value', M(r'''
    std::cout << std::popcount(-1) << "\n";''', 'bit'),
      'Does this compile?', 'No: the bit functions accept only unsigned integer types', ['Yes; it prints 32', 'Yes; it prints 0'],
      'std::popcount is constrained to unsigned integer types to avoid sign-dependent results.', check='reject', diagnostic='no matching function')
drill('bit-utilities', O, 'Power-of-two helpers', M(r'''
    std::cout << std::has_single_bit(64u) << " " << std::bit_ceil(17u) << " " << +std::rotl(std::uint8_t{0x81}, 1) << "\n";''', 'bit cstdint'),
      'What does this print?', '1 32 3', ['1 16 2', '0 32 3'],
      'bit_ceil rounds up to a power of two. rotl moves the top bit of 1000_0001 around to the bottom, giving 0000_0011.')

drill('byteswap23', O, 'Swapping four bytes', M(r'''
    std::cout << std::hex << std::byteswap(std::uint32_t{0x12345678}) << "\n";''', 'bit cstdint'),
      'What does this print?', '78563412', ['87654321', '12345678'],
      'byteswap reverses whole bytes, not hexadecimal digits.')
drill('byteswap23', O, 'Native endianness here', M(r'''
    std::cout << (std::endian::native == std::endian::little) << " " << +std::byteswap(std::uint8_t{0xAB}) << "\n";''', 'bit cstdint'),
      'What does this print on an arm64 Mac?', '1 171', ['0 171', '1 186'],
      'arm64 macOS is little-endian. Swapping a single byte leaves it unchanged (0xAB is 171).')
drill('byteswap23', C, 'byteswap on a double', M(r'''
    std::cout << std::byteswap(1.0) << "\n";''', 'bit'),
      'Does this compile?', 'No: byteswap accepts only integral types', ['Yes; it reverses the double\'s bytes', 'Yes; it converts to long first'],
      'byteswap is constrained to integral types. Use bit_cast to an integer first if you really need the bytes.', check='reject', diagnostic='no matching function')

drill('to-underlying23', O, 'Underlying value and type', M(r'''
    std::cout << +std::to_underlying(Color::red) << " " << sizeof(std::to_underlying(Color::red)) << "\n";''', 'utility cstdint', r'''
enum class Color : std::uint8_t { red = 200 };'''),
      'What does this print?', '200 1', ['200 4', '-56 1'],
      'to_underlying returns the declared underlying type, uint8_t. Unary plus promotes it to int for printing.')
drill('to-underlying23', C, 'Scoped enum to int', M(r'''
    enum class Color { red };
    int x = Color::red;
    std::cout << x << "\n";'''),
      'Does this compile?', 'No: scoped enums do not convert implicitly to integers', ['Yes; it prints 0', 'Yes, with a warning'],
      'A scoped enumeration needs an explicit conversion such as to_underlying or static_cast.', check='reject', diagnostic='cannot initialize')
drill('to-underlying23', O, 'Deduced result type', M(r'''
    enum class Small : short { a = 1 };
    std::cout << std::is_same_v<decltype(std::to_underlying(Small::a)), short> << "\n";''', 'type_traits utility'),
      'What does this print?', '1', ['0', 'It does not compile'],
      'to_underlying returns std::underlying_type_t<E>, here short.')

drill('string-contains23', O, 'Substring and character search', M(r'''
    const std::string s = "hello";
    std::cout << s.contains("ell") << s.contains('z') << s.contains("Hell") << "\n";''', 'string'),
      'What does this print?', '100', ['110', '101'],
      'contains is an exact, case-sensitive search for a substring or character.')
drill('string-contains23', O, 'Empty needle', M(r'''
    std::cout << std::string("abc").contains("") << std::string_view("").contains("") << "\n";''', 'string string_view'),
      'What does this print?', '11', ['00', '10'],
      'contains(x) is find(x) != npos, and the empty string is found at position 0 of every string.')
drill('string-contains23', O, 'contains on string_view', M(r'''
    const std::string_view csv = "a,b";
    std::cout << csv.contains(',') << " " << csv.starts_with('a') << " " << csv.ends_with("a") << "\n";''', 'string_view'),
      'What does this print?', '1 1 0', ['1 1 1', '1 0 0'],
      'string_view gained contains in C++23 alongside starts_with and ends_with from C++20; the view ends with b.')

drill('resize-overwrite23', O, 'Callback result becomes the size', M(r'''
    std::string s;
    s.resize_and_overwrite(10, [](char* p, std::size_t) { p[0] = 'o'; p[1] = 'k'; return 2; });
    std::cout << s << " " << s.size() << "\n";''', 'string'),
      'What does this print?', 'ok 2', ['ok 10', 'ok        10'],
      'The callback\'s return value is the new size; the requested count only bounds what the callback may write.')
drill('resize-overwrite23', O, 'Returning zero', M(r'''
    std::string s = "keep";
    s.resize_and_overwrite(8, [](char*, std::size_t) { return 0; });
    std::cout << s.size() << s.empty() << "\n";''', 'string'),
      'What does this print?', '01', ['40', '80'],
      'Returning 0 sets the size to zero, discarding the old characters.')
R('resize-overwrite23', 'Writing past the count',
  'A resize_and_overwrite(n, op) callback writes p[n + 4]. What happens?',
  'Undefined behavior: op may write only [p, p + n]', ['The string grows automatically', 'An exception is thrown'],
  'The callback contract allows writes up to the requested count. The library does not check, and capacity padding can hide the bug from tests.', kind=U)

drill('optional-monadic23', O, 'transform on engaged and empty', M(r'''
    auto twice = [](int x) { return x * 2; };
    std::optional<int> some = 4;
    std::optional<int> none;
    std::cout << some.transform(twice).value_or(0) << " " << none.transform(twice).value_or(0) << "\n";''', 'optional'),
      'What does this print?', '8 0', ['8 -1', '8 2'],
      'transform applies the callback only when engaged; an empty optional stays empty and value_or supplies 0.')
drill('optional-monadic23', O, 'or_else runs only when empty', M(r'''
    int calls = 0;
    auto fallback = [&] { ++calls; return std::optional<int>(1); };
    std::optional<int> some = 5;
    std::optional<int> none;
    const int a = *some.or_else(fallback);
    const int b = *none.or_else(fallback);
    std::cout << a << b << calls << "\n";''', 'optional'),
      'What does this print?', '511', ['512', '111'],
      'or_else returns the engaged optional unchanged and invokes the callable only for the empty one.')
drill('optional-monadic23', C, 'and_then must return an optional', M(r'''
    std::optional<int> o = 2;
    auto r = o.and_then([](int x) { return x + 1; });
    std::cout << *r << "\n";''', 'optional'),
      'Does this compile?', 'No: and_then requires the callable to return a specialization of optional', ['Yes; it prints 3', 'Yes; and_then wraps the int'],
      'and_then is a flat-map. Use transform when the callable returns a plain value.', check='reject', diagnostic='optional')

drill('expected-monadic23', O, 'transform_error maps only the error', M(r'''
    std::expected<int, int> e = std::unexpected(5);
    std::cout << e.transform_error([](int code) { return code * 10; }).error() << "\n";''', 'expected'),
      'What does this print?', '50', ['5', '0'],
      'transform_error applies to the error channel and leaves the success channel untouched.')
drill('expected-monadic23', O, 'and_then short-circuits on error', M(r'''
    int steps = 0;
    auto next = [&](int x) { ++steps; return std::expected<int, std::string>(x + 1); };
    std::expected<int, std::string> start = std::unexpected("bad");
    const auto result = start.and_then(next).and_then(next);
    std::cout << steps << " " << result.error() << "\n";''', 'expected string'),
      'What does this print?', '0 bad', ['2 bad', '0 '],
      'Each and_then forwards an existing error without calling the callable.')
drill('expected-monadic23', O, 'or_else recovers', M(r'''
    std::expected<int, std::string> e = std::unexpected("missing");
    auto recovered = e.or_else([](const std::string& err) { return std::expected<int, std::string>(static_cast<int>(err.size())); });
    std::cout << recovered.value() << "\n";''', 'expected string'),
      'What does this print?', '7', ['0', 'missing'],
      'or_else invokes the callable with the error and returns its expected, here a value of 7 (the error length).')

drill('ranges-to23', O, 'Materializing iota', M(r'''
    const auto v = std::views::iota(1, 5) | std::ranges::to<std::vector>();
    std::cout << v.size() << " " << v.back() << "\n";''', 'ranges vector'),
      'What does this print?', '4 4', ['5 5', '4 5'],
      'iota(1, 5) is half-open, producing 1 through 4. to<std::vector> deduces vector<int>.')
drill('ranges-to23', O, 'Reversing into a string', M(r'''
    const std::string s = std::string_view("abc") | std::views::reverse | std::ranges::to<std::string>();
    std::cout << s << "\n";''', 'ranges string string_view'),
      'What does this print?', 'cba', ['abc', 'It does not compile'],
      'to<std::string> constructs a string from any input range of char.')
drill('ranges-to23', O, 'Materializing into a set', M(r'''
    const std::vector<int> v{3, 1, 3};
    const auto s = v | std::ranges::to<std::set>();
    std::cout << s.size() << " " << *s.begin() << "\n";''', 'ranges set vector'),
      'What does this print?', '2 1', ['3 3', '2 3'],
      'The target container applies its own rules: the set removes the duplicate and orders the keys.')

drill('zip23', O, 'zip length', M(r'''
    const std::vector<int> a{1, 2, 3};
    const std::vector<char> b{'x', 'y'};
    std::cout << std::ranges::distance(std::views::zip(a, b)) << "\n";''', 'ranges vector'),
      'What does this print?', '2', ['3', '5'],
      'zip stops at the shortest input.')
drill('zip23', O, 'Writing through zip', M(r'''
    std::vector<int> x{1, 2};
    const std::vector<int> y{10, 20};
    for (auto [a, b] : std::views::zip(x, y)) a += b;
    std::cout << x[0] << " " << x[1] << "\n";''', 'ranges vector'),
      'What does this print?', '11 22', ['1 2', 'It does not compile'],
      'zip yields a tuple of references, so binding it by value still binds a and b as references to the elements.')
drill('zip23', O, 'zip_transform', M(r'''
    const std::vector<int> x{1, 2};
    const std::vector<int> y{4, 5, 6};
    for (int s : std::views::zip_transform(std::plus<>{}, x, y)) std::cout << s << " ";
    std::cout << "\n";''', 'functional ranges vector'),
      'What does this print (trailing space included)?', '5 7 ', ['5 7 6 ', '5 7'],
      'zip_transform applies the function to corresponding elements and, like zip, stops at the shortest input.')

drill('flat-map23', O, 'Sorted iteration', M(r'''
    std::flat_map<int, char> m;
    m[3] = 'c';
    m[1] = 'a';
    m[2] = 'b';
    for (const auto& [k, v] : m) std::cout << k << v;
    std::cout << "\n";''', 'flat_map'),
      'What does this print?', '1a2b3c', ['3c1a2b', '1a3c2b'],
      'flat_map keeps its keys sorted, like map, but in contiguous storage.')
drill('flat-map23', O, 'insert does not overwrite', M(r'''
    std::flat_map<int, char> m{{1, 'a'}};
    const bool inserted = m.insert({1, 'b'}).second;
    std::cout << inserted << m.at(1) << "\n";''', 'flat_map'),
      'What does this print?', '0a', ['1b', '0b'],
      'insert leaves an existing key untouched and reports false. Use insert_or_assign to overwrite.')
drill('flat-map23', O, 'Separate key and value containers', M(r'''
    std::flat_map<int, char> m{{2, 'b'}, {1, 'a'}};
    std::cout << m.keys()[0] << m.values()[0] << m.keys().size() << "\n";''', 'flat_map'),
      'What does this print?', '1a2', ['2b2', '1a1'],
      'flat_map stores keys and mapped values in two parallel containers exposed by keys() and values().')

drill('out-ptr23', O, 'Filling a unique_ptr from an output parameter', M(r'''
    std::unique_ptr<int> owner;
    make(std::out_ptr(owner));
    std::cout << *owner << "\n";''', 'memory', r'''
int make(int** out) {
    *out = new int(41);
    return 0;
}'''),
      'What does this print?', '41', ['0', 'It leaks and prints nothing'],
      'out_ptr passes a temporary int** and resets owner with the stored pointer when the full-expression ends.')
drill('out-ptr23', O, 'out_ptr releases the previous pointee', M(r'''
    std::unique_ptr<Tracked> owner(new Tracked);
    make(std::out_ptr(owner));
    std::cout << Tracked::destroyed << "\n";''', 'memory', r'''
struct Tracked {
    static inline int destroyed = 0;
    ~Tracked() { ++destroyed; }
};
void make(Tracked** out) { *out = new Tracked; }'''),
      'What does this print?', '1', ['0', '2'],
      'out_ptr resets the smart pointer, so the old object is deleted when the new pointer is adopted; the new one is destroyed after printing.')
drill('out-ptr23', C, 'out_ptr with shared_ptr needs a deleter', M(r'''
    std::shared_ptr<int> owner;
    make(std::out_ptr(owner));
    std::cout << *owner << "\n";''', 'memory', r'''
void make(int** out) { *out = new int(1); }'''),
      'Does this compile?', 'No: shared_ptr reset needs an explicit deleter argument', ['Yes; it prints 1', 'Yes, but it leaks'],
      'shared_ptr cannot recover a deleter from a raw pointer, so out_ptr requires one to be passed explicitly.',
      check='reject', diagnostic='deleter')

# reference-only C++23 facilities (not available in Apple clang 21 libc++): reasoning only
R('move-only-function23', 'Why move_only_function exists',
  'Which callable can std::move_only_function<void()> store that std::function<void()> cannot?',
  'A lambda that captures a std::unique_ptr', ['A function pointer', 'A lambda with no captures'],
  'std::function requires a copy-constructible target. move_only_function only requires move construction.')
R('move-only-function23', 'Copying a move_only_function',
  'Is std::move_only_function copyable?', 'No; it is move-only', ['Yes; it deep-copies its target', 'Yes, if the target is copyable'],
  'It is move-only regardless of the target, which is what lets it hold move-only targets.')
R('move-only-function23', 'const-qualified signature',
  'move_only_function<int() const> stores a lambda whose operator() is not const (mutable). What happens?',
  'It is ill-formed: the cv-qualifier in the signature must be satisfied by the target', ['It compiles and casts away const', 'It throws at call time'],
  'Unlike std::function, move_only_function carries cv, ref and noexcept qualifiers in its signature and checks them against the target.')
R('enumerate-chunk23', 'enumerate element type',
  'What does views::enumerate yield for a vector<char>?', 'A tuple of an index and a reference to the element', ['Only the index', 'A pair of copies'],
  'enumerate yields (index, reference) tuples whose index type is the range difference type.')
R('enumerate-chunk23', 'chunk remainder',
  'views::chunk(3) over seven elements yields how many chunks?', '3, the last holding one element', ['2, the remainder is dropped', '7'],
  'chunk keeps a final shorter chunk; it does not pad or discard the remainder.')
R('enumerate-chunk23', 'chunk versus slide',
  'Which view produces overlapping windows of size 3?', 'views::slide(3)', ['views::chunk(3)', 'views::stride(3)'],
  'chunk partitions into disjoint groups; slide produces every window of n consecutive elements.')
R('standard-generator23', 'Lazy generator body',
  'When does the body of a std::generator coroutine start running?', 'When the first iterator is obtained via begin()', ['When the function is called', 'When the generator is destroyed'],
  'std::generator suspends initially; begin() resumes it until the first co_yield.')
R('standard-generator23', 'Single pass',
  'Can a std::generator be iterated twice?', 'No; it is an input range consumed by one pass', ['Yes; it restarts the coroutine', 'Yes; values are cached'],
  'A generator models input_range. After a pass the coroutine has finished.')
R('standard-generator23', 'Reference parameters',
  'A generator takes const std::string& and is called with a temporary. What is the risk?', 'The reference dangles once the call expression ends, before iteration', ['None; coroutine parameters extend lifetime', 'A compile error'],
  'Coroutine frames copy reference parameters as references. The temporary dies at the end of the full-expression that created the generator.')
R('spanstream23', 'Fixed external buffer',
  'An ospanstream writes 20 characters into a 10-character span. What happens?', 'The stream sets badbit or failbit once the span is full; it does not reallocate', ['It grows the buffer', 'It writes past the end'],
  'spanstream never owns or grows storage. Output beyond the span fails like a full stream buffer.')
R('spanstream23', 'Getting the written text',
  'How do you read what an ospanstream has written?', 'span() returns the written portion of the buffer', ['str() returns a std::string copy', 'The buffer is null-terminated automatically'],
  'span() exposes the written subrange without copying, unlike stringstream::str().')
R('spanstream23', 'Lifetime of the span',
  'Who must keep the character buffer alive?', 'The caller, for the whole life of the stream', ['The stream copies it', 'Nobody; the stream allocates its own'],
  'spanstream only refers to external storage.')
R('stacktrace23', 'Optimized builds',
  'Can std::stacktrace show every source frame in an optimized build?', 'No; inlined and tail-called frames can be missing', ['Yes; the standard requires it', 'Only on Linux'],
  'Frame contents are implementation-defined and depend on debug information and optimization.')
R('stacktrace23', 'Cost of capture',
  'Where should std::stacktrace::current() be called?', 'On diagnostic paths, because capturing can be expensive', ['In every hot function for logging', 'Only in destructors'],
  'Capturing walks the stack; symbolization can allocate and read debug data.')
R('stacktrace23', 'Linking on toolchains',
  'Why might code using <stacktrace> fail to link even with a C++23 compiler?', 'Some implementations need an extra support library or do not ship it', ['stacktrace is header-only everywhere', 'It requires exceptions to be disabled'],
  'Library support is separate from language mode; libstdc++ historically needed -lstdc++exp, and Apple libc++ does not provide it.')

# drills for the new stage-07 lessons
drill('function-wrapper-cost', O, 'Calling an empty std::function', M(r'''
    std::function<int()> f;
    try {
        f();
    } catch (const std::bad_function_call&) {
        std::cout << "bad_function_call ";
    }
    std::cout << (f ? "set" : "empty") << "\n";''', 'functional'),
      'What does this print?', 'bad_function_call empty', ['empty', 'Undefined behavior: nothing reliable'],
      'Invoking an empty std::function throws bad_function_call, and the wrapper remains empty.')
drill('function-wrapper-cost', C, 'Move-only target', M(r'''
    std::function<int()> f = [p = std::make_unique<int>(1)] { return *p; };
    std::cout << f() << "\n";''', 'functional memory'),
      'Does this compile?', 'No: std::function requires a copy-constructible target', ['Yes; it prints 1', 'Yes; the unique_ptr is shared'],
      'The lambda captures a unique_ptr, so it is move-only. std::function must be able to copy whatever it stores.',
      check='reject', diagnostic='implicitly-deleted copy constructor')
drill('function-wrapper-cost', CM, 'Copying a wrapper around a reference capture', M(r'''
    int n = 0;
    std::function<int()> f = [&n] { return ++n; };
    twice(f);
    std::cout << n << "\n";''', 'functional', r'''
void twice(std::function<int()> f) { f(); f(); }'''),
      'What does this print?', '2', ['0', '1'],
      'Passing by value copies the lambda, but the copy still holds a reference to the same n.')

drill('reference-wrapper', C, 'thread argument bound to int&', M(r'''
    int a = 0;
    std::thread t(bump, a);
    t.join();
    std::cout << a << "\n";''', 'thread', 'void bump(int& x) { ++x; }'),
      'Does this compile?', 'No: thread passes a decayed copy as an rvalue, which cannot bind to int&', ['Yes; it prints 1', 'Yes; it prints 0'],
      'std::thread requires the function to be invocable with rvalue copies of the arguments. Use std::ref(a).',
      check='reject', diagnostic='is_invocable')
drill('reference-wrapper', O, 'A vector of references', M(r'''
    int x = 1;
    int y = 2;
    std::vector<std::reference_wrapper<int>> refs{x, y};
    for (int& r : refs) r *= 10;
    std::cout << x << " " << y << "\n";''', 'functional vector'),
      'What does this print?', '10 20', ['1 2', 'It does not compile: vector<int&> is invalid'],
      'reference_wrapper is an assignable object that converts to int&, so the loop modifies x and y.')
drill('reference-wrapper', O, 'bind captures at bind time', M(r'''
    int n = 1;
    auto bound = std::bind(show, n);
    auto lambda = [&n] { show(n); };
    n = 5;
    bound();
    lambda();
    std::cout << "\n";''', 'functional', 'void show(int v) { std::cout << v; }'),
      'What does this print?', '15', ['55', '11'],
      'bind copies n when the binder is created; the lambda captured n by reference and reads it at call time.')
drill('reference-wrapper', O, 'Placeholders reorder arguments', M(r'''
    using namespace std::placeholders;
    auto reversed = std::bind(std::minus<int>{}, _2, _1);
    std::cout << reversed(10, 3) << "\n";''', 'functional'),
      'What does this print?', '-7', ['7', '13'],
      '_2 receives the second call argument (3) and goes first, so the call is 3 - 10.')

drill('math-helpers20', U, 'Averaging with a sum', M(r'''
    volatile int a = 2'000'000'000;
    volatile int b = 2'000'000'000;
    const int average = (a + b) / 2;
    std::cout << average << "\n";'''),
      'What does the standard say about this program?', 'Undefined behavior: a + b overflows int', ['It prints 2000000000', 'It prints a negative number'],
      'The intermediate sum exceeds INT_MAX before the division. std::midpoint avoids forming that sum.', check='ubsan', standard=20)
drill('math-helpers20', O, 'midpoint rounding direction', M(r'''
    std::cout << std::midpoint(0, 5) << " " << std::midpoint(5, 0) << "\n";''', 'numeric'),
      'What does this print?', '2 3', ['2 2', '3 3'],
      'For integers, midpoint rounds toward its first argument, so argument order matters.')
drill('math-helpers20', O, 'Typed constants and clamp', M(r'''
    std::cout << std::is_same_v<decltype(std::numbers::pi_v<float>), const float> << " "
              << std::clamp(-3, 0, 10) << " " << std::lerp(2.0, 4.0, 1.0) << "\n";''', 'algorithm cmath numbers type_traits'),
      'What does this print?', '1 0 4', ['0 0 4', '1 -3 4'],
      'pi_v<float> is an inline constexpr float. clamp returns lo for a value below it, and lerp(a, b, 1) is exactly b.')
drill('math-helpers20', U, 'Dangling clamp result', M(r'''
    int value = 50;
    const int& bounded = std::clamp(value, 0, 10);
    std::cout << bounded << "\n";''', 'algorithm'),
      'What is wrong with this program?', 'bounded refers to the temporary 10, which is destroyed at the end of the declaration',
      ['Nothing; clamp returns by value', 'clamp throws because value is out of range'],
      'clamp returns a const reference to one of its arguments. The prvalue 10 lives only until the full-expression ends, and ASan reports the later read.',
      check='asan')

drill('to-chars-roundtrip', O, 'Buffer too small', M(r'''
    char buffer[3];
    const auto result = std::to_chars(buffer, buffer + 3, 12345);
    std::cout << (result.ec == std::errc::value_too_large) << (result.ptr == buffer + 3) << "\n";''', 'charconv'),
      'What does this print?', '11', ['00', '10'],
      'On failure ec is value_too_large and ptr equals the end of the range.')
drill('to-chars-roundtrip', O, 'Integer bases', M(r'''
    char buffer[16];
    auto end = std::to_chars(buffer, buffer + 16, 255, 16).ptr;
    *end++ = ' ';
    end = std::to_chars(end, buffer + 16, 5, 2).ptr;
    std::cout << std::string_view(buffer, end - buffer) << "\n";''', 'charconv string_view'),
      'What does this print?', 'ff 101', ['FF 101', '0xff 0b101'],
      'to_chars uses lowercase digits and writes no base prefix.')
drill('to-chars-roundtrip', O, 'Shortest float versus widened double', M(r'''
    char buffer[32];
    const auto end = std::to_chars(buffer, buffer + 32, 0.1f).ptr;
    std::cout << std::string_view(buffer, end - buffer) << " " << std::setprecision(17) << static_cast<double>(0.1f) << "\n";''', 'charconv iomanip string_view'),
      'What does this print?', '0.1 0.10000000149011612', ['0.10000000149011612 0.10000000149011612', '0.1 0.1'],
      'Shortest round-trip is computed for the float type. Converting to double keeps the exact float value, which needs more digits as a double.')

drill('quoted-io', O, 'Plain extraction of a quoted token', M(r'''
    std::istringstream in("\"a b\" c");
    std::string word;
    in >> word;
    std::cout << word << "\n";''', 'sstream string'),
      'What does this print?', '"a', ['a b', '"a b"'],
      'Without quoted, >> stops at the first whitespace and keeps the quote character.')
drill('quoted-io', O, 'Custom delimiter', M(r'''
    std::cout << std::quoted("it's", '\'') << "\n";''', 'iomanip'),
      'What does this print?', "'it\\'s'", ['"it\'s"', "'it's'"],
      'The chosen delimiter is written around the text, and occurrences of it inside are escaped with a backslash.')
drill('quoted-io', O, 'Escaping backslashes', M(r'''
    std::cout << std::quoted("C:\\dir") << "\n";''', 'iomanip'),
      'What does this print?', '"C:\\\\dir"', ['"C:\\dir"', 'C:\\dir'],
      'The escape character itself is escaped on output, so one backslash becomes two.')

drill('stream-sync-tie', O, 'cerr is tied and unit-buffered', M(r'''
    std::cout << (std::cerr.tie() == &std::cout) << ((std::cerr.flags() & std::ios::unitbuf) != 0)
              << ((std::cout.flags() & std::ios::unitbuf) != 0) << "\n";'''),
      'What does this print?', '110', ['010', '111'],
      'The standard ties cerr to cout and sets unitbuf on cerr, so error output flushes immediately and after pending cout output.')
R('stream-sync-tie', 'Untied prompt',
  'After cin.tie(nullptr), a program writes "Name: " with cout and then reads with cin. What can the user see?',
  'The prompt may not appear before the program waits for input', ['The prompt always appears first', 'The read fails'],
  'Only the tie forced a flush before input. Flush explicitly when untied prompts must appear.')
R('stream-sync-tie', 'endl in a loop',
  'Why can replacing std::endl with "\\n" speed up a loop that writes a million lines to a file?',
  'endl also flushes the stream on every line', ['"\\n" writes fewer bytes', 'endl converts to CRLF'],
  'endl inserts a newline and calls flush. Repeated flushes defeat buffering.', kind='Complexity')

drill('hash-combining', O, 'XOR is symmetric', M(r'''
    std::hash<int> h;
    const auto xorHash = [&](int x, int y) { return h(x) ^ h(y); };
    std::cout << (xorHash(1, 2) == xorHash(2, 1)) << "\n";''', 'functional'),
      'What does this print on every implementation?', '1', ['0', 'It depends on std::hash<int>'],
      'XOR commutes, so swapping fields gives the same combined hash regardless of how each int is hashed.')
drill('hash-combining', C, 'Unordered set without a hash', M(r'''
    std::unordered_set<Point> points;
    std::cout << points.size() << "\n";''', 'unordered_set', r'''
struct Point { int x; int y; };
bool operator==(const Point& a, const Point& b) { return a.x == b.x && a.y == b.y; }'''),
      'Does this compile?', 'No: std::hash<Point> is not enabled', ['Yes; it hashes the bytes', 'Yes, but inserts throw'],
      'std::hash has no primary definition for user types. Provide a specialization or a hasher template argument.',
      check='reject', diagnostic='Hash requirements')
drill('hash-combining', O, 'A constant hash is slow but correct', M(r'''
    std::unordered_set<int, Constant> s{1, 2, 3, 2};
    std::cout << s.size() << s.count(3) << "\n";''', 'unordered_set', r'''
struct Constant {
    std::size_t operator()(int) const noexcept { return 0; }
};'''),
      'What does this print?', '31', ['11', '41'],
      'Every key lands in one bucket, so lookups degrade to linear scans, but equality still distinguishes the keys.')

drill('exchange-idiom', O, 'exchange returns the old value', M(r'''
    int x = 1;
    const int old = std::exchange(x, x + 5);
    std::cout << x << " " << old << "\n";''', 'utility'),
      'What does this print?', '6 1', ['1 6', '6 6'],
      'The new value x + 5 is computed before the call; exchange stores it and returns the previous 1.')
drill('exchange-idiom', O, 'Fibonacci with exchange', M(r'''
    int a = 0;
    int b = 1;
    for (int i = 0; i < 5; ++i) a = std::exchange(b, a + b);
    std::cout << a << " " << b << "\n";''', 'utility'),
      'What does this print?', '5 8', ['8 13', '3 5'],
      'Each step sets b to a + b and a to the old b, advancing the pair (0,1) five times to (5,8).')
drill('exchange-idiom', CC, 'exchange is not atomic', M(r'''
    int shared = 0;
    std::thread a([&] { for (int i = 0; i < 1000; ++i) std::exchange(shared, i); });
    std::thread b([&] { for (int i = 0; i < 1000; ++i) std::exchange(shared, -i); });
    a.join();
    b.join();
    std::cout << "done\n";''', 'thread utility'),
      'Is this program free of data races?', 'No: both threads read and write shared without synchronization',
      ['Yes; std::exchange is atomic', 'Yes; the values written are independent'],
      'std::exchange is an ordinary read followed by a write. Use std::atomic<int>::exchange for shared data.', check='tsan')

drill('fixed-bitset', O, 'Construct from an integer', M(r'''
    std::bitset<4> b(5);
    std::cout << b << " " << b[0] << b[1] << "\n";''', 'bitset'),
      'What does this print?', '0101 10', ['1010 10', '0101 01'],
      'Output is most-significant first, while index 0 is the least significant bit.')
drill('fixed-bitset', O, 'Checked access', M(r'''
    std::bitset<8> b;
    try {
        std::cout << b.test(9) << "\n";
    } catch (const std::out_of_range&) {
        std::cout << "out_of_range\n";
    }''', 'bitset stdexcept'),
      'What does this print?', 'out_of_range', ['0', 'Undefined behavior'],
      'test validates the position and throws out_of_range for 9 >= 8.')
drill('fixed-bitset', O, 'to_ulong overflow and shifts', M(r'''
    std::bitset<70> big;
    big.set(65);
    try {
        std::cout << big.to_ulong();
    } catch (const std::overflow_error&) {
        std::cout << "overflow ";
    }
    std::cout << (std::bitset<4>("1001") << 1) << "\n";''', 'bitset stdexcept'),
      'What does this print?', 'overflow 0010', ['0 0010', 'overflow 10010'],
      'Bit 65 does not fit in unsigned long. A bitset shift discards bits shifted beyond the fixed size.')

# Stage 08 drills
def _task(initial):
    return r'''struct Task {
    struct promise_type {
        Task get_return_object() { return Task{std::coroutine_handle<promise_type>::from_promise(*this)}; }
        std::suspend_''' + initial + r''' initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };
    explicit Task(std::coroutine_handle<promise_type> h) : handle(h) {}
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;
    ~Task() { if (handle) handle.destroy(); }
    std::coroutine_handle<promise_type> handle;
};
'''

drill('thread-ownership', CC, 'Destroying a joinable thread', M(r'''
    std::set_terminate([] {
        std::cout << "terminate" << std::endl;
        std::_Exit(0);
    });
    {
        std::thread worker([] {});
    }
    std::cout << "after" << std::endl;''', 'cstdlib exception thread'),
      'What does this print?', 'terminate', ['after', 'Nothing: the destructor joins silently'],
      'std::thread\'s destructor calls std::terminate if the thread is still joinable. Join or detach on every path; std::jthread joins for you.')
drill('thread-ownership', CM, 'Moving thread ownership', M(r'''
    std::thread empty;
    std::thread a([] {});
    std::thread b = std::move(a);
    std::cout << empty.joinable() << a.joinable() << b.joinable() << "\n";
    b.join();''', 'thread'),
      'What does this print?', '001', ['011', '101'],
      'A default thread owns nothing, and moving transfers the execution handle, leaving the source not joinable.')
drill('thread-ownership', C, 'Copying a thread', M(r'''
    std::thread a([] {});
    std::thread b = a;
    a.join();''', 'thread'),
      'Does this compile?', 'No: std::thread is move-only', ['Yes; both objects refer to one thread', 'Yes; a second thread is started'],
      'Each thread of execution has one owner. The standard deletes the copy constructor; libc++ reports it as an inaccessible private constructor.', check='reject', diagnostic='private constructor')

drill('jthread-stop', O, 'jthread destructor requests stop and joins', M(r'''
    bool stopped = false;
    {
        std::jthread worker([&](std::stop_token token) {
            while (!token.stop_requested()) std::this_thread::yield();
            stopped = true;
        });
    }
    std::cout << stopped << "\n";''', 'thread stop_token'),
      'What does this print?', '1', ['0', 'It hangs forever'],
      'jthread\'s destructor calls request_stop and then join, so the loop exits and its write happens before join returns.')
drill('jthread-stop', O, 'request_stop return value', M(r'''
    std::stop_source source;
    const bool first = source.request_stop();
    const bool second = source.request_stop();
    std::cout << first << second << source.stop_requested() << "\n";''', 'stop_token'),
      'What does this print?', '101', ['111', '001'],
      'request_stop returns true only for the call that actually made the stop request.')
drill('jthread-stop', O, 'Token injection with extra arguments', M(r'''
    int result = 0;
    bool possible = false;
    {
        std::jthread worker([&](std::stop_token token, int n) {
            result = n;
            possible = token.stop_possible();
        }, 21);
    }
    std::cout << result << possible << "\n";''', 'thread stop_token'),
      'What does this print?', '211', ['210', 'It does not compile: 21 is passed as the token'],
      'If the callable accepts a stop_token first, jthread passes its own token before the supplied arguments.')

drill('mutex-invariants', CC, 'Unprotected increment', M(r'''
    int count = 0;
    std::thread a([&] { for (int i = 0; i < 1000; ++i) ++count; });
    std::thread b([&] { for (int i = 0; i < 1000; ++i) ++count; });
    a.join();
    b.join();
    std::cout << count << "\n";''', 'thread'),
      'Is this program well defined?', 'No: concurrent unsynchronized writes are a data race and undefined behavior',
      ['Yes, but it may print less than 2000', 'Yes; ++ on int is atomic on arm64'],
      'A data race is undefined behavior regardless of what the hardware does. Use a mutex or std::atomic.', check='tsan')
drill('mutex-invariants', CC, 'Two mutexes for one variable', M(r'''
    int count = 0;
    std::mutex first;
    std::mutex second;
    std::thread a([&] { for (int i = 0; i < 1000; ++i) { std::lock_guard<std::mutex> g(first); ++count; } });
    std::thread b([&] { for (int i = 0; i < 1000; ++i) { std::lock_guard<std::mutex> g(second); ++count; } });
    a.join();
    b.join();
    std::cout << count << "\n";''', 'mutex thread'),
      'Is count protected?', 'No: the threads lock different mutexes, so the writes still race',
      ['Yes; every access holds a lock', 'Yes, because lock_guard is a full fence'],
      'Mutual exclusion exists only between threads that lock the same mutex.', check='tsan')
drill('mutex-invariants', O, 'Keeping a two-field invariant', M(r'''
    std::mutex m;
    int a = 100;
    int b = 100;
    auto move = [&](int& from, int& to) {
        for (int i = 0; i < 1000; ++i) {
            std::lock_guard<std::mutex> g(m);
            --from;
            ++to;
        }
    };
    std::thread t1(move, std::ref(a), std::ref(b));
    std::thread t2(move, std::ref(b), std::ref(a));
    t1.join();
    t2.join();
    std::cout << a << " " << b << " " << a + b << "\n";''', 'functional mutex thread'),
      'What does this print?', '100 100 200', ['It varies between runs', '-900 1100 200'],
      'Both updates of each transfer happen under the same lock, and both directions run 1000 times.')

drill('condition-variables', O, 'Notification before waiting', M(r'''
    std::mutex m;
    std::condition_variable cv;
    bool ready = false;
    {
        std::lock_guard<std::mutex> lock(m);
        ready = true;
    }
    cv.notify_one();
    std::thread waiter([&] {
        std::unique_lock<std::mutex> lock(m);
        cv.wait(lock, [&] { return ready; });
        std::cout << "proceeded\n";
    });
    waiter.join();''', 'condition_variable mutex thread'),
      'What does this print?', 'proceeded', ['Nothing: the notification was lost and it hangs', 'Undefined behavior'],
      'The predicate overload checks ready before blocking, so a notification sent earlier is not needed.')
R('condition-variables', 'Waiting without a predicate',
  'Why is cv.wait(lock) without a predicate loop a bug?', 'A notification before the wait is lost, and spurious wakeups return without the condition holding',
  ['wait(lock) never returns spuriously', 'It deadlocks because the lock is held'],
  'Condition variables carry no state. Always re-check the shared condition under the mutex.')
drill('condition-variables', CC, 'Setting the flag without the mutex', M(r'''
    std::mutex m;
    std::condition_variable cv;
    bool ready = false;
    std::thread waiter([&] {
        std::unique_lock<std::mutex> lock(m);
        while (!ready) cv.wait_for(lock, std::chrono::milliseconds(1));
    });
    ready = true;
    cv.notify_one();
    waiter.join();
    std::cout << "done\n";''', 'chrono condition_variable mutex thread'),
      'Is this program free of data races?', 'No: ready is written without the mutex while the waiter reads it under the mutex',
      ['Yes; the waiter holds the lock', 'Yes; notify_one synchronizes the write'],
      'Every access to the shared flag must use the same mutex (or the flag must be atomic). notify does not publish data.', check='tsan')

drill('deadlock-avoidance', O, 'scoped_lock with opposite argument orders', M(r'''
    std::mutex a;
    std::mutex b;
    int count = 0;
    std::thread t1([&] { for (int i = 0; i < 10000; ++i) { std::scoped_lock lock(a, b); ++count; } });
    std::thread t2([&] { for (int i = 0; i < 10000; ++i) { std::scoped_lock lock(b, a); ++count; } });
    t1.join();
    t2.join();
    std::cout << count << "\n";''', 'mutex thread'),
      'What does this print?', '20000', ['It may deadlock', 'A value below 20000'],
      'scoped_lock with several mutexes uses a deadlock-avoidance algorithm, so argument order does not matter.')
R('deadlock-avoidance', 'Lock-order inversion',
  'Thread 1 locks a then b; thread 2 locks b then a, each with separate lock_guards. What can happen?',
  'Deadlock: each thread holds one mutex and waits for the other', ['Nothing; mutexes queue fairly', 'A std::system_error is thrown'],
  'Two locks acquired in opposite orders form a cycle in the wait-for graph. Use one global order or std::scoped_lock.')
drill('deadlock-avoidance', O, 'Relocking a recursive_mutex', M(r'''
    std::recursive_mutex m;
    m.lock();
    const bool again = m.try_lock();
    if (again) m.unlock();
    m.unlock();
    std::cout << again << "\n";''', 'mutex'),
      'What does this print?', '1', ['0', 'Undefined behavior'],
      'A recursive_mutex lets its owner acquire further levels. The same pattern with std::mutex would be undefined.')

drill('futures', O, 'shared_future allows repeated get', M(r'''
    std::promise<int> p;
    std::shared_future<int> f = p.get_future().share();
    p.set_value(7);
    const int a = f.get();
    const int b = f.get();
    std::cout << a << " " << b << "\n";''', 'future'),
      'What does this print?', '7 7', ['7 0', 'It throws future_error on the second get'],
      'shared_future::get returns a reference to the stored value and may be called repeatedly.')
drill('futures', O, 'valid after get', M(r'''
    auto f = std::async(std::launch::async, [] { return 1; });
    const bool before = f.valid();
    const int value = f.get();
    std::cout << before << f.valid() << value << "\n";''', 'future'),
      'What does this print?', '101', ['111', '100'],
      'get moves the result out and releases the shared state, so the future is no longer valid.')
drill('futures', O, 'Stored exception', M(r'''
    std::promise<void> p;
    p.set_exception(std::make_exception_ptr(std::runtime_error("late")));
    try {
        p.get_future().get();
    } catch (const std::exception& e) {
        std::cout << e.what() << "\n";
    }''', 'future stdexcept'),
      'What does this print?', 'late', ['std::future_error', 'Nothing'],
      'get rethrows the stored exception object itself, not a wrapper.')

drill('atomic-counters', O, 'fetch_add returns the old value', M(r'''
    std::atomic<int> a{5};
    std::cout << a.fetch_add(2) << " " << a << "\n";''', 'atomic'),
      'What does this print?', '5 7', ['7 7', '5 5'],
      'fetch_add returns the value before the addition. In C++17 the << operands are evaluated left to right.', standard=17)
drill('atomic-counters', O, 'Postfix and prefix', M(r'''
    std::atomic<int> a{5};
    const int x = a++;
    const int y = ++a;
    std::cout << x << " " << y << "\n";''', 'atomic'),
      'What does this print?', '5 7', ['6 7', '5 6'],
      'Postfix returns the old value and prefix returns the new value; both are single atomic read-modify-writes.')
R('atomic-counters', 'Check then act on an atomic',
  'Two threads run if (stock > 0) --stock; where stock is std::atomic<int> starting at 1. Is this a data race, and can stock end at -1?',
  'No data race, but yes: both checks can pass before either decrement', ['It is a data race', 'No; atomics make the whole if statement atomic'],
  'Each operation is atomic, but the check and the decrement are separate. Use a compare_exchange loop or a mutex for the invariant.', kind=CC)
drill('atomic-counters', C, 'Copying an atomic', M(r'''
    std::atomic<int> a{1};
    std::atomic<int> b = a;
    std::cout << b << "\n";''', 'atomic'),
      'Does this compile?', 'No: std::atomic is not copyable', ['Yes; b is 1', 'Yes; b shares a\'s storage'],
      'A copy would be a load followed by a store, not one atomic operation, so the copy constructor is deleted.', check='reject', diagnostic='deleted')

drill('release-acquire', CC, 'Release store, relaxed load', M(r'''
    int payload = 0;
    std::atomic<bool> ready{false};
    std::thread producer([&] {
        payload = 42;
        ready.store(true, std::memory_order_release);
    });
    while (!ready.load(std::memory_order_relaxed)) {}
    std::cout << payload << "\n";
    producer.join();''', 'atomic thread'),
      'Is the read of payload race-free?', 'No: a relaxed load does not synchronize with the release store',
      ['Yes; release on the store is enough', 'Yes; the loop waits for ready'],
      'Synchronization needs both halves: a release operation and an acquire operation that reads its value.', check='tsan')
drill('release-acquire', O, 'Matching release and acquire', M(r'''
    int payload = 0;
    std::atomic<bool> ready{false};
    std::thread producer([&] {
        payload = 42;
        ready.store(true, std::memory_order_release);
    });
    while (!ready.load(std::memory_order_acquire)) {}
    std::cout << payload << "\n";
    producer.join();''', 'atomic thread'),
      'What does this print?', '42', ['0 or 42', 'Undefined behavior'],
      'The acquire load reads the release store, so the earlier payload write happens before the read.')
R('release-acquire', 'IRIW',
  'Two writers store x = 1 and y = 1 with release; two readers load x then y and y then x with acquire. Can the readers disagree on which store happened first?',
  'Yes; only seq_cst operations guarantee one total order seen by all threads', ['No; acquire loads always agree', 'Only on x86'],
  'Release/acquire gives pairwise synchronization, not a global order of independent writes.')

drill('atomic-wait', O, 'wait and notify', M(r'''
    std::atomic<int> state{0};
    std::thread setter([&] {
        state.store(1);
        state.notify_one();
    });
    state.wait(0);
    setter.join();
    std::cout << state.load() << "\n";''', 'atomic thread'),
      'What does this print?', '1', ['0', 'It may hang if notify runs first'],
      'wait(0) returns only after observing a value other than 0. If the store happened first, it returns without blocking.')
drill('atomic-wait', O, 'Waiting for a value that already changed', M(r'''
    std::atomic<int> a{3};
    a.wait(0);
    std::cout << "returned\n";''', 'atomic'),
      'What does this print?', 'returned', ['Nothing: it blocks forever', 'Undefined behavior'],
      'wait(old) first compares the current value with old and returns immediately when they differ.')
R('atomic-wait', 'Missing a transient value',
  'A writer stores 1 then 0 quickly and notifies once. A thread called wait(0) earlier. May it keep blocking?',
  'Yes; wait re-checks the value and may only ever observe 0', ['No; any notify ends the wait', 'No; the value 1 is queued'],
  'atomic wait compares values, not events. Use a counter or sequence number when every change must be seen.')

drill('stop-callbacks', O, 'Registering after stop', M(r'''
    std::stop_source source;
    source.request_stop();
    std::stop_callback callback(source.get_token(), [] { std::cout << "callback "; });
    std::cout << "constructed\n";''', 'stop_token'),
      'What does this print?', 'callback constructed', ['constructed', 'constructed callback'],
      'If stop was already requested, the stop_callback constructor invokes the callback immediately on the constructing thread.')
drill('stop-callbacks', O, 'Callbacks run in request_stop', M(r'''
    std::stop_source source;
    std::stop_callback callback(source.get_token(), [] { std::cout << "cb "; });
    source.request_stop();
    std::cout << "after\n";''', 'stop_token'),
      'What does this print?', 'cb after', ['after', 'after cb'],
      'request_stop synchronously invokes registered callbacks on the requesting thread before returning.')
drill('stop-callbacks', O, 'Deregistration on destruction', M(r'''
    std::stop_source source;
    int runs = 0;
    {
        std::stop_callback callback(source.get_token(), [&] { ++runs; });
    }
    source.request_stop();
    std::cout << runs << "\n";''', 'stop_token'),
      'What does this print?', '0', ['1', 'Undefined behavior'],
      'The callback is deregistered when the stop_callback is destroyed, so a later stop request does not run it.')

drill('latches-and-barriers', O, 'try_wait on a latch', M(r'''
    std::latch done(2);
    done.count_down();
    const bool early = done.try_wait();
    done.count_down();
    std::cout << early << done.try_wait() << "\n";''', 'latch'),
      'What does this print?', '01', ['11', '00'],
      'try_wait reports whether the counter has reached zero, which happens only after the second count_down.')
drill('latches-and-barriers', O, 'Barrier completion per phase', M(r'''
    int phases = 0;
    std::barrier sync(3, [&]() noexcept { ++phases; });
    std::vector<std::thread> threads;
    for (int t = 0; t < 3; ++t)
        threads.emplace_back([&] {
            sync.arrive_and_wait();
            sync.arrive_and_wait();
        });
    for (auto& thread : threads) thread.join();
    std::cout << phases << "\n";''', 'barrier thread vector'),
      'What does this print?', '2', ['6', '3'],
      'The completion function runs once per phase, after all participants arrive and before any is released.')
R('latches-and-barriers', 'Reusing a latch',
  'Can a std::latch be reset for a second round?', 'No; it is single-use. Use std::barrier for repeated phases',
  ['Yes, with count_down(-n)', 'Yes; it resets automatically at zero'],
  'latch has no reset operation, and decrementing below zero is a precondition violation.')

drill('coroutine-model', O, 'Initial suspension', M(r'''
    Task task = work();
    std::cout << "created ";
    task.handle.resume();
    std::cout << task.handle.done() << "\n";''', 'coroutine exception', _task('always') + r'''
Task work() {
    std::cout << "body ";
    co_return;
}'''),
      'What does this print?', 'created body 1', ['body created 1', 'created body 0'],
      'initial_suspend returning suspend_always stops before the body. After resume the body runs to final suspension, so done() is true.')
drill('coroutine-model', U, 'Resuming a destroyed frame', M(r'''
    auto handle = work().release();
    handle.destroy();
    handle.resume();''', 'coroutine exception', r'''
struct Lazy {
    struct promise_type {
        Lazy get_return_object() { return Lazy{std::coroutine_handle<promise_type>::from_promise(*this)}; }
        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };
    std::coroutine_handle<promise_type> handle;
    std::coroutine_handle<promise_type> release() { return handle; }
};

Lazy work() { co_return; }'''),
      'What does the standard say about this program?', 'Undefined behavior: the frame was freed, and resume reads it',
      ['resume on a destroyed handle is a no-op', 'It throws std::logic_error'],
      'A coroutine handle is a raw pointer to the frame. After destroy, any use is a use-after-free; ASan reports it.', check='asan')
R('coroutine-model', 'Double destruction',
  'final_suspend returns suspend_never, and the owning Task destructor also calls handle.destroy(). What goes wrong?',
  'The frame is destroyed twice: once when the coroutine finishes and again by the owner', ['Nothing; destroy is idempotent', 'The coroutine never finishes'],
  'Not suspending at the final point destroys the frame automatically. Choose one owner for destruction.')

drill('semaphores', O, 'Counting permits', M(r'''
    std::counting_semaphore<3> slots(3);
    for (int i = 0; i < 4; ++i) std::cout << slots.try_acquire();
    std::cout << "\n";''', 'semaphore'),
      'What does this print (try_acquire may fail spuriously, but not here)?', '1110', ['1111', '1000'],
      'Each successful try_acquire consumes a permit; the fourth finds the count at zero.')
drill('semaphores', O, 'Binary semaphore as a signal', M(r'''
    std::binary_semaphore ready(0);
    int value = 0;
    std::thread producer([&] {
        value = 42;
        ready.release();
    });
    ready.acquire();
    std::cout << "signaled " << value << "\n";
    producer.join();''', 'semaphore thread'),
      'What does this print?', 'signaled 42', ['signaled 0', 'It deadlocks'],
      'release synchronizes with the acquire that observes it, so value is published.')
R('semaphores', 'Releasing too many permits',
  'counting_semaphore<1> s(1); s.release(); What is the status of the release?',
  'Undefined behavior wherever max() is 1; portable code must not rely on spare capacity', ['It is ignored', 'It throws std::system_error'],
  'release(update) has the precondition update <= max() - counter. max() is only guaranteed to be at least the template argument, so the release is a precondition violation when max() is 1 and never a portable way to exceed it.', kind=U)

drill('atomic-ref', O, 'Atomic access to a plain int', M(r'''
    alignas(std::atomic_ref<int>::required_alignment) int value = 0;
    auto work = [&] { for (int i = 0; i < 1000; ++i) std::atomic_ref<int>(value).fetch_add(1); };
    std::thread a(work);
    std::thread b(work);
    a.join();
    b.join();
    std::cout << value << "\n";''', 'atomic thread'),
      'What does this print?', '2000', ['A value up to 2000', '1000'],
      'All concurrent accesses go through atomic_ref, so the increments are atomic; join makes the final plain read safe.')
drill('atomic-ref', CC, 'Mixing atomic_ref with plain access', M(r'''
    int value = 0;
    std::thread a([&] { for (int i = 0; i < 1000; ++i) std::atomic_ref<int>(value).fetch_add(1); });
    std::thread b([&] { for (int i = 0; i < 1000; ++i) ++value; });
    a.join();
    b.join();
    std::cout << value << "\n";''', 'atomic thread'),
      'Is this race-free?', 'No: the plain increment conflicts with the atomic accesses',
      ['Yes; one side is atomic', 'Yes; atomic_ref makes the object atomic for its lifetime'],
      'While any atomic_ref to an object exists, every concurrent access must go through atomic_ref.', check='tsan')
drill('atomic-ref', L, 'Required alignment here', M(r'''
    std::cout << std::atomic_ref<int>::required_alignment << " " << std::atomic_ref<int>::is_always_lock_free << "\n";''', 'atomic'),
      'What does this print on arm64 macOS?', '4 1', ['8 1', '4 0'],
      'For int the required alignment equals alignof(int) here, and 4-byte atomics are always lock-free on arm64.')

# drills for the new stage-08 lessons
drill('shared-mutex-readers', C, 'shared_lock on a plain mutex', M(r'''
    std::mutex m;
    std::shared_lock<std::mutex> lock(m);''', 'mutex shared_mutex'),
      'Does this compile?', 'No: std::mutex has no lock_shared', ['Yes; it behaves like unique_lock', 'Yes, but it is undefined'],
      'shared_lock calls lock_shared and unlock_shared, which only shared mutex types provide.', check='reject', diagnostic='lock_shared')
drill('shared-mutex-readers', CC, 'Writing under a shared lock', M(r'''
    std::shared_mutex m;
    std::latch both(2);
    int hits = 0;
    auto reader = [&] {
        std::shared_lock<std::shared_mutex> lock(m);
        both.arrive_and_wait();
        ++hits;
    };
    std::thread a(reader);
    std::thread b(reader);
    a.join();
    b.join();
    std::cout << hits << "\n";''', 'latch shared_mutex thread'),
      'Is the increment protected?', 'No: shared ownership lets both threads write at once, which is a data race',
      ['Yes; every access holds the mutex', 'Yes; the latch orders the increments'],
      'A shared lock excludes writers only if writers take exclusive ownership. Mutating under a shared lock races.', check='tsan', standard=20)
drill('shared-mutex-readers', CC, 'Exclusive try_lock while a reader holds the mutex', M(r'''
    std::shared_mutex m;
    std::shared_lock<std::shared_mutex> reader(m);
    bool exclusive = true;
    bool shared = false;
    std::thread other([&] {
        exclusive = m.try_lock();
        if (exclusive) m.unlock();
        shared = m.try_lock_shared();
        if (shared) m.unlock_shared();
    });
    other.join();
    std::cout << exclusive << shared << "\n";''', 'shared_mutex thread'),
      'What does this print with libc++?', '01', ['11', '00'],
      'A held shared lock blocks exclusive ownership but admits another reader. The standard allows try functions to fail spuriously; libc++ does not.')

drill('call-once-init', O, 'A throwing initializer is retried', M(r'''
    std::once_flag flag;
    int attempts = 0;
    for (int i = 0; i < 3; ++i) {
        try {
            std::call_once(flag, [&] {
                ++attempts;
                if (attempts == 1) throw std::runtime_error("fail");
            });
        } catch (const std::runtime_error&) {
            std::cout << "threw ";
        }
    }
    std::cout << attempts << "\n";''', 'mutex stdexcept'),
      'What does this print?', 'threw 2', ['threw 1', 'threw threw 3'],
      'An exceptional call does not complete the flag. The second call returns normally, so the third does nothing.')
drill('call-once-init', O, 'Function-local static initialization', M(r'''
    counter()++;
    counter()++;
    std::cout << counter() << "\n";''', '', r'''
int& counter() {
    static int value = [] {
        std::cout << "init ";
        return 10;
    }();
    return value;
}'''),
      'What does this print?', 'init 12', ['init init init 12', 'init 10'],
      'A block-scope static is initialized once, on first pass, and that initialization is thread-safe.')
drill('call-once-init', CC, 'Double-checked locking with a plain bool', M(r'''
    std::mutex m;
    bool ready = false;
    int value = 0;
    auto get = [&] {
        if (!ready) {
            std::lock_guard<std::mutex> lock(m);
            if (!ready) {
                value = 42;
                ready = true;
            }
        }
        return value;
    };
    int a = 0;
    int b = 0;
    std::thread t1([&] { a = get(); });
    std::thread t2([&] { b = get(); });
    t1.join();
    t2.join();
    std::cout << a + b << "\n";''', 'mutex thread'),
      'Is this initialization race-free?', 'No: the first read of ready happens outside the lock and races with the locked write',
      ['Yes; the second check is under the lock', 'Yes; bool writes are atomic'],
      'Every access to a shared non-atomic variable must be synchronized. Use call_once, a static local, or an atomic flag with acquire/release.', check='tsan')

drill('thread-local-storage', O, 'thread_local inside a lambda', M(r'''
    auto tick = [] {
        thread_local int n = 0;
        return ++n;
    };
    tick();
    tick();
    int other = 0;
    std::thread t([&] { other = tick(); });
    t.join();
    std::cout << tick() << " " << other << "\n";''', 'thread'),
      'What does this print?', '3 1', ['4 3', '3 3'],
      'A block-scope thread_local variable is per thread, so the new thread starts its own count at zero.')
drill('thread-local-storage', O, 'Destruction at thread exit', M(r'''
    std::thread t([] {
        tracer.touch();
        std::cout << "body ";
    });
    t.join();
    std::cout << "joined\n";''', 'thread', r'''
struct Tracer {
    ~Tracer() { std::cout << "dtor "; }
    void touch() {}
};
thread_local Tracer tracer;'''),
      'What does this print?', 'body dtor joined', ['body joined dtor', 'body joined'],
      'A thread_local object used by a thread is destroyed as that thread exits, which happens before join returns.')
drill('thread-local-storage', CC, 'An escaped pointer to thread_local data', M(r'''
    std::atomic<int*> shared{nullptr};
    std::barrier<> both(2);
    std::thread owner([&] {
        shared.store(&mine, std::memory_order_release);
        both.arrive_and_wait();
        ++mine;
        both.arrive_and_wait();
    });
    std::thread other([&] {
        int* p = nullptr;
        while (!(p = shared.load(std::memory_order_acquire))) {}
        both.arrive_and_wait();
        ++*p;
        both.arrive_and_wait();
    });
    owner.join();
    other.join();
    std::cout << "done\n";''', 'atomic barrier thread', 'thread_local int mine = 0;'),
      'Is this program race-free?', 'No: both threads write the owner\'s instance concurrently through the escaped pointer',
      ['Yes; thread_local data cannot be shared', 'Yes; the barrier orders the writes'],
      'thread_local gives each thread a separate object, but an address still identifies one memory location that any thread can reach.',
      check='tsan', standard=20)

drill('relaxed-seqcst-fences', CC, 'Publishing with a relaxed flag', M(r'''
    int payload = 0;
    std::atomic<bool> ready{false};
    std::thread producer([&] {
        payload = 42;
        ready.store(true, std::memory_order_relaxed);
    });
    while (!ready.load(std::memory_order_relaxed)) {}
    std::cout << payload << "\n";
    producer.join();''', 'atomic thread'),
      'Is reading payload well defined?', 'No: relaxed operations create no happens-before edge, so this is a data race',
      ['Yes; the loop waits for the flag', 'Yes on arm64 because loads are ordered'],
      'Relaxed atomics are atomic but do not order other memory. Use release and acquire for publication.', check='tsan')
R('relaxed-seqcst-fences', 'Store buffering',
  'Thread 1: x.store(1); r1 = y.load(). Thread 2: y.store(1); r2 = x.load(). With release stores and acquire loads, can r1 == 0 and r2 == 0?',
  'Yes; only seq_cst on all four operations forbids it', ['No; acquire prevents it', 'Only with relaxed ordering'],
  'Release/acquire does not order a store before a later load of a different variable. seq_cst adds the single total order that rules this out.', kind=CC)
R('relaxed-seqcst-fences', 'A fence on its own',
  'A writer runs payload = 1; atomic_thread_fence(release); and never touches an atomic. The reader runs an acquire fence and reads payload. Is that synchronized?',
  'No; fences synchronize only through an atomic that the reader observes', ['Yes; the fences pair up', 'Yes, with seq_cst fences'],
  'A fence-fence synchronization requires an atomic store after the release fence that is read by an atomic load before the acquire fence.')

R('false-sharing', 'Results under false sharing',
  'Two threads each fetch_add their own adjacent std::atomic<long> on one cache line. Which statement is true?',
  'The totals are exact; only throughput suffers', ['Increments can be lost', 'It is undefined behavior'],
  'Distinct atomic objects are distinct memory locations. Cache-line sharing is invisible to program semantics.', kind='Complexity')
drill('false-sharing', L, 'Size of separately aligned members', M(r'''
    std::cout << sizeof(Pair) << " " << alignof(Pair) << "\n";''', 'atomic', r'''
struct Pair {
    alignas(64) std::atomic<int> a;
    alignas(64) std::atomic<int> b;
};'''),
      'What does this print?', '128 64', ['8 4', '64 64'],
      'Each member starts on a 64-byte boundary, and the struct size is rounded up to a multiple of its alignment.')
drill('false-sharing', L, 'Over-aligned elements in a vector', M(r'''
    std::vector<Slot> slots(3);
    const auto address = reinterpret_cast<std::uintptr_t>(slots.data());
    std::cout << (address % 64 == 0) << " " << sizeof(Slot) << "\n";''', 'cstdint vector', r'''
struct alignas(64) Slot { long value = 0; };'''),
      'What does this print in C++17?', '1 64', ['0 64', '1 8'],
      'C++17 aligned allocation passes the alignment to operator new, so heap elements honour alignas(64).')

R('spsc-ring-buffer', 'Relaxed publication of tail',
  'If push stored tail_ with memory_order_relaxed, what could the consumer observe?',
  'A new tail before the slot contents, so reading the slot is a data race', ['Nothing different; tail is atomic', 'Only a stale tail, never stale data'],
  'The release store is what orders the slot write before the index update for an acquiring reader.', kind=CC)
drill('spsc-ring-buffer', CC, 'All relaxed indices', M(r'''
    std::array<int, 4> slots{};
    std::atomic<std::size_t> tail{0};
    std::thread producer([&] {
        slots[0] = 7;
        tail.store(1, std::memory_order_relaxed);
    });
    while (tail.load(std::memory_order_relaxed) == 0) {}
    std::cout << slots[0] << "\n";
    producer.join();''', 'array atomic cstddef thread'),
      'Is reading slots[0] race-free?', 'No: the relaxed index store does not publish the slot write',
      ['Yes; the slot is written before tail', 'Yes; the consumer only reads'],
      'Program order in the producer is not visible to another thread without a release/acquire edge.', check='tsan')
drill('spsc-ring-buffer', O, 'Usable capacity', M(r'''
    std::size_t head = 0;
    std::size_t tail = 0;
    constexpr std::size_t N = 4;
    int accepted = 0;
    for (int i = 0; i < 10; ++i) {
        const std::size_t next = (tail + 1) % N;
        if (next == head) break;
        tail = next;
        ++accepted;
    }
    std::cout << accepted << "\n";''', 'cstddef'),
      'This is the ring\'s full test with no consumer. What does it print?', '3', ['4', '10'],
      'One slot stays empty so that head == tail can mean empty; a ring of N slots holds N - 1 values.')

drill('cas-loops-aba', O, 'Two strong CAS attempts', M(r'''
    std::atomic<int> v{10};
    int expected = 10;
    const bool first = v.compare_exchange_strong(expected, 20);
    const bool second = v.compare_exchange_strong(expected, 30);
    std::cout << first << second << " " << expected << " " << v.load() << "\n";''', 'atomic'),
      'What does this print?', '10 20 20', ['11 20 30', '10 10 20'],
      'The first CAS succeeds and leaves expected at 10. The second fails against 20 and loads 20 into expected.')
drill('cas-loops-aba', O, 'Read-modify-write via a CAS loop', M(r'''
    std::atomic<int> product{1};
    auto twice = [&] {
        int current = product.load();
        while (!product.compare_exchange_weak(current, current * 2)) {}
    };
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) threads.emplace_back(twice);
    for (auto& thread : threads) thread.join();
    std::cout << product << "\n";''', 'atomic thread vector'),
      'What does this print?', '16', ['8', 'Any power of two up to 16'],
      'Each loop retries with the refreshed current value until its doubling applies to the latest value, so no update is lost.')
R('cas-loops-aba', 'ABA in a lock-free stack',
  'Thread 1 reads top = A and next = B, then stalls. Thread 2 pops A and B, frees B, and pushes A back. Thread 1\'s CAS(top, A -> B) succeeds. What is wrong?',
  'top now points to freed node B', ['Nothing; the CAS verified top', 'The CAS spuriously failed'],
  'CAS saw the same pointer value but the structure changed. Version tags or safe memory reclamation detect or prevent this.', kind=CC)

drill('atomic-flag-spinlock', CC, 'A relaxed spinlock', M(r'''
    std::atomic_flag locked;
    long total = 0;
    auto work = [&] {
        for (int i = 0; i < 1000; ++i) {
            while (locked.test_and_set(std::memory_order_relaxed)) {}
            ++total;
            locked.clear(std::memory_order_relaxed);
        }
    };
    std::thread a(work);
    std::thread b(work);
    a.join();
    b.join();
    std::cout << total << "\n";''', 'atomic thread'),
      'Is total protected by this lock?', 'No: relaxed operations give mutual exclusion on the flag but no happens-before for total',
      ['Yes; test_and_set is atomic', 'Yes; only one thread is ever inside'],
      'A lock must acquire on entry and release on exit. Without that, the protected writes form a data race.', check='tsan')
drill('atomic-flag-spinlock', C, 'unique_lock try_to_lock with a BasicLockable type', M(r'''
    Spinlock spin;
    std::unique_lock<Spinlock> lock(spin, std::try_to_lock);
    std::cout << lock.owns_lock() << "\n";''', 'atomic mutex', r'''
class Spinlock {
    std::atomic_flag locked_;
public:
    void lock() { while (locked_.test_and_set(std::memory_order_acquire)) {} }
    void unlock() { locked_.clear(std::memory_order_release); }
};'''),
      'Does this compile?', 'No: try_to_lock requires a try_lock member', ['Yes; it prints 1', 'Yes; it spins until locked'],
      'Spinlock is only BasicLockable. Lockable also needs try_lock, which the try_to_lock constructor calls.', check='reject', diagnostic='try_lock')
drill('atomic-flag-spinlock', O, 'test_and_set returns the previous state', M(r'''
    std::atomic_flag flag;
    std::cout << flag.test_and_set() << flag.test_and_set() << flag.test() << "\n";''', 'atomic'),
      'What does this print in C++20?', '011', ['111', '001'],
      'Since C++20 a default atomic_flag is clear. test_and_set returns the old state; test reads without modifying.')

drill('async-launch-policy', O, 'Discarding an async future', M(r'''
    std::atomic<int> step{0};
    std::async(std::launch::async, [&] {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        step = 1;
    });
    std::cout << step << "\n";''', 'atomic chrono future thread'),
      'What does this print?', '1', ['0', '0 or 1'],
      'The temporary future is destroyed at the end of the statement, and that destructor waits for the async task.')
drill('async-launch-policy', O, 'A deferred task that is never waited on', M(r'''
    bool ran = false;
    {
        auto f = std::async(std::launch::deferred, [&] { ran = true; });
    }
    std::cout << ran << "\n";''', 'future'),
      'What does this print?', '0', ['1', 'Undefined behavior'],
      'A deferred function runs only when get or wait is called. Destroying the future discards it.')
drill('async-launch-policy', O, 'Exceptions cross the future', M(r'''
    auto f = std::async(std::launch::async, []() -> int { throw std::runtime_error("boom"); });
    try {
        std::cout << f.get() << "\n";
    } catch (const std::runtime_error& e) {
        std::cout << e.what() << "\n";
    }''', 'future stdexcept'),
      'What does this print?', 'boom', ['0', 'It terminates in the worker thread'],
      'The exception is captured in the shared state and rethrown by get on the waiting thread.')

drill('packaged-task-promise', O, 'Broken promise', M(r'''
    std::future<int> f;
    {
        std::promise<int> p;
        f = p.get_future();
    }
    try {
        f.get();
    } catch (const std::future_error& e) {
        std::cout << (e.code() == std::future_errc::broken_promise) << "\n";
    }''', 'future'),
      'What does this print?', '1', ['0', 'Nothing: get blocks forever'],
      'Abandoning a shared state stores a future_error with broken_promise, which get throws.')
drill('packaged-task-promise', O, 'get consumes the future', M(r'''
    std::promise<int> p;
    auto f = p.get_future();
    p.set_value(3);
    const int v = f.get();
    std::cout << v << f.valid() << "\n";''', 'future'),
      'What does this print?', '30', ['31', '3'],
      'A std::future can be read once; get leaves it without a shared state, so valid() is false.')
drill('packaged-task-promise', O, 'Setting a value twice', M(r'''
    std::promise<int> p;
    p.set_value(1);
    try {
        p.set_value(2);
    } catch (const std::future_error& e) {
        std::cout << (e.code() == std::future_errc::promise_already_satisfied) << " " << p.get_future().get() << "\n";
    }''', 'future'),
      'What does this print?', '1 1', ['1 2', '0 1'],
      'The second set_value throws promise_already_satisfied and leaves the first value in place.')

drill('custom-awaitable', O, 'await_suspend returning false', M(r'''
    Task task = run();
    std::cout << "after\n";''', 'coroutine exception', _task('never') + r'''
struct Probe {
    bool await_ready() const noexcept { std::cout << "ready "; return false; }
    bool await_suspend(std::coroutine_handle<>) const noexcept { std::cout << "suspend "; return false; }
    void await_resume() const noexcept { std::cout << "resume "; }
};

Task run() { co_await Probe{}; }'''),
      'What does this print?', 'ready suspend resume after', ['ready suspend after', 'ready resume after'],
      'await_suspend runs after await_ready returns false; returning false resumes immediately, so await_resume runs before run returns.')
drill('custom-awaitable', C, 'An awaiter without await_resume', M(r'''
    Task task = run();''', 'coroutine exception', _task('never') + r'''
struct Incomplete {
    bool await_ready() const noexcept { return true; }
    void await_suspend(std::coroutine_handle<>) const noexcept {}
};

Task run() { co_await Incomplete{}; }'''),
      'Does this compile?', 'No: every awaiter needs await_resume', ['Yes; the co_await expression is void', 'Yes, because await_ready is true'],
      'co_await always calls await_resume to produce its result, so the member must exist even when the awaiter is ready.',
      check='reject', diagnostic='await_resume')
drill('custom-awaitable', O, 'operator co_await supplies the awaiter', M(r'''
    Task task = run();
    std::cout << "\n";''', 'coroutine exception', _task('never') + r'''
struct Ready {
    int value;
    bool await_ready() const noexcept { return true; }
    void await_suspend(std::coroutine_handle<>) const noexcept {}
    int await_resume() const noexcept { return value; }
};

struct Delay {
    int ms;
    Ready operator co_await() const { return Ready{ms * 2}; }
};

Task run() { std::cout << co_await Delay{21}; }'''),
      'What does this print?', '42', ['21', 'It does not compile: Delay has no await_ready'],
      'co_await first applies a member or free operator co_await, and the awaiter it returns supplies the result.')

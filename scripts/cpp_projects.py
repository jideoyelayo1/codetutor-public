"""Complete original CMake projects; displayed files are the validation inputs."""
from textwrap import dedent


def text(value):
    return dedent(value).strip() + '\n'


CMAKE = '''
cmake_minimum_required(VERSION 3.20)
project(cpp_guide LANGUAGES CXX)
set(CMAKE_CXX_STANDARD @STANDARD@)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
find_package(Threads REQUIRED)
option(GUIDE_ASAN "Address and undefined-behavior sanitizers" OFF)
option(GUIDE_TSAN "Thread sanitizer (separate build)" OFF)
if(GUIDE_ASAN AND GUIDE_TSAN)
  message(FATAL_ERROR "Use separate ASan and TSan builds")
endif()
add_executable(guide_demo main.cpp)
add_executable(guide_tests tests.cpp)
foreach(target guide_demo guide_tests)
  target_link_libraries(${target} PRIVATE Threads::Threads)
  target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
  if(GUIDE_ASAN)
    target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(${target} PRIVATE -fsanitize=address,undefined)
  endif()
  if(GUIDE_TSAN)
    target_compile_options(${target} PRIVATE -fsanitize=thread -fno-omit-frame-pointer)
    target_link_options(${target} PRIVATE -fsanitize=thread)
  endif()
endforeach()
enable_testing()
add_test(NAME guide_tests COMMAND guide_tests)
'''
CHECK = '''
#pragma once
#include <stdexcept>
inline void require(bool condition) {
    if (!condition) throw std::runtime_error("project check failed");
}
'''
PROJECTS = []


def project(key, title, standard, prose, header, demo, tests, prompt, answer_header, answer_tests, answer, topics, sources):
    checkpoints={
        'parser-project':('What establishes whole-token numeric parsing?', 'Both successful conversion and a stopping pointer at the end', ['A nonempty input alone','Ignoring a valid numeric prefix suffix']),
        'value-project':('How does Amount preserve its value on arithmetic overflow?', 'Check bounds before committing the new representation', ['Perform signed overflow and inspect the result','Negate every right operand first']),
        'allocator-ring-project':('What must outlive the allocator-backed Ring?', 'The memory_resource supplying its storage', ['Only the last popped element','No external object because PMR owns the resource']),
        'pipeline-project':('What is the pipeline teardown order?', 'Close and notify the queue, then join workers before releasing state', ['Destroy the queue before joining','Detach all workers and release state immediately']),
        'coroutine-project':('Who destroys this generator frame after early abandonment?', 'The single owning Generator wrapper', ['Every copied coroutine_handle automatically','The caller of value()']),
        'design-project':('What changes when adding Triangle to this closed variant?', 'The alternative set changes and clients need recompilation', ['Every unknown runtime plugin becomes supported','The existing Shape binary interface is automatically unchanged'])
    }
    question,correct,wrong=checkpoints[key]
    PROJECTS.append(dict(key=key, title=title, standard=standard, stage='10 Complete CMake projects',
        body=prose.split('|'), code='', solution='', expectedStdout='', solutionStdout='',
        challenge=prompt, practiceAnswer=answer, question=question,
        correct=correct,wrong=wrong, reasoning=answer,
        sourceURL='https://cmake.org/cmake/help/latest/guide/tutorial/index.html', sourceIDs=sources, topics=topics,
        projectFiles=[dict(path=p,content=text(c)) for p,c in [('CMakeLists.txt',CMAKE.replace('@STANDARD@',str(standard))),('check.hpp',CHECK),('lesson.hpp',header),('main.cpp',demo),('tests.cpp',tests)]],
        projectSolutionFiles=[dict(path=p,content=text(c)) for p,c in [('lesson.hpp',answer_header),('tests.cpp',answer_tests)]],
        projectInstructions='Create all files with these relative paths. Build locally with cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug, cmake --build build, then ctest --test-dir build --output-on-failure. Run build/guide_demo. Use separate build directories with -DGUIDE_ASAN=ON or -DGUIDE_TSAN=ON when supported. Replacement answer files keep the other files unchanged. The single-file mobile runner does not build this project.', minutes=75))


parser = text('''
#pragma once
#include <charconv>
#include <string_view>
#include <system_error>
#include <limits>
#include <stdexcept>
inline int parse_integer(std::string_view input) {
    int value = 0;
    auto result = std::from_chars(input.data(), input.data() + input.size(), value);
    if (result.ec != std::errc{} || result.ptr != input.data() + input.size())
        throw std::invalid_argument("expected a complete base-10 integer");
    return value;
}
inline int checked_add(int a, int b) {
    const int low = std::numeric_limits<int>::min(), high = std::numeric_limits<int>::max();
    if ((b > 0 && a > high - b) || (b < 0 && a < low - b)) throw std::overflow_error("sum overflow");
    return a + b;
}
''')
parser_tests = text('''
#include "lesson.hpp"
#include "check.hpp"
#include <string>
int main() {
    require(parse_integer("0") == 0);
    require(parse_integer("-7") == -7);
    require(parse_integer("42") == 42);
    for (auto bad : {"", " ", "+3", "2x", "999999999999999999999999999999999999999999"}) {
        bool rejected = false;
        try { (void)parse_integer(bad); } catch (const std::invalid_argument&) { rejected = true; }
        require(rejected);
    }
    require(checked_add(-3, 7) == 4);
    bool overflow = false;
    try { (void)checked_add(std::numeric_limits<int>::max(), 1); } catch (const std::overflow_error&) { overflow = true; }
    require(overflow);
}
''')
parser_answer = parser + text('''
inline int sum_line(std::string_view line) {
    int total = 0;
    while (!line.empty()) {
        auto start = line.find_first_not_of(' ');
        if (start == std::string_view::npos) break;
        line.remove_prefix(start);
        auto end = line.find(' ');
        auto token = line.substr(0, end);
        total = checked_add(total, parse_integer(token));
        if (end == std::string_view::npos) break;
        line.remove_prefix(end);
    }
    return total;
}
''')
project('parser-project','Build a checked command-line integer parser',17,
        'The CLI accepts separate base-10 integer arguments and prints their checked sum. A token must be consumed completely; whitespace and a plus sign are intentionally not accepted by the single-token grammar.|The parser separates invalid syntax from sum overflow and keeps the arithmetic within int bounds. The executable reports errors on stderr and a nonzero exit status.|The tests exercise empty input, trailing data, representational overflow, valid negative values, and addition overflow. Their require helper remains active in release builds.|The answer adds a line parser whose separator grammar is ASCII spaces. Tabs and other whitespace remain invalid rather than being silently accepted.',
        parser, '''
        #include "lesson.hpp"
        #include <iostream>
        int main(int argc, char** argv) {
            try {
                int total = 0;
                for (int i = 1; i < argc; ++i) total = checked_add(total, parse_integer(argv[i]));
                std::cout << total << "\\n";
            } catch (const std::exception& e) { std::cerr << e.what() << "\\n"; return 2; }
        }
        ''', parser_tests,
        'Add sum_line(string_view) for space-separated tokens. Accept an empty or space-only line as zero, reject malformed tokens and overflow, and keep the original CLI intact.',
        parser_answer, parser_tests.replace('\n}', '''
    require(sum_line("") == 0);
    require(sum_line("   ") == 0);
    require(sum_line(" 2 -3 7 ") == 6);
    bool bad_line = false;
    try { (void)sum_line("2 3x"); } catch (const std::invalid_argument&) { bad_line = true; }
    require(bad_line);
    bool sum_overflow = false;
    try { (void)sum_line(std::to_string(std::numeric_limits<int>::max()) + " 1"); }
    catch (const std::overflow_error&) { sum_overflow = true; }
    require(sum_overflow);
}'''),
        'Scan bounded string_view tokens without retaining views beyond the input lifetime. Require full-token conversion and use checked_add for every accumulated value; the local total is discarded if an error occurs.',
        ['parsing','CLI','from_chars','overflow'], [])

money = text('''
#pragma once
#include <cstdint>
#include <limits>
#include <stdexcept>
class Amount {
    std::int64_t cents_;
public:
    explicit Amount(std::int64_t cents) : cents_(cents) {}
    std::int64_t cents() const noexcept { return cents_; }
    Amount& operator+=(Amount other) {
        const auto a = cents_, b = other.cents_;
        const auto low = std::numeric_limits<std::int64_t>::min(), high = std::numeric_limits<std::int64_t>::max();
        if ((b > 0 && a > high - b) || (b < 0 && a < low - b)) throw std::overflow_error("amount overflow");
        cents_ = a + b;
        return *this;
    }
};
inline Amount operator+(Amount a, Amount b) { return a += b; }
inline bool operator==(Amount a, Amount b) noexcept { return a.cents() == b.cents(); }
''')
money_tests=text('''
#include "lesson.hpp"
#include "check.hpp"
int main() {
    Amount a(7), b(3);
    require(a + b == Amount(10));
    require(a == Amount(7));
    Amount high(std::numeric_limits<std::int64_t>::max());
    bool failed = false;
    try { high += Amount(1); } catch (const std::overflow_error&) { failed = true; }
    require(failed && high.cents() == std::numeric_limits<std::int64_t>::max());
    Amount low(std::numeric_limits<std::int64_t>::min());
    failed = false;
    try { low += Amount(-1); } catch (const std::overflow_error&) { failed = true; }
    require(failed && low.cents() == std::numeric_limits<std::int64_t>::min());
}
''')
money_answer=money.replace('    Amount& operator+=', '''    Amount& operator-=(Amount other) {
        const auto a = cents_, b = other.cents_;
        const auto low = std::numeric_limits<std::int64_t>::min(), high = std::numeric_limits<std::int64_t>::max();
        if ((b > 0 && a < low + b) || (b < 0 && a > high + b)) throw std::overflow_error("amount overflow");
        cents_ = a - b;
        return *this;
    }
    Amount& operator+=''') + 'inline Amount operator-(Amount a, Amount b) { return a -= b; }\n'
project('value-project','Design a checked value library',14,
        'Amount stores signed 64-bit cents as a domain value. Its explicit constructor prevents accidental mixing with unrelated scalar quantities. It is a teaching money-like value, without currency conversion or financial rounding policy.|The rule-of-zero representation delegates ordinary copy and move behavior to its integer member. Addition checks the range before changing state and supplies a nonmutating operator+ through a value copy.|Boundary checks verify the strong failure behavior: a rejected operation leaves the original Amount unchanged. Signed overflow is never used as a test oracle.|The answer implements subtraction directly rather than negating the right operand, because negating the minimum signed integer would itself overflow.',
        money, '#include "lesson.hpp"\n#include <iostream>\nint main() { std::cout << (Amount(7) + Amount(3)).cents() << "\\n"; }',money_tests,
        'Add operator-= and operator-. Preserve the left value on overflow and test subtracting the minimum representable value without first negating it.',
        money_answer,money_tests.replace('\n}', '''
    require((Amount(7) - Amount(3)) == Amount(4));
    require((Amount(-1) - Amount(std::numeric_limits<std::int64_t>::min())).cents() == std::numeric_limits<std::int64_t>::max());
    Amount zero(0); failed = false;
    try { zero -= Amount(std::numeric_limits<std::int64_t>::min()); } catch (const std::overflow_error&) { failed = true; }
    require(failed && zero.cents() == 0);
}'''), 'Check subtraction bounds before evaluating a-b. Commit the new representation only after the check succeeds, preserving value semantics and the strong failure guarantee.',
        ['value semantics','operators','exception safety'], [])

ring=text('''
#pragma once
#include <memory_resource>
#include <memory>
#include <optional>
#include <type_traits>
#include <utility>
#include <cstddef>
template<class T, std::size_t Capacity> class Ring {
    static_assert(std::is_nothrow_move_constructible_v<T> && std::is_nothrow_destructible_v<T>);
    using Alloc = std::pmr::polymorphic_allocator<T>;
    Alloc alloc_;
    T* items_;
    std::size_t head_ = 0, size_ = 0;
public:
    explicit Ring(std::pmr::memory_resource* resource) : alloc_(resource), items_(Capacity ? alloc_.allocate(Capacity) : nullptr) {}
    Ring(const Ring&) = delete;
    Ring& operator=(const Ring&) = delete;
    ~Ring() {
        for (std::size_t i = 0; i < size_; ++i) std::allocator_traits<Alloc>::destroy(alloc_, items_ + (head_ + i) % Capacity);
        if (items_) alloc_.deallocate(items_, Capacity);
    }
    std::size_t size() const noexcept { return size_; }
    template<class U> bool try_push(U&& value) {
        if (size_ == Capacity) return false;
        auto index = (head_ + size_) % Capacity;
        std::allocator_traits<Alloc>::construct(alloc_, items_ + index, std::forward<U>(value));
        ++size_;
        return true;
    }
    std::optional<T> pop() {
        if (size_ == 0) return std::nullopt;
        std::optional<T> result(std::in_place, std::move(items_[head_]));
        std::allocator_traits<Alloc>::destroy(alloc_, items_ + head_);
        head_ = (head_ + 1) % Capacity;
        --size_;
        return result;
    }
};
''')
ring_tests=text('''
#include "lesson.hpp"
#include "check.hpp"
struct Resource : std::pmr::memory_resource {
    int blocks = 0;
    void* do_allocate(std::size_t bytes, std::size_t alignment) override {
        void* p = std::pmr::new_delete_resource()->allocate(bytes, alignment); ++blocks; return p;
    }
    void do_deallocate(void* p, std::size_t bytes, std::size_t alignment) override {
        --blocks; std::pmr::new_delete_resource()->deallocate(p, bytes, alignment);
    }
    bool do_is_equal(const std::pmr::memory_resource& other) const noexcept override { return this == &other; }
};
int main() {
    Resource resource;
    {
        Ring<std::unique_ptr<int>, 2> ring(&resource);
        require(resource.blocks == 1 && !ring.pop());
        auto first = std::make_unique<int>(1), second = std::make_unique<int>(2), rejected = std::make_unique<int>(3);
        require(ring.try_push(std::move(first)) && !first);
        require(ring.try_push(std::move(second)) && !second);
        require(!ring.try_push(std::move(rejected)) && *rejected == 3);
        auto item = ring.pop(); require(item && **item == 1);
        require(ring.try_push(std::move(rejected)) && !rejected);
        require(**ring.pop() == 2);
        require(ring.size() == 1);
    }
    require(resource.blocks == 0);
    { Ring<std::unique_ptr<int>, 0> empty(&resource); auto value = std::make_unique<int>(4); require(!empty.try_push(std::move(value)) && value && !empty.pop()); }
    require(resource.blocks == 0);
}
''')
ring_answer=ring.replace('    std::size_t size()', '    const T* front() const noexcept { return size_ ? items_ + head_ : nullptr; }\n    std::size_t size()')
project('allocator-ring-project','Own a bounded generic container and its allocator',17,
        'Ring allocates storage for a fixed maximum number of elements through a caller-provided memory_resource. Only occupied positions contain live T objects. The resource must outlive the ring.|Copying and moving the container are deliberately disabled; element moves and destructors must be nonthrowing. A full insertion rejects without consuming the supplied argument, while a successful construction commits the new size.|The test uses move-only owners, wraparound, rejection, empty and zero-capacity paths, and a counting upstream resource. Remaining elements are destroyed before storage deallocation.|This is not a standard-container implementation: it has no iterators, general allocator propagation, concurrent access, or support for throwing element moves. The answer adds a const non-owning front view whose lifetime is bounded by the next invalidating operation.',
        ring,'#include "lesson.hpp"\n#include <iostream>\nint main() { Ring<int, 2> r(std::pmr::new_delete_resource()); r.try_push(7); std::cout << *r.pop() << "\\n"; }',ring_tests,
        'Add const T* front() const. Return nullptr when empty, preserve ownership, and verify that the view identifies the first element after wraparound.',
        ring_answer,ring_tests.replace('require(ring.size() == 1);','require(ring.size() == 1);\n        require(ring.front() && **ring.front() == 3);').replace('require(resource.blocks == 1 && !ring.pop());','require(resource.blocks == 1 && !ring.pop() && ring.front() == nullptr);'),
        'Return a pointer only to an actually constructed front element. The caller must not retain it across pop, destruction, or later slot reuse. The resource owns allocation policy while the ring owns element lifetimes.',
        ['allocators','PMR','generic containers','move-only ownership'], [])

pipeline=text('''
#pragma once
#include <mutex>
#include <condition_variable>
#include <queue>
#include <thread>
#include <vector>
#include <atomic>
#include <optional>
#include <stdexcept>
class Queue {
    std::mutex mutex_;
    std::condition_variable ready_;
    std::queue<int> values_;
    std::size_t capacity_;
    bool closed_ = false;
public:
    explicit Queue(std::size_t capacity) : capacity_(capacity) { if (!capacity) throw std::invalid_argument("zero capacity"); }
    bool try_push(int value) {
        { std::lock_guard lock(mutex_); if (closed_ || values_.size() == capacity_) return false; values_.push(value); }
        ready_.notify_one(); return true;
    }
    std::optional<int> pop() {
        std::unique_lock lock(mutex_);
        ready_.wait(lock, [&] { return closed_ || !values_.empty(); });
        if (values_.empty()) return std::nullopt;
        int value = values_.front(); values_.pop(); return value;
    }
    void close() { { std::lock_guard lock(mutex_); closed_ = true; } ready_.notify_all(); }
};
class Pipeline {
    Queue queue_;
    std::atomic<long long> total_{0};
    std::vector<std::jthread> workers_;
public:
    explicit Pipeline(std::size_t capacity) : queue_(capacity) {
        try { for (int i = 0; i < 2; ++i) workers_.emplace_back([this] { while (auto n = queue_.pop()) total_.fetch_add(*n, std::memory_order_relaxed); }); }
        catch (...) { queue_.close(); workers_.clear(); throw; }
    }
    Pipeline(const Pipeline&) = delete;
    Pipeline& operator=(const Pipeline&) = delete;
    ~Pipeline() { finish(); }
    bool submit(int value) { return queue_.try_push(value); }
    long long finish() { queue_.close(); workers_.clear(); return total_.load(); }
};
''')
pipeline_tests=text('''
#include "lesson.hpp"
#include "check.hpp"
int main() {
    { Queue q(2); require(q.try_push(1) && q.try_push(2) && !q.try_push(3)); q.close(); require(q.pop() == 1 && q.pop() == 2 && !q.pop() && !q.try_push(4)); }
    { Queue q(1); std::jthread waiter([&] { require(!q.pop()); }); q.close(); }
    for (int trial = 0; trial < 10; ++trial) {
        Pipeline pipeline(4);
        for (int n = 1; n <= 100; ++n) while (!pipeline.submit(n)) std::this_thread::yield();
        require(pipeline.finish() == 5050);
        require(pipeline.finish() == 5050 && !pipeline.submit(1));
    }
    { Pipeline pipeline(1); } // idle teardown must wake both waiters
    bool rejected = false; try { Queue q(0); } catch (const std::invalid_argument&) { rejected = true; }
    require(rejected);
}
''')
pipeline_answer=pipeline.replace('    void close()', '''    std::size_t pending() {
        std::lock_guard lock(mutex_); return values_.size();
    }
    void close()''')
project('pipeline-project','Drain a bounded concurrent pipeline safely',20,
        'The queue owns bounded pending integers and protects its closed state and contents with one mutex. pop waits on a state predicate; close wakes all consumers and allows queued items to drain.|Pipeline owns two workers and closes the queue before joining them. Its constructor also closes and joins partially created workers if thread construction fails, avoiding a teardown wait on an open empty queue.|finish is idempotent and rejects later submissions. Workers borrow the externally owned Pipeline only until finish joins them. Concurrent calls to finish are not supported.|Tests cover saturation without consumers, FIFO drain after close, empty waiter wakeup, repeated finish, idle destruction, and repeated parallel totals. No user callback runs on a worker, so final-owner destruction on that worker is deliberately outside this project interface.',
        pipeline,'#include "lesson.hpp"\n#include <iostream>\nint main() { Pipeline p(4); for (int n=1; n<=10; ++n) while (!p.submit(n)) std::this_thread::yield(); std::cout << p.finish() << "\\n"; }',pipeline_tests,
        'Add a synchronized pending() snapshot to Queue. Test full, partially drained, and closed/drained states without using the snapshot as a check-then-act synchronization substitute.',
        pipeline_answer,pipeline_tests.replace('q.close(); require(q.pop() == 1', 'require(q.pending() == 2); q.close(); require(q.pop() == 1').replace('!q.try_push(4));', '!q.try_push(4)); require(q.pending() == 0);'),
        'Read size under the same mutex used for modifications. The snapshot is immediately stale when other threads can modify the queue; use try_push/pop themselves to perform atomic decisions.',
        ['bounded queues','condition variables','shutdown','thread ownership'], ['hayden'])

generator=text('''
#pragma once
#include <coroutine>
#include <exception>
#include <stdexcept>
#include <utility>
class Generator {
public:
    struct promise_type;
    using Handle = std::coroutine_handle<promise_type>;
    struct promise_type {
        inline static int live = 0;
        int value = 0;
        std::exception_ptr error;
        promise_type() { ++live; }
        ~promise_type() { --live; }
        Generator get_return_object() { return Generator(Handle::from_promise(*this)); }
        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        std::suspend_always yield_value(int n) noexcept { value = n; return {}; }
        void return_void() noexcept {}
        void unhandled_exception() noexcept { error = std::current_exception(); }
    };
private:
    Handle handle_;
    bool ready_ = false;
    explicit Generator(Handle handle) : handle_(handle) {}
public:
    Generator(const Generator&) = delete;
    Generator& operator=(const Generator&) = delete;
    Generator(Generator&& other) noexcept : handle_(std::exchange(other.handle_, {})), ready_(std::exchange(other.ready_, false)) {}
    Generator& operator=(Generator&& other) noexcept {
        if (this != &other) { if (handle_) handle_.destroy(); handle_ = std::exchange(other.handle_, {}); ready_ = std::exchange(other.ready_, false); }
        return *this;
    }
    ~Generator() { if (handle_) handle_.destroy(); }
    bool next() {
        ready_ = false;
        if (!handle_ || handle_.done()) return false;
        handle_.resume();
        if (handle_.promise().error) std::rethrow_exception(handle_.promise().error);
        ready_ = !handle_.done(); return ready_;
    }
    int value() const { if (!ready_) throw std::logic_error("no current yield"); return handle_.promise().value; }
    static int live_frames() { return promise_type::live; }
};
inline Generator count_to(int end) { for (int n = 0; n < end; ++n) co_yield n; }
inline Generator fails() { co_yield 1; throw std::runtime_error("generator failed"); }
''')
generator_tests=text('''
#include "lesson.hpp"
#include "check.hpp"
int main() {
    require(Generator::live_frames() == 0);
    { auto g = count_to(3); require(g.next() && g.value() == 0); auto moved = std::move(g); require(!g.next()); require(moved.next() && moved.value() == 1); }
    require(Generator::live_frames() == 0);
    { auto g = count_to(2); require(g.next() && g.value() == 0); require(g.next() && g.value() == 1); require(!g.next() && !g.next()); bool rejected = false; try { (void)g.value(); } catch (const std::logic_error&) { rejected = true; } require(rejected); }
    { auto g = count_to(0); require(!g.next()); }
    { auto g = fails(); require(g.next() && g.value() == 1); bool failed = false; try { (void)g.next(); } catch (const std::runtime_error&) { failed = true; } require(failed); }
    { auto a = count_to(3), b = count_to(2); a = std::move(b); require(!b.next() && a.next()); }
    require(Generator::live_frames() == 0);
}
''')
project('coroutine-project','Give each coroutine frame exactly one owner',20,
        'Generator owns a suspended coroutine frame through a move-only wrapper. Its promise counts live frames, stores the current yielded int, and preserves exceptions for the next caller observation.|initial_suspend and final_suspend leave destruction to the wrapper. next refuses to resume a completed or moved-from handle, and value requires a current yield.|Early abandonment, full iteration, exception propagation, move construction, and move assignment all release frames through the same ownership path. The counters are scoped regression evidence, not a universal heap proof.|This generator is synchronous and confined to one thread. It does not implement asynchronous callback cancellation, scheduler integration, or shared concurrent resume; those require a more elaborate lifetime protocol.',
        generator,'#include "lesson.hpp"\n#include <iostream>\nint main() { auto g = count_to(3); while (g.next()) std::cout << g.value() << "\\n"; }',generator_tests,
        'Add range(first,last) with a half-open interval. Empty and reversed intervals must yield nothing; abandoning a range early must still destroy its frame.',
        generator+'inline Generator range(int first, int last) { for (int n = first; n < last; ++n) co_yield n; }\n',
        generator_tests.replace('    require(Generator::live_frames() == 0);\n}', '''    { auto g = range(3, 5); require(g.next() && g.value() == 3); require(g.next() && g.value() == 4); require(!g.next()); }
    { auto g = range(5, 3); require(!g.next()); }
    { auto g = range(1, 8); require(g.next()); }
    require(Generator::live_frames() == 0);
}'''), 'The frame owns its by-value bounds, so it borrows no caller locals. The loop stops before incrementing past last-1, and the wrapper releases the frame on every exit path.',
        ['coroutines','frame lifetime','move ownership','exception propagation'], [])

design=text('''
#pragma once
#include <variant>
#include <cstdint>
#include <stdexcept>
inline int dimension(int n) { if (n < 0 || n > 1000) throw std::invalid_argument("dimension outside 0..1000"); return n; }
struct Square { int side; explicit Square(int n) : side(dimension(n)) {} std::int64_t area() const { return std::int64_t(side) * side; } };
struct Rectangle { int width, height; Rectangle(int w, int h) : width(dimension(w)), height(dimension(h)) {} std::int64_t area() const { return std::int64_t(width) * height; } };
using Shape = std::variant<Square, Rectangle>;
inline std::int64_t area(const Shape& shape) { return std::visit([](const auto& value) { return value.area(); }, shape); }
// Comparison baseline: a closed legacy tag representation with runtime validation.
inline std::int64_t legacy_area(int kind, int first, int second) {
    if (kind == 0) return Square(first).area();
    if (kind == 1) return Rectangle(first, second).area();
    throw std::invalid_argument("unknown shape");
}
''')
design_tests=text('''
#include "lesson.hpp"
#include "check.hpp"
int main() {
    for (int n : {0, 1, 7, 1000}) require(area(Shape(Square(n))) == legacy_area(0, n, 0));
    require(area(Shape(Rectangle(3, 4))) == legacy_area(1, 3, 4));
    bool rejected = false; try { Square bad(-1); } catch (const std::invalid_argument&) { rejected = true; } require(rejected);
    rejected = false; try { Rectangle bad(1001, 1); } catch (const std::invalid_argument&) { rejected = true; } require(rejected);
    auto original = Shape(Square(3)); auto copy = original; copy = Rectangle(2, 7);
    require(area(original) == 9 && area(copy) == 14);
}
''')
design_answer=design.replace('using Shape = std::variant<Square, Rectangle>;', '''struct Triangle { int base, height; Triangle(int b, int h) : base(dimension(b)), height(dimension(h)) {} std::int64_t area() const { return std::int64_t(base) * height / 2; } };
using Shape = std::variant<Square, Rectangle, Triangle>;''')
project('design-project','Refactor a tagged API into closed value alternatives',17,
        'The legacy function encodes its type choice with an integer tag and loosely related fields. The replacement uses a variant of domain values and an external area operation.|Tests compare old and new behavior before adding another alternative. Variant gives value-copy ownership and a closed type set; it does not support adding unknown plugin types without recompilation.|The dimension guard bounds arithmetic. The public sample structs still allow later direct mutation, so callers must preserve their documented range contract; a production invariant-enforcing API should make those fields private.|The answer adds an integer-area triangle and states that odd products truncate. This is a deliberate domain choice for the exercise, not exact real-valued geometry.',
        design,'#include "lesson.hpp"\n#include <iostream>\nint main() { std::cout << area(Shape(Rectangle(3, 4))) << "\\n"; }',design_tests,
        'Add Triangle as a third value alternative. Reuse the visitor, define odd half-area truncation explicitly, and test copying, zero area, invalid dimensions, and the new alternative.',
        design_answer,design_tests.replace('\n}', '''
    require(area(Shape(Triangle(3, 3))) == 4);
    require(area(Shape(Triangle(0, 7))) == 0);
    bool bad_triangle = false; try { Triangle bad(2, -1); } catch (const std::invalid_argument&) { bad_triangle = true; }
    require(bad_triangle);
}'''), 'Add the alternative to the closed variant and provide its area member. The generic visitor still calls the same operation; extending the type set changes the variant interface and requires recompilation.',
        ['design refactor','variant','visitor','value semantics'], [])

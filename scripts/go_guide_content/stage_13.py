STAGE = '13 · Synchronisation'
SYNC = 'https://pkg.go.dev/sync'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='mutex', stage=STAGE, title='sync.Mutex and RWMutex: protecting shared state', race=True,
body=[
'A sync.Mutex makes a critical section exclusive: Lock, change shared state, Unlock. Pair them with defer mu.Unlock() right after Lock so every return path releases the lock. The zero Mutex is unlocked and ready to use.',
'Keep the mutex next to the data it protects, usually as an unexported struct field, and give the type pointer receivers: copying a struct copies its mutex, which breaks the protection. go vet\'s copylocks check reports such copies.',
'sync.RWMutex allows many concurrent readers or one writer. It helps only when reads dominate and the critical sections are long enough to matter; otherwise a plain Mutex is simpler and often faster. Go mutexes are not re-entrant: locking twice in the same goroutine deadlocks.',
],
code=r'''package main

import (
    "fmt"
    "sync"
)

type Counter struct {
    mu     sync.Mutex
    counts map[string]int
}

func (c *Counter) Inc(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.counts[key]++
}

func (c *Counter) Get(key string) int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.counts[key]
}

func main() {
    c := Counter{counts: map[string]int{}}
    var wg sync.WaitGroup
    for range 100 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            c.Inc("hits")
        }()
    }
    wg.Wait()
    fmt.Println(c.Get("hits"))
}
''',
expectedStdout='100\n',
challenge='Write a Cache type with an RWMutex-protected map, using RLock in Get and Lock in Set; set "go" to 1 from ten goroutines and print Get("go").',
solution=r'''package main

import (
    "fmt"
    "sync"
)

type Cache struct {
    mu   sync.RWMutex
    data map[string]int
}

func (c *Cache) Get(k string) int {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.data[k]
}

func (c *Cache) Set(k string, v int) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[k] = v
}

func main() {
    c := &Cache{data: map[string]int{}}
    var wg sync.WaitGroup
    for range 10 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            c.Set("go", 1)
            _ = c.Get("go")
        }()
    }
    wg.Wait()
    fmt.Println(c.Get("go"))
}
''',
solutionStdout='1\n',
question='Why must a struct containing a sync.Mutex have pointer receivers?',
correct='A value receiver copies the struct and its mutex, so methods lock different mutexes',
wrong=['Mutexes cannot be struct fields otherwise', 'Value receivers cannot call Lock'],
reasoning='Each copy has its own lock state. go vet copylocks flags copies of values containing locks.',
rejections=[dict(source='package main\n\nimport "sync"\n\ntype C struct{ mu sync.Mutex }\n\nfunc (c C) Lock() { c.mu.Lock() }\n\nfunc main() { C{}.Lock() }\n', args=['vet', '.'], diagnostic='passes lock by value')],
sourceURL=SYNC+'#Mutex'),

dict(key='waitgroup-go', stage=STAGE, title='sync.WaitGroup and WaitGroup.Go', race=True,
body=[
'A WaitGroup waits for a collection of goroutines. The classic pattern is wg.Add(1) before go, defer wg.Done() inside, and wg.Wait() in the owner. Add must happen before Wait could return, which is why it is called in the starting goroutine rather than inside the new one.',
'Go 1.25 added wg.Go(f): it calls Add(1), starts f in a goroutine and calls Done when f returns. It removes the most common WaitGroup mistakes, forgetting Done or calling Add inside the goroutine. Go 1.27 renames the go fix modernizer that rewrites old patterns to waitgroupgo.',
'The return of each function started by Go synchronises before Wait returns, so results written by the goroutines are visible after Wait. f must not panic; recover inside f if it can.',
],
code=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup
    squares := make([]int, 4)
    for i := range squares {
        wg.Go(func() {
            squares[i] = i * i
        })
    }
    wg.Wait()
    fmt.Println(squares)
}
''',
expectedStdout='[0 1 4 9]\n',
challenge='Use wg.Go to compute the lengths of four words concurrently into a slice, then print the slice and its sum.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    words := []string{"wait", "group", "go", "!"}
    lengths := make([]int, len(words))
    var wg sync.WaitGroup
    for i, w := range words {
        wg.Go(func() { lengths[i] = len(w) })
    }
    wg.Wait()
    sum := 0
    for _, n := range lengths {
        sum += n
    }
    fmt.Println(lengths, sum)
}
''',
solutionStdout='[4 5 2 1] 12\n',
question='Why must wg.Add(1) run before the go statement rather than inside the goroutine?',
correct='Otherwise Wait might run while the counter is still zero and return too early',
wrong=['Add panics when called from a new goroutine', 'The goroutine cannot access wg'],
reasoning='If the goroutine has not started yet, its Add has not happened and Wait sees zero. wg.Go performs Add before starting the goroutine.',
sourceURL=SYNC+'#WaitGroup.Go',
additionalReadings=[dict(title='Go 1.25 release notes: sync', url='https://go.dev/doc/go1.25#sync', section='WaitGroup.Go')]),

dict(key='once', stage=STAGE, title='sync.Once, OnceFunc, OnceValue and lazy initialisation', race=True,
body=[
'sync.Once runs a function exactly once, however many goroutines call Do, and every caller returns only after it has finished. It is the safe way to initialise something lazily, such as a configuration or a compiled regular expression.',
'Go 1.21 added helpers: sync.OnceFunc(f) returns a function that runs f once, sync.OnceValue(f) caches one result, and sync.OnceValues(f) caches a (value, error) pair. If f panics, every call re-panics with the same value.',
'Prefer package-level variable initialisation when the value is always needed; use Once when initialisation is expensive or may not be needed at all.',
],
code=r'''package main

import (
    "fmt"
    "strings"
    "sync"
)

var calls int

var config = sync.OnceValue(func() map[string]string {
    calls++
    return map[string]string{"mode": "fast"}
})

func main() {
    var wg sync.WaitGroup
    for range 10 {
        wg.Go(func() { _ = config()["mode"] })
    }
    wg.Wait()
    fmt.Println(config()["mode"], calls)
    load := sync.OnceValues(func() (string, error) {
        return strings.ToUpper("loaded"), nil
    })
    v, err := load()
    fmt.Println(v, err)
}
''',
expectedStdout='fast 1\nLOADED <nil>\n',
challenge='Use sync.OnceFunc to make a cleanup function that prints "closed" once, call it three times, and print "done".',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    closeOnce := sync.OnceFunc(func() { fmt.Println("closed") })
    closeOnce()
    closeOnce()
    closeOnce()
    fmt.Println("done")
}
''',
solutionStdout='closed\ndone\n',
question='What happens if the function passed to OnceValue panics?',
correct='Every call, including later ones, panics with the same value',
wrong=['The next call retries the function', 'The panic is swallowed and zero is returned'],
reasoning='The Once helpers remember the panic and re-raise it, so a failed initialisation is never silently retried or ignored.',
sourceURL=SYNC+'#OnceValue'),

dict(key='cond', stage=STAGE, title='sync.Cond for waiting on state changes', race=True,
body=[
'A sync.Cond lets goroutines wait until some condition on shared state holds. Each Cond is tied to a Locker. Waiters hold the lock, check the condition in a for loop and call Wait, which atomically unlocks, sleeps and relocks when woken.',
'Signal wakes one waiter and Broadcast wakes all. Always re-check the condition after Wait returns: another goroutine may have changed the state first, and spurious wake-ups are allowed.',
'Channels usually express the same thing more simply. Cond is useful when many goroutines wait for a condition on data already protected by a mutex, such as a bounded queue with "not empty" and "not full" states.',
],
code=r'''package main

import (
    "fmt"
    "sync"
)

type Queue struct {
    mu    sync.Mutex
    ready *sync.Cond
    items []int
}

func NewQueue() *Queue {
    q := &Queue{}
    q.ready = sync.NewCond(&q.mu)
    return q
}

func (q *Queue) Put(v int) {
    q.mu.Lock()
    q.items = append(q.items, v)
    q.mu.Unlock()
    q.ready.Signal()
}

func (q *Queue) Take() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    for len(q.items) == 0 {
        q.ready.Wait()
    }
    v := q.items[0]
    q.items = q.items[1:]
    return v
}

func main() {
    q := NewQueue()
    var wg sync.WaitGroup
    sums := make([]int, 2)
    for i := range 2 {
        wg.Go(func() { sums[i] = q.Take() + q.Take() })
    }
    for v := range 4 {
        q.Put(v + 1)
    }
    wg.Wait()
    fmt.Println(sums[0] + sums[1])
}
''',
expectedStdout='10\n',
challenge='Build a gate: five goroutines wait on a Cond until open becomes true; main sets open under the lock and calls Broadcast. Print how many goroutines passed.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    var mu sync.Mutex
    gate := sync.NewCond(&mu)
    open, passed := false, 0
    var wg sync.WaitGroup
    for range 5 {
        wg.Go(func() {
            mu.Lock()
            defer mu.Unlock()
            for !open {
                gate.Wait()
            }
            passed++
        })
    }
    mu.Lock()
    open = true
    mu.Unlock()
    gate.Broadcast()
    wg.Wait()
    fmt.Println(passed)
}
''',
solutionStdout='5\n',
question='Why is Cond.Wait always called inside a for loop?',
correct='The condition may be false again by the time the waiter relocks',
wrong=['Wait returns immediately the first time', 'A for loop is required by the compiler'],
reasoning='Another goroutine can change the state between Signal and the waiter reacquiring the lock, so the condition must be rechecked.',
sourceURL=SYNC+'#Cond'),

dict(key='atomics', stage=STAGE, title='Typed atomics: atomic.Int64, Bool and Pointer', race=True,
body=[
'sync/atomic performs indivisible operations on single words. The typed values added in Go 1.19, atomic.Int32, Int64, Uint64, Bool and Pointer[T], cannot be accessed non-atomically by mistake and are correctly aligned automatically. Go 1.27\'s go fix atomictypes modernizer rewrites older atomic.AddInt64(&x, 1) code to them.',
'Load, Store, Add, Swap and CompareAndSwap are sequentially consistent in Go: all goroutines observe atomic operations in a single order, and an atomic write synchronises with the atomic read that observes it.',
'Atomics suit counters, flags and publishing an immutable snapshot through atomic.Pointer. When an update touches several values together, use a mutex; combining several atomics does not make the group atomic.',
],
code=r'''package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

type Config struct{ Version int }

func main() {
    var hits atomic.Int64
    var wg sync.WaitGroup
    for range 50 {
        wg.Go(func() { hits.Add(2) })
    }
    wg.Wait()
    fmt.Println(hits.Load())
    var current atomic.Pointer[Config]
    current.Store(&Config{Version: 1})
    old := current.Swap(&Config{Version: 2})
    fmt.Println(old.Version, current.Load().Version)
    var ready atomic.Bool
    fmt.Println(ready.CompareAndSwap(false, true), ready.CompareAndSwap(false, true))
}
''',
expectedStdout='100\n1 2\ntrue false\n',
challenge='Write func maxUpdate(m *atomic.Int64, v int64) that raises m to v only if v is larger, using a CompareAndSwap loop; update from goroutines with values 0..99 and print the result.',
solution=r'''package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func maxUpdate(m *atomic.Int64, v int64) {
    for {
        old := m.Load()
        if v <= old || m.CompareAndSwap(old, v) {
            return
        }
    }
}

func main() {
    var m atomic.Int64
    var wg sync.WaitGroup
    for i := range 100 {
        wg.Go(func() { maxUpdate(&m, int64(i)) })
    }
    wg.Wait()
    fmt.Println(m.Load())
}
''',
solutionStdout='99\n',
question='When is a mutex better than several atomics?',
correct='When several values must change together as one consistent update',
wrong=['Never; atomics are always faster', 'Only for integers larger than 64 bits'],
reasoning='Each atomic operation is individually atomic, but other goroutines can observe states between them. A mutex makes the whole update indivisible.',
sourceURL='https://pkg.go.dev/sync/atomic'),

dict(key='sync-map-pool', stage=STAGE, title='sync.Map and sync.Pool: specialised tools', race=True,
body=[
'sync.Map is a concurrent map optimised for two cases: keys written once and read many times, and goroutines working on disjoint keys. For most code a plain map with a Mutex is clearer and type-safe. Its methods include Load, Store, LoadOrStore, CompareAndSwap, Delete and Range.',
'sync.Pool caches temporary objects to reduce allocation, for example buffers reused across requests. The pool may drop items at any garbage collection, so it is a cache, not a free list with guaranteed reuse. Reset objects before putting them back, and do not store objects that hold onto large memory.',
'Both are tools for measured hot spots. Benchmark first; a Pool adds complexity and can retain memory you expected to be freed.',
],
code=r'''package main

import (
    "bytes"
    "fmt"
    "sync"
)

var buffers = sync.Pool{New: func() any { return new(bytes.Buffer) }}

func render(name string) string {
    b := buffers.Get().(*bytes.Buffer)
    defer func() {
        b.Reset()
        buffers.Put(b)
    }()
    fmt.Fprintf(b, "<p>%s</p>", name)
    return b.String()
}

func main() {
    fmt.Println(render("pool"))
    var m sync.Map
    v, loaded := m.LoadOrStore("lang", "go")
    fmt.Println(v, loaded)
    v, loaded = m.LoadOrStore("lang", "rust")
    fmt.Println(v, loaded)
}
''',
expectedStdout='<p>pool</p>\ngo false\ngo true\n',
challenge='Use a sync.Map from ten goroutines so each stores its index under key i%3, then count the keys with Range and print the count.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    var m sync.Map
    var wg sync.WaitGroup
    for i := range 10 {
        wg.Go(func() { m.Store(i%3, i) })
    }
    wg.Wait()
    keys := 0
    m.Range(func(k, v any) bool {
        keys++
        return true
    })
    fmt.Println(keys)
}
''',
solutionStdout='3\n',
question='What must you assume about objects put into a sync.Pool?',
correct='They may be discarded at any garbage collection',
wrong=['They are kept until the program exits', 'Get always returns the most recent Put'],
reasoning='Pool contents are weakly held per-P caches cleared over GC cycles. New must be able to recreate any object.',
sourceURL=SYNC+'#Pool'),

dict(key='race-detector', stage=STAGE, title='Finding data races with the race detector',
body=[
'A data race is two goroutines accessing the same variable concurrently, at least one writing, without synchronisation. Racy Go programs have undefined results: torn values, lost updates and, for maps and interfaces, crashes.',
'Build or test with -race (go test -race ./..., go run -race .) and the runtime instruments every memory access. When two unsynchronised accesses happen, it prints WARNING: DATA RACE with both stacks and makes the test fail. It finds races that actually occur during the run, so run it on tests that exercise concurrency.',
'The detector costs roughly 5–10x CPU and memory, so use it in CI and staging rather than production. It needs cgo on most platforms; this project runs it on macOS.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/stats\n\ngo 1.27\n'),
f('stats.go', r'''// Package stats counts events.
package stats

import "sync"

// Counter counts events from many goroutines.
type Counter struct {
    n int
}

// Inc adds one.
func (c *Counter) Inc() { c.n++ }

// Value returns the count.
func (c *Counter) Value() int { return c.n }

// IncMany increments from k goroutines and waits for them.
func IncMany(c *Counter, k int) {
    var wg sync.WaitGroup
    for range k {
        wg.Go(c.Inc)
    }
    wg.Wait()
}
'''),
f('stats_test.go', r'''package stats

import "testing"

func TestIncMany(t *testing.T) {
    var c Counter
    IncMany(&c, 50)
    if c.Value() != 50 {
        t.Fatalf("Value = %d, want 50", c.Value())
    }
}
'''),
],
projectSolutionFiles=[f('stats.go', r'''// Package stats counts events.
package stats

import (
    "sync"
    "sync/atomic"
)

// Counter counts events from many goroutines.
type Counter struct {
    n atomic.Int64
}

// Inc adds one.
func (c *Counter) Inc() { c.n.Add(1) }

// Value returns the count.
func (c *Counter) Value() int { return int(c.n.Load()) }

// IncMany increments from k goroutines and waits for them.
func IncMany(c *Counter, k int) {
    var wg sync.WaitGroup
    for range k {
        wg.Go(c.Inc)
    }
    wg.Wait()
}
''')],
projectInstructions='Go 1.27 with cgo (the race detector needs it on macOS). Run:\ngo test -race ./...\nThe test may even pass without -race, but the detector reports WARNING: DATA RACE on c.n++ and fails the run.\nPractice: make Counter safe with atomic.Int64. Replace stats.go with the worked answer and rerun go test -race.',
projectChecks=[
dict(name='race detector reports the unsynchronised increment', args=['test', '-race', '-count=1', './...'], exit=1, timeout=240, outputContains=['WARNING: DATA RACE', 'race detected during execution of test']),
dict(name='answer is race-free', args=['test', '-race', '-count=1', './...'], useSolution=True, timeout=240, outputContains=['ok']),
],
challenge='Fix Counter so that go test -race passes, using atomic.Int64 instead of a plain int.',
question='What does the race detector guarantee about a passing run?',
correct='No race occurred on the paths that run executed',
wrong=['The program can never race', 'Every goroutine was joined'],
reasoning='The detector is dynamic: it reports races it observes. Code paths not exercised by the run are not checked.',
sourceURL='https://go.dev/doc/articles/race_detector'),
]

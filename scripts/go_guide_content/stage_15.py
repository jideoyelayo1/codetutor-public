STAGE = '15 · Runtime and performance'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='escape-analysis', stage=STAGE, title='Stack, heap and escape analysis',
body=[
'Go decides where each variable lives. If the compiler can prove a variable is not referenced after its function returns, it stays on the goroutine\'s stack and costs nothing to free. Otherwise it "escapes" to the heap and the garbage collector must reclaim it later.',
'Common causes of escape: returning a pointer to a local, storing a pointer in a heap object or global, converting a value to an interface that is retained, closures that outlive their function, and slices whose size is not known at compile time. go build -gcflags=-m prints the decisions; repeat -m for more detail.',
'Escape is not wrong; it is how Go makes pointers safe. Look at it only for hot paths, after a profile shows allocation cost. Returning a value instead of a pointer, or letting callers pass a buffer, often removes allocations.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/esc\n\ngo 1.27\n'),
f('esc.go', r'''// Package esc shows escape-analysis decisions.
package esc

// Point is a small value type.
type Point struct{ X, Y int }

// NewPoint returns a pointer, so the Point escapes to the heap.
func NewPoint(x, y int) *Point {
    p := Point{x, y}
    return &p
}

// SumLocal keeps its Point on the stack.
func SumLocal(x, y int) int {
    p := Point{x, y}
    return p.X + p.Y
}
'''),
f('esc_test.go', r'''package esc

import "testing"

func TestAllocations(t *testing.T) {
    if n := testing.AllocsPerRun(100, func() { _ = SumLocal(1, 2) }); n != 0 {
        t.Errorf("SumLocal allocates %v times", n)
    }
    var sink *Point
    if n := testing.AllocsPerRun(100, func() { sink = NewPoint(1, 2) }); n != 1 {
        t.Errorf("NewPoint allocates %v times", n)
    }
    _ = sink
}
'''),
],
projectSolutionFiles=[f('esc.go', r'''// Package esc shows escape-analysis decisions.
package esc

// Point is a small value type.
type Point struct{ X, Y int }

// NewPoint returns a pointer, so the Point escapes to the heap.
func NewPoint(x, y int) *Point {
    p := Point{x, y}
    return &p
}

// MakePoint returns a value, which callers can keep on their stack.
func MakePoint(x, y int) Point { return Point{x, y} }

// SumLocal keeps its Point on the stack.
func SumLocal(x, y int) int {
    p := Point{x, y}
    return p.X + p.Y
}
'''), f('value_test.go', r'''package esc

import "testing"

func TestMakePointDoesNotAllocate(t *testing.T) {
    var sink Point
    if n := testing.AllocsPerRun(100, func() { sink = MakePoint(1, 2) }); n != 0 {
        t.Errorf("MakePoint allocates %v times", n)
    }
    _ = sink
}
''')],
projectInstructions='Go 1.27. Run:\ngo build -gcflags=-m ./...\ngo test ./...\nThe compiler reports "moved to heap: p" for NewPoint. The test confirms 1 allocation for NewPoint and 0 for SumLocal.\nPractice: add MakePoint returning a Point value, and a test that it allocates nothing. Replace esc.go and add value_test.go from the worked answer.',
projectChecks=[
dict(name='compiler explains escape', args=['build', '-gcflags=-m', './...'], outputContains=['moved to heap: p']),
dict(name='allocation counts', args=['test', '-count=1', './...'], outputContains=['ok']),
dict(name='answer value return stays on stack', args=['test', '-count=1', '-run', 'TestMakePointDoesNotAllocate', '-v', './...'], useSolution=True, outputContains=['--- PASS: TestMakePointDoesNotAllocate']),
],
challenge='Add MakePoint(x, y int) Point that returns a value and a test proving it allocates nothing.',
question='Why does p escape in NewPoint?',
correct='Its address is returned, so it must outlive the function',
wrong=['Structs are always heap-allocated', 'The function has two parameters'],
reasoning='The stack frame disappears when NewPoint returns, so a pointer to p must point into the heap.',
sourceURL='https://go.dev/doc/faq#stack_or_heap',
additionalReadings=[dict(title='Go GC guide: eliminating heap allocations', url='https://go.dev/doc/gc-guide#Eliminating_heap_allocations', section='Escape analysis')]),

dict(key='garbage-collector', stage=STAGE, title='The garbage collector, GOGC, GOMEMLIMIT and Green Tea',
body=[
'Go\'s garbage collector is concurrent and non-moving: it marks reachable objects while the program runs and sweeps the rest, with short stop-the-world pauses. Go 1.26 made the Green Tea collector the default; it scans memory span by span for better locality, reducing GC CPU cost by 10–40% in many programs.',
'GOGC (default 100) sets how much the heap may grow over the live heap before the next collection: 100 means the heap can double. Lower values use less memory and more CPU; GOGC=off disables collection. debug.SetGCPercent changes it at run time and returns the old value.',
'GOMEMLIMIT (Go 1.19) sets a soft memory limit for the whole runtime, such as GOMEMLIMIT=512MiB. The GC works harder as the limit approaches, which suits containers with fixed memory. runtime.ReadMemStats and runtime/metrics report heap size and GC counts.',
],
code=r'''package main

import (
    "fmt"
    "runtime"
    "runtime/debug"
)

var keep [][]byte

func main() {
    old := debug.SetGCPercent(50)
    fmt.Println("previous GOGC:", old)
    debug.SetGCPercent(old)
    limit := debug.SetMemoryLimit(-1)
    fmt.Println("default limit is effectively unlimited:", limit > 1<<60)
    var before, after runtime.MemStats
    runtime.ReadMemStats(&before)
    for range 1000 {
        keep = append(keep, make([]byte, 1024))
    }
    keep = nil
    runtime.GC()
    runtime.ReadMemStats(&after)
    fmt.Println("collections ran:", after.NumGC > before.NumGC)
    fmt.Println("allocated at least 1 MB:", after.TotalAlloc-before.TotalAlloc >= 1000*1024)
}
''',
expectedStdout='previous GOGC: 100\ndefault limit is effectively unlimited: true\ncollections ran: true\nallocated at least 1 MB: true\n',
challenge='Read the "/gc/cycles/total:gc-cycles" metric with runtime/metrics before and after calling runtime.GC() twice, and print whether it increased by at least 2.',
solution=r'''package main

import (
    "fmt"
    "runtime"
    "runtime/metrics"
)

func cycles() uint64 {
    s := []metrics.Sample{{Name: "/gc/cycles/total:gc-cycles"}}
    metrics.Read(s)
    return s[0].Value.Uint64()
}

func main() {
    before := cycles()
    runtime.GC()
    runtime.GC()
    fmt.Println(cycles()-before >= 2)
}
''',
solutionStdout='true\n',
question='What does GOGC=100 mean?',
correct='The heap may grow to about twice the live heap before the next collection',
wrong=['The GC runs every 100 milliseconds', 'The program may use at most 100 MB'],
reasoning='GOGC is a growth percentage relative to the live heap after the last cycle. GOMEMLIMIT is the absolute limit.',
sourceURL='https://go.dev/doc/gc-guide',
additionalReadings=[dict(title='Go 1.26 release notes: Green Tea GC', url='https://go.dev/doc/go1.26#runtime', section='Green Tea garbage collector')]),

dict(key='gomaxprocs', stage=STAGE, title='GOMAXPROCS and container-aware scheduling',
body=[
'GOMAXPROCS is the number of Ps, so the maximum number of goroutines executing Go code at the same instant. Goroutines blocked in system calls do not count. runtime.GOMAXPROCS(0) reads it without changing it, and runtime.NumCPU reports logical CPUs.',
'Since Go 1.25, on Linux the default respects the cgroup CPU limit of a container: a pod limited to 2 CPUs on a 64-core machine gets GOMAXPROCS=2, and the runtime updates it if the limit changes. Before 1.25 it used the host CPU count, which caused heavy throttling.',
'Setting the GOMAXPROCS environment variable, or calling runtime.GOMAXPROCS with a positive value, disables the automatic adjustment. runtime.SetDefaultGOMAXPROCS (1.25) restores it.',
],
code=r'''package main

import (
    "fmt"
    "runtime"
)

func main() {
    procs := runtime.GOMAXPROCS(0)
    fmt.Println(procs >= 1, procs <= runtime.NumCPU())
    old := runtime.GOMAXPROCS(1)
    fmt.Println(runtime.GOMAXPROCS(0))
    runtime.GOMAXPROCS(old)
    runtime.SetDefaultGOMAXPROCS()
    fmt.Println(runtime.GOMAXPROCS(0) == procs)
}
''',
expectedStdout='true true\n1\ntrue\n',
challenge='Print runtime.NumGoroutine before and after starting three goroutines that block on a channel, then release them and wait.',
solution=r'''package main

import (
    "fmt"
    "runtime"
    "sync"
)

func main() {
    before := runtime.NumGoroutine()
    release := make(chan struct{})
    var wg sync.WaitGroup
    for range 3 {
        wg.Go(func() { <-release })
    }
    fmt.Println(runtime.NumGoroutine() - before)
    close(release)
    wg.Wait()
}
''',
solutionStdout='3\n',
question='How does Go 1.25+ choose the default GOMAXPROCS inside a Linux container with a CPU limit?',
correct='It uses the cgroup CPU limit rather than the host\'s CPU count',
wrong=['It always uses 1 in containers', 'It uses the host CPU count, as before'],
reasoning='Container-aware GOMAXPROCS avoids running more parallel threads than the quota allows, which reduces throttling and tail latency.',
sourceURL='https://go.dev/doc/go1.25#container-aware-gomaxprocs'),

dict(key='pprof-profiles', stage=STAGE, title='Profiling CPU and memory with pprof',
body=[
'Profiles show where a program spends time or allocates memory. go test -cpuprofile=cpu.out and -memprofile=mem.out profile tests and benchmarks; a running service exposes /debug/pprof/ by importing net/http/pprof; runtime/pprof writes profiles from any program.',
'go tool pprof reads them: -top lists the heaviest functions, -list=Func annotates source lines, and -http=:8080 opens a web UI with flame graphs. For memory, -sample_index=alloc_space shows total bytes allocated and inuse_space shows live bytes at the moment of the profile.',
'Profile first, then optimise the largest cost. Allocation profiles are often more revealing than CPU profiles, because allocation also costs GC time later. Setting -memprofilerate=1 records every allocation, which is exact but slow, so use it only in focused tests like this one.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/report\n\ngo 1.27\n'),
f('report.go', r'''// Package report builds text reports.
package report

import "strconv"

// Lines renders one line per value using repeated concatenation.
func Lines(values []int) string {
    out := ""
    for _, v := range values {
        out += "value=" + strconv.Itoa(v) + "\n"
    }
    return out
}
'''),
f('report_test.go', r'''package report

import "testing"

var values = func() []int {
    v := make([]int, 200)
    for i := range v {
        v[i] = i
    }
    return v
}()

func BenchmarkLines(b *testing.B) {
    b.ReportAllocs()
    for b.Loop() {
        Lines(values)
    }
}
'''),
],
projectSolutionFiles=[f('report.go', r'''// Package report builds text reports.
package report

import "strconv"

// Lines renders one line per value into a single growing buffer.
func Lines(values []int) string {
    buf := make([]byte, 0, len(values)*12)
    for _, v := range values {
        buf = append(buf, "value="...)
        buf = strconv.AppendInt(buf, int64(v), 10)
        buf = append(buf, '\n')
    }
    return string(buf)
}
''')],
projectInstructions='Go 1.27. Collect an exact allocation profile, then inspect it:\ngo test -run=^$ -bench=. -benchtime=50x -memprofile=mem.out -memprofilerate=1 .\ngo tool pprof -sample_index=alloc_space -top mem.out\nLines dominates the allocation profile because each += copies the whole string.\nPractice: rewrite Lines to append into one pre-sized []byte with strconv.AppendInt. Replace report.go with the worked answer; allocs/op falls from hundreds to two.',
projectChecks=[
dict(name='collect allocation profile', args=['test', '-run=^$', '-bench=.', '-benchtime=50x', '-memprofile=mem.out', '-memprofilerate=1', '.'], outputContains=['BenchmarkLines', 'allocs/op']),
dict(name='pprof attributes allocations to Lines', args=['tool', 'pprof', '-sample_index=alloc_space', '-top', 'mem.out'], outputContains=['report.Lines']),
dict(name='answer allocates twice per call', args=['test', '-run=^$', '-bench=.', '-benchtime=50x', '.'], useSolution=True, outputContains=['2 allocs/op']),
],
challenge='Rewrite Lines to build the report in one pre-sized []byte with strconv.AppendInt, cutting allocations per call to two.',
question='Which pprof sample index shows total bytes allocated over the run, including freed memory?',
correct='alloc_space',
wrong=['inuse_space', 'cpu'],
reasoning='alloc_space accumulates every allocation; inuse_space shows only what was still live when the profile was written.',
sourceURL='https://go.dev/doc/diagnostics#profiling',
additionalReadings=[dict(title='Profiling Go programs', url='https://go.dev/blog/pprof', section='pprof')]),

dict(key='tracing-flight-recorder', stage=STAGE, title='Execution traces, regions and the flight recorder',
body=[
'An execution trace records scheduler events, goroutine creation and blocking, system calls, GC phases and user annotations with nanosecond timestamps. trace.Start(w) and trace.Stop() capture one, go test -trace=trace.out does so for tests, and go tool trace trace.out opens a timeline viewer. Since Go 1.27 the viewer listens only on localhost by default.',
'Annotate with trace.NewTask, trace.WithRegion and trace.Log so the viewer groups work by request. Traces explain latency that profiles average away, such as a goroutine waiting for a lock or a GC pause in the middle of a request.',
'Go 1.25 added trace.FlightRecorder: it keeps the last few seconds of trace data in a ring buffer with low overhead. When something unusual happens, such as a slow request, call WriteTo to save just that recent window. This makes tracing practical in production.',
],
code=r'''package main

import (
    "bytes"
    "context"
    "fmt"
    "runtime/trace"
    "time"
)

func handle(ctx context.Context) {
    ctx, task := trace.NewTask(ctx, "request")
    defer task.End()
    trace.WithRegion(ctx, "work", func() {
        time.Sleep(2 * time.Millisecond)
    })
    trace.Log(ctx, "result", "ok")
}

func main() {
    fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{MinAge: time.Second, MaxBytes: 1 << 20})
    if err := fr.Start(); err != nil {
        fmt.Println(err)
        return
    }
    defer fr.Stop()
    fmt.Println("recording:", fr.Enabled(), trace.IsEnabled())
    start := time.Now()
    handle(context.Background())
    if time.Since(start) > time.Millisecond {
        var snapshot bytes.Buffer
        n, err := fr.WriteTo(&snapshot)
        fmt.Println("snapshot saved:", n > 0, err)
    }
}
''',
expectedStdout='recording: true true\nsnapshot saved: true <nil>\n',
challenge='Write a complete trace of a function that starts two goroutines into a bytes.Buffer with trace.Start/Stop, and print whether any bytes were written.',
solution=r'''package main

import (
    "bytes"
    "fmt"
    "runtime/trace"
    "sync"
)

func main() {
    var buf bytes.Buffer
    if err := trace.Start(&buf); err != nil {
        fmt.Println(err)
        return
    }
    var wg sync.WaitGroup
    for range 2 {
        wg.Go(func() {})
    }
    wg.Wait()
    trace.Stop()
    fmt.Println(buf.Len() > 0)
}
''',
solutionStdout='true\n',
question='What problem does trace.FlightRecorder solve?',
correct='It keeps a cheap rolling window so you can save a trace of what just happened',
wrong=['It replaces CPU profiling', 'It records traces only for the race detector'],
reasoning='Full tracing of a long-running service is expensive and huge. A flight recorder captures the recent past on demand, when an anomaly is detected.',
sourceURL='https://pkg.go.dev/runtime/trace#FlightRecorder',
additionalReadings=[dict(title='Flight recording in Go 1.25', url='https://go.dev/blog/flight-recorder', section='Flight recorder')]),

dict(key='benchmark-method', stage=STAGE, title='Benchmarking method: variance, benchstat and fair comparisons',
body=[
'One benchmark run is an anecdote. Run each variant several times with -count=10, on a quiet machine, and compare the distributions. benchstat (golang.org/x/perf/cmd/benchstat) reports means, variation and whether a difference is statistically significant.',
'Guard against measuring the wrong thing: keep setup outside the b.Loop body, make inputs realistic in size, avoid benchmarks whose result the compiler can discard (b.Loop helps), and check allocations as well as time.',
'testing.AllocsPerRun and the allocs/op column are stable across machines, which makes them good regression tests. Wall-clock numbers vary with CPU, frequency scaling and other processes, so they belong in reports rather than pass/fail tests.',
],
code=r'''package main

import (
    "fmt"
    "strings"
    "testing"
)

func joinPlus(parts []string) string {
    s := ""
    for _, p := range parts {
        s += p
    }
    return s
}

func main() {
    parts := strings.Fields("a b c d e f g h")
    plus := testing.AllocsPerRun(50, func() { _ = joinPlus(parts) })
    join := testing.AllocsPerRun(50, func() { _ = strings.Join(parts, "") })
    fmt.Println(plus > join, join)
    r := testing.Benchmark(func(b *testing.B) {
        for b.Loop() {
            _ = strings.Join(parts, "")
        }
    })
    fmt.Println(r.N > 0, r.AllocsPerOp())
}
''',
expectedStdout='true 1\ntrue 1\n',
challenge='Use testing.AllocsPerRun to show that strings.Builder with Grow allocates exactly once when joining eight one-letter strings.',
solution=r'''package main

import (
    "fmt"
    "strings"
    "testing"
)

func main() {
    parts := strings.Fields("a b c d e f g h")
    n := testing.AllocsPerRun(50, func() {
        var b strings.Builder
        b.Grow(len(parts))
        for _, p := range parts {
            b.WriteString(p)
        }
        _ = b.String()
    })
    fmt.Println(n)
}
''',
solutionStdout='1\n',
question='Why are allocation counts better than nanoseconds for a CI regression test?',
correct='They are deterministic across machines, while timings vary with hardware and load',
wrong=['Nanoseconds cannot be measured in tests', 'Allocations are the only cost that matters'],
reasoning='Allocs per op depends on the code, not the machine. Timings need repeated runs and statistics to compare fairly.',
sourceURL='https://pkg.go.dev/golang.org/x/perf/cmd/benchstat',
additionalReadings=[dict(title='testing.Benchmark', url='https://pkg.go.dev/testing#Benchmark', section='Benchmark')]),

dict(key='pgo', stage=STAGE, title='Profile-guided optimisation',
body=[
'Profile-guided optimisation (PGO, Go 1.21) feeds a CPU profile from representative runs back into the compiler, which then inlines and devirtualises hot calls more aggressively. Typical gains are 2–14% CPU.',
'Put the profile in the main package directory as default.pgo and go build uses it automatically (-pgo=auto is the default). -pgo=off disables it and -pgo=path selects another file. The binary records the setting, visible with go version -m.',
'Profiles from production are best; profiles from benchmarks work if they exercise the same hot paths. Commit default.pgo and refresh it periodically. Builds stay reproducible because the profile is a normal input.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/pgo\n\ngo 1.27\n'),
f('main.go', r'''// Command pgo hashes words; it is a small target for profile-guided optimisation.
package main

import (
    "fmt"
    "hash/fnv"
)

func hash(s string) uint32 {
    h := fnv.New32a()
    h.Write([]byte(s))
    return h.Sum32()
}

func main() {
    var total uint32
    for i := range 1000 {
        total += hash(fmt.Sprint("word", i))
    }
    fmt.Println(total > 0)
}
'''),
f('main_test.go', r'''package main

import "testing"

func BenchmarkHash(b *testing.B) {
    for b.Loop() {
        hash("profile-guided optimisation")
    }
}
'''),
],
projectSolutionFiles=[f('main_test.go', r'''package main

import (
    "fmt"
    "testing"
)

func BenchmarkHash(b *testing.B) {
    for b.Loop() {
        hash("profile-guided optimisation")
    }
}

func BenchmarkMain(b *testing.B) {
    words := make([]string, 1000)
    for i := range words {
        words[i] = fmt.Sprint("word", i)
    }
    for b.Loop() {
        var total uint32
        for _, w := range words {
            total += hash(w)
        }
        _ = total
    }
}
''')],
projectInstructions='Go 1.27. Collect a CPU profile into default.pgo, then build with it:\ngo test -run=^$ -bench=. -benchtime=20000x -cpuprofile=default.pgo .\ngo build -o app .\ngo version -m app\nThe build information shows -pgo=…/default.pgo. Build again with -pgo=off to compare.\nPractice: add a benchmark that mirrors main\'s real workload so the profile reflects production. Replace main_test.go with the worked answer.',
projectChecks=[
dict(name='profile written as default.pgo', args=['test', '-run=^$', '-bench=.', '-benchtime=20000x', '-cpuprofile=default.pgo', '.'], outputContains=['BenchmarkHash']),
dict(name='build picks up default.pgo', args=['build', '-o', 'app', '.']),
dict(name='binary records the profile', args=['version', '-m', 'app'], outputContains=['-pgo=', 'default.pgo']),
dict(name='answer realistic benchmark profiles', args=['test', '-run=^$', '-bench=BenchmarkMain', '-benchtime=200x', '-cpuprofile=default.pgo', '.'], useSolution=True, outputContains=['BenchmarkMain']),
],
challenge='Add BenchmarkMain that hashes the same 1000 words main uses, so the PGO profile reflects the real workload.',
question='How does go build find a PGO profile without flags?',
correct='It uses default.pgo in the main package\'s directory',
wrong=['It downloads one from the module proxy', 'It always profiles the program during the build'],
reasoning='-pgo=auto is the default and looks for default.pgo next to the main package. The setting is embedded in the binary\'s build info.',
sourceURL='https://go.dev/doc/pgo'),

dict(key='allocation-reduction', stage=STAGE, title='Reducing allocations: preallocation, reuse and value types',
body=[
'The cheapest allocation is the one you avoid. Preallocate slices and maps when the final size is known (make([]T, 0, n), make(map[K]V, n)), append into caller-provided buffers (the AppendX convention used by strconv and time), and return small structs by value.',
'Converting between string and []byte copies, except in cases the compiler optimises, such as map lookups m[string(b)] and comparisons. Interfaces holding non-pointer values usually allocate when the value escapes. strings.Builder avoids the copy in its String method.',
'Reuse long-lived buffers with sync.Pool only after measuring. Clarity first: most code is not hot, and the allocator got about 30% faster for small objects in Go 1.27.',
],
code=r'''package main

import (
    "fmt"
    "strconv"
    "testing"
)

func formatAll(nums []int) []string {
    out := make([]string, 0, len(nums))
    for _, n := range nums {
        out = append(out, strconv.Itoa(n))
    }
    return out
}

func main() {
    nums := []int{100, 200, 300}
    fmt.Println(testing.AllocsPerRun(20, func() { _ = formatAll(nums) }))
    buf := make([]byte, 0, 64)
    n := testing.AllocsPerRun(20, func() {
        buf = buf[:0]
        for _, v := range nums {
            buf = strconv.AppendInt(buf, int64(v), 10)
            buf = append(buf, ' ')
        }
    })
    fmt.Println(n, string(buf))
    m := map[string]int{"go": 1}
    key := []byte("go")
    fmt.Println(testing.AllocsPerRun(20, func() { _ = m[string(key)] }))
}
''',
expectedStdout='4\n0 100 200 300 \n0\n',
challenge='Show that preallocating a map with make(map[int]int, 1000) allocates fewer times than growing an empty one when inserting 1000 keys; print whether that is true.',
solution=r'''package main

import (
    "fmt"
    "testing"
)

func fill(m map[int]int) {
    for i := range 1000 {
        m[i] = i
    }
}

func main() {
    grown := testing.AllocsPerRun(10, func() { fill(map[int]int{}) })
    sized := testing.AllocsPerRun(10, func() { fill(make(map[int]int, 1000)) })
    fmt.Println(sized < grown)
}
''',
solutionStdout='true\n',
question='Why does m[string(key)] not allocate even though key is a []byte?',
correct='The compiler recognises the lookup and uses the bytes without copying them into a new string',
wrong=['Map keys are stored as byte slices internally', 'string conversion never allocates'],
reasoning='The temporary string cannot escape a map index expression, so the compiler skips the copy. A conversion stored in a variable would allocate.',
sourceURL='https://go.dev/doc/gc-guide#Eliminating_heap_allocations'),

dict(key='weak-unique-cleanup', stage=STAGE, title='weak pointers, unique handles and runtime.AddCleanup',
body=[
'Go 1.24 added package weak: weak.Make(p) returns a weak.Pointer that does not keep its target alive, and Value() returns nil once the target has been collected. Weak pointers build caches that never prevent memory from being freed.',
'Package unique (Go 1.23) interns values: unique.Make(v) returns a Handle[T], and two handles are equal exactly when their values are equal. Comparing handles is a pointer comparison, and identical strings share one copy, which saves memory for repetitive data such as host names.',
'runtime.AddCleanup (Go 1.24) runs a function after an object becomes unreachable, replacing most uses of runtime.SetFinalizer. Cleanups receive a separate argument, not the object itself, so they cannot resurrect it; they run on a runtime goroutine at an unspecified time and are not guaranteed to run before exit. Use them as a safety net, never as the main way to release resources: call Close explicitly.',
],
code=r'''package main

import (
    "fmt"
    "runtime"
    "time"
    "unique"
    "weak"
)

type blob struct{ data [1 << 16]byte }

func main() {
    a := unique.Make("example.com")
    b := unique.Make("example." + "com")
    fmt.Println(a == b, a.Value())
    obj := &blob{}
    w := weak.Make(obj)
    done := make(chan string, 1)
    runtime.AddCleanup(obj, func(name string) { done <- name + " cleaned" }, "blob")
    fmt.Println(w.Value() == obj)
    obj = nil
    runtime.GC()
    fmt.Println(w.Value() == nil)
    select {
    case msg := <-done:
        fmt.Println(msg)
    case <-time.After(5 * time.Second):
        fmt.Println("cleanup not run yet")
    }
}
''',
expectedStdout='true example.com\ntrue\ntrue\nblob cleaned\n',
challenge='Intern the strings "a", "b", "a", "c", "b" with unique.Make into a map[unique.Handle[string]]int counting occurrences, and print the count for "a" and the number of distinct handles.',
solution=r'''package main

import (
    "fmt"
    "unique"
)

func main() {
    counts := map[unique.Handle[string]]int{}
    for _, s := range []string{"a", "b", "a", "c", "b"} {
        counts[unique.Make(s)]++
    }
    fmt.Println(counts[unique.Make("a")], len(counts))
}
''',
solutionStdout='2 3\n',
question='Why should runtime.AddCleanup not be the only way to close a file?',
correct='Cleanups run at an unspecified time and may never run before the program exits',
wrong=['AddCleanup only works for strings', 'Cleanups run before the object becomes unreachable'],
reasoning='Collection timing depends on the GC. Deterministic release needs an explicit Close; a cleanup is a backstop for forgotten calls.',
sourceURL='https://pkg.go.dev/runtime#AddCleanup',
additionalReadings=[dict(title='weak package', url='https://pkg.go.dev/weak', section='Pointer'),
                    dict(title='unique package', url='https://pkg.go.dev/unique', section='Handle')]),
]

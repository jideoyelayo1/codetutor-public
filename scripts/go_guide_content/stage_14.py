STAGE = '14 · Memory model and context'
MEM = 'https://go.dev/ref/mem'
CTX = 'https://pkg.go.dev/context'

LESSONS = [
dict(key='happens-before', stage=STAGE, title='The Go memory model: happens-before', race=True,
body=[
'The memory model defines when a write in one goroutine is guaranteed to be seen by a read in another. Within one goroutine, actions happen in program order. Across goroutines, only synchronisation creates ordering: a send on a channel happens before the corresponding receive completes, closing a channel happens before a receive that observes the close, and Unlock happens before the next Lock returns.',
'If a write happens before a read and no other write intervenes, the read sees that write. Without such an edge there is no guarantee at all. A loop that spins on a plain bool set by another goroutine may never see the change, because the compiler may hoist the read out of the loop.',
'Programs free of data races behave as if goroutines were interleaved in some sequential order (DRF-SC). Make that your rule: every shared variable is protected by a channel, a lock or an atomic, and then you can reason sequentially.',
],
code=r'''package main

import "fmt"

var message string

func main() {
    done := make(chan struct{})
    go func() {
        message = "written before close"
        close(done)
    }()
    <-done
    fmt.Println(message)
}
''',
expectedStdout='written before close\n',
challenge='Publish a slice of three numbers from a goroutine to main using an unbuffered channel of struct{} as the only synchronisation, and print the sum in main.',
solution=r'''package main

import "fmt"

func main() {
    var data []int
    ready := make(chan struct{})
    go func() {
        data = []int{1, 2, 3}
        ready <- struct{}{}
    }()
    <-ready
    fmt.Println(data[0] + data[1] + data[2])
}
''',
solutionStdout='6\n',
question='Why is reading message after <-done guaranteed to see the write?',
correct='The write precedes close in its goroutine, and close happens before the receive that observes it',
wrong=['Strings are always shared atomically', 'Goroutines run before main resumes'],
reasoning='Program order plus the close/receive synchronisation edge give a happens-before chain from the write to the read.',
sourceURL=MEM,
additionalReadings=[dict(title='Updating the Go memory model', url='https://research.swtch.com/gomm', section='Background')]),

dict(key='data-race-semantics', stage=STAGE, title='What racy programs may do, and why atomics fix it', race=True,
body=[
'In Go a data race on a single-word variable can produce any value previously written, or cause a crash for multi-word values such as interfaces, slices and strings, whose parts can be torn. Unlike C, Go limits the damage, but a racy program is still wrong.',
'Double-checked locking with a plain flag is broken: another goroutine can see the flag set before the data it guards. Use sync.Once, a mutex, or publish through an atomic.Pointer so the pointer and the data it points to are ordered.',
'A store to an atomic and a load observing it create a happens-before edge, just like a channel. That is why atomic.Pointer can safely publish an immutable configuration that readers then use without locks.',
],
code=r'''package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

type Settings struct {
    Name  string
    Limit int
}

var current atomic.Pointer[Settings]

func reload(name string, limit int) {
    current.Store(&Settings{Name: name, Limit: limit})
}

func main() {
    reload("initial", 1)
    var wg sync.WaitGroup
    for i := range 4 {
        wg.Go(func() {
            if i == 2 {
                reload("updated", 10)
            }
            s := current.Load()
            _ = s.Name + fmt.Sprint(s.Limit)
        })
    }
    wg.Wait()
    fmt.Println(current.Load().Name, current.Load().Limit)
}
''',
expectedStdout='updated 10\n',
challenge='Replace a racy "initialised bool plus value" lazy initialiser with sync.OnceValue so ten goroutines all read the same computed value 42; print it.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

var answer = sync.OnceValue(func() int { return 6 * 7 })

func main() {
    var wg sync.WaitGroup
    results := make([]int, 10)
    for i := range results {
        wg.Go(func() { results[i] = answer() })
    }
    wg.Wait()
    fmt.Println(results[0], results[9])
}
''',
solutionStdout='42 42\n',
question='Why is publishing a struct through atomic.Pointer safe for lock-free readers?',
correct='The Store happens before any Load that observes it, so the struct\'s fields are visible',
wrong=['atomic.Pointer copies the struct for each reader', 'Pointers can never be torn'],
reasoning='Atomic operations synchronise. Writes to the fields before Store are ordered before reads after the matching Load, provided the struct is not modified afterwards.',
sourceURL=MEM+'#restrictions'),

dict(key='context-cancellation', stage=STAGE, title='context: cancellation and deadlines', race=True,
body=[
'context.Context carries cancellation, deadlines and request-scoped values across API boundaries. By convention it is the first parameter, named ctx. context.Background() is the root; WithCancel, WithTimeout and WithDeadline derive children that are cancelled when their parent is, or when their own cancel function or deadline fires.',
'Always call the cancel function, usually with defer cancel(), even if the context times out by itself; it releases the timer and the parent\'s reference. go vet\'s lostcancel check reports cancel functions that are dropped.',
'Code that blocks should select on <-ctx.Done() and return ctx.Err(), which is context.Canceled or context.DeadlineExceeded. Standard library functions that take a context, such as http.NewRequestWithContext and net.Dialer.DialContext, stop their work when it is cancelled.',
],
code=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "time"
)

func slowWork(ctx context.Context, d time.Duration) error {
    select {
    case <-time.After(d):
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
    defer cancel()
    fmt.Println(slowWork(ctx, time.Millisecond))
    err := slowWork(ctx, time.Second)
    fmt.Println(err, errors.Is(err, context.DeadlineExceeded))
    parent, stop := context.WithCancel(context.Background())
    child, cancelChild := context.WithTimeout(parent, time.Hour)
    defer cancelChild()
    stop()
    <-child.Done()
    fmt.Println(child.Err())
}
''',
expectedStdout='<nil>\ncontext deadline exceeded true\ncontext canceled\n',
challenge='Write func firstResult(ctx context.Context, delays []time.Duration) int that starts one goroutine per delay, returns the index of the first to finish, and cancels the others; make sure the losers exit by checking ctx.Done(). Print the result for delays 30ms, 1ms, 50ms.',
solution=r'''package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

func firstResult(ctx context.Context, delays []time.Duration) int {
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()
    winner := make(chan int, len(delays))
    var wg sync.WaitGroup
    for i, d := range delays {
        wg.Go(func() {
            select {
            case <-time.After(d):
                winner <- i
            case <-ctx.Done():
            }
        })
    }
    first := <-winner
    cancel()
    wg.Wait()
    return first
}

func main() {
    fmt.Println(firstResult(context.Background(), []time.Duration{30 * time.Millisecond, time.Millisecond, 50 * time.Millisecond}))
}
''',
solutionStdout='1\n',
question='Why call cancel even after a WithTimeout context has expired?',
correct='It releases resources such as the timer and the parent\'s reference to the child',
wrong=['Otherwise ctx.Err stays nil', 'Expired contexts restart without it'],
reasoning='Cancel is idempotent and cheap. Not calling it keeps the child registered with its parent until the parent ends.',
rejections=[dict(source='package main\n\nimport (\n\t"context"\n\t"time"\n)\n\nfunc main() {\n\tctx, _ := context.WithTimeout(context.Background(), time.Second)\n\t_ = ctx\n}\n', args=['vet', '.'], diagnostic='the cancel function returned by context.WithTimeout should be called')],
sourceURL=CTX,
additionalReadings=[dict(title='Go Concurrency Patterns: Context', url='https://go.dev/blog/context', section='Context')]),

dict(key='context-cause-afterfunc', stage=STAGE, title='Causes, AfterFunc, WithoutCancel and values', race=True,
body=[
'WithCancelCause and WithTimeoutCause (Go 1.20, 1.21) record why a context ended: cancel(errQuotaExceeded) makes context.Cause(ctx) return that error while ctx.Err() still returns context.Canceled. Causes make logs explain cancellations.',
'context.AfterFunc(ctx, f) runs f in its own goroutine after ctx is done and returns a stop function that unregisters it. It connects contexts to APIs that do not accept one, such as closing a connection or waking a sync.Cond.',
'context.WithoutCancel(ctx) keeps values but drops cancellation, for work that must finish after a request ends, such as an audit write. context.WithValue carries request-scoped data like trace IDs. Use an unexported key type to avoid collisions, and never pass optional parameters through values.',
],
code=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "sync"
)

type traceKey struct{}

var errShutdown = errors.New("server shutting down")

func main() {
    base := context.WithValue(context.Background(), traceKey{}, "trace-7")
    ctx, cancel := context.WithCancelCause(base)
    var wg sync.WaitGroup
    wg.Add(1)
    stop := context.AfterFunc(ctx, func() {
        defer wg.Done()
        fmt.Println("after:", context.Cause(ctx))
    })
    detached := context.WithoutCancel(ctx)
    cancel(errShutdown)
    wg.Wait()
    fmt.Println(ctx.Err(), stop())
    fmt.Println(detached.Err(), detached.Value(traceKey{}))
}
''',
expectedStdout='after: server shutting down\ncontext canceled false\n<nil> trace-7\n',
challenge='Create a context with WithTimeoutCause(…, 10*time.Millisecond, errSlow), wait on Done, and print ctx.Err() and context.Cause(ctx).',
solution=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "time"
)

var errSlow = errors.New("backend too slow")

func main() {
    ctx, cancel := context.WithTimeoutCause(context.Background(), 10*time.Millisecond, errSlow)
    defer cancel()
    <-ctx.Done()
    fmt.Println(ctx.Err())
    fmt.Println(context.Cause(ctx))
}
''',
solutionStdout='context deadline exceeded\nbackend too slow\n',
question='What does context.WithoutCancel(ctx) keep and drop?',
correct='It keeps ctx\'s values and drops its cancellation and deadline',
wrong=['It keeps cancellation and drops values', 'It copies everything but makes cancel a no-op for the parent'],
reasoning='The derived context is never cancelled and has no deadline, but Value lookups still reach the parent.',
sourceURL=CTX+'#AfterFunc',
additionalReadings=[dict(title='context.Cause', url=CTX+'#Cause', section='Cause')]),

dict(key='timers-tickers', stage=STAGE, title='Timers, tickers and the Go 1.23 timer semantics', race=True,
body=[
'time.NewTimer(d) delivers one value on its channel C after d; time.NewTicker(d) delivers repeatedly. Stop prevents future deliveries and Reset reschedules.',
'Go 1.23 changed timers for modules declaring go 1.23 or later: timer channels are unbuffered (synchronous), so after Stop or Reset returns no stale value from the old setting will be received, and timers and tickers that are no longer referenced are garbage collected even if never stopped. The old "drain the channel after Stop" idiom is no longer needed. Go 1.27 removes the asynctimerchan setting that restored the old behaviour.',
'Use time.AfterFunc to run a function after a delay in its own goroutine. For deadlines on a whole operation, a context is usually better than hand-managed timers.',
],
code=r'''package main

import (
    "fmt"
    "time"
)

func main() {
    t := time.NewTimer(time.Hour)
    fmt.Println(t.Stop())
    t.Reset(5 * time.Millisecond)
    <-t.C
    fmt.Println("timer fired")
    ticker := time.NewTicker(2 * time.Millisecond)
    defer ticker.Stop()
    ticks := 0
    for range ticker.C {
        ticks++
        if ticks == 3 {
            break
        }
    }
    fmt.Println("ticks:", ticks)
    done := make(chan string)
    time.AfterFunc(time.Millisecond, func() { done <- "after func ran" })
    fmt.Println(<-done)
}
''',
expectedStdout='true\ntimer fired\nticks: 3\nafter func ran\n',
challenge='Implement a debounce: events arrive on a channel at 1ms intervals five times; reset a single timer of 100ms on each event and print "flushed 5" when it finally fires.',
solution=r'''package main

import (
    "fmt"
    "time"
)

func main() {
    events := make(chan int)
    go func() {
        for i := range 5 {
            events <- i
            time.Sleep(time.Millisecond)
        }
    }()
    t := time.NewTimer(time.Hour)
    count := 0
    for {
        select {
        case <-events:
            count++
            t.Reset(100 * time.Millisecond)
        case <-t.C:
            fmt.Println("flushed", count)
            return
        }
    }
}
''',
solutionStdout='flushed 5\n',
question='With go 1.23 or later in go.mod, what can you rely on after t.Stop() returns?',
correct='No stale value from before the Stop will be received from t.C',
wrong=['t.C is closed', 'You must drain t.C manually before Reset'],
reasoning='Timer channels became synchronous in Go 1.23, which removed the need for the drain idiom for modules declaring 1.23+.',
sourceURL='https://go.dev/doc/go1.23#timer-changes',
additionalReadings=[dict(title='time.Timer', url='https://pkg.go.dev/time#Timer', section='Timer')]),
]

STAGE = '12 · Goroutines and channels'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='goroutines', stage=STAGE, title='Goroutines and the Go scheduler', race=True,
body=[
'go f(x) starts a goroutine: a function running concurrently with the caller. Goroutines are cheap, starting with a few kilobytes of stack that grows as needed, so programs can run hundreds of thousands. The runtime multiplexes them onto operating-system threads with an M:N scheduler: G (goroutines) run on M (threads) holding P (processors, GOMAXPROCS of them).',
'The arguments of go f(x) are evaluated immediately in the calling goroutine; f runs later. When main returns the program exits, killing every other goroutine, so main must wait for work it started. sync.WaitGroup and channels are the usual ways to wait.',
'Goroutine execution order is not specified. Output from several goroutines interleaves differently between runs unless you synchronise. The scheduler is preemptive (since Go 1.14), so a tight loop cannot starve the others forever.',
],
code=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup
    results := make([]int, 5)
    for i := range 5 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            results[i] = i * i
        }()
    }
    wg.Wait()
    fmt.Println(results)
}
''',
expectedStdout='[0 1 4 9 16]\n',
challenge='Start three goroutines that each compute the sum of a third of 1..300 into their own slot of a [3]int, wait for them, and print the total.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    var parts [3]int
    var wg sync.WaitGroup
    for p := range 3 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for n := p*100 + 1; n <= (p+1)*100; n++ {
                parts[p] += n
            }
        }()
    }
    wg.Wait()
    fmt.Println(parts[0] + parts[1] + parts[2])
}
''',
solutionStdout='45150\n',
question='Why is writing results[i] from separate goroutines safe here?',
correct='Each goroutine writes a different element, and Wait orders those writes before the read',
wrong=['Slices are protected by an internal lock', 'Goroutines run one after another in order'],
reasoning='Distinct elements are distinct memory locations, so there is no data race. wg.Wait synchronises with each Done, making the writes visible to main.',
sourceURL='https://go.dev/doc/effective_go#goroutines',
additionalReadings=[dict(title='Go statements', url=SPEC+'#Go_statements', section='go')]),

dict(key='channels-buffering', stage=STAGE, title='Unbuffered and buffered channels', race=True,
body=[
'A channel carries values of one type between goroutines: ch := make(chan int). A send ch <- v and a receive v := <-ch on an unbuffered channel wait for each other: the send completes only when a receiver takes the value, so it also synchronises the two goroutines.',
'make(chan int, 3) creates a buffered channel. Sends succeed without a receiver until the buffer is full; receives succeed until it is empty. len(ch) and cap(ch) report the queue length and capacity, but checking len before acting is racy.',
'Use unbuffered channels for hand-offs and synchronisation, small buffers to absorb bursts, and never a buffer size chosen to "avoid deadlock": if correctness depends on the buffer size, the design has a bug. Channel direction types, chan<- int (send-only) and <-chan int (receive-only), document intent in signatures.',
],
code=r'''package main

import "fmt"

func produce(out chan<- int) {
    for i := 1; i <= 3; i++ {
        out <- i * 10
    }
    close(out)
}

func main() {
    ch := make(chan int)
    go produce(ch)
    for v := range ch {
        fmt.Println("got", v)
    }
    buf := make(chan string, 2)
    buf <- "a"
    buf <- "b"
    fmt.Println(len(buf), cap(buf), <-buf, <-buf)
}
''',
expectedStdout='got 10\ngot 20\ngot 30\n2 2 a b\n',
challenge='Write a ping-pong: two goroutines pass an int back and forth on two unbuffered channels, each adding 1, until it reaches 6; print each value as it is received by main\'s side.',
solution=r'''package main

import "fmt"

func main() {
    ping, pong := make(chan int), make(chan int)
    go func() {
        for v := range ping {
            pong <- v + 1
        }
        close(pong)
    }()
    v := 0
    for v < 6 {
        ping <- v + 1
        v = <-pong
        fmt.Println(v)
    }
    close(ping)
}
''',
solutionStdout='2\n4\n6\n',
question='When does a send on an unbuffered channel complete?',
correct='When another goroutine receives the value',
wrong=['Immediately; the value is queued', 'When the channel is closed'],
reasoning='An unbuffered channel has no storage, so sender and receiver must meet. That rendezvous is also a synchronisation point.',
rejections=[dict(source='package main\n\nfunc main() {\n\tch := make(chan int)\n\tch <- 1\n}\n', args=['run', '.'], diagnostic='all goroutines are asleep - deadlock!')],
sourceURL=SPEC+'#Channel_types',
additionalReadings=[dict(title='Send statements', url=SPEC+'#Send_statements', section='Send statements')]),

dict(key='close-and-range', stage=STAGE, title='Closing channels, comma-ok receives and ownership', race=True,
body=[
'close(ch) records that no more values will be sent. Receivers then drain the remaining buffered values and afterwards receive the zero value immediately. v, ok := <-ch reports ok=false once the channel is closed and empty, and for v := range ch stops at that point.',
'Only the sender should close, and only once. Sending on a closed channel panics, and so does closing it twice. With several senders, close after all of them are done, typically from a goroutine that waits on a WaitGroup.',
'Closing is a broadcast: every receiver sees it, which makes a closed chan struct{} a cheap "done" signal. You do not have to close a channel for garbage collection; close it to tell receivers to stop.',
],
code=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    ch := make(chan int, 2)
    ch <- 1
    close(ch)
    v, ok := <-ch
    fmt.Println(v, ok)
    v, ok = <-ch
    fmt.Println(v, ok)
    results := make(chan int)
    var wg sync.WaitGroup
    for id := 1; id <= 3; id++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            results <- id
        }()
    }
    go func() {
        wg.Wait()
        close(results)
    }()
    sum := 0
    for r := range results {
        sum += r
    }
    fmt.Println(sum)
}
''',
expectedStdout='1 true\n0 false\n6\n',
challenge='Use a closed chan struct{} named done to stop three waiting goroutines at once; each prints nothing but signals a WaitGroup when it sees done closed. Print "all stopped" after waiting.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    done := make(chan struct{})
    var wg sync.WaitGroup
    for range 3 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            <-done
        }()
    }
    close(done)
    wg.Wait()
    fmt.Println("all stopped")
}
''',
solutionStdout='all stopped\n',
question='Who should close a channel with several senders?',
correct='A coordinator that closes it after every sender has finished',
wrong=['Each sender, after its last send', 'The receiver, once it has seen enough values'],
reasoning='Closing twice or sending after close panics. Waiting for all senders, then closing once, avoids both.',
rejections=[dict(source='package main\n\nfunc main() {\n\tch := make(chan int, 1)\n\tclose(ch)\n\tch <- 1\n}\n', args=['run', '.'], diagnostic='send on closed channel')],
sourceURL=SPEC+'#Close'),

dict(key='select-timeouts', stage=STAGE, title='select, timeouts and non-blocking operations', race=True,
body=[
'select waits on several channel operations and runs the first that can proceed; if several are ready it picks one at random, which prevents starvation. A default case makes the select non-blocking: it runs immediately when no other case is ready.',
'time.After(d) returns a channel that receives after d, so case <-time.After(time.Second): implements a timeout. In a loop, prefer one time.Timer or a context deadline over creating a new After channel per iteration. Since Go 1.23 unreferenced timers are collected even if not stopped.',
'A select with no cases, select {}, blocks forever. Each case expression is evaluated once on entry, including the right-hand side of sends.',
],
code=r'''package main

import (
    "fmt"
    "time"
)

func main() {
    fast := make(chan string, 1)
    fast <- "ready"
    select {
    case msg := <-fast:
        fmt.Println(msg)
    case <-time.After(time.Second):
        fmt.Println("timeout")
    }
    slow := make(chan string)
    select {
    case msg := <-slow:
        fmt.Println(msg)
    case <-time.After(20 * time.Millisecond):
        fmt.Println("timeout")
    }
    select {
    case slow <- "x":
        fmt.Println("sent")
    default:
        fmt.Println("nobody listening")
    }
}
''',
expectedStdout='ready\ntimeout\nnobody listening\n',
challenge='Write func trySend(ch chan<- int, v int) bool that sends without blocking and reports success; call it twice on a channel with buffer 1 and print both results.',
solution=r'''package main

import "fmt"

func trySend(ch chan<- int, v int) bool {
    select {
    case ch <- v:
        return true
    default:
        return false
    }
}

func main() {
    ch := make(chan int, 1)
    fmt.Println(trySend(ch, 1), trySend(ch, 2))
}
''',
solutionStdout='true false\n',
question='Which case runs when several select cases are ready?',
correct='One chosen uniformly at random',
wrong=['The first one in source order', 'All of them in order'],
reasoning='Random choice stops one busy channel from starving the others. Code must not rely on case order.',
sourceURL=SPEC+'#Select_statements'),

dict(key='nil-channels', stage=STAGE, title='nil channels to disable select cases', race=True,
body=[
'Sending to or receiving from a nil channel blocks forever. Inside select, a case on a nil channel is never ready, so setting a channel variable to nil switches that case off.',
'This is how to merge two inputs that close at different times: when one input is closed, set its variable to nil and keep selecting on the other until both are nil.',
'Closing a nil channel panics. A nil channel is the zero value of a channel type, so an uninitialised struct field of channel type blocks every operation; make channels in constructors.',
],
code=r'''package main

import "fmt"

func emit(vals ...int) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        for _, v := range vals {
            ch <- v
        }
    }()
    return ch
}

func main() {
    a, b := emit(1, 2, 3), emit(10)
    sum, count := 0, 0
    for a != nil || b != nil {
        select {
        case v, ok := <-a:
            if !ok {
                a = nil
                continue
            }
            sum += v
            count++
        case v, ok := <-b:
            if !ok {
                b = nil
                continue
            }
            sum += v
            count++
        }
    }
    fmt.Println(sum, count)
}
''',
expectedStdout='16 4\n',
challenge='Generalise the merge into func merge(a, b <-chan int) <-chan int that forwards values from both and closes its output when both inputs are closed; print the sorted values merged from emit(3, 1) and emit(2).',
solution=r'''package main

import (
    "fmt"
    "slices"
)

func emit(vals ...int) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        for _, v := range vals {
            ch <- v
        }
    }()
    return ch
}

func merge(a, b <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for a != nil || b != nil {
            select {
            case v, ok := <-a:
                if !ok {
                    a = nil
                    continue
                }
                out <- v
            case v, ok := <-b:
                if !ok {
                    b = nil
                    continue
                }
                out <- v
            }
        }
    }()
    return out
}

func main() {
    var got []int
    for v := range merge(emit(3, 1), emit(2)) {
        got = append(got, v)
    }
    slices.Sort(got)
    fmt.Println(got)
}
''',
solutionStdout='[1 2 3]\n',
question='What does a select case on a nil channel do?',
correct='It is never ready, so the case is effectively disabled',
wrong=['It panics', 'It receives the zero value immediately'],
reasoning='Operations on nil channels block forever, and select simply never chooses a case that cannot proceed.',
sourceURL='https://go.dev/ref/spec#Receive_operator'),

dict(key='pipelines', stage=STAGE, title='Pipelines of stages connected by channels', race=True,
body=[
'A pipeline is a chain of stages, each a goroutine that receives from an inbound channel, processes values and sends them outbound. Each stage owns and closes its output channel, so the end of input propagates down the chain.',
'Stages that may be abandoned must be cancellable. If the consumer stops early, upstream stages blocked on sends leak. Pass a done channel or context.Context and select on it alongside every send.',
'Return receive-only channels from stage constructors (func square(in <-chan int) <-chan int). The types then prevent callers from sending into or closing a stage\'s output.',
],
code=r'''package main

import "fmt"

func gen(done <-chan struct{}, nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            select {
            case out <- n:
            case <-done:
                return
            }
        }
    }()
    return out
}

func square(done <-chan struct{}, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * n:
            case <-done:
                return
            }
        }
    }()
    return out
}

func main() {
    done := make(chan struct{})
    defer close(done)
    for v := range square(done, square(done, gen(done, 1, 2, 3))) {
        fmt.Println(v)
    }
}
''',
expectedStdout='1\n16\n81\n',
challenge='Add a stage filterOdd(done, in) that forwards only odd numbers, and print the result of square(filterOdd(gen(1..6))).',
solution=r'''package main

import "fmt"

func gen(done <-chan struct{}, nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            select {
            case out <- n:
            case <-done:
                return
            }
        }
    }()
    return out
}

func filterOdd(done <-chan struct{}, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            if n%2 == 0 {
                continue
            }
            select {
            case out <- n:
            case <-done:
                return
            }
        }
    }()
    return out
}

func square(done <-chan struct{}, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * n:
            case <-done:
                return
            }
        }
    }()
    return out
}

func main() {
    done := make(chan struct{})
    defer close(done)
    for v := range square(done, filterOdd(done, gen(done, 1, 2, 3, 4, 5, 6))) {
        fmt.Print(v, " ")
    }
    fmt.Println()
}
''',
solutionStdout='1 9 25 \n',
question='Why does every send in a stage select on done?',
correct='So the stage can exit instead of blocking forever if the consumer stops early',
wrong=['Select makes sends faster', 'Channels cannot be closed otherwise'],
reasoning='A blocked send with no receiver never completes, leaking the goroutine. done gives it a way out.',
sourceURL='https://go.dev/blog/pipelines'),

dict(key='fan-out-fan-in', stage=STAGE, title='Fan-out, fan-in and preserving order', race=True,
body=[
'Fan-out starts several goroutines reading from one channel, spreading work across CPUs. Fan-in merges several channels into one, usually with a WaitGroup that closes the merged output after every input is drained.',
'Fan-out loses ordering: results arrive in completion order. When order matters, send results with their index and place them into a pre-sized slice, or sort afterwards.',
'Fan-out helps CPU-bound work up to GOMAXPROCS goroutines and I/O-bound work further, until an external limit such as a connection pool is reached. Measure; more goroutines than useful parallelism only adds scheduling cost.',
],
code=r'''package main

import (
    "fmt"
    "sync"
)

type result struct {
    index, value int
}

func main() {
    jobs := make(chan int)
    results := make(chan result)
    var wg sync.WaitGroup
    for range 3 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for i := range jobs {
                results <- result{i, i * i * i}
            }
        }()
    }
    go func() {
        for i := range 6 {
            jobs <- i
        }
        close(jobs)
    }()
    go func() {
        wg.Wait()
        close(results)
    }()
    ordered := make([]int, 6)
    for r := range results {
        ordered[r.index] = r.value
    }
    fmt.Println(ordered)
}
''',
expectedStdout='[0 1 8 27 64 125]\n',
challenge='Write func fanIn(chans ...<-chan string) <-chan string using a WaitGroup, merge three channels each carrying one word, and print the sorted words.',
solution=r'''package main

import (
    "fmt"
    "slices"
    "sync"
)

func one(s string) <-chan string {
    ch := make(chan string, 1)
    ch <- s
    close(ch)
    return ch
}

func fanIn(chans ...<-chan string) <-chan string {
    out := make(chan string)
    var wg sync.WaitGroup
    for _, c := range chans {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for v := range c {
                out <- v
            }
        }()
    }
    go func() {
        wg.Wait()
        close(out)
    }()
    return out
}

func main() {
    var words []string
    for w := range fanIn(one("go"), one("chan"), one("select")) {
        words = append(words, w)
    }
    slices.Sort(words)
    fmt.Println(words)
}
''',
solutionStdout='[chan go select]\n',
question='How do you keep results in input order after fanning out?',
correct='Send each result with its index and store it at that position',
wrong=['Use a buffered channel the size of the input', 'Start the workers in order'],
reasoning='Workers finish in arbitrary order. Carrying the index restores order deterministically without serialising the work.',
sourceURL='https://go.dev/blog/pipelines'),

dict(key='worker-pools', stage=STAGE, title='Bounded concurrency: worker pools and semaphores', race=True,
body=[
'Starting one goroutine per item is fine for small inputs but unbounded for large ones: it can exhaust memory, file descriptors or a remote service. Bound concurrency with a fixed pool of workers reading from a jobs channel, or with a semaphore.',
'A buffered channel is a counting semaphore: sem := make(chan struct{}, n); acquire with sem <- struct{}{} before work and release with <-sem after. At most n holders exist at once.',
'Collect errors as well as results. Common patterns are a result struct carrying an error, or the first-error-cancels-the-rest pattern of errgroup (golang.org/x/sync/errgroup), which combines a WaitGroup, a context and an error.',
],
code=r'''package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    const limit = 2
    sem := make(chan struct{}, limit)
    var active, peak atomic.Int32
    var wg sync.WaitGroup
    for range 8 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            sem <- struct{}{}
            defer func() { <-sem }()
            n := active.Add(1)
            for {
                p := peak.Load()
                if n <= p || peak.CompareAndSwap(p, n) {
                    break
                }
            }
            active.Add(-1)
        }()
    }
    wg.Wait()
    fmt.Println(peak.Load() <= limit)
}
''',
expectedStdout='true\n',
challenge='Build a pool of 3 workers that read words from a jobs channel and send their lengths on a results channel; process "go", "gopher", "channel", "x" and print the total length.',
solution=r'''package main

import (
    "fmt"
    "sync"
)

func main() {
    jobs := make(chan string)
    results := make(chan int)
    var wg sync.WaitGroup
    for range 3 {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for w := range jobs {
                results <- len(w)
            }
        }()
    }
    go func() {
        for _, w := range []string{"go", "gopher", "channel", "x"} {
            jobs <- w
        }
        close(jobs)
    }()
    go func() {
        wg.Wait()
        close(results)
    }()
    total := 0
    for n := range results {
        total += n
    }
    fmt.Println(total)
}
''',
solutionStdout='16\n',
question='How does a buffered channel of capacity n act as a semaphore?',
correct='Each worker sends to acquire and receives to release, so at most n hold a slot',
wrong=['The buffer stores the results of n workers', 'It makes the channel n times faster'],
reasoning='A send blocks when the buffer is full, which happens exactly when n slots are held.',
sourceURL='https://go.dev/doc/effective_go#channels',
additionalReadings=[dict(title='errgroup', url='https://pkg.go.dev/golang.org/x/sync/errgroup', section='Group')]),

dict(key='goroutine-leaks', stage=STAGE, title='Goroutine leaks and the Go 1.27 goroutineleak profile',
body=[
'A goroutine leaks when it can never finish, usually because it is blocked forever on a channel nobody will use again, such as a send after the receiver returned early. Leaked goroutines keep their stacks and everything they reference alive.',
'Prevent leaks by giving every goroutine an exit path: buffered result channels sized to the number of senders, done channels or contexts on every blocking operation, and an owner that waits for goroutines it started.',
'Go 1.27 adds a goroutineleak profile to runtime/pprof (and /debug/pprof/goroutineleak in net/http/pprof). Collecting it runs a garbage collection that finds goroutines blocked on concurrency primitives no running goroutine can reach, and reports their stacks. It finds leaks that can be proven; a goroutine blocked on a reachable channel is not reported even if it will never be woken.',
],
code=r'''package main

import (
    "bytes"
    "fmt"
    "runtime/pprof"
    "strings"
    "time"
)

func firstOf(fns ...func() int) int {
    out := make(chan int)
    for _, f := range fns {
        go func() { out <- f() }()
    }
    return <-out
}

func main() {
    quick := func() int { return 1 }
    slow := func() int { time.Sleep(10 * time.Millisecond); return 2 }
    fmt.Println(firstOf(quick, slow, slow))
    time.Sleep(50 * time.Millisecond)
    var buf bytes.Buffer
    if err := pprof.Lookup("goroutineleak").WriteTo(&buf, 1); err != nil {
        fmt.Println(err)
        return
    }
    fmt.Println(strings.Contains(buf.String(), "goroutineleak profile: total 2"))
}
''',
expectedStdout='1\ntrue\n',
challenge='Fix firstOf so no goroutine leaks: give the channel enough buffer for every sender, then show that the goroutineleak profile reports total 0.',
solution=r'''package main

import (
    "bytes"
    "fmt"
    "runtime/pprof"
    "strings"
    "time"
)

func firstOf(fns ...func() int) int {
    out := make(chan int, len(fns))
    for _, f := range fns {
        go func() { out <- f() }()
    }
    return <-out
}

func main() {
    quick := func() int { return 1 }
    slow := func() int { time.Sleep(10 * time.Millisecond); return 2 }
    fmt.Println(firstOf(quick, slow, slow))
    time.Sleep(50 * time.Millisecond)
    var buf bytes.Buffer
    if err := pprof.Lookup("goroutineleak").WriteTo(&buf, 1); err != nil {
        fmt.Println(err)
        return
    }
    fmt.Println(strings.Contains(buf.String(), "goroutineleak profile: total 0"))
}
''',
solutionStdout='1\ntrue\n',
question='Why did two goroutines leak in the original firstOf?',
correct='They sent on an unbuffered channel after its only receiver had returned',
wrong=['time.Sleep never returns inside goroutines', 'pprof itself starts two goroutines'],
reasoning='Only one receive happens. The two slower senders block forever on a channel nothing can reach, which is exactly what the leak profile detects.',
sourceURL='https://go.dev/doc/go1.27#runtime',
additionalReadings=[dict(title='runtime/pprof profiles', url='https://pkg.go.dev/runtime/pprof#Profile', section='goroutineleak')]),
]

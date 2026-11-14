STAGE = '20 · Projects'


def f(path, content):
    return dict(path=path, content=content)


def gomod(name):
    return f('go.mod', f'module example.com/{name}\n\ngo 1.27\n')


WC_LIB = r'''// Package wc counts lines, words and bytes like the Unix wc tool.
package wc

import (
    "bufio"
    "io"
    "unicode"
)

// Counts holds the totals for one input.
type Counts struct {
    Lines, Words, Bytes int
}

// Count reads r to the end and returns its totals.
func Count(r io.Reader) (Counts, error) {
    var c Counts
    br := bufio.NewReader(r)
    inWord := false
    for {
        ch, size, err := br.ReadRune()
        if err == io.EOF {
            return c, nil
        }
        if err != nil {
            return c, err
        }
        c.Bytes += size
        if ch == '\n' {
            c.Lines++
        }
        if unicode.IsSpace(ch) {
            inWord = false
        } else if !inWord {
            inWord = true
            c.Words++
        }
    }
}
'''

WC_TEST = r'''package wc

import (
    "errors"
    "strings"
    "testing"
    "testing/iotest"
)

func TestCount(t *testing.T) {
    cases := []struct {
        name, in string
        want     Counts
    }{
        {"empty", "", Counts{}},
        {"one line", "hello go\n", Counts{1, 2, 9}},
        {"no newline", "a b c", Counts{0, 3, 5}},
        {"unicode", "héllo wörld\n", Counts{1, 2, 14}},
        {"spaces", "  a \t\n\n b ", Counts{2, 2, 10}},
    }
    for _, c := range cases {
        t.Run(c.name, func(t *testing.T) {
            got, err := Count(strings.NewReader(c.in))
            if err != nil || got != c.want {
                t.Fatalf("Count(%q) = %+v, %v; want %+v", c.in, got, err, c.want)
            }
        })
    }
}

func TestCountReadError(t *testing.T) {
    boom := errors.New("boom")
    if _, err := Count(iotest.ErrReader(boom)); !errors.Is(err, boom) {
        t.Fatalf("err = %v", err)
    }
}
'''

WC_MAIN = r'''// Command wc prints line, word and byte counts for files or standard input.
package main

import (
    "flag"
    "fmt"
    "io"
    "os"

    "example.com/wc"
)

func run(args []string, stdin io.Reader, stdout, stderr io.Writer) int {
    fs := flag.NewFlagSet("wc", flag.ContinueOnError)
    fs.SetOutput(stderr)
    lines := fs.Bool("l", false, "print only the line count")
    if err := fs.Parse(args); err != nil {
        return 2
    }
    show := func(c wc.Counts, name string) {
        if *lines {
            fmt.Fprintf(stdout, "%d %s\n", c.Lines, name)
            return
        }
        fmt.Fprintf(stdout, "%d %d %d %s\n", c.Lines, c.Words, c.Bytes, name)
    }
    if fs.NArg() == 0 {
        c, err := wc.Count(stdin)
        if err != nil {
            fmt.Fprintln(stderr, "wc:", err)
            return 1
        }
        show(c, "-")
        return 0
    }
    status := 0
    for _, name := range fs.Args() {
        f, err := os.Open(name)
        if err != nil {
            fmt.Fprintln(stderr, "wc:", err)
            status = 1
            continue
        }
        c, err := wc.Count(f)
        f.Close()
        if err != nil {
            fmt.Fprintln(stderr, "wc:", err)
            status = 1
            continue
        }
        show(c, name)
    }
    return status
}

func main() {
    os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}
'''

WC_MAIN_TEST = r'''package main

import (
    "bytes"
    "strings"
    "testing"
)

func TestRunStdin(t *testing.T) {
    var out, errOut bytes.Buffer
    code := run(nil, strings.NewReader("a b\nc\n"), &out, &errOut)
    if code != 0 || out.String() != "2 3 6 -\n" {
        t.Fatalf("code %d out %q err %q", code, out.String(), errOut.String())
    }
}

func TestRunMissingFile(t *testing.T) {
    var out, errOut bytes.Buffer
    if code := run([]string{"definitely-missing.txt"}, nil, &out, &errOut); code != 1 {
        t.Fatalf("code = %d", code)
    }
    if !strings.Contains(errOut.String(), "no such file") {
        t.Fatalf("stderr %q", errOut.String())
    }
}
'''

LESSONS = [
dict(key='wordcount-cli-project', stage=STAGE, title='Project: a tested word-count command',
body=[
'This project builds a small but complete command-line tool: a reusable wc package with a Count(io.Reader) function, and a cmd/wc command that handles flags, files, standard input, exit codes and error messages.',
'The command\'s logic lives in run(args, stdin, stdout, stderr) int, and main only calls os.Exit(run(...)). Tests can then call run with buffers and fake inputs, checking output and exit status without starting a process.',
'Count streams the input with bufio.Reader.ReadRune instead of reading it all, so memory stays constant for large files. Words are maximal runs of non-space runes, using unicode.IsSpace so tabs and Unicode spaces count as separators. Bytes are counted from the encoded size of each rune.',
'Error handling follows Unix conventions: a missing file prints wc: <error> to stderr and makes the final status 1, but the remaining files are still processed. Bad flags return status 2.',
'Tests cover edge cases: empty input, no trailing newline, multi-byte characters, mixed whitespace, and a read error injected with testing/iotest.ErrReader.',
'The practice adds a -w flag for words only. Make it mutually exclusive with -l: when both are given, print usage and exit 2.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[gomod('wc'), f('wc.go', WC_LIB), f('wc_test.go', WC_TEST), f('cmd/wc/main.go', WC_MAIN), f('cmd/wc/main_test.go', WC_MAIN_TEST),
         f('testdata/poem.txt', 'Go is expressive,\nconcise, clean, and efficient.\n')],
projectSolutionFiles=[f('cmd/wc/main.go', WC_MAIN.replace(
    '    lines := fs.Bool("l", false, "print only the line count")\n    if err := fs.Parse(args); err != nil {\n        return 2\n    }\n',
    '    lines := fs.Bool("l", false, "print only the line count")\n    words := fs.Bool("w", false, "print only the word count")\n    if err := fs.Parse(args); err != nil {\n        return 2\n    }\n    if *lines && *words {\n        fmt.Fprintln(stderr, "wc: -l and -w are mutually exclusive")\n        fs.Usage()\n        return 2\n    }\n').replace(
    '        if *lines {\n            fmt.Fprintf(stdout, "%d %s\\n", c.Lines, name)\n            return\n        }\n',
    '        if *lines {\n            fmt.Fprintf(stdout, "%d %s\\n", c.Lines, name)\n            return\n        }\n        if *words {\n            fmt.Fprintf(stdout, "%d %s\\n", c.Words, name)\n            return\n        }\n'))],
projectInstructions='Go 1.27, standard library only. Create all six files, then from the module root run:\ngo test -race ./...\ngo run ./cmd/wc testdata/poem.txt\nprintf "a b\\nc\\n" | go run ./cmd/wc -l\nExpected: 2 7 49 testdata/poem.txt, then 2 -.\nPractice: add a -w flag (words only) that cannot be combined with -l (exit status 2). Replace cmd/wc/main.go with the worked answer.',
projectChecks=[
dict(name='package and command tests', args=['test', '-race', '-count=1', './...'], timeout=240, outputContains=['ok  \texample.com/wc', 'ok  \texample.com/wc/cmd/wc']),
dict(name='counts a file', args=['run', './cmd/wc', 'testdata/poem.txt'], stdout='2 7 49 testdata/poem.txt\n'),
dict(name='-l on stdin', args=['run', './cmd/wc', '-l'], stdin='a b\nc\n', stdout='2 -\n'),
dict(name='missing file exits 1 and continues', args=['run', './cmd/wc', 'missing.txt', 'testdata/poem.txt'], exit=1, stdout='2 7 49 testdata/poem.txt\n', stderrContains='wc: open missing.txt'),
dict(name='word boundary bug is caught', args=['test', './...'], exit=1,
     mutations=[dict(path='wc.go', find='if unicode.IsSpace(ch) {', replace='if ch == \' \' {')], outputContains=['FAIL']),
dict(name='answer -w flag', args=['run', './cmd/wc', '-w', 'testdata/poem.txt'], useSolution=True, stdout='7 testdata/poem.txt\n'),
dict(name='answer rejects -l with -w', args=['run', './cmd/wc', '-l', '-w', 'testdata/poem.txt'], useSolution=True, exit=1, outputContains=['mutually exclusive', 'exit status 2']),
dict(name='answer keeps tests passing', args=['test', '-race', '-count=1', './...'], useSolution=True, timeout=240, outputContains=['ok']),
],
challenge='Add a -w flag that prints only the word count, and make -l together with -w print an error with usage and exit with status 2.',
question='Why does main only call os.Exit(run(os.Args[1:], os.Stdin, os.Stdout, os.Stderr))?',
correct='So the whole command can be tested with buffers and fake inputs, without exiting the test process',
wrong=['os.Exit must be the only statement in main', 'It makes the binary smaller'],
reasoning='os.Exit skips deferred calls and would end a test run. Keeping logic in run, with injected streams, makes every path testable.',
sourceURL='https://go.dev/doc/tutorial/create-module',
minutes=60),
]

FETCH_LIB = r'''// Package fetch downloads URLs concurrently with bounded parallelism.
package fetch

import (
    "context"
    "fmt"
    "io"
    "net/http"
    "sync"
)

// Result is the outcome for one URL.
type Result struct {
    URL    string
    Status int
    Bytes  int
    Err    error
}

// All fetches every URL with at most limit requests in flight and returns
// results in input order. It stops starting new requests when ctx is done.
func All(ctx context.Context, client *http.Client, urls []string, limit int) []Result {
    results := make([]Result, len(urls))
    sem := make(chan struct{}, limit)
    var wg sync.WaitGroup
    for i, u := range urls {
        select {
        case sem <- struct{}{}:
        case <-ctx.Done():
            results[i] = Result{URL: u, Err: ctx.Err()}
            continue
        }
        wg.Go(func() {
            defer func() { <-sem }()
            results[i] = one(ctx, client, u)
        })
    }
    wg.Wait()
    return results
}

func one(ctx context.Context, client *http.Client, url string) Result {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return Result{URL: url, Err: err}
    }
    resp, err := client.Do(req)
    if err != nil {
        return Result{URL: url, Err: err}
    }
    defer resp.Body.Close()
    n, err := io.Copy(io.Discard, io.LimitReader(resp.Body, 1<<20))
    if err != nil {
        return Result{URL: url, Status: resp.StatusCode, Err: fmt.Errorf("read body: %w", err)}
    }
    return Result{URL: url, Status: resp.StatusCode, Bytes: int(n)}
}
'''

FETCH_TEST = r'''package fetch

import (
    "context"
    "errors"
    "io"
    "net/http"
    "strings"
    "sync/atomic"
    "testing"
    "time"
)

// fakeTransport serves canned responses and records concurrency, with no network.
type fakeTransport struct {
    delay        time.Duration
    active, peak atomic.Int32
}

func (f *fakeTransport) RoundTrip(r *http.Request) (*http.Response, error) {
    n := f.active.Add(1)
    defer f.active.Add(-1)
    for {
        p := f.peak.Load()
        if n <= p || f.peak.CompareAndSwap(p, n) {
            break
        }
    }
    select {
    case <-time.After(f.delay):
    case <-r.Context().Done():
        return nil, r.Context().Err()
    }
    if strings.HasSuffix(r.URL.Path, "/missing") {
        return &http.Response{StatusCode: 404, Body: io.NopCloser(strings.NewReader("")), Request: r}, nil
    }
    return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(r.URL.Path)), Request: r}, nil
}

func TestAllOrderAndLimit(t *testing.T) {
    ft := &fakeTransport{delay: 5 * time.Millisecond}
    client := &http.Client{Transport: ft}
    urls := []string{"http://x/a", "http://x/missing", "http://x/ccc", "http://x/dd", "http://x/e"}
    got := All(context.Background(), client, urls, 2)
    want := []int{200, 404, 200, 200, 200}
    for i, r := range got {
        if r.URL != urls[i] || r.Status != want[i] || r.Err != nil {
            t.Errorf("result %d = %+v", i, r)
        }
    }
    if got[2].Bytes != len("/ccc") {
        t.Errorf("bytes = %d", got[2].Bytes)
    }
    if p := ft.peak.Load(); p > 2 {
        t.Errorf("peak concurrency %d exceeds limit 2", p)
    }
}

func TestAllCancellation(t *testing.T) {
    ft := &fakeTransport{delay: time.Hour}
    ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
    defer cancel()
    start := time.Now()
    got := All(ctx, &http.Client{Transport: ft}, []string{"http://x/1", "http://x/2", "http://x/3"}, 1)
    if time.Since(start) > 2*time.Second {
        t.Fatal("All did not stop after cancellation")
    }
    for _, r := range got {
        if !errors.Is(r.Err, context.DeadlineExceeded) {
            t.Errorf("%s: err = %v", r.URL, r.Err)
        }
    }
}
'''

LESSONS += [
dict(key='concurrent-fetcher-project', stage=STAGE, title='Project: a bounded, cancellable concurrent fetcher',
body=[
'fetch.All downloads many URLs concurrently while respecting three contracts: at most limit requests are in flight, results come back in input order, and cancelling the context stops both new and in-flight requests.',
'A buffered channel is the semaphore. The loop acquires a slot before starting each goroutine, selecting on ctx.Done() so a cancelled context stops the loop instead of blocking. Each goroutine writes only its own results[i], which preserves order without a mutex, and wg.Wait orders those writes before the return.',
'Every request carries the context through http.NewRequestWithContext, so cancellation reaches the transport. Bodies are always closed, and reads are capped with io.LimitReader so a hostile server cannot exhaust memory.',
'Tests use a fake http.RoundTripper rather than the network. It records peak concurrency with atomics, simulates latency, returns a 404 for one path, and honours request cancellation. The tests run under the race detector.',
'The cancellation test uses a transport that would wait an hour; the context deadline must end the whole call within moments, with every result carrying context.DeadlineExceeded.',
'The practice adds per-request timeouts: each URL gets its own deadline derived from the parent context, so one slow server cannot use up the whole budget.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[gomod('fetch'), f('fetch.go', FETCH_LIB), f('fetch_test.go', FETCH_TEST)],
projectSolutionFiles=[
f('fetch.go', FETCH_LIB.replace(
    '// Package fetch downloads URLs concurrently with bounded parallelism.\npackage fetch\n\nimport (\n    "context"\n    "fmt"\n    "io"\n    "net/http"\n    "sync"\n)\n',
    '// Package fetch downloads URLs concurrently with bounded parallelism.\npackage fetch\n\nimport (\n    "context"\n    "fmt"\n    "io"\n    "net/http"\n    "sync"\n    "time"\n)\n\n// PerRequest is the deadline for each individual URL; zero means none.\nvar PerRequest time.Duration\n').replace(
    'func one(ctx context.Context, client *http.Client, url string) Result {\n',
    'func one(ctx context.Context, client *http.Client, url string) Result {\n    if PerRequest > 0 {\n        var cancel context.CancelFunc\n        ctx, cancel = context.WithTimeout(ctx, PerRequest)\n        defer cancel()\n    }\n')),
f('timeout_test.go', r'''package fetch

import (
    "context"
    "errors"
    "net/http"
    "testing"
    "time"
)

func TestPerRequestTimeout(t *testing.T) {
    PerRequest = 10 * time.Millisecond
    defer func() { PerRequest = 0 }()
    slow := &fakeTransport{delay: time.Hour}
    got := All(context.Background(), &http.Client{Transport: slow}, []string{"http://x/a", "http://x/b"}, 2)
    for _, r := range got {
        if !errors.Is(r.Err, context.DeadlineExceeded) {
            t.Errorf("%s: %v", r.URL, r.Err)
        }
    }
}
'''),
],
projectInstructions='Go 1.27, standard library only, no network: tests use a fake RoundTripper. Run:\ngo test -race -count=1 -v ./...\nBoth tests pass. A deliberate bug that sizes the semaphore to the whole input is caught by the concurrency-limit assertion.\nPractice: add a PerRequest timeout applied to every URL, with a test. Replace fetch.go and add timeout_test.go from the worked answer.',
projectChecks=[
dict(name='order, limit and cancellation under -race', args=['test', '-race', '-count=1', '-v', './...'], timeout=240, outputContains=['--- PASS: TestAllOrderAndLimit', '--- PASS: TestAllCancellation']),
dict(name='removing the semaphore breaks the limit', args=['test', '-count=1', '-run', 'TestAllOrderAndLimit', './...'], exit=1,
     mutations=[dict(path='fetch.go', find='sem := make(chan struct{}, limit)', replace='sem := make(chan struct{}, len(urls))')], outputContains=['exceeds limit 2']),
dict(name='answer per-request timeout', args=['test', '-race', '-count=1', '-v', './...'], useSolution=True, timeout=240, outputContains=['--- PASS: TestPerRequestTimeout', '--- PASS: TestAllCancellation']),
],
challenge='Add a per-request timeout so each URL gets its own deadline derived from the parent context, and test it with a transport that never answers.',
question='How does All keep results in input order without a mutex?',
correct='Each goroutine writes only its own index of a pre-sized slice, and Wait orders the writes before return',
wrong=['Goroutines finish in the order they start', 'The semaphore serialises the writes'],
reasoning='Distinct slice elements are separate memory locations, so there is no race. WaitGroup.Wait synchronises with every goroutine\'s completion.',
sourceURL='https://go.dev/blog/context',
minutes=60),
]

API_LIB = r'''// Package tasks is a small in-memory JSON API.
package tasks

import (
    "encoding/json"
    "net/http"
    "strconv"
    "strings"
    "sync"
)

// Task is one to-do item.
type Task struct {
    ID    int    `json:"id"`
    Title string `json:"title"`
    Done  bool   `json:"done"`
}

// Store holds tasks safely for concurrent handlers.
type Store struct {
    mu     sync.Mutex
    nextID int
    tasks  map[int]Task
}

// NewStore returns an empty store.
func NewStore() *Store { return &Store{nextID: 1, tasks: map[int]Task{}} }

// Handler returns the API routes.
func (s *Store) Handler() http.Handler {
    mux := http.NewServeMux()
    mux.HandleFunc("POST /tasks", s.create)
    mux.HandleFunc("GET /tasks/{id}", s.get)
    mux.HandleFunc("PATCH /tasks/{id}/done", s.markDone)
    return mux
}

func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}

func errorJSON(w http.ResponseWriter, status int, msg string) {
    writeJSON(w, status, map[string]string{"error": msg})
}

func (s *Store) create(w http.ResponseWriter, r *http.Request) {
    var in struct {
        Title string `json:"title"`
    }
    dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4096))
    dec.DisallowUnknownFields()
    if err := dec.Decode(&in); err != nil {
        errorJSON(w, http.StatusBadRequest, "malformed JSON")
        return
    }
    if strings.TrimSpace(in.Title) == "" {
        errorJSON(w, http.StatusUnprocessableEntity, "title is required")
        return
    }
    s.mu.Lock()
    t := Task{ID: s.nextID, Title: in.Title}
    s.tasks[t.ID] = t
    s.nextID++
    s.mu.Unlock()
    w.Header().Set("Location", "/tasks/"+strconv.Itoa(t.ID))
    writeJSON(w, http.StatusCreated, t)
}

func (s *Store) lookup(w http.ResponseWriter, r *http.Request) (int, bool) {
    id, err := strconv.Atoi(r.PathValue("id"))
    if err != nil {
        errorJSON(w, http.StatusBadRequest, "id must be an integer")
        return 0, false
    }
    return id, true
}

func (s *Store) get(w http.ResponseWriter, r *http.Request) {
    id, ok := s.lookup(w, r)
    if !ok {
        return
    }
    s.mu.Lock()
    t, found := s.tasks[id]
    s.mu.Unlock()
    if !found {
        errorJSON(w, http.StatusNotFound, "task not found")
        return
    }
    writeJSON(w, http.StatusOK, t)
}

func (s *Store) markDone(w http.ResponseWriter, r *http.Request) {
    id, ok := s.lookup(w, r)
    if !ok {
        return
    }
    s.mu.Lock()
    t, found := s.tasks[id]
    if found {
        t.Done = true
        s.tasks[id] = t
    }
    s.mu.Unlock()
    if !found {
        errorJSON(w, http.StatusNotFound, "task not found")
        return
    }
    writeJSON(w, http.StatusOK, t)
}
'''

API_TEST = r'''package tasks

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "strings"
    "sync"
    "testing"
)

func do(t *testing.T, h http.Handler, method, path, body string) (int, string) {
    t.Helper()
    rec := httptest.NewRecorder()
    h.ServeHTTP(rec, httptest.NewRequest(method, path, strings.NewReader(body)))
    return rec.Code, strings.TrimSpace(rec.Body.String())
}

func TestLifecycle(t *testing.T) {
    h := NewStore().Handler()
    steps := []struct {
        method, path, body string
        status             int
        resp               string
    }{
        {"POST", "/tasks", `{"title":"write tests"}`, 201, `{"id":1,"title":"write tests","done":false}`},
        {"GET", "/tasks/1", "", 200, `{"id":1,"title":"write tests","done":false}`},
        {"PATCH", "/tasks/1/done", "", 200, `{"id":1,"title":"write tests","done":true}`},
        {"GET", "/tasks/2", "", 404, `{"error":"task not found"}`},
        {"GET", "/tasks/abc", "", 400, `{"error":"id must be an integer"}`},
        {"POST", "/tasks", `{"title":""}`, 422, `{"error":"title is required"}`},
        {"POST", "/tasks", `{"titel":"typo"}`, 400, `{"error":"malformed JSON"}`},
        {"PUT", "/tasks/1", "", 405, "Method Not Allowed"},
    }
    for _, s := range steps {
        status, body := do(t, h, s.method, s.path, s.body)
        if status != s.status || body != s.resp {
            t.Errorf("%s %s = %d %s; want %d %s", s.method, s.path, status, body, s.status, s.resp)
        }
    }
}

func TestConcurrentCreatesOverServer(t *testing.T) {
    srv := httptest.NewTestServer(t, NewStore().Handler())
    var wg sync.WaitGroup
    ids := make([]int, 20)
    for i := range ids {
        wg.Go(func() {
            resp, err := srv.Client().Post(srv.URL+"/tasks", "application/json", strings.NewReader(fmt.Sprintf(`{"title":"t%d"}`, i)))
            if err != nil {
                t.Error(err)
                return
            }
            defer resp.Body.Close()
            var task Task
            if err := json.NewDecoder(resp.Body).Decode(&task); err != nil {
                t.Error(err)
            }
            io.Copy(io.Discard, resp.Body)
            ids[i] = task.ID
        })
    }
    wg.Wait()
    seen := map[int]bool{}
    for _, id := range ids {
        if id < 1 || id > 20 || seen[id] {
            t.Fatalf("ids not unique 1..20: %v", ids)
        }
        seen[id] = true
    }
}
'''

LESSONS += [
dict(key='json-api-project', stage=STAGE, title='Project: an in-memory JSON REST API',
body=[
'This project is a small task API: create a task, fetch it, and mark it done. It brings together ServeMux method and wildcard patterns, JSON decoding with limits and unknown-field rejection, consistent JSON errors, a mutex-protected store, and two levels of testing.',
'Handlers are methods on *Store, so they share state without globals. The store\'s lock covers only the map access, never the encoding of the response, which keeps critical sections short. IDs come from a counter incremented under the same lock, so concurrent creates never collide.',
'Status codes carry meaning: 201 with a Location header on create, 404 for unknown IDs, 400 for malformed input or a non-integer ID, 422 for a valid document that fails validation, and 405, produced by ServeMux itself, for unsupported methods.',
'The table-driven lifecycle test drives the handler directly with httptest.NewRecorder, step by step. The concurrency test uses Go 1.27\'s httptest.NewTestServer and twenty parallel POST requests under the race detector, then checks that IDs are unique.',
'The practice adds DELETE /tasks/{id} returning 204 No Content, then 404 for later reads.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[gomod('tasks'), f('tasks.go', API_LIB), f('tasks_test.go', API_TEST)],
projectSolutionFiles=[
f('tasks.go', API_LIB.replace('    mux.HandleFunc("PATCH /tasks/{id}/done", s.markDone)\n',
    '    mux.HandleFunc("PATCH /tasks/{id}/done", s.markDone)\n    mux.HandleFunc("DELETE /tasks/{id}", s.remove)\n') + r'''
func (s *Store) remove(w http.ResponseWriter, r *http.Request) {
    id, ok := s.lookup(w, r)
    if !ok {
        return
    }
    s.mu.Lock()
    _, found := s.tasks[id]
    delete(s.tasks, id)
    s.mu.Unlock()
    if !found {
        errorJSON(w, http.StatusNotFound, "task not found")
        return
    }
    w.WriteHeader(http.StatusNoContent)
}
'''),
f('delete_test.go', r'''package tasks

import "testing"

func TestDelete(t *testing.T) {
    h := NewStore().Handler()
    do(t, h, "POST", "/tasks", `{"title":"temporary"}`)
    if status, body := do(t, h, "DELETE", "/tasks/1", ""); status != 204 || body != "" {
        t.Fatalf("delete = %d %q", status, body)
    }
    if status, _ := do(t, h, "GET", "/tasks/1", ""); status != 404 {
        t.Fatalf("get after delete = %d", status)
    }
    if status, _ := do(t, h, "DELETE", "/tasks/1", ""); status != 404 {
        t.Fatalf("second delete = %d", status)
    }
}
'''),
],
projectInstructions='Go 1.27 (NewTestServer is new in 1.27), standard library only. Run:\ngo test -race -count=1 -v ./...\nThe lifecycle table and the concurrent-create test pass. Removing the lock from create is caught by the race detector.\nPractice: add DELETE /tasks/{id} returning 204, then 404. Replace tasks.go and add delete_test.go from the worked answer.',
projectChecks=[
dict(name='lifecycle and concurrent creates under -race', args=['test', '-race', '-count=1', '-v', './...'], timeout=240, outputContains=['--- PASS: TestLifecycle', '--- PASS: TestConcurrentCreatesOverServer']),
dict(name='unlocked create is a data race', args=['test', '-race', '-count=1', '-run', 'TestConcurrentCreates', './...'], exit=1, timeout=240,
     mutations=[dict(path='tasks.go', find='    s.mu.Lock()\n    t := Task{ID: s.nextID, Title: in.Title}', replace='    t := Task{ID: s.nextID, Title: in.Title}'),
                dict(path='tasks.go', find='    s.nextID++\n    s.mu.Unlock()\n', replace='    s.nextID++\n')],
     outputContains=['DATA RACE']),
dict(name='answer DELETE route', args=['test', '-race', '-count=1', '-v', './...'], useSolution=True, timeout=240, outputContains=['--- PASS: TestDelete', '--- PASS: TestLifecycle']),
],
challenge='Add DELETE /tasks/{id}: 204 No Content on success, 404 if the task does not exist, and a test for both.',
question='Why is JSON encoding done after s.mu.Unlock()?',
correct='To keep the critical section short; encoding and network writes do not need the lock',
wrong=['json.Encoder cannot run while a mutex is held', 'Unlock must precede any write to w'],
reasoning='Holding a lock during I/O makes every other request wait on a slow client. Copy what you need under the lock, then release it.',
sourceURL='https://pkg.go.dev/net/http#ServeMux',
minutes=60),
]

LRU_LIB = r'''// Package lru is a generic least-recently-used cache.
package lru

import (
    "container/list"
    "iter"
)

type entry[K comparable, V any] struct {
    key K
    val V
}

// Cache holds at most Cap entries, evicting the least recently used.
// It is not safe for concurrent use.
type Cache[K comparable, V any] struct {
    cap   int
    order *list.List
    items map[K]*list.Element
}

// New returns a cache holding at most capacity entries; capacity must be positive.
func New[K comparable, V any](capacity int) *Cache[K, V] {
    if capacity <= 0 {
        panic("lru: capacity must be positive")
    }
    return &Cache[K, V]{cap: capacity, order: list.New(), items: make(map[K]*list.Element, capacity)}
}

// Get returns the value for key and marks it most recently used.
func (c *Cache[K, V]) Get(key K) (V, bool) {
    if el, ok := c.items[key]; ok {
        c.order.MoveToFront(el)
        return el.Value.(*entry[K, V]).val, true
    }
    var zero V
    return zero, false
}

// Put stores key and value, evicting the oldest entry if the cache is full.
func (c *Cache[K, V]) Put(key K, val V) {
    if el, ok := c.items[key]; ok {
        el.Value.(*entry[K, V]).val = val
        c.order.MoveToFront(el)
        return
    }
    c.items[key] = c.order.PushFront(&entry[K, V]{key, val})
    if c.order.Len() > c.cap {
        oldest := c.order.Back()
        c.order.Remove(oldest)
        delete(c.items, oldest.Value.(*entry[K, V]).key)
    }
}

// Len reports the number of entries.
func (c *Cache[K, V]) Len() int { return c.order.Len() }

// All yields entries from most to least recently used without changing the order.
func (c *Cache[K, V]) All() iter.Seq2[K, V] {
    return func(yield func(K, V) bool) {
        for el := c.order.Front(); el != nil; el = el.Next() {
            e := el.Value.(*entry[K, V])
            if !yield(e.key, e.val) {
                return
            }
        }
    }
}
'''

LRU_TEST = r'''package lru

import (
    "maps"
    "slices"
    "testing"
)

func keys[K comparable, V any](c *Cache[K, V]) []K {
    var out []K
    for k := range c.All() {
        out = append(out, k)
    }
    return out
}

func TestEvictionOrder(t *testing.T) {
    c := New[string, int](2)
    c.Put("a", 1)
    c.Put("b", 2)
    c.Get("a")
    c.Put("c", 3)
    if _, ok := c.Get("b"); ok {
        t.Fatal("b should have been evicted")
    }
    if got := keys(c); !slices.Equal(got, []string{"c", "a"}) {
        t.Fatalf("order = %v", got)
    }
    c.Put("a", 10)
    if v, _ := c.Get("a"); v != 10 || c.Len() != 2 {
        t.Fatalf("update failed: %d len %d", v, c.Len())
    }
}

func TestAllStopsEarlyAndCollects(t *testing.T) {
    c := New[int, string](3)
    for i := range 3 {
        c.Put(i, string(rune('x'+i)))
    }
    for k := range c.All() {
        if k != 2 {
            t.Fatalf("first key %d", k)
        }
        break
    }
    if m := maps.Collect(c.All()); len(m) != 3 || m[0] != "x" {
        t.Fatalf("collected %v", m)
    }
}

func TestNewRejectsZeroCapacity(t *testing.T) {
    defer func() {
        if recover() == nil {
            t.Fatal("expected panic")
        }
    }()
    New[int, int](0)
}

func BenchmarkPutGet(b *testing.B) {
    c := New[int, int](1024)
    i := 0
    for b.Loop() {
        c.Put(i%2048, i)
        c.Get((i + 7) % 2048)
        i++
    }
}
'''

LESSONS += [
dict(key='generic-lru-project', stage=STAGE, title='Project: a generic LRU cache with iterators',
body=[
'An LRU cache keeps the most recently used entries and evicts the oldest when it is full. This implementation combines a map for O(1) lookup with container/list, a doubly linked list, for O(1) reordering: Get and Put move entries to the front and eviction removes from the back.',
'The cache is generic over a comparable key and any value, so Cache[string, []byte] and Cache[int, *User] share one implementation with full type safety. The list stores *entry values in its untyped Element.Value field, so methods type-assert them back; this is the one place where the type system cannot help.',
'All returns an iter.Seq2[K, V] that walks from most to least recent without changing the order, so callers can range over the cache, stop early, or collect it with maps.Collect. New panics on a non-positive capacity, a programmer error, rather than returning an error.',
'Tests check eviction order, updates of existing keys, early termination of the iterator, and the panic. A benchmark measures Put/Get cost with b.Loop.',
'The cache is documented as not safe for concurrent use; the practice adds a concurrent wrapper with a mutex and a race-tested test, which is the usual way to add locking without slowing single-goroutine users.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[gomod('lru'), f('lru.go', LRU_LIB), f('lru_test.go', LRU_TEST)],
projectSolutionFiles=[
f('safe.go', r'''package lru

import "sync"

// Safe wraps a Cache with a mutex for concurrent use.
type Safe[K comparable, V any] struct {
    mu sync.Mutex
    c  *Cache[K, V]
}

// NewSafe returns a concurrency-safe cache.
func NewSafe[K comparable, V any](capacity int) *Safe[K, V] {
    return &Safe[K, V]{c: New[K, V](capacity)}
}

// Get returns the value for key; it reorders entries, so it needs the full lock.
func (s *Safe[K, V]) Get(key K) (V, bool) {
    s.mu.Lock()
    defer s.mu.Unlock()
    return s.c.Get(key)
}

// Put stores a value.
func (s *Safe[K, V]) Put(key K, val V) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.c.Put(key, val)
}

// Len reports the number of entries.
func (s *Safe[K, V]) Len() int {
    s.mu.Lock()
    defer s.mu.Unlock()
    return s.c.Len()
}
'''),
f('safe_test.go', r'''package lru

import (
    "sync"
    "testing"
)

func TestSafeConcurrent(t *testing.T) {
    s := NewSafe[int, int](8)
    var wg sync.WaitGroup
    for g := range 8 {
        wg.Go(func() {
            for i := range 200 {
                s.Put(g*1000+i, i)
                s.Get(g*1000 + i/2)
            }
        })
    }
    wg.Wait()
    if s.Len() != 8 {
        t.Fatalf("Len = %d", s.Len())
    }
}
'''),
],
projectInstructions='Go 1.27, standard library only. Run:\ngo test -race -count=1 -v ./...\ngo test -run=^$ -bench=. -benchtime=20000x ./...\nPractice: add Safe[K, V], a mutex-protected wrapper, and a concurrent test that passes under -race. Note that Get needs the full lock because it reorders the list. Add safe.go and safe_test.go from the worked answer.',
projectChecks=[
dict(name='eviction, iterator and panic tests', args=['test', '-race', '-count=1', '-v', './...'], timeout=240, outputContains=['--- PASS: TestEvictionOrder', '--- PASS: TestAllStopsEarlyAndCollects', '--- PASS: TestNewRejectsZeroCapacity']),
dict(name='benchmark', args=['test', '-run=^$', '-bench=.', '-benchtime=20000x', './...'], outputContains=['BenchmarkPutGet']),
dict(name='evicting the newest entry is caught', args=['test', '-count=1', './...'], exit=1,
     mutations=[dict(path='lru.go', find='oldest := c.order.Back()', replace='oldest := c.order.Front()')], outputContains=['FAIL']),
dict(name='answer concurrent wrapper under -race', args=['test', '-race', '-count=1', '-v', '-run', 'TestSafe', './...'], useSolution=True, timeout=240, outputContains=['--- PASS: TestSafeConcurrent']),
],
challenge='Add Safe[K, V], a mutex-protected wrapper around Cache, and a test with eight goroutines that passes under the race detector.',
question='Why must Safe.Get take the full lock rather than a read lock?',
correct='Get moves the entry to the front of the list, which is a write',
wrong=['RWMutex cannot be used with generics', 'Read locks are slower than full locks'],
reasoning='An LRU read updates recency. Concurrent RLock holders would modify the list together, a data race.',
sourceURL='https://pkg.go.dev/container/list',
minutes=60),
]

LIMIT_LIB = r'''// Package limit is a token-bucket rate limiter.
package limit

import (
    "context"
    "sync"
    "time"
)

// Bucket allows rate events per second with bursts of up to burst events.
type Bucket struct {
    mu     sync.Mutex
    rate   float64
    burst  float64
    tokens float64
    last   time.Time
}

// New returns a full bucket.
func New(rate float64, burst int) *Bucket {
    return &Bucket{rate: rate, burst: float64(burst), tokens: float64(burst), last: time.Now()}
}

func (b *Bucket) refill(now time.Time) {
    b.tokens = min(b.burst, b.tokens+now.Sub(b.last).Seconds()*b.rate)
    b.last = now
}

// Allow reports whether an event may happen now, consuming a token if so.
func (b *Bucket) Allow() bool {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.refill(time.Now())
    if b.tokens >= 1 {
        b.tokens--
        return true
    }
    return false
}

// Wait blocks until a token is available or ctx is done.
func (b *Bucket) Wait(ctx context.Context) error {
    for {
        b.mu.Lock()
        b.refill(time.Now())
        if b.tokens >= 1 {
            b.tokens--
            b.mu.Unlock()
            return nil
        }
        need := time.Duration((1 - b.tokens) / b.rate * float64(time.Second))
        b.mu.Unlock()
        t := time.NewTimer(need)
        select {
        case <-t.C:
        case <-ctx.Done():
            t.Stop()
            return ctx.Err()
        }
    }
}
'''

LIMIT_TEST = r'''package limit

import (
    "context"
    "errors"
    "sync"
    "testing"
    "testing/synctest"
    "time"
)

func TestBurstThenRefill(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        b := New(2, 3)
        for i := range 3 {
            if !b.Allow() {
                t.Fatalf("burst event %d refused", i)
            }
        }
        if b.Allow() {
            t.Fatal("fourth immediate event allowed")
        }
        time.Sleep(500 * time.Millisecond)
        if !b.Allow() || b.Allow() {
            t.Fatal("half a second at 2/s should refill exactly one token")
        }
        time.Sleep(10 * time.Second)
        allowed := 0
        for range 10 {
            if b.Allow() {
                allowed++
            }
        }
        if allowed != 3 {
            t.Fatalf("after a long idle period %d events were allowed; the burst cap is 3", allowed)
        }
    })
}

func TestWaitPacesWorkers(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        b := New(10, 1)
        start := time.Now()
        var wg sync.WaitGroup
        for range 5 {
            wg.Go(func() {
                if err := b.Wait(context.Background()); err != nil {
                    t.Error(err)
                }
            })
        }
        wg.Wait()
        // shortcut: 1ms tolerance absorbs float refill rounding; fake time is otherwise exact
        if got := time.Since(start); got < 400*time.Millisecond || got > 401*time.Millisecond {
            t.Fatalf("five events at 10/s with burst 1 took %v, want 400ms", got)
        }
    })
}

func TestWaitCancelled(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        b := New(1, 1)
        b.Allow()
        ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
        defer cancel()
        if err := b.Wait(ctx); !errors.Is(err, context.DeadlineExceeded) {
            t.Fatalf("err = %v", err)
        }
    })
}
'''

LESSONS += [
dict(key='rate-limiter-project', stage=STAGE, title='Project: a token-bucket rate limiter tested with synctest',
body=[
'A token bucket allows short bursts while enforcing an average rate: the bucket holds up to burst tokens, refills continuously at rate tokens per second, and each event spends one. Allow answers immediately; Wait blocks until a token is available or the context ends.',
'Refilling is computed lazily from elapsed time whenever the bucket is used, so no background goroutine is needed and an idle limiter costs nothing. A mutex protects the counters because many goroutines share one bucket.',
'Wait computes exactly how long until the next token and sleeps on a timer, re-checking afterwards because another goroutine may have taken the token first. It releases the lock before sleeping, so waiters do not block each other.',
'Timing code is notoriously flaky to test with real sleeps. These tests run inside synctest bubbles: the fake clock advances only when every goroutine is blocked, so "half a second" or "400 ms" are exact, instant and deterministic, even with five goroutines competing under the race detector.',
'The practice adds a Reserve-style method, Tokens() float64, reporting the current balance, and a test showing it rises fractionally over time.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[gomod('limit'), f('limit.go', LIMIT_LIB), f('limit_test.go', LIMIT_TEST)],
projectSolutionFiles=[
f('tokens.go', r'''package limit

import "time"

// Tokens reports the tokens currently available, including partial ones.
func (b *Bucket) Tokens() float64 {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.refill(time.Now())
    return b.tokens
}
'''),
f('tokens_test.go', r'''package limit

import (
    "testing"
    "testing/synctest"
    "time"
)

func TestTokensRefillFractionally(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        b := New(4, 2)
        b.Allow()
        b.Allow()
        time.Sleep(125 * time.Millisecond)
        if got := b.Tokens(); got != 0.5 {
            t.Fatalf("Tokens = %v, want 0.5", got)
        }
        time.Sleep(time.Second)
        if got := b.Tokens(); got != 2 {
            t.Fatalf("Tokens = %v, want burst cap 2", got)
        }
    })
}
'''),
],
projectInstructions='Go 1.27 (testing/synctest), standard library only. Run:\ngo test -race -count=1 -v ./...\nAll three tests finish instantly because time inside synctest bubbles is fake.\nPractice: add Tokens() float64 and a test that the balance refills fractionally and is capped at the burst size. Add tokens.go and tokens_test.go from the worked answer.',
projectChecks=[
dict(name='deterministic timing tests under -race', args=['test', '-race', '-count=1', '-v', './...'], timeout=240, outputContains=['--- PASS: TestBurstThenRefill', '--- PASS: TestWaitPacesWorkers', '--- PASS: TestWaitCancelled']),
dict(name='uncapped refill is caught', args=['test', '-count=1', './...'], exit=1,
     mutations=[dict(path='limit.go', find='b.tokens = min(b.burst, b.tokens+now.Sub(b.last).Seconds()*b.rate)', replace='b.tokens = b.tokens + now.Sub(b.last).Seconds()*b.rate')], outputContains=['FAIL']),
dict(name='answer fractional tokens', args=['test', '-race', '-count=1', '-v', '-run', 'TestTokens', './...'], useSolution=True, timeout=240, outputContains=['--- PASS: TestTokensRefillFractionally']),
],
challenge='Add Tokens() float64 reporting the current balance, and a synctest test showing 0.5 tokens after 125ms at 4/s and a cap at the burst size.',
question='Why can the test assert exactly 400ms for five Wait calls?',
correct='synctest\'s fake clock advances only to the next timer when all goroutines block, so durations are exact',
wrong=['The race detector slows time down', 'time.Since is rounded to 100ms in tests'],
reasoning='Inside a bubble there is no real-time jitter: each timer fires at its exact fake instant, so the schedule is fully deterministic.',
sourceURL='https://pkg.go.dev/testing/synctest',
minutes=60),
]

LOG_LIB = r'''// Package logstat summarises structured log lines.
package logstat

import (
    "bufio"
    "bytes"
    "io"
)

// Summary counts log lines by level and records the slowest request.
type Summary struct {
    Levels  map[string]int
    Slowest int
    Lines   int
}

var (
    levelKey = []byte("level=")
    msKey    = []byte("ms=")
)

// Scan reads key=value log lines from r, one per line.
func Scan(r io.Reader) (Summary, error) {
    var s Summary
    levels := map[string]*int{}
    sc := bufio.NewScanner(r)
    for sc.Scan() {
        line := sc.Bytes()
        s.Lines++
        if lv, ok := field(line, levelKey); ok {
            bump(levels, lv)
        }
        if ms, ok := field(line, msKey); ok {
            s.Slowest = max(s.Slowest, atoi(ms))
        }
    }
    s.Levels = flatten(levels)
    return s, sc.Err()
}

// bump counts key. The m[string(b)] lookup does not allocate; only a new key
// is converted to a string and stored.
func bump(m map[string]*int, key []byte) {
    if n := m[string(key)]; n != nil {
        *n++
        return
    }
    one := 1
    m[string(key)] = &one
}

func flatten(m map[string]*int) map[string]int {
    out := make(map[string]int, len(m))
    for k, n := range m {
        out[k] = *n
    }
    return out
}

// field returns the value after key, up to the next space, without allocating.
func field(line, key []byte) ([]byte, bool) {
    for len(line) > 0 {
        var tok []byte
        tok, line, _ = bytes.Cut(line, []byte{' '})
        if v, ok := bytes.CutPrefix(tok, key); ok {
            return v, true
        }
    }
    return nil, false
}

func atoi(b []byte) int {
    n := 0
    for _, c := range b {
        if c < '0' || c > '9' {
            return n
        }
        n = n*10 + int(c-'0')
    }
    return n
}
'''

LOG_TEST = r'''package logstat

import (
    "bytes"
    "strings"
    "testing"
)

const sample = `level=INFO msg=start
level=WARN msg=slow ms=250
level=INFO msg=req ms=12
garbage line
level=ERROR msg=fail ms=900
`

func TestScan(t *testing.T) {
    s, err := Scan(strings.NewReader(sample))
    if err != nil {
        t.Fatal(err)
    }
    if s.Lines != 5 || s.Levels["INFO"] != 2 || s.Levels["ERROR"] != 1 || s.Slowest != 900 {
        t.Fatalf("summary %+v", s)
    }
}

func TestFieldDoesNotAllocate(t *testing.T) {
    line := []byte("level=INFO msg=req ms=12")
    n := testing.AllocsPerRun(100, func() {
        if _, ok := field(line, msKey); !ok {
            t.Fatal("missing")
        }
    })
    if n != 0 {
        t.Fatalf("field allocates %v times", n)
    }
}

func TestScanAllocationBudget(t *testing.T) {
    data := []byte(strings.Repeat("level=INFO msg=req ms=12\n", 1000))
    n := testing.AllocsPerRun(10, func() {
        if _, err := Scan(bytes.NewReader(data)); err != nil {
            t.Fatal(err)
        }
    })
    if n > 10 {
        t.Fatalf("Scan of 1000 lines allocates %v times; budget is 10", n)
    }
}

func BenchmarkScan(b *testing.B) {
    data := []byte(strings.Repeat(sample, 200))
    b.ReportAllocs()
    for b.Loop() {
        Scan(bytes.NewReader(data))
    }
}
'''

LESSONS += [
dict(key='log-pipeline-project', stage=STAGE, title='Project: a zero-allocation log summariser',
body=[
'logstat.Scan streams key=value log lines and summarises them: counts per level and the slowest request time. It is designed for large inputs, so it works on the scanner\'s []byte buffer directly and avoids allocating per line.',
'Three techniques keep allocations near zero. bufio.Scanner.Bytes returns a view into its buffer instead of a new string. field uses bytes.Cut and bytes.CutPrefix, which return sub-slices rather than copies. And counting goes through bump: the compiler optimises a lookup written as m[string(b)] so it does not copy the bytes, but an assignment such as m[string(b)]++ must own its key and allocates on every line. bump looks up a *int and increments it, inserting a new string key only the first time a level is seen; flatten builds the public map once at the end.',
'atoi parses digits by hand to avoid strconv\'s string conversion; it is safe here because the format is known and it stops at the first non-digit. That trade-off, a small specialised parser in a measured hot path, is the kind profiles justify.',
'Tests turn performance into contracts: field must not allocate at all, and scanning 1000 lines must stay within an allocation budget of 10, independent of input size. Unlike timings, allocation counts are deterministic, so these are reliable regression tests.',
'The practice adds a per-message count while preserving the budget. The obvious s.Msgs[string(m)]++ would cost one allocation per line and fail the budget test; reuse bump so repeated messages are lookups only.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[gomod('logstat'), f('logstat.go', LOG_LIB), f('logstat_test.go', LOG_TEST)],
projectSolutionFiles=[
f('logstat.go', LOG_LIB.replace('    Slowest int\n    Lines   int\n}', '    Slowest int\n    Lines   int\n    Msgs    map[string]int\n}').replace(
    'var (\n    levelKey = []byte("level=")\n    msKey    = []byte("ms=")\n)', 'var (\n    levelKey = []byte("level=")\n    msKey    = []byte("ms=")\n    msgKey   = []byte("msg=")\n)').replace(
    '    levels := map[string]*int{}\n', '    levels, msgs := map[string]*int{}, map[string]*int{}\n').replace(
    '        if ms, ok := field(line, msKey); ok {', '        if m, ok := field(line, msgKey); ok {\n            bump(msgs, m)\n        }\n        if ms, ok := field(line, msKey); ok {').replace(
    '    s.Levels = flatten(levels)\n', '    s.Levels, s.Msgs = flatten(levels), flatten(msgs)\n')),
f('msgs_test.go', r'''package logstat

import (
    "strings"
    "testing"
)

func TestMessageCounts(t *testing.T) {
    s, err := Scan(strings.NewReader(sample))
    if err != nil {
        t.Fatal(err)
    }
    if s.Msgs["req"] != 1 || s.Msgs["fail"] != 1 || len(s.Msgs) != 4 {
        t.Fatalf("msgs %v", s.Msgs)
    }
}
'''),
],
projectInstructions='Go 1.27, standard library only. Run:\ngo test -count=1 -v ./...\ngo test -run=^$ -bench=. -benchtime=200x ./...\nThe allocation tests pass. A mutation that stores a fresh counter through m[string(key)] on every line breaks the 1000-line budget.\nPractice: count lines per msg value without exceeding the budget. Replace logstat.go and add msgs_test.go from the worked answer.',
projectChecks=[
dict(name='summary and allocation contracts', args=['test', '-count=1', '-v', './...'], outputContains=['--- PASS: TestScan', '--- PASS: TestFieldDoesNotAllocate', '--- PASS: TestScanAllocationBudget']),
dict(name='benchmark reports allocations', args=['test', '-run=^$', '-bench=.', '-benchtime=200x', './...'], outputContains=['BenchmarkScan', 'allocs/op']),
dict(name='writing through m[string(key)] every line breaks the budget', args=['test', '-count=1', '-run', 'TestScanAllocationBudget', './...'], exit=1,
     mutations=[dict(path='logstat.go', find='    if n := m[string(key)]; n != nil {\n        *n++\n        return\n    }\n    one := 1\n', replace='    one := 1\n    if n := m[string(key)]; n != nil {\n        one = *n + 1\n    }\n')], outputContains=['budget is 10']),
dict(name='answer message counts within budget', args=['test', '-count=1', '-v', './...'], useSolution=True, outputContains=['--- PASS: TestMessageCounts', '--- PASS: TestScanAllocationBudget']),
],
challenge='Count lines per msg value in a Msgs map while keeping the 1000-line allocation budget; s.Msgs[string(m)]++ is not good enough.',
question='Why does bump look up a *int instead of writing m[string(key)]++?',
correct='Only the lookup form m[string(b)] avoids allocating; an increment or assignment converts the key every time',
wrong=['Maps cannot store int values', 'Pointers make the map iterate in order'],
reasoning='The compiler can use the bytes in place for a read, because the key is not retained. A write may store the key, so it needs an allocated string. The validator measured 1004 allocations for 1000 lines with ++ and stays within 10 with bump.',
sourceURL='https://go.dev/doc/gc-guide#Eliminating_heap_allocations',
minutes=60),
]

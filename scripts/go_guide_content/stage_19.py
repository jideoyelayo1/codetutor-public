STAGE = '19 · Design and idioms'

LESSONS = [
dict(key='useful-zero-values', stage=STAGE, title='Make the zero value useful',
body=[
'Idiomatic Go types work without a constructor: var buf bytes.Buffer, var mu sync.Mutex and var wg sync.WaitGroup are ready to use. Design your types the same way, so a zero struct is a valid, empty instance and users cannot forget to initialise it.',
'Techniques: lazily create maps on first write, treat nil slices as empty, use zero numbers as "use the default", and make methods on a nil pointer receiver behave sensibly when that is natural, as in a linked list where nil is the empty list.',
'When a zero value cannot be valid, for example a client that needs a URL, provide a New function and make the type\'s fields unexported so the invalid state cannot be built from outside the package.',
],
code=r'''package main

import (
    "fmt"
    "strings"
)

type Registry struct {
    entries map[string]string
    Sep     string
}

func (r *Registry) Add(k, v string) {
    if r.entries == nil {
        r.entries = map[string]string{}
    }
    r.entries[k] = v
}

func (r *Registry) Get(k string) string { return r.entries[k] }

func (r *Registry) Join(keys ...string) string {
    sep := r.Sep
    if sep == "" {
        sep = ","
    }
    vals := make([]string, len(keys))
    for i, k := range keys {
        vals[i] = r.Get(k)
    }
    return strings.Join(vals, sep)
}

func main() {
    var r Registry
    fmt.Printf("%q\n", r.Get("missing"))
    r.Add("a", "1")
    r.Add("b", "2")
    fmt.Println(r.Join("a", "b"))
}
''',
expectedStdout='""\n1,2\n',
challenge='Write a linked list type type List struct{ head *node; n int } whose zero value is an empty list, with Push(v int) and Len() int; print the length after pushing twice and of an untouched list.',
solution=r'''package main

import "fmt"

type node struct {
    v    int
    next *node
}

type List struct {
    head *node
    n    int
}

func (l *List) Push(v int) {
    l.head = &node{v, l.head}
    l.n++
}

func (l *List) Len() int { return l.n }

func main() {
    var a, b List
    a.Push(1)
    a.Push(2)
    fmt.Println(a.Len(), b.Len())
}
''',
solutionStdout='2 0\n',
question='Why can Registry.Get be called before any Add?',
correct='Reading a nil map returns the zero value, so the empty registry is valid',
wrong=['Get creates the map automatically', 'Methods on zero structs are skipped'],
reasoning='Only writes need the map to exist. Lazy creation in Add keeps the zero Registry fully usable.',
sourceURL='https://go.dev/doc/effective_go#allocation_new'),

dict(key='functional-options', stage=STAGE, title='Constructors, functional options and config structs',
body=[
'When a constructor has several optional settings, avoid long parameter lists. Two idioms are common: a Config struct passed by value whose zero fields mean defaults, and functional options, variadic func(*Server) values such as WithTimeout(5*time.Second).',
'Functional options keep the common call short (NewServer(addr)), let new options be added without breaking callers, and can validate as they apply. A Config struct is simpler, self-documenting, and easy to load from files; prefer it unless options need logic.',
'Either way, validate in the constructor and return an error rather than building an invalid object. Keep defaults in one place.',
],
code=r'''package main

import (
    "errors"
    "fmt"
    "time"
)

type Server struct {
    addr    string
    timeout time.Duration
    retries int
}

type Option func(*Server) error

func WithTimeout(d time.Duration) Option {
    return func(s *Server) error {
        if d <= 0 {
            return errors.New("timeout must be positive")
        }
        s.timeout = d
        return nil
    }
}

func WithRetries(n int) Option {
    return func(s *Server) error {
        s.retries = n
        return nil
    }
}

func NewServer(addr string, opts ...Option) (*Server, error) {
    s := &Server{addr: addr, timeout: 30 * time.Second, retries: 3}
    for _, opt := range opts {
        if err := opt(s); err != nil {
            return nil, fmt.Errorf("new server: %w", err)
        }
    }
    return s, nil
}

func main() {
    a, _ := NewServer(":8080")
    b, _ := NewServer(":9090", WithTimeout(time.Second), WithRetries(0))
    fmt.Println(a.timeout, a.retries, b.timeout, b.retries)
    _, err := NewServer(":1", WithTimeout(-1))
    fmt.Println(err)
}
''',
expectedStdout='30s 3 1s 0\nnew server: timeout must be positive\n',
challenge='Rewrite the constructor in Config-struct style: type Config struct{ Timeout time.Duration; Retries *int }, where a nil Retries means the default 3. Print the effective values for Config{} and Config{Retries: new(0)}.',
solution=r'''package main

import (
    "fmt"
    "time"
)

type Config struct {
    Timeout time.Duration
    Retries *int
}

type Server struct {
    timeout time.Duration
    retries int
}

func New(cfg Config) *Server {
    s := &Server{timeout: 30 * time.Second, retries: 3}
    if cfg.Timeout > 0 {
        s.timeout = cfg.Timeout
    }
    if cfg.Retries != nil {
        s.retries = *cfg.Retries
    }
    return s
}

func main() {
    a, b := New(Config{}), New(Config{Retries: new(0)})
    fmt.Println(a.timeout, a.retries, b.timeout, b.retries)
}
''',
solutionStdout='30s 3 30s 0\n',
question='Why does the Config solution use *int for Retries?',
correct='To distinguish "not set" from an explicit 0',
wrong=['Pointers are faster to copy', 'Config structs cannot contain ints'],
reasoning='The zero value of int is 0, which might be a real choice. A nil pointer means "use the default"; new(0) (Go 1.26) sets an explicit zero.',
sourceURL='https://go.dev/blog/module-compatibility',
additionalReadings=[dict(title='Self-referential functions and the design of options', url='https://commandcenter.blogspot.com/2014/01/self-referential-functions-and-design.html', section='Functional options')]),

dict(key='accept-interfaces', stage=STAGE, title='Accept interfaces, return concrete types',
body=[
'Functions should accept the smallest interface they need, such as io.Reader rather than *os.File, so callers can pass files, buffers, network connections or test doubles. They should return concrete types, so callers get every method and future additions do not break them.',
'Returning an interface hides capabilities and makes adding methods a breaking change for implementers. The exception is a constructor that genuinely chooses among implementations, or the error interface.',
'Test doubles follow naturally: a fake that implements the consumer\'s small interface replaces a database or HTTP client in tests, with no mocking framework.',
],
code=r'''package main

import (
    "bufio"
    "fmt"
    "io"
    "strings"
)

type Stats struct {
    Lines, Words int
}

func Count(r io.Reader) (Stats, error) {
    var s Stats
    sc := bufio.NewScanner(r)
    for sc.Scan() {
        s.Lines++
        s.Words += len(strings.Fields(sc.Text()))
    }
    return s, sc.Err()
}

type failingReader struct{}

func (failingReader) Read([]byte) (int, error) { return 0, fmt.Errorf("disk unplugged") }

func main() {
    fmt.Println(Count(strings.NewReader("accept interfaces\nreturn structs\n")))
    fmt.Println(Count(failingReader{}))
}
''',
expectedStdout='{2 4} <nil>\n{0 0} disk unplugged\n',
challenge='Define a one-method interface Clock{ Now() time.Time } used by func greeting(c Clock) string returning "morning" before noon and "afternoon" otherwise; test it with a fake clock fixed at 09:00 and 15:00.',
solution=r'''package main

import (
    "fmt"
    "time"
)

type Clock interface{ Now() time.Time }

type fixed time.Time

func (f fixed) Now() time.Time { return time.Time(f) }

func greeting(c Clock) string {
    if c.Now().Hour() < 12 {
        return "morning"
    }
    return "afternoon"
}

func main() {
    day := time.Date(2026, 10, 17, 0, 0, 0, 0, time.UTC)
    fmt.Println(greeting(fixed(day.Add(9*time.Hour))), greeting(fixed(day.Add(15*time.Hour))))
}
''',
solutionStdout='morning afternoon\n',
question='Why return *Store rather than a StoreInterface from NewStore?',
correct='Callers get the full concrete API, and adding methods later breaks nobody',
wrong=['Interfaces cannot be returned from functions', 'Concrete types are always faster to call'],
reasoning='Consumers can define the small interface they need themselves. Returning an interface fixes a method set that is costly to change.',
sourceURL='https://go.dev/wiki/CodeReviewComments#interfaces'),

dict(key='package-layout', stage=STAGE, title='Package and project layout',
body=[
'Start small: a single package at the module root is fine for a library, and a single main package for a command. Split packages when a part has a clear, independent purpose and a small API, not to mirror layers such as models/controllers/utils.',
'Conventions from the official module layout guide: commands under cmd/name/, private shared code under internal/, and packages named for what they provide. Avoid import cycles by keeping dependencies flowing one way, with lower-level packages unaware of higher-level ones.',
'Package names are short, lower-case and singular (http, json, user). Avoid stutter in exported names: user.New, not user.NewUser. Unit tests sit next to the code; larger test data goes in testdata/, which the go tool ignores.',
],
code=r'''package main

import (
    "fmt"
    "path"
    "strings"
)

func stutters(pkg, name string) bool {
    return strings.HasPrefix(strings.ToLower(name), pkg)
}

func main() {
    layout := []string{"go.mod", "cmd/server/main.go", "internal/store/store.go", "user/user.go", "user/testdata/users.json"}
    for _, p := range layout {
        fmt.Printf("%-26s package dir: %s\n", p, path.Dir(p))
    }
    fmt.Println(stutters("user", "UserService"), stutters("user", "Service"))
}
''',
expectedStdout='go.mod                     package dir: .\ncmd/server/main.go         package dir: cmd/server\ninternal/store/store.go    package dir: internal/store\nuser/user.go               package dir: user\nuser/testdata/users.json   package dir: user/testdata\ntrue false\n',
challenge='Write func goodName(pkg string) bool that rejects package names containing upper-case letters, underscores or the words "util", "common" or "misc"; print results for "http", "my_pkg", "utils" and "Store".',
solution=r'''package main

import (
    "fmt"
    "strings"
)

func goodName(pkg string) bool {
    if pkg != strings.ToLower(pkg) || strings.Contains(pkg, "_") {
        return false
    }
    for _, vague := range []string{"util", "common", "misc"} {
        if strings.Contains(pkg, vague) {
            return false
        }
    }
    return true
}

func main() {
    for _, p := range []string{"http", "my_pkg", "utils", "Store"} {
        fmt.Println(p, goodName(p))
    }
}
''',
solutionStdout='http true\nmy_pkg false\nutils false\nStore false\n',
question='Where should a module\'s private helper packages live?',
correct='Under internal/, so other modules cannot import them',
wrong=['Under pkg/, which the go tool treats as private', 'In a utils package at the root'],
reasoning='internal/ is enforced by the go command. pkg/ is only a convention with no special meaning.',
sourceURL='https://go.dev/doc/modules/layout'),

dict(key='concurrency-api-design', stage=STAGE, title='Designing concurrent APIs',
body=[
'Prefer synchronous APIs: a function that does its work and returns lets callers add concurrency with go and a WaitGroup if they want it. An API that starts goroutines internally must say who stops them, usually by taking a context and providing Close or Stop, and must wait for them before returning from Close.',
'Make ownership clear. Whoever starts a goroutine is responsible for its exit. Channels in signatures should have directions, and the side that sends should be the side that closes.',
'Document whether a type is safe for concurrent use. Many standard types are not (maps, bytes.Buffer, strings.Builder); http.Client and *sql.DB are. Hide locks inside the type rather than asking callers to lock.',
],
code=r'''package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

type Ticker struct {
    cancel context.CancelFunc
    wg     sync.WaitGroup
    mu     sync.Mutex
    ticks  int
}

func StartTicker(ctx context.Context, every time.Duration) *Ticker {
    ctx, cancel := context.WithCancel(ctx)
    t := &Ticker{cancel: cancel}
    t.wg.Go(func() {
        tk := time.NewTicker(every)
        defer tk.Stop()
        for {
            select {
            case <-ctx.Done():
                return
            case <-tk.C:
                t.mu.Lock()
                t.ticks++
                t.mu.Unlock()
            }
        }
    })
    return t
}

func (t *Ticker) Close() int {
    t.cancel()
    t.wg.Wait()
    t.mu.Lock()
    defer t.mu.Unlock()
    return t.ticks
}

func main() {
    t := StartTicker(context.Background(), time.Millisecond)
    time.Sleep(20 * time.Millisecond)
    n := t.Close()
    fmt.Println(n > 0)
}
''',
expectedStdout='true\n',
race=True,
challenge='Give Ticker a Ticks() int method that is safe to call concurrently with the goroutine, and call it from three goroutines before Close; print whether Close returned a value at least as large as each observed count.',
solution=r'''package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

type Ticker struct {
    cancel context.CancelFunc
    wg     sync.WaitGroup
    mu     sync.Mutex
    ticks  int
}

func StartTicker(ctx context.Context, every time.Duration) *Ticker {
    ctx, cancel := context.WithCancel(ctx)
    t := &Ticker{cancel: cancel}
    t.wg.Go(func() {
        tk := time.NewTicker(every)
        defer tk.Stop()
        for {
            select {
            case <-ctx.Done():
                return
            case <-tk.C:
                t.mu.Lock()
                t.ticks++
                t.mu.Unlock()
            }
        }
    })
    return t
}

func (t *Ticker) Ticks() int {
    t.mu.Lock()
    defer t.mu.Unlock()
    return t.ticks
}

func (t *Ticker) Close() int {
    t.cancel()
    t.wg.Wait()
    return t.Ticks()
}

func main() {
    t := StartTicker(context.Background(), time.Millisecond)
    time.Sleep(5 * time.Millisecond)
    seen := make([]int, 3)
    var wg sync.WaitGroup
    for i := range seen {
        wg.Go(func() { seen[i] = t.Ticks() })
    }
    wg.Wait()
    final := t.Close()
    fmt.Println(final >= max(seen[0], seen[1], seen[2]))
}
''',
solutionStdout='true\n',
question='What must Close do for a type that starts its own goroutine?',
correct='Signal the goroutine to stop and wait until it has exited',
wrong=['Only cancel the context and return immediately', 'Nothing; goroutines end when the type is garbage collected'],
reasoning='Returning before the goroutine exits leaves it running, possibly touching freed resources. Wait makes shutdown deterministic.',
sourceURL='https://go.dev/wiki/CodeReviewComments#goroutine-lifetimes'),
]

STAGE = '06 · Errors, panic and recovery'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='error-values', stage=STAGE, title='Errors are values: return, check, add context',
body=[
'error is a predeclared interface with one method, Error() string. Functions that can fail return an error as their last result, and callers check it immediately: if err != nil { return ..., err }. Errors are ordinary values, so they can be stored, compared, wrapped and inspected.',
'errors.New and fmt.Errorf create errors. Messages are lower-case, without trailing punctuation, because they are often joined into chains such as "load config: open app.toml: no such file or directory".',
'Handle each error once: either deal with it (retry, use a default, report it) or return it with added context. Logging an error and also returning it produces duplicate reports further up the stack.',
],
code=r'''package main

import (
    "errors"
    "fmt"
    "strconv"
)

func parseAge(s string) (int, error) {
    n, err := strconv.Atoi(s)
    if err != nil {
        return 0, fmt.Errorf("parse age %q: %w", s, err)
    }
    if n < 0 {
        return 0, errors.New("age cannot be negative")
    }
    return n, nil
}

func main() {
    for _, in := range []string{"36", "-1", "old"} {
        age, err := parseAge(in)
        if err != nil {
            fmt.Println("error:", err)
            continue
        }
        fmt.Println("age", age)
    }
}
''',
expectedStdout='age 36\nerror: age cannot be negative\nerror: parse age "old": strconv.Atoi: parsing "old": invalid syntax\n',
challenge='Write func safeDiv(a, b int) (int, error) that returns an error "division by zero" for b == 0; print the results of safeDiv(7, 2) and safeDiv(1, 0).',
solution=r'''package main

import (
    "errors"
    "fmt"
)

func safeDiv(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

func main() {
    fmt.Println(safeDiv(7, 2))
    fmt.Println(safeDiv(1, 0))
}
''',
solutionStdout='3 <nil>\n0 division by zero\n',
question='What is the idiomatic way to handle an error you cannot resolve locally?',
correct='Return it with added context, without also logging it',
wrong=['Log it and return it so nothing is missed', 'Panic so the caller notices'],
reasoning='Each error should be handled once. Adding context while returning builds a readable chain for whoever finally handles it.',
sourceURL='https://go.dev/blog/errors-are-values',
additionalReadings=[dict(title='Go Code Review Comments: error strings', url='https://go.dev/wiki/CodeReviewComments#error-strings', section='Error strings')]),

dict(key='wrapping-is-as', stage=STAGE, title='Wrapping with %w, errors.Is, errors.As and errors.AsType',
body=[
'fmt.Errorf with %w wraps an error: the new error\'s message includes the old one, and errors.Unwrap returns the original. %v includes the message but breaks the chain, which is right when you deliberately hide an implementation detail.',
'errors.Is(err, target) walks the chain looking for an error equal to target, for sentinels such as io.EOF or fs.ErrNotExist. errors.As(err, &target) walks the chain looking for an error assignable to target\'s type and stores it, for typed errors such as *fs.PathError.',
'Go 1.26 adds the generic errors.AsType[E](err) (E, bool), which returns the matching error directly instead of needing a pointer variable, and is checked at compile time. Prefer it in new code that targets 1.26 or later.',
'Never compare wrapped errors with ==; use errors.Is. go vet reports %w used with a non-error operand, and Go 1.27\'s vet also reports %w given a pointer to an error.',
],
code=r'''package main

import (
    "errors"
    "fmt"
    "io/fs"
    "os"
)

func load(path string) error {
    _, err := os.ReadFile(path)
    if err != nil {
        return fmt.Errorf("load settings: %w", err)
    }
    return nil
}

func main() {
    err := load("/definitely/missing.toml")
    fmt.Println(errors.Is(err, fs.ErrNotExist))
    if pe, ok := errors.AsType[*fs.PathError](err); ok {
        fmt.Println(pe.Op, pe.Path)
    }
    var old *fs.PathError
    fmt.Println(errors.As(err, &old), err == fs.ErrNotExist)
}
''',
expectedStdout='true\nopen /definitely/missing.toml\ntrue false\n',
challenge='Wrap io.EOF twice with different context using %w and print whether errors.Is still finds io.EOF, then print the full message.',
solution=r'''package main

import (
    "errors"
    "fmt"
    "io"
)

func main() {
    err := fmt.Errorf("read header: %w", io.EOF)
    err = fmt.Errorf("open archive: %w", err)
    fmt.Println(errors.Is(err, io.EOF))
    fmt.Println(err)
}
''',
solutionStdout='true\nopen archive: read header: EOF\n',
question='What is the difference between wrapping with %w and formatting with %v?',
correct='%w keeps the original error inspectable through Is/As; %v keeps only its text',
wrong=['They are identical; %w is just a newer spelling', '%v wraps and %w discards the original'],
reasoning='%w records the operand as the wrapped error returned by Unwrap. %v formats it into a string, so callers can no longer match it.',
sourceURL='https://go.dev/blog/go1.13-errors',
additionalReadings=[dict(title='errors.AsType (Go 1.26)', url='https://pkg.go.dev/errors#AsType', section='AsType')]),

dict(key='sentinel-typed-errors', stage=STAGE, title='Designing errors: sentinels, types and opaque errors',
body=[
'A sentinel error is a package-level variable, such as var ErrNotFound = errors.New("not found"). Callers test it with errors.Is. Sentinels are part of your API: once exported, callers depend on them.',
'An error type carries structured data: type ValidationError struct{ Field string }. Callers extract it with errors.As or errors.AsType. Give error types pointer receivers consistently so a single dynamic type is matched.',
'An error type can customise matching by implementing Is(target error) bool or As(target any) bool, for example to say that every ValidationError counts as ErrInvalid. Expose as little as callers need; opaque errors that are only printed are the easiest to evolve.',
],
code=r'''package main

import (
    "errors"
    "fmt"
)

var ErrInvalid = errors.New("invalid input")

type FieldError struct {
    Field string
}

func (e *FieldError) Error() string        { return "invalid field " + e.Field }
func (e *FieldError) Is(target error) bool { return target == ErrInvalid }

func validate(name string) error {
    if name == "" {
        return fmt.Errorf("validate user: %w", &FieldError{Field: "name"})
    }
    return nil
}

func main() {
    err := validate("")
    fmt.Println(err)
    fmt.Println(errors.Is(err, ErrInvalid))
    if fe, ok := errors.AsType[*FieldError](err); ok {
        fmt.Println("field:", fe.Field)
    }
}
''',
expectedStdout='validate user: invalid field name\ntrue\nfield: name\n',
challenge='Define var ErrNotFound and func find(id int) error that returns ErrNotFound wrapped as "user 7: not found" for id 7 and nil otherwise; print errors.Is(find(7), ErrNotFound) and find(1).',
solution=r'''package main

import (
    "errors"
    "fmt"
)

var ErrNotFound = errors.New("not found")

func find(id int) error {
    if id == 7 {
        return fmt.Errorf("user %d: %w", id, ErrNotFound)
    }
    return nil
}

func main() {
    fmt.Println(errors.Is(find(7), ErrNotFound))
    fmt.Println(find(1))
}
''',
solutionStdout='true\n<nil>\n',
question='When should an error be a struct type rather than a sentinel?',
correct='When callers need structured details such as the failing field',
wrong=['Always; sentinels are deprecated', 'Only when the error is never wrapped'],
reasoning='Sentinels answer "which error?". Types answer "what are the details?" and are matched with errors.As or AsType.',
sourceURL='https://pkg.go.dev/errors'),

dict(key='errors-join', stage=STAGE, title='Combining errors with errors.Join and multiple %w',
body=[
'errors.Join(errs...) returns one error that wraps several. Its message puts each on its own line, and errors.Is and errors.As search all of them. nil inputs are skipped, and Join of only nils returns nil.',
'fmt.Errorf can also wrap more than one error with several %w verbs. Such errors implement Unwrap() []error rather than Unwrap() error, so errors.Unwrap returns nil for them; use Is and As instead.',
'Join suits validation that reports every problem, and cleanup where both the operation and Close failed: err = errors.Join(err, f.Close()).',
],
code=r'''package main

import (
    "errors"
    "fmt"
)

var (
    ErrName  = errors.New("name required")
    ErrEmail = errors.New("email required")
)

func validate(name, email string) error {
    var errs []error
    if name == "" {
        errs = append(errs, ErrName)
    }
    if email == "" {
        errs = append(errs, ErrEmail)
    }
    return errors.Join(errs...)
}

func main() {
    err := validate("", "")
    fmt.Println(err)
    fmt.Println(errors.Is(err, ErrEmail), validate("a", "b") == nil)
}
''',
expectedStdout='name required\nemail required\ntrue true\n',
challenge='Combine two errors with a single fmt.Errorf using two %w verbs and print whether errors.Is finds each of them.',
solution=r'''package main

import (
    "errors"
    "fmt"
)

func main() {
    a, b := errors.New("disk full"), errors.New("network down")
    err := fmt.Errorf("sync failed: %w; %w", a, b)
    fmt.Println(errors.Is(err, a), errors.Is(err, b))
}
''',
solutionStdout='true true\n',
question='What does errors.Join(nil, nil) return?',
correct='nil',
wrong=['An empty non-nil error', 'It panics on nil inputs'],
reasoning='Join discards nil errors and returns nil if none remain, so it is safe to accumulate optional failures.',
sourceURL='https://pkg.go.dev/errors#Join'),

dict(key='panic-recover', stage=STAGE, title='panic, recover and when not to use them',
body=[
'panic stops normal execution of the current goroutine and starts running its deferred calls. If nothing recovers, the program prints the panic value and a stack trace and exits with status 2. Run-time errors such as an out-of-range index or a nil map write are panics.',
'recover() inside a deferred function stops the panic and returns its value; anywhere else it returns nil. A recover only catches panics in its own goroutine. Use it at boundaries, such as a server that converts a handler panic into a 500 response, and convert the panic to an error.',
'Use panic for programmer errors and impossible states, not for expected failures like a missing file. Since Go 1.21, panic(nil) becomes a *runtime.PanicNilError, so recover() == nil reliably means "no panic".',
],
code=r'''package main

import (
    "errors"
    "fmt"
)

func safeIndex(xs []int, i int) (v int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered: %v", r)
        }
    }()
    return xs[i], nil
}

func main() {
    fmt.Println(safeIndex([]int{1, 2}, 1))
    _, err := safeIndex([]int{1, 2}, 5)
    fmt.Println(err)
    fmt.Println(errors.Unwrap(err) == nil)
}
''',
expectedStdout='2 <nil>\nrecovered: runtime error: index out of range [5] with length 2\ntrue\n',
challenge='Write func mustPositive(n int) int that panics with "negative" for n < 0, and func try(n int) (result string) that recovers and returns "caught: negative"; print try(-1) and try(3).',
solution=r'''package main

import "fmt"

func mustPositive(n int) int {
    if n < 0 {
        panic("negative")
    }
    return n
}

func try(n int) (result string) {
    defer func() {
        if r := recover(); r != nil {
            result = fmt.Sprint("caught: ", r)
        }
    }()
    return fmt.Sprint(mustPositive(n))
}

func main() {
    fmt.Println(try(-1))
    fmt.Println(try(3))
}
''',
solutionStdout='caught: negative\n3\n',
question='Why could the deferred function change err in safeIndex?',
correct='err is a named result, and deferred functions run before the caller receives the results',
wrong=['recover returns the error to the caller automatically', 'Panics always return the zero value with an error'],
reasoning='Deferred closures can assign to named results after a panic or return. That is how recovery is converted into an ordinary error.',
sourceURL='https://go.dev/blog/defer-panic-and-recover',
additionalReadings=[dict(title='Handling panics', url=SPEC+'#Handling_panics', section='recover')]),

dict(key='defer-cleanup-errors', stage=STAGE, title='Cleanup errors, defer ordering and Close',
body=[
'Close on a file being written can fail: data may be flushed only when it is closed. defer f.Close() discards that error. For writers, capture it with a named result: defer func() { err = errors.Join(err, f.Close()) }().',
'Deferred calls run in reverse order, so acquiring A then B and deferring both releases B before A. A deferred method value such as defer w.Flush() evaluates the receiver w immediately.',
'Readers can usually ignore Close errors, but writers, network transactions and database commits should not. os.CreateTemp, then write, sync, close and rename is the safe way to replace a file: a failure at any step leaves the old file in place.',
],
code=r'''package main

import (
    "errors"
    "fmt"
)

type resource struct{ name string }

func (r *resource) Close() error {
    fmt.Println("close", r.name)
    if r.name == "b" {
        return errors.New("close b failed")
    }
    return nil
}

func work() (err error) {
    a := &resource{"a"}
    defer func() { err = errors.Join(err, a.Close()) }()
    b := &resource{"b"}
    defer func() { err = errors.Join(err, b.Close()) }()
    fmt.Println("working")
    return nil
}

func main() {
    fmt.Println("result:", work())
}
''',
expectedStdout='working\nclose b\nclose a\nresult: close b failed\n',
challenge='Write a value to a temporary file with os.CreateTemp, return any Close error with errors.Join, read it back, remove the file and print the contents.',
solution=r'''package main

import (
    "errors"
    "fmt"
    "os"
)

func write(text string) (path string, err error) {
    f, err := os.CreateTemp("", "lesson-*.txt")
    if err != nil {
        return "", err
    }
    defer func() { err = errors.Join(err, f.Close()) }()
    _, err = f.WriteString(text)
    return f.Name(), err
}

func main() {
    path, err := write("saved")
    if err != nil {
        fmt.Println(err)
        return
    }
    defer os.Remove(path)
    data, err := os.ReadFile(path)
    fmt.Println(string(data), err)
}
''',
solutionStdout='saved <nil>\n',
question='Why can defer f.Close() be wrong for a file you are writing?',
correct='It discards the Close error, which may report data that failed to flush',
wrong=['Close cannot be deferred for writable files', 'Deferred Close runs before the writes finish'],
reasoning='Write errors can surface at Close. Capture the error into a named result so the caller learns the write failed.',
sourceURL='https://pkg.go.dev/os#File.Close'),
]

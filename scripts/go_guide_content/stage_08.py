STAGE = '08 · Testing'
TESTING = 'https://pkg.go.dev/testing'


def f(path, content):
    return dict(path=path, content=content)


def gomod(name):
    return f('go.mod', f'module example.com/{name}\n\ngo 1.27\n')


LESSONS = [
dict(key='table-tests', stage=STAGE, title='go test and table-driven tests',
body=[
'Tests live in files ending _test.go next to the code. A test is func TestXxx(t *testing.T). t.Errorf records a failure and continues; t.Fatalf records it and stops this test. go test ./... builds and runs every package\'s tests; -run takes a regular expression to select tests and -v prints each one.',
'A table-driven test lists cases as a slice of structs and loops over them. Adding a case is one line, and failure messages print the input, the result and the expectation: Reverse(%q) = %q, want %q.',
'Tests in package x see its unexported names. Tests in package x_test (an external test package in the same directory) see only the exported API, which checks it the way callers will use it. Both kinds can live side by side.',
'This project starts with a byte-based Reverse that breaks multi-byte characters. One check adds a failing case on purpose to show what a failure looks like; the answer fixes the function.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('text'),
f('text.go', r'''// Package text holds small string helpers.
package text

// Reverse returns s with its bytes in reverse order.
func Reverse(s string) string {
    b := []byte(s)
    for i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {
        b[i], b[j] = b[j], b[i]
    }
    return string(b)
}
'''),
f('text_test.go', r'''package text

import "testing"

func TestReverse(t *testing.T) {
    cases := []struct {
        in, want string
    }{
        {"", ""},
        {"a", "a"},
        {"gopher", "rehpog"},
    }
    for _, c := range cases {
        if got := Reverse(c.in); got != c.want {
            t.Errorf("Reverse(%q) = %q, want %q", c.in, got, c.want)
        }
    }
}
'''),
],
projectSolutionFiles=[f('text.go', r'''// Package text holds small string helpers.
package text

// Reverse returns s with its runes in reverse order.
func Reverse(s string) string {
    r := []rune(s)
    for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    return string(r)
}
''')],
projectInstructions='Go 1.27, standard library only. Create the files, then run:\ngo test -v ./...\nAll three cases pass. Now add the case {"héllo", "olléh"}: it fails because Reverse swaps bytes.\nPractice: fix Reverse so the new case passes. Replace text.go with the worked answer.',
projectChecks=[
dict(name='table passes', args=['test', '-v', './...'], outputContains=['--- PASS: TestReverse', 'ok']),
dict(name='multi-byte case fails on byte reversal', args=['test', './...'], exit=1,
     mutations=[dict(path='text_test.go', find='{"gopher", "rehpog"},', replace='{"gopher", "rehpog"},\n\t\t{"héllo", "olléh"},')],
     outputContains=['Reverse("héllo") =', 'want "olléh"', 'FAIL']),
dict(name='answer reverses runes', args=['test', './...'], useSolution=True,
     mutations=[dict(path='text_test.go', find='{"gopher", "rehpog"},', replace='{"gopher", "rehpog"},\n\t\t{"héllo", "olléh"},')], outputContains=['ok']),
],
challenge='Add the test case {"héllo", "olléh"}, watch it fail, then fix Reverse so the whole table passes.',
question='What is the difference between t.Errorf and t.Fatalf?',
correct='Errorf marks the test failed and continues; Fatalf marks it failed and stops the test',
wrong=['Errorf only logs; Fatalf fails the test', 'Fatalf stops every remaining test in the package'],
reasoning='Fatalf calls FailNow, which ends the current test function via runtime.Goexit. Other tests still run.',
sourceURL='https://go.dev/doc/tutorial/add-a-test',
additionalReadings=[dict(title='Go wiki: table-driven tests', url='https://go.dev/wiki/TableDrivenTests', section='Table-driven tests')]),

dict(key='subtests-helpers', stage=STAGE, title='Subtests, helpers, cleanup, temp dirs and parallel tests',
body=[
't.Run(name, func(t *testing.T)) runs a named subtest. Each table case becomes its own entry, can be selected with -run TestParse/empty, and a Fatal in one case does not stop the others.',
't.Helper() marks a function as a test helper, so failure locations point at the caller rather than the helper. t.Cleanup registers teardown that runs after the test and its subtests, in last-in, first-out order. t.TempDir returns a directory removed automatically, and t.Context returns a context cancelled just before cleanup runs (Go 1.24).',
't.Parallel() lets a test run alongside other parallel tests. Since Go 1.22 each loop iteration has its own variable, so parallel subtests in a loop no longer need the old tc := tc copy. t.Setenv and t.Chdir change process-wide state and therefore cannot be combined with Parallel.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('store'),
f('store.go', r'''// Package store saves small notes to files.
package store

import (
    "os"
    "path/filepath"
)

// Save writes text to name inside dir.
func Save(dir, name, text string) error {
    return os.WriteFile(filepath.Join(dir, name), []byte(text), 0o600)
}

// Load reads name from dir.
func Load(dir, name string) (string, error) {
    b, err := os.ReadFile(filepath.Join(dir, name))
    return string(b), err
}
'''),
f('store_test.go', r'''package store

import "testing"

func roundTrip(t *testing.T, dir, name, text string) string {
    t.Helper()
    if err := Save(dir, name, text); err != nil {
        t.Fatalf("Save: %v", err)
    }
    got, err := Load(dir, name)
    if err != nil {
        t.Fatalf("Load: %v", err)
    }
    return got
}

func TestRoundTrip(t *testing.T) {
    dir := t.TempDir()
    t.Cleanup(func() { t.Log("cleanup ran") })
    for _, text := range []string{"", "hello", "multi\nline"} {
        t.Run(text, func(t *testing.T) {
            t.Parallel()
            name := "note" + string(rune('a'+len(text))) + ".txt"
            if got := roundTrip(t, dir, name, text); got != text {
                t.Errorf("got %q, want %q", got, text)
            }
        })
    }
}
'''),
],
projectSolutionFiles=[f('store_test.go', r'''package store

import (
    "errors"
    "io/fs"
    "testing"
)

func roundTrip(t *testing.T, dir, name, text string) string {
    t.Helper()
    if err := Save(dir, name, text); err != nil {
        t.Fatalf("Save: %v", err)
    }
    got, err := Load(dir, name)
    if err != nil {
        t.Fatalf("Load: %v", err)
    }
    return got
}

func TestRoundTrip(t *testing.T) {
    dir := t.TempDir()
    t.Cleanup(func() { t.Log("cleanup ran") })
    for _, text := range []string{"", "hello", "multi\nline"} {
        t.Run(text, func(t *testing.T) {
            t.Parallel()
            name := "note" + string(rune('a'+len(text))) + ".txt"
            if got := roundTrip(t, dir, name, text); got != text {
                t.Errorf("got %q, want %q", got, text)
            }
        })
    }
}

func TestLoadMissing(t *testing.T) {
    _, err := Load(t.TempDir(), "absent.txt")
    if !errors.Is(err, fs.ErrNotExist) {
        t.Fatalf("Load error = %v, want fs.ErrNotExist", err)
    }
}
''')],
projectInstructions='Go 1.27, standard library only. Run:\ngo test -v ./...\nYou should see three parallel subtests and the cleanup log.\nPractice: add TestLoadMissing checking that loading an absent file reports fs.ErrNotExist via errors.Is. Replace store_test.go with the worked answer.',
projectChecks=[
dict(name='subtests and cleanup', args=['test', '-v', './...'], outputContains=['--- PASS: TestRoundTrip/hello', 'cleanup ran', 'ok']),
dict(name='select one subtest', args=['test', '-v', '-run', 'TestRoundTrip/hello', './...'], outputContains=['TestRoundTrip/hello'],
     ),
dict(name='answer missing-file test', args=['test', '-v', '-run', 'TestLoadMissing', './...'], useSolution=True, outputContains=['--- PASS: TestLoadMissing']),
],
challenge='Add TestLoadMissing asserting that Load on an absent file returns an error matching fs.ErrNotExist.',
question='What does t.Helper() change?',
correct='Failures inside the helper are reported at the caller\'s line',
wrong=['The helper runs in its own goroutine', 'Failures in the helper are ignored'],
reasoning='Helper removes the function from the reported call site, so the message points to the test that called it.',
sourceURL=TESTING+'#hdr-Subtests_and_Sub_benchmarks',
additionalReadings=[dict(title='Using subtests and sub-benchmarks', url='https://go.dev/blog/subtests', section='Subtests')]),

dict(key='benchmarks-bloop', stage=STAGE, title='Benchmarks with b.Loop and allocation reports',
body=[
'A benchmark is func BenchmarkXxx(b *testing.B). Since Go 1.24, write the measured code inside for b.Loop() { ... }. Loop resets the timer the first time it is called, stops it at the end, and keeps the loop body\'s results alive so the compiler cannot optimise the work away.',
'Run benchmarks with go test -run=^$ -bench=. so ordinary tests are skipped. -benchmem or b.ReportAllocs adds bytes and allocations per operation, often the most useful number. -count=10 repeats runs so a tool such as benchstat can compare before and after.',
'Benchmarks measure one machine at one moment. Compare variants on the same machine, look at allocations as well as time, and treat small differences as noise unless benchstat shows them as significant.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('join'),
f('join.go', r'''// Package join compares string-building strategies.
package join

// Plus joins words with repeated string concatenation.
func Plus(words []string) string {
    s := ""
    for i, w := range words {
        if i > 0 {
            s += ","
        }
        s += w
    }
    return s
}
'''),
f('join_test.go', r'''package join

import "testing"

var words = []string{"go", "rust", "ocaml", "lean", "python", "c++"}

func TestPlus(t *testing.T) {
    if got := Plus(words); got != "go,rust,ocaml,lean,python,c++" {
        t.Fatal(got)
    }
}

func BenchmarkPlus(b *testing.B) {
    b.ReportAllocs()
    for b.Loop() {
        Plus(words)
    }
}
'''),
],
projectSolutionFiles=[
f('join.go', r'''// Package join compares string-building strategies.
package join

import "strings"

// Plus joins words with repeated string concatenation.
func Plus(words []string) string {
    s := ""
    for i, w := range words {
        if i > 0 {
            s += ","
        }
        s += w
    }
    return s
}

// Builder joins words with one pre-sized strings.Builder.
func Builder(words []string) string {
    n := max(len(words)-1, 0)
    for _, w := range words {
        n += len(w)
    }
    var sb strings.Builder
    sb.Grow(n)
    for i, w := range words {
        if i > 0 {
            sb.WriteByte(',')
        }
        sb.WriteString(w)
    }
    return sb.String()
}
'''),
f('join_test.go', r'''package join

import "testing"

var words = []string{"go", "rust", "ocaml", "lean", "python", "c++"}

func TestJoin(t *testing.T) {
    for name, fn := range map[string]func([]string) string{"Plus": Plus, "Builder": Builder} {
        if got := fn(words); got != "go,rust,ocaml,lean,python,c++" {
            t.Errorf("%s = %q", name, got)
        }
    }
}

func TestBuilderAllocatesOnce(t *testing.T) {
    if n := testing.AllocsPerRun(100, func() { Builder(words) }); n != 1 {
        t.Fatalf("Builder allocations = %v, want 1", n)
    }
}

func BenchmarkPlus(b *testing.B) {
    b.ReportAllocs()
    for b.Loop() {
        Plus(words)
    }
}

func BenchmarkBuilder(b *testing.B) {
    b.ReportAllocs()
    for b.Loop() {
        Builder(words)
    }
}
'''),
],
projectInstructions='Go 1.24+ (checked with 1.27). Run:\ngo test ./...\ngo test -run=^$ -bench=. -benchtime=200x ./...\nThe benchmark output reports ns/op, B/op and allocs/op.\nPractice: add a Builder version that pre-sizes a strings.Builder, a test proving it allocates exactly once (testing.AllocsPerRun), and a benchmark for it. Replace both files with the worked answer.',
projectChecks=[
dict(name='tests pass', args=['test', './...'], outputContains=['ok']),
dict(name='benchmark runs with b.Loop', args=['test', '-run=^$', '-bench=.', '-benchtime=200x', './...'], outputContains=['BenchmarkPlus', 'allocs/op']),
dict(name='answer allocates once', args=['test', '-v', './...'], useSolution=True, outputContains=['--- PASS: TestBuilderAllocatesOnce']),
dict(name='answer benchmarks both', args=['test', '-run=^$', '-bench=.', '-benchtime=200x', './...'], useSolution=True, outputContains=['BenchmarkPlus', 'BenchmarkBuilder', '1 allocs/op']),
],
challenge='Add Builder, which pre-sizes a strings.Builder, plus a test that it allocates exactly once and a benchmark comparing it with Plus.',
question='What does for b.Loop() do that the older for range b.N did not?',
correct='It times only the loop and keeps the body\'s results alive against dead-code elimination',
wrong=['It runs the benchmark in parallel automatically', 'It fixes the iteration count at one million'],
reasoning='Loop resets and stops the timer itself and prevents the compiler from discarding results computed in the body, two classic benchmark mistakes.',
sourceURL='https://pkg.go.dev/testing#B.Loop',
additionalReadings=[dict(title='Go 1.24 release notes: testing.B.Loop', url='https://go.dev/doc/go1.24#testing', section='B.Loop')]),

dict(key='fuzzing', stage=STAGE, title='Native fuzzing with seed corpora',
body=[
'A fuzz test is func FuzzXxx(f *testing.F). f.Add supplies seed inputs; f.Fuzz(func(t *testing.T, in string) { ... }) is the target. Plain go test runs only the seeds, so fuzz tests also act as regression tests.',
'go test -fuzz=FuzzXxx generates new inputs, guided by coverage, until it finds a failure or -fuzztime ends. A failing input is written to testdata/fuzz/FuzzXxx/ and replayed by every later go test run, so commit those files.',
'Fuzz targets should check properties rather than exact outputs: reversing twice gives the input back, the output is valid UTF-8, parsing what you formatted round-trips. Inputs that are invalid by design should be skipped with t.Skip or rejected with an error, not crash.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('text'),
f('reverse.go', r'''// Package text holds small string helpers.
package text

import (
    "errors"
    "unicode/utf8"
)

// Reverse reverses the runes of s. It rejects invalid UTF-8.
func Reverse(s string) (string, error) {
    if !utf8.ValidString(s) {
        return s, errors.New("input is not valid UTF-8")
    }
    r := []rune(s)
    for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    return string(r), nil
}
'''),
f('reverse_test.go', r'''package text

import (
    "testing"
    "unicode/utf8"
)

func FuzzReverse(f *testing.F) {
    for _, seed := range []string{"", "gopher", "héllo", "\xff"} {
        f.Add(seed)
    }
    f.Fuzz(func(t *testing.T, in string) {
        once, err := Reverse(in)
        if err != nil {
            return
        }
        twice, err := Reverse(once)
        if err != nil {
            t.Fatalf("second Reverse failed: %v", err)
        }
        if twice != in {
            t.Errorf("double reverse %q -> %q", in, twice)
        }
        if !utf8.ValidString(once) {
            t.Errorf("Reverse(%q) produced invalid UTF-8 %q", in, once)
        }
    })
}
'''),
],
projectSolutionFiles=[f('reverse_test.go', r'''package text

import (
    "testing"
    "unicode/utf8"
)

func FuzzReverse(f *testing.F) {
    for _, seed := range []string{"", "gopher", "héllo", "\xff"} {
        f.Add(seed)
    }
    f.Fuzz(func(t *testing.T, in string) {
        once, err := Reverse(in)
        if err != nil {
            if utf8.ValidString(in) {
                t.Fatalf("Reverse rejected valid input %q", in)
            }
            return
        }
        twice, err := Reverse(once)
        if err != nil {
            t.Fatalf("second Reverse failed: %v", err)
        }
        if twice != in {
            t.Errorf("double reverse %q -> %q", in, twice)
        }
        if utf8.RuneCountInString(once) != utf8.RuneCountInString(in) {
            t.Errorf("rune count changed for %q", in)
        }
    })
}
''')],
projectInstructions='Go 1.27, standard library only. Run the seed corpus, then a short fuzzing session:\ngo test ./...\ngo test -run=^$ -fuzz=FuzzReverse -fuzztime=3000x ./...\nThe third check removes the UTF-8 guard: the seed "\\xff" then fails, because []rune replaces invalid bytes with U+FFFD and reversing twice no longer returns the input.\nPractice: strengthen the target so that rejecting valid input is a failure and rune counts are preserved. Replace reverse_test.go with the worked answer.',
projectChecks=[
dict(name='seed corpus passes', args=['test', './...'], outputContains=['ok']),
dict(name='bounded fuzzing session', args=['test', '-run=^$', '-fuzz=FuzzReverse', '-fuzztime=3000x', './...'], timeout=240, outputContains=['ok']),
dict(name='removing the guard fails on the invalid seed', args=['test', './...'], exit=1,
     mutations=[dict(path='reverse.go', find='if !utf8.ValidString(s) {', replace='if false && !utf8.ValidString(s) {')], outputContains=['FuzzReverse', 'FAIL']),
dict(name='answer stronger properties', args=['test', '-v', './...'], useSolution=True, outputContains=['--- PASS: FuzzReverse']),
],
challenge='Strengthen the fuzz target so that Reverse rejecting valid UTF-8 is a failure and the rune count is preserved.',
question='What does plain go test do with a fuzz test?',
correct='Runs it on the seed corpus and saved failing inputs only',
wrong=['Fuzzes for a default of ten seconds', 'Skips it unless -fuzz is given'],
reasoning='Fuzzing proper needs -fuzz. Without it, seeds and testdata/fuzz entries run as ordinary regression cases.',
sourceURL='https://go.dev/doc/security/fuzz/',
additionalReadings=[dict(title='Tutorial: getting started with fuzzing', url='https://go.dev/doc/tutorial/fuzz', section='Fuzzing tutorial')]),

dict(key='examples-tests', stage=STAGE, title='Testable examples as documentation',
body=[
'func ExampleXxx() in a _test.go file is documentation that go test runs. If it ends with an // Output: comment, its standard output must match exactly; // Unordered output: compares lines as a set. An example with no output comment is compiled but not run.',
'The name links the example to the API: Example for the package, ExampleReverse for a function, ExampleBuffer_Len for a method, with an optional _suffix for variants. pkg.go.dev and go doc show them next to the documentation, and Go 1.27\'s go doc -ex can run them.',
'Examples are best for typical use; edge cases still belong in table tests. Keep them short and deterministic, without map iteration order or timing in the output.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('slug'),
f('slug.go', r'''// Package slug turns titles into URL path segments.
package slug

import (
    "strings"
    "unicode"
)

// Make lower-cases title and joins its letter-and-digit words with hyphens.
func Make(title string) string {
    words := strings.FieldsFunc(strings.ToLower(title), func(r rune) bool {
        return !unicode.IsLetter(r) && !unicode.IsDigit(r)
    })
    return strings.Join(words, "-")
}
'''),
f('example_test.go', r'''package slug_test

import (
    "fmt"

    "example.com/slug"
)

func ExampleMake() {
    fmt.Println(slug.Make("Hello, Go 1.27!"))
    // Output: hello-go-1-27
}
'''),
],
projectSolutionFiles=[f('example_test.go', r'''package slug_test

import (
    "fmt"

    "example.com/slug"
)

func ExampleMake() {
    fmt.Println(slug.Make("Hello, Go 1.27!"))
    // Output: hello-go-1-27
}

func ExampleMake_unicode() {
    fmt.Println(slug.Make("Ça va? Très bien"))
    fmt.Println(slug.Make("  --  "))
    // Output:
    // ça-va-très-bien
    //
}
''')],
projectInstructions='Go 1.27. Run:\ngo test -v ./...\nExampleMake runs and its output is compared. A second check breaks the expected output to show the mismatch report.\nPractice: add ExampleMake_unicode covering accented letters and an input with no words. Replace example_test.go with the worked answer.',
projectChecks=[
dict(name='example output verified', args=['test', '-v', './...'], outputContains=['--- PASS: ExampleMake']),
dict(name='wrong output fails', args=['test', './...'], exit=1,
     mutations=[dict(path='example_test.go', find='// Output: hello-go-1-27', replace='// Output: hello-go-127')], outputContains=['got:', 'hello-go-1-27', 'want:']),
dict(name='answer unicode example', args=['test', '-v', './...'], useSolution=True, outputContains=['--- PASS: ExampleMake_unicode']),
],
challenge='Add ExampleMake_unicode showing that "Ça va? Très bien" becomes "ça-va-très-bien" and that "  --  " becomes an empty string.',
question='When does go test run an Example function?',
correct='When it has an // Output: or // Unordered output: comment',
wrong=['Always, even without an output comment', 'Only with the -examples flag'],
reasoning='Without an output comment there is nothing to compare, so the example is compiled to keep it correct but not executed.',
sourceURL='https://go.dev/blog/examples',
additionalReadings=[dict(title='testing: Examples', url=TESTING+'#hdr-Examples', section='Examples')]),

dict(key='coverage', stage=STAGE, title='Coverage profiles and what they do not prove',
body=[
'go test -cover reports the percentage of statements executed by the tests. -coverprofile=c.out writes per-block data, go tool cover -func=c.out lists coverage by function and go tool cover -html=c.out shows uncovered lines in a browser. -covermode=atomic is needed for accurate counts with concurrent tests.',
'Since Go 1.20, go build -cover produces an instrumented binary that writes coverage data to GOCOVERDIR, so integration tests that run the real program can contribute coverage too.',
'Coverage shows what was executed, not what was checked. A test that calls every function without asserting anything reaches 100%. Use coverage to find untested branches, especially error paths, then write tests that check the behaviour there.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('grade'),
f('grade.go', r'''// Package grade converts scores to letters.
package grade

import "errors"

// ErrRange reports a score outside 0..100.
var ErrRange = errors.New("score out of range")

// Letter returns the letter grade for score.
func Letter(score int) (string, error) {
    if score < 0 || score > 100 {
        return "", ErrRange
    }
    if score >= 90 {
        return "A", nil
    }
    return "B", nil
}
'''),
f('grade_test.go', r'''package grade

import "testing"

func TestLetter(t *testing.T) {
    if got, _ := Letter(95); got != "A" {
        t.Fatalf("Letter(95) = %q", got)
    }
}
'''),
],
projectSolutionFiles=[f('grade_test.go', r'''package grade

import (
    "errors"
    "testing"
)

func TestLetter(t *testing.T) {
    cases := []struct {
        score int
        want  string
        err   error
    }{
        {95, "A", nil},
        {90, "A", nil},
        {89, "B", nil},
        {-1, "", ErrRange},
        {101, "", ErrRange},
    }
    for _, c := range cases {
        got, err := Letter(c.score)
        if got != c.want || !errors.Is(err, c.err) {
            t.Errorf("Letter(%d) = %q, %v; want %q, %v", c.score, got, err, c.want, c.err)
        }
    }
}
''')],
projectInstructions='Go 1.27. Run:\ngo test -cover ./...\nThe single test covers only part of Letter.\nPractice: turn it into a table that checks both boundaries, both grades and both out-of-range sides, reaching 100% statement coverage. Replace grade_test.go with the worked answer.',
projectChecks=[
dict(name='partial coverage', args=['test', '-cover', './...'], outputContains=['coverage: 60.0% of statements']),
dict(name='answer full coverage', args=['test', '-cover', './...'], useSolution=True, outputContains=['coverage: 100.0% of statements']),
],
challenge='Rewrite the test as a table that checks 95, 90, 89, -1 and 101, including the ErrRange errors, so coverage reaches 100%.',
question='What does 100% statement coverage prove?',
correct='Only that every statement ran during the tests',
wrong=['That the code has no bugs', 'That every branch outcome was asserted'],
reasoning='Coverage measures execution. Correctness needs assertions on results, which coverage tools cannot see.',
sourceURL='https://go.dev/blog/cover',
additionalReadings=[dict(title='Coverage for integration tests', url='https://go.dev/doc/build-cover', section='go build -cover')]),

dict(key='httptest', stage=STAGE, title='Testing HTTP handlers with httptest and NewTestServer',
body=[
'httptest.NewRecorder gives an http.ResponseWriter that records status, headers and body; pass it with a request from httptest.NewRequest straight to a handler. This tests the handler alone without any network, and runs fast.',
'To test a client and server together, start a server. Go 1.27 adds httptest.NewTestServer(t, handler): it serves over an in-memory network by default and closes itself when the test ends. Use srv.Client() for requests so they reach that network. httptest.NewServer still starts a real loopback listener when you need one.',
'Check status codes, content types and bodies. Close response bodies; since Go 1.27 the HTTP/1 client also drains a closed body automatically so the connection can be reused.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('hello'),
f('hello.go', r'''// Package hello serves greetings.
package hello

import (
    "fmt"
    "net/http"
)

// Handler greets the name query parameter.
func Handler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    w.Header().Set("Content-Type", "text/plain; charset=utf-8")
    fmt.Fprintf(w, "hello, %s", name)
}
'''),
f('hello_test.go', r'''package hello

import (
    "io"
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestHandlerDirect(t *testing.T) {
    rec := httptest.NewRecorder()
    Handler(rec, httptest.NewRequest("GET", "/?name=go", nil))
    if rec.Code != http.StatusOK || rec.Body.String() != "hello, go" {
        t.Fatalf("got %d %q", rec.Code, rec.Body.String())
    }
}

func TestHandlerOverTestServer(t *testing.T) {
    srv := httptest.NewTestServer(t, http.HandlerFunc(Handler))
    resp, err := srv.Client().Get(srv.URL + "/?name=gopher")
    if err != nil {
        t.Fatal(err)
    }
    defer resp.Body.Close()
    body, err := io.ReadAll(resp.Body)
    if err != nil {
        t.Fatal(err)
    }
    if string(body) != "hello, gopher" {
        t.Fatalf("body %q", body)
    }
}
'''),
],
projectSolutionFiles=[
f('hello.go', r'''// Package hello serves greetings.
package hello

import (
    "fmt"
    "net/http"
)

// Handler greets the name query parameter.
func Handler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    if name == "" {
        http.Error(w, "missing name", http.StatusBadRequest)
        return
    }
    w.Header().Set("Content-Type", "text/plain; charset=utf-8")
    fmt.Fprintf(w, "hello, %s", name)
}
'''),
f('missing_test.go', r'''package hello

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestMissingName(t *testing.T) {
    rec := httptest.NewRecorder()
    Handler(rec, httptest.NewRequest("GET", "/", nil))
    if rec.Code != http.StatusBadRequest {
        t.Fatalf("status %d, want 400", rec.Code)
    }
}
'''),
],
projectInstructions='Go 1.27 (NewTestServer is new in 1.27). Run:\ngo test -v ./...\nOne test calls the handler directly; the other goes through an in-memory test server.\nPractice: return 400 Bad Request when name is missing, and add missing_test.go. Replace hello.go and add the new test from the worked answer.',
projectChecks=[
dict(name='direct and server tests', args=['test', '-v', './...'], outputContains=['--- PASS: TestHandlerDirect', '--- PASS: TestHandlerOverTestServer']),
dict(name='answer rejects missing name', args=['test', '-v', './...'], useSolution=True, outputContains=['--- PASS: TestMissingName', '--- PASS: TestHandlerOverTestServer']),
],
challenge='Make Handler return 400 Bad Request when the name parameter is missing, and add a test for it.',
question='What does httptest.NewTestServer (Go 1.27) use by default?',
correct='An in-memory network, with the server closed automatically when the test ends',
wrong=['A real TCP listener on a random port that you must close', 'No network: it calls the handler directly like NewRecorder'],
reasoning='NewTestServer takes testing.TB, registers cleanup, and serves over an in-memory network; srv.Client() is configured to reach it.',
sourceURL='https://pkg.go.dev/net/http/httptest#NewTestServer',
additionalReadings=[dict(title='Go 1.27 release notes: httptest', url='https://go.dev/doc/go1.27#nethttphttptestpkgnethttphttptest', section='NewTestServer')]),

dict(key='synctest', stage=STAGE, title='Deterministic concurrent tests with testing/synctest',
body=[
'testing/synctest (stable since Go 1.25) runs a test function in an isolated bubble. Goroutines started inside belong to the bubble, and time inside it is fake: it starts at midnight UTC on 1 January 2000 and advances only when every goroutine in the bubble is durably blocked.',
'synctest.Wait blocks until every other goroutine in the bubble is durably blocked, which gives a precise point to check state without sleeping. Code that waits for a timeout of one hour therefore finishes instantly and deterministically.',
'Go 1.27 adds synctest.Sleep, which advances the fake clock and then waits for the bubble to settle. Durably blocked means blocked on something inside the bubble, such as a channel created there, a timer or a sync.WaitGroup; blocking on real I/O or an outside mutex is not durable.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('cache'),
f('cache.go', r'''// Package cache holds values that expire.
package cache

import (
    "sync"
    "time"
)

// Cache stores values for a fixed time to live.
type Cache struct {
    mu   sync.Mutex
    ttl  time.Duration
    data map[string]entry
}

type entry struct {
    value   string
    expires time.Time
}

// New returns an empty cache.
func New(ttl time.Duration) *Cache {
    return &Cache{ttl: ttl, data: map[string]entry{}}
}

// Set stores value under key.
func (c *Cache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = entry{value, time.Now().Add(c.ttl)}
}

// Get returns the value if it has not expired.
func (c *Cache) Get(key string) (string, bool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    e, ok := c.data[key]
    if !ok || !time.Now().Before(e.expires) {
        return "", false
    }
    return e.value, true
}
'''),
f('cache_test.go', r'''package cache

import (
    "testing"
    "testing/synctest"
    "time"
)

func TestExpiry(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        c := New(time.Hour)
        c.Set("k", "v")
        time.Sleep(59 * time.Minute)
        if _, ok := c.Get("k"); !ok {
            t.Fatal("expired too early")
        }
        time.Sleep(time.Minute)
        if _, ok := c.Get("k"); ok {
            t.Fatal("still present after an hour")
        }
    })
}
'''),
],
projectSolutionFiles=[f('janitor_test.go', r'''package cache

import (
    "testing"
    "testing/synctest"
    "time"
)

func TestBackgroundRefresh(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        c := New(time.Minute)
        done := make(chan struct{})
        go func() {
            defer close(done)
            for range 3 {
                c.Set("tick", time.Now().Format(time.TimeOnly))
                time.Sleep(30 * time.Second)
            }
        }()
        synctest.Sleep(65 * time.Second)
        if v, ok := c.Get("tick"); !ok || v != "00:01:00" {
            t.Fatalf("Get = %q, %v", v, ok)
        }
        <-done
    })
}
''')],
projectInstructions='Go 1.27 (synctest.Test from 1.25, synctest.Sleep from 1.27). Run:\ngo test -v ./...\nThe test "waits" a whole hour of fake time instantly.\nPractice: add a test where a background goroutine refreshes a value every 30 seconds; use synctest.Sleep to advance 65 seconds and check that the latest value was written at 00:01:00. Add janitor_test.go from the worked answer.',
projectChecks=[
dict(name='fake hour passes instantly', args=['test', '-v', '-race', './...'], outputContains=['--- PASS: TestExpiry'], timeout=240),
dict(name='off-by-one expiry is caught', args=['test', './...'], exit=1,
     mutations=[dict(path='cache.go', find='!time.Now().Before(e.expires)', replace='time.Now().After(e.expires)')], outputContains=['still present after an hour']),
dict(name='answer background goroutine', args=['test', '-v', '-race', './...'], useSolution=True, outputContains=['--- PASS: TestBackgroundRefresh'], timeout=240),
],
challenge='Add a synctest test in which a goroutine refreshes the cache every 30 seconds; advance 65 seconds with synctest.Sleep and check the stored time is 00:01:00.',
question='When does fake time advance inside a synctest bubble?',
correct='Only when every goroutine in the bubble is durably blocked',
wrong=['At real wall-clock speed', 'Each time the test calls t.Log'],
reasoning='The clock jumps to the next timer only when nothing in the bubble can make progress, which makes timing-dependent tests deterministic.',
sourceURL='https://pkg.go.dev/testing/synctest',
additionalReadings=[dict(title='Testing concurrent code with testing/synctest', url='https://go.dev/blog/synctest', section='synctest')]),
]

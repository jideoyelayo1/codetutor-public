STAGE = '18 · Tooling'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='vet-analyzers', stage=STAGE, title='go vet, analyzers and the stdversion check',
body=[
'go vet runs analyzers that find likely bugs in code that compiles: Printf format mismatches, copied locks, unreachable code, malformed struct tags, lost context cancel functions, self-assignment and more. go test runs a subset of them automatically before tests.',
'Go 1.27 adds stdversion to the vet checks run by go test: it reports standard-library symbols newer than the go version in force for a file, from the go.mod go line or a //go:build constraint. Using strings.CutLast in a module declaring go 1.22 is reported because older toolchains would fail to build it.',
'Additional analyzers come from golang.org/x/tools and tools such as staticcheck. go vet -vettool=prog runs a custom analysis binary; analyzers are written with the golang.org/x/tools/go/analysis framework.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/tool\n\ngo 1.22\n'),
f('path.go', r'''// Package tool splits paths.
package tool

import "strings"

// Dir returns everything before the last slash.
func Dir(p string) string {
    dir, _, _ := strings.CutLast(p, "/")
    return dir
}
'''),
f('path_test.go', r'''package tool

import "testing"

func TestDir(t *testing.T) {
    if got := Dir("a/b/c"); got != "a/b" {
        t.Fatal(got)
    }
}
'''),
],
projectSolutionFiles=[f('go.mod', 'module example.com/tool\n\ngo 1.27\n')],
projectVet=[],  # vet failing is the lesson; the checks assert it
projectInstructions='Checked with go1.27.2. The module declares go 1.22 but uses strings.CutLast, added in Go 1.27. Run:\ngo vet ./...\ngo test ./...\nBoth report that CutLast requires go1.27. A struct tag mistake is shown with a mutation in the second check.\nPractice: raise the go directive to 1.27 so the code and its declared version agree. Replace go.mod with the worked answer.',
projectChecks=[
dict(name='go vet reports a too-new symbol', args=['vet', './...'], exit=1, outputContains=['strings.CutLast requires go1.27 or later']),
dict(name='go test runs stdversion by default', args=['test', './...'], exit=1, outputContains=['strings.CutLast requires go1.27 or later']),
dict(name='go vet reports malformed struct tags', args=['vet', './...'], exit=1,
     mutations=[dict(path='path.go', find='import "strings"\n', replace='import "strings"\n\ntype T struct {\n\tName string `json:name`\n}\n')], outputContains=['not compatible with reflect.StructTag.Get']),
dict(name='answer declares go 1.27', args=['test', './...'], useSolution=True, outputContains=['ok']),
dict(name='answer passes go vet', args=['vet', './...'], useSolution=True),
],
challenge='Fix the mismatch between the declared language version and the API used, so go vet and go test pass.',
question='What does the stdversion analyzer report?',
correct='Standard-library symbols newer than the go version declared for the file',
wrong=['Packages with no recent commits', 'Use of deprecated syntax such as interface{}'],
reasoning='A go 1.22 module promises to build with Go 1.22, which lacks strings.CutLast. stdversion catches that broken promise early.',
sourceURL='https://pkg.go.dev/cmd/vet',
additionalReadings=[dict(title='Go 1.27 release notes: go test', url='https://go.dev/doc/go1.27#go-command', section='stdversion in go test')]),

dict(key='go-fix-modernizers', stage=STAGE, title='go fix and modernizers',
body=[
'Since Go 1.26 go fix runs modernizers: analyzers whose suggested fixes rewrite code to newer idioms. Examples include any (interface{} to any), rangeint (3-clause loops to range over int), minmax (if/else to min/max), newexpr (helper functions to new(expr)), errorsastype (errors.As to errors.AsType) and waitgroupgo (Add/Done to WaitGroup.Go, renamed in 1.27).',
'Go 1.27 adds atomictypes (sync/atomic functions to typed atomics), embedlit (shorter composite literals using promoted fields), slicesbackward and unsafefuncs. go fix -diff prints the patch without applying it and exits non-zero when there is something to change, which suits CI.',
'Each fix respects the go version declared for the file, so it never introduces a feature the module cannot use. //go:fix inline directives let library authors mark functions whose calls go fix should inline, which helps migrate users off deprecated APIs.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/legacy\n\ngo 1.27\n'),
f('legacy.go', r'''// Package legacy is written in pre-generics style.
package legacy

import "sync"

// Describe formats any value.
func Describe(v interface{}) string {
    if v == nil {
        return "nil"
    }
    return "value"
}

// Squares computes n squares concurrently.
func Squares(n int) []int {
    out := make([]int, n)
    var wg sync.WaitGroup
    for i := 0; i < n; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            out[i] = i * i
        }()
    }
    wg.Wait()
    return out
}
'''),
],
projectSolutionFiles=[f('legacy.go', r'''// Package legacy is written in pre-generics style.
package legacy

import "sync"

// Describe formats any value.
func Describe(v any) string {
    if v == nil {
        return "nil"
    }
    return "value"
}

// Squares computes n squares concurrently.
func Squares(n int) []int {
    out := make([]int, n)
    var wg sync.WaitGroup
    for i := range n {
        wg.Go(func() {
            out[i] = i * i
        })
    }
    wg.Wait()
    return out
}
''')],
projectInstructions='Go 1.27. Preview the suggested modernisations, apply them, and confirm nothing is left:\ngo fix -diff ./...\ngo fix ./...\ngo fix -diff ./...\nPractice: make the same changes by hand; your result should match the worked answer, for which go fix -diff reports nothing.',
projectChecks=[
dict(name='preview finds modernisations', args=['fix', '-diff', './...'], exit=1, outputContains=['+func Describe(v any) string', '+\tfor i := range n {', 'wg.Go(func() {']),
dict(name='apply fixes', args=['fix', './...']),
dict(name='nothing left to modernise', args=['fix', '-diff', './...'], stdout=''),
dict(name='answer already modern', args=['fix', '-diff', './...'], useSolution=True, stdout=''),
],
challenge='Modernise legacy.go by hand: use any, range over int, and WaitGroup.Go, so go fix -diff reports nothing.',
question='What does go fix -diff do when modernisations are available?',
correct='Prints the patch without changing files and exits with a non-zero status',
wrong=['Applies the fixes and prints a summary', 'Fails the build until fixes are applied'],
reasoning='-diff is a dry run suited to CI; plain go fix applies the changes.',
sourceURL='https://go.dev/doc/go1.26#go-command',
additionalReadings=[dict(title='Go 1.27 release notes: go fix', url='https://go.dev/doc/go1.27#go-command', section='New modernizers')]),

dict(key='go-ast', stage=STAGE, title='Reading Go source with go/parser, go/ast and go/token',
body=[
'The go/ packages expose the toolchain\'s view of source code. go/parser builds an abstract syntax tree, go/ast defines its node types and provides ast.Inspect to walk it, and go/token records positions in a FileSet so tools can report file:line:column.',
'go/types adds type checking, resolving every identifier to its object and type; golang.org/x/tools/go/packages loads whole modules with types. Linters, code generators, refactoring tools and gopls are built on these packages. Go 1.27 adds token.File.String and scanner.Scanner.End among other refinements.',
'go/format formats an AST or source the same way gofmt does, so generated code can be canonical.',
],
code=r'''package main

import (
    "fmt"
    "go/ast"
    "go/parser"
    "go/token"
)

const src = `package demo

func Exported() {}
func helper(a, b int) int { return a + b }
`

func main() {
    fset := token.NewFileSet()
    file, err := parser.ParseFile(fset, "demo.go", src, 0)
    if err != nil {
        panic(err)
    }
    ast.Inspect(file, func(n ast.Node) bool {
        if fn, ok := n.(*ast.FuncDecl); ok {
            pos := fset.Position(fn.Pos())
            fmt.Printf("%s:%d %s exported=%v params=%d\n", pos.Filename, pos.Line, fn.Name.Name, fn.Name.IsExported(), fn.Type.Params.NumFields())
        }
        return true
    })
}
''',
expectedStdout='demo.go:3 Exported exported=true params=0\ndemo.go:4 helper exported=false params=2\n',
challenge='Count the call expressions (*ast.CallExpr) in `package p; func f() { g(); h(g()) }` and print the count.',
solution=r'''package main

import (
    "fmt"
    "go/ast"
    "go/parser"
    "go/token"
)

func main() {
    file, err := parser.ParseFile(token.NewFileSet(), "p.go", "package p; func f() { g(); h(g()) }", 0)
    if err != nil {
        panic(err)
    }
    calls := 0
    ast.Inspect(file, func(n ast.Node) bool {
        if _, ok := n.(*ast.CallExpr); ok {
            calls++
        }
        return true
    })
    fmt.Println(calls)
}
''',
solutionStdout='3\n',
question='What does a token.FileSet provide to tools built on go/ast?',
correct='A mapping from compact positions to file, line and column',
wrong=['The type of every expression', 'A list of the files in the module'],
reasoning='AST nodes store token.Pos integers. The FileSet translates them into human-readable positions for diagnostics.',
sourceURL='https://pkg.go.dev/go/ast',
additionalReadings=[dict(title='go/types tutorial', url='https://github.com/golang/example/tree/master/gotypes', section='go/types')]),

dict(key='go-generate', stage=STAGE, title='Code generation with go generate',
body=[
'//go:generate command args... comments mark commands that go generate runs, in the directory of the file. Typical generators are stringer (String methods for enumerations), protocol-buffer compilers and mock generators. Generated files are committed so ordinary builds do not need the generator.',
'go generate is never run by go build or go test. Generated files should start with a line matching ^// Code generated .* DO NOT EDIT\\.$ so tools and reviewers know not to edit them; gofmt-ing the output keeps diffs clean.',
'A small generator can be a Go program in the same module run with go run, guarded by //go:build ignore so it is not part of the package build. Since Go 1.24, versioned generators can be declared as tool dependencies and run with go tool.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/gen\n\ngo 1.27\n'),
f('colors.go', r'''// Package colors shows go generate.
package colors

//go:generate go run gen.go

// Color is an enumeration with a generated String method.
type Color int

const (
    Red Color = iota
    Green
    Blue
)
'''),
f('gen.go', r'''//go:build ignore

// Command gen writes color_string.go.
package main

import (
    "fmt"
    "go/format"
    "os"
    "strings"
)

func main() {
    names := []string{"Red", "Green", "Blue"}
    var b strings.Builder
    b.WriteString("// Code generated by gen.go; DO NOT EDIT.\n\npackage colors\n\n")
    b.WriteString("func (c Color) String() string {\n\tswitch c {\n")
    for _, n := range names {
        fmt.Fprintf(&b, "\tcase %s:\n\t\treturn %q\n", n, n)
    }
    b.WriteString("\t}\n\treturn \"Color(?)\"\n}\n")
    src, err := format.Source([]byte(b.String()))
    if err != nil {
        panic(err)
    }
    if err := os.WriteFile("color_string.go", src, 0o644); err != nil {
        panic(err)
    }
}
'''),
f('color_string.go', '// Code generated by gen.go; DO NOT EDIT.\n\npackage colors\n\nfunc (c Color) String() string {\n\tswitch c {\n\tcase Red:\n\t\treturn \"Red\"\n\tcase Green:\n\t\treturn \"Green\"\n\tcase Blue:\n\t\treturn \"Blue\"\n\t}\n\treturn \"Color(?)\"\n}\n'),
f('colors_test.go', r'''package colors

import "testing"

func TestString(t *testing.T) {
    if Green.String() != "Green" {
        t.Fatal(Green.String())
    }
}
'''),
],
projectSolutionFiles=[
f('colors.go', r'''// Package colors shows go generate.
package colors

//go:generate go run gen.go

// Color is an enumeration with a generated String method.
type Color int

const (
    Red Color = iota
    Green
    Blue
    Yellow
)
'''),
f('gen.go', r'''//go:build ignore

// Command gen writes color_string.go.
package main

import (
    "fmt"
    "go/format"
    "os"
    "strings"
)

func main() {
    names := []string{"Red", "Green", "Blue", "Yellow"}
    var b strings.Builder
    b.WriteString("// Code generated by gen.go; DO NOT EDIT.\n\npackage colors\n\n")
    b.WriteString("func (c Color) String() string {\n\tswitch c {\n")
    for _, n := range names {
        fmt.Fprintf(&b, "\tcase %s:\n\t\treturn %q\n", n, n)
    }
    b.WriteString("\t}\n\treturn \"Color(?)\"\n}\n")
    src, err := format.Source([]byte(b.String()))
    if err != nil {
        panic(err)
    }
    if err := os.WriteFile("color_string.go", src, 0o644); err != nil {
        panic(err)
    }
}
'''),
f('color_string.go', '// Code generated by gen.go; DO NOT EDIT.\n\npackage colors\n\nfunc (c Color) String() string {\n\tswitch c {\n\tcase Red:\n\t\treturn \"Red\"\n\tcase Green:\n\t\treturn \"Green\"\n\tcase Blue:\n\t\treturn \"Blue\"\n\tcase Yellow:\n\t\treturn \"Yellow\"\n\t}\n\treturn \"Color(?)\"\n}\n'),
f('colors_test.go', r'''package colors

import "testing"

func TestString(t *testing.T) {
    for c, want := range map[Color]string{Green: "Green", Yellow: "Yellow", Color(9): "Color(?)"} {
        if c.String() != want {
            t.Errorf("%d: %q", int(c), c.String())
        }
    }
}
'''),
],
projectInstructions='Go 1.27. color_string.go is generated and committed, like real generated code. Run:\ngo generate ./...\ngo test ./...\ngo generate rewrites color_string.go identically; it carries a DO NOT EDIT header.\nPractice: add a Yellow constant, regenerate, and test the fallback for unknown values. Replace the three files with the worked answer.',
projectChecks=[
dict(name='generate writes the String method', args=['generate', './...']),
dict(name='generated code compiles and passes', args=['test', './...'], outputContains=['ok']),
dict(name='answer regenerate with Yellow', args=['generate', './...'], useSolution=True),
dict(name='answer tests fallback', args=['test', './...'], useSolution=True, outputContains=['ok']),
],
challenge='Add Yellow to the enumeration and the generator, regenerate, and test that unknown values print "Color(?)".',
question='When does go generate run?',
correct='Only when you invoke go generate explicitly',
wrong=['Before every go build', 'Automatically when go.mod changes'],
reasoning='Generation is a deliberate developer step. Its output is committed so builds stay fast and need no generator tools.',
sourceURL='https://go.dev/blog/generate'),

dict(key='build-flags', stage=STAGE, title='Cross-compilation, -ldflags -X, -trimpath and build info',
body=[
'GOOS and GOARCH select the target: GOOS=linux GOARCH=arm64 go build cross-compiles with no extra toolchain for pure-Go code. go tool dist list prints all supported targets.',
'-ldflags="-X main.version=1.2.3" sets a string variable at link time, a common way to stamp versions. -ldflags="-s -w" strips symbol tables for smaller binaries. -trimpath removes local file-system paths from the binary, making builds reproducible across machines.',
'Builds also embed version-control information (vcs.revision, vcs.modified) when built inside a repository, readable with go version -m or debug.ReadBuildInfo. Go 1.27\'s linker adds -macos and -macsdk options for the macOS load command.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/stamp\n\ngo 1.27\n'),
f('main.go', r'''// Command stamp prints its build version.
package main

import (
    "fmt"
    "runtime"
)

var version = "dev"

func main() {
    fmt.Println(version, runtime.GOOS)
}
'''),
],
projectSolutionFiles=[f('main.go', r'''// Command stamp prints its build version.
package main

import (
    "fmt"
    "runtime"
)

var (
    version = "dev"
    commit  = "none"
)

func main() {
    fmt.Println(version, commit, runtime.GOOS)
}
''')],
projectInstructions='Go 1.27. Run:\ngo run .\ngo run -ldflags="-X main.version=1.2.3" .\nGOOS=linux GOARCH=arm64 go build -trimpath -o stamp-linux .\ngo version -m stamp-linux\nPractice: add a commit variable and set both with one -ldflags value. Replace main.go with the worked answer.',
projectChecks=[
dict(name='default version', args=['run', '.'], stdout='dev darwin\n'),
dict(name='linker sets the version', args=['run', '-ldflags=-X main.version=1.2.3', '.'], stdout='1.2.3 darwin\n'),
dict(name='cross-compile with trimpath', args=['build', '-trimpath', '-o', 'stamp-linux', '.'], environment=dict(GOOS='linux', GOARCH='arm64', CGO_ENABLED='0')),
dict(name='build info records target and flags', args=['version', '-m', 'stamp-linux'], outputContains=['GOOS=linux', 'GOARCH=arm64', '-trimpath=true']),
dict(name='answer stamps two variables', args=['run', '-ldflags=-X main.version=2.0.0 -X main.commit=abc123', '.'], useSolution=True, stdout='2.0.0 abc123 darwin\n'),
],
challenge='Add a commit variable and set both version and commit in a single -ldflags value.',
question='What does -trimpath change?',
correct='It removes local directory paths from the compiled binary',
wrong=['It strips debug symbols', 'It shortens import paths in the source'],
reasoning='Without -trimpath, file paths of your machine appear in stack traces and build info, which hurts reproducibility.',
sourceURL='https://pkg.go.dev/cmd/go#hdr-Compile_packages_and_dependencies',
additionalReadings=[dict(title='cmd/link flags', url='https://pkg.go.dev/cmd/link', section='-X and -s -w')]),

dict(key='debugging', stage=STAGE, title='Debugging: stack traces, GOTRACEBACK, Delve and govulncheck',
body=[
'An unrecovered panic prints the panicking goroutine\'s stack; GOTRACEBACK=all prints every goroutine, and GOTRACEBACK=crash also dumps core. runtime/debug.Stack and runtime.Stack capture stacks programmatically, and since Go 1.27 tracebacks include runtime/pprof goroutine labels.',
'Delve (github.com/go-delve/delve, run as dlv debug or dlv test) is the standard Go debugger and understands goroutines, channels and interfaces. Build with -gcflags=all="-N -l" to disable optimisation and inlining when stepping through code. GODEBUG settings, such as gctrace=1, print runtime diagnostics.',
'govulncheck (golang.org/x/vuln/cmd/govulncheck) checks dependencies against the Go vulnerability database and reports only vulnerabilities your code actually reaches. Run it in CI alongside go vet and the race detector.',
],
code=r'''package main

import (
    "fmt"
    "runtime/debug"
    "strings"
)

func inner() string { return string(debug.Stack()) }

func outer() string { return inner() }

func main() {
    stack := outer()
    fmt.Println(strings.Contains(stack, "main.inner"), strings.Contains(stack, "main.outer"))
    defer func() {
        r := recover()
        fmt.Println("recovered:", r)
    }()
    var m map[string]int
    m["x"] = 1
}
''',
expectedStdout='true true\nrecovered: assignment to entry in nil map\n',
challenge='Use runtime.Callers and runtime.CallersFrames to print the function names of the first two frames above your helper.',
solution=r'''package main

import (
    "fmt"
    "runtime"
)

func callers() []string {
    pcs := make([]uintptr, 8)
    n := runtime.Callers(2, pcs)
    frames := runtime.CallersFrames(pcs[:n])
    var names []string
    for len(names) < 2 {
        f, more := frames.Next()
        names = append(names, f.Function)
        if !more {
            break
        }
    }
    return names
}

func work() []string { return callers() }

func main() {
    fmt.Println(work())
}
''',
solutionStdout='[main.work main.main]\n',
question='What does GOTRACEBACK=all add to a crash report?',
correct='Stacks of every goroutine, not just the one that panicked',
wrong=['Source code for each frame', 'A heap profile'],
reasoning='By default only the failing goroutine is shown. all reveals what other goroutines were doing, which is vital for deadlocks.',
sourceURL='https://pkg.go.dev/runtime#hdr-Environment_Variables',
additionalReadings=[dict(title='govulncheck', url='https://go.dev/doc/security/vuln/', section='Vulnerability management'),
                    dict(title='Debugging Go with Delve', url='https://github.com/go-delve/delve/tree/master/Documentation', section='Delve')]),
]

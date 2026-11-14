STAGE = '26 · Toolchain, binaries, runtime modes and images'
PKG = 'https://pkg.go.dev/'


def f(path, content):
    return dict(path=path, content=content)


def gomod(name):
    return f('go.mod', f'module example.com/{name}\n\ngo 1.27\n')


LESSONS = [
dict(key='go-types-analysis', stage=STAGE, title='Type-checking source with go/types, go/importer, go/constant and go/printer',
body=[
'go/types is the type checker used by gopls, vet and most analysers. types.Config.Check takes parsed files and an Importer for dependencies and fills a types.Info with the type of every expression (Types), the object each identifier refers to (Defs and Uses) and more. Type errors are returned rather than printed.',
'go/importer supplies importers: ForCompiler(fset, "source", nil) type-checks dependencies from source, while Default reads compiler export data. Constant expressions are evaluated exactly with go/constant values, so a checker knows that 1 << 62 fits in int64 and 1 << 64 does not.',
'go/printer prints an AST back as source, honouring comments and positions; go/format is the gofmt-styled wrapper. Together these packages let you build linters, code generators and refactoring tools that understand types, not just syntax.',
],
code=r'''package main

import (
    "bytes"
    "fmt"
    "go/ast"
    "go/constant"
    "go/format"
    "go/importer"
    "go/parser"
    "go/printer"
    "go/token"
    "go/types"
)

const src = `package demo

import "strings"

const Big = 1 << 62

func Shout(s string) string { return strings.ToUpper(s) + "!" }

var n = len(Shout("go"))
`

func main() {
    fset := token.NewFileSet()
    file, err := parser.ParseFile(fset, "demo.go", src, parser.ParseComments)
    if err != nil {
        panic(err)
    }
    info := &types.Info{Types: map[ast.Expr]types.TypeAndValue{}, Defs: map[*ast.Ident]types.Object{}}
    conf := types.Config{Importer: importer.ForCompiler(fset, "source", nil)}
    pkg, err := conf.Check("demo", fset, []*ast.File{file}, info)
    fmt.Println(pkg.Path(), err)
    for _, name := range []string{"Big", "Shout", "n"} {
        fmt.Println(name, pkg.Scope().Lookup(name).Type())
    }
    big := pkg.Scope().Lookup("Big").(*types.Const).Val()
    v, exact := constant.Int64Val(big)
    fmt.Println(v, exact, constant.Compare(big, token.LSS, constant.MakeInt64(1<<63-1)))
    var buf bytes.Buffer
    printer.Fprint(&buf, fset, file.Decls[2])
    fmt.Println(buf.String())
    formatted, err := format.Source([]byte("package p\nfunc  f( ){ }"))
    fmt.Printf("%q %v\n", formatted, err)
}
''',
expectedStdout='demo <nil>\nBig untyped int\nShout func(s string) string\nn int\n4611686018427387904 true true\nfunc Shout(s string) string\t{ return strings.ToUpper(s) + "!" }\n"package p\\n\\nfunc f() {}\\n" <nil>\n',
challenge='Type-check `package p; var x int = "text"` and print the type error that go/types returns.',
solution=r'''package main

import (
    "fmt"
    "go/ast"
    "go/parser"
    "go/token"
    "go/types"
)

func main() {
    fset := token.NewFileSet()
    file, _ := parser.ParseFile(fset, "p.go", `package p; var x int = "text"`, 0)
    _, err := (&types.Config{}).Check("p", fset, []*ast.File{file}, nil)
    fmt.Println(err)
}
''',
solutionStdout='p.go:1:24: cannot use "text" (untyped string constant) as int value in variable declaration\n',
question='What does go/types add that go/parser alone cannot provide?',
correct='The type of every expression and the object every identifier refers to',
wrong=['Formatting of source code', 'The ability to read .go files'],
reasoning='The parser builds syntax. The checker resolves names across files and packages and computes types and constant values.',
sourceURL=PKG+'go/types',
additionalReadings=[dict(title='go/constant', url=PKG+'go/constant', section='Value'), dict(title='go/importer', url=PKG+'go/importer', section='ForCompiler')]),

dict(key='go-doc-build-version', stage=STAGE, title='Documentation, build contexts and versions: go/doc, go/doc/comment, go/build, constraints and go/version',
body=[
'go/doc extracts package documentation from ASTs: the package synopsis, types with their methods, functions and examples, which is how go doc and pkg.go.dev work. go/doc/comment parses doc comments into headings, paragraphs, lists, code blocks and links, and prints them as text, Markdown or HTML; a [Name] doc link that the printer cannot resolve is written escaped as \\[Name].',
'go/build describes a build context (GOOS, GOARCH, tags) and finds which files of a package match it. go/build/constraint parses //go:build expressions so tools can evaluate them, and GoVersion extracts a go1.N requirement from one.',
'go/version (Go 1.22) compares Go version strings correctly, where simple string comparison fails: go1.9 < go1.10, and go1.27 < go1.27rc1 < go1.27.0 < go1.27.2, because a bare go1.27 names the language version, which precedes every release of it. Lang returns the language version of a toolchain version, so Lang("go1.27.2") is go1.27.',
],
code=r'''package main

import (
    "fmt"
    "go/ast"
    "go/build"
    "go/build/constraint"
    "go/doc"
    "go/doc/comment"
    "go/parser"
    "go/token"
    "go/version"
)

const src = `// Package shapes computes areas.
//
// # Usage
//
// Call [Area] with a width and height.
package shapes

// Area returns w times h.
func Area(w, h int) int { return w * h }
`

func main() {
    fset := token.NewFileSet()
    file, _ := parser.ParseFile(fset, "shapes.go", src, parser.ParseComments)
    pkg, _ := doc.NewFromFiles(fset, []*ast.File{file}, "example.com/shapes")
    fmt.Println(pkg.Synopsis(pkg.Doc))
    fmt.Println(pkg.Funcs[0].Name, pkg.Funcs[0].Doc)
    var p comment.Parser
    d := p.Parse(pkg.Doc)
    var pr comment.Printer
    fmt.Print(string(pr.Markdown(d)))
    expr, _ := constraint.Parse("//go:build linux && (amd64 || arm64) && go1.24")
    fmt.Println(expr.Eval(func(tag string) bool { return tag == "linux" || tag == "arm64" || tag == "go1.24" }), constraint.GoVersion(expr))
    ctx := build.Default
    ctx.GOOS = "windows"
    match, _ := ctx.MatchFile(".", "net_windows.go")
    fmt.Println(match, build.IsLocalImport("./x"))
    fmt.Println(version.Compare("go1.9", "go1.10"), version.Compare("go1.27rc1", "go1.27"), version.Lang("go1.27.2"), "go1.9" < "go1.10")
}
''',
expectedStdout='Package shapes computes areas.\nArea Area returns w times h.\n\nPackage shapes computes areas.\n\n### Usage {#hdr-Usage}\n\nCall \\[Area] with a width and height.\ntrue go1.24\nfalse true\n-1 1 go1.27 false\n',
challenge='Sort the versions go1.21, go1.9, go1.27.2, go1.27rc1 and go1.10 correctly with slices.SortFunc and version.Compare, and print them.',
solution=r'''package main

import (
    "fmt"
    "go/version"
    "slices"
)

func main() {
    vs := []string{"go1.21", "go1.9", "go1.27.2", "go1.27rc1", "go1.10"}
    slices.SortFunc(vs, version.Compare)
    fmt.Println(vs)
}
''',
solutionStdout='[go1.9 go1.10 go1.21 go1.27rc1 go1.27.2]\n',
question='Why use go/version.Compare instead of comparing version strings with <?',
correct='String order is wrong for versions: "go1.9" sorts after "go1.10" lexically',
wrong=['Strings cannot be compared in Go', 'version.Compare also checks the network for releases'],
reasoning='Version components are numbers with release-candidate suffixes. Compare parses them; < compares bytes.',
sourceURL=PKG+'go/version',
additionalReadings=[dict(title='go/doc/comment', url=PKG+'go/doc/comment', section='Parser and Printer'), dict(title='go/build/constraint', url=PKG+'go/build/constraint', section='Parse')]),

dict(key='binary-formats-project', stage=STAGE, title='Project: inspecting ELF, PE, Mach-O and Plan 9 binaries',
body=[
'Go can build executables for many systems from one machine, and the debug/ packages can read them all. debug/elf reads Linux and BSD executables, debug/pe reads Windows, debug/macho reads macOS and debug/plan9obj reads Plan 9. Each exposes the file header (machine, type) and sections such as .text and .gopclntab.',
'debug/buildinfo reads the Go version, module path, dependencies and build settings embedded in a Go binary in ELF, PE, Mach-O, XCOFF or Wasm format: the same data go version -m prints. It does not read Plan 9 binaries, which this project shows. debug/dwarf reads the debugging information the linker writes (compilation units, functions, types), unless -ldflags=-w stripped it.',
'debug/gosym decodes Go\'s own symbol and line tables (.gopclntab), mapping program counters to functions and source lines. This project cross-builds one program for Linux, Windows, macOS and Plan 9, then a second command inspects every binary.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('inspect'),
f('cmd/hello/main.go', r'''// Command hello is the binary that gets inspected.
package main

import "fmt"

func main() { fmt.Println("hello") }
'''),
f('cmd/inspect/main.go', r'''// Command inspect reports on executables built for different systems.
package main

import (
    "debug/buildinfo"
    "debug/dwarf"
    "debug/elf"
    "debug/gosym"
    "debug/macho"
    "debug/pe"
    "debug/plan9obj"
    "fmt"
    "os"
)

func main() {
    for _, path := range os.Args[1:] {
        if info, err := buildinfo.ReadFile(path); err != nil {
            fmt.Printf("%s no Go build info:", path)
        } else {
            fmt.Printf("%s %s %s:", path, info.GoVersion, info.Path)
        }
        if f, err := elf.Open(path); err == nil {
            fmt.Print(" elf ", f.Machine)
            pcln, _ := f.Section(".gopclntab").Data()
            table, err := gosym.NewTable(nil, gosym.NewLineTable(pcln, f.Section(".text").Addr))
            if err == nil {
                fmt.Print(" main.main found=", table.LookupFunc("main.main") != nil)
            }
            if d, err := f.DWARF(); err == nil {
                fmt.Print(" dwarf")
                if e, err := d.Reader().Next(); err == nil && e.Tag == dwarf.TagCompileUnit {
                    fmt.Print(" cu")
                }
            }
            f.Close()
        }
        if f, err := pe.Open(path); err == nil {
            fmt.Printf(" pe machine=%#x", f.Machine)
            f.Close()
        }
        if f, err := macho.Open(path); err == nil {
            fmt.Print(" macho ", f.Cpu)
            if _, err := f.DWARF(); err == nil {
                fmt.Print(" dwarf")
            }
            f.Close()
        }
        if f, err := plan9obj.Open(path); err == nil {
            syms, _ := f.Symbols()
            fmt.Print(" plan9 symbols=", len(syms) > 0)
            f.Close()
        }
        fmt.Println()
    }
}
'''),
],
projectSolutionFiles=[f('cmd/inspect/deps.go', r'''package main

import (
    "debug/buildinfo"
    "fmt"
)

// settings prints selected build settings recorded in a binary.
func settings(path string) {
    info, err := buildinfo.ReadFile(path)
    if err != nil {
        fmt.Println(err)
        return
    }
    for _, s := range info.Settings {
        if s.Key == "GOOS" || s.Key == "GOARCH" || s.Key == "-ldflags" {
            fmt.Printf("%s=%s\n", s.Key, s.Value)
        }
    }
}
'''), f('cmd/inspect/deps_test.go', r'''package main

import "testing"

func TestSettings(t *testing.T) {
    settings("../../hello.linux")
}
''')],
projectInstructions='Go 1.27, standard library only; cross-compilation needs no extra tools. From the module root run:\nGOOS=linux GOARCH=amd64 go build -o hello.linux ./cmd/hello\nGOOS=windows GOARCH=amd64 go build -o hello.exe ./cmd/hello\nGOOS=plan9 GOARCH=amd64 go build -o hello.plan9 ./cmd/hello\ngo build -o hello.darwin ./cmd/hello\ngo build -ldflags=-w -o hello.nodwarf.linux ./cmd/hello (with GOOS=linux)\ngo run ./cmd/inspect hello.linux hello.exe hello.plan9 hello.darwin hello.nodwarf.linux\nEach line names the format; the -w build has no DWARF.\nPractice: add a settings function that prints the GOOS, GOARCH and -ldflags build settings recorded in a binary.',
projectChecks=[
dict(name='build linux', args=['build', '-o', 'hello.linux', './cmd/hello'], environment=dict(GOOS='linux', GOARCH='amd64', CGO_ENABLED='0')),
dict(name='build windows', args=['build', '-o', 'hello.exe', './cmd/hello'], environment=dict(GOOS='windows', GOARCH='amd64', CGO_ENABLED='0')),
dict(name='build plan9', args=['build', '-o', 'hello.plan9', './cmd/hello'], environment=dict(GOOS='plan9', GOARCH='amd64', CGO_ENABLED='0')),
dict(name='build darwin', args=['build', '-o', 'hello.darwin', './cmd/hello']),
dict(name='build linux without DWARF', args=['build', '-ldflags=-w', '-o', 'hello.nodwarf.linux', './cmd/hello'], environment=dict(GOOS='linux', GOARCH='amd64', CGO_ENABLED='0')),
dict(name='inspect every format', args=['run', './cmd/inspect', 'hello.linux', 'hello.exe', 'hello.plan9', 'hello.darwin', 'hello.nodwarf.linux'],
     stdout='hello.linux go1.27.2 example.com/inspect/cmd/hello: elf EM_X86_64 main.main found=true dwarf cu\nhello.exe go1.27.2 example.com/inspect/cmd/hello: pe machine=0x8664\nhello.plan9 no Go build info: plan9 symbols=true\nhello.darwin go1.27.2 example.com/inspect/cmd/hello: macho CpuArm64 dwarf\nhello.nodwarf.linux go1.27.2 example.com/inspect/cmd/hello: elf EM_X86_64 main.main found=true\n'),
dict(name='answer build linux', args=['build', '-o', 'hello.linux', './cmd/hello'], environment=dict(GOOS='linux', GOARCH='amd64', CGO_ENABLED='0'), useSolution=True),
dict(name='answer prints build settings', args=['test', '-v', './cmd/inspect'], useSolution=True, outputContains=['GOOS=linux', 'GOARCH=amd64', '--- PASS: TestSettings']),
],
challenge='Add a settings(path) function that prints the GOOS, GOARCH and -ldflags build settings recorded in a binary by debug/buildinfo.',
question='Which package reads the Go version and module information embedded in an ELF, PE or Mach-O binary?',
correct='debug/buildinfo',
wrong=['debug/elf', 'runtime/debug only, for the running program'],
reasoning='buildinfo understands ELF, PE, Mach-O, XCOFF and Wasm and finds the embedded build information in each; the project shows it reports none for Plan 9.',
sourceURL=PKG+'debug/buildinfo',
additionalReadings=[dict(title='debug/gosym', url=PKG+'debug/gosym', section='Table'), dict(title='debug/dwarf', url=PKG+'debug/dwarf', section='Data')],
minutes=45),

dict(key='runtime-modes-project', stage=STAGE, title='Project: runtime/race, runtime/cgo and runtime/coverage',
body=[
'Some runtime packages exist to be linked rather than called. runtime/race holds the race detector runtime; it is linked automatically by -race and has no public API. runtime/cgo is the support code that lets Go call C and run C threads; a blank import _ "runtime/cgo" forces the cgo-based runtime even when no package uses import "C".',
'runtime/coverage (Go 1.20) lets a long-running program built with go build -cover write its coverage data on demand: WriteMetaDir and WriteCountersDir dump counters without exiting, and ClearCounters resets them between phases; writing counters while running requires -covermode=atomic. go tool covdata then merges and reports the data.',
'This project builds a server-like program with -cover, has it write coverage for two phases into a directory, and reports the percentage with go tool covdata. A blank import of runtime/cgo is included to show the build still works with CGO_ENABLED=1 and fails with CGO_ENABLED=0.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('modes'),
f('main.go', r'''// Command modes writes its own coverage data while running.
package main

import (
    "fmt"
    "os"
    _ "runtime/cgo"
    "runtime/coverage"
)

func classify(n int) string {
    if n < 0 {
        return "negative"
    }
    if n == 0 {
        return "zero"
    }
    return "positive"
}

func main() {
    dir := os.Args[1]
    fmt.Println(classify(5))
    if err := coverage.WriteMetaDir(dir); err != nil {
        fmt.Println("not built with -cover:", err != nil)
        return
    }
    if err := coverage.WriteCountersDir(dir); err != nil {
        panic(err)
    }
    fmt.Println("coverage written")
}
'''),
f('race_test.go', r'''package main

import (
    _ "runtime/race" // linked anyway by -race; imported here to show it has no API
    "sync"
    "testing"
)

func TestClassifyConcurrently(t *testing.T) {
    var wg sync.WaitGroup
    for i := range 8 {
        wg.Go(func() { _ = classify(i - 4) })
    }
    wg.Wait()
}
'''),
],
projectSolutionFiles=[f('main.go', r'''// Command modes writes its own coverage data while running.
package main

import (
    "fmt"
    "os"
    _ "runtime/cgo"
    "runtime/coverage"
)

func classify(n int) string {
    if n < 0 {
        return "negative"
    }
    if n == 0 {
        return "zero"
    }
    return "positive"
}

func main() {
    dir := os.Args[1]
    for _, n := range []int{5, 0, -5} {
        fmt.Println(classify(n))
    }
    if err := coverage.WriteMetaDir(dir); err != nil {
        fmt.Println("not built with -cover:", err != nil)
        return
    }
    if err := coverage.WriteCountersDir(dir); err != nil {
        panic(err)
    }
    fmt.Println("coverage written")
}
''')],
projectInstructions='Go 1.27 with cgo (Xcode command-line tools on macOS). Run:\ngo build -cover -covermode=atomic -o modes .\nmkdir cov && ./modes cov\ngo tool covdata percent -i=cov\ngo test -race ./...\nThe program writes its own coverage data while running. Without -cover it reports that it was not instrumented.\nPractice: exercise all three branches of classify and confirm with go tool covdata func that classify reaches 100% (main\'s error paths stay uncovered). Replace main.go with the worked answer.',
projectChecks=[
dict(name='without -cover there is nothing to write', args=['run', '.', 'cov-none'], stdout='positive\nnot built with -cover: true\n'),
dict(name='build instrumented binary', args=['build', '-cover', '-covermode=atomic', '-o', 'modes', '.']),
dict(name='write coverage while running', args=['run', '-cover', '-covermode=atomic', '.', '.'], stdout='positive\ncoverage written\n'),
dict(name='report written coverage', args=['tool', 'covdata', 'percent', '-i=.'], outputContains=['example.com/modes', 'coverage: 53.8% of statements']),
dict(name='race runtime linked by -race', args=['test', '-race', '-count=1', './...'], timeout=240, outputContains=['ok']),
dict(name='runtime/cgo needs cgo', args=['build', '-o', '/dev/null', '.'], environment=dict(CGO_ENABLED='0'), exit=1, outputContains=['_cgo_init: relocation target x_cgo_init not defined']),
dict(name='answer covers every branch', args=['run', '-cover', '-covermode=atomic', '.', '.'], useSolution=True, stdout='positive\nzero\nnegative\ncoverage written\n'),
dict(name='answer covers classify completely', args=['tool', 'covdata', 'func', '-i=.'], useSolution=True, outputContains=['main.go:12:\tclassify\t100.0%']),
],
challenge='Call classify with 5, 0 and -5 so that go tool covdata func reports classify at 100% coverage.',
question='When is runtime/coverage.WriteCountersDir useful?',
correct='For long-running programs built with -cover that must report coverage without exiting',
wrong=['For every go test run', 'To collect CPU profiles'],
reasoning='Normally coverage is written at exit. Servers in integration tests can write snapshots on demand instead.',
sourceURL=PKG+'runtime/coverage',
additionalReadings=[dict(title='runtime/race', url=PKG+'runtime/race', section='Race detector'), dict(title='runtime/cgo', url=PKG+'runtime/cgo', section='cgo runtime')],
minutes=45),

dict(key='plugin-project', stage=STAGE, title='Project: loading code at run time with plugin',
body=[
'go build -buildmode=plugin compiles a main package into a shared object that another Go program can open with plugin.Open. Lookup returns an exported variable (as a pointer) or function by name, as a plugin.Symbol that you type-assert.',
'Plugins are restrictive: they work only on Linux, FreeBSD and macOS, need cgo, and the plugin and host must be built with the same toolchain, the same build flags and identical versions of every shared dependency. A plugin cannot be unloaded.',
'Because of those constraints, most Go programs prefer other extension mechanisms: separate processes speaking RPC (as HashiCorp\'s go-plugin does), WebAssembly, or simply compiling extensions in. Use plugin only when you control both builds.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('host'),
f('greeter/main.go', r'''// Package main is built as a plugin.
package main

// Greeting is looked up as a variable.
var Greeting = "hello"

// Greet is looked up as a function.
func Greet(name string) string { return Greeting + ", " + name }
'''),
f('main.go', r'''// Command host loads greeter.so at run time.
package main

import (
    "fmt"
    "plugin"
)

func main() {
    p, err := plugin.Open("greeter.so")
    if err != nil {
        fmt.Println("open:", err)
        return
    }
    v, _ := p.Lookup("Greeting")
    *v.(*string) = "hi"
    g, _ := p.Lookup("Greet")
    fmt.Println(g.(func(string) string)("plugin"))
    _, err = p.Lookup("Missing")
    fmt.Println(err != nil)
}
'''),
],
projectSolutionFiles=[f('greeter/main.go', r'''// Package main is built as a plugin.
package main

import "strings"

// Greeting is looked up as a variable.
var Greeting = "hello"

// Greet is looked up as a function.
func Greet(name string) string { return Greeting + ", " + strings.ToUpper(name) }
''')],
projectInstructions='Go 1.27 on macOS or Linux with cgo. Build the plugin, then run the host:\ngo build -buildmode=plugin -o greeter.so ./greeter\ngo run .\nExpected: hi, plugin then true. Running the host before building the plugin reports the open error.\nPractice: make Greet upper-case the name, rebuild only the plugin, and rerun the host. Replace greeter/main.go with the worked answer.',
projectChecks=[
dict(name='host before plugin exists', args=['run', '.'], outputContains=['open: plugin.Open("greeter.so")']),
dict(name='build plugin', args=['build', '-buildmode=plugin', '-o', 'greeter.so', './greeter'], timeout=240),
dict(name='host loads plugin symbols', args=['run', '.'], stdout='hi, plugin\ntrue\n'),
dict(name='answer rebuild plugin', args=['build', '-buildmode=plugin', '-o', 'greeter.so', './greeter'], useSolution=True, timeout=240),
dict(name='answer host sees new behaviour', args=['run', '.'], useSolution=True, stdout='hi, PLUGIN\ntrue\n'),
],
challenge='Change the plugin so Greet upper-cases the name, rebuild only the plugin, and run the unchanged host.',
question='What must match between a plugin and the program that loads it?',
correct='The toolchain version, build flags and versions of shared dependencies',
wrong=['Only the operating system', 'Nothing; plugins are self-contained'],
reasoning='The runtime checks that packages shared by host and plugin are identical builds; any mismatch makes plugin.Open fail.',
sourceURL=PKG+'plugin',
minutes=30),

dict(key='quick-slogtest-project', stage=STAGE, title='Project: property tests with testing/quick and handler conformance with testing/slogtest',
body=[
'testing/quick generates random inputs for a function and checks a property: quick.Check(f, nil) calls f(bool-returning) with random arguments until it returns false or the iteration limit is reached; CheckEqual compares two implementations. The package is frozen, and native fuzzing is now preferred for exploration, but quick remains handy for small algebraic properties.',
'testing/slogtest checks that a custom slog.Handler behaves like the standard ones: it logs a series of records, then asks your test to parse what the handler wrote and compares the results with the rules every handler must follow, such as ignoring empty attributes and nesting groups.',
'This project tests an encoding function with properties, then writes a minimal key=value slog handler and proves it conforms with slogtest.Run.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
gomod('props'),
f('props.go', r'''// Package props holds functions tested with properties.
package props

// Rotate shifts each ASCII letter by n places, wrapping within its case.
func Rotate(s string, n int) string {
    out := []byte(s)
    for i, c := range out {
        switch {
        case c >= 'a' && c <= 'z':
            out[i] = 'a' + byte((int(c-'a')+n%26+26)%26)
        case c >= 'A' && c <= 'Z':
            out[i] = 'A' + byte((int(c-'A')+n%26+26)%26)
        }
    }
    return string(out)
}
'''),
f('props_test.go', r'''package props

import (
    "math/rand"
    "testing"
    "testing/quick"
)

func TestRotateRoundTrip(t *testing.T) {
    const s = "Hello, Gophers zZ"
    f := func(n int) bool { return Rotate(Rotate(s, n), -n) == s }
    // A fixed seed makes failures reproducible.
    if err := quick.Check(f, &quick.Config{MaxCount: 500, Rand: rand.New(rand.NewSource(1))}); err != nil {
        t.Fatal(err)
    }
}

func TestRotateMatchesRepeatedSteps(t *testing.T) {
    step := func(s string, k uint8) string {
        for range k % 30 {
            s = Rotate(s, 1)
        }
        return s
    }
    direct := func(s string, k uint8) string { return Rotate(s, int(k%30)) }
    if err := quick.CheckEqual(direct, step, nil); err != nil {
        t.Fatal(err)
    }
}
'''),
f('handler.go', r'''package props

import (
    "context"
    "fmt"
    "io"
    "log/slog"
    "strings"
    "sync"
)

// KVHandler writes one line of key=value pairs per record.
type KVHandler struct {
    mu     *sync.Mutex
    w      io.Writer
    attrs  []slog.Attr
    groups []string
}

// NewKVHandler returns a handler writing to w.
func NewKVHandler(w io.Writer) *KVHandler { return &KVHandler{mu: &sync.Mutex{}, w: w} }

func (h *KVHandler) Enabled(context.Context, slog.Level) bool { return true }

func (h *KVHandler) WithAttrs(as []slog.Attr) slog.Handler {
    c := *h
    prefix := strings.Join(h.groups, ".")
    for _, a := range as {
        if prefix != "" {
            a.Key = prefix + "." + a.Key
        }
        c.attrs = append(c.attrs[:len(c.attrs):len(c.attrs)], a)
    }
    return &c
}

func (h *KVHandler) WithGroup(name string) slog.Handler {
    if name == "" {
        return h
    }
    c := *h
    c.groups = append(c.groups[:len(c.groups):len(c.groups)], name)
    return &c
}

func (h *KVHandler) Handle(_ context.Context, r slog.Record) error {
    var b strings.Builder
    if !r.Time.IsZero() {
        fmt.Fprintf(&b, "time=%d ", r.Time.UnixNano())
    }
    fmt.Fprintf(&b, "level=%s msg=%q", r.Level, r.Message)
    for _, a := range h.attrs {
        write(&b, "", a)
    }
    prefix := strings.Join(h.groups, ".")
    r.Attrs(func(a slog.Attr) bool {
        write(&b, prefix, a)
        return true
    })
    h.mu.Lock()
    defer h.mu.Unlock()
    _, err := fmt.Fprintln(h.w, b.String())
    return err
}

func write(b *strings.Builder, prefix string, a slog.Attr) {
    a.Value = a.Value.Resolve()
    if a.Equal(slog.Attr{}) {
        return
    }
    key := a.Key
    if prefix != "" && key != "" {
        key = prefix + "." + key
    } else if key == "" {
        key = prefix
    }
    if a.Value.Kind() == slog.KindGroup {
        for _, g := range a.Value.Group() {
            write(b, key, g)
        }
        return
    }
    fmt.Fprintf(b, " %s=%q", key, a.Value.String())
}
'''),
f('handler_test.go', r'''package props

import (
    "bytes"
    "log/slog"
    "strconv"
    "strings"
    "testing"
    "testing/slogtest"
)

func parse(line string) map[string]any {
    out := map[string]any{}
    for _, field := range strings.Fields(line) {
        k, v, _ := strings.Cut(field, "=")
        if u, err := strconv.Unquote(v); err == nil {
            v = u
        }
        m := out
        parts := strings.Split(k, ".")
        for _, p := range parts[:len(parts)-1] {
            sub, ok := m[p].(map[string]any)
            if !ok {
                sub = map[string]any{}
                m[p] = sub
            }
            m = sub
        }
        if k == "time" {
            m[k] = 1
            continue
        }
        m[parts[len(parts)-1]] = v
    }
    return out
}

func TestKVHandlerConforms(t *testing.T) {
    var buf bytes.Buffer
    h := NewKVHandler(&buf)
    results := func() []map[string]any {
        var ms []map[string]any
        for line := range strings.Lines(buf.String()) {
            ms = append(ms, parse(strings.TrimSpace(line)))
        }
        return ms
    }
    if err := slogtest.TestHandler(h, results); err != nil {
        t.Fatal(err)
    }
    _ = slog.New(h)
}
'''),
],
projectSolutionFiles=[f('extra_test.go', r'''package props

import (
    "testing"
    "testing/quick"
)

func TestRotateKeepsLength(t *testing.T) {
    if err := quick.Check(func(s string, n int) bool { return len(Rotate(s, n)) == len(s) }, nil); err != nil {
        t.Fatal(err)
    }
}
''')],
projectInstructions='Go 1.27, standard library only. Run:\ngo test -count=1 -v ./...\nTwo property tests and the slogtest conformance test pass. A mutation that breaks the wrap-around for negative shifts is caught by the round-trip property.\nPractice: add a property that Rotate never changes the length of its input. Add extra_test.go from the worked answer.',
projectChecks=[
dict(name='properties and handler conformance', args=['test', '-count=1', '-v', './...'], outputContains=['--- PASS: TestRotateRoundTrip', '--- PASS: TestRotateMatchesRepeatedSteps', '--- PASS: TestKVHandlerConforms']),
dict(name='broken negative wrap-around is found', args=['test', '-count=1', '-run', 'TestRotateRoundTrip', './...'], exit=1,
     mutations=[dict(path='props.go', find="out[i] = 'a' + byte((int(c-'a')+n%26+26)%26)", replace="out[i] = 'a' + byte((int(c-'a')+n)%26)")], outputContains=['failed on input']),
dict(name='handler that drops groups fails slogtest', args=['test', '-count=1', '-run', 'TestKVHandlerConforms', './...'], exit=1,
     mutations=[dict(path='handler.go', find='    c.groups = append(c.groups[:len(c.groups):len(c.groups)], name)\n', replace='')], outputContains=['FAIL']),
dict(name='answer length property', args=['test', '-count=1', '-v', '-run', 'TestRotateKeepsLength', './...'], useSolution=True, outputContains=['--- PASS: TestRotateKeepsLength']),
],
challenge='Add a quick.Check property that Rotate never changes the length of its input.',
question='What does slogtest.TestHandler check?',
correct='That a handler\'s output follows the rules every slog.Handler must obey',
wrong=['That the handler is fast enough', 'That log lines are valid JSON'],
reasoning='It logs records exercising groups, attributes and edge cases, then compares your parsed output with the expected structure.',
sourceURL=PKG+'testing/slogtest',
additionalReadings=[dict(title='testing/quick', url=PKG+'testing/quick', section='Check')],
minutes=45),

dict(key='images', stage=STAGE, title='Images: image, color, draw, palette and the PNG, GIF and JPEG codecs',
body=[
'Package image defines the Image interface (ColorModel, Bounds, At) and concrete types such as RGBA, NRGBA, Gray and Paletted. Rectangles and points use image.Rect and image.Pt; Bounds need not start at (0, 0). image/color defines colour models and conversions, and image/color/palette provides the Plan 9 and Web-safe palettes.',
'image/draw composes images: draw.Draw copies or blends a source onto a destination with draw.Src or draw.Over, and draw.FloydSteinberg dithers when converting to a palette. golang.org/x/image adds scaling and fonts.',
'image/png (lossless), image/gif (palettes and animation) and image/jpeg (lossy) encode and decode. Decoders register themselves when imported, so image.Decode and image.DecodeConfig detect the format from the data. Use DecodeConfig to check dimensions before decoding untrusted images, because a small file can describe an enormous image.',
],
code=r'''package main

import (
    "bytes"
    "fmt"
    "image"
    "image/color"
    "image/color/palette"
    "image/draw"
    "image/gif"
    "image/jpeg"
    "image/png"
)

func main() {
    img := image.NewRGBA(image.Rect(0, 0, 4, 2))
    draw.Draw(img, img.Bounds(), &image.Uniform{color.RGBA{0, 0, 255, 255}}, image.Point{}, draw.Src)
    img.Set(0, 0, color.White)
    fmt.Println(img.Bounds(), img.At(0, 0), img.At(3, 1))
    gray := color.GrayModel.Convert(color.RGBA{255, 0, 0, 255}).(color.Gray)
    fmt.Println(gray.Y, len(palette.WebSafe), len(palette.Plan9))
    var pngBuf, gifBuf, jpgBuf bytes.Buffer
    png.Encode(&pngBuf, img)
    pal := image.NewPaletted(img.Bounds(), palette.WebSafe)
    draw.FloydSteinberg.Draw(pal, img.Bounds(), img, image.Point{})
    gif.Encode(&gifBuf, pal, nil)
    jpeg.Encode(&jpgBuf, img, &jpeg.Options{Quality: 90})
    for _, buf := range []*bytes.Buffer{&pngBuf, &gifBuf, &jpgBuf} {
        cfg, format, err := image.DecodeConfig(bytes.NewReader(buf.Bytes()))
        fmt.Println(format, cfg.Width, cfg.Height, err)
    }
    back, _ := png.Decode(&pngBuf)
    fmt.Println(back.At(3, 1) == color.Color(color.RGBA{0, 0, 255, 255}))
}
''',
expectedStdout='(0,0)-(4,2) {255 255 255 255} {0 0 255 255}\n76 216 256\npng 4 2 <nil>\ngif 4 2 <nil>\njpeg 4 2 <nil>\ntrue\n',
challenge='Create a two-frame animated GIF (a red frame then a green frame, 2x2 each) with gif.EncodeAll and decode it again with gif.DecodeAll, printing the number of frames.',
solution=r'''package main

import (
    "bytes"
    "fmt"
    "image"
    "image/color"
    "image/gif"
)

func frame(c color.Color) *image.Paletted {
    p := image.NewPaletted(image.Rect(0, 0, 2, 2), color.Palette{c})
    return p
}

func main() {
    anim := &gif.GIF{Image: []*image.Paletted{frame(color.RGBA{255, 0, 0, 255}), frame(color.RGBA{0, 255, 0, 255})}, Delay: []int{10, 10}}
    var buf bytes.Buffer
    if err := gif.EncodeAll(&buf, anim); err != nil {
        panic(err)
    }
    back, err := gif.DecodeAll(&buf)
    fmt.Println(len(back.Image), err)
}
''',
solutionStdout='2 <nil>\n',
question='Why call image.DecodeConfig before decoding an untrusted image?',
correct='It reads only the header, so you can reject huge dimensions before allocating memory',
wrong=['Decode fails without a prior DecodeConfig', 'It converts the image to RGBA'],
reasoning='A few kilobytes can declare a gigapixel image. Checking width and height first prevents memory exhaustion.',
sourceURL=PKG+'image',
additionalReadings=[dict(title='image/draw', url=PKG+'image/draw', section='Draw'), dict(title='The Go image package', url='https://go.dev/blog/image', section='Images')]),
]

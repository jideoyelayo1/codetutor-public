STAGE = '17 · Systems, reflection and unsafe'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='os-exec', stage=STAGE, title='Running processes with os/exec',
body=[
'exec.Command(name, args...) prepares a process; arguments are passed directly, not through a shell, so there is no quoting or injection risk from spaces and metacharacters. Output runs it and returns stdout; CombinedOutput merges stderr. Run, Start and Wait give finer control, and StdinPipe/StdoutPipe connect streams.',
'exec.CommandContext kills the process when the context is cancelled or its deadline passes; Cmd.Cancel and WaitDelay customise how. A non-zero exit returns an *exec.ExitError carrying the exit code.',
'exec.LookPath finds programs on PATH and, since Go 1.19, refuses to run a program found in the current directory through a relative PATH entry, a common attack. Never build a command line by concatenating untrusted input into "sh -c".',
],
code=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "os/exec"
    "strings"
    "time"
)

func main() {
    out, err := exec.Command("echo", "hello", "from a child").Output()
    fmt.Printf("%q %v\n", out, err)
    err = exec.Command("sh", "-c", "exit 3").Run()
    var exitErr *exec.ExitError
    fmt.Println(errors.As(err, &exitErr), exitErr.ExitCode())
    ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
    defer cancel()
    err = exec.CommandContext(ctx, "sleep", "5").Run()
    fmt.Println(strings.Contains(err.Error(), "killed"), ctx.Err())
}
''',
expectedStdout='"hello from a child\\n" <nil>\ntrue 3\ntrue context deadline exceeded\n',
challenge='Run "tr a-z A-Z" with cmd.Stdin set to strings.NewReader("pipe me") and print its output.',
solution=r'''package main

import (
    "fmt"
    "os/exec"
    "strings"
)

func main() {
    cmd := exec.Command("tr", "a-z", "A-Z")
    cmd.Stdin = strings.NewReader("pipe me")
    out, err := cmd.Output()
    fmt.Println(string(out), err)
}
''',
solutionStdout='PIPE ME <nil>\n',
question='Why is exec.Command("rm", userPath) safer than exec.Command("sh", "-c", "rm "+userPath)?',
correct='Arguments go straight to the program, so no shell parses the untrusted text',
wrong=['rm refuses paths from Go programs', 'sh -c is not available on Unix'],
reasoning='A shell interprets spaces, semicolons and $(…). Passing arguments directly keeps the path a single, literal argument.',
sourceURL='https://pkg.go.dev/os/exec'),

dict(key='signals', stage=STAGE, title='Handling signals with os/signal',
body=[
'Programs receive signals such as SIGINT (Ctrl-C) and SIGTERM (container stop). signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM) returns a context cancelled when one arrives, which plugs straight into graceful shutdown code.',
'signal.Notify(ch, sigs...) delivers signals to a channel instead; use a buffered channel so the runtime never drops a signal while you are busy. signal.Stop or the stop function from NotifyContext restores default behaviour, so a second Ctrl-C can kill a stuck program.',
'SIGKILL and SIGSTOP cannot be caught. Signal handling is process-wide, so libraries should not install handlers; leave that to main.',
],
code=r'''package main

import (
    "context"
    "fmt"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGUSR1)
    defer stop()
    go func() {
        time.Sleep(10 * time.Millisecond)
        syscall.Kill(os.Getpid(), syscall.SIGUSR1)
    }()
    select {
    case <-ctx.Done():
        fmt.Println("signal received:", context.Cause(ctx))
    case <-time.After(5 * time.Second):
        fmt.Println("timed out")
    }
}
''',
expectedStdout='signal received: user defined signal 1 signal received\n',
challenge='Use signal.Notify with a buffered channel to catch SIGUSR2 sent to yourself twice, and print the number of signals received.',
solution=r'''package main

import (
    "fmt"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    ch := make(chan os.Signal, 2)
    signal.Notify(ch, syscall.SIGUSR2)
    defer signal.Stop(ch)
    syscall.Kill(os.Getpid(), syscall.SIGUSR2)
    <-ch
    syscall.Kill(os.Getpid(), syscall.SIGUSR2)
    <-ch
    select {
    case <-ch:
        fmt.Println("unexpected")
    case <-time.After(10 * time.Millisecond):
        fmt.Println(2)
    }
}
''',
solutionStdout='2\n',
question='Why must the channel passed to signal.Notify be buffered?',
correct='The runtime does not block when sending, so signals arriving while you are busy would be dropped',
wrong=['Unbuffered channels cannot carry os.Signal', 'Notify panics on unbuffered channels'],
reasoning='Signal delivery uses a non-blocking send. A buffer gives the receiver time to catch up.',
sourceURL='https://pkg.go.dev/os/signal'),

dict(key='reflection', stage=STAGE, title='Reflection with reflect: types, values and struct tags',
body=[
'reflect.TypeOf(x) returns a reflect.Type describing x\'s dynamic type; reflect.ValueOf(x) returns a reflect.Value holding it. Kind() reports the basic category (Struct, Slice, Ptr…), NumField and Field walk struct fields, and Field(i).Tag.Get("json") reads tags. reflect.TypeFor[T]() (Go 1.22) gets a Type without a value.',
'To modify a value through reflection you need an addressable Value: reflect.ValueOf(&x).Elem(). CanSet reports whether a field can be set; unexported fields cannot. Setting a value of the wrong type panics.',
'Reflection powers encoding/json, fmt and template packages, but it is slower, bypasses compile-time checking and panics on misuse. Prefer generics or interfaces in ordinary code; use reflection for generic infrastructure such as encoders and validators.',
],
code=r'''package main

import (
    "fmt"
    "reflect"
)

type User struct {
    Name  string `validate:"required"`
    Email string `validate:"required"`
    Age   int
    note  string
}

func missing(v any) []string {
    var out []string
    rv := reflect.ValueOf(v)
    rt := rv.Type()
    for i := range rt.NumField() {
        field := rt.Field(i)
        if field.Tag.Get("validate") == "required" && rv.Field(i).IsZero() {
            out = append(out, field.Name)
        }
    }
    return out
}

func main() {
    u := User{Name: "Ada"}
    fmt.Println(missing(u))
    rv := reflect.ValueOf(&u).Elem()
    rv.FieldByName("Age").SetInt(36)
    fmt.Println(u.Age, rv.FieldByName("note").CanSet())
    fmt.Println(reflect.TypeFor[[]User]().Elem().Name(), reflect.TypeOf(u).Kind())
}
''',
expectedStdout='[Email]\n36 false\nUser struct\n',
challenge='Write func fieldNames(v any) []string that returns the names of all exported fields of a struct (or pointer to struct), and print it for &User{}.',
solution=r'''package main

import (
    "fmt"
    "reflect"
)

type User struct {
    Name, Email string
    Age         int
    note        string
}

func fieldNames(v any) []string {
    t := reflect.TypeOf(v)
    if t.Kind() == reflect.Pointer {
        t = t.Elem()
    }
    var out []string
    for i := range t.NumField() {
        if t.Field(i).IsExported() {
            out = append(out, t.Field(i).Name)
        }
    }
    return out
}

func main() {
    fmt.Println(fieldNames(&User{}))
}
''',
solutionStdout='[Name Email Age]\n',
question='Why does reflect.ValueOf(u).Field(0).SetString("x") panic?',
correct='ValueOf(u) holds a copy, which is not addressable; use ValueOf(&u).Elem()',
wrong=['Strings cannot be set through reflection', 'Field(0) is unexported'],
reasoning='Setting needs an addressable value that refers to the original variable. Passing a pointer and calling Elem provides one.',
sourceURL='https://go.dev/blog/laws-of-reflection',
additionalReadings=[dict(title='reflect package', url='https://pkg.go.dev/reflect', section='Type and Value')]),

dict(key='unsafe-pointer', stage=STAGE, title='unsafe.Pointer and its valid conversion patterns',
body=[
'Package unsafe steps outside Go\'s type safety. unsafe.Pointer can be converted to and from any pointer type and to uintptr. The unsafe package documents six valid patterns, such as converting *T1 to *T2 when the memory layouts are compatible, and pointer arithmetic expressed in a single expression: unsafe.Pointer(uintptr(p) + offset).',
'A uintptr is just an integer: the garbage collector does not treat it as a reference and may move or free the object it came from, so storing a uintptr and converting back later is invalid. unsafe.Add(p, n) (Go 1.17) performs the arithmetic safely without a uintptr round trip.',
'unsafe code is not portable across architectures or Go versions, and go vet\'s unsafeptr check flags suspicious conversions. Use it only for interoperability (cgo, syscalls) or measured performance work, and isolate it behind a safe API.',
],
code=r'''package main

import (
    "fmt"
    "math"
    "unsafe"
)

type header struct {
    Kind  uint8
    Flags uint8
    Size  uint32
}

func main() {
    f := 1.0
    bits := *(*uint64)(unsafe.Pointer(&f))
    fmt.Printf("%#x %v\n", bits, bits == math.Float64bits(f))
    h := header{Kind: 1, Flags: 2, Size: 512}
    size := (*uint32)(unsafe.Add(unsafe.Pointer(&h), unsafe.Offsetof(h.Size)))
    *size = 1024
    fmt.Println(h.Size, unsafe.Offsetof(h.Size))
}
''',
expectedStdout='0x3ff0000000000000 true\n1024 4\n',
challenge='Read the second element of an [4]int32 array through unsafe.Add on a pointer to its first element, and print it.',
solution=r'''package main

import (
    "fmt"
    "unsafe"
)

func main() {
    a := [4]int32{10, 20, 30, 40}
    second := *(*int32)(unsafe.Add(unsafe.Pointer(&a[0]), unsafe.Sizeof(a[0])))
    fmt.Println(second)
}
''',
solutionStdout='20\n',
question='Why is storing uintptr(unsafe.Pointer(p)) in a variable and converting it back later invalid?',
correct='The GC does not see a uintptr as a reference, so the object may be freed or moved',
wrong=['uintptr is only 32 bits', 'The conversion is a compile error'],
reasoning='Only unsafe.Pointer values keep objects alive. A stored integer address can dangle, so conversions must stay within one expression.',
sourceURL='https://pkg.go.dev/unsafe#Pointer'),

dict(key='unsafe-slice-string', stage=STAGE, title='unsafe.Slice, unsafe.String and zero-copy views',
body=[
'unsafe.Slice(ptr, len) builds a slice over existing memory, and unsafe.String(ptr, len) builds a string. unsafe.SliceData and unsafe.StringData return the pointer to the first element. Together they convert between []byte and string without copying.',
'A zero-copy string made from a []byte must never see the bytes change afterwards: strings are immutable, and the compiler and runtime rely on that (for example, map keys and interning). Converting a string to a []byte with unsafe and writing to it is undefined behaviour and may crash on read-only memory.',
'Most programs never need this. The compiler already avoids copies for common cases (map lookups, comparisons, range over []byte(s)), and strings.Builder hands its buffer to a string without a copy. Reserve unsafe conversions for profiled hot paths.',
],
code=r'''package main

import (
    "fmt"
    "unsafe"
)

func bytesToString(b []byte) string {
    if len(b) == 0 {
        return ""
    }
    return unsafe.String(&b[0], len(b))
}

func main() {
    buf := []byte("zero copy")
    s := bytesToString(buf)
    fmt.Println(s, unsafe.StringData(s) == &buf[0])
    nums := [5]int{1, 2, 3, 4, 5}
    view := unsafe.Slice(&nums[1], 3)
    view[0] = 20
    fmt.Println(view, nums, cap(view))
}
''',
expectedStdout='zero copy true\n[20 3 4] [1 20 3 4 5] 3\n',
challenge='Write stringToBytes(s string) []byte using unsafe.Slice and unsafe.StringData, use it only to read, and print the sum of the bytes of "abc".',
solution=r'''package main

import (
    "fmt"
    "unsafe"
)

// stringToBytes returns a read-only view; writing to it is undefined behaviour.
func stringToBytes(s string) []byte {
    return unsafe.Slice(unsafe.StringData(s), len(s))
}

func main() {
    sum := 0
    for _, b := range stringToBytes("abc") {
        sum += int(b)
    }
    fmt.Println(sum)
}
''',
solutionStdout='294\n',
question='What must stay true after creating a string with unsafe.String over a []byte?',
correct='The bytes must never be modified while the string is in use',
wrong=['The slice must be freed immediately', 'The string must be shorter than 64 bytes'],
reasoning='Go assumes strings are immutable. Mutating the shared bytes silently changes a "constant" string and breaks that assumption.',
sourceURL='https://pkg.go.dev/unsafe#String'),

dict(key='memory-layout', stage=STAGE, title='Struct layout, alignment and padding',
body=[
'Each type has a size (unsafe.Sizeof) and an alignment (unsafe.Alignof). The compiler inserts padding so every field starts at a multiple of its alignment, and pads the end so arrays of the struct stay aligned. On 64-bit platforms int64, pointers and float64 align to 8 bytes.',
'Field order changes size: {a bool; b int64; c bool} takes 24 bytes, while {b int64; a bool; c bool} takes 16. In large slices of structs, ordering fields from largest to smallest alignment saves memory and cache space. The fieldalignment analyzer (in golang.org/x/tools) reports such savings.',
'64-bit atomic operations need 8-byte alignment; on 32-bit platforms a plain int64 field may not be aligned, which is one reason the typed atomic.Int64 exists: it guarantees alignment. A zero-size field at the end of a struct also gets padding so a pointer to it never points past the object.',
],
code=r'''package main

import (
    "fmt"
    "unsafe"
)

type loose struct {
    a bool
    b int64
    c bool
}

type tight struct {
    b int64
    a bool
    c bool
}

func main() {
    fmt.Println(unsafe.Sizeof(loose{}), unsafe.Sizeof(tight{}))
    var l loose
    fmt.Println(unsafe.Offsetof(l.a), unsafe.Offsetof(l.b), unsafe.Offsetof(l.c))
    fmt.Println(unsafe.Alignof(l.b), unsafe.Sizeof(""), unsafe.Sizeof([]int(nil)), unsafe.Sizeof(any(nil)))
}
''',
expectedStdout='24 16\n0 8 16\n8 16 24 16\n',
challenge='Reorder the fields of struct{ a byte; b int32; c byte; d int64; e byte } to minimise its size; print the original and reordered sizes.',
solution=r'''package main

import (
    "fmt"
    "unsafe"
)

type before struct {
    a byte
    b int32
    c byte
    d int64
    e byte
}

type after struct {
    d int64
    b int32
    a byte
    c byte
    e byte
}

func main() {
    fmt.Println(unsafe.Sizeof(before{}), unsafe.Sizeof(after{}))
}
''',
solutionStdout='32 16\n',
question='Why is struct{ a bool; b int64; c bool } 24 bytes on 64-bit platforms?',
correct='Padding aligns b to 8 bytes and rounds the total up to a multiple of 8',
wrong=['bool takes 8 bytes', 'Go adds a hidden 8-byte header to structs'],
reasoning='a takes 1 byte plus 7 padding, b 8, c 1 plus 7 trailing padding: 24 in total.',
sourceURL='https://go.dev/ref/spec#Size_and_alignment_guarantees'),

dict(key='cgo-basics', stage=STAGE, title='Calling C with cgo',
body=[
'A Go file that imports "C" is processed by cgo: the comment directly above the import is C source (preamble), and C.name refers to C functions, types and variables. C.CString copies a Go string into C memory that you must free with C.free; C.GoString copies back.',
'cgo calls cost more than Go calls (tens of nanoseconds), and C code is invisible to the race detector and GC. The pointer-passing rules forbid C from keeping Go pointers after a call returns; runtime.Pinner (Go 1.21) pins Go memory when C must hold a pointer temporarily.',
'cgo needs a C toolchain and disables simple cross-compilation; CGO_ENABLED=0 builds pure-Go binaries and makes import "C" files fail to build. Prefer pure-Go libraries unless you need an existing C library.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/cmath\n\ngo 1.27\n'),
f('main.go', r'''package main

/*
#include <stdlib.h>
#include <string.h>

static int add(int a, int b) { return a + b; }
static size_t length(const char *s) { return strlen(s); }
*/
import "C"

import (
    "fmt"
    "unsafe"
)

func main() {
    fmt.Println(C.add(40, 2))
    cs := C.CString("hello cgo")
    defer C.free(unsafe.Pointer(cs))
    fmt.Println(C.length(cs))
}
'''),
],
projectSolutionFiles=[f('main.go', r'''package main

/*
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

static int add(int a, int b) { return a + b; }
static size_t length(const char *s) { return strlen(s); }
static void upper(char *s) { for (; *s; s++) *s = (char)toupper((unsigned char)*s); }
*/
import "C"

import (
    "fmt"
    "unsafe"
)

func main() {
    fmt.Println(C.add(40, 2))
    cs := C.CString("hello cgo")
    defer C.free(unsafe.Pointer(cs))
    fmt.Println(C.length(cs))
    C.upper(cs)
    fmt.Println(C.GoString(cs))
}
''')],
projectInstructions='Go 1.27 with cgo and a C compiler (Xcode command-line tools on macOS). Run:\ngo run .\nExpected stdout: 42 then 9.\nCGO_ENABLED=0 go build fails because main.go imports "C".\nPractice: add a C function that upper-cases the string in place and print the result with C.GoString. Replace main.go with the worked answer.',
projectChecks=[
dict(name='cgo call and C string', args=['run', '.'], stdout='42\n9\n'),
dict(name='cgo disabled cannot build import "C"', args=['build', '-o', '/dev/null', '.'], environment=dict(CGO_ENABLED='0'), exit=1, outputContains=['build constraints exclude all Go files']),
dict(name='answer upper-cases in C', args=['run', '.'], useSolution=True, stdout='42\n9\nHELLO CGO\n'),
],
challenge='Add a C function that upper-cases a C string in place, call it on the C copy, and print the result with C.GoString.',
question='Who frees memory returned by C.CString?',
correct='You must, with C.free, because it is allocated by C malloc',
wrong=['The Go garbage collector', 'It is freed automatically when the C call returns'],
reasoning='CString copies into C heap memory that Go\'s GC does not manage. Pair it with defer C.free.',
sourceURL='https://pkg.go.dev/cmd/cgo',
additionalReadings=[dict(title='cgo pointer passing rules', url='https://pkg.go.dev/cmd/cgo#hdr-Passing_pointers', section='Passing pointers')]),
]

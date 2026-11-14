STAGE = '01 · Start from zero'
TOUR = 'https://go.dev/tour/'

LESSONS = [
dict(key='first-program', stage=STAGE, title='Your first Go program and the go command',
body=[
'A Go program is a set of packages compiled into one executable. Execution starts in package main at func main(); when main returns the process exits, even if other work is still running. The go command is the single front door: go run compiles to a temporary binary and runs it, go build leaves a binary behind, and go vet looks for suspicious code that still compiles.',
'Every source file begins with a package clause, then imports, then declarations. Imports name packages by path, so "fmt" is the formatted-I/O package from the standard library. Exported names start with an upper-case letter, which is why you call fmt.Println and not fmt.println.',
'Go compiles quickly and refuses to build code that imports a package it does not use or declares a local variable it never reads. These rules feel strict at first; they keep programs free of dead dependencies and half-finished edits. Treat a compiler error as precise feedback: it names the file, line and column.',
],
code=r'''package main

import "fmt"

func main() {
    fmt.Println("Go:", 6*7)
}
''',
expectedStdout='Go: 42\n',
challenge='Print two lines: the word Go, then the result of 8 * 8.',
solution=r'''package main

import "fmt"

func main() {
    fmt.Println("Go")
    fmt.Println(8 * 8)
}
''',
solutionStdout='Go\n64\n',
question='What does fmt.Println put between its operands?',
correct='A single space, followed by a newline at the end',
wrong=['Nothing; operands are concatenated', 'A comma and a space'],
reasoning='Println always separates operands with spaces and appends a newline. That is why "Go:" and 42 appear as "Go: 42".',
rejections=[dict(source='package main\n\nimport (\n\t"fmt"\n\t"os"\n)\n\nfunc main() {\n\tfmt.Println("hi")\n}\n', diagnostic='"os" imported and not used'),
            dict(source='package main\n\nfunc main() {\n\tx := 1\n}\n', diagnostic='declared and not used: x')],
sourceURL='https://go.dev/doc/tutorial/getting-started'),

dict(key='modules-and-run', stage=STAGE, title='Modules, go.mod, and building a binary',
body=[
'A module is a tree of packages with a go.mod file at its root. go mod init example.com/hello writes a go.mod naming the module path and a go directive such as go 1.27. The go line is the language version the module is written for. It enables features of that release and tells newer toolchains which semantics to use.',
'Inside a module, go run . builds the package in the current directory and runs it; go build produces an executable named after the directory; go install places it in GOBIN. A toolchain line in go.mod, or the GOTOOLCHAIN environment variable, can ask the go command to download and use a specific release, which is how this guide pins go1.27.2.',
'Programs read their command-line arguments through os.Args, where os.Args[0] is the program name. Exit codes come from os.Exit; returning from main exits with status 0. Deferred functions do not run when os.Exit is called, so do cleanup before exiting.',
],
code=r'''package main

import (
    "fmt"
    "os"
)

func main() {
    fmt.Println("arguments:", len(os.Args)-1)
    fmt.Println("program name present:", os.Args[0] != "")
}
''',
expectedStdout='arguments: 0\nprogram name present: true\n',
challenge='Print the number of arguments, then print "none" if there are no arguments and "some" otherwise.',
solution=r'''package main

import (
    "fmt"
    "os"
)

func main() {
    n := len(os.Args) - 1
    fmt.Println(n)
    if n == 0 {
        fmt.Println("none")
    } else {
        fmt.Println("some")
    }
}
''',
solutionStdout='0\nnone\n',
question='What does the go directive in go.mod control?',
correct='The Go language version and semantics the module is written for',
wrong=['The exact compiler binary that must be installed', 'The version of every dependency'],
reasoning='go 1.27 selects language features and defaults (such as per-iteration loop variables from 1.22). Dependencies are recorded on require lines, and the toolchain line or GOTOOLCHAIN selects a compiler.',
sourceURL='https://go.dev/doc/modules/gomod-ref',
additionalReadings=[dict(title='Go toolchains', url='https://go.dev/doc/toolchain', section='GOTOOLCHAIN and the toolchain line')]),

dict(key='fmt-verbs', stage=STAGE, title='Printing with fmt: Print, Printf and verbs',
body=[
'fmt offers three families: Print/Println/Printf write to standard output, Sprint/Sprintln/Sprintf return a string, and Fprint/Fprintln/Fprintf write to any io.Writer such as os.Stderr. Printf takes a format string whose verbs describe how each argument is shown.',
'Common verbs: %v prints a value in its default format, %+v adds struct field names, %#v prints Go syntax, %T prints the type, %d an integer, %s a string, %q a quoted string, %x hexadecimal, %f a float and %t a boolean. Width and precision sit between % and the verb: %5d pads to five columns and %.2f rounds to two decimal places.',
'Printf does not add a newline; put \\n in the format. go vet checks that verbs match their arguments, so a %d given a string is reported before the program ever runs. Use %% for a literal percent sign.',
],
code=r'''package main

import "fmt"

func main() {
    name, score := "Ada", 93.456
    fmt.Printf("%s scored %.1f%%\n", name, score)
    fmt.Printf("%q has type %T\n", name, name)
    fmt.Printf("[%5d] [%-5d]\n", 42, 42)
}
''',
expectedStdout='Ada scored 93.5%\n"Ada" has type string\n[   42] [42   ]\n',
challenge='Use Sprintf to build the string "07:05" from hours 7 and minutes 5, then print it.',
solution=r'''package main

import "fmt"

func main() {
    clock := fmt.Sprintf("%02d:%02d", 7, 5)
    fmt.Println(clock)
}
''',
solutionStdout='07:05\n',
question='Which verb prints a value together with its Go type name?',
correct='%T prints the type; combine it with %v for the value',
wrong=['%v prints both automatically', '%#v prints only the type'],
reasoning='%T formats the dynamic type of its operand. %#v prints a Go-syntax representation of the value, which often includes the type for composite literals but is not the type name alone.',
rejections=[dict(source='package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Printf("%d\\n", "seven")\n}\n', args=['vet', '.'], diagnostic='wrong type string')],
sourceURL='https://pkg.go.dev/fmt'),

dict(key='gofmt-and-style', stage=STAGE, title='gofmt, comments, and the shape of Go source',
body=[
'gofmt prints Go source in one canonical layout: tabs for indentation, aligned comments and a fixed brace style. Teams do not argue about formatting because the tool decides. Run go fmt ./... or let your editor format on save; every example in this guide is checked to be unchanged by gofmt.',
'The opening brace of a block must be on the same line as its statement. Go inserts semicolons automatically at the end of a line that ends with an identifier, literal, closing bracket or certain keywords, so moving a brace onto the next line changes the meaning and fails to compile.',
'Line comments start with //; block comments use /* */. A comment directly above a declaration is its doc comment and should begin with the declared name, for example // Area returns.... go doc and pkg.go.dev render those comments as documentation.',
],
code=r'''package main

import "fmt"

// Area returns the area of a w by h rectangle.
func Area(w, h int) int {
    return w * h
}

func main() {
    fmt.Println(Area(3, 4))
}
''',
expectedStdout='12\n',
challenge='Add a documented function Perimeter(w, h int) int and print the perimeter of a 3 by 4 rectangle.',
solution=r'''package main

import "fmt"

// Perimeter returns the perimeter of a w by h rectangle.
func Perimeter(w, h int) int {
    return 2 * (w + h)
}

func main() {
    fmt.Println(Perimeter(3, 4))
}
''',
solutionStdout='14\n',
question='Why does putting a function\'s opening brace on the next line fail to compile?',
correct='Automatic semicolon insertion ends the declaration at the line break',
wrong=['gofmt rejects the file before compilation', 'Go forbids blank lines inside declarations'],
reasoning='The lexer inserts a semicolon after the closing parenthesis, so the brace starts a separate statement. gofmt is a formatter, not part of the compiler.',
rejections=[dict(source='package main\n\nfunc main()\n{\n}\n', diagnostic='unexpected semicolon or newline before {')],
sourceURL='https://go.dev/doc/effective_go#formatting',
additionalReadings=[dict(title='Go doc comments', url='https://go.dev/doc/comment', section='Doc comment syntax')]),

dict(key='go-doc-and-packages', stage=STAGE, title='Reading the standard library with go doc',
body=[
'The standard library is documented in the source and readable offline: go doc strings.Cut prints one function, go doc -all strings prints a whole package, and go doc -src shows the implementation. Go 1.27 adds go doc package@version for modules and go doc -ex for running examples.',
'Learn a package by its types and the verbs on them. For strings, start with Contains, Index, Cut, Fields, Split, Join, Repeat, ToUpper and the strings.Builder type. Most functions accept and return plain values, so you can predict them from their signature.',
'strings.Cut(s, sep) splits around the first separator and reports whether it was found; Go 1.27 adds strings.CutLast for the last separator. Prefer Cut over Index plus slicing because the found flag makes the not-found case explicit.',
],
code=r'''package main

import (
    "fmt"
    "strings"
)

func main() {
    key, value, found := strings.Cut("lang=go", "=")
    fmt.Println(key, value, found)
    fmt.Println(strings.Fields("  a  b c "))
    fmt.Println(strings.Repeat("ab", 3))
}
''',
expectedStdout='lang go true\n[a b c]\nababab\n',
challenge='Split "dir/sub/file.go" around its last "/" with strings.CutLast and print the directory and file name.',
solution=r'''package main

import (
    "fmt"
    "strings"
)

func main() {
    dir, file, ok := strings.CutLast("dir/sub/file.go", "/")
    fmt.Println(dir, file, ok)
}
''',
solutionStdout='dir/sub file.go true\n',
question='What does strings.Cut return when the separator is missing?',
correct='The whole input, an empty string, and false',
wrong=['Two empty strings and false', 'It panics with an index error'],
reasoning='Cut returns before=s, after="" and found=false, so code can test found instead of comparing indices against -1.',
sourceURL='https://pkg.go.dev/strings#Cut',
additionalReadings=[dict(title='Go 1.27 release notes', url='https://go.dev/doc/go1.27', section='strings.CutLast and go doc changes')]),

dict(key='reading-input', stage=STAGE, title='Reading standard input line by line',
body=[
'Interactive and pipeline programs read standard input. bufio.Scanner wraps os.Stdin and splits it into lines by default: call Scan in a loop, read the current line with Text, and check Err after the loop. Scan returns false at end of input or on an error.',
'Scanner has a maximum token size (64 KiB by default). A longer line makes Scan stop with bufio.ErrTooLong, so always check Err; use Scanner.Buffer to raise the limit or bufio.Reader for unbounded lines.',
'Write results to os.Stdout and diagnostics to os.Stderr so pipelines can separate them. fmt.Fprintln(os.Stderr, ...) writes a diagnostic without mixing it into the data stream.',
],
code=r'''package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    lines := 0
    for scanner.Scan() {
        lines++
        fmt.Println(strings.ToUpper(scanner.Text()))
    }
    if err := scanner.Err(); err != nil {
        fmt.Fprintln(os.Stderr, "read:", err)
        os.Exit(1)
    }
    fmt.Println("lines:", lines)
}
''',
expectedStdout='HELLO\nGO\nlines: 2\n',
stdin='hello\ngo\n',
challenge='Read lines and print only the non-empty ones, each prefixed with its line number starting at 1.',
solution=r'''package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    for n := 1; scanner.Scan(); n++ {
        if scanner.Text() != "" {
            fmt.Printf("%d: %s\n", n, scanner.Text())
        }
    }
    if err := scanner.Err(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
''',
solutionStdout='1: hello\n2: go\n',
question='Why check scanner.Err() after the Scan loop?',
correct='Scan returns false for both end of input and failures such as a too-long line',
wrong=['Err resets the scanner for the next file', 'Scan panics on errors, and Err recovers it'],
reasoning='A false Scan is ambiguous. Err returns nil at a clean end of input and the error otherwise, for example bufio.ErrTooLong.',
sourceURL='https://pkg.go.dev/bufio#Scanner'),
]

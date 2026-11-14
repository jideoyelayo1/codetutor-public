STAGE = '21 · The specification in depth'
SPEC = 'https://go.dev/ref/spec'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='spec-lexical-elements', stage=STAGE, title='Reading the spec: notation, source text, identifiers and keywords',
spec=['Introduction', 'Notation', 'Source_code_representation', 'Characters', 'Letters_and_digits', 'Lexical_elements', 'Identifiers', 'Keywords'],
body=[
'The Go specification is short enough to read in an evening and is the final authority on what a program means. Its grammar is written in Extended Backus-Naur Form: Production = name "=" Expression ".", with | for alternatives, () for grouping, [] for an optional part and {} for repetition. Reading one production, such as IdentifierList = identifier { "," identifier }, tells you exactly what the parser accepts.',
'Source code is Unicode text encoded in UTF-8, and the compiler does not normalise it: an accented letter written as one code point and as a letter plus combining mark are different identifiers. A byte order mark is ignored only at the very start of a file. The NUL character is not allowed.',
'An identifier is a letter followed by letters and digits, where letter means any Unicode letter or the underscore. So π and _tmp are valid names, while 2x is not. Exported identifiers start with an upper-case letter (Unicode class Lu); names in scripts without case, such as 名前, are therefore never exported.',
'Go has exactly 25 keywords: break, case, chan, const, continue, default, defer, else, fallthrough, for, func, go, goto, if, import, interface, map, package, range, return, select, struct, switch, type, var. Names such as int, len, true, nil, any and error are predeclared identifiers, not keywords, so they can be shadowed, which is legal and usually a mistake.',
],
code=r'''package main

import (
    "fmt"
    "go/scanner"
    "go/token"
    "unicode"
)

func main() {
    π, _tmp, 名前 := 3.14, 1, "go"
    fmt.Println(π, _tmp, 名前)
    fmt.Println(token.IsKeyword("range"), token.IsKeyword("len"), token.IsIdentifier("2x"))
    fmt.Println(token.IsExported("Name"), token.IsExported("名前"), unicode.IsUpper('N'))
    src := []byte("x := 0x1F // hex")
    fset := token.NewFileSet()
    var s scanner.Scanner
    s.Init(fset.AddFile("", fset.Base(), len(src)), src, nil, scanner.ScanComments)
    for {
        _, tok, lit := s.Scan()
        if tok == token.EOF {
            break
        }
        fmt.Printf("%s %q\n", tok, lit)
    }
}
''',
expectedStdout='3.14 1 go\ntrue false false\ntrue false true\nIDENT "x"\n:= ""\nINT "0x1F"\nCOMMENT "// hex"\n; "\\n"\n',
challenge='Count how many of the 25 Go keywords appear in the source text "for i := range xs { if i > 0 { break } }" by scanning it with go/scanner and token.Token.IsKeyword.',
solution=r'''package main

import (
    "fmt"
    "go/scanner"
    "go/token"
)

func main() {
    src := []byte("for i := range xs { if i > 0 { break } }")
    fset := token.NewFileSet()
    var s scanner.Scanner
    s.Init(fset.AddFile("", fset.Base(), len(src)), src, nil, 0)
    keywords := 0
    for {
        _, tok, _ := s.Scan()
        if tok == token.EOF {
            break
        }
        if tok.IsKeyword() {
            keywords++
        }
    }
    fmt.Println(keywords)
}
''',
solutionStdout='4\n',
question='Is len a keyword in Go?',
correct='No; it is a predeclared identifier that can be shadowed',
wrong=['Yes, one of the 25 keywords', 'Yes, but only inside functions'],
reasoning='Built-in functions, types and constants live in the universe block as predeclared identifiers. Only the 25 keywords are reserved.',
sourceURL=SPEC+'#Lexical_elements'),

dict(key='spec-literals', stage=STAGE, title='Integer, floating-point, imaginary and rune literals in full',
spec=['Integer_literals', 'Floating-point_literals', 'Imaginary_literals', 'Complex_numbers', 'Go_1.13'],
body=[
'Integer literals come in four bases: decimal 255, binary 0b1111_1111, octal 0o377 (or the legacy 0377), and hexadecimal 0xFF. Underscores may separate digits for readability, but only between digits or after the base prefix: 1_000_000 is valid, while _100 is an identifier and 100_ is an error. The 0b, 0o and underscore forms need go 1.13 or later.',
'Floating-point literals are decimal (1.5, .5, 1e9, 6.02e23) or hexadecimal with a mandatory p exponent: 0x1p-2 is 0.25. An imaginary literal is an integer or float followed by i, such as 2i or 1.5e3i, and denotes a complex constant.',
'The built-ins complex, real and imag build and take apart complex values; complex128 holds two float64s. math/cmplx provides Abs, Sqrt, Exp, Pow and friends. Rune literals can use escapes: \'\\n\', \'\\x41\', \'\\u00e9\', \'\\U0001F600\' and octal \'\\101\'.',
],
code=r'''package main

import (
    "fmt"
    "math/cmplx"
)

func main() {
    fmt.Println(255, 0b1111_1111, 0o377, 0377, 0xFF, 1_000_000)
    fmt.Println(.5, 1e3, 0x1p-2, 0x1.8p1)
    z := complex(3, 4)
    fmt.Println(z, real(z), imag(z), cmplx.Abs(z))
    fmt.Println(2i*2i, cmplx.Sqrt(-1))
    fmt.Println('\x41', '\101', '\u00e9' == 'é', string('\U0001F600'))
}
''',
expectedStdout='255 255 255 255 255 1000000\n0.5 1000 0.25 3\n(3+4i) 3 4 5\n(-4+0i) (0+1i)\n65 65 true 😀\n',
challenge='Use cmplx.Exp to compute e^(iπ) + 1 and print whether its absolute value is below 1e-12 (Euler\'s identity).',
solution=r'''package main

import (
    "fmt"
    "math"
    "math/cmplx"
)

func main() {
    v := cmplx.Exp(complex(0, math.Pi)) + 1
    fmt.Println(cmplx.Abs(v) < 1e-12)
}
''',
solutionStdout='true\n',
question='What value does the literal 0x1p-2 denote?',
correct='0.25, because p gives a power-of-two exponent',
wrong=['The hex integer 0x12', 'It is invalid; hex floats are not allowed'],
reasoning='Hex floating-point literals scale the mantissa by 2 to the power after p: 1 × 2⁻² = 0.25.',
rejections=[dict(source='package main\n\nfunc main() {\n\t_ = 100_\n}\n', diagnostic="'_' must separate successive digits")],
sourceURL=SPEC+'#Integer_literals',
additionalReadings=[dict(title='math/cmplx', url='https://pkg.go.dev/math/cmplx', section='Complex functions')]),

dict(key='spec-type-identity', stage=STAGE, title='Types, type identity, assignability and representability',
spec=['Types', 'Boolean_types', 'Properties_of_types_and_values', 'Representation_of_values', 'Type_identity', 'Assignability', 'Representability'],
body=[
'Every named type is distinct from every other type, while two type literals are identical when they have the same structure: []int and []int are identical, and struct{ X int } in two packages is identical too, unless one of its fields is unexported. That is why the defined types Celsius and Fahrenheit never mix, but two anonymous struct types with the same fields do.',
'A value x is assignable to a variable of type T when the types are identical, when they share an underlying type and at least one is not a named type, when T is an interface that x implements, for bidirectional channels assigned to a directional channel of the same element type, when x is the predeclared nil and T is a pointer, function, slice, map, channel or interface, or when x is an untyped constant representable as T.',
'Representable means the constant fits: 1.0 is representable as an int, while 1.5 or 300 as a byte is not. bool is its own type: there is no implicit conversion between booleans and integers, which removes a whole class of C bugs.',
],
code=r'''package main

import "fmt"

type Celsius float64
type IntSlice []int

func sum(xs []int) int {
    t := 0
    for _, x := range xs {
        t += x
    }
    return t
}

func main() {
    var a struct{ X int } = struct{ X int }{1}
    b := struct{ X int }{2}
    a = b
    fmt.Println(a)
    s := IntSlice{1, 2, 3}
    fmt.Println(sum(s))
    var recvOnly <-chan int = make(chan int)
    fmt.Printf("%T\n", recvOnly)
    const whole = 3.0
    var n int = whole
    var c Celsius = 21
    fmt.Println(n, c, true && !false)
}
''',
expectedStdout='{2}\n6\n<-chan int\n3 21 true\n',
challenge='Predict, then confirm by compiling, which of these is assignable to []int: a value of type IntSlice, a value of a type Ints that is defined as IntSlice, and nil. Print a line for each that compiles.',
solution=r'''package main

import "fmt"

type IntSlice []int

func main() {
    var target []int
    target = IntSlice{1}
    fmt.Println("IntSlice ok", target)
    target = nil
    fmt.Println("nil ok", target == nil)
}
''',
solutionStdout='IntSlice ok [1]\nnil ok true\n',
question='Why can an IntSlice value be passed to func sum(xs []int)?',
correct='They share an underlying type and []int is not a named type',
wrong=['Named slice types convert automatically to any slice type', 'Because IntSlice has no methods'],
reasoning='Assignability allows identical underlying types when at least one side is unnamed. Two different named types, such as Celsius and Fahrenheit, need a conversion.',
rejections=[dict(source='package main\n\nfunc main() {\n\tvar b byte = 300\n\t_ = b\n}\n', diagnostic='cannot use 300 (untyped int constant) as byte value in variable declaration (overflows)'),
            dict(source='package main\n\nfunc main() {\n\tvar n int = true\n\t_ = n\n}\n', diagnostic='cannot use true (untyped bool constant) as int value in variable declaration')],
sourceURL=SPEC+'#Assignability'),

dict(key='spec-scope-blocks', stage=STAGE, title='Blocks, scope, predeclared identifiers and uniqueness',
spec=['Blocks', 'Declarations_and_scope', 'Predeclared_identifiers', 'Uniqueness_of_identifiers', 'Qualified_identifiers'],
body=[
'Go has nested blocks: the universe block (predeclared identifiers), the package block (all files of the package), the file block (imports), and the blocks of functions, statements and clauses. Each if, for and switch is its own implicit block, and each case clause is another. A declaration is visible from its point of declaration to the end of the innermost enclosing block, except that package-level names are visible throughout the package, so order there does not matter.',
'Shadowing an outer name in an inner block is legal. The predeclared identifiers include the types bool, byte, comparable, complex64/128, error, float32/64, int and its sizes, rune, string, uint and its sizes, uintptr and any; the constants true, false and iota; the zero value nil; and the functions append, cap, clear, close, complex, copy, delete, imag, len, make, max, min, new, panic, print, println, real and recover.',
'Two identifiers are different if they are spelled differently, or if they appear in different packages and are not exported: the unexported name count in package a is unrelated to count in package b. A qualified identifier, pkg.Name, reaches an exported name through an import.',
],
code=r'''package main

import "fmt"

func later() string { return early }

var early = "package scope ignores declaration order"

func main() {
    fmt.Println(later())
    x := "outer"
    if x := "if block"; len(x) > 0 {
        fmt.Println(x)
    }
    switch x := 1; x {
    case 1:
        x := "case block"
        fmt.Println(x)
    }
    fmt.Println(x)
    len := func(s string) int { return 42 }
    fmt.Println(len("shadowed"))
}
''',
expectedStdout='package scope ignores declaration order\nif block\ncase block\nouter\n42\n',
challenge='Show that the predeclared nil can be shadowed: declare nil := 0 inside a block and print nil+1, then show the real nil still works outside by comparing a nil slice.',
solution=r'''package main

import "fmt"

func main() {
    {
        nil := 0
        fmt.Println(nil + 1)
    }
    var s []int
    fmt.Println(s == nil)
}
''',
solutionStdout='1\ntrue\n',
question='Why can later() use early even though early is declared after it?',
correct='Package-level identifiers are scoped to the whole package block',
wrong=['The compiler reorders functions alphabetically', 'Only variables declared with var can be used before declaration'],
reasoning='Order matters inside function bodies, but at package level every name is visible throughout; initialisation order is then computed from dependencies.',
rejections=[dict(source='package main\n\nfunc main() {\n\tprintln(y)\n\ty := 1\n\t_ = y\n}\n', diagnostic='undefined: y')],
sourceURL=SPEC+'#Declarations_and_scope'),

dict(key='spec-method-values', stage=STAGE, title='Operands, primary expressions, method values and method expressions',
spec=['Expressions', 'Operands', 'Primary_expressions', 'Method_expressions', 'Method_values'],
body=[
'An expression computes a value from operands (literals, identifiers, qualified identifiers and parenthesised expressions) using primary expressions such as selectors x.f, index expressions a[i], slices a[i:j], type assertions x.(T) and calls f(x).',
'A method value t.M is a function value bound to the receiver: f := counter.Inc saves both the method and the receiver, which is evaluated and copied at that moment. For a value receiver, later changes to counter do not affect f; for a pointer receiver bound through &counter, they do.',
'A method expression T.M (or (*T).M) is an ordinary function whose first parameter is the receiver: Point.Dist has type func(Point, Point) float64. Method expressions turn methods into plain functions for tables and higher-order code.',
],
code=r'''package main

import (
    "fmt"
    "strings"
)

type Counter struct{ n int }

func (c Counter) Get() int { return c.n }
func (c *Counter) Inc()    { c.n++ }

func main() {
    c := Counter{n: 1}
    get := c.Get
    inc := c.Inc
    inc()
    inc()
    fmt.Println(c.n, get())
    getFn := Counter.Get
    incFn := (*Counter).Inc
    incFn(&c)
    fmt.Println(getFn(c))
    upper := strings.ToUpper
    fmt.Printf("%T %s\n", getFn, upper("method values"))
}
''',
expectedStdout='3 1\n4\nfunc(main.Counter) int METHOD VALUES\n',
challenge='Build a map[string]func(*Counter) from the method expressions (*Counter).Inc and a new (*Counter).Reset, apply "inc", "inc", "reset", "inc" to one counter, and print n.',
solution=r'''package main

import "fmt"

type Counter struct{ n int }

func (c *Counter) Inc()   { c.n++ }
func (c *Counter) Reset() { c.n = 0 }

func main() {
    ops := map[string]func(*Counter){"inc": (*Counter).Inc, "reset": (*Counter).Reset}
    var c Counter
    for _, name := range []string{"inc", "inc", "reset", "inc"} {
        ops[name](&c)
    }
    fmt.Println(c.n)
}
''',
solutionStdout='1\n',
question='Why does get() still return 1 after two inc() calls?',
correct='The method value c.Get copied the value receiver when it was created',
wrong=['Get caches its first result', 'inc changed a different counter'],
reasoning='inc was bound to &c, so it changes c. get was bound to a copy of c taken before the increments.',
sourceURL=SPEC+'#Method_values'),

dict(key='spec-slice-to-array', stage=STAGE, title='Converting slices to arrays and array pointers',
spec=['Conversions_from_slice_to_array_or_array_pointer', 'Go_1.17', 'Go_1.20'],
body=[
'Go 1.17 allowed converting a slice to an array pointer: (*[4]byte)(s) returns a pointer that shares s\'s backing array. Go 1.20 added direct conversion to an array value: [4]byte(s) copies the first four elements.',
'Both conversions panic at run time if len(s) is smaller than the array length. A nil slice converts to a nil array pointer, and to a zero-length array value without panicking.',
'These conversions are handy for fixed-size keys, hashes and headers: parsing a 16-byte UUID from a slice, or using the first bytes of a buffer as a map key.',
],
code=r'''package main

import "fmt"

func main() {
    s := []byte{1, 2, 3, 4, 5}
    p := (*[4]byte)(s)
    p[0] = 9
    fmt.Println(s[0], len(p))
    a := [4]byte(s)
    a[1] = 0
    fmt.Println(s[1], a)
    var empty []int
    fmt.Println((*[0]int)(empty) == nil, [0]int(empty))
    defer func() { fmt.Println("recovered:", recover()) }()
    _ = [8]byte(s)
}
''',
expectedStdout='9 4\n2 [9 0 3 4]\ntrue []\nrecovered: runtime error: cannot convert slice with length 5 to array or pointer to array with length 8\n',
challenge='Use the first two bytes of each of the slices []byte("go"), []byte("gopher") and []byte("rust") as [2]byte map keys and count how many distinct prefixes there are.',
solution=r'''package main

import "fmt"

func main() {
    seen := map[[2]byte]bool{}
    for _, w := range [][]byte{[]byte("go"), []byte("gopher"), []byte("rust")} {
        seen[[2]byte(w)] = true
    }
    fmt.Println(len(seen))
}
''',
solutionStdout='2\n',
question='What is the difference between (*[4]byte)(s) and [4]byte(s)?',
correct='The pointer shares s\'s memory; the array value is a copy',
wrong=['They are identical spellings', 'The pointer form copies, the array form shares'],
reasoning='Array pointers alias the backing array, so writes are visible through s. Array values are independent copies.',
sourceURL=SPEC+'#Conversions_from_slice_to_array_or_array_pointer'),

dict(key='spec-evaluation-order', stage=STAGE, title='Order of evaluation and statements',
spec=['Order_of_evaluation', 'Statements', 'Expression_statements', 'Empty_statements'],
body=[
'Within an expression, function calls, method calls, receive operations and binary logical operations are evaluated left to right. Other details are unspecified: in a := f() + g() the calls happen left to right, but in y[f()], ok = g(h(), i()+x[j()], <-c), k() the evaluation of the index expressions relative to x is not pinned down. Do not write code whose meaning depends on such details.',
'Assignment happens in two phases: first all index expressions and pointer indirections on the left and all expressions on the right are evaluated in the usual order, then the assignments are carried out left to right. That is why a, b = b, a swaps, and why i, x[i] = 1, 2 sets x[0] (with the old i) rather than x[1].',
'Function calls, method calls and receive operations can appear as statements (expression statements); most other expressions cannot, so len(s) on its own line is an error. An empty statement does nothing; it appears, for example, as the missing post statement in for i := 0; i < n; {.',
],
code=r'''package main

import "fmt"

func trace(name string, v int) int {
    fmt.Print(name, " ")
    return v
}

func main() {
    sum := trace("a", 1) + trace("b", 2)*trace("c", 3)
    fmt.Println("=", sum)
    i := 0
    x := []int{0, 0}
    i, x[i] = 1, 2
    fmt.Println(i, x)
    a, b := 1, 2
    a, b = b, a
    fmt.Println(a, b)
    for n := 0; n < 3; {
        n++
        fmt.Print(n)
    }
    fmt.Println()
}
''',
expectedStdout='a b c = 7\n1 [2 0]\n2 1\n123\n',
challenge='Predict and print the result of xs[trace(0)], xs[trace(1)] = trace(10), trace(20) where trace prints its argument; show the order of the four calls and the final slice.',
solution=r'''package main

import "fmt"

func trace(v int) int {
    fmt.Print(v, " ")
    return v
}

func main() {
    xs := make([]int, 2)
    xs[trace(0)], xs[trace(1)] = trace(10), trace(20)
    fmt.Println(xs)
}
''',
solutionStdout='0 1 10 20 [10 20]\n',
question='After i := 0; x := []int{0, 0}; i, x[i] = 1, 2, which element of x is 2?',
correct='x[0], because index expressions are evaluated before any assignment',
wrong=['x[1], because i is assigned first', 'Neither; the statement does not compile'],
reasoning='Phase one evaluates x[i] with i == 0; phase two assigns i = 1 and x[0] = 2.',
rejections=[dict(source='package main\n\nfunc main() {\n\ts := []int{1}\n\tlen(s)\n}\n', diagnostic='len(s) (value of type int) is not used')],
sourceURL=SPEC+'#Order_of_evaluation'),

dict(key='spec-terminating-statements', stage=STAGE, title='Terminating statements and missing returns',
spec=['Terminating_statements'],
body=[
'A function with results must end in a terminating statement, and the compiler decides this syntactically, not by data flow. Terminating statements include return and goto, a call to panic, a block ending in a terminating statement, an if with an else where both branches terminate, a for with no condition and no break referring to it, and switch or select statements whose every case (including a default for switch) terminates and that contain no break.',
'So a function ending in for { ... } with no break needs no return, and a switch with an exhaustive-looking set of cases still needs a default or a final return, because the compiler does not know the cases are exhaustive.',
'When the compiler reports "missing return", either add the return or restructure, for example by turning if/else chains into a final return or a panic("unreachable") for truly impossible states.',
],
code=r'''package main

import "fmt"

func sign(n int) string {
    switch {
    case n < 0:
        return "negative"
    case n > 0:
        return "positive"
    default:
        return "zero"
    }
}

func firstEven(xs []int) int {
    for i := 0; ; i++ {
        if xs[i]%2 == 0 {
            return xs[i]
        }
    }
}

func must(ok bool) int {
    if ok {
        return 1
    }
    panic("not ok")
}

func main() {
    fmt.Println(sign(-3), sign(0), firstEven([]int{3, 5, 8}), must(true))
}
''',
expectedStdout='negative zero 8 1\n',
challenge='Write func classify(r rune) string with an if/else-if/else chain (letter, digit, other) that compiles without a trailing return, and print it for \'a\', \'7\' and \'!\'.',
solution=r'''package main

import (
    "fmt"
    "unicode"
)

func classify(r rune) string {
    if unicode.IsLetter(r) {
        return "letter"
    } else if unicode.IsDigit(r) {
        return "digit"
    } else {
        return "other"
    }
}

func main() {
    fmt.Println(classify('a'), classify('7'), classify('!'))
}
''',
solutionStdout='letter digit other\n',
question='Why does a switch without a default, whose cases all return, still cause "missing return"?',
correct='A switch is terminating only with a default case; the compiler does not prove exhaustiveness',
wrong=['Switches can never terminate a function', 'Cases must use fallthrough to terminate'],
reasoning='The rule is syntactic. Without default, control may fall out of the switch, so a return must follow.',
rejections=[dict(source='package main\n\nfunc f(n int) int {\n\tswitch {\n\tcase n < 0:\n\t\treturn -1\n\tcase n >= 0:\n\t\treturn 1\n\t}\n}\n\nfunc main() { _ = f(1) }\n', diagnostic='missing return'),
            dict(source='package main\n\nfunc f() int {\n\tfor {\n\t\tbreak\n\t}\n}\n\nfunc main() { _ = f() }\n', diagnostic='missing return')],
sourceURL=SPEC+'#Terminating_statements'),

dict(key='spec-bootstrapping-example', stage=STAGE, title='Bootstrapping built-ins, the spec\'s example package and system considerations',
spec=['Bootstrapping', 'An_example_package', 'Program_initialization_and_execution', 'System_considerations'],
body=[
'print and println are bootstrapping built-ins: they write to standard error, their output format is implementation-specific, and they may be removed. They exist for the runtime\'s own debugging. Use fmt in real programs.',
'The specification\'s example package is a concurrent prime sieve: a generator goroutine sends 2, 3, 4, ... on a channel, and each discovered prime adds a filter goroutine that removes its multiples. It demonstrates goroutines, directional channels and pipelines in a dozen lines.',
'System considerations covers package unsafe and the size and alignment guarantees: for example, a struct or array of size zero may share an address with another variable, and unsafe.Sizeof of a value of a given type is the same on every call. Program execution begins by initialising the main package and its imports, then calls main.main; when it returns, the program exits without waiting for other goroutines.',
],
code=r'''package main

import "fmt"

func generate(ch chan<- int) {
    for i := 2; ; i++ {
        ch <- i
    }
}

func filter(in <-chan int, out chan<- int, prime int) {
    for {
        i := <-in
        if i%prime != 0 {
            out <- i
        }
    }
}

func main() {
    ch := make(chan int)
    go generate(ch)
    for range 10 {
        prime := <-ch
        fmt.Print(prime, " ")
        ch1 := make(chan int)
        go filter(ch, ch1, prime)
        ch = ch1
    }
    fmt.Println()
    println("println writes to standard error")
}
''',
expectedStdout='2 3 5 7 11 13 17 19 23 29 \n',
challenge='Change the sieve to stop cleanly: pass a done channel to generate and filter, close it after collecting the primes below 50, and print them.',
solution=r'''package main

import "fmt"

func generate(done <-chan struct{}, ch chan<- int) {
    for i := 2; ; i++ {
        select {
        case ch <- i:
        case <-done:
            return
        }
    }
}

func filter(done <-chan struct{}, in <-chan int, out chan<- int, prime int) {
    for {
        select {
        case i := <-in:
            if i%prime != 0 {
                select {
                case out <- i:
                case <-done:
                    return
                }
            }
        case <-done:
            return
        }
    }
}

func main() {
    done := make(chan struct{})
    defer close(done)
    ch := make(chan int)
    go generate(done, ch)
    for {
        prime := <-ch
        if prime >= 50 {
            break
        }
        fmt.Print(prime, " ")
        next := make(chan int)
        go filter(done, ch, next, prime)
        ch = next
    }
    fmt.Println()
}
''',
solutionStdout='2 3 5 7 11 13 17 19 23 29 31 37 41 43 47 \n',
question='Where does println write?',
correct='To standard error, in an implementation-defined format',
wrong=['To standard output, like fmt.Println', 'Nowhere unless built with -debug'],
reasoning='The bootstrapping built-ins are for runtime development; fmt.Println is the stable, documented way to print.',
sourceURL=SPEC+'#An_example_package'),

dict(key='spec-language-versions', stage=STAGE, title='The language-version appendix: features gated by the go line',
spec=['Appendix', 'Go_1.9', 'Go_1.14', 'Go_1.18', 'Go_1.21', 'Go_1.24'],
body=[
'The appendix lists what changed in each language version, so the compiler can reject newer features in modules that declare an older go line. Go 1.9 added type aliases; 1.13 the 0b/0o/underscore literals and signed shift counts; 1.14 duplicate methods from embedded interfaces; 1.17 slice-to-array-pointer conversion; 1.18 generics; 1.20 slice-to-array conversion and comparable for interfaces; 1.21 min, max, clear and better inference; 1.22 per-iteration loop variables and range over int; 1.23 range over functions; 1.24 generic type aliases; 1.26 new(expr); 1.27 generic methods and promoted-field literal keys.',
'A file can also select a version with a //go:build go1.N constraint, which only ever upgrades within the module\'s range. Library authors declare the oldest go version they support, test with it, and adopt newer features only when they raise it.',
'This project declares go 1.20 and uses min, which arrived in 1.21: the compiler refuses. Raising the go line to 1.21 fixes it.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/versions\n\ngo 1.20\n'),
f('main.go', r'''package main

import "fmt"

func main() {
    fmt.Println(min(3, 1, 2))
}
'''),
],
projectSolutionFiles=[f('go.mod', 'module example.com/versions\n\ngo 1.21\n')],
projectVet=[],  # the base module is intentionally too old; the checks assert the error
projectInstructions='Checked with go1.27.2. The module declares go 1.20 but calls the built-in min, added in Go 1.21. Run:\ngo build ./...\nThe compiler reports that min requires go1.21 or later.\nPractice: raise the go directive to the first version that allows min. Replace go.mod with the worked answer and run go run .',
projectChecks=[
dict(name='old go line rejects min', args=['build', './...'], exit=1, outputContains=['requires go1.21 or later']),
dict(name='old go line rejects range over int', args=['build', './...'], exit=1,
     mutations=[dict(path='main.go', find='    fmt.Println(min(3, 1, 2))\n', replace='    for i := range 3 {\n        fmt.Println(i)\n    }\n')], outputContains=['requires go1.22 or later']),
dict(name='answer go 1.21', args=['run', '.'], useSolution=True, stdout='1\n'),
],
challenge='Raise the go directive to the earliest version that permits min, then run the program.',
question='Why does a go 1.20 module fail to compile min(3, 1, 2) with a 1.27 toolchain?',
correct='The go line fixes the language version, and min was added in Go 1.21',
wrong=['The 1.27 toolchain removed min', 'min needs an import of math'],
reasoning='Newer toolchains honour the declared language version, rejecting features from later versions so the module keeps building with the toolchains it claims to support.',
sourceURL=SPEC+'#Language_versions'),
]

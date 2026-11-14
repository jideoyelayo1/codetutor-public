STAGE = '05 · Methods and interfaces'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='methods-receivers', stage=STAGE, title='Methods, value receivers and pointer receivers',
body=[
'A method is a function with a receiver: func (c Counter) Value() int. Methods can be declared on any defined type in the same package, not only structs. The receiver is an ordinary parameter, so a value receiver works on a copy and a pointer receiver can modify the caller\'s value.',
'Use a pointer receiver when the method mutates the receiver, when the value is large, or when it contains something that must not be copied, such as a sync.Mutex. Be consistent: if some methods need pointers, give all methods of the type pointer receivers.',
'Calls are convenient in both directions. If v is addressable, v.Inc() on a pointer method is shorthand for (&v).Inc(). If p is a pointer, p.Value() on a value method is shorthand for (*p).Value(). The shorthand does not apply to values that are not addressable, such as map elements or return values.',
],
code=r'''package main

import "fmt"

type Counter struct{ n int }

func (c Counter) Value() int { return c.n }
func (c *Counter) Inc()      { c.n++ }
func (c Counter) BrokenInc() { c.n++ }

func main() {
    var c Counter
    c.Inc()
    c.Inc()
    c.BrokenInc()
    fmt.Println(c.Value())
    p := &c
    fmt.Println(p.Value())
}
''',
expectedStdout='2\n2\n',
challenge='Define type Stack []int with pointer-receiver methods Push(int) and Pop() int; push 1, 2, 3, pop once and print the popped value and the remaining stack.',
solution=r'''package main

import "fmt"

type Stack []int

func (s *Stack) Push(v int) { *s = append(*s, v) }

func (s *Stack) Pop() int {
    old := *s
    v := old[len(old)-1]
    *s = old[:len(old)-1]
    return v
}

func main() {
    var s Stack
    s.Push(1)
    s.Push(2)
    s.Push(3)
    fmt.Println(s.Pop(), s)
}
''',
solutionStdout='3 [1 2]\n',
question='Why did BrokenInc not change c?',
correct='A value receiver increments a copy of c',
wrong=['Methods cannot modify struct fields', 'The compiler optimised the call away'],
reasoning='The receiver is a parameter passed by value. Only a pointer receiver can change the caller\'s Counter.',
rejections=[dict(source='package main\n\ntype C struct{ n int }\n\nfunc (c *C) Inc() { c.n++ }\n\nfunc main() {\n\tm := map[string]C{"a": {}}\n\tm["a"].Inc()\n}\n', diagnostic='cannot call pointer method Inc on C')],
sourceURL=SPEC+'#Method_declarations',
additionalReadings=[dict(title='Go FAQ: pointer or value receivers', url='https://go.dev/doc/faq#methods_on_values_or_pointers', section='Methods on values or pointers')]),

dict(key='interfaces-implicit', stage=STAGE, title='Interfaces are satisfied implicitly',
body=[
'An interface type lists method signatures. Any type whose method set includes those methods satisfies the interface; there is no implements keyword. This lets you define small interfaces where they are used, and lets existing types satisfy interfaces written later.',
'An interface value holds two things: a dynamic type and a value of that type. Calling a method dispatches to the dynamic type\'s implementation. The zero interface value has neither and is nil.',
'Method sets decide satisfaction. The method set of T contains its value-receiver methods; the method set of *T contains both value- and pointer-receiver methods. So if Write has a pointer receiver, *Buffer satisfies io.Writer but Buffer does not. A compile-time assertion var _ io.Writer = (*Buffer)(nil) documents and checks this.',
],
code=r'''package main

import (
    "fmt"
    "math"
)

type Shape interface {
    Area() float64
}

type Rect struct{ W, H float64 }
type Circle struct{ R float64 }

func (r Rect) Area() float64   { return r.W * r.H }
func (c Circle) Area() float64 { return math.Pi * c.R * c.R }

func total(shapes ...Shape) float64 {
    sum := 0.0
    for _, s := range shapes {
        sum += s.Area()
    }
    return sum
}

var _ Shape = Rect{}

func main() {
    fmt.Printf("%.2f\n", total(Rect{2, 3}, Circle{1}))
}
''',
expectedStdout='9.14\n',
challenge='Add a Square type with field S that satisfies Shape and include Square{2} in the total; print it with two decimals.',
solution=r'''package main

import (
    "fmt"
    "math"
)

type Shape interface {
    Area() float64
}

type Rect struct{ W, H float64 }
type Circle struct{ R float64 }
type Square struct{ S float64 }

func (r Rect) Area() float64   { return r.W * r.H }
func (c Circle) Area() float64 { return math.Pi * c.R * c.R }
func (s Square) Area() float64 { return s.S * s.S }

func main() {
    sum := 0.0
    for _, s := range []Shape{Rect{2, 3}, Circle{1}, Square{2}} {
        sum += s.Area()
    }
    fmt.Printf("%.2f\n", sum)
}
''',
solutionStdout='13.14\n',
question='If Write has a pointer receiver on Buffer, which type satisfies io.Writer?',
correct='*Buffer only',
wrong=['Buffer only', 'Both Buffer and *Buffer'],
reasoning='The method set of the value type Buffer excludes pointer-receiver methods, because a value stored in an interface is not addressable.',
rejections=[dict(source='package main\n\nimport "io"\n\ntype B struct{}\n\nfunc (b *B) Write(p []byte) (int, error) { return len(p), nil }\n\nvar _ io.Writer = B{}\n\nfunc main() {}\n', diagnostic='method Write has pointer receiver')],
sourceURL=SPEC+'#Interface_types',
additionalReadings=[dict(title='Method sets', url=SPEC+'#Method_sets', section='Method sets')]),

dict(key='nil-interfaces', stage=STAGE, title='nil interfaces versus interfaces holding nil pointers',
body=[
'An interface is nil only when both its dynamic type and value are absent. Storing a nil *MyError in an error variable gives a non-nil interface whose dynamic type is *MyError and whose value is nil.',
'The classic bug is a function returning a concrete pointer type through an error result: var e *MyError; return e. The caller\'s err != nil is true even though nothing failed. Return a literal nil for "no error", and declare the result as error rather than *MyError.',
'A method with a pointer receiver can be called on a nil pointer, and can even handle it deliberately. That is why the runtime cannot simply treat "interface holding nil" as nil.',
],
code=r'''package main

import "fmt"

type MyError struct{}

func (e *MyError) Error() string { return "my error" }

func bad() error {
    var e *MyError
    return e
}

func good() error {
    return nil
}

func main() {
    fmt.Println(bad() == nil, good() == nil)
    fmt.Printf("%T\n", bad())
}
''',
expectedStdout='false true\n*main.MyError\n',
challenge='Rewrite a function find(ok bool) error so it returns &MyError{} when ok is false and a true nil interface otherwise; print find(true) == nil and find(false) == nil.',
solution=r'''package main

import "fmt"

type MyError struct{}

func (e *MyError) Error() string { return "my error" }

func find(ok bool) error {
    if !ok {
        return &MyError{}
    }
    return nil
}

func main() {
    fmt.Println(find(true) == nil, find(false) == nil)
}
''',
solutionStdout='true false\n',
question='Why is bad() != nil even though e was nil?',
correct='The interface has a dynamic type (*MyError) even though its value is nil',
wrong=['nil pointers are converted to empty structs', 'Comparison with nil always fails for errors'],
reasoning='An interface compares equal to nil only if it has no dynamic type. Return untyped nil to signal "no error".',
sourceURL='https://go.dev/doc/faq#nil_error'),

dict(key='type-assertions-switches', stage=STAGE, title='Type assertions and type switches',
body=[
'x.(T) asserts that interface value x holds a T. With one result it panics if wrong; with two, v, ok := x.(T), it reports success instead. If T is an interface type, the assertion checks whether the dynamic type implements T, which is how optional capabilities (such as io.WriterTo) are discovered.',
'A type switch, switch v := x.(type), branches on the dynamic type. In each case v has that case\'s type; in a case listing several types, or in default, v keeps the interface type. case nil matches a nil interface.',
'Prefer methods and small interfaces to large type switches: a type switch must be edited for each new type, while an interface lets new types plug in. Type switches are right for closed sets of message or AST node types.',
],
code=r'''package main

import "fmt"

func describe(x any) string {
    switch v := x.(type) {
    case nil:
        return "nil"
    case int:
        return fmt.Sprint("int+1=", v+1)
    case string, []byte:
        return fmt.Sprintf("text %v", v)
    case fmt.Stringer:
        return "stringer " + v.String()
    default:
        return fmt.Sprintf("other %T", v)
    }
}

func main() {
    for _, x := range []any{nil, 41, "go", 2.5} {
        fmt.Println(describe(x))
    }
    var a any = "hi"
    n, ok := a.(int)
    fmt.Println(n, ok)
}
''',
expectedStdout='nil\nint+1=42\ntext go\nother float64\n0 false\n',
challenge='Write func sum(xs []any) float64 that adds int and float64 elements and ignores everything else; print sum([]any{1, 2.5, "x", 3}).',
solution=r'''package main

import "fmt"

func sum(xs []any) float64 {
    total := 0.0
    for _, x := range xs {
        switch v := x.(type) {
        case int:
            total += float64(v)
        case float64:
            total += v
        }
    }
    return total
}

func main() {
    fmt.Println(sum([]any{1, 2.5, "x", 3}))
}
''',
solutionStdout='6.5\n',
question='What does v, ok := x.(T) do when x does not hold a T?',
correct='Sets ok to false and v to T\'s zero value, without panicking',
wrong=['Panics with a type assertion error', 'Converts x to T if possible'],
reasoning='The comma-ok form makes the assertion non-panicking. The single-result form panics on failure.',
sourceURL=SPEC+'#Type_switches',
additionalReadings=[dict(title='Type assertions', url=SPEC+'#Type_assertions', section='Type assertions')]),

dict(key='interface-composition', stage=STAGE, title='Small interfaces, embedding and any',
body=[
'The standard library favours one-method interfaces: io.Reader, io.Writer, fmt.Stringer, error. Larger interfaces are built by embedding: io.ReadWriter embeds Reader and Writer. A small interface is easy to satisfy and easy to fake in tests.',
'any is an alias for interface{}, the interface with no methods, satisfied by every type. Accepting any discards static typing, so use it only when values really can be of any type, such as formatting and encoding. Generics are usually a better fit for containers.',
'Define interfaces in the package that consumes them, sized to what that code needs. Returning concrete types and accepting interfaces keeps APIs flexible: callers can pass anything with the needed methods.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "strings"
)

type upper struct{ r io.Reader }

func (u upper) Read(p []byte) (int, error) {
    n, err := u.r.Read(p)
    copy(p, strings.ToUpper(string(p[:n])))
    return n, err
}

func main() {
    var r io.Reader = upper{strings.NewReader("small interfaces compose")}
    data, err := io.ReadAll(r)
    fmt.Println(string(data), err)
}
''',
expectedStdout='SMALL INTERFACES COMPOSE <nil>\n',
challenge='Write a type countingWriter that wraps an io.Writer, counts bytes written, and forwards them; write "hello" and " go" through it to os.Stdout and then print the count on its own line.',
solution=r'''package main

import (
    "fmt"
    "io"
    "os"
)

type countingWriter struct {
    w io.Writer
    n int
}

func (c *countingWriter) Write(p []byte) (int, error) {
    n, err := c.w.Write(p)
    c.n += n
    return n, err
}

func main() {
    cw := &countingWriter{w: os.Stdout}
    fmt.Fprint(cw, "hello")
    fmt.Fprint(cw, " go")
    fmt.Println()
    fmt.Println(cw.n)
}
''',
solutionStdout='hello go\n8\n',
question='Where should a Go interface usually be declared?',
correct='In the package that uses it, with only the methods it needs',
wrong=['Next to every type that implements it', 'In a shared interfaces package for the whole program'],
reasoning='Implicit satisfaction lets consumers declare the minimal interface they depend on without the implementer importing it.',
sourceURL='https://go.dev/doc/effective_go#interfaces'),

dict(key='stringer-format', stage=STAGE, title='Stringer, error and custom formatting',
body=[
'If a type has a String() string method, fmt uses it for %v and %s. If it has Error() string, fmt uses that, and error takes priority over String. Defining String on a value receiver means both values and pointers print nicely.',
'Calling fmt.Sprint(s) inside s.String() on the same type recurses forever. Convert to an underlying type without the method first, for example fmt.Sprint(int(d)).',
'For full control implement fmt.Formatter, or fmt.GoStringer for %#v. Most code only needs String. go vet warns when a String method has the wrong signature, because fmt would silently ignore it.',
],
code=r'''package main

import "fmt"

type Weekday int

const (
    Sunday Weekday = iota
    Monday
)

func (d Weekday) String() string {
    switch d {
    case Sunday:
        return "Sunday"
    case Monday:
        return "Monday"
    }
    return fmt.Sprintf("Weekday(%d)", int(d))
}

func main() {
    fmt.Println(Monday, Weekday(9))
    fmt.Printf("%v %d %s\n", Sunday, Sunday, Weekday(1))
}
''',
expectedStdout='Monday Weekday(9)\nSunday 0 Monday\n',
challenge='Give type Celsius float64 a String method that prints one decimal and a °C suffix; print Celsius(21.55).',
solution=r'''package main

import "fmt"

type Celsius float64

func (c Celsius) String() string {
    return fmt.Sprintf("%.1f°C", float64(c))
}

func main() {
    fmt.Println(Celsius(21.55))
}
''',
solutionStdout='21.6°C\n',
question='Why convert to int(d) inside Weekday.String before formatting?',
correct='Formatting d itself would call String again and recurse forever',
wrong=['%d does not accept named types', 'String methods must return only constants'],
reasoning='fmt checks for a String method on the operand. The underlying int has none, so the conversion breaks the recursion.',
sourceURL='https://pkg.go.dev/fmt#Stringer'),

dict(key='comparable-equality', stage=STAGE, title='Equality, comparability and interface comparison panics',
body=[
'Booleans, numbers, strings, pointers, channels and interfaces are comparable, and so are structs and arrays whose elements are comparable. Slices, maps and functions are not comparable except with nil; use slices.Equal and maps.Equal for contents.',
'Two interface values are equal if their dynamic types are identical and their values are equal. If the dynamic type is not comparable, for example a slice, the comparison compiles but panics at run time. The same applies to using such an interface as a map key.',
'Pointers are equal when they point to the same variable. Two distinct zero-size variables may or may not have equal addresses, so do not rely on pointer identity for empty structs.',
],
code=r'''package main

import (
    "fmt"
    "slices"
)

func main() {
    a, b := []int{1, 2}, []int{1, 2}
    fmt.Println(slices.Equal(a, b))
    var x, y any = 3, 3
    fmt.Println(x == y)
    defer func() { fmt.Println("recovered:", recover()) }()
    var p, q any = a, b
    fmt.Println(p == q)
}
''',
expectedStdout='true\ntrue\nrecovered: runtime error: comparing uncomparable type []int\n',
challenge='Show that two struct values type key struct{ a string; b int } with equal fields are == and can be used as the same map key; print the map length after inserting key{"x", 1} twice.',
solution=r'''package main

import "fmt"

type key struct {
    a string
    b int
}

func main() {
    m := map[key]bool{}
    m[key{"x", 1}] = true
    m[key{"x", 1}] = true
    fmt.Println(key{"x", 1} == key{"x", 1}, len(m))
}
''',
solutionStdout='true 1\n',
question='What happens when two any values holding slices are compared with ==?',
correct='It compiles but panics at run time',
wrong=['It compares the slice contents', 'It is always a compile error'],
reasoning='Interface comparison is checked dynamically. The static type any is comparable, but the dynamic type []int is not, so the runtime panics.',
rejections=[dict(source='package main\n\nfunc main() {\n\ta, b := []int{1}, []int{1}\n\t_ = a == b\n}\n', diagnostic='slice can only be compared to nil')],
sourceURL=SPEC+'#Comparison_operators'),
]

STAGE = '09 · Generics'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='type-parameters', stage=STAGE, title='Type parameters and generic functions',
body=[
'A generic function declares type parameters in square brackets: func Map[T, U any](xs []T, f func(T) U) []U. Each type parameter has a constraint, an interface describing what the function may do with values of that type. any allows only operations every type supports: assignment, passing, and comparison with nil for some kinds.',
'Callers can write type arguments explicitly, Map[int, string](xs, f), but usually the compiler infers them from the ordinary arguments. Inference works from function arguments and, for untyped constants, picks the default type.',
'Generics remove duplicated code for containers and algorithms that are the same for every type. They do not replace interfaces: if a function only calls methods, an interface parameter is simpler. Reach for type parameters when you need to keep the concrete type, such as returning []T rather than []any.',
],
code=r'''package main

import (
    "fmt"
    "strconv"
)

func Map[T, U any](xs []T, f func(T) U) []U {
    out := make([]U, 0, len(xs))
    for _, x := range xs {
        out = append(out, f(x))
    }
    return out
}

func Filter[T any](xs []T, keep func(T) bool) []T {
    var out []T
    for _, x := range xs {
        if keep(x) {
            out = append(out, x)
        }
    }
    return out
}

func main() {
    nums := []int{1, 2, 3, 4}
    fmt.Println(Map(nums, strconv.Itoa))
    fmt.Println(Filter(nums, func(n int) bool { return n%2 == 0 }))
    fmt.Printf("%T\n", Map[int, float64](nums, func(n int) float64 { return float64(n) / 2 }))
}
''',
expectedStdout='[1 2 3 4]\n[2 4]\n[]float64\n',
challenge='Write func Reduce[T, A any](xs []T, init A, f func(A, T) A) A and use it to sum []int{1, 2, 3} and to join []string{"a", "b"} into "ab".',
solution=r'''package main

import "fmt"

func Reduce[T, A any](xs []T, init A, f func(A, T) A) A {
    acc := init
    for _, x := range xs {
        acc = f(acc, x)
    }
    return acc
}

func main() {
    fmt.Println(Reduce([]int{1, 2, 3}, 0, func(a, x int) int { return a + x }))
    fmt.Println(Reduce([]string{"a", "b"}, "", func(a, x string) string { return a + x }))
}
''',
solutionStdout='6\nab\n',
question='When is an interface parameter a better choice than a type parameter?',
correct='When the function only calls methods and does not need the concrete type back',
wrong=['Never; generics are always faster', 'When the function works with slices'],
reasoning='Interfaces give dynamic dispatch with simple signatures. Type parameters help when the type must be preserved in results or containers.',
sourceURL='https://go.dev/doc/tutorial/generics',
additionalReadings=[dict(title='When to use generics', url='https://go.dev/blog/when-generics', section='When to use generics')]),

dict(key='constraints-type-sets', stage=STAGE, title='Constraints, type sets, ~ and cmp.Ordered',
body=[
'A constraint is an interface, and an interface defines a type set. Besides methods, a constraint can list types: interface{ int | int64 | float64 } permits exactly those types, and operators such as + and < are allowed only if every type in the set supports them.',
'~T means "any type whose underlying type is T". interface{ ~int } accepts int and also type Celsius int. Without the tilde, defined types built on int are excluded, which is rarely what you want for numeric helpers.',
'The standard library provides cmp.Ordered (types supporting < <= > >=) and comparable (types supporting == and !=). Interfaces containing type elements can only be used as constraints, never as ordinary variable types.',
],
code=r'''package main

import (
    "cmp"
    "fmt"
)

type Number interface {
    ~int | ~int64 | ~float64
}

func Sum[T Number](xs ...T) T {
    var total T
    for _, x := range xs {
        total += x
    }
    return total
}

func Largest[T cmp.Ordered](xs []T) T {
    best := xs[0]
    for _, x := range xs[1:] {
        best = max(best, x)
    }
    return best
}

type Cents int

func main() {
    fmt.Println(Sum(1, 2, 3), Sum(1.5, 2))
    fmt.Println(Sum(Cents(250), Cents(100)))
    fmt.Println(Largest([]string{"pear", "apple", "zucchini"}))
}
''',
expectedStdout='6 3.5\n350\nzucchini\n',
challenge='Write func Clamp[T cmp.Ordered](v, lo, hi T) T and print Clamp(15, 0, 10), Clamp(-2.5, -1, 1) and Clamp("m", "a", "k").',
solution=r'''package main

import (
    "cmp"
    "fmt"
)

func Clamp[T cmp.Ordered](v, lo, hi T) T {
    return min(max(v, lo), hi)
}

func main() {
    fmt.Println(Clamp(15, 0, 10), Clamp(-2.5, -1, 1), Clamp("m", "a", "k"))
}
''',
solutionStdout='10 -1 k\n',
question='Which types satisfy interface{ ~int }?',
correct='int and every defined type whose underlying type is int',
wrong=['Only int itself', 'Every integer type of any size'],
reasoning='~ widens a type element to its underlying type. Without it the set contains int alone.',
rejections=[dict(source='package main\n\ntype Number interface{ int | float64 }\n\ntype Cents int\n\nfunc Sum[T Number](xs ...T) T {\n\tvar t T\n\treturn t\n}\n\nfunc main() {\n\t_ = Sum(Cents(1))\n}\n', diagnostic='Cents does not satisfy Number')],
sourceURL=SPEC+'#General_interfaces',
additionalReadings=[dict(title='cmp package', url='https://pkg.go.dev/cmp', section='Ordered, Compare, Or')]),

dict(key='comparable-constraint', stage=STAGE, title='comparable, map keys and strict comparability',
body=[
'A type parameter used as a map key or compared with == needs the comparable constraint. func Index[T comparable](xs []T, v T) int works for strings, numbers, pointers, structs of comparable fields, and so on.',
'Since Go 1.20, interface types such as any also satisfy comparable, even though comparing two interface values can panic if their dynamic types are not comparable. Only strictly comparable types guarantee == never panics.',
'Generic sets and deduplication are typical uses: type Set[T comparable] map[T]struct{}. The empty struct value takes no space, so the map stores only keys.',
],
code=r'''package main

import (
    "fmt"
    "slices"
)

type Set[T comparable] map[T]struct{}

func (s Set[T]) Add(v T) { s[v] = struct{}{} }

func (s Set[T]) Has(v T) bool {
    _, ok := s[v]
    return ok
}

func (s Set[T]) Len() int { return len(s) }

func Of[T comparable](vs ...T) Set[T] {
    s := Set[T]{}
    for _, v := range vs {
        s.Add(v)
    }
    return s
}

func Dedup[T comparable](xs []T) []T {
    seen := Set[T]{}
    var out []T
    for _, x := range xs {
        if !seen.Has(x) {
            seen.Add(x)
            out = append(out, x)
        }
    }
    return out
}

func main() {
    s := Of("go", "rust", "go")
    fmt.Println(s.Len(), s.Has("rust"), s.Has("java"))
    fmt.Println(Dedup([]int{3, 1, 3, 2, 1}))
    fmt.Println(slices.Index([]string{"a", "b"}, "b"))
}
''',
expectedStdout='2 true false\n[3 1 2]\n1\n',
challenge='Write func Intersect[T comparable](a, b []T) []T returning the elements of a that also appear in b, in a\'s order without duplicates; print Intersect([]int{1, 2, 2, 3}, []int{2, 3, 4}).',
solution=r'''package main

import "fmt"

func Intersect[T comparable](a, b []T) []T {
    inB := map[T]bool{}
    for _, v := range b {
        inB[v] = true
    }
    var out []T
    for _, v := range a {
        if inB[v] {
            out = append(out, v)
            delete(inB, v)
        }
    }
    return out
}

func main() {
    fmt.Println(Intersect([]int{1, 2, 2, 3}, []int{2, 3, 4}))
}
''',
solutionStdout='[2 3]\n',
question='Can any be used as a type argument for a comparable type parameter?',
correct='Yes since Go 1.20, though == may panic for non-comparable dynamic types',
wrong=['No, any is never comparable', 'Yes, and comparison can never panic'],
reasoning='Go 1.20 allowed interfaces to satisfy comparable. Strict comparability, which rules out run-time panics, holds only for non-interface comparable types.',
sourceURL=SPEC+'#Comparable_types'),

dict(key='type-inference', stage=STAGE, title='Type inference, including Go 1.27\'s assignment inference',
body=[
'Function argument type inference unifies parameter types with argument types: Map(nums, strconv.Itoa) infers T=int and U=string. Constraint type inference fills in parameters that appear inside other constraints, such as the element type E of a slice type S ~[]E.',
'func Scale[S ~[]E, E Number](s S, k E) S returns the caller\'s own slice type, not plain []E. That matters when the caller has methods on a named slice type.',
'Go 1.21 allowed inference when a generic function is assigned to a variable of a function type. Go 1.27 generalises this to every context where a generic function is assigned or converted to a matching function type, such as struct fields and return values. You no longer need to write Double[int] when the target type already says int.',
],
code=r'''package main

import "fmt"

type Number interface{ ~int | ~float64 }

func Scale[S ~[]E, E Number](s S, k E) S {
    out := make(S, len(s))
    for i, v := range s {
        out[i] = v * k
    }
    return out
}

type Prices []float64

func (p Prices) Total() float64 {
    t := 0.0
    for _, v := range p {
        t += v
    }
    return t
}

func Double[T Number](x T) T { return x * 2 }

type Ops struct {
    F func(int) int
}

func pick() func(float64) float64 { return Double }

func main() {
    p := Scale(Prices{1, 2.5}, 2)
    fmt.Println(p.Total())
    ops := Ops{F: Double}
    fmt.Println(ops.F(21), pick()(1.25))
}
''',
expectedStdout='7\n42 2.5\n',
challenge='Write func Negate[T Number](x T) T and store it, without explicit type arguments, in a []func(int) int alongside Double; apply both to 5.',
solution=r'''package main

import "fmt"

type Number interface{ ~int | ~float64 }

func Double[T Number](x T) T { return x * 2 }
func Negate[T Number](x T) T { return -x }

func main() {
    fs := []func(int) int{Double, Negate}
    for _, f := range fs {
        fmt.Println(f(5))
    }
}
''',
solutionStdout='10\n-5\n',
question='Why does Scale take S ~[]E instead of a plain []E?',
correct='So it returns the caller\'s named slice type, keeping its methods',
wrong=['Because []E cannot be ranged over', 'To make the function run faster'],
reasoning='With []E the result would be []float64 and lose Prices.Total. Constraint inference derives E from S.',
sourceURL='https://go.dev/blog/type-inference',
additionalReadings=[dict(title='Go 1.27 release notes: language', url='https://go.dev/doc/go1.27#language', section='Generalised function type inference')]),

dict(key='generic-types', stage=STAGE, title='Generic types, methods on them and generic aliases',
body=[
'Types can have type parameters too: type Stack[T any] struct { items []T }. Methods on a generic type list the receiver\'s parameters, func (s *Stack[T]) Push(v T), and can use T but, before Go 1.27, could not add new type parameters of their own.',
'Instantiating a generic type with type arguments makes an ordinary type: Stack[int] and Stack[string] are distinct. The zero value works if the struct is designed for it, which is the usual Go goal.',
'Since Go 1.24 type aliases can be generic: type Set[T comparable] = map[T]struct{}. That helps move generic types between packages without breaking callers.',
],
code=r'''package main

import "fmt"

type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(v T) { s.items = append(s.items, v) }

func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.items) == 0 {
        return zero, false
    }
    v := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return v, true
}

type Pair[K comparable, V any] struct {
    Key K
    Val V
}

type Lookup[V any] = map[string]V

func main() {
    var s Stack[string]
    s.Push("a")
    s.Push("b")
    v, ok := s.Pop()
    fmt.Println(v, ok)
    var empty Stack[int]
    fmt.Println(empty.Pop())
    fmt.Printf("%+v\n", Pair[string, int]{"go", 1})
    l := Lookup[int]{"x": 1}
    fmt.Println(l["x"])
}
''',
expectedStdout='b true\n0 false\n{Key:go Val:1}\n1\n',
challenge='Write a generic Queue[T any] with Enqueue and Dequeue (returning T, bool); enqueue 1, 2, 3 and dequeue twice, printing each result.',
solution=r'''package main

import "fmt"

type Queue[T any] struct {
    items []T
}

func (q *Queue[T]) Enqueue(v T) { q.items = append(q.items, v) }

func (q *Queue[T]) Dequeue() (T, bool) {
    var zero T
    if len(q.items) == 0 {
        return zero, false
    }
    v := q.items[0]
    q.items = q.items[1:]
    return v, true
}

func main() {
    var q Queue[int]
    for i := 1; i <= 3; i++ {
        q.Enqueue(i)
    }
    fmt.Println(q.Dequeue())
    fmt.Println(q.Dequeue())
}
''',
solutionStdout='1 true\n2 true\n',
question='How do you return "no value" from a generic method returning T?',
correct='Declare var zero T and return it with a false flag or an error',
wrong=['Return nil', 'Return T{}'],
reasoning='nil is not valid for every T, and T{} is not valid syntax for all types. var zero T is the zero value of whatever T is.',
sourceURL=SPEC+'#Type_parameter_declarations',
additionalReadings=[dict(title='Go 1.24 generic type aliases', url='https://go.dev/doc/go1.24#language', section='Generic type aliases')]),

dict(key='generic-methods', stage=STAGE, title='Go 1.27 generic methods',
body=[
'Go 1.27 lets a method declare its own type parameters in addition to the receiver\'s: func (l List[T]) Map[U any](f func(T) U) List[U]. Before 1.27 such helpers had to be package-level functions, Map(l, f), because methods could not introduce new types.',
'Type arguments are inferred at the call as for functions, or can be given explicitly: l.Map[string](f). Non-generic types can have generic methods too, for example func (r Reader) Decode[T any]() (T, error).',
'A generic method does not belong to any interface\'s method set, because an interface cannot list a method whose type depends on a parameter chosen per call. So generic methods are for convenience on concrete types, not for satisfying interfaces. Older modules need go 1.27 in go.mod to use them.',
],
code=r'''package main

import (
    "fmt"
    "strings"
)

type List[T any] struct {
    items []T
}

func (l List[T]) Map[U any](f func(T) U) List[U] {
    out := List[U]{items: make([]U, 0, len(l.items))}
    for _, v := range l.items {
        out.items = append(out.items, f(v))
    }
    return out
}

type Config map[string]string

func (c Config) Get[T any](key string, parse func(string) (T, error)) (T, error) {
    return parse(c[key])
}

func main() {
    words := List[string]{items: []string{"go", "gopher"}}
    lengths := words.Map(func(s string) int { return len(s) })
    fmt.Println(lengths.items, words.Map(strings.ToUpper).items)
    c := Config{"debug": "true"}
    v, err := c.Get("debug", func(s string) (bool, error) { return s == "true", nil })
    fmt.Println(v, err)
}
''',
expectedStdout='[2 6] [GO GOPHER]\ntrue <nil>\n',
challenge='Add a generic method Fold[A any](init A, f func(A, T) A) A to List[T] and use it to sum the lengths of List[string]{items: []string{"a", "bb", "ccc"}}.',
solution=r'''package main

import "fmt"

type List[T any] struct {
    items []T
}

func (l List[T]) Fold[A any](init A, f func(A, T) A) A {
    acc := init
    for _, v := range l.items {
        acc = f(acc, v)
    }
    return acc
}

func main() {
    l := List[string]{items: []string{"a", "bb", "ccc"}}
    fmt.Println(l.Fold(0, func(n int, s string) int { return n + len(s) }))
}
''',
solutionStdout='6\n',
question='Can a generic method be used to satisfy an interface?',
correct='No; generic methods are not part of any interface\'s method set',
wrong=['Yes, if the interface lists the same name', 'Yes, but only with explicit type arguments'],
reasoning='An interface method has one fixed signature, while a generic method has a family of signatures chosen per call.',
sourceURL='https://go.dev/doc/go1.27#language',
additionalReadings=[dict(title='Method declarations', url=SPEC+'#Method_declarations', section='Method type parameters')]),

dict(key='generics-limits', stage=STAGE, title='Generics: limits, costs and design trade-offs',
body=[
'Type parameters cannot be used in a type switch directly; switch any(v).(type) converts to an interface first. You cannot declare a type parameter on an embedded field or use one as an embedded type. Before 1.27, methods could not have their own type parameters.',
'The compiler shares code between instantiations whose types have the same memory shape (GC shape stenciling), passing a dictionary for the specific types. Generic code is usually as fast as hand-written code, but calling methods through a type parameter can cost an indirect call similar to an interface call.',
'Start with concrete code; introduce type parameters when a second or third type needs the same logic. Constraints should be as loose as possible: any, then comparable, then cmp.Ordered, then custom sets.',
],
code=r'''package main

import "fmt"

func Describe[T any](v T) string {
    switch x := any(v).(type) {
    case int:
        return fmt.Sprintf("int %d", x)
    case string:
        return fmt.Sprintf("string %q", x)
    default:
        return fmt.Sprintf("%T", x)
    }
}

func main() {
    fmt.Println(Describe(7))
    fmt.Println(Describe("go"))
    fmt.Println(Describe([]byte("x")))
}
''',
expectedStdout='int 7\nstring "go"\n[]uint8\n',
challenge='Write func Zero[T any]() T and print Zero[int](), Zero[string]() quoted with %q, and whether Zero[*int]() is nil.',
solution=r'''package main

import "fmt"

func Zero[T any]() T {
    var z T
    return z
}

func main() {
    fmt.Println(Zero[int]())
    fmt.Printf("%q\n", Zero[string]())
    fmt.Println(Zero[*int]() == nil)
}
''',
solutionStdout='0\n""\ntrue\n',
question='How do you branch on the concrete type of a type parameter value v?',
correct='Convert it to an interface: switch any(v).(type)',
wrong=['switch v.(type) works directly', 'Use reflect only; type switches are impossible'],
reasoning='Type switches apply to interface values. Converting with any(v) gives an interface holding the concrete type argument.',
rejections=[dict(source='package main\n\nfunc F[T any](v T) {\n\tswitch v.(type) {\n\t}\n}\n\nfunc main() {}\n', diagnostic='cannot use type switch on type parameter value v')],
sourceURL='https://go.dev/blog/intro-generics'),
]

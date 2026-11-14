STAGE = '04 · Composite data'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='arrays', stage=STAGE, title='Arrays are values with a fixed length',
body=[
'An array type includes its length: [3]int and [4]int are different types. Arrays are values, so assigning or passing one copies every element. That makes small arrays useful as map keys and as fixed-size records, but it surprises programmers coming from C, where arrays decay to pointers.',
'Array literals can let the compiler count: [...]string{"a", "b"} has type [2]string. Indexed literals such as [5]int{2: 7} set selected positions and leave the rest zero. Indexing out of range with a constant index is a compile error; with a variable index it panics at run time.',
'Arrays of comparable elements can be compared with ==. In practice most Go code uses slices, which are views onto arrays; arrays appear in hashes ([32]byte), coordinates and buffers sized at compile time.',
],
code=r'''package main

import "fmt"

func bump(a [3]int) [3]int {
    a[0] = 100
    return a
}

func main() {
    a := [...]int{1, 2, 3}
    b := bump(a)
    fmt.Println(a, b)
    sparse := [5]int{2: 7, 4: 9}
    fmt.Println(sparse, len(sparse))
    fmt.Println([2]string{"x", "y"} == [2]string{"x", "y"})
}
''',
expectedStdout='[1 2 3] [100 2 3]\n[0 0 7 0 9] 5\ntrue\n',
challenge='Use a [2]int{x, y} array as a map key to count how many times each grid point appears in the list (1,2), (3,4), (1,2); print the count for (1,2).',
solution=r'''package main

import "fmt"

func main() {
    seen := map[[2]int]int{}
    for _, p := range [][2]int{{1, 2}, {3, 4}, {1, 2}} {
        seen[p]++
    }
    fmt.Println(seen[[2]int{1, 2}])
}
''',
solutionStdout='2\n',
question='What happens when an array is passed to a function?',
correct='The whole array is copied',
wrong=['A pointer to the first element is passed', 'A slice view is created automatically'],
reasoning='Arrays are values. To share one, pass a pointer (*[3]int) or a slice of it (a[:]).',
rejections=[dict(source='package main\n\nfunc main() {\n\tvar a [3]int\n\ta[5] = 1\n}\n', diagnostic='out of bounds')],
sourceURL=SPEC+'#Array_types'),

dict(key='slices-len-cap', stage=STAGE, title='Slices: length, capacity and shared backing arrays',
body=[
'A slice is a small header: a pointer into a backing array, a length and a capacity. s[lo:hi] makes a new header over the same array, with length hi-lo and capacity reaching to the end of the array. Writing through one slice is visible through every slice that shares the array.',
'append(s, x) writes into the existing array when len < cap and returns a header with a larger length. When capacity runs out it allocates a bigger array, copies the elements and returns a header pointing there. Always assign the result: s = append(s, x).',
'Because append may or may not reallocate, two slices that once shared memory may silently stop sharing. A full slice expression s[lo:hi:max] limits the capacity, forcing the next append on the sub-slice to copy instead of overwriting the parent\'s later elements.',
'A nil slice has length and capacity zero, and works with len, append and range. make([]T, n, c) allocates a slice with length n and capacity c.',
],
code=r'''package main

import "fmt"

func main() {
    base := []int{1, 2, 3, 4, 5}
    head := base[:2]
    fmt.Println(len(head), cap(head))
    head = append(head, 99)
    fmt.Println(base)
    safe := base[:2:2]
    safe = append(safe, -1)
    fmt.Println(base, safe)
    var empty []int
    fmt.Println(empty == nil, len(empty), append(empty, 7))
}
''',
expectedStdout='2 5\n[1 2 99 4 5]\n[1 2 99 4 5] [1 2 -1]\ntrue 0 [7]\n',
challenge='Write func remove(s []int, i int) []int that deletes element i without changing order, then show that the caller\'s original slice was modified by printing it.',
solution=r'''package main

import "fmt"

func remove(s []int, i int) []int {
    copy(s[i:], s[i+1:])
    return s[:len(s)-1]
}

func main() {
    s := []int{10, 20, 30, 40}
    t := remove(s, 1)
    fmt.Println(t)
    fmt.Println(s)
}
''',
solutionStdout='[10 30 40]\n[10 30 40 40]\n',
question='After t := s[:2]; t = append(t, 9), when is s[2] overwritten?',
correct='When cap(t) > 2, because append writes into the shared array',
wrong=['Never; append always copies', 'Only if s is a nil slice'],
reasoning='With spare capacity, append places the new element in the backing array that s also uses. A full slice expression s[:2:2] prevents this.',
sourceURL='https://go.dev/blog/slices-intro',
additionalReadings=[dict(title='Slice expressions', url=SPEC+'#Slice_expressions', section='Full slice expressions')]),

dict(key='slices-package', stage=STAGE, title='The slices package: sort, search, insert, compact',
body=[
'The generic slices package (Go 1.21+) replaces many hand-written loops: slices.Sort, SortFunc, SortStableFunc, BinarySearch, Contains, Index, IndexFunc, Insert, Delete, Compact, Reverse, Max, Min, Equal and Clone.',
'Comparison functions return a negative, zero or positive int; cmp.Compare and cmp.Or help compose multi-key orderings. SortFunc is not stable; use SortStableFunc when equal elements must keep their order.',
'Delete, Insert and Compact return the new slice and may reuse the old backing array. Since Go 1.22 the removed tail elements are zeroed, so pointers left behind do not keep objects alive. As with append, use the returned slice.',
],
code=r'''package main

import (
    "cmp"
    "fmt"
    "slices"
)

type person struct {
    name string
    age  int
}

func main() {
    xs := []int{3, 1, 3, 2, 1}
    slices.Sort(xs)
    xs = slices.Compact(xs)
    fmt.Println(xs)
    i, found := slices.BinarySearch(xs, 2)
    fmt.Println(i, found)
    people := []person{{"bo", 30}, {"al", 25}, {"cy", 30}}
    slices.SortStableFunc(people, func(a, b person) int {
        return cmp.Compare(b.age, a.age)
    })
    fmt.Println(people)
    fmt.Println(slices.Insert([]int{1, 4}, 1, 2, 3))
}
''',
expectedStdout='[1 2 3]\n1 true\n[{bo 30} {cy 30} {al 25}]\n[1 2 3 4]\n',
challenge='Sort people by name length, then alphabetically for equal lengths, using cmp.Or; print the names for "bob", "al", "eve", "zo".',
solution=r'''package main

import (
    "cmp"
    "fmt"
    "slices"
)

func main() {
    names := []string{"bob", "al", "eve", "zo"}
    slices.SortFunc(names, func(a, b string) int {
        return cmp.Or(cmp.Compare(len(a), len(b)), cmp.Compare(a, b))
    })
    fmt.Println(names)
}
''',
solutionStdout='[al zo bob eve]\n',
question='Why use SortStableFunc rather than SortFunc?',
correct='It keeps equal elements in their original relative order',
wrong=['It is always faster', 'It sorts in descending order'],
reasoning='SortFunc may reorder elements that compare equal. Stability matters when sorting by a secondary key after an earlier sort.',
sourceURL='https://pkg.go.dev/slices'),

dict(key='maps', stage=STAGE, title='Maps: lookup, comma-ok, deletion and iteration order',
body=[
'map[K]V stores key/value pairs; K must be comparable. m[k] returns the zero value for a missing key, so use the comma-ok form v, ok := m[k] to tell "missing" from "present with zero value". delete(m, k) removes a key and is a no-op if it is absent.',
'Iteration order over a map is unspecified and deliberately varies between runs. If output must be deterministic, collect the keys, sort them (slices.Sorted(maps.Keys(m)) does both since Go 1.23) and range over the sorted keys.',
'Maps are reference-like: assigning a map copies the header, so both names see the same entries. Writing to a nil map panics. Maps are not safe for concurrent writes; the runtime detects many such races and crashes with "concurrent map writes".',
],
code=r'''package main

import (
    "fmt"
    "maps"
    "slices"
)

func main() {
    ages := map[string]int{"ada": 36, "bob": 0}
    v, ok := ages["bob"]
    fmt.Println(v, ok)
    v, ok = ages["cy"]
    fmt.Println(v, ok)
    delete(ages, "bob")
    ages["cy"] = 41
    for _, k := range slices.Sorted(maps.Keys(ages)) {
        fmt.Println(k, ages[k])
    }
    alias := ages
    alias["ada"]++
    fmt.Println(ages["ada"], len(ages))
}
''',
expectedStdout='0 true\n0 false\nada 36\ncy 41\n37 2\n',
challenge='Count word frequencies in "the cat and the hat and the bat" and print each word with its count in alphabetical order.',
solution=r'''package main

import (
    "fmt"
    "maps"
    "slices"
    "strings"
)

func main() {
    counts := map[string]int{}
    for _, w := range strings.Fields("the cat and the hat and the bat") {
        counts[w]++
    }
    for _, w := range slices.Sorted(maps.Keys(counts)) {
        fmt.Println(w, counts[w])
    }
}
''',
solutionStdout='and 2\nbat 1\ncat 1\nhat 1\nthe 3\n',
question='How should you print a map\'s entries in a stable order?',
correct='Collect and sort the keys, then range over the sorted keys',
wrong=['Range over the map; insertion order is preserved', 'Call maps.Clone first to fix the order'],
reasoning='Map iteration order is unspecified and randomised. fmt prints maps with sorted keys, but range does not.',
sourceURL='https://go.dev/blog/maps',
additionalReadings=[dict(title='maps package', url='https://pkg.go.dev/maps', section='Keys, Values, Clone, Collect')]),

dict(key='structs-embedding', stage=STAGE, title='Structs, field tags and embedding',
body=[
'A struct groups named fields: type Point struct { X, Y int }. Composite literals can name fields (Point{X: 1}) or list them positionally; naming fields keeps code working when fields are added. Structs of comparable fields can be compared with ==.',
'Embedding a type in a struct (a field with no name) promotes the embedded type\'s fields and methods to the outer struct. This is composition, not inheritance: the outer value contains the inner one, and methods still receive the inner value as their receiver. An outer field or method with the same name shadows the promoted one.',
'Field tags are string metadata read by reflection, for example `json:"name,omitempty"`. They do not change the language semantics; packages such as encoding/json interpret them. Anonymous structs are useful for one-off groupings and table-driven tests.',
],
code=r'''package main

import "fmt"

type Point struct {
    X, Y int
}

type Named struct {
    Point
    Name string `json:"name"`
}

func (p Point) Sum() int { return p.X + p.Y }

func main() {
    n := Named{Point: Point{X: 1, Y: 2}, Name: "origin-ish"}
    fmt.Println(n.X, n.Sum(), n.Point == Point{1, 2})
    cases := []struct {
        in   int
        want int
    }{{1, 2}, {2, 4}}
    fmt.Printf("%+v\n", cases[1])
}
''',
expectedStdout='1 3 true\n{in:2 want:4}\n',
challenge='Define type Animal struct{ Name string } with method Hello() string returning "I am "+Name, and type Dog struct{ Animal; Breed string }; print Hello for a Dog named Rex.',
solution=r'''package main

import "fmt"

type Animal struct{ Name string }

func (a Animal) Hello() string { return "I am " + a.Name }

type Dog struct {
    Animal
    Breed string
}

func main() {
    d := Dog{Animal{"Rex"}, "collie"}
    fmt.Println(d.Hello())
}
''',
solutionStdout='I am Rex\n',
question='When Dog embeds Animal and you call d.Hello(), what is the receiver?',
correct='The embedded Animal value inside d',
wrong=['The whole Dog value', 'A new Animal copied from Dog\'s fields'],
reasoning='Promotion rewrites d.Hello() to d.Animal.Hello(). The method has no knowledge of the outer Dog, which is why embedding is not virtual dispatch.',
sourceURL=SPEC+'#Struct_types',
additionalReadings=[dict(title='Effective Go: embedding', url='https://go.dev/doc/effective_go#embedding', section='Embedding')]),

dict(key='pointers-new', stage=STAGE, title='Pointers, new, new(expr) and addressability',
body=[
'&x takes the address of a variable and *p reads or writes through a pointer. Go has no pointer arithmetic outside package unsafe. Taking the address of a local variable is safe: if the pointer outlives the function, the compiler moves the variable to the heap (escape analysis).',
'new(T) allocates a zero T and returns *T. Since Go 1.26, new also accepts an expression: new(42) or new(time.Now()) allocates a variable initialised to that value. This removes small helper functions written only to get a pointer to a constant, common with optional fields.',
'Composite literals are addressable through &: &Point{1, 2} is idiomatic. Map elements are not addressable (&m[k] is a compile error) because a map may move its entries as it grows. The field selector p.X automatically dereferences a pointer to a struct.',
],
code=r'''package main

import "fmt"

type Config struct {
    Retries *int
}

type Point struct{ X, Y int }

func double(n *int) { *n *= 2 }

func main() {
    x := 21
    double(&x)
    fmt.Println(x)
    c := Config{Retries: new(3)}
    fmt.Println(*c.Retries)
    p := &Point{1, 2}
    p.X = 10
    fmt.Println(*p)
    var nothing *int
    fmt.Println(nothing == nil)
}
''',
expectedStdout='42\n3\n{10 2}\ntrue\n',
challenge='Write func swap(a, b *int) and use it to swap two variables holding 1 and 2; print them.',
solution=r'''package main

import "fmt"

func swap(a, b *int) {
    *a, *b = *b, *a
}

func main() {
    x, y := 1, 2
    swap(&x, &y)
    fmt.Println(x, y)
}
''',
solutionStdout='2 1\n',
question='Why is &m["k"] a compile error?',
correct='Map elements are not addressable because the map may relocate them',
wrong=['Strings cannot be map keys', 'The & operator only applies to struct fields'],
reasoning='Growing a map rehashes and moves entries, so a pointer to an element could dangle. Store pointers as values (map[string]*T) if you need shared mutable elements.',
rejections=[dict(source='package main\n\nfunc main() {\n\tm := map[string]int{"k": 1}\n\tp := &m["k"]\n\t_ = p\n}\n', diagnostic='cannot take address of m["k"]')],
sourceURL='https://go.dev/doc/go1.26#language',
additionalReadings=[dict(title='Allocation with new', url=SPEC+'#Allocation', section='new')]),

dict(key='struct-literal-selectors', stage=STAGE, title='Go 1.27 struct literals with promoted field keys',
body=[
'Before Go 1.27, a struct literal could only name the struct\'s own top-level fields. To set a field promoted from an embedded struct, you had to spell the nesting: Named{Point: Point{X: 1}}.',
'Go 1.27 lets a key be any valid field selector for the struct type, so Named{X: 1, Name: "a"} sets the promoted X directly. The embedded struct is still a real field; the literal is shorthand for initialising inside it.',
'This only works when the selector is unambiguous and does not pass through an embedded pointer, which could be nil. Older modules with a go line below 1.27 reject the shorter form, so the go directive matters for which literals compile.',
],
code=r'''package main

import "fmt"

type Point struct{ X, Y int }

type Named struct {
    Point
    Name string
}

func main() {
    n := Named{X: 3, Y: 4, Name: "p"}
    fmt.Println(n.Point, n.Name)
}
''',
expectedStdout='{3 4} p\n',
challenge='Embed type Meta struct{ ID int } in type Doc struct{ Meta; Title string } and build a Doc with ID 7 and title "go" using the 1.27 promoted-key form; print it with %+v.',
solution=r'''package main

import "fmt"

type Meta struct{ ID int }

type Doc struct {
    Meta
    Title string
}

func main() {
    d := Doc{ID: 7, Title: "go"}
    fmt.Printf("%+v\n", d)
}
''',
solutionStdout='{Meta:{ID:7} Title:go}\n',
question='What does Named{X: 3} mean under Go 1.27 when Named embeds Point?',
correct='It initialises the promoted field Named.Point.X',
wrong=['It declares a new field X on Named', 'It is still a compile error'],
reasoning='The 1.27 rule allows any valid field selector as a key. X selects the promoted field inside the embedded Point.',
sourceURL='https://go.dev/doc/go1.27#language',
additionalReadings=[dict(title='Composite literals', url=SPEC+'#Composite_literals', section='Struct keys')]),

dict(key='copy-clear-min-max', stage=STAGE, title='Built-ins: len, cap, copy, clear, min and max',
body=[
'copy(dst, src) copies min(len(dst), len(src)) elements and returns that count; it handles overlapping slices correctly. It also copies bytes from a string into a []byte.',
'clear (Go 1.21) deletes every entry from a map, or sets every element of a slice to its zero value without changing its length. Clearing is how to reuse a map without reallocating.',
'min and max (Go 1.21) are built-ins for any ordered type and take one or more arguments. For floats, if any argument is NaN the result is NaN. They work with constants at compile time too.',
],
code=r'''package main

import "fmt"

func main() {
    dst := make([]int, 2)
    n := copy(dst, []int{7, 8, 9})
    fmt.Println(n, dst)
    m := map[string]int{"a": 1, "b": 2}
    clear(m)
    s := []int{1, 2, 3}
    clear(s)
    fmt.Println(len(m), s, len(s))
    fmt.Println(min(3, 1, 2), max("go", "gopher"), max(2.5, 1))
}
''',
expectedStdout='2 [7 8]\n0 [0 0 0] 3\n1 gopher 2.5\n',
challenge='Shift the elements of []int{1, 2, 3, 4} one place left in place with copy, then set the last element to 0; print the slice.',
solution=r'''package main

import "fmt"

func main() {
    s := []int{1, 2, 3, 4}
    copy(s, s[1:])
    s[len(s)-1] = 0
    fmt.Println(s)
}
''',
solutionStdout='[2 3 4 0]\n',
question='What does clear(s) do to a slice s?',
correct='Zeroes every element; the length is unchanged',
wrong=['Sets the length to zero', 'Frees the backing array'],
reasoning='clear on a slice zeroes elements up to len(s). For a map, clear removes all entries. Use s = s[:0] to reset a slice\'s length.',
sourceURL=SPEC+'#Built-in_functions'),
]

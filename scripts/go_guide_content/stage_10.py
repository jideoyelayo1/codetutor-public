STAGE = '10 · Iterators'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='range-over-func', stage=STAGE, title='Range-over-func iterators: iter.Seq and iter.Seq2',
body=[
'Since Go 1.23, for range accepts functions. An iter.Seq[V] is func(yield func(V) bool), and iter.Seq2[K, V] is func(yield func(K, V) bool). The loop body becomes the yield function; the iterator calls it once per element.',
'yield returns false when the loop stops early with break or return. The iterator must then stop and must not call yield again, otherwise the program panics. Write iterators as: for ... { if !yield(v) { return } }.',
'Iterators are lazy: nothing happens until a loop or a consumer such as slices.Collect pulls values. They let collections expose traversal without allocating a slice, and let infinite sequences, such as Fibonacci numbers, be consumed in bounded amounts.',
],
code=r'''package main

import (
    "fmt"
    "iter"
)

func Fib() iter.Seq[int] {
    return func(yield func(int) bool) {
        a, b := 0, 1
        for {
            if !yield(a) {
                return
            }
            a, b = b, a+b
        }
    }
}

func Enumerate[T any](xs []T) iter.Seq2[int, T] {
    return func(yield func(int, T) bool) {
        for i, x := range xs {
            if !yield(i+1, x) {
                return
            }
        }
    }
}

func main() {
    for n := range Fib() {
        if n > 20 {
            break
        }
        fmt.Print(n, " ")
    }
    fmt.Println()
    for i, s := range Enumerate([]string{"go", "iter"}) {
        fmt.Println(i, s)
    }
}
''',
expectedStdout='0 1 1 2 3 5 8 13 \n1 go\n2 iter\n',
challenge='Write func Countdown(n int) iter.Seq[int] yielding n down to 1, and print the values from Countdown(3) on one line.',
solution=r'''package main

import (
    "fmt"
    "iter"
)

func Countdown(n int) iter.Seq[int] {
    return func(yield func(int) bool) {
        for i := n; i > 0; i-- {
            if !yield(i) {
                return
            }
        }
    }
}

func main() {
    for v := range Countdown(3) {
        fmt.Print(v, " ")
    }
    fmt.Println()
}
''',
solutionStdout='3 2 1 \n',
question='What must an iterator do when yield returns false?',
correct='Stop immediately and never call yield again',
wrong=['Restart from the first element', 'Keep yielding but the loop ignores the values'],
reasoning='false means the loop body executed break or return. Calling yield after that panics at run time.',
sourceURL='https://go.dev/blog/range-functions',
additionalReadings=[dict(title='iter package', url='https://pkg.go.dev/iter', section='Seq and Seq2')]),

dict(key='iter-pull', stage=STAGE, title='Pull iterators with iter.Pull and cleanup',
body=[
'A push iterator calls your code. Sometimes you need to pull values one at a time, for example to merge two sorted sequences. iter.Pull(seq) returns next() (V, bool) and stop(). Each next call resumes the iterator until it yields one value.',
'Always call stop when you finish early, usually with defer stop(). stop ends the iterator and lets its deferred cleanup run. Forgetting it leaks the iterator\'s state.',
'Iterators may also need to release resources, such as files, when the consumer breaks early. Put the cleanup in a defer inside the iterator function: it runs whether the loop finishes, breaks, or the pull iterator is stopped.',
],
code=r'''package main

import (
    "fmt"
    "iter"
    "slices"
)

func Merge(a, b iter.Seq[int]) iter.Seq[int] {
    return func(yield func(int) bool) {
        nextA, stopA := iter.Pull(a)
        defer stopA()
        nextB, stopB := iter.Pull(b)
        defer stopB()
        x, okA := nextA()
        y, okB := nextB()
        for okA || okB {
            if okA && (!okB || x <= y) {
                if !yield(x) {
                    return
                }
                x, okA = nextA()
            } else {
                if !yield(y) {
                    return
                }
                y, okB = nextB()
            }
        }
    }
}

func main() {
    merged := Merge(slices.Values([]int{1, 4, 9}), slices.Values([]int{2, 3, 10}))
    fmt.Println(slices.Collect(merged))
}
''',
expectedStdout='[1 2 3 4 9 10]\n',
challenge='Write an iterator that prints "open" when started, yields 1, 2, 3, and prints "closed" in a defer; consume it with a loop that breaks after the first value and show that "closed" is printed.',
solution=r'''package main

import (
    "fmt"
    "iter"
)

func Resource() iter.Seq[int] {
    return func(yield func(int) bool) {
        fmt.Println("open")
        defer fmt.Println("closed")
        for i := 1; i <= 3; i++ {
            if !yield(i) {
                return
            }
        }
    }
}

func main() {
    for v := range Resource() {
        fmt.Println("got", v)
        break
    }
}
''',
solutionStdout='open\ngot 1\nclosed\n',
question='Why defer stop() after iter.Pull?',
correct='So the iterator ends and runs its cleanup even if you stop pulling early',
wrong=['next panics unless stop is deferred', 'stop rewinds the iterator for reuse'],
reasoning='A pulled iterator is suspended mid-loop. stop resumes it with yield returning false so its deferred cleanup runs.',
sourceURL='https://pkg.go.dev/iter#Pull'),

dict(key='slices-maps-iterators', stage=STAGE, title='Iterator helpers in slices, maps and strings',
body=[
'slices.All, slices.Values and slices.Backward produce iterators over a slice; slices.Collect, slices.AppendSeq and slices.Sorted consume them. maps.Keys, maps.Values and maps.All iterate a map; maps.Collect builds one from an iter.Seq2.',
'Since Go 1.24 strings and bytes offer iterator versions of splitting: strings.Lines, strings.SplitSeq, strings.FieldsSeq and strings.FieldsFuncSeq. They avoid allocating the whole []string when you only scan.',
'Chaining is explicit and still lazy: slices.Sorted(maps.Keys(m)) collects only once. There is no built-in Map or Filter over iterators in the standard library; writing them is a few lines with iter.Seq.',
],
code=r'''package main

import (
    "fmt"
    "maps"
    "slices"
    "strings"
)

func main() {
    for i, v := range slices.Backward([]string{"a", "b", "c"}) {
        fmt.Print(i, v, " ")
    }
    fmt.Println()
    stock := map[string]int{"pear": 3, "apple": 5}
    fmt.Println(slices.Sorted(maps.Keys(stock)))
    for line := range strings.Lines("one\ntwo\n") {
        fmt.Printf("%q ", line)
    }
    fmt.Println()
    for part := range strings.SplitSeq("a,b,c", ",") {
        fmt.Print(part)
    }
    fmt.Println()
}
''',
expectedStdout='2c 1b 0a \n[apple pear]\n"one\\n" "two\\n" \nabc\n',
challenge='Write a generic Filter[V any](seq iter.Seq[V], keep func(V) bool) iter.Seq[V] and use it with slices.Values and slices.Collect to keep the even numbers of []int{1, 2, 3, 4}.',
solution=r'''package main

import (
    "fmt"
    "iter"
    "slices"
)

func Filter[V any](seq iter.Seq[V], keep func(V) bool) iter.Seq[V] {
    return func(yield func(V) bool) {
        for v := range seq {
            if keep(v) && !yield(v) {
                return
            }
        }
    }
}

func main() {
    even := Filter(slices.Values([]int{1, 2, 3, 4}), func(n int) bool { return n%2 == 0 })
    fmt.Println(slices.Collect(even))
}
''',
solutionStdout='[2 4]\n',
question='What does strings.Lines yield for "one\\ntwo\\n"?',
correct='"one\\n" and "two\\n", keeping each newline',
wrong=['"one" and "two" without newlines', '"one", "two" and a final empty string'],
reasoning='Lines yields each line including its terminating newline, so rejoining them reproduces the input exactly.',
sourceURL='https://pkg.go.dev/strings#Lines',
additionalReadings=[dict(title='slices iterator functions', url='https://pkg.go.dev/slices#All', section='All, Values, Backward, Collect, Sorted')]),

dict(key='iterator-design', stage=STAGE, title='Designing collection APIs with iterators',
body=[
'A collection type exposes traversal by returning an iterator from a method: func (t *Tree[T]) All() iter.Seq[T]. Callers loop with for v := range t.All() and can stop early without the type allocating a slice.',
'Recursive structures fit naturally: an in-order traversal yields left, node, right, and propagates a false yield upward so the whole walk stops. Return false from your helper when yield does, and check it at every level.',
'Document whether an iterator can be used more than once and whether the collection may change during iteration. Single-use iterators, such as those reading a stream, should say so in their doc comment.',
],
code=r'''package main

import (
    "cmp"
    "fmt"
    "iter"
)

type Tree[T cmp.Ordered] struct {
    root *node[T]
}

type node[T cmp.Ordered] struct {
    v           T
    left, right *node[T]
}

func (t *Tree[T]) Insert(v T) {
    p := &t.root
    for *p != nil {
        if v < (*p).v {
            p = &(*p).left
        } else {
            p = &(*p).right
        }
    }
    *p = &node[T]{v: v}
}

func (t *Tree[T]) All() iter.Seq[T] {
    return func(yield func(T) bool) { t.root.walk(yield) }
}

func (n *node[T]) walk(yield func(T) bool) bool {
    if n == nil {
        return true
    }
    return n.left.walk(yield) && yield(n.v) && n.right.walk(yield)
}

func main() {
    var t Tree[int]
    for _, v := range []int{5, 2, 8, 1, 9} {
        t.Insert(v)
    }
    for v := range t.All() {
        if v > 5 {
            break
        }
        fmt.Print(v, " ")
    }
    fmt.Println()
}
''',
expectedStdout='1 2 5 \n',
challenge='Add a method Backward() iter.Seq[T] to Tree that yields values in descending order, and print all values of the tree above in that order.',
solution=r'''package main

import (
    "cmp"
    "fmt"
    "iter"
)

type Tree[T cmp.Ordered] struct {
    root *node[T]
}

type node[T cmp.Ordered] struct {
    v           T
    left, right *node[T]
}

func (t *Tree[T]) Insert(v T) {
    p := &t.root
    for *p != nil {
        if v < (*p).v {
            p = &(*p).left
        } else {
            p = &(*p).right
        }
    }
    *p = &node[T]{v: v}
}

func (t *Tree[T]) Backward() iter.Seq[T] {
    return func(yield func(T) bool) { t.root.back(yield) }
}

func (n *node[T]) back(yield func(T) bool) bool {
    if n == nil {
        return true
    }
    return n.right.back(yield) && yield(n.v) && n.left.back(yield)
}

func main() {
    var t Tree[int]
    for _, v := range []int{5, 2, 8, 1, 9} {
        t.Insert(v)
    }
    for v := range t.Backward() {
        fmt.Print(v, " ")
    }
    fmt.Println()
}
''',
solutionStdout='9 8 5 2 1 \n',
question='Why does walk return a bool?',
correct='To stop the whole recursive traversal once yield returns false',
wrong=['To report whether the tree is empty', 'Because iter.Seq requires helpers to return bool'],
reasoning='After the consumer breaks, every level must stop. The && chain short-circuits as soon as any call reports false.',
sourceURL='https://go.dev/blog/range-functions'),
]

STAGE = '03 · Control flow and functions'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='if-and-for', stage=STAGE, title='if with init statements and the single for loop',
body=[
'if needs no parentheses but always needs braces. An if can start with a short statement: if v, ok := m[k]; ok { ... }. Variables declared there are scoped to the if and its else branches, which keeps temporary values out of the surrounding function.',
'for is Go\'s only loop. It has three forms: the C-style for i := 0; i < n; i++, the condition-only for cond (a while loop), and the infinite for { } that ends with break or return.',
'Since Go 1.22 you can range over an integer: for i := range 5 runs i = 0..4. Use it when you only need a count; it removes off-by-one mistakes in the condition.',
],
code=r'''package main

import "fmt"

func main() {
    for i := range 3 {
        fmt.Print(i, " ")
    }
    fmt.Println()
    n := 10
    for n > 1 {
        n /= 2
    }
    fmt.Println(n)
    if r := 17 % 5; r > 1 {
        fmt.Println("remainder", r)
    } else {
        fmt.Println("small", r)
    }
}
''',
expectedStdout='0 1 2 \n1\nremainder 2\n',
challenge='Count the Collatz steps for 6 (halve when even, 3n+1 when odd) until it reaches 1; print the count.',
solution=r'''package main

import "fmt"

func main() {
    n, steps := 6, 0
    for n != 1 {
        if n%2 == 0 {
            n /= 2
        } else {
            n = 3*n + 1
        }
        steps++
    }
    fmt.Println(steps)
}
''',
solutionStdout='8\n',
question='Where is a variable declared in if v := f(); v > 0 { } visible?',
correct='In the condition, the if block and any else blocks',
wrong=['For the rest of the function', 'Only inside the if block'],
reasoning='The init statement opens an implicit scope covering the whole if/else chain and ending after it.',
sourceURL=SPEC+'#For_statements',
additionalReadings=[dict(title='Range over integers (Go 1.22)', url='https://go.dev/doc/go1.22#language', section='Range over int')]),

dict(key='switch', stage=STAGE, title='switch: no fallthrough by default, tagless switch',
body=[
'A switch compares a value against cases from top to bottom and runs the first match. Unlike C, a case ends without break; the explicit fallthrough keyword continues into the next case body without testing it. A case may list several values: case "sat", "sun":.',
'A switch with no tag is a cleaner if/else-if chain: each case is a boolean expression. Like if, switch accepts an init statement before the tag.',
'break inside a switch leaves the switch, not an enclosing loop. To leave a loop from inside a switch, label the loop and use break Label.',
],
code=r'''package main

import "fmt"

func kind(day string) string {
    switch day {
    case "sat", "sun":
        return "weekend"
    default:
        return "weekday"
    }
}

func grade(score int) string {
    switch {
    case score >= 90:
        return "A"
    case score >= 75:
        return "B"
    }
    return "C"
}

func main() {
    fmt.Println(kind("sun"), kind("tue"))
    fmt.Println(grade(95), grade(80), grade(10))
    switch x := 1; x {
    case 1:
        fmt.Println("one")
        fallthrough
    case 2:
        fmt.Println("two (via fallthrough)")
    }
}
''',
expectedStdout='weekend weekday\nA B C\none\ntwo (via fallthrough)\n',
challenge='Write a tagless switch that prints "fizzbuzz", "fizz", "buzz" or the number for 1 to 15, all on one line separated by spaces.',
solution=r'''package main

import (
    "fmt"
    "strconv"
    "strings"
)

func main() {
    var out []string
    for i := 1; i <= 15; i++ {
        switch {
        case i%15 == 0:
            out = append(out, "fizzbuzz")
        case i%3 == 0:
            out = append(out, "fizz")
        case i%5 == 0:
            out = append(out, "buzz")
        default:
            out = append(out, strconv.Itoa(i))
        }
    }
    fmt.Println(strings.Join(out, " "))
}
''',
solutionStdout='1 2 fizz 4 buzz fizz 7 8 fizz buzz 11 fizz 13 14 fizzbuzz\n',
question='What does break do inside a switch that is inside a for loop?',
correct='It leaves only the switch; use a labelled break to leave the loop',
wrong=['It leaves the loop', 'It is a compile error'],
reasoning='break targets the innermost for, switch or select. A label names the outer statement explicitly.',
sourceURL=SPEC+'#Switch_statements'),

dict(key='labels-break-continue', stage=STAGE, title='Labels, break, continue and goto',
body=[
'A label names a statement: outer: for .... break outer leaves that loop and continue outer starts its next iteration. Labels are the clear way to exit nested loops, for example after finding a match in a grid.',
'goto jumps to a label in the same function. It cannot jump over variable declarations or into a block. It is legal but rare; generated code and a few error-cleanup paths use it.',
'Unused labels are compile errors, like unused variables. A labelled continue is usually clearer than a flag variable checked after the inner loop.',
],
code=r'''package main

import "fmt"

func main() {
    grid := [][]int{{1, 2}, {3, 4}, {5, 6}}
    target := 4
outer:
    for r, row := range grid {
        for c, v := range row {
            if v == target {
                fmt.Println("found at", r, c)
                break outer
            }
        }
    }
    fmt.Println("done")
}
''',
expectedStdout='found at 1 1\ndone\n',
challenge='Print every pair (i, j) with 0 <= i, j < 3 except that when j == i you skip the rest of that row with continue outer.',
solution=r'''package main

import "fmt"

func main() {
outer:
    for i := range 3 {
        for j := range 3 {
            if j == i {
                continue outer
            }
            fmt.Println(i, j)
        }
    }
}
''',
solutionStdout='1 0\n2 0\n2 1\n',
question='Which statement starts the next iteration of an enclosing loop labelled outer?',
correct='continue outer',
wrong=['break outer', 'goto outer'],
reasoning='continue with a label applies to that labelled for statement. break outer would leave it, and goto outer would restart the loop from its initialisation.',
rejections=[dict(source='package main\n\nfunc main() {\nunused:\n\tfor {\n\t\tbreak\n\t}\n}\n', diagnostic='label unused defined and not used')],
sourceURL=SPEC+'#Labeled_statements'),

dict(key='functions-multiple-results', stage=STAGE, title='Functions, multiple results and named results',
body=[
'A function declares typed parameters and results: func divmod(a, b int) (int, int). Consecutive parameters of one type can share it. Arguments are passed by value: the function receives copies, so to let it change the caller\'s variable you pass a pointer.',
'Returning several values is idiomatic, especially (result, error) and (value, ok). The blank identifier _ discards a result you do not need. Every result must be received or explicitly discarded.',
'Results can be named. Named results start as zero values and a bare return returns their current values. Use them for short functions or for documentation; in long functions bare returns hide what is being returned.',
],
code=r'''package main

import "fmt"

func divmod(a, b int) (q, r int) {
    q = a / b
    r = a % b
    return
}

func minMax(xs ...int) (lo, hi int) {
    lo, hi = xs[0], xs[0]
    for _, x := range xs[1:] {
        lo, hi = min(lo, x), max(hi, x)
    }
    return lo, hi
}

func main() {
    q, r := divmod(17, 5)
    fmt.Println(q, r)
    _, hi := minMax(4, 9, 1)
    fmt.Println(hi)
}
''',
expectedStdout='3 2\n9\n',
challenge='Write func parsePair(s string) (string, string, bool) that splits "k=v" on the first "=" and reports whether it succeeded; print the results for "a=b" and "ab".',
solution=r'''package main

import (
    "fmt"
    "strings"
)

func parsePair(s string) (string, string, bool) {
    k, v, ok := strings.Cut(s, "=")
    return k, v, ok
}

func main() {
    fmt.Println(parsePair("a=b"))
    fmt.Println(parsePair("ab"))
}
''',
solutionStdout='a b true\nab  false\n',
question='What does a bare return do in a function with named results?',
correct='Returns the current values of the named result variables',
wrong=['Returns zero values regardless of assignments', 'Is only allowed in functions with no results'],
reasoning='Named results are ordinary local variables initialised to zero. A bare return returns whatever they hold at that moment, including changes made by deferred functions.',
sourceURL=SPEC+'#Function_declarations',
additionalReadings=[dict(title='Effective Go: multiple return values', url='https://go.dev/doc/effective_go#multiple-returns', section='Named result parameters')]),

dict(key='variadic-and-function-values', stage=STAGE, title='Variadic functions and functions as values',
body=[
'A final parameter ...T accepts any number of T values and receives them as a []T. A caller can pass an existing slice with s..., which passes the slice itself without copying, so the function can see and modify the caller\'s elements.',
'Functions are values with types such as func(int) int. They can be stored in variables, maps and struct fields, passed as arguments and returned. The zero value of a function type is nil, and calling a nil function panics.',
'Function values compare only to nil. Passing behaviour as a function is often simpler than defining a one-method interface, and the sort and slices packages accept comparison functions this way.',
],
code=r'''package main

import (
    "fmt"
    "strings"
)

func apply(xs []string, f func(string) string) []string {
    out := make([]string, 0, len(xs))
    for _, x := range xs {
        out = append(out, f(x))
    }
    return out
}

func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

func main() {
    fmt.Println(apply([]string{"go", "gopher"}, strings.ToUpper))
    fmt.Println(sum(), sum(1, 2, 3))
    nums := []int{4, 5}
    fmt.Println(sum(nums...))
}
''',
expectedStdout='[GO GOPHER]\n0 6\n9\n',
challenge='Build a map from operator strings "+", "-", "*" to func(int, int) int and print the result of each on 6 and 3, in that order.',
solution=r'''package main

import "fmt"

func main() {
    ops := map[string]func(int, int) int{
        "+": func(a, b int) int { return a + b },
        "-": func(a, b int) int { return a - b },
        "*": func(a, b int) int { return a * b },
    }
    for _, op := range []string{"+", "-", "*"} {
        fmt.Println(op, ops[op](6, 3))
    }
}
''',
solutionStdout='+ 9\n- 3\n* 18\n',
question='What does a variadic function receive when called as f(s...)?',
correct='The caller\'s slice itself, sharing its backing array',
wrong=['A fresh copy of the slice', 'Each element as a separate parameter'],
reasoning='s... passes the slice header unchanged, so writes to elements are visible to the caller. Calling f(a, b) instead builds a new slice.',
sourceURL=SPEC+'#Passing_arguments_to_..._parameters'),

dict(key='closures-loop-variables', stage=STAGE, title='Closures and per-iteration loop variables',
body=[
'A function literal can refer to variables of the enclosing function; it captures the variables themselves, not copies of their values. A counter generator returns a closure that keeps its own count alive after the outer function returns. The captured variable then lives on the heap.',
'Before Go 1.22, a for loop had one variable shared by all iterations, so closures created in the loop all saw its final value. Since Go 1.22, in modules whose go line is 1.22 or later, each iteration of a 3-clause or range loop gets a fresh variable. This guide targets go 1.27, so each closure sees its own iteration value.',
'Closures make small strategies and callbacks easy, but capturing a variable that another goroutine also writes is a data race. Pass values as arguments when in doubt.',
],
code=r'''package main

import "fmt"

func counter() func() int {
    n := 0
    return func() int {
        n++
        return n
    }
}

func main() {
    next := counter()
    next()
    next()
    fmt.Println(next())
    var prints []func()
    for i := range 3 {
        prints = append(prints, func() { fmt.Print(i, " ") })
    }
    for _, p := range prints {
        p()
    }
    fmt.Println()
}
''',
expectedStdout='3\n0 1 2 \n',
challenge='Write func adder(start int) func(int) int that returns a closure accumulating a running total; print the results of adding 5, then 10, to adder(1).',
solution=r'''package main

import "fmt"

func adder(start int) func(int) int {
    total := start
    return func(x int) int {
        total += x
        return total
    }
}

func main() {
    add := adder(1)
    fmt.Println(add(5))
    fmt.Println(add(10))
}
''',
solutionStdout='6\n16\n',
question='With go 1.27 in go.mod, what do closures created in for i := range 3 capture?',
correct='A distinct i for each iteration, so they see 0, 1 and 2',
wrong=['One shared i, so they all see 3', 'A copy of i taken when the closure is called'],
reasoning='Go 1.22 made loop variables per-iteration for modules declaring go 1.22 or later. The closures capture variables, but each iteration has its own.',
sourceURL='https://go.dev/blog/loopvar-preview',
additionalReadings=[dict(title='Function literals', url=SPEC+'#Function_literals', section='Closures')]),

dict(key='defer-basics', stage=STAGE, title='defer: cleanup that runs on every return path',
body=[
'defer schedules a function call to run when the surrounding function returns, whether by return, reaching the end, or a panic. Deferred calls run in last-in, first-out order, which matches acquiring resources in order and releasing them in reverse.',
'The arguments of a deferred call are evaluated when the defer statement runs, not when the call happens. defer fmt.Println(i) prints the value i had at that moment. A deferred closure that reads i instead sees its final value.',
'The common pattern is acquire, check the error, then defer the release: f, err := os.Open(p); if err != nil { return err }; defer f.Close(). A defer inside a loop does not run until the function returns, so a loop that opens many files should call a helper function per item.',
],
code=r'''package main

import "fmt"

func main() {
    for i := range 3 {
        defer fmt.Println("deferred", i)
    }
    x := 1
    defer fmt.Println("argument evaluated early:", x)
    defer func() { fmt.Println("closure sees:", x) }()
    x = 2
    fmt.Println("body done")
}
''',
expectedStdout='body done\nclosure sees: 2\nargument evaluated early: 1\ndeferred 2\ndeferred 1\ndeferred 0\n',
challenge='Write func trace(name string) func() that prints "enter name" and returns a function printing "exit name"; use it as defer trace("work")() and print "working" in between.',
solution=r'''package main

import "fmt"

func trace(name string) func() {
    fmt.Println("enter", name)
    return func() { fmt.Println("exit", name) }
}

func work() {
    defer trace("work")()
    fmt.Println("working")
}

func main() {
    work()
}
''',
solutionStdout='enter work\nworking\nexit work\n',
question='When are the arguments of a deferred function call evaluated?',
correct='When the defer statement executes',
wrong=['When the surrounding function returns', 'Lazily, the first time the call reads them'],
reasoning='defer evaluates the function value and its arguments immediately and saves them; only the call is postponed.',
sourceURL=SPEC+'#Defer_statements',
additionalReadings=[dict(title='Defer, Panic, and Recover', url='https://go.dev/blog/defer-panic-and-recover', section='Three rules of defer')]),
]

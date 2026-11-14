STAGE = '02 · Values and types'
SPEC = 'https://go.dev/ref/spec'

LESSONS = [
dict(key='variables-zero-values', stage=STAGE, title='Variables, short declarations and zero values',
body=[
'var name Type declares a variable and sets it to the zero value of its type: 0 for numbers, false for bool, "" for string, and nil for pointers, slices, maps, channels, functions and interfaces. There is no uninitialised memory in Go; every variable always holds a valid value of its type.',
'Inside a function, x := expr declares and initialises in one step, inferring the type from the expression. := needs at least one new variable on its left. In a new scope it creates a new variable even if an outer one has the same name; this is called shadowing and is a common source of bugs with err.',
'Declarations can be grouped in var ( ... ) blocks, and several variables can be declared at once: a, b := 1, 2. Swapping is a single statement, a, b = b, a, because all right-hand values are evaluated before any assignment happens.',
],
code=r'''package main

import "fmt"

func main() {
    var count int
    var label string
    var ready bool
    fmt.Printf("%d %q %t\n", count, label, ready)
    a, b := 1, 2
    a, b = b, a
    fmt.Println(a, b)
}
''',
expectedStdout='0 "" false\n2 1\n',
challenge='Declare x := 1, then in an inner block write x := 2 and print it; print x again after the block. Predict both lines first.',
solution=r'''package main

import "fmt"

func main() {
    x := 1
    {
        x := 2
        fmt.Println(x)
    }
    fmt.Println(x)
}
''',
solutionStdout='2\n1\n',
question='What value does a newly declared var m map[string]int hold?',
correct='nil: reads work and return zero, but writes panic',
wrong=['An empty, ready-to-use map', 'Uninitialised memory until make is called'],
reasoning='The zero value of a map is nil. Looking up a key in a nil map returns the zero value, but assigning to one panics, so maps are made with make or a literal before writing.',
sourceURL=SPEC+'#The_zero_value',
additionalReadings=[dict(title='Short variable declarations', url=SPEC+'#Short_variable_declarations', section='Redeclaration and scope')]),

dict(key='constants-iota', stage=STAGE, title='Constants, untyped constants and iota',
body=[
'A constant is a compile-time value: const Pi = 3.14159. Constants can be typed (const Max int = 10) or untyped. An untyped constant has arbitrary precision and takes a type only when it is used, so const Big = 1 << 100 is legal as long as it is never stored in a type too small for it.',
'Inside a const block, iota counts from 0 and increases by one per line. An omitted expression repeats the previous one, so a block of enumerated values needs iota only on its first line. Expressions such as 1 << iota build bit flags.',
'Go has no enum keyword. The idiom is a named integer type with iota constants and a String method for printing. A named type stops values of one enumeration from being mixed with plain integers by accident.',
],
code=r'''package main

import "fmt"

type Weekday int

const (
    Sunday Weekday = iota
    Monday
    Tuesday
)

const (
    Read = 1 << iota
    Write
    Exec
)

func main() {
    fmt.Println(Sunday, Monday, Tuesday)
    fmt.Println(Read, Write, Exec, Read|Exec)
    const huge = 1 << 100
    fmt.Println(huge >> 98)
}
''',
expectedStdout='0 1 2\n1 2 4 5\n4\n',
challenge='Define byte-size constants KB, MB and GB with iota so that KB = 1 << 10, then print MB.',
solution=r'''package main

import "fmt"

const (
    _  = iota
    KB = 1 << (10 * iota)
    MB
    GB
)

func main() {
    fmt.Println(MB)
}
''',
solutionStdout='1048576\n',
question='Why does const huge = 1 << 100 compile even though no integer type can hold it?',
correct='Untyped constants have arbitrary precision until converted to a type',
wrong=['The compiler silently wraps it to zero', 'Constants are always float64'],
reasoning='Untyped constant arithmetic is exact. It only fails if the value is used where it must fit a concrete type, such as assigning huge to an int.',
rejections=[dict(source='package main\n\nimport "fmt"\n\nfunc main() {\n\tconst huge = 1 << 100\n\tvar n int = huge\n\tfmt.Println(n)\n}\n', diagnostic='as int value in variable declaration (overflows)')],
sourceURL=SPEC+'#Iota',
additionalReadings=[dict(title='Constants (Go blog)', url='https://go.dev/blog/constants', section='Untyped constants')]),

dict(key='numeric-types', stage=STAGE, title='Integers, floats, overflow and explicit conversion',
body=[
'Go has sized integers (int8 to int64, uint8 to uint64), int and uint (64 bits on current 64-bit platforms), uintptr, float32/float64 and complex64/complex128. byte is an alias for uint8 and rune is an alias for int32.',
'Go never converts between numeric types implicitly. Adding an int and a float64 is a compile error until you write float64(n). Converting a float to an integer truncates toward zero; converting to a smaller integer type keeps the low bits.',
'Integer arithmetic wraps on overflow with no error: an int8 holding 127 plus one becomes -128. Integer division truncates toward zero, and % keeps the sign of the dividend. Dividing an integer by a constant zero is a compile error; dividing by a variable that is zero panics at run time. Floating-point division by zero gives ±Inf or NaN.',
],
code=r'''package main

import "fmt"

func main() {
    var small int8 = 127
    small++
    fmt.Println(small)
    n, f := 7, 2.5
    fmt.Println(float64(n) * f)
    neg := -3.9
    fmt.Println(-7/2, -7%2, int(neg))
    var big int32 = 300
    fmt.Println(uint8(big))
}
''',
expectedStdout='-128\n17.5\n-3 -1 -3\n44\n',
challenge='Compute the average of the integers 3, 4 and 4 as a float64 and print it with two decimals.',
solution=r'''package main

import "fmt"

func main() {
    sum := 3 + 4 + 4
    avg := float64(sum) / 3
    fmt.Printf("%.2f\n", avg)
}
''',
solutionStdout='3.67\n',
question='What happens when int and float64 values are added directly?',
correct='A compile error; one operand must be converted explicitly',
wrong=['The int is promoted to float64', 'The float is truncated to int'],
reasoning='Go has no implicit numeric conversions between variables of different types. Untyped constants are flexible; typed variables are not.',
rejections=[dict(source='package main\n\nimport "fmt"\n\nfunc main() {\n\tn, f := 7, 2.5\n\tfmt.Println(n * f)\n}\n', diagnostic='mismatched types int and float64')],
sourceURL=SPEC+'#Numeric_types',
additionalReadings=[dict(title='Conversions', url=SPEC+'#Conversions', section='Conversions between numeric types')]),

dict(key='strings-bytes-runes', stage=STAGE, title='Strings, bytes, runes and UTF-8',
body=[
'A Go string is an immutable sequence of bytes, conventionally UTF-8. len(s) counts bytes, not characters, and s[i] is a byte. Indexing never decodes text; "é" occupies two bytes.',
'A rune is a Unicode code point (an int32). Ranging over a string with for i, r := range s decodes UTF-8 and yields the byte offset and rune of each character. Invalid bytes decode as the replacement character U+FFFD. utf8.RuneCountInString counts code points.',
'Converting a string to []byte or []rune copies it. Building strings by repeated + allocates a new string each time; use strings.Builder for loops. Raw string literals in backquotes keep backslashes and newlines literally, which suits regular expressions and multi-line text.',
],
code=r'''package main

import (
    "fmt"
    "unicode/utf8"
)

func main() {
    s := "héllo"
    fmt.Println(len(s), utf8.RuneCountInString(s))
    for i, r := range "hé!" {
        fmt.Println(i, string(r))
    }
    fmt.Println(s[1] == 0xc3)
    fmt.Println(`a\nb`)
}
''',
expectedStdout='6 5\n0 h\n1 é\n3 !\ntrue\na\\nb\n',
challenge='Reverse the string "Go→é" by runes (not bytes) and print it.',
solution=r'''package main

import "fmt"

func main() {
    r := []rune("Go→é")
    for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    fmt.Println(string(r))
}
''',
solutionStdout='é→oG\n',
question='What does len("é") return?',
correct='2, because len counts the UTF-8 bytes',
wrong=['1, because it counts characters', '4, because runes are int32'],
reasoning='Strings are byte sequences. "é" (U+00E9) is encoded in UTF-8 as two bytes, 0xC3 0xA9.',
sourceURL='https://go.dev/blog/strings',
additionalReadings=[dict(title='String types', url=SPEC+'#String_types', section='Strings')]),

dict(key='operators-precedence', stage=STAGE, title='Operators, precedence and bit manipulation',
body=[
'Go has five precedence levels for binary operators: * / % << >> & &^ bind tightest, then + - | ^, then comparisons, then &&, then ||. The levels are fewer than in C, so a<<1 + 1 groups as (a<<1) + 1.',
'Increment and decrement are statements, not expressions: i++ is allowed on its own line, but x := i++ is a syntax error. Assignment is also a statement, so it cannot appear inside a condition.',
'Bitwise operators work on integers: & and, | or, ^ xor (and unary ^ for bitwise not), &^ and-not (bit clear), << and >> shifts. && and || short-circuit, which makes guards such as p != nil && p.ok safe.',
],
code=r'''package main

import "fmt"

func main() {
    a := 3
    fmt.Println(a<<1 + 1)
    flags := 0b1011
    fmt.Printf("%04b %04b %04b\n", flags&0b0110, flags&^0b0011, ^flags&0xf)
    fmt.Println(1 < 2 && 2 < 3 || false)
}
''',
expectedStdout='7\n0010 1000 0100\ntrue\n',
challenge='Given bits := uint8(0b1010_0101), print it with bit 0 cleared and bit 1 set, in %08b form.',
solution=r'''package main

import "fmt"

func main() {
    bits := uint8(0b1010_0101)
    bits = bits&^1 | 1<<1
    fmt.Printf("%08b\n", bits)
}
''',
solutionStdout='10100110\n',
question='How does a<<1 + 1 group in Go?',
correct='(a<<1) + 1, because shifts bind tighter than addition',
wrong=['a << (1 + 1), as in C', 'It is a compile error without parentheses'],
reasoning='<< shares the multiplication precedence level, which is above +. gofmt even removes the spaces around << to show the grouping.',
rejections=[dict(source='package main\n\nfunc main() {\n\ti := 0\n\tx := i++\n\t_ = x\n}\n', diagnostic='syntax error')],
sourceURL=SPEC+'#Operator_precedence'),

dict(key='type-definitions-aliases', stage=STAGE, title='Defined types, aliases and underlying types',
body=[
'type Celsius float64 defines a new named type whose underlying type is float64. Celsius and float64 are different types: mixing them needs a conversion, and Celsius can have its own methods. This is how Go expresses units and domain meanings in the type system.',
'type Name = string is an alias: another name for exactly the same type. Aliases exist mainly for gradual refactoring across packages, and since Go 1.24 they can have type parameters. byte and rune are predeclared aliases.',
'Conversion between a defined type and its underlying type is always allowed, and so is conversion between two defined types that share an underlying type. Untyped constants convert implicitly, so var c Celsius = 100 compiles without a cast.',
],
code=r'''package main

import "fmt"

type Celsius float64
type Fahrenheit float64

type Label = string

func toF(c Celsius) Fahrenheit {
    return Fahrenheit(c*9/5 + 32)
}

func main() {
    var boil Celsius = 100
    fmt.Println(toF(boil))
    var l Label = "same type as string"
    var s string = l
    fmt.Printf("%T %T\n", boil, s)
}
''',
expectedStdout='212\nmain.Celsius string\n',
challenge='Define type Meters float64 and type Feet float64 and write a function converting Feet to Meters (1 ft = 0.3048 m); print the result for 10 feet.',
solution=r'''package main

import "fmt"

type Meters float64
type Feet float64

func toMeters(f Feet) Meters {
    return Meters(f * 0.3048)
}

func main() {
    fmt.Printf("%.3f\n", toMeters(10))
}
''',
solutionStdout='3.048\n',
question='What is the difference between type A B and type A = B?',
correct='The first defines a distinct type; the second is an alias for the same type',
wrong=['They are identical spellings', 'The first is an alias; the second copies B\'s methods into a new type'],
reasoning='A type definition creates a new, distinct named type with no methods of its own yet. An alias is just another name, so values flow between A and B freely.',
rejections=[dict(source='package main\n\ntype Celsius float64\ntype Fahrenheit float64\n\nfunc main() {\n\tvar c Celsius = 1\n\tvar f Fahrenheit = c\n\t_ = f\n}\n', diagnostic='cannot use c (variable of float64 type Celsius) as Fahrenheit value')],
sourceURL=SPEC+'#Type_declarations',
additionalReadings=[dict(title='Generic type aliases (Go 1.24)', url='https://go.dev/doc/go1.24#language', section='Alias type parameters')]),
]

STAGE = '11 · Standard library'
PKG = 'https://pkg.go.dev/'

LESSONS = [
dict(key='io-composition', stage=STAGE, title='io.Reader and io.Writer composition',
body=[
'io.Reader has one method, Read(p []byte) (n int, err error). It fills up to len(p) bytes and returns how many; it may return fewer than requested without error, and io.EOF signals the end. Always process the n bytes before looking at err, because a reader may return data and io.EOF together.',
'Small adapters combine readers and writers: io.MultiReader concatenates, io.TeeReader copies what it reads to a writer, io.LimitReader caps how much can be read, io.MultiWriter duplicates writes, and io.Pipe connects a writer goroutine to a reader. io.Copy moves data between them with a reusable buffer.',
'Accepting io.Reader instead of a filename makes code testable: tests pass strings.NewReader, production passes a file or network connection. io.ReadAll is fine for small inputs; for large or untrusted input, wrap with io.LimitReader first.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "os"
    "strings"
)

func main() {
    r := io.MultiReader(strings.NewReader("hello, "), strings.NewReader("readers\n"))
    var seen strings.Builder
    tee := io.TeeReader(r, &seen)
    n, err := io.Copy(os.Stdout, io.LimitReader(tee, 100))
    fmt.Println(n, err, seen.Len())
    capped, _ := io.ReadAll(io.LimitReader(strings.NewReader("0123456789"), 4))
    fmt.Println(string(capped))
}
''',
expectedStdout='hello, readers\n15 <nil> 15\n0123\n',
challenge='Use io.Pipe: a goroutine writes "from a pipe" to the writer and closes it, while main reads everything with io.ReadAll and prints it.',
solution=r'''package main

import (
    "fmt"
    "io"
)

func main() {
    pr, pw := io.Pipe()
    go func() {
        fmt.Fprint(pw, "from a pipe")
        pw.Close()
    }()
    data, err := io.ReadAll(pr)
    fmt.Println(string(data), err)
}
''',
solutionStdout='from a pipe <nil>\n',
question='A Read call returns n > 0 and io.EOF together. What should the caller do?',
correct='Use the n bytes first, then stop because of EOF',
wrong=['Discard the bytes because an error occurred', 'Call Read again to get the bytes without the error'],
reasoning='The io.Reader contract allows data and EOF in the same call. Processing p[:n] before checking err is the safe pattern.',
sourceURL=PKG+'io#Reader'),

dict(key='bufio', stage=STAGE, title='Buffered I/O: bufio.Reader, Writer and Scanner splitters',
body=[
'Small reads and writes on files or sockets are expensive system calls. bufio.Reader and bufio.Writer batch them with an in-memory buffer. A bufio.Writer must be flushed: until Flush is called the bytes may sit in memory, and an error from a failed write appears at Flush.',
'bufio.Scanner splits input into tokens with a SplitFunc: ScanLines (default), ScanWords, ScanRunes or ScanBytes. Custom split functions parse other formats. For lines longer than the buffer, call Buffer to raise the limit, or use Reader.ReadString.',
'bufio.Reader offers ReadString(\'\\n\'), ReadRune and Peek. ReadString returns the data read before an error, so the last line without a trailing newline comes back together with io.EOF.',
],
code=r'''package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func main() {
    sc := bufio.NewScanner(strings.NewReader("go is  fun\nand fast"))
    sc.Split(bufio.ScanWords)
    words := 0
    for sc.Scan() {
        words++
    }
    fmt.Println("words:", words, sc.Err())
    w := bufio.NewWriter(os.Stdout)
    fmt.Fprintln(w, "buffered line")
    fmt.Println("unbuffered first")
    if err := w.Flush(); err != nil {
        fmt.Println(err)
    }
}
''',
expectedStdout='words: 5 <nil>\nunbuffered first\nbuffered line\n',
challenge='Read "a\\nb\\nlast" with bufio.Reader.ReadString(\'\\n\') in a loop, printing each line with %q and stopping after the line returned together with io.EOF.',
solution=r'''package main

import (
    "bufio"
    "errors"
    "fmt"
    "io"
    "strings"
)

func main() {
    r := bufio.NewReader(strings.NewReader("a\nb\nlast"))
    for {
        line, err := r.ReadString('\n')
        fmt.Printf("%q\n", line)
        if errors.Is(err, io.EOF) {
            break
        }
        if err != nil {
            fmt.Println(err)
            return
        }
    }
}
''',
solutionStdout='"a\\n"\n"b\\n"\n"last"\n',
question='Why did "buffered line" print after "unbuffered first"?',
correct='bufio.Writer held it in memory until Flush',
wrong=['fmt.Fprintln writes asynchronously', 'Standard output reorders writes'],
reasoning='The buffered bytes reached os.Stdout only when Flush ran. Forgetting Flush loses output entirely.',
sourceURL=PKG+'bufio'),

dict(key='files-os-root', stage=STAGE, title='Files, directories and traversal-safe os.Root',
body=[
'os.ReadFile and os.WriteFile handle whole small files. os.Open returns a read-only *os.File; os.Create truncates or creates for writing; os.OpenFile takes flags such as os.O_APPEND|os.O_CREATE|os.O_WRONLY and permissions such as 0o644. os.MkdirAll, os.ReadDir and os.RemoveAll work on directories.',
'Joining an untrusted name onto a directory, filepath.Join(dir, name), is unsafe: "../secret" or a symlink can escape. Go 1.24 added os.Root: os.OpenRoot(dir) returns a handle whose Open, Create, ReadFile, WriteFile, Mkdir and Remove methods refuse any path, including symlinks, that resolves outside the root.',
'Use os.Root whenever paths come from users, archives or network requests. root.FS() adapts it to fs.FS. Close the root when done.',
],
code=r'''package main

import (
    "fmt"
    "os"
    "path/filepath"
)

func main() {
    dir, err := os.MkdirTemp("", "root-lesson")
    if err != nil {
        panic(err)
    }
    defer os.RemoveAll(dir)
    root, err := os.OpenRoot(dir)
    if err != nil {
        panic(err)
    }
    defer root.Close()
    if err := root.WriteFile("notes.txt", []byte("inside"), 0o600); err != nil {
        panic(err)
    }
    data, err := root.ReadFile("notes.txt")
    fmt.Println(string(data), err)
    _, err = root.Open("../outside.txt")
    fmt.Println(err != nil)
    entries, _ := os.ReadDir(dir)
    fmt.Println(len(entries), filepath.Base(entries[0].Name()))
}
''',
expectedStdout='inside <nil>\ntrue\n1 notes.txt\n',
challenge='Inside an os.Root, create a subdirectory "logs" with root.Mkdir, write "logs/a.txt", then try root.Create("logs/../../x") and print whether it failed.',
solution=r'''package main

import (
    "fmt"
    "os"
)

func main() {
    dir, err := os.MkdirTemp("", "root-practice")
    if err != nil {
        panic(err)
    }
    defer os.RemoveAll(dir)
    root, err := os.OpenRoot(dir)
    if err != nil {
        panic(err)
    }
    defer root.Close()
    if err := root.Mkdir("logs", 0o700); err != nil {
        panic(err)
    }
    fmt.Println(root.WriteFile("logs/a.txt", []byte("ok"), 0o600))
    _, err = root.Create("logs/../../x")
    fmt.Println(err != nil)
}
''',
solutionStdout='<nil>\ntrue\n',
question='Why use os.Root instead of filepath.Join for user-supplied names?',
correct='Root rejects paths and symlinks that escape the directory',
wrong=['Root is faster for every file operation', 'filepath.Join cannot handle subdirectories'],
reasoning='Join only cleans the string; it does not stop ".." or symlinks pointing elsewhere. Root checks every resolved component.',
sourceURL=PKG+'os#Root',
additionalReadings=[dict(title='Traversal-resistant file APIs', url='https://go.dev/blog/osroot', section='os.Root')]),

dict(key='filepath-fs-embed', stage=STAGE, title='path/filepath, io/fs and embedded files',
body=[
'path/filepath handles operating-system paths: Join, Base, Dir, Ext, Rel, Clean and WalkDir. The plain path package is for slash-separated paths such as URLs and fs.FS names, which always use / on every OS.',
'io/fs defines a read-only file-system interface. fs.WalkDir, fs.ReadFile, fs.Glob and fs.Sub work on any fs.FS: os.DirFS, an os.Root, a zip archive, testing/fstest.MapFS, or files embedded in the binary.',
'//go:embed patterns before a variable of type string, []byte or embed.FS include files at build time. Embedded files ship inside the executable, so templates and static assets need no deployment step. fstest.MapFS is the in-memory fs.FS for tests.',
],
code=r'''package main

import (
    "fmt"
    "io/fs"
    "path/filepath"
    "testing/fstest"
)

func main() {
    fmt.Println(filepath.Join("a", "b", "..", "c.txt"), filepath.Ext("x.tar.gz"))
    fsys := fstest.MapFS{
        "docs/a.md":      {Data: []byte("# A")},
        "docs/b.md":      {Data: []byte("# B")},
        "docs/img/x.png": {Data: []byte{0x89}},
    }
    matches, _ := fs.Glob(fsys, "docs/*.md")
    fmt.Println(matches)
    fs.WalkDir(fsys, ".", func(p string, d fs.DirEntry, err error) error {
        if err == nil && !d.IsDir() {
            fmt.Println("file", p)
        }
        return err
    })
}
''',
expectedStdout='a/c.txt .gz\n[docs/a.md docs/b.md]\nfile docs/a.md\nfile docs/b.md\nfile docs/img/x.png\n',
challenge='Use fs.Sub to view the "docs" directory of a MapFS as its own file system and read "a.md" from it with fs.ReadFile.',
solution=r'''package main

import (
    "fmt"
    "io/fs"
    "testing/fstest"
)

func main() {
    fsys := fstest.MapFS{"docs/a.md": {Data: []byte("# A")}}
    docs, err := fs.Sub(fsys, "docs")
    if err != nil {
        panic(err)
    }
    data, err := fs.ReadFile(docs, "a.md")
    fmt.Println(string(data), err)
}
''',
solutionStdout='# A <nil>\n',
question='Which separator do fs.FS paths use on Windows?',
correct='Always forward slashes',
wrong=['Backslashes, like filepath', 'Whatever os.PathSeparator is'],
reasoning='fs.FS names are slash-separated and unrooted on every platform; filepath converts to OS form only at the edges.',
sourceURL=PKG+'io/fs',
additionalReadings=[dict(title='embed package', url=PKG+'embed', section='//go:embed directives')]),

dict(key='strconv-strings-unicode', stage=STAGE, title='strconv, strings, bytes and unicode',
body=[
'strconv converts between strings and numbers with explicit errors: Atoi, ParseInt(s, base, bits), ParseFloat, ParseBool, and the reverse Itoa, FormatInt and FormatFloat. Quote and Unquote handle Go-syntax string literals. Errors are *strconv.NumError values with Func, Num and Err fields.',
'strings and bytes mirror each other: Contains, HasPrefix, TrimSpace, TrimFunc, Fields, Split, Replace, EqualFold (case-insensitive comparison), Map and Title-free casing with ToUpper and ToLower. strings.NewReplacer performs many replacements in one pass.',
'unicode classifies runes: IsLetter, IsDigit, IsSpace, IsUpper. Go 1.27 updates the tables to Unicode 17. Case conversion is per rune and does not handle every language\'s rules; golang.org/x/text covers those.',
],
code=r'''package main

import (
    "errors"
    "fmt"
    "strconv"
    "strings"
    "unicode"
)

func main() {
    n, err := strconv.ParseInt("ff", 16, 64)
    fmt.Println(n, err)
    _, err = strconv.Atoi("12x")
    var ne *strconv.NumError
    fmt.Println(errors.As(err, &ne), ne.Func, ne.Err)
    fmt.Println(strconv.FormatFloat(3.14159, 'f', 2, 64), strconv.Quote("tab\t"))
    r := strings.NewReplacer("&", "&amp;", "<", "&lt;")
    fmt.Println(r.Replace("a<b & c"))
    fmt.Println(strings.EqualFold("Go", "GO"), strings.IndexFunc("ab1", unicode.IsDigit))
}
''',
expectedStdout='255 <nil>\ntrue Atoi invalid syntax\n3.14 "tab\\t"\na&lt;b &amp; c\ntrue 2\n',
challenge='Parse the comma-separated string "3, 4.5, x, 10" into float64 values, skipping and counting the invalid ones; print the sum and the number skipped.',
solution=r'''package main

import (
    "fmt"
    "strconv"
    "strings"
)

func main() {
    sum, skipped := 0.0, 0
    for part := range strings.SplitSeq("3, 4.5, x, 10", ",") {
        v, err := strconv.ParseFloat(strings.TrimSpace(part), 64)
        if err != nil {
            skipped++
            continue
        }
        sum += v
    }
    fmt.Println(sum, skipped)
}
''',
solutionStdout='17.5 1\n',
question='What does strconv.ParseInt("300", 10, 8) return?',
correct='127 and a range error, because 300 does not fit in 8 bits',
wrong=['300 and nil; bitSize is only a hint', '44, the low 8 bits, and nil'],
reasoning='bitSize limits the accepted range. Out-of-range input returns the nearest limit with ErrRange.',
sourceURL=PKG+'strconv'),

dict(key='time-durations', stage=STAGE, title='time: durations, monotonic clocks, layouts and zones',
body=[
'time.Duration is an int64 count of nanoseconds with constants such as time.Second; multiply a duration by an integer constant (3*time.Second), but convert a variable: time.Duration(n)*time.Second.',
'time.Now() includes a monotonic clock reading, so time.Since(start) measures elapsed time correctly even if the wall clock is changed. The monotonic reading is dropped by operations such as t.Round(0), Truncate and serialisation; compare times with Before, After and Equal, not ==.',
'Formatting uses a reference time, Mon Jan 2 15:04:05 MST 2006, written in the desired layout: t.Format("2006-01-02 15:04"). time.RFC3339 and time.DateOnly are predefined layouts. time.LoadLocation reads zone data; time.Parse defaults to UTC.',
],
code=r'''package main

import (
    "fmt"
    "time"
)

func main() {
    d := 90 * time.Minute
    fmt.Println(d, d.Hours())
    t := time.Date(2026, time.October, 16, 21, 5, 0, 0, time.UTC)
    fmt.Println(t.Format("Mon 2 Jan 2006 15:04"), t.Format(time.DateOnly))
    later := t.Add(36 * time.Hour)
    fmt.Println(later.Weekday(), later.Sub(t), later.After(t))
    parsed, err := time.Parse(time.RFC3339, "2026-08-12T10:00:00+02:00")
    fmt.Println(parsed.UTC(), err)
    n := 3
    fmt.Println(time.Duration(n) * time.Second)
}
''',
expectedStdout='1h30m0s 1.5\nFri 16 Oct 2026 21:05 2026-10-16\nSunday 36h0m0s true\n2026-08-12 08:00:00 +0000 UTC <nil>\n3s\n',
challenge='Compute how many whole days lie between 2026-01-01 and 2026-10-16 (UTC) and print them.',
solution=r'''package main

import (
    "fmt"
    "time"
)

func main() {
    a := time.Date(2026, time.January, 1, 0, 0, 0, 0, time.UTC)
    b := time.Date(2026, time.October, 16, 0, 0, 0, 0, time.UTC)
    fmt.Println(int(b.Sub(a).Hours() / 24))
}
''',
solutionStdout='288\n',
question='Why should elapsed time be measured with time.Since rather than subtracting wall-clock readings you saved as strings?',
correct='Since uses the monotonic clock, which is immune to wall-clock changes',
wrong=['Strings lose time zones', 'time.Since rounds to milliseconds'],
reasoning='The monotonic reading inside time.Now values only moves forward. Serialised times keep only the wall clock.',
sourceURL=PKG+'time#hdr-Monotonic_Clocks'),

dict(key='sort-and-search', stage=STAGE, title='Sorting, searching and ordering with cmp',
body=[
'slices.Sort and slices.SortFunc are the modern way to sort; the older sort package with sort.Slice and sort.Interface still works and is widely used. Sorting is in place and not stable unless you pick the stable variant.',
'slices.BinarySearch and sort.Search find positions in sorted data in O(log n). sort.Search(n, f) returns the smallest index for which f is true, assuming f is false then true: a general tool for monotone predicates, not just equality.',
'Ordering functions must be consistent: if a < b and b < c then a < c. An inconsistent comparator, such as one that compares floats containing NaN with <, can produce unsorted output. cmp.Compare treats NaN as less than every other value, which gives a total order.',
],
code=r'''package main

import (
    "cmp"
    "fmt"
    "math"
    "slices"
    "sort"
)

func main() {
    xs := []float64{3, math.NaN(), 1, 2}
    slices.SortFunc(xs, cmp.Compare[float64])
    fmt.Println(xs)
    sorted := []int{1, 3, 5, 7, 9}
    i := sort.Search(len(sorted), func(i int) bool { return sorted[i] >= 6 })
    fmt.Println(i, sorted[i])
    names := []string{"bo", "Al", "cy"}
    sort.Strings(names)
    fmt.Println(names, sort.StringsAreSorted(names))
}
''',
expectedStdout='[NaN 1 2 3]\n3 7\n[Al bo cy] true\n',
challenge='Use sort.Search to find the smallest integer n in [0, 100) such that n*n >= 50, and print it.',
solution=r'''package main

import (
    "fmt"
    "sort"
)

func main() {
    n := sort.Search(100, func(n int) bool { return n*n >= 50 })
    fmt.Println(n)
}
''',
solutionStdout='8\n',
question='What does sort.Search(n, f) require of f?',
correct='f must be false for a prefix of indices and true for the rest',
wrong=['f must return true exactly once', 'f must compare against a target value with =='],
reasoning='Search is a binary search over a monotone predicate and returns the first index where it becomes true, or n if never.',
sourceURL=PKG+'sort#Search'),

dict(key='encoding-json', stage=STAGE, title='encoding/json: struct tags, decoding and streaming',
body=[
'json.Marshal turns Go values into JSON: exported struct fields become object members named by their `json:"name"` tag. Options in the tag include omitempty (skip zero values like 0, "", nil) and, since Go 1.24, omitzero (skip values whose IsZero or zero value is zero, useful for time.Time and structs). Unexported fields are ignored.',
'json.Unmarshal decodes into a pointer. Unknown members are ignored by default; a json.Decoder with DisallowUnknownFields rejects them. Numbers decode into float64 when the target is any; use json.Number or concrete types to avoid precision loss.',
'json.NewDecoder(r) and json.NewEncoder(w) stream values from and to readers and writers, which avoids holding a whole document in memory. Encoder.SetIndent pretty-prints.',
],
code=r'''package main

import (
    "encoding/json"
    "fmt"
    "os"
    "strings"
)

type User struct {
    Name   string   `json:"name"`
    Email  string   `json:"email,omitempty"`
    Tags   []string `json:"tags"`
    secret string
}

func main() {
    out, _ := json.Marshal(User{Name: "Ada", secret: "x"})
    fmt.Println(string(out))
    var u User
    err := json.Unmarshal([]byte(`{"name":"Bo","tags":["go"],"extra":1}`), &u)
    fmt.Println(u.Name, u.Tags, err)
    dec := json.NewDecoder(strings.NewReader(`{"name":"Cy","age":3}`))
    dec.DisallowUnknownFields()
    fmt.Println(dec.Decode(&u))
    enc := json.NewEncoder(os.Stdout)
    enc.Encode(map[string]int{"b": 2, "a": 1})
}
''',
expectedStdout='{"name":"Ada","tags":null}\nBo [go] <nil>\njson: unknown field "age"\n{"a":1,"b":2}\n',
challenge='Decode the JSON array [{"id":1,"done":true},{"id":2,"done":false}] into a slice of structs and print how many are done.',
solution=r'''package main

import (
    "encoding/json"
    "fmt"
)

type Task struct {
    ID   int  `json:"id"`
    Done bool `json:"done"`
}

func main() {
    var tasks []Task
    if err := json.Unmarshal([]byte(`[{"id":1,"done":true},{"id":2,"done":false}]`), &tasks); err != nil {
        fmt.Println(err)
        return
    }
    done := 0
    for _, t := range tasks {
        if t.Done {
            done++
        }
    }
    fmt.Println(done)
}
''',
solutionStdout='1\n',
question='Why did Tags marshal as null in the first line?',
correct='A nil slice encodes as null in encoding/json v1',
wrong=['Tags lacked omitempty', 'Slices are never encoded'],
reasoning='v1 distinguishes nil slices (null) from empty slices ([]). json/v2 encodes nil slices as [] by default.',
sourceURL=PKG+'encoding/json'),

dict(key='json-v2', stage=STAGE, title='Go 1.27 encoding/json/v2 and jsontext',
body=[
'Go 1.27 adds encoding/json/v2, a revised API with stricter, more consistent defaults, and encoding/json/jsontext for low-level tokens. encoding/json v1 now runs on the v2 implementation while keeping its old behaviour.',
'Notable v2 defaults: nil slices and maps encode as [] and {}, member names match case-sensitively, duplicate names are rejected, and invalid UTF-8 is an error. Behaviour is adjusted with options passed to Marshal and Unmarshal, such as json.Deterministic(true), json.RejectUnknownMembers(true) or json.OmitZeroStructFields(true).',
'jsontext.Value is a raw JSON value with methods for formatting and canonicalising, and jsontext.Encoder and Decoder stream tokens. MarshalWrite and UnmarshalRead read and write io streams directly. Prefer v2 for new code that targets 1.27; migrate v1 code by checking the documented behaviour differences.',
],
code=r'''package main

import (
    "encoding/json/jsontext"
    "encoding/json/v2"
    "fmt"
)

type Config struct {
    Name  string   `json:"name"`
    Hosts []string `json:"hosts"`
}

func main() {
    out, err := json.Marshal(Config{Name: "api"})
    fmt.Println(string(out), err)
    var c Config
    err = json.Unmarshal([]byte(`{"NAME":"x"}`), &c)
    fmt.Printf("%q %v\n", c.Name, err)
    err = json.Unmarshal([]byte(`{"name":"a","port":1}`), &c, json.RejectUnknownMembers(true))
    fmt.Println(err != nil)
    v := jsontext.Value(`{ "b" : 2, "a" : [1, 2] }`)
    if err := v.Compact(); err != nil {
        fmt.Println(err)
    }
    fmt.Println(string(v))
}
''',
expectedStdout='{"name":"api","hosts":[]} <nil>\n"" <nil>\ntrue\n{"b":2,"a":[1,2]}\n',
challenge='Marshal map[string]int{"z": 1, "a": 2} with json/v2 and json.Deterministic(true), then reformat the bytes with jsontext.Value.Indent using "  " and print them.',
solution=r'''package main

import (
    "encoding/json/jsontext"
    "encoding/json/v2"
    "fmt"
)

func main() {
    out, err := json.Marshal(map[string]int{"z": 1, "a": 2}, json.Deterministic(true))
    if err != nil {
        fmt.Println(err)
        return
    }
    v := jsontext.Value(out)
    if err := v.Indent(jsontext.WithIndent("  ")); err != nil {
        fmt.Println(err)
        return
    }
    fmt.Println(string(v))
}
''',
solutionStdout='{\n  "a": 2,\n  "z": 1\n}\n',
question='How does json/v2 encode a nil []string by default?',
correct='As an empty array []',
wrong=['As null, like v1', 'It omits the member'],
reasoning='v2 treats nil and empty slices alike by default. The FormatNilSliceAsNull option restores v1-style null.',
sourceURL=PKG+'encoding/json/v2',
additionalReadings=[dict(title='Go 1.27 release notes: json/v2', url='https://go.dev/doc/go1.27#encodingjsonv2', section='encoding/json/v2'),
                    dict(title='jsontext package', url=PKG+'encoding/json/jsontext', section='Value, Encoder, Decoder')]),

dict(key='log-slog', stage=STAGE, title='Structured logging with log/slog',
body=[
'log/slog (Go 1.21) writes structured records: a time, a level, a message and key-value attributes. slog.Info("saved", "user", id, "bytes", n) produces machine-readable output that log systems can filter by field.',
'A Logger sends records to a Handler. slog.NewTextHandler writes key=value text and slog.NewJSONHandler writes JSON objects; HandlerOptions sets the minimum level, adds source locations, or rewrites attributes with ReplaceAttr (for example to drop the time in tests). logger.With adds attributes to every record and WithGroup nests them.',
'slog.SetDefault installs a logger used by the top-level functions and by the older log package. Use typed attributes such as slog.Int and slog.Any in hot paths to avoid allocation, and implement slog.LogValuer to control how a type is logged, such as redacting secrets.',
],
code=r'''package main

import (
    "log/slog"
    "os"
)

type Token string

func (Token) LogValue() slog.Value { return slog.StringValue("REDACTED") }

func main() {
    opts := &slog.HandlerOptions{
        Level: slog.LevelDebug,
        ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
            if a.Key == slog.TimeKey && len(groups) == 0 {
                return slog.Attr{}
            }
            return a
        },
    }
    logger := slog.New(slog.NewTextHandler(os.Stdout, opts))
    logger.Debug("starting", "port", 8080)
    req := logger.With("request", 42)
    req.Info("auth", "token", Token("s3cret"))
    req.WithGroup("db").Warn("slow", slog.Int("ms", 250))
}
''',
expectedStdout='level=DEBUG msg=starting port=8080\nlevel=INFO msg=auth request=42 token=REDACTED\nlevel=WARN msg=slow request=42 db.ms=250\n',
challenge='Log one Info record with a JSON handler (time removed) containing user="ada" and attempts=3, and print it.',
solution=r'''package main

import (
    "log/slog"
    "os"
)

func main() {
    h := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
        ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
            if a.Key == slog.TimeKey && len(groups) == 0 {
                return slog.Attr{}
            }
            return a
        },
    })
    slog.New(h).Info("login", "user", "ada", "attempts", 3)
}
''',
solutionStdout='{"level":"INFO","msg":"login","user":"ada","attempts":3}\n',
question='How do you stop a secret type from appearing in logs?',
correct='Implement slog.LogValuer to return a redacted value',
wrong=['Mark the field unexported', 'Log it at Debug level only'],
reasoning='Handlers resolve LogValuer before formatting, so the redacted value is all any handler sees.',
sourceURL=PKG+'log/slog',
additionalReadings=[dict(title='Structured logging with slog', url='https://go.dev/blog/slog', section='slog')]),

dict(key='flag-cli', stage=STAGE, title='Command-line flags with the flag package',
body=[
'flag defines typed options: n := flag.Int("n", 10, "number of lines"). After flag.Parse(), *n holds the value and flag.Args() returns the remaining positional arguments. flag.StringVar and friends bind to existing variables, and flag.Func or a type implementing flag.Value supports custom parsing.',
'Flags may be written -n=5, -n 5 or --n 5. Boolean flags need -v=false to turn off. -h or -help prints usage generated from the descriptions; set flag.Usage to customise it.',
'For testable programs use a flag.FlagSet created with flag.ContinueOnError and parse an explicit []string, instead of the global flag set and os.Args. FlagSet.Parse then returns an error instead of exiting.',
],
code=r'''package main

import (
    "flag"
    "fmt"
    "io"
    "strings"
)

func parse(args []string) (int, bool, []string, error) {
    fs := flag.NewFlagSet("demo", flag.ContinueOnError)
    fs.SetOutput(io.Discard)
    n := fs.Int("n", 10, "number of lines")
    verbose := fs.Bool("v", false, "verbose output")
    err := fs.Parse(args)
    return *n, *verbose, fs.Args(), err
}

func main() {
    fmt.Println(parse([]string{"-n=3", "-v", "a.txt", "b.txt"}))
    fmt.Println(parse(nil))
    _, _, _, err := parse([]string{"-n", "many"})
    fmt.Println(strings.Contains(err.Error(), "invalid value"))
}
''',
expectedStdout='3 true [a.txt b.txt] <nil>\n10 false [] <nil>\ntrue\n',
challenge='Add a repeated -tag flag using fs.Func that collects every value into a []string; parse ["-tag", "a", "-tag", "b"] and print the tags.',
solution=r'''package main

import (
    "flag"
    "fmt"
)

func main() {
    fs := flag.NewFlagSet("demo", flag.ContinueOnError)
    var tags []string
    fs.Func("tag", "add a tag (repeatable)", func(s string) error {
        tags = append(tags, s)
        return nil
    })
    if err := fs.Parse([]string{"-tag", "a", "-tag", "b"}); err != nil {
        fmt.Println(err)
        return
    }
    fmt.Println(tags)
}
''',
solutionStdout='[a b]\n',
question='Why parse flags with a FlagSet and an explicit argument slice?',
correct='So tests can pass arguments and receive errors instead of the process exiting',
wrong=['The global flag set cannot parse integers', 'FlagSet is required for boolean flags'],
reasoning='With ContinueOnError, Parse returns an error. The global flag.Parse uses ExitOnError and os.Args.',
sourceURL=PKG+'flag'),

dict(key='uuid-package', stage=STAGE, title='The Go 1.27 uuid package',
body=[
'Go 1.27 adds package uuid to the standard library. uuid.UUID is a [16]byte array type, so UUIDs are comparable with == and usable as map keys. uuid.New returns a random version 4 UUID; uuid.NewV7 returns a version 7 UUID whose leading bits are a timestamp, so values sort roughly by creation time, which suits database keys.',
'uuid.Parse and uuid.MustParse read the standard 36-character hyphenated text form; String writes it. UUID implements encoding.TextMarshaler, so it works with JSON and other text encodings. Compare orders two UUIDs bytewise.',
'Random UUIDs are unpredictable but not secret tokens; use crypto/rand for credentials. Nil() is the all-zero UUID and Max() the all-ones value.',
],
code=r'''package main

import (
    "fmt"
    "uuid"
)

func main() {
    id := uuid.MustParse("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    fmt.Println(id, id[6]>>4)
    a, b := uuid.NewV7(), uuid.NewV7()
    fmt.Println(a != b, a[6]>>4)
    _, err := uuid.Parse("not-a-uuid")
    fmt.Println(err != nil, uuid.Nil() == uuid.UUID{})
}
''',
expectedStdout='f47ac10b-58cc-4372-a567-0e02b2c3d479 4\ntrue 7\ntrue true\n',
challenge='Generate three version 7 UUIDs one after another and print whether they are in non-decreasing order using Compare.',
solution=r'''package main

import (
    "fmt"
    "uuid"
)

func main() {
    ids := []uuid.UUID{uuid.NewV7(), uuid.NewV7(), uuid.NewV7()}
    ordered := true
    for i := 1; i < len(ids); i++ {
        if ids[i-1].Compare(ids[i]) > 0 {
            ordered = false
        }
    }
    fmt.Println(ordered)
}
''',
solutionStdout='true\n',
question='Why might you prefer uuid.NewV7 over uuid.New for database primary keys?',
correct='V7 values start with a timestamp, so new keys sort near each other',
wrong=['V7 is cryptographically stronger', 'V4 cannot be stored in a [16]byte'],
reasoning='Time-ordered keys keep B-tree inserts local. V4 values are uniformly random, which scatters inserts.',
sourceURL=PKG+'uuid',
additionalReadings=[dict(title='Go 1.27 release notes: uuid', url='https://go.dev/doc/go1.27#uuid', section='uuid')]),

dict(key='math-big-rand', stage=STAGE, title='math, math/big and math/rand/v2',
body=[
'math provides float functions (Sqrt, Floor, Inf, NaN, IsNaN) and integer limits (math.MaxInt64). math/bits does bit counting and overflow-checked arithmetic. Floating-point variables are not exact: x+y with x=0.1, y=0.2 differs from 0.3, so compare with a tolerance. Constant expressions are evaluated exactly at compile time, which is why the constant 0.1+0.2 == 0.3 is true.',
'math/big gives arbitrary-precision Int, Rat and Float. Methods set a receiver and return it, so z := new(big.Int).Mul(x, y) avoids allocations in loops. Go 1.27 adds Int.Divide with explicit rounding modes (Trunc, Floor, Round, Ceil).',
'math/rand/v2 (Go 1.22) has rand.IntN, rand.N for any integer type or duration, and seedable sources such as rand.NewPCG for reproducible simulations. Go 1.27 adds the generic Rand.N method. These are not suitable for secrets; use crypto/rand for keys and tokens.',
],
code=r'''package main

import (
    "fmt"
    "math"
    "math/big"
    "math/rand/v2"
)

func main() {
    const exact = 0.1+0.2 == 0.3
    x, y := 0.1, 0.2
    fmt.Println(exact, x+y == 0.3, math.Abs(x+y-0.3) < 1e-9)
    f := new(big.Int)
    f.MulRange(1, 25)
    fmt.Println(f)
    q, r := new(big.Int).Divide(big.NewInt(-7), big.NewInt(2), new(big.Int), big.Floor)
    fmt.Println(q, r)
    rng := rand.New(rand.NewPCG(1, 2))
    a := rng.IntN(100)
    rng2 := rand.New(rand.NewPCG(1, 2))
    fmt.Println(a == rng2.IntN(100), rand.N(int64(10)) < 10)
}
''',
expectedStdout='true false true\n15511210043330985984000000\n-4 1\ntrue true\n',
challenge='Compute 2^100 with math/big and print it, then print its number of decimal digits.',
solution=r'''package main

import (
    "fmt"
    "math/big"
)

func main() {
    p := new(big.Int).Exp(big.NewInt(2), big.NewInt(100), nil)
    s := p.String()
    fmt.Println(s)
    fmt.Println(len(s))
}
''',
solutionStdout='1267650600228229401496703205376\n31\n',
question='Why seed a rand.Rand with rand.NewPCG(1, 2) in a simulation?',
correct='The same seed reproduces the same sequence, which makes runs repeatable',
wrong=['It makes the output cryptographically secure', 'Unseeded generators always return zero'],
reasoning='Deterministic sources let you replay a simulation or test. The top-level functions are randomly seeded.',
sourceURL=PKG+'math/rand/v2',
additionalReadings=[dict(title='math/big Int.Divide (Go 1.27)', url=PKG+'math/big#Int.Divide', section='Divide')]),
]

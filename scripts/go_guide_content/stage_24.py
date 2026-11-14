STAGE = '24 · Storage, compression and system packages'
PKG = 'https://pkg.go.dev/'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='compression', stage=STAGE, title='Compression: flate, gzip, zlib, lzw and bzip2',
body=[
'compress/flate implements DEFLATE, the algorithm underneath compress/gzip (files with a header, name and CRC) and compress/zlib (a smaller header and Adler-32 checksum used by PNG and HTTP deflate). All of them are streams: wrap an io.Writer with NewWriter, write, then Close to flush the final block and checksum. Forgetting Close produces truncated output.',
'Compression levels trade speed for size: flate.BestSpeed, flate.BestCompression, flate.DefaultCompression and flate.HuffmanOnly. Go 1.27 made compress/flate faster. Readers verify checksums and report gzip.ErrChecksum on corruption.',
'compress/lzw implements the LZW codes used by GIF and TIFF. compress/bzip2 only decompresses: the standard library has no bzip2 writer. Always bound decompressed size from untrusted input with io.LimitReader, because a tiny archive can expand to gigabytes.',
],
code=r'''package main

import (
    "bytes"
    "compress/bzip2"
    "compress/flate"
    "compress/gzip"
    "compress/lzw"
    "compress/zlib"
    "fmt"
    "io"
    "strings"
)

func main() {
    text := strings.Repeat("go gopher ", 100)
    var gz bytes.Buffer
    zw := gzip.NewWriter(&gz)
    zw.Name = "notes.txt"
    zw.Write([]byte(text))
    zw.Close()
    zr, _ := gzip.NewReader(&gz)
    back, _ := io.ReadAll(zr)
    fmt.Println(len(text), gz.Len() < 100, zr.Name, string(back) == text)
    var fast, best bytes.Buffer
    fw, _ := flate.NewWriter(&fast, flate.HuffmanOnly)
    fw.Write([]byte(text))
    fw.Close()
    bw, _ := flate.NewWriter(&best, flate.BestCompression)
    bw.Write([]byte(text))
    bw.Close()
    fmt.Println(best.Len() < fast.Len())
    var z bytes.Buffer
    w := zlib.NewWriter(&z)
    w.Write([]byte("zlib"))
    w.Close()
    fmt.Printf("% x\n", z.Bytes()[:2])
    var l bytes.Buffer
    lw := lzw.NewWriter(&l, lzw.LSB, 8)
    lw.Write([]byte("TOBEORNOTTOBEORTOBEORNOT"))
    lw.Close()
    lr := lzw.NewReader(&l, lzw.LSB, 8)
    plain, _ := io.ReadAll(lr)
    fmt.Println(string(plain))
    bz := []byte{0x42, 0x5a, 0x68, 0x39, 0x31, 0x41, 0x59, 0x26, 0x53, 0x59, 0xab, 0x6b, 0xa1, 0xf1, 0x00, 0x00, 0x02, 0xd9, 0x80, 0x00, 0x10, 0x40, 0x00, 0x10, 0x00, 0x12, 0x64, 0xc0, 0x10, 0x20, 0x00, 0x31, 0x00, 0xd3, 0x4d, 0x04, 0x00, 0x1e, 0xa3, 0xef, 0x4e, 0x51, 0xa2, 0x07, 0x8b, 0xb9, 0x22, 0x9c, 0x28, 0x48, 0x55, 0xb5, 0xd0, 0xf8, 0x80}
    unz, err := io.ReadAll(bzip2.NewReader(bytes.NewReader(bz)))
    fmt.Printf("%q %v\n", unz, err)
}
''',
expectedStdout='1000 true notes.txt true\ntrue\n78 9c\nTOBEORNOTTOBEORTOBEORNOT\n"hello bzip2\\n" <nil>\n',
challenge='Write func gunzipLimited(r io.Reader, max int64) ([]byte, error) that refuses to expand beyond max bytes, and show it rejects 1000 bytes of compressed zeros when max is 100.',
solution=r'''package main

import (
    "bytes"
    "compress/gzip"
    "errors"
    "fmt"
    "io"
)

func gunzipLimited(r io.Reader, max int64) ([]byte, error) {
    zr, err := gzip.NewReader(r)
    if err != nil {
        return nil, err
    }
    data, err := io.ReadAll(io.LimitReader(zr, max+1))
    if err != nil {
        return nil, err
    }
    if int64(len(data)) > max {
        return nil, errors.New("decompressed data too large")
    }
    return data, nil
}

func main() {
    var buf bytes.Buffer
    w := gzip.NewWriter(&buf)
    w.Write(make([]byte, 1000))
    w.Close()
    _, err := gunzipLimited(&buf, 100)
    fmt.Println(err)
}
''',
solutionStdout='decompressed data too large\n',
question='What happens if you forget to Close a gzip.Writer?',
correct='The final compressed block and the trailer are never written, so the output is truncated',
wrong=['The data is written uncompressed', 'Nothing; Close only frees memory'],
reasoning='Compressors buffer data. Close flushes the last block and writes the CRC and size trailer readers check.',
sourceURL=PKG+'compress/gzip',
additionalReadings=[dict(title='compress/flate', url=PKG+'compress/flate', section='Levels'), dict(title='compress/bzip2', url=PKG+'compress/bzip2', section='NewReader')]),

dict(key='archives', stage=STAGE, title='Archives: archive/tar and archive/zip',
body=[
'archive/tar writes a sequence of entries, each a tar.Header (name, mode, size, type) followed by its content; combine it with compress/gzip for .tar.gz. tar.Reader.Next walks the entries. archive/zip stores a central directory, so readers can jump to any file; zip.NewReader needs an io.ReaderAt and the total size.',
'Both formats can hold names such as ../../etc/passwd. When extracting, reject absolute paths and any name that escapes the destination: use filepath.IsLocal (Go 1.20) or open files through an os.Root. Since Go 1.20 the readers can also reject such names themselves, returning zip.ErrInsecurePath or tar.ErrInsecurePath, when GODEBUG=zipinsecurepath=0 or tarinsecurepath=0 is set.',
'zip.Writer.Create adds a deflated file; CreateHeader sets the method and timestamps. Both archive writers must be closed to write their trailers.',
],
code=r'''package main

import (
    "archive/tar"
    "archive/zip"
    "bytes"
    "fmt"
    "io"
    "path/filepath"
)

func main() {
    var tb bytes.Buffer
    tw := tar.NewWriter(&tb)
    for name, body := range map[string]string{"a.txt": "alpha"} {
        tw.WriteHeader(&tar.Header{Name: name, Mode: 0o644, Size: int64(len(body))})
        tw.Write([]byte(body))
    }
    tw.Close()
    tr := tar.NewReader(&tb)
    hdr, _ := tr.Next()
    data, _ := io.ReadAll(tr)
    fmt.Println(hdr.Name, hdr.Size, string(data))
    var zb bytes.Buffer
    zw := zip.NewWriter(&zb)
    w, _ := zw.Create("docs/readme.md")
    w.Write([]byte("# zip"))
    zw.Close()
    zr, _ := zip.NewReader(bytes.NewReader(zb.Bytes()), int64(zb.Len()))
    rc, _ := zr.File[0].Open()
    body, _ := io.ReadAll(rc)
    rc.Close()
    fmt.Println(zr.File[0].Name, zr.File[0].Method == zip.Deflate, string(body))
    for _, name := range []string{"docs/readme.md", "../escape", "/etc/passwd"} {
        fmt.Print(filepath.IsLocal(name), " ")
    }
    fmt.Println()
}
''',
expectedStdout='a.txt 5 alpha\ndocs/readme.md true # zip\ntrue false false \n',
challenge='Write func safeNames(zr *zip.Reader) []string that returns only the entry names safe to extract, and test it on an archive containing "ok.txt" and "../evil.txt".',
solution=r'''package main

import (
    "archive/zip"
    "bytes"
    "fmt"
    "path/filepath"
)

func safeNames(zr *zip.Reader) []string {
    var out []string
    for _, f := range zr.File {
        if filepath.IsLocal(f.Name) {
            out = append(out, f.Name)
        }
    }
    return out
}

func main() {
    var buf bytes.Buffer
    zw := zip.NewWriter(&buf)
    for _, n := range []string{"ok.txt", "../evil.txt"} {
        w, _ := zw.Create(n)
        w.Write([]byte("x"))
    }
    zw.Close()
    zr, _ := zip.NewReader(bytes.NewReader(buf.Bytes()), int64(buf.Len()))
    fmt.Println(safeNames(zr))
}
''',
solutionStdout='[ok.txt]\n',
question='Why check entry names before extracting an archive?',
correct='Names like ../../x can write outside the target directory (a "zip slip")',
wrong=['Archive names are always lower-case', 'zip.Reader rejects such names automatically by default'],
reasoning='Archives are untrusted input. filepath.IsLocal or an os.Root keeps writes inside the destination.',
sourceURL=PKG+'archive/zip',
additionalReadings=[dict(title='archive/tar', url=PKG+'archive/tar', section='Reader and Writer')]),

dict(key='database-sql', stage=STAGE, title='database/sql and writing a driver with database/sql/driver',
body=[
'database/sql is a driver-agnostic API over a connection pool: sql.Open(driverName, dsn) returns a *sql.DB that is safe for concurrent use and should live for the program\'s lifetime. QueryContext returns *sql.Rows to iterate with Next and Scan; always defer rows.Close() and check rows.Err(). QueryRowContext returns one row, and ErrNoRows reports none. ExecContext runs statements; BeginTx starts transactions.',
'Use placeholders (? or $1 depending on the driver) for every value, never string concatenation, so the driver passes data separately from SQL and injection is impossible. SetMaxOpenConns, SetMaxIdleConns and SetConnMaxLifetime tune the pool.',
'Drivers implement the small interfaces in database/sql/driver: Driver.Open returns a Conn, which prepares Stmts that return Rows. This lesson implements a toy in-memory driver to show what a real one (for PostgreSQL, MySQL or SQLite) provides. Go 1.27 adds sql.ConvertAssign and driver.RowsColumnScanner for drivers that scan columns themselves.',
],
code=r'''package main

import (
    "context"
    "database/sql"
    "database/sql/driver"
    "errors"
    "fmt"
    "io"
    "strings"
    "sync"
)

type store struct {
    mu   sync.Mutex
    data map[string]string
}

type memDriver struct{ s *store }
type conn struct{ s *store }
type stmt struct {
    s     *store
    query string
}
type rows struct {
    vals []string
    i    int
}

func (d memDriver) Open(string) (driver.Conn, error) { return conn{d.s}, nil }
func (c conn) Prepare(q string) (driver.Stmt, error) { return stmt{c.s, q}, nil }
func (c conn) Close() error                          { return nil }
func (c conn) Begin() (driver.Tx, error)             { return nil, errors.New("no transactions") }
func (s stmt) Close() error                          { return nil }
func (s stmt) NumInput() int                         { return strings.Count(s.query, "?") }

func (s stmt) Exec(args []driver.Value) (driver.Result, error) {
    s.s.mu.Lock()
    defer s.s.mu.Unlock()
    s.s.data[args[0].(string)] = args[1].(string)
    return driver.RowsAffected(1), nil
}

func (s stmt) Query(args []driver.Value) (driver.Rows, error) {
    s.s.mu.Lock()
    defer s.s.mu.Unlock()
    v, ok := s.s.data[args[0].(string)]
    if !ok {
        return &rows{}, nil
    }
    return &rows{vals: []string{v}}, nil
}

func (r *rows) Columns() []string { return []string{"value"} }
func (r *rows) Close() error      { return nil }
func (r *rows) Next(dest []driver.Value) error {
    if r.i >= len(r.vals) {
        return io.EOF
    }
    dest[0] = r.vals[r.i]
    r.i++
    return nil
}

func main() {
    sql.Register("mem", memDriver{&store{data: map[string]string{}}})
    db, err := sql.Open("mem", "")
    if err != nil {
        panic(err)
    }
    defer db.Close()
    ctx := context.Background()
    res, _ := db.ExecContext(ctx, "SET ? ?", "lang", "go")
    n, _ := res.RowsAffected()
    var v string
    err = db.QueryRowContext(ctx, "GET ?", "lang").Scan(&v)
    fmt.Println(n, v, err)
    err = db.QueryRowContext(ctx, "GET ?", "missing").Scan(&v)
    fmt.Println(errors.Is(err, sql.ErrNoRows))
    var dest int
    fmt.Println(sql.ConvertAssign(driver.ScanContext{}, &dest, "42"), dest)
}
''',
expectedStdout='1 go <nil>\ntrue\n<nil> 42\n',
challenge='Extend the example so a query with the wrong number of arguments fails: call db.ExecContext(ctx, "SET ? ?", "only-one") and print whether an error was returned.',
solution=r'''package main

import (
    "context"
    "database/sql"
    "database/sql/driver"
    "errors"
    "fmt"
    "strings"
)

type d struct{}
type c struct{}
type s struct{ q string }

func (d) Open(string) (driver.Conn, error)      { return c{}, nil }
func (c) Prepare(q string) (driver.Stmt, error) { return s{q}, nil }
func (c) Close() error                          { return nil }
func (c) Begin() (driver.Tx, error)             { return nil, errors.New("no") }
func (s) Close() error                          { return nil }
func (x s) NumInput() int                       { return strings.Count(x.q, "?") }
func (s) Exec([]driver.Value) (driver.Result, error) {
    return driver.RowsAffected(1), nil
}
func (s) Query([]driver.Value) (driver.Rows, error) { return nil, errors.New("no") }

func main() {
    sql.Register("mem", d{})
    db, _ := sql.Open("mem", "")
    _, err := db.ExecContext(context.Background(), "SET ? ?", "only-one")
    fmt.Println(err != nil)
}
''',
solutionStdout='true\n',
question='Why use placeholders instead of formatting values into the SQL string?',
correct='The driver sends values separately from the SQL text, so they can never be parsed as SQL',
wrong=['Placeholders make queries run in parallel', 'database/sql forbids string literals'],
reasoning='SQL injection happens when data is interpreted as code. Placeholders keep data and code apart by construction.',
sourceURL=PKG+'database/sql',
additionalReadings=[dict(title='database/sql/driver', url=PKG+'database/sql/driver', section='Driver interfaces'), dict(title='Accessing databases', url='https://go.dev/doc/database/', section='Tutorial')]),

dict(key='embed-files', stage=STAGE, title='Embedding files in the binary with embed',
body=[
'A //go:embed directive above a package-level variable copies files into the compiled binary at build time. A string or []byte variable takes exactly one file; an embed.FS variable takes many files and directories, matched by patterns such as static/* or templates.',
'embed.FS implements fs.FS, fs.ReadDirFS and fs.ReadFileFS, so it plugs into http.FileServerFS, template.ParseFS and fs.WalkDir. Paths are slash-separated and relative to the source file\'s directory; patterns cannot contain .. and files whose names start with . or _ are excluded unless the pattern names them or uses the all: prefix.',
'The package must import embed (a blank import is enough when only string or []byte variables are used). Embedded data is read-only and requires no deployment step, which makes single-binary tools and servers easy to ship.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/site\n\ngo 1.27\n'),
f('main.go', r'''package main

import (
    "embed"
    "fmt"
    "io/fs"
    "strings"
)

//go:embed version.txt
var version string

//go:embed static
var static embed.FS

func main() {
    fmt.Println("version", strings.TrimSpace(version))
    fs.WalkDir(static, ".", func(p string, d fs.DirEntry, err error) error {
        if err == nil && !d.IsDir() {
            data, _ := static.ReadFile(p)
            fmt.Printf("%s %d bytes\n", p, len(data))
        }
        return err
    })
}
'''),
f('version.txt', '1.27.2\n'),
f('static/index.html', '<h1>embedded</h1>\n'),
f('static/css/site.css', 'h1 { color: teal; }\n'),
f('static/.hidden', 'not embedded by default\n'),
],
projectSolutionFiles=[f('main.go', r'''package main

import (
    "embed"
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "strings"
)

//go:embed version.txt
var version string

//go:embed static
var static embed.FS

func main() {
    fmt.Println("version", strings.TrimSpace(version))
    srv := httptest.NewServer(http.FileServerFS(static))
    defer srv.Close()
    resp, err := http.Get(srv.URL + "/static/index.html")
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    body, _ := io.ReadAll(resp.Body)
    fmt.Print(resp.StatusCode, " ", string(body))
}
''')],
projectInstructions='Go 1.27, standard library only. Create the files (including static/.hidden), then run:\ngo run .\nThe walk lists static/css/site.css and static/index.html, but not .hidden.\nPractice: serve the embedded directory over HTTP with http.FileServerFS and fetch /static/index.html. Replace main.go with the worked answer.',
projectChecks=[
dict(name='embedded files, hidden file excluded', args=['run', '.'], stdout='version 1.27.2\nstatic/css/site.css 20 bytes\nstatic/index.html 18 bytes\n'),
dict(name='all: prefix includes dot files', args=['run', '.'], mutations=[dict(path='main.go', find='//go:embed static\n', replace='//go:embed all:static\n')],
     stdout='version 1.27.2\nstatic/.hidden 24 bytes\nstatic/css/site.css 20 bytes\nstatic/index.html 18 bytes\n'),
dict(name='patterns cannot escape the package', args=['build', '-o', '/dev/null', '.'], exit=1,
     mutations=[dict(path='main.go', find='//go:embed version.txt\n', replace='//go:embed ../version.txt\n')], outputContains=['invalid pattern syntax']),
dict(name='answer serves embedded files', args=['run', '.'], useSolution=True, stdout='version 1.27.2\n200 <h1>embedded</h1>\n'),
],
challenge='Serve the embedded static directory over HTTP with http.FileServerFS and fetch /static/index.html.',
question='Why is static/.hidden missing from the embedded file system?',
correct='Directory patterns skip files starting with . or _ unless all: is used',
wrong=['embed only includes .html and .css files', 'Hidden files are too small to embed'],
reasoning='The default excludes dot and underscore files, such as editor backups. all:static includes them deliberately.',
sourceURL=PKG+'embed'),

dict(key='legacy-and-system', stage=STAGE, title='Classic packages: log, io/ioutil, math/rand v1, os/user, time/tzdata and structs',
body=[
'The classic log package writes timestamped lines to standard error; log.New makes loggers with a prefix and flags such as log.Lshortfile, and Fatal/Panic variants exit or panic after logging. New services prefer log/slog, but log remains common in small tools.',
'io/ioutil is deprecated since Go 1.16: its functions moved to io and os (ioutil.ReadAll is io.ReadAll, ioutil.ReadFile is os.ReadFile). math/rand (v1) is kept for compatibility; since Go 1.20 its global functions are randomly seeded, and new code should use math/rand/v2.',
'os/user looks up the current user and groups. time/tzdata embeds the time-zone database into the binary (about 450 KB), so time.LoadLocation works on systems without zoneinfo, such as minimal containers; importing it for its side effect is enough. Package structs (Go 1.23) provides HostLayout, a marker field that requests the platform\'s C memory layout for a struct passed to foreign code.',
],
code=r'''package main

import (
    "bytes"
    "fmt"
    "io/ioutil"
    "log"
    "math/rand"
    "os/user"
    "strings"
    "structs"
    "time"
    _ "time/tzdata"
    "unsafe"
)

type cPoint struct {
    _    structs.HostLayout
    X, Y int32
}

func main() {
    var buf bytes.Buffer
    l := log.New(&buf, "app: ", 0)
    l.Printf("started %d workers", 4)
    fmt.Print(buf.String())
    data, _ := ioutil.ReadAll(strings.NewReader("deprecated but working"))
    fmt.Println(string(data))
    r := rand.New(rand.NewSource(1))
    fmt.Println(r.Intn(100) == rand.New(rand.NewSource(1)).Intn(100))
    u, err := user.Current()
    fmt.Println(err == nil && u.Username != "")
    tokyo, err := time.LoadLocation("Asia/Tokyo")
    t := time.Date(2026, 10, 17, 0, 0, 0, 0, time.UTC).In(tokyo)
    fmt.Println(t.Format("15:04 MST"), err)
    fmt.Println(unsafe.Sizeof(cPoint{}))
}
''',
expectedStdout='app: started 4 workers\ndeprecated but working\ntrue\ntrue\n09:00 JST <nil>\n8\n',
challenge='Rewrite the ioutil.ReadAll call with its modern replacement and print the result; then use math/rand/v2 with rand.NewPCG(1, 1) for a reproducible IntN(100).',
solution=r'''package main

import (
    "fmt"
    "io"
    "math/rand/v2"
    "strings"
)

func main() {
    data, _ := io.ReadAll(strings.NewReader("modern"))
    fmt.Println(string(data))
    a := rand.New(rand.NewPCG(1, 1)).IntN(100)
    b := rand.New(rand.NewPCG(1, 1)).IntN(100)
    fmt.Println(a == b)
}
''',
solutionStdout='modern\ntrue\n',
question='Why import _ "time/tzdata" in a binary for a minimal container?',
correct='It embeds the time-zone database so LoadLocation works without system zoneinfo files',
wrong=['It sets the container\'s local time zone', 'It makes time.Now faster'],
reasoning='LoadLocation normally reads /usr/share/zoneinfo. Scratch or distroless images lack it; tzdata is the embedded fallback.',
sourceURL=PKG+'time/tzdata',
additionalReadings=[dict(title='log', url=PKG+'log', section='Logger'), dict(title='structs', url=PKG+'structs', section='HostLayout'), dict(title='io/ioutil', url=PKG+'io/ioutil', section='Deprecated')]),

dict(key='expvar-syslog', stage=STAGE, title='Exported metrics with expvar and logging to syslog',
body=[
'expvar publishes named variables (Int, Float, String, Map, Func) and serves them as JSON at /debug/vars when the package is imported by a program with an HTTP server. It is a dependency-free way to expose counters for monitoring; expvar.Handler returns the handler for custom muxes.',
'log/syslog writes to the system log daemon, locally through a Unix socket or remotely over UDP or TCP with syslog.Dial. Each message carries a priority, a facility and a tag. It is not available on Windows or Plan 9.',
'For new services, structured logs to standard output collected by the platform, and metrics through a client library, are usual. expvar and syslog remain useful for small daemons and legacy integration.',
],
code=r'''package main

import (
    "encoding/json"
    "expvar"
    "fmt"
    "log/syslog"
    "net"
    "net/http/httptest"
    "strings"
)

var requests = expvar.NewInt("requests")

func main() {
    requests.Add(3)
    expvar.NewMap("byStatus").Add("200", 2)
    rec := httptest.NewRecorder()
    expvar.Handler().ServeHTTP(rec, httptest.NewRequest("GET", "/debug/vars", nil))
    var vars map[string]any
    json.Unmarshal(rec.Body.Bytes(), &vars)
    fmt.Println(vars["requests"], vars["byStatus"])
    pc, err := net.ListenPacket("udp", "127.0.0.1:0")
    if err != nil {
        panic(err)
    }
    defer pc.Close()
    w, err := syslog.Dial("udp", pc.LocalAddr().String(), syslog.LOG_WARNING|syslog.LOG_DAEMON, "guide")
    if err != nil {
        panic(err)
    }
    w.Warning("disk almost full")
    buf := make([]byte, 512)
    n, _, _ := pc.ReadFrom(buf)
    msg := string(buf[:n])
    fmt.Println(strings.HasPrefix(msg, "<28>"), strings.Contains(msg, "guide["), strings.HasSuffix(strings.TrimSpace(msg), "disk almost full"))
}
''',
expectedStdout='3 map[200:2]\ntrue true true\n',
challenge='Publish an expvar.Func named "uptimeKnown" that returns true, and read it back through expvar.Get(...).String().',
solution=r'''package main

import (
    "expvar"
    "fmt"
)

func main() {
    expvar.Publish("uptimeKnown", expvar.Func(func() any { return true }))
    fmt.Println(expvar.Get("uptimeKnown").String())
}
''',
solutionStdout='true\n',
question='What does the <28> at the start of the syslog message encode?',
correct='The priority: facility daemon (3) × 8 plus severity warning (4)',
wrong=['The message length', 'The process ID'],
reasoning='Syslog priority is facility*8 + severity. LOG_DAEMON is 3 and LOG_WARNING is 4, giving 28.',
sourceURL=PKG+'expvar',
additionalReadings=[dict(title='log/syslog', url=PKG+'log/syslog', section='Dial')]),
]

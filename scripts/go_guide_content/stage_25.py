STAGE = '25 · Networking in depth'
PKG = 'https://pkg.go.dev/'

LESSONS = [
dict(key='url-cookiejar', stage=STAGE, title='URLs with net/url and client cookies with net/http/cookiejar',
body=[
'url.Parse splits a URL into Scheme, User, Host, Path, RawQuery and Fragment, and decodes percent-escapes in the path. Query() parses the query into url.Values, a map[string][]string; Values.Encode sorts keys and escapes values. Build URLs by setting fields or using JoinPath (Go 1.19) rather than concatenating strings, which breaks on special characters.',
'url.QueryEscape escapes a value for a query string (spaces become +), while url.PathEscape escapes a path segment (spaces become %20). ResolveReference resolves relative links the way a browser does. Go 1.27 adds URL.Clone and Values.Clone for safe copies.',
'An http.Client ignores cookies unless it has a Jar. cookiejar.New returns an in-memory jar that stores Set-Cookie responses and sends matching cookies back, following domain and path rules; pass publicsuffix.List from golang.org/x/net to stop sites setting cookies for whole top-level domains.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/cookiejar"
    "net/http/httptest"
    "net/url"
)

func main() {
    u, _ := url.Parse("https://ada@example.com:8443/docs/go%20guide?lang=go&tag=a&tag=b#intro")
    fmt.Println(u.Scheme, u.User.Username(), u.Hostname(), u.Port(), u.Path, u.Fragment)
    q := u.Query()
    fmt.Println(q["tag"], q.Get("lang"))
    q.Set("page", "2 of 3")
    u.RawQuery = q.Encode()
    fmt.Println(u.RawQuery)
    base, _ := url.Parse("https://example.com/a/b/")
    ref, _ := url.Parse("../c?x=1")
    fmt.Println(base.ResolveReference(ref), base.JoinPath("x y"), url.PathEscape("x y"), url.QueryEscape("x y"))
    copyURL := u.Clone()
    copyURL.Host = "other.test"
    fmt.Println(u.Host != copyURL.Host)
    srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if c, err := r.Cookie("session"); err == nil {
            fmt.Fprint(w, "welcome back ", c.Value)
            return
        }
        http.SetCookie(w, &http.Cookie{Name: "session", Value: "s1", Path: "/"})
        fmt.Fprint(w, "new visitor")
    }))
    defer srv.Close()
    jar, _ := cookiejar.New(nil)
    client := &http.Client{Jar: jar}
    for range 2 {
        resp, _ := client.Get(srv.URL)
        body, _ := io.ReadAll(resp.Body)
        resp.Body.Close()
        fmt.Println(string(body))
    }
}
''',
expectedStdout='https ada example.com 8443 /docs/go guide intro\n[a b] go\nlang=go&page=2+of+3&tag=a&tag=b\nhttps://example.com/a/c?x=1 https://example.com/a/b/x%20y x%20y x+y\ntrue\nnew visitor\nwelcome back s1\n',
challenge='Build the URL https://api.example.com/v1/search with query parameters q="go & rust" and limit=10 using url.URL and url.Values, and print it.',
solution=r'''package main

import (
    "fmt"
    "net/url"
)

func main() {
    q := url.Values{}
    q.Set("q", "go & rust")
    q.Set("limit", "10")
    u := url.URL{Scheme: "https", Host: "api.example.com", Path: "/v1/search", RawQuery: q.Encode()}
    fmt.Println(u.String())
}
''',
solutionStdout='https://api.example.com/v1/search?limit=10&q=go+%26+rust\n',
question='Why does a plain http.Client not send cookies back on the second request?',
correct='It has no Jar; cookies are only stored and resent when Client.Jar is set',
wrong=['Cookies require HTTPS', 'The server must set Max-Age'],
reasoning='Cookie handling lives in the jar. Without one, Set-Cookie headers are ignored by the client.',
sourceURL=PKG+'net/url',
additionalReadings=[dict(title='net/http/cookiejar', url=PKG+'net/http/cookiejar', section='Jar')]),

dict(key='httptrace-httputil', stage=STAGE, title='Request tracing with httptrace and proxies with httputil',
body=[
'net/http/httptrace attaches hooks to a request\'s context: DNS start and done, connection acquisition (with GotConnInfo.Reused telling you whether keep-alive worked), TLS handshake, first response byte. It is the tool for explaining slow requests and confirming connection reuse.',
'net/http/httputil provides DumpRequest and DumpResponse for debugging wire formats, and ReverseProxy for forwarding requests to a backend. Configure the proxy with a Rewrite function (Go 1.20), which receives both the inbound and outbound request and is safer than the older Director because it handles hop-by-hop and forwarding headers correctly; SetXForwarded adds X-Forwarded-For and friends.',
'A reverse proxy should set timeouts on its Transport and limit request sizes, like any server. Never dump requests containing credentials into logs.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "net/http/httptrace"
    "net/http/httputil"
    "net/url"
    "strings"
)

func main() {
    backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "backend saw %s xff=%t", r.URL.Path, r.Header.Get("X-Forwarded-For") != "")
    }))
    defer backend.Close()
    target, _ := url.Parse(backend.URL)
    proxy := &httputil.ReverseProxy{Rewrite: func(pr *httputil.ProxyRequest) {
        pr.SetURL(target)
        pr.SetXForwarded()
    }}
    front := httptest.NewServer(proxy)
    defer front.Close()
    var reused []bool
    trace := &httptrace.ClientTrace{GotConn: func(info httptrace.GotConnInfo) { reused = append(reused, info.Reused) }}
    for range 2 {
        req, _ := http.NewRequest("GET", front.URL+"/api/items", nil)
        req = req.WithContext(httptrace.WithClientTrace(req.Context(), trace))
        resp, err := http.DefaultClient.Do(req)
        if err != nil {
            panic(err)
        }
        body, _ := io.ReadAll(resp.Body)
        resp.Body.Close()
        fmt.Println(string(body))
    }
    fmt.Println("connections reused:", reused)
    req, _ := http.NewRequest("POST", "http://example.com/submit", strings.NewReader("a=1"))
    dump, _ := httputil.DumpRequestOut(req, true)
    fmt.Println(strings.Split(string(dump), "\r\n")[0])
}
''',
expectedStdout='backend saw /api/items xff=true\nbackend saw /api/items xff=true\nconnections reused: [false true]\nPOST /submit HTTP/1.1\n',
challenge='Add a Rewrite step that strips an /api prefix before forwarding, so a request for /api/items reaches the backend as /items.',
solution=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "net/http/httputil"
    "net/url"
    "strings"
)

func main() {
    backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprint(w, r.URL.Path)
    }))
    defer backend.Close()
    target, _ := url.Parse(backend.URL)
    proxy := &httputil.ReverseProxy{Rewrite: func(pr *httputil.ProxyRequest) {
        pr.SetURL(target)
        pr.Out.URL.Path = strings.TrimPrefix(pr.In.URL.Path, "/api")
    }}
    front := httptest.NewServer(proxy)
    defer front.Close()
    resp, err := http.Get(front.URL + "/api/items")
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    body, _ := io.ReadAll(resp.Body)
    fmt.Println(string(body))
}
''',
solutionStdout='/items\n',
question='What does GotConnInfo.Reused tell you?',
correct='Whether the request used an existing keep-alive connection instead of dialling',
wrong=['Whether the response was cached', 'Whether TLS session resumption happened'],
reasoning='Reuse avoids TCP and TLS setup. Seeing false on every request reveals bodies not being closed or drained.',
sourceURL=PKG+'net/http/httputil#ReverseProxy',
additionalReadings=[dict(title='net/http/httptrace', url=PKG+'net/http/httptrace', section='ClientTrace')]),

dict(key='net-http-pprof', stage=STAGE, title='Live profiling endpoints with net/http/pprof',
body=[
'Importing net/http/pprof registers handlers under /debug/pprof/ on http.DefaultServeMux: an index, goroutine, heap, allocs, block, mutex and threadcreate profiles, a 30-second CPU profile at /debug/pprof/profile, an execution trace at /debug/pprof/trace, and, since Go 1.27, goroutineleak. go tool pprof http://host/debug/pprof/heap fetches and analyses one directly.',
'Expose these endpoints only on a private listener or behind authentication: they reveal internals and the CPU and trace endpoints are expensive. A common pattern is a second server on localhost:6060 that serves http.DefaultServeMux, while public traffic uses its own mux.',
'The handlers can also be mounted explicitly on any mux with pprof.Index, pprof.Profile, pprof.Symbol, pprof.Trace and pprof.Handler(name), which avoids relying on the default mux at all.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "net/http/pprof"
    "strings"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/debug/pprof/", pprof.Index)
    mux.Handle("/debug/pprof/goroutine", pprof.Handler("goroutine"))
    srv := httptest.NewServer(mux)
    defer srv.Close()
    get := func(path string) string {
        resp, err := http.Get(srv.URL + path)
        if err != nil {
            panic(err)
        }
        defer resp.Body.Close()
        b, _ := io.ReadAll(resp.Body)
        return string(b)
    }
    index := get("/debug/pprof/")
    fmt.Println(strings.Contains(index, "heap"), strings.Contains(index, "goroutineleak"))
    fmt.Println(strings.HasPrefix(get("/debug/pprof/goroutine?debug=1"), "goroutine profile: total"))
}
''',
expectedStdout='true true\ntrue\n',
challenge='Mount pprof.Handler("heap") on your own mux at /internal/heap and print whether fetching it with ?debug=1 returns text starting with "heap profile:".',
solution=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "net/http/pprof"
    "strings"
)

func main() {
    mux := http.NewServeMux()
    mux.Handle("/internal/heap", pprof.Handler("heap"))
    srv := httptest.NewServer(mux)
    defer srv.Close()
    resp, err := http.Get(srv.URL + "/internal/heap?debug=1")
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    b, _ := io.ReadAll(resp.Body)
    fmt.Println(strings.HasPrefix(string(b), "heap profile:"))
}
''',
solutionStdout='true\n',
question='Why serve net/http/pprof on a separate localhost listener?',
correct='The endpoints expose internals and expensive operations, so they must not be public',
wrong=['pprof only works on port 6060', 'The handlers conflict with JSON APIs'],
reasoning='Anyone reaching /debug/pprof/profile can make the server spend 30 seconds profiling and can read stack traces.',
sourceURL=PKG+'net/http/pprof'),

dict(key='textproto-smtp', stage=STAGE, title='Line protocols with net/textproto and email with net/smtp',
body=[
'net/textproto implements the shared machinery of text protocols such as SMTP, HTTP/1 headers, NNTP and FTP: reading CRLF lines, multi-line responses with numeric codes (ReadResponse), MIME-style headers (ReadMIMEHeader) and dot-encoded bodies. CanonicalMIMEHeaderKey turns content-type into Content-Type.',
'net/smtp is a small SMTP client: Dial or NewClient, then Hello, Auth, Mail, Rcpt, Data and Quit, or the one-call SendMail. PlainAuth refuses to send credentials over an unencrypted connection except to localhost. The package is frozen; production mail usually goes through a provider\'s API or a maintained library.',
'This lesson runs a tiny fake SMTP server on a loopback listener, built with textproto, and sends a message to it with net/smtp, so the whole protocol exchange happens without the internet.',
],
code=r'''package main

import (
    "fmt"
    "net"
    "net/smtp"
    "net/textproto"
    "strings"
)

func fakeServer(ln net.Listener, got chan<- string) {
    conn, err := ln.Accept()
    if err != nil {
        return
    }
    defer conn.Close()
    tp := textproto.NewConn(conn)
    tp.PrintfLine("220 fake.test ready")
    for {
        line, err := tp.ReadLine()
        if err != nil {
            return
        }
        switch verb := strings.ToUpper(strings.Fields(line)[0]); verb {
        case "EHLO", "HELO":
            tp.PrintfLine("250 fake.test")
        case "MAIL", "RCPT":
            tp.PrintfLine("250 ok")
        case "DATA":
            tp.PrintfLine("354 go ahead")
            body, _ := tp.ReadDotLines()
            got <- strings.Join(body, "|")
            tp.PrintfLine("250 queued")
        case "QUIT":
            tp.PrintfLine("221 bye")
            return
        default:
            tp.PrintfLine("502 not implemented")
        }
    }
}

func main() {
    fmt.Println(textproto.CanonicalMIMEHeaderKey("content-type"))
    ln, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        panic(err)
    }
    defer ln.Close()
    got := make(chan string, 1)
    go fakeServer(ln, got)
    msg := []byte("Subject: hi\r\n\r\nHello from net/smtp\r\n")
    err = smtp.SendMail(ln.Addr().String(), nil, "ada@example.com", []string{"bo@example.com"}, msg)
    fmt.Println(err)
    fmt.Println(<-got)
}
''',
expectedStdout='Content-Type\n<nil>\nSubject: hi||Hello from net/smtp\n',
challenge='Parse the header block "Content-Type: text/plain\\r\\nX-Lang: go\\r\\n\\r\\n" with textproto.NewReader(...).ReadMIMEHeader and print both values.',
solution=r'''package main

import (
    "bufio"
    "fmt"
    "net/textproto"
    "strings"
)

func main() {
    r := textproto.NewReader(bufio.NewReader(strings.NewReader("Content-Type: text/plain\r\nX-Lang: go\r\n\r\n")))
    h, err := r.ReadMIMEHeader()
    fmt.Println(h.Get("content-type"), h.Get("x-lang"), err)
}
''',
solutionStdout='text/plain go <nil>\n',
question='Why does smtp.PlainAuth refuse to authenticate to most servers over plain TCP?',
correct='It would send the password unencrypted; it only allows TLS or localhost',
wrong=['SMTP does not support passwords', 'PlainAuth is deprecated and always fails'],
reasoning='PLAIN authentication transmits credentials in base64, which is not encryption. The check protects against accidental leaks.',
sourceURL=PKG+'net/textproto',
additionalReadings=[dict(title='net/smtp', url=PKG+'net/smtp', section='SendMail')]),

dict(key='rpc-jsonrpc', stage=STAGE, title='Remote procedure calls with net/rpc and net/rpc/jsonrpc',
body=[
'net/rpc exposes the exported methods of a registered value over a connection. Methods must have the form func (t *T) Method(args A, reply *R) error. The client calls client.Call("Service.Method", args, &reply), or Go for an asynchronous call that completes on a channel. The default codec is gob.',
'net/rpc/jsonrpc swaps in a JSON-RPC 1.0 codec, so non-Go clients can talk to the same server. Both packages are frozen: they work and are stable, but new systems usually choose gRPC or plain HTTP/JSON APIs with explicit schemas and versioning.',
'Errors returned by a method arrive at the client as rpc.ServerError strings; transport failures return rpc.ErrShutdown or the network error.',
],
code=r'''package main

import (
    "errors"
    "fmt"
    "net"
    "net/rpc"
    "net/rpc/jsonrpc"
)

type Args struct{ A, B int }

type Calc struct{}

func (Calc) Multiply(args Args, reply *int) error {
    *reply = args.A * args.B
    return nil
}

func (Calc) Divide(args Args, reply *int) error {
    if args.B == 0 {
        return errors.New("divide by zero")
    }
    *reply = args.A / args.B
    return nil
}

func main() {
    server := rpc.NewServer()
    server.Register(Calc{})
    c1, s1 := net.Pipe()
    go server.ServeConn(s1)
    client := rpc.NewClient(c1)
    var product int
    fmt.Println(client.Call("Calc.Multiply", Args{6, 7}, &product), product)
    err := client.Call("Calc.Divide", Args{1, 0}, &product)
    var se rpc.ServerError
    fmt.Println(errors.As(err, &se), err)
    c2, s2 := net.Pipe()
    go server.ServeCodec(jsonrpc.NewServerCodec(s2))
    jc := jsonrpc.NewClient(c2)
    call := jc.Go("Calc.Multiply", Args{3, 3}, new(int), nil)
    <-call.Done
    fmt.Println(*call.Reply.(*int), call.Error)
    client.Close()
    jc.Close()
}
''',
expectedStdout='<nil> 42\ntrue divide by zero\n9 <nil>\n',
challenge='Add a method Sum(nums []int, reply *int) error to Calc and call it over JSON-RPC with []int{1, 2, 3, 4}.',
solution=r'''package main

import (
    "fmt"
    "net"
    "net/rpc"
    "net/rpc/jsonrpc"
)

type Calc struct{}

func (Calc) Sum(nums []int, reply *int) error {
    for _, n := range nums {
        *reply += n
    }
    return nil
}

func main() {
    server := rpc.NewServer()
    server.Register(Calc{})
    c, s := net.Pipe()
    go server.ServeCodec(jsonrpc.NewServerCodec(s))
    client := jsonrpc.NewClient(c)
    defer client.Close()
    var total int
    fmt.Println(client.Call("Calc.Sum", []int{1, 2, 3, 4}, &total), total)
}
''',
solutionStdout='<nil> 10\n',
question='What signature must a method have to be exported by net/rpc?',
correct='func (t *T) Name(args A, reply *R) error with exported names and types',
wrong=['func (t T) Name(args ...any) any', 'Any exported method'],
reasoning='rpc uses reflection to find methods with exactly one argument, one pointer reply and an error result.',
sourceURL=PKG+'net/rpc',
additionalReadings=[dict(title='net/rpc/jsonrpc', url=PKG+'net/rpc/jsonrpc', section='Codec')]),

dict(key='cgi-fcgi', stage=STAGE, title='CGI and FastCGI with net/http/cgi and net/http/fcgi',
body=[
'CGI runs a program per request: the web server passes request data in environment variables and standard input, and the program writes headers, a blank line and the body to standard output. cgi.Handler runs such a program from a Go server; cgi.Serve and cgi.Request let a Go program be the CGI script.',
'FastCGI keeps the application running and multiplexes requests over a socket, avoiding process start-up per request. fcgi.Serve(listener, handler) turns any http.Handler into a FastCGI application behind servers such as nginx or Apache, and fcgi.ProcessEnv exposes the extra variables those servers pass.',
'Both exist mainly for integration with traditional hosting. A Go service normally serves HTTP directly behind a reverse proxy.',
],
code=r'''package main

import (
    "fmt"
    "net"
    "net/http"
    "net/http/cgi"
    "net/http/fcgi"
    "net/http/httptest"
    "os"
    "path/filepath"
)

func main() {
    dir, _ := os.MkdirTemp("", "cgi")
    defer os.RemoveAll(dir)
    script := filepath.Join(dir, "hello.sh")
    os.WriteFile(script, []byte("#!/bin/sh\nprintf 'Content-Type: text/plain\\r\\n\\r\\nmethod=%s query=%s\\n' \"$REQUEST_METHOD\" \"$QUERY_STRING\"\n"), 0o755)
    h := &cgi.Handler{Path: script}
    rec := httptest.NewRecorder()
    h.ServeHTTP(rec, httptest.NewRequest("GET", "/cgi?lang=go", nil))
    fmt.Print(rec.Code, " ", rec.Header().Get("Content-Type"), " ", rec.Body.String())
    req, err := cgi.RequestFromMap(map[string]string{"REQUEST_METHOD": "POST", "SERVER_PROTOCOL": "HTTP/1.1", "REQUEST_URI": "/form?x=1"})
    fmt.Println(req.Method, req.URL.Query().Get("x"), err)
    ln, _ := net.Listen("tcp", "127.0.0.1:0")
    ln.Close()
    err = fcgi.Serve(ln, http.NotFoundHandler())
    fmt.Println(err != nil, len(fcgi.ProcessEnv(httptest.NewRequest("GET", "/", nil))))
}
''',
expectedStdout='200 text/plain method=GET query=lang=go\nPOST 1 <nil>\ntrue 0\n',
challenge='Change the CGI script to emit a "Status: 404 Not Found" header and show that cgi.Handler turns it into a 404 response.',
solution=r'''package main

import (
    "fmt"
    "net/http/cgi"
    "net/http/httptest"
    "os"
    "path/filepath"
)

func main() {
    dir, _ := os.MkdirTemp("", "cgi")
    defer os.RemoveAll(dir)
    script := filepath.Join(dir, "missing.sh")
    os.WriteFile(script, []byte("#!/bin/sh\nprintf 'Status: 404 Not Found\\r\\nContent-Type: text/plain\\r\\n\\r\\nno such page\\n'\n"), 0o755)
    rec := httptest.NewRecorder()
    (&cgi.Handler{Path: script}).ServeHTTP(rec, httptest.NewRequest("GET", "/x", nil))
    fmt.Print(rec.Code, " ", rec.Body.String())
}
''',
solutionStdout='404 no such page\n',
question='What is the main cost CGI has that FastCGI avoids?',
correct='Starting a new process for every request',
wrong=['Parsing HTTP headers', 'TLS handshakes'],
reasoning='FastCGI keeps one long-lived application process and sends many requests to it over a socket.',
sourceURL=PKG+'net/http/cgi',
additionalReadings=[dict(title='net/http/fcgi', url=PKG+'net/http/fcgi', section='Serve')]),
]

STAGE = '16 · Networking and HTTP'
HTTP = 'https://pkg.go.dev/net/http'

LESSONS = [
dict(key='tcp-echo', stage=STAGE, title='TCP servers and clients with package net', race=True,
body=[
'net.Listen("tcp", "127.0.0.1:0") opens a listener on a free port; ln.Addr() reports which. Accept returns a net.Conn for each client, and a server usually handles each connection in its own goroutine. net.Dial connects a client. A net.Conn is an io.Reader and io.Writer, so bufio, io.Copy and fmt work on it.',
'TCP is a byte stream, not a sequence of messages. One Write may arrive as several Reads or be merged with the next, so protocols need framing: newline-terminated lines, length prefixes, or a format such as HTTP.',
'Set deadlines with SetDeadline, SetReadDeadline and SetWriteDeadline; a blocked Read then fails with an error satisfying os.ErrDeadlineExceeded. Close the listener to stop Accept, and close each connection when its handler returns.',
],
code=r'''package main

import (
    "bufio"
    "fmt"
    "net"
    "strings"
)

func serve(ln net.Listener) {
    for {
        conn, err := ln.Accept()
        if err != nil {
            return
        }
        go func() {
            defer conn.Close()
            sc := bufio.NewScanner(conn)
            for sc.Scan() {
                fmt.Fprintln(conn, strings.ToUpper(sc.Text()))
            }
        }()
    }
}

func main() {
    ln, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        panic(err)
    }
    defer ln.Close()
    go serve(ln)
    conn, err := net.Dial("tcp", ln.Addr().String())
    if err != nil {
        panic(err)
    }
    defer conn.Close()
    replies := bufio.NewScanner(conn)
    for _, msg := range []string{"hello", "tcp"} {
        fmt.Fprintln(conn, msg)
        replies.Scan()
        fmt.Println(replies.Text())
    }
}
''',
expectedStdout='HELLO\nTCP\n',
challenge='Give the client a read deadline of 50ms, send nothing, and print whether the failed Read error matches os.ErrDeadlineExceeded with errors.Is.',
solution=r'''package main

import (
    "errors"
    "fmt"
    "net"
    "os"
    "time"
)

func main() {
    ln, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        panic(err)
    }
    defer ln.Close()
    go func() {
        conn, err := ln.Accept()
        if err == nil {
            defer conn.Close()
            time.Sleep(200 * time.Millisecond)
        }
    }()
    conn, err := net.Dial("tcp", ln.Addr().String())
    if err != nil {
        panic(err)
    }
    defer conn.Close()
    conn.SetReadDeadline(time.Now().Add(50 * time.Millisecond))
    _, err = conn.Read(make([]byte, 1))
    fmt.Println(errors.Is(err, os.ErrDeadlineExceeded))
}
''',
solutionStdout='true\n',
question='Why does a line-based protocol need bufio.Scanner on a TCP connection?',
correct='TCP delivers a byte stream, so message boundaries must be reconstructed',
wrong=['net.Conn cannot be read directly', 'Scanner encrypts the connection'],
reasoning='Reads return whatever bytes have arrived, which may be part of a line or several lines. Framing restores message boundaries.',
sourceURL='https://pkg.go.dev/net'),

dict(key='servemux-patterns', stage=STAGE, title='http.ServeMux routing patterns: methods and wildcards',
body=[
'Since Go 1.22, http.ServeMux patterns can include a method and wildcards: "GET /items/{id}" matches only GET (and HEAD) requests, and r.PathValue("id") returns the segment. "{path...}" matches the rest of the path, and "{$}" anchors a pattern to the exact path, so "/{$}" matches only the root.',
'When two patterns match, the more specific one wins, and registering two patterns that conflict without either being more specific panics. A path that matches a pattern with a different method gets 405 Method Not Allowed with an Allow header, not 404.',
'Handlers implement ServeHTTP(w, r); http.HandlerFunc adapts a function. Write headers before the body: the first Write sends status 200 if WriteHeader was not called.',
],
code=r'''package main

import (
    "fmt"
    "net/http"
    "net/http/httptest"
)

func routes() *http.ServeMux {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprint(w, "home")
    })
    mux.HandleFunc("GET /items/{id}", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "item %s", r.PathValue("id"))
    })
    mux.HandleFunc("POST /items", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusCreated)
    })
    mux.HandleFunc("GET /files/{path...}", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "file %s", r.PathValue("path"))
    })
    return mux
}

func main() {
    mux := routes()
    for _, req := range [][2]string{{"GET", "/"}, {"GET", "/items/42"}, {"POST", "/items"}, {"DELETE", "/items/42"}, {"GET", "/files/a/b.txt"}, {"GET", "/nope"}} {
        rec := httptest.NewRecorder()
        mux.ServeHTTP(rec, httptest.NewRequest(req[0], req[1], nil))
        fmt.Println(req[0], req[1], rec.Code, rec.Body.String())
    }
}
''',
expectedStdout='GET / 200 home\nGET /items/42 200 item 42\nPOST /items 201 \nDELETE /items/42 405 Method Not Allowed\n\nGET /files/a/b.txt 200 file a/b.txt\nGET /nope 404 404 page not found\n\n',
challenge='Add "GET /users/{name}/posts/{n}" that responds "name:n" and test it with /users/ada/posts/3.',
solution=r'''package main

import (
    "fmt"
    "net/http"
    "net/http/httptest"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /users/{name}/posts/{n}", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "%s:%s", r.PathValue("name"), r.PathValue("n"))
    })
    rec := httptest.NewRecorder()
    mux.ServeHTTP(rec, httptest.NewRequest("GET", "/users/ada/posts/3", nil))
    fmt.Println(rec.Code, rec.Body.String())
}
''',
solutionStdout='200 ada:3\n',
question='What does ServeMux return for DELETE /items/42 when only GET /items/{id} is registered?',
correct='405 Method Not Allowed, with an Allow header',
wrong=['404 Not Found', 'It runs the GET handler'],
reasoning='The path matches a registered pattern but the method does not, so the mux reports 405 and lists the allowed methods.',
sourceURL=HTTP+'#ServeMux',
additionalReadings=[dict(title='Routing enhancements for Go 1.22', url='https://go.dev/blog/routing-enhancements', section='Patterns')]),

dict(key='http-client', stage=STAGE, title='HTTP clients: timeouts, contexts and closing bodies', race=True,
body=[
'http.Get uses http.DefaultClient, which has no timeout: a server that never answers blocks forever. Create an http.Client with Timeout for a whole-request limit, or attach a context with http.NewRequestWithContext for per-call deadlines and cancellation.',
'Always close resp.Body, usually with defer resp.Body.Close() right after checking err. A non-2xx status is not an error: check resp.StatusCode yourself. Limit how much you read from untrusted servers with io.LimitReader.',
'Reuse one Client (and its Transport) across requests; it pools connections and is safe for concurrent use. Since Go 1.27 the HTTP/1 client drains a closed body automatically so the connection can be reused.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "strings"
    "time"
)

func main() {
    srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path == "/slow" {
            select {
            case <-time.After(time.Second):
            case <-r.Context().Done():
            }
            return
        }
        http.Error(w, "teapot", http.StatusTeapot)
    }))
    defer srv.Close()
    client := &http.Client{Timeout: 50 * time.Millisecond}
    resp, err := client.Get(srv.URL + "/brew")
    if err != nil {
        panic(err)
    }
    body, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
    resp.Body.Close()
    fmt.Println(resp.StatusCode, strings.TrimSpace(string(body)))
    _, err = client.Get(srv.URL + "/slow")
    fmt.Println(strings.Contains(err.Error(), "Client.Timeout exceeded"))
}
''',
expectedStdout='418 teapot\ntrue\n',
challenge='Instead of Client.Timeout, use a context with a 30ms deadline and http.NewRequestWithContext for the slow request; print whether errors.Is(err, context.DeadlineExceeded).',
solution=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "net/http"
    "net/http/httptest"
    "time"
)

func main() {
    srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        select {
        case <-time.After(time.Second):
        case <-r.Context().Done():
        }
    }))
    defer srv.Close()
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
    defer cancel()
    req, err := http.NewRequestWithContext(ctx, "GET", srv.URL, nil)
    if err != nil {
        panic(err)
    }
    _, err = srv.Client().Do(req)
    fmt.Println(errors.Is(err, context.DeadlineExceeded))
}
''',
solutionStdout='true\n',
question='Is a 404 response an error from client.Get?',
correct='No; err is nil and you must check resp.StatusCode',
wrong=['Yes, every non-2xx status returns an error', 'Only 5xx statuses are errors'],
reasoning='The client returns an error only when it could not get a response at all. Status codes are application-level results.',
sourceURL=HTTP+'#Client'),

dict(key='middleware', stage=STAGE, title='Middleware: wrapping handlers for logging, limits and recovery',
body=[
'Middleware is a function from http.Handler to http.Handler. It can act before and after calling next.ServeHTTP: logging, authentication, adding headers, measuring latency or recovering from panics. Chain middlewares by nesting them.',
'To observe the status code, wrap the ResponseWriter in a struct that records WriteHeader. http.ResponseController (Go 1.20) reaches optional features such as Flush and per-request deadlines through such wrappers if they implement Unwrap.',
'http.MaxBytesReader limits request bodies, protecting servers from huge uploads. http.TimeoutHandler bounds handler time. Go 1.25 added http.CrossOriginProtection, which rejects unsafe cross-origin browser requests using Fetch metadata headers, a modern defence against CSRF.',
],
code=r'''package main

import (
    "fmt"
    "io"
    "net/http"
    "net/http/httptest"
    "strings"
)

type statusRecorder struct {
    http.ResponseWriter
    status int
}

func (s *statusRecorder) WriteHeader(code int) {
    s.status = code
    s.ResponseWriter.WriteHeader(code)
}

func logStatus(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
        next.ServeHTTP(rec, r)
        fmt.Println("log:", r.Method, r.URL.Path, rec.status)
    })
}

func limitBody(n int64, next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        r.Body = http.MaxBytesReader(w, r.Body, n)
        next.ServeHTTP(w, r)
    })
}

func upload(w http.ResponseWriter, r *http.Request) {
    data, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, "too large", http.StatusRequestEntityTooLarge)
        return
    }
    fmt.Fprintf(w, "%d bytes", len(data))
}

func main() {
    h := logStatus(limitBody(8, http.HandlerFunc(upload)))
    for _, body := range []string{"small", "far too large"} {
        rec := httptest.NewRecorder()
        h.ServeHTTP(rec, httptest.NewRequest("POST", "/upload", strings.NewReader(body)))
        fmt.Println(rec.Body.String())
    }
}
''',
expectedStdout='log: POST /upload 200\n5 bytes\nlog: POST /upload 413\ntoo large\n\n',
challenge='Write a recoverPanic middleware that turns a handler panic into a 500 response with body "internal error", and show it with a handler that panics.',
solution=r'''package main

import (
    "fmt"
    "net/http"
    "net/http/httptest"
)

func recoverPanic(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if v := recover(); v != nil {
                http.Error(w, "internal error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

func main() {
    h := recoverPanic(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        panic("boom")
    }))
    rec := httptest.NewRecorder()
    h.ServeHTTP(rec, httptest.NewRequest("GET", "/", nil))
    fmt.Print(rec.Code, " ", rec.Body.String())
}
''',
solutionStdout='500 internal error\n',
question='How does middleware observe the status code a handler writes?',
correct='By wrapping the ResponseWriter and recording WriteHeader calls',
wrong=['By reading r.Response after next returns', 'ServeMux stores it in the request context'],
reasoning='The status goes to the ResponseWriter. A wrapper that embeds it and overrides WriteHeader sees the value as it passes through.',
sourceURL=HTTP+'#Handler',
additionalReadings=[dict(title='http.CrossOriginProtection (Go 1.25)', url=HTTP+'#CrossOriginProtection', section='CrossOriginProtection')]),

dict(key='graceful-shutdown', stage=STAGE, title='Server timeouts and graceful shutdown', race=True,
body=[
'An http.Server should set timeouts: ReadHeaderTimeout protects against slow clients that never finish headers, ReadTimeout and WriteTimeout bound whole requests, and IdleTimeout closes idle keep-alive connections. The zero values mean no limits.',
'srv.Shutdown(ctx) stops accepting new connections, closes idle ones and waits for active requests to finish, or for ctx to expire. ListenAndServe and Serve then return http.ErrServerClosed, which is the expected result and not a failure.',
'Typical main: start Serve in a goroutine, wait for SIGINT or SIGTERM with signal.NotifyContext, call Shutdown with a deadline, then exit. RegisterOnShutdown and BaseContext help close long-lived connections such as WebSockets.',
],
code=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "io"
    "net"
    "net/http"
    "time"
)

func main() {
    started := make(chan struct{})
    srv := &http.Server{
        ReadHeaderTimeout: time.Second,
        Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            close(started)
            time.Sleep(50 * time.Millisecond)
            fmt.Fprint(w, "finished in-flight request")
        }),
    }
    ln, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        panic(err)
    }
    served := make(chan error, 1)
    go func() { served <- srv.Serve(ln) }()
    reply := make(chan string, 1)
    go func() {
        resp, err := http.Get("http://" + ln.Addr().String())
        if err != nil {
            reply <- err.Error()
            return
        }
        defer resp.Body.Close()
        b, _ := io.ReadAll(resp.Body)
        reply <- string(b)
    }()
    <-started
    ctx, cancel := context.WithTimeout(context.Background(), time.Second)
    defer cancel()
    fmt.Println("shutdown:", srv.Shutdown(ctx))
    fmt.Println(<-reply)
    fmt.Println(errors.Is(<-served, http.ErrServerClosed))
}
''',
expectedStdout='shutdown: <nil>\nfinished in-flight request\ntrue\n',
challenge='Show what happens when Shutdown\'s context expires first: give it a 10ms deadline while the handler sleeps 200ms, and print whether the error is context.DeadlineExceeded.',
solution=r'''package main

import (
    "context"
    "errors"
    "fmt"
    "net"
    "net/http"
    "time"
)

func main() {
    started := make(chan struct{})
    srv := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        close(started)
        time.Sleep(200 * time.Millisecond)
    })}
    ln, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        panic(err)
    }
    go srv.Serve(ln)
    go http.Get("http://" + ln.Addr().String())
    <-started
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
    defer cancel()
    err = srv.Shutdown(ctx)
    fmt.Println(errors.Is(err, context.DeadlineExceeded))
    srv.Close()
}
''',
solutionStdout='true\n',
question='What does srv.Serve return after a successful Shutdown?',
correct='http.ErrServerClosed, which signals a normal stop',
wrong=['nil', 'context.Canceled'],
reasoning='Serve always returns a non-nil error. ErrServerClosed distinguishes a requested shutdown from a real failure.',
sourceURL=HTTP+'#Server.Shutdown'),

dict(key='tls-basics', stage=STAGE, title='TLS clients and servers with crypto/tls',
body=[
'HTTPS is HTTP over TLS. srv.ListenAndServeTLS(certFile, keyFile) serves it; a tls.Config controls versions, cipher suites and certificates. Go\'s defaults are secure: TLS 1.2 minimum for clients and servers, modern cipher suites, and certificate verification on by default.',
'Never set InsecureSkipVerify in production; it disables server authentication. For tests, httptest.NewTLSServer creates a server with a self-signed certificate, and srv.Client() returns a client that trusts exactly that certificate.',
'Go 1.24 enabled the hybrid post-quantum key exchange X25519MLKEM768 by default. Go 1.27 adds ML-DSA signature support in crypto/tls and crypto/x509, an MLKEM1024 key exchange, and the crypto/mldsa package.',
],
code=r'''package main

import (
    "crypto/tls"
    "fmt"
    "net/http"
    "net/http/httptest"
)

func main() {
    srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "tls %s", tls.VersionName(r.TLS.Version))
    }))
    defer srv.Close()
    resp, err := srv.Client().Get(srv.URL)
    if err != nil {
        panic(err)
    }
    var body [32]byte
    n, _ := resp.Body.Read(body[:])
    resp.Body.Close()
    fmt.Println(string(body[:n]))
    _, err = http.Get(srv.URL)
    fmt.Println("default client rejects self-signed:", err != nil)
}
''',
expectedStdout='tls TLS 1.3\ndefault client rejects self-signed: true\n',
challenge='Configure a test server with MaxVersion TLS 1.2 by setting srv.TLS before StartTLS (use httptest.NewUnstartedServer), and print the negotiated version name.',
solution=r'''package main

import (
    "crypto/tls"
    "fmt"
    "net/http"
    "net/http/httptest"
)

func main() {
    srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprint(w, tls.VersionName(r.TLS.Version))
    }))
    srv.TLS = &tls.Config{MaxVersion: tls.VersionTLS12}
    srv.StartTLS()
    defer srv.Close()
    resp, err := srv.Client().Get(srv.URL)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    var b [16]byte
    n, _ := resp.Body.Read(b[:])
    fmt.Println(string(b[:n]))
}
''',
solutionStdout='TLS 1.2\n',
question='Why does http.Get fail against httptest.NewTLSServer?',
correct='The default client verifies certificates and does not trust the test server\'s self-signed one',
wrong=['TLS is disabled in the default client', 'Test servers only speak HTTP/2'],
reasoning='srv.Client() is configured with the test certificate. The default client uses the system roots, which correctly reject it.',
sourceURL='https://pkg.go.dev/crypto/tls',
additionalReadings=[dict(title='Go 1.27 release notes: crypto/tls', url='https://go.dev/doc/go1.27#cryptotlspkgcryptotls', section='ML-DSA and MLKEM1024')]),

dict(key='json-api', stage=STAGE, title='A JSON API handler: decode, validate, respond',
body=[
'A robust JSON endpoint limits the body size, decodes into a struct with unknown fields rejected, validates the values, and responds with a consistent JSON error shape and the right status: 400 for malformed input, 422 for semantically invalid input, 201 for creation.',
'Set Content-Type: application/json before writing the body. Encode responses with json.NewEncoder(w).Encode; if encoding fails after headers were sent, all you can do is log, so encode simple, known-good types.',
'Keep handlers thin: parse and validate HTTP input, call ordinary functions that hold the logic, and map their errors to statuses. Those functions are then testable without HTTP.',
],
code=r'''package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "strings"
)

type createTask struct {
    Title string `json:"title"`
}

type apiError struct {
    Error string `json:"error"`
}

func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}

func create(w http.ResponseWriter, r *http.Request) {
    dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<10))
    dec.DisallowUnknownFields()
    var in createTask
    if err := dec.Decode(&in); err != nil {
        writeJSON(w, http.StatusBadRequest, apiError{"malformed JSON"})
        return
    }
    if strings.TrimSpace(in.Title) == "" {
        writeJSON(w, http.StatusUnprocessableEntity, apiError{"title is required"})
        return
    }
    writeJSON(w, http.StatusCreated, map[string]string{"title": in.Title})
}

func main() {
    for _, body := range []string{`{"title":"learn go"}`, `{"title":" "}`, `{"name":1}`} {
        rec := httptest.NewRecorder()
        create(rec, httptest.NewRequest("POST", "/tasks", strings.NewReader(body)))
        fmt.Print(rec.Code, " ", rec.Body.String())
    }
}
''',
expectedStdout='201 {"title":"learn go"}\n422 {"error":"title is required"}\n400 {"error":"malformed JSON"}\n',
challenge='Extend the handler so a title longer than 20 characters is rejected with 422 and "title too long"; test it with a 25-character title.',
solution=r'''package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "strings"
)

type createTask struct {
    Title string `json:"title"`
}

func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}

func create(w http.ResponseWriter, r *http.Request) {
    var in createTask
    if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<10)).Decode(&in); err != nil {
        writeJSON(w, http.StatusBadRequest, map[string]string{"error": "malformed JSON"})
        return
    }
    switch {
    case strings.TrimSpace(in.Title) == "":
        writeJSON(w, http.StatusUnprocessableEntity, map[string]string{"error": "title is required"})
    case len(in.Title) > 20:
        writeJSON(w, http.StatusUnprocessableEntity, map[string]string{"error": "title too long"})
    default:
        writeJSON(w, http.StatusCreated, map[string]string{"title": in.Title})
    }
}

func main() {
    rec := httptest.NewRecorder()
    body := `{"title":"` + strings.Repeat("x", 25) + `"}`
    create(rec, httptest.NewRequest("POST", "/tasks", strings.NewReader(body)))
    fmt.Print(rec.Code, " ", rec.Body.String())
}
''',
solutionStdout='422 {"error":"title too long"}\n',
question='Which status suits a well-formed JSON body whose title is empty?',
correct='422 Unprocessable Entity',
wrong=['400 Bad Request', '500 Internal Server Error'],
reasoning='400 means the request could not be parsed. 422 means it parsed but failed validation, which helps clients fix the right thing.',
sourceURL=HTTP),
]

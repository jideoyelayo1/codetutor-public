STAGE = '22 · Text, templates and encodings'
PKG = 'https://pkg.go.dev/'

LESSONS = [
dict(key='regexp', stage=STAGE, title='Regular expressions with regexp and regexp/syntax',
body=[
'regexp implements RE2 syntax with a guarantee: matching runs in time linear in the input, because the engine never backtracks. The price is that backreferences and look-around are not supported. Compile once with regexp.MustCompile at package level, since compiling is far more expensive than matching, and reuse the *Regexp, which is safe for concurrent use.',
'The method names follow a pattern: Find, FindAll, with String for string input, Submatch for capture groups and Index for positions. Named groups (?P<year>\\d{4}) or (?<year>\\d{4}) are read with SubexpIndex. ReplaceAllString expands $1 or ${name}; ReplaceAllStringFunc calls a function per match.',
'regexp/syntax parses patterns into an abstract syntax tree and simplifies them. It is what regexp uses internally, and is useful for tools that analyse or rewrite patterns. Prefer strings functions for fixed substrings; regular expressions are for structure.',
],
code=r'''package main

import (
    "fmt"
    "regexp"
    "regexp/syntax"
    "strings"
)

var date = regexp.MustCompile(`(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})`)

func main() {
    text := "released 2026-08-12, patched 2026-10-16"
    fmt.Println(date.FindAllString(text, -1))
    m := date.FindStringSubmatch(text)
    fmt.Println(m[date.SubexpIndex("month")])
    fmt.Println(date.ReplaceAllString(text, "${day}/${month}/${year}"))
    fmt.Println(regexp.MustCompile(`\s+`).ReplaceAllStringFunc("a  b   c", func(s string) string {
        return strings.Repeat("_", len(s))
    }))
    re, err := syntax.Parse(`a+b*|c`, syntax.Perl)
    fmt.Println(re.Op == syntax.OpAlternate, len(re.Sub), err)
    _, err = regexp.Compile(`(a)\1`)
    fmt.Println(err != nil)
}
''',
expectedStdout='[2026-08-12 2026-10-16]\n08\nreleased 12/08/2026, patched 16/10/2026\na__b___c\ntrue 2 <nil>\ntrue\n',
challenge='Extract every key=value pair from "a=1 bb=22 ccc=x" with one regexp and FindAllStringSubmatch, and print them as key:value.',
solution=r'''package main

import (
    "fmt"
    "regexp"
)

var pair = regexp.MustCompile(`(\w+)=(\w+)`)

func main() {
    for _, m := range pair.FindAllStringSubmatch("a=1 bb=22 ccc=x", -1) {
        fmt.Printf("%s:%s\n", m[1], m[2])
    }
}
''',
solutionStdout='a:1\nbb:22\nccc:x\n',
question='Why does regexp reject the backreference \\1?',
correct='RE2 guarantees linear-time matching, which backreferences would break',
wrong=['Backreferences need the Perl flag', 'Capture groups cannot be numbered in Go'],
reasoning='Backreferences make matching NP-hard in general. Go trades that feature for predictable performance on untrusted input.',
sourceURL=PKG+'regexp',
additionalReadings=[dict(title='regexp/syntax', url=PKG+'regexp/syntax', section='Syntax')]),

dict(key='text-template', stage=STAGE, title='text/template and its parse tree',
body=[
'text/template renders text from data: {{.Name}} reads a field, {{range .Items}}...{{end}} loops, {{if}}/{{else}} branches, {{with}} rebinds the dot, and {{template "name" .}} includes another template. Pipelines pass values through functions: {{.Price | printf "%.2f"}}. A leading or trailing dash, {{- or -}}, trims surrounding whitespace.',
'Functions are added with Funcs before parsing. Option("missingkey=error") turns a missing map key into an error instead of printing <no value>. Templates are safe for concurrent execution once parsed.',
'text/template/parse exposes the parsed tree: tmpl.Tree.Root lists ActionNodes, TextNodes and others. Tools use it to inspect which fields a template reads. Never use text/template for HTML: it does no escaping.',
],
code=r'''package main

import (
    "fmt"
    "os"
    "strings"
    "text/template"
    "text/template/parse"
)

const report = `{{define "row"}}- {{.Name | upper}}: {{printf "%.1f" .Score}}{{end -}}
{{range .}}{{template "row" .}}
{{end}}`

type result struct {
    Name  string
    Score float64
}

func main() {
    t := template.Must(template.New("report").Funcs(template.FuncMap{"upper": strings.ToUpper}).Parse(report))
    if err := t.Execute(os.Stdout, []result{{"ada", 9.25}, {"bo", 7}}); err != nil {
        fmt.Println(err)
    }
    actions := 0
    for _, n := range t.Lookup("row").Tree.Root.Nodes {
        if n.Type() == parse.NodeAction {
            actions++
        }
    }
    fmt.Println("actions in row:", actions)
    strict := template.Must(template.New("s").Option("missingkey=error").Parse("{{.missing}}"))
    fmt.Println(strict.Execute(os.Stdout, map[string]int{}) != nil)
}
''',
expectedStdout='- ADA: 9.2\n- BO: 7.0\nactions in row: 2\ntrue\n',
challenge='Write a template that prints a comma-separated list of names using range with $index, printing no comma before the first item, for []string{"go", "rust", "lean"}.',
solution=r'''package main

import (
    "os"
    "text/template"
)

func main() {
    t := template.Must(template.New("list").Parse(`{{range $i, $n := .}}{{if $i}}, {{end}}{{$n}}{{end}}` + "\n"))
    t.Execute(os.Stdout, []string{"go", "rust", "lean"})
}
''',
solutionStdout='go, rust, lean\n',
question='Why must HTML output use html/template rather than text/template?',
correct='text/template performs no escaping, so user data could inject markup or script',
wrong=['text/template cannot produce angle brackets', 'html/template is faster'],
reasoning='html/template understands HTML, CSS, JavaScript and URL contexts and escapes each correctly. text/template prints values verbatim.',
sourceURL=PKG+'text/template',
additionalReadings=[dict(title='text/template/parse', url=PKG+'text/template/parse', section='Nodes')]),

dict(key='html-template', stage=STAGE, title='Contextual escaping with html/template and package html',
body=[
'html/template has the same API as text/template but escapes every value according to where it appears: element text, attribute values, URLs, JavaScript and CSS each get their own escaping. A value placed in an href that starts with javascript: is replaced with #ZgotmplZ, a harmless marker.',
'To include trusted markup on purpose, wrap it in template.HTML (or template.URL, template.JS). Those types bypass escaping, so use them only for content you produced, never for user input.',
'Package html provides the low-level EscapeString and UnescapeString for the five characters < > & \' ". Use them for plain text outside templates.',
],
code=r'''package main

import (
    "fmt"
    "html"
    "html/template"
    "os"
)

func main() {
    page := template.Must(template.New("p").Parse(`<p title="{{.Title}}">{{.Body}}</p> <a href="{{.Link}}">x</a> {{.Safe}}` + "\n"))
    page.Execute(os.Stdout, map[string]any{
        "Title": `"quoted"`,
        "Body":  "<script>alert(1)</script>",
        "Link":  "javascript:alert(1)",
        "Safe":  template.HTML("<b>trusted</b>"),
    })
    fmt.Println(html.EscapeString(`a < b & "c"`), html.UnescapeString("&lt;ok&gt;"))
}
''',
expectedStdout='<p title="&#34;quoted&#34;">&lt;script&gt;alert(1)&lt;/script&gt;</p> <a href="#ZgotmplZ">x</a> <b>trusted</b>\na &lt; b &amp; &#34;c&#34; <ok>\n',
challenge='Render a link whose URL comes from data as /search?q={{.}} with the value "go & rust" and show that the query is URL-escaped.',
solution=r'''package main

import (
    "html/template"
    "os"
)

func main() {
    t := template.Must(template.New("q").Parse(`<a href="/search?q={{.}}">search</a>` + "\n"))
    t.Execute(os.Stdout, "go & rust")
}
''',
solutionStdout='<a href="/search?q=go%20%26%20rust">search</a>\n',
question='What does html/template do with a value "javascript:alert(1)" in an href?',
correct='Replaces it with #ZgotmplZ because the URL scheme is unsafe',
wrong=['Escapes the colon and keeps the link', 'Leaves it unchanged inside quotes'],
reasoning='The URL context filter only allows safe schemes such as http, https and mailto. Anything else becomes an inert placeholder.',
sourceURL=PKG+'html/template',
additionalReadings=[dict(title='html package', url=PKG+'html', section='EscapeString')]),

dict(key='tabwriter-scanner-utf16', stage=STAGE, title='Aligned columns, tokenising text and UTF-16',
body=[
'text/tabwriter aligns tab-separated cells into columns: create it with minimum width, tab width, padding and pad character, write lines with \\t between cells, then Flush. AlignRight and Debug flags adjust the layout. go doc and gofmt use it for alignment.',
'text/scanner tokenises Go-like text (identifiers, numbers, strings, comments) from an io.Reader with positions, which suits small configuration languages and calculators. Mode selects which token kinds to recognise.',
'unicode/utf16 converts between runes and UTF-16 code units, which Windows APIs, JavaScript strings and some file formats use. Characters outside the Basic Multilingual Plane become surrogate pairs: utf16.Encode([]rune("😀")) yields two units.',
],
code=r'''package main

import (
    "fmt"
    "os"
    "strings"
    "text/scanner"
    "text/tabwriter"
    "unicode/utf16"
)

func main() {
    w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
    fmt.Fprintln(w, "name\tlang\tstars")
    fmt.Fprintln(w, "gopher\tgo\t5")
    fmt.Fprintln(w, "ferris\trust\t4")
    w.Flush()
    var s scanner.Scanner
    s.Init(strings.NewReader(`total = price * 1.2 // tax`))
    for tok := s.Scan(); tok != scanner.EOF; tok = s.Scan() {
        fmt.Print(scanner.TokenString(tok), " ")
    }
    fmt.Println()
    units := utf16.Encode([]rune("a😀"))
    fmt.Printf("%d %#04x %s\n", len(units), units[1], string(utf16.Decode(units)))
}
''',
expectedStdout='name    lang  stars\ngopher  go    5\nferris  rust  4\nIdent "=" Ident "*" Float \n3 0xd83d a😀\n',
challenge='Use text/scanner to evaluate the sum in "1 + 2 + 39" by scanning Int tokens and adding their values.',
solution=r'''package main

import (
    "fmt"
    "strconv"
    "strings"
    "text/scanner"
)

func main() {
    var s scanner.Scanner
    s.Init(strings.NewReader("1 + 2 + 39"))
    sum := 0
    for tok := s.Scan(); tok != scanner.EOF; tok = s.Scan() {
        if tok == scanner.Int {
            n, _ := strconv.Atoi(s.TokenText())
            sum += n
        }
    }
    fmt.Println(sum)
}
''',
solutionStdout='42\n',
question='How many UTF-16 code units encode "😀"?',
correct='Two, a surrogate pair, because it lies outside the Basic Multilingual Plane',
wrong=['One, because it is a single rune', 'Four, the same as its UTF-8 length'],
reasoning='UTF-16 represents code points above U+FFFF with a high and a low surrogate.',
sourceURL=PKG+'text/tabwriter',
additionalReadings=[dict(title='text/scanner', url=PKG+'text/scanner', section='Scanner'), dict(title='unicode/utf16', url=PKG+'unicode/utf16', section='Encode')]),

dict(key='text-encodings', stage=STAGE, title='base64, base32, hex, ascii85, PEM and the encoding interfaces',
body=[
'encoding/base64 has StdEncoding, URLEncoding (with - and _ for URLs) and Raw variants without padding. encoding/base32 offers StdEncoding and HexEncoding. encoding/hex prints bytes as hex and Dump shows a hexdump. encoding/ascii85 is denser than base64 and used in PDF and PostScript.',
'encoding/pem wraps base64 data between -----BEGIN TYPE----- and -----END TYPE----- lines with optional headers, the format of certificates and keys. pem.Decode returns the first block and the remaining input.',
'Package encoding defines the interfaces that let types choose their own representation: TextMarshaler/TextUnmarshaler (used by JSON, XML and flag), BinaryMarshaler/BinaryUnmarshaler (used by gob), and since Go 1.24 TextAppender/BinaryAppender for allocation-free encoding.',
],
code=r'''package main

import (
    "encoding"
    "encoding/ascii85"
    "encoding/base32"
    "encoding/base64"
    "encoding/hex"
    "encoding/pem"
    "fmt"
    "net/netip"
)

func main() {
    data := []byte("go?>")
    fmt.Println(base64.StdEncoding.EncodeToString(data), base64.URLEncoding.EncodeToString(data), base64.RawStdEncoding.EncodeToString([]byte("a")))
    fmt.Println(base32.StdEncoding.EncodeToString(data), hex.EncodeToString(data))
    dst := make([]byte, ascii85.MaxEncodedLen(len(data)))
    n := ascii85.Encode(dst, data)
    fmt.Println(string(dst[:n]))
    block := &pem.Block{Type: "NOTE", Headers: map[string]string{"Lang": "go"}, Bytes: data}
    text := pem.EncodeToMemory(block)
    back, rest := pem.Decode(text)
    fmt.Printf("%s%s %q %d\n", text, back.Type, back.Bytes, len(rest))
    var m encoding.TextMarshaler = netip.MustParseAddr("::ffff:10.0.0.1")
    out, _ := m.MarshalText()
    fmt.Println(string(out))
}
''',
expectedStdout='Z28/Pg== Z28_Pg== YQ\nM5XT6PQ= 676f3f3e\nB5^!u\n-----BEGIN NOTE-----\nLang: go\n\nZ28/Pg==\n-----END NOTE-----\nNOTE "go?>" 0\n::ffff:10.0.0.1\n',
challenge='Give type RGB struct{ R, G, B uint8 } a MarshalText method producing "#rrggbb" and an UnmarshalText method that parses it back with encoding/hex; round-trip RGB{255, 128, 0}.',
solution=r'''package main

import (
    "encoding/hex"
    "fmt"
)

type RGB struct{ R, G, B uint8 }

func (c RGB) MarshalText() ([]byte, error) {
    return []byte("#" + hex.EncodeToString([]byte{c.R, c.G, c.B})), nil
}

func (c *RGB) UnmarshalText(b []byte) error {
    raw, err := hex.DecodeString(string(b[1:]))
    if err != nil || len(raw) != 3 {
        return fmt.Errorf("bad colour %q", b)
    }
    c.R, c.G, c.B = raw[0], raw[1], raw[2]
    return nil
}

func main() {
    text, _ := RGB{255, 128, 0}.MarshalText()
    var back RGB
    fmt.Println(string(text), back.UnmarshalText(text), back)
}
''',
solutionStdout='#ff8000 <nil> {255 128 0}\n',
question='Why use base64.URLEncoding for tokens placed in URLs?',
correct='It replaces + and / with - and _, which need no percent-escaping',
wrong=['It is shorter than StdEncoding', 'It encrypts the data'],
reasoning='The standard alphabet uses characters with special meaning in URLs. The URL-safe alphabet avoids them.',
sourceURL=PKG+'encoding',
additionalReadings=[dict(title='encoding/pem', url=PKG+'encoding/pem', section='Block')]),

dict(key='binary-hashes-bits', stage=STAGE, title='encoding/binary, checksums, maphash and math/bits',
body=[
'encoding/binary converts numbers to and from bytes in a chosen byte order: binary.BigEndian.PutUint32, binary.LittleEndian.Uint16, the Append variants added in Go 1.19, and Read/Write for fixed-size structs. Uvarint encodings store small numbers in fewer bytes, as protocol buffers do.',
'Package hash defines Hash, Hash32 and Hash64; hash/crc32 (with the IEEE and Castagnoli tables), hash/crc64 and hash/adler32 compute checksums that detect accidental corruption, not tampering. hash/maphash provides fast, randomly seeded hashing for hash tables; since Go 1.24 maphash.Comparable hashes any comparable value.',
'math/bits gives portable bit tricks that compile to single instructions: OnesCount, LeadingZeros, TrailingZeros, RotateLeft, Reverse and overflow-detecting Add64 and Mul64.',
],
code=r'''package main

import (
    "encoding/binary"
    "fmt"
    "hash"
    "hash/adler32"
    "hash/crc32"
    "hash/crc64"
    "hash/maphash"
    "math/bits"
)

func main() {
    buf := binary.BigEndian.AppendUint32(nil, 0xCAFEBABE)
    fmt.Printf("% x %#x\n", buf, binary.LittleEndian.Uint32(buf))
    v := binary.AppendUvarint(nil, 300)
    n, size := binary.Uvarint(v)
    fmt.Println(len(v), n, size)
    var h hash.Hash32 = crc32.NewIEEE()
    h.Write([]byte("hello"))
    fmt.Printf("%08x %08x\n", h.Sum32(), adler32.Checksum([]byte("hello")))
    fmt.Printf("%016x\n", crc64.Checksum([]byte("hello"), crc64.MakeTable(crc64.ISO)))
    seed := maphash.MakeSeed()
    fmt.Println(maphash.Comparable(seed, [2]int{1, 2}) == maphash.Comparable(seed, [2]int{1, 2}))
    hi, lo := bits.Mul64(1<<63, 4)
    fmt.Println(bits.OnesCount(255), bits.LeadingZeros64(1), hi, lo)
}
''',
expectedStdout='ca fe ba be 0xbebafeca\n2 300 2\n3610a686 062c0215\n3c3eeee2d8100000\ntrue\n8 63 2 0\n',
challenge='Encode a struct header{ Magic uint32; Len uint16 } with binary.Write in little-endian into a bytes.Buffer, print its bytes, then decode it back with binary.Read.',
solution=r'''package main

import (
    "bytes"
    "encoding/binary"
    "fmt"
)

type header struct {
    Magic uint32
    Len   uint16
}

func main() {
    var buf bytes.Buffer
    if err := binary.Write(&buf, binary.LittleEndian, header{0x01020304, 7}); err != nil {
        panic(err)
    }
    fmt.Printf("% x\n", buf.Bytes())
    var back header
    fmt.Println(binary.Read(&buf, binary.LittleEndian, &back), back.Magic == 0x01020304, back.Len)
}
''',
solutionStdout='04 03 02 01 07 00\n<nil> true 7\n',
question='Can a CRC32 checksum protect data against deliberate tampering?',
correct='No; it detects accidental corruption, while tampering needs a MAC or signature',
wrong=['Yes, CRC32 is a cryptographic hash', 'Only with the Castagnoli table'],
reasoning='An attacker can recompute or forge a CRC easily. Use crypto/hmac or digital signatures against adversaries.',
sourceURL=PKG+'encoding/binary',
additionalReadings=[dict(title='math/bits', url=PKG+'math/bits', section='Bit operations'), dict(title='hash/maphash', url=PKG+'hash/maphash', section='Comparable')]),

dict(key='encoding-csv', stage=STAGE, title='Reading and writing CSV with encoding/csv',
body=[
'csv.NewReader parses RFC 4180 CSV: quoted fields may contain commas, quotes ("") and newlines. Read returns one record; ReadAll returns them all. Set Comma for other separators such as tabs, Comment to skip lines, and FieldsPerRecord to enforce a fixed column count (0 means "same as the first record").',
'Errors are *csv.ParseError values with line and column. ReuseRecord avoids allocating a new slice per record when streaming large files.',
'csv.NewWriter quotes fields only when needed. Call Flush and then check Error, because writes are buffered.',
],
code=r'''package main

import (
    "encoding/csv"
    "errors"
    "fmt"
    "os"
    "strings"
)

func main() {
    in := "name,quote\nada,\"says \"\"hi\"\", ok\"\nbo,\"two\nlines\"\n"
    records, err := csv.NewReader(strings.NewReader(in)).ReadAll()
    fmt.Printf("%q %v\n", records[1:], err)
    bad := csv.NewReader(strings.NewReader("a,b\nc\n"))
    _, err = bad.ReadAll()
    var pe *csv.ParseError
    fmt.Println(errors.As(err, &pe), pe.Line)
    w := csv.NewWriter(os.Stdout)
    w.Write([]string{"plain", "with,comma", `with "quote"`})
    w.Flush()
    fmt.Println(w.Error())
}
''',
expectedStdout='[["ada" "says \\"hi\\", ok"] ["bo" "two\\nlines"]] <nil>\ntrue 2\nplain,"with,comma","with ""quote"""\n<nil>\n',
challenge='Parse tab-separated data "x\\t1\\ny\\t2\\n" by setting Comma to \'\\t\', and print the sum of the second column.',
solution=r'''package main

import (
    "encoding/csv"
    "fmt"
    "strconv"
    "strings"
)

func main() {
    r := csv.NewReader(strings.NewReader("x\t1\ny\t2\n"))
    r.Comma = '\t'
    rows, err := r.ReadAll()
    if err != nil {
        panic(err)
    }
    sum := 0
    for _, row := range rows {
        n, _ := strconv.Atoi(row[1])
        sum += n
    }
    fmt.Println(sum)
}
''',
solutionStdout='3\n',
question='Why did the second input fail with a ParseError on line 2?',
correct='FieldsPerRecord defaults to the first record\'s width, and line 2 has one field instead of two',
wrong=['CSV forbids single-column rows', 'Line 2 lacks a trailing comma'],
reasoning='A zero FieldsPerRecord means "match the first record". Set it to -1 to allow ragged rows.',
sourceURL=PKG+'encoding/csv'),

dict(key='encoding-xml', stage=STAGE, title='XML with encoding/xml: struct tags and token streams',
body=[
'encoding/xml maps structs to elements using tags: `xml:"name"` for child elements, `xml:"id,attr"` for attributes, `xml:",chardata"` for text, `xml:",innerxml"` for raw content and `xml:"a>b"` for nested paths. XMLName records the element name.',
'xml.Unmarshal decodes a whole document; xml.NewDecoder(r).Token streams StartElement, EndElement and CharData tokens, which handles large documents and selective extraction. MarshalIndent pretty-prints.',
'The decoder does not resolve external entities or fetch DTDs, which avoids XXE attacks. Namespaces appear in Name.Space.',
],
code=r'''package main

import (
    "encoding/xml"
    "fmt"
    "strings"
)

type Book struct {
    XMLName xml.Name `xml:"book"`
    ID      string   `xml:"id,attr"`
    Title   string   `xml:"title"`
    Authors []string `xml:"authors>author"`
}

func main() {
    doc := `<book id="go1"><title>The Go Guide</title><authors><author>Ada</author><author>Bo</author></authors></book>`
    var b Book
    fmt.Println(xml.Unmarshal([]byte(doc), &b), b.ID, b.Title, b.Authors)
    out, _ := xml.MarshalIndent(Book{ID: "x", Title: "T", Authors: []string{"C"}}, "", " ")
    fmt.Println(string(out))
    dec := xml.NewDecoder(strings.NewReader(doc))
    elements := 0
    for {
        tok, err := dec.Token()
        if err != nil {
            break
        }
        if _, ok := tok.(xml.StartElement); ok {
            elements++
        }
    }
    fmt.Println("elements:", elements)
}
''',
expectedStdout='<nil> go1 The Go Guide [Ada Bo]\n<book id="x">\n <title>T</title>\n <authors>\n  <author>C</author>\n </authors>\n</book>\nelements: 5\n',
challenge='Stream `<list><item n="1"/><item n="2"/><item n="3"/></list>` with a Decoder and sum the n attributes of the item elements.',
solution=r'''package main

import (
    "encoding/xml"
    "fmt"
    "strconv"
    "strings"
)

func main() {
    dec := xml.NewDecoder(strings.NewReader(`<list><item n="1"/><item n="2"/><item n="3"/></list>`))
    sum := 0
    for {
        tok, err := dec.Token()
        if err != nil {
            break
        }
        if se, ok := tok.(xml.StartElement); ok && se.Name.Local == "item" {
            for _, a := range se.Attr {
                if a.Name.Local == "n" {
                    v, _ := strconv.Atoi(a.Value)
                    sum += v
                }
            }
        }
    }
    fmt.Println(sum)
}
''',
solutionStdout='6\n',
question='What does the tag `xml:"authors>author"` mean?',
correct='Each slice element is an <author> nested inside an <authors> element',
wrong=['Authors is an attribute named "authors>author"', 'The field is renamed to "author" only'],
reasoning='a>b paths describe nesting, so the decoder walks into authors and collects every author child.',
sourceURL=PKG+'encoding/xml'),

dict(key='encoding-gob', stage=STAGE, title='Go-native binary streams with encoding/gob',
body=[
'encoding/gob serialises Go values in a self-describing binary format designed for Go-to-Go communication, as used by net/rpc. The first value of each type sends a type description, so streams of many values are compact.',
'Fields are matched by name, not position: the receiver may have extra or missing fields, and integer sizes may differ, which allows gentle evolution of types. Interface values must have their concrete types registered with gob.Register.',
'Gob is not a cross-language format and is not hardened against hostile input of unbounded size; use JSON or protocol buffers for public APIs, and bound inputs from untrusted sources.',
],
code=r'''package main

import (
    "bytes"
    "encoding/gob"
    "fmt"
)

type V1 struct {
    Name string
    Age  int
}

type V2 struct {
    Name  string
    Email string
}

type Shape interface{ Area() float64 }
type Square struct{ S float64 }

func (s Square) Area() float64 { return s.S * s.S }

func main() {
    var buf bytes.Buffer
    gob.NewEncoder(&buf).Encode(V1{"Ada", 36})
    var v2 V2
    fmt.Println(gob.NewDecoder(&buf).Decode(&v2), v2.Name, v2.Email == "")
    gob.Register(Square{})
    buf.Reset()
    var s Shape = Square{3}
    gob.NewEncoder(&buf).Encode(&s)
    var back Shape
    fmt.Println(gob.NewDecoder(&buf).Decode(&back), back.Area())
}
''',
expectedStdout='<nil> Ada true\n<nil> 9\n',
challenge='Encode three Point{X, Y int} values onto one gob stream with a single Encoder and decode them back in a loop until io.EOF; print them.',
solution=r'''package main

import (
    "bytes"
    "encoding/gob"
    "errors"
    "fmt"
    "io"
)

type Point struct{ X, Y int }

func main() {
    var buf bytes.Buffer
    enc := gob.NewEncoder(&buf)
    for i := range 3 {
        enc.Encode(Point{i, i * i})
    }
    dec := gob.NewDecoder(&buf)
    for {
        var p Point
        if err := dec.Decode(&p); errors.Is(err, io.EOF) {
            break
        }
        fmt.Println(p)
    }
}
''',
solutionStdout='{0 0}\n{1 1}\n{2 4}\n',
question='How does gob match struct fields between sender and receiver?',
correct='By field name, so added or removed fields are tolerated',
wrong=['By field position', 'By struct type name, so types must be identical'],
reasoning='Name matching lets V1 decode into V2: Name transfers, Age is dropped and Email stays zero.',
sourceURL=PKG+'encoding/gob'),

dict(key='encoding-asn1', stage=STAGE, title='ASN.1 DER with encoding/asn1',
body=[
'ASN.1 with DER encoding is the binary format beneath X.509 certificates, PKCS keys and many telecom protocols. encoding/asn1 marshals Go structs to DER and back, using tags such as `asn1:"optional"`, `asn1:"explicit,tag:0"` and `asn1:"utf8"`.',
'DER is a tag-length-value encoding: an INTEGER 5 is 02 01 05, a SEQUENCE is 30 followed by its length and contents. ObjectIdentifier represents OIDs such as 1.2.840.113549 used to name algorithms.',
'Most code reaches ASN.1 through crypto/x509 rather than directly. golang.org/x/crypto/cryptobyte is a safer, more flexible parser for new protocol code.',
],
code=r'''package main

import (
    "encoding/asn1"
    "fmt"
)

type Record struct {
    Version int
    Name    string `asn1:"utf8"`
    Algo    asn1.ObjectIdentifier
    Note    string `asn1:"optional,utf8"`
}

func main() {
    der, err := asn1.Marshal(5)
    fmt.Printf("% x %v\n", der, err)
    der, _ = asn1.Marshal(Record{Version: 1, Name: "go", Algo: asn1.ObjectIdentifier{1, 2, 840, 113549}})
    fmt.Printf("%x\n", der[:2])
    var back Record
    rest, err := asn1.Unmarshal(der, &back)
    fmt.Println(back.Version, back.Name, back.Algo, back.Note == "", len(rest), err)
}
''',
expectedStdout='02 01 05 <nil>\n300f\n1 go 1.2.840.113549 true 0 <nil>\n',
challenge='Marshal the OID 2.5.4.3 (the X.509 commonName attribute) and print its DER bytes in hex.',
solution=r'''package main

import (
    "encoding/asn1"
    "fmt"
)

func main() {
    der, err := asn1.Marshal(asn1.ObjectIdentifier{2, 5, 4, 3})
    fmt.Printf("% x %v\n", der, err)
}
''',
solutionStdout='06 03 55 04 03 <nil>\n',
question='What do the bytes 02 01 05 encode in DER?',
correct='An INTEGER (tag 02) of length 1 with value 5',
wrong=['A SEQUENCE of two elements', 'The string "5"'],
reasoning='DER is tag, length, value. Tag 0x02 is INTEGER, and the single content byte is 5.',
sourceURL=PKG+'encoding/asn1'),

dict(key='mime-mail', stage=STAGE, title='MIME types, multipart bodies, quoted-printable and mail messages',
body=[
'mime maps file extensions to types (mime.TypeByExtension(".json")), parses media-type headers with parameters (ParseMediaType) and encodes non-ASCII header words (mime.QEncoding). mime/quotedprintable encodes mostly-ASCII text for email bodies.',
'mime/multipart reads and writes multipart bodies, used by HTML form uploads and email attachments: a Writer creates parts with headers and a boundary, and a Reader iterates them with NextPart. http.Request.ParseMultipartForm builds on it.',
'net/mail parses RFC 5322 messages and addresses: mail.ReadMessage splits headers from the body, and mail.ParseAddress handles display names. Together these are what an email client needs below the network layer.',
],
code=r'''package main

import (
    "bytes"
    "fmt"
    "io"
    "mime"
    "mime/multipart"
    "mime/quotedprintable"
    "net/mail"
    "strings"
)

func main() {
    fmt.Println(mime.TypeByExtension(".json"))
    mt, params, _ := mime.ParseMediaType(`multipart/form-data; boundary=XYZ`)
    fmt.Println(mt, params["boundary"])
    fmt.Println(mime.QEncoding.Encode("utf-8", "Café"))
    var qp bytes.Buffer
    w := quotedprintable.NewWriter(&qp)
    w.Write([]byte("naïve = 1"))
    w.Close()
    fmt.Println(qp.String())
    var body bytes.Buffer
    mw := multipart.NewWriter(&body)
    mw.SetBoundary("XYZ")
    mw.WriteField("lang", "go")
    mw.Close()
    mr := multipart.NewReader(&body, "XYZ")
    part, _ := mr.NextPart()
    value, _ := io.ReadAll(part)
    fmt.Println(part.FormName(), string(value))
    msg, _ := mail.ReadMessage(strings.NewReader("From: Ada <ada@example.com>\r\nSubject: hi\r\n\r\nbody\r\n"))
    from, _ := mail.ParseAddress(msg.Header.Get("From"))
    rest, _ := io.ReadAll(msg.Body)
    fmt.Printf("%s %s %q\n", from.Name, msg.Header.Get("Subject"), rest)
}
''',
expectedStdout='application/json\nmultipart/form-data XYZ\n=?utf-8?q?Caf=C3=A9?=\nna=C3=AFve =3D 1\nlang go\nAda hi "body\\r\\n"\n',
challenge='Parse the address list "Ada <ada@example.com>, bo@example.com" with mail.ParseAddressList and print each address\'s Address field.',
solution=r'''package main

import (
    "fmt"
    "net/mail"
)

func main() {
    list, err := mail.ParseAddressList("Ada <ada@example.com>, bo@example.com")
    if err != nil {
        panic(err)
    }
    for _, a := range list {
        fmt.Println(a.Address)
    }
}
''',
solutionStdout='ada@example.com\nbo@example.com\n',
question='What does mime/multipart need to find part boundaries?',
correct='The boundary string from the Content-Type header\'s parameters',
wrong=['Fixed-size parts', 'A length header on every part'],
reasoning='Multipart bodies separate parts with --boundary lines. ParseMediaType extracts the boundary parameter for the Reader.',
sourceURL=PKG+'mime/multipart',
additionalReadings=[dict(title='net/mail', url=PKG+'net/mail', section='ReadMessage'), dict(title='mime/quotedprintable', url=PKG+'mime/quotedprintable', section='Writer')]),

dict(key='suffixarray-heap-ring', stage=STAGE, title='index/suffixarray, container/heap and container/ring',
body=[
'index/suffixarray builds a suffix array over a byte slice once, then answers substring queries in O(log n) per lookup: Lookup returns every offset of a pattern and FindAllIndex accepts a regular expression. It suits read-mostly search over a large text.',
'container/heap turns any type implementing heap.Interface (sort.Interface plus Push and Pop) into a binary heap: heap.Init, heap.Push, heap.Pop and heap.Fix keep the minimum at index 0. It is how you build priority queues, Dijkstra\'s algorithm and schedulers.',
'container/ring is a circular doubly linked list: Next, Prev, Move, Link and Do. It fits fixed-size round-robin buffers, though a slice with a moving index is often simpler.',
],
code=r'''package main

import (
    "container/heap"
    "container/ring"
    "fmt"
    "index/suffixarray"
    "slices"
)

type task struct {
    name     string
    priority int
}

type queue []task

func (q queue) Len() int           { return len(q) }
func (q queue) Less(i, j int) bool { return q[i].priority < q[j].priority }
func (q queue) Swap(i, j int)      { q[i], q[j] = q[j], q[i] }
func (q *queue) Push(x any)        { *q = append(*q, x.(task)) }
func (q *queue) Pop() any {
    old := *q
    t := old[len(old)-1]
    *q = old[:len(old)-1]
    return t
}

func main() {
    idx := suffixarray.New([]byte("banana bandana"))
    hits := idx.Lookup([]byte("ana"), -1)
    slices.Sort(hits)
    fmt.Println(hits)
    q := &queue{{"write", 3}, {"test", 1}, {"ship", 5}}
    heap.Init(q)
    heap.Push(q, task{"review", 2})
    for q.Len() > 0 {
        fmt.Print(heap.Pop(q).(task).name, " ")
    }
    fmt.Println()
    r := ring.New(3)
    for i := range 3 {
        r.Value = i
        r = r.Next()
    }
    r.Do(func(v any) { fmt.Print(v, " ") })
    fmt.Println()
}
''',
expectedStdout='[1 3 11]\ntest review write ship \n0 1 2 \n',
challenge='Use container/heap to find the three largest numbers in []int{5, 1, 9, 3, 7, 2} by keeping a min-heap of size three; print them in descending order.',
solution=r'''package main

import (
    "container/heap"
    "fmt"
    "slices"
)

type minHeap []int

func (h minHeap) Len() int           { return len(h) }
func (h minHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h minHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *minHeap) Pop() any {
    old := *h
    v := old[len(old)-1]
    *h = old[:len(old)-1]
    return v
}

func main() {
    h := &minHeap{}
    for _, v := range []int{5, 1, 9, 3, 7, 2} {
        heap.Push(h, v)
        if h.Len() > 3 {
            heap.Pop(h)
        }
    }
    top := []int(*h)
    slices.Sort(top)
    slices.Reverse(top)
    fmt.Println(top)
}
''',
solutionStdout='[9 7 5]\n',
question='What must a type implement to be used with container/heap?',
correct='sort.Interface plus Push(any) and Pop() any',
wrong=['Only Less', 'A Compare method returning int'],
reasoning='heap.Interface embeds sort.Interface for ordering and adds Push and Pop to grow and shrink the underlying slice.',
sourceURL=PKG+'container/heap',
additionalReadings=[dict(title='index/suffixarray', url=PKG+'index/suffixarray', section='Index'), dict(title='container/ring', url=PKG+'container/ring', section='Ring')]),
]

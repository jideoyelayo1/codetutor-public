STAGE = '07 · Packages and modules'
SPEC = 'https://go.dev/ref/spec'
MOD = 'https://go.dev/ref/mod'


def f(path, content):
    return dict(path=path, content=content)


LESSONS = [
dict(key='packages-visibility-init', stage=STAGE, title='Packages, exported names and initialisation order',
body=[
'A package is a directory of .go files sharing one package clause. Its import path is the module path plus the directory, so example.com/shop/price lives in shop/price. Identifiers starting with an upper-case letter are exported to other packages; everything else is private to the package, across all of its files.',
'Package initialisation runs once, before main: package-level variables are initialised in dependency order, then each file\'s init functions run. Imported packages initialise before the packages that import them. Keep init small; hidden work there makes programs hard to test.',
'A package should be named for what it provides (price, not utils), and its exported names should read well with the package qualifier: price.Format, not price.FormatPrice. Package main is special: it builds a command rather than a library.',
'This lesson is a two-package module. Run it as shown, then do the practice by changing only the price package.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/shop\n\ngo 1.27\n'),
f('main.go', r'''package main

import (
    "fmt"

    "example.com/shop/price"
)

func init() { fmt.Println("main init") }

func main() {
    fmt.Println(price.Format(1999))
}
'''),
f('price/price.go', r'''// Package price formats amounts stored in cents.
package price

import "fmt"

var currency = pick()

func pick() string {
    fmt.Println("price var")
    return "EUR"
}

func init() { fmt.Println("price init") }

// Format renders cents as a decimal amount with a currency code.
func Format(cents int) string {
    return fmt.Sprintf("%d.%02d %s", cents/100, cents%100, currency)
}
'''),
],
projectSolutionFiles=[f('price/price.go', r'''// Package price formats amounts stored in cents.
package price

import "fmt"

var currency = pick()

func pick() string {
    fmt.Println("price var")
    return "EUR"
}

func init() { fmt.Println("price init") }

// Format renders cents as a decimal amount with a currency code.
func Format(cents int) string {
    sign := ""
    if cents < 0 {
        sign, cents = "-", -cents
    }
    return fmt.Sprintf("%s%d.%02d %s", sign, cents/100, cents%100, currency)
}
''')],
projectInstructions='Go 1.27, standard library only. Create the three files, then from the module root run:\ngo run .\nExpected stdout: price var, price init, main init, then 19.99 EUR.\nPractice: make Format handle negative amounts so that Format(-250) is -2.50 EUR. Replace price/price.go with the worked answer and run go run . again.',
projectChecks=[
dict(name='initialisation order and output', args=['run', '.'], stdout='price var\nprice init\nmain init\n19.99 EUR\n'),
dict(name='unexported name is private', args=['build', '-o', '/dev/null', '.'], exit=1,
     mutations=[dict(path='main.go', find='price.Format(1999)', replace='price.currency')], outputContains=['name currency not exported by package price']),
dict(name='answer formats negative amounts', args=['run', '.'], useSolution=True, stdout='price var\nprice init\nmain init\n19.99 EUR\n',
     mutations=[]),
dict(name='answer negative case', args=['run', '.'], useSolution=True,
     mutations=[dict(path='main.go', find='price.Format(1999)', replace='price.Format(-250)')], stdout='price var\nprice init\nmain init\n-2.50 EUR\n'),
],
challenge='Make price.Format handle negative amounts so that Format(-250) returns "-2.50 EUR".',
question='In what order do package-level variables, init functions and main run?',
correct='Imported packages first; within a package, variables then init functions; main last',
wrong=['main first, then init functions lazily', 'init functions in alphabetical order of package name'],
reasoning='Initialisation follows the import graph. Each package finishes initialising its variables and running its inits before packages that import it start.',
sourceURL=SPEC+'#Package_initialization',
additionalReadings=[dict(title='Effective Go: package names', url='https://go.dev/doc/effective_go#package-names', section='Package names')]),

dict(key='go-directive-toolchain', stage=STAGE, title='The go and toolchain lines, GOTOOLCHAIN and versions',
body=[
'The go line in go.mod is a minimum: the module needs at least that language version, and the go command refuses to build it with an older toolchain unless it can switch. Since Go 1.21 the go command can download a newer toolchain automatically when go.mod demands one.',
'The optional toolchain line names a preferred toolchain for work inside this module, for example toolchain go1.27.2. GOTOOLCHAIN overrides the choice: local uses the installed toolchain, go1.27.2 forces a release, and go1.27.2+auto allows upgrades.',
'runtime.Version reports the toolchain that built the binary, and runtime/debug.ReadBuildInfo reports the module path, main version and dependency versions embedded at build time. go version -m binary prints the same information for an existing executable.',
],
code=r'''package main

import (
    "fmt"
    "runtime"
    "runtime/debug"
    "strings"
)

func main() {
    fmt.Println(strings.HasPrefix(runtime.Version(), "go1.27"))
    info, ok := debug.ReadBuildInfo()
    fmt.Println(ok, info.Path, info.GoVersion == runtime.Version())
}
''',
expectedStdout='true\ntrue guide.example/lesson true\n',
challenge='Print the main module path and the number of dependency modules reported by debug.ReadBuildInfo.',
solution=r'''package main

import (
    "fmt"
    "runtime/debug"
)

func main() {
    info, ok := debug.ReadBuildInfo()
    if !ok {
        fmt.Println("no build info")
        return
    }
    fmt.Println(info.Main.Path, len(info.Deps))
}
''',
solutionStdout='guide.example/lesson 0\n',
question='What does go 1.27 in go.mod mean?',
correct='The module requires at least Go 1.27 language semantics and toolchain',
wrong=['The module only builds with exactly Go 1.27.0', 'Dependencies must be at version 1.27'],
reasoning='Since Go 1.21 the go line is a mandatory minimum. Newer toolchains build it with 1.27 semantics; older ones must switch or fail.',
sourceURL='https://go.dev/doc/toolchain',
additionalReadings=[dict(title='go.mod reference: go directive', url=MOD+'#go-mod-file-go', section='go directive')]),

dict(key='dependencies-mvs', stage=STAGE, title='Requirements, go.sum, replace and minimal version selection',
body=[
'require lines name the minimum version of each dependency. When several modules require different versions, the go command uses minimal version selection: it picks the highest of the stated minimums, never a newer release nobody asked for. Builds are therefore reproducible without a lock file.',
'go.sum records cryptographic hashes of every module version used, checked against the public checksum database on first download. Commit go.sum with go.mod. go get example.com/lib@v1.4.0 changes a requirement, go mod tidy adds missing and removes unused requirements, and go list -m all prints the selected build list.',
'A replace directive substitutes a different source, such as a local directory, for a module version. It applies only when building this main module, which makes it right for local development and offline examples like this one, and wrong for libraries others depend on.',
'Go 1.27 makes go mod tidy merge duplicate require blocks for modules with go 1.27 or later.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/app\n\ngo 1.27\n\nrequire example.com/greet v1.2.0\n\nreplace example.com/greet v1.2.0 => ./greet\n'),
f('main.go', r'''package main

import (
    "fmt"

    "example.com/greet"
)

func main() {
    fmt.Println(greet.Hello("modules"))
}
'''),
f('greet/go.mod', 'module example.com/greet\n\ngo 1.27\n'),
f('greet/greet.go', r'''// Package greet is a local stand-in for a published module.
package greet

// Hello returns a greeting.
func Hello(name string) string { return "hello, " + name }
'''),
],
projectSolutionFiles=[f('greet/greet.go', r'''// Package greet is a local stand-in for a published module.
package greet

import "strings"

// Hello returns a greeting.
func Hello(name string) string { return "hello, " + name }

// Shout returns an upper-case greeting.
func Shout(name string) string { return strings.ToUpper(Hello(name)) + "!" }
''')],
projectInstructions='Go 1.27; works offline because example.com/greet is replaced by a local directory. From the app module root run:\ngo run .\ngo list -m all\nExpected: hello, modules, then a build list showing example.com/greet v1.2.0 => ./greet.\nPractice: add Shout to greet and call it from main. Replace greet/greet.go with the worked answer.',
projectChecks=[
dict(name='replaced dependency builds offline', args=['run', '.'], stdout='hello, modules\n'),
dict(name='build list shows replacement', args=['list', '-m', 'all'], stdout='example.com/app\nexample.com/greet v1.2.0 => ./greet\n'),
dict(name='answer adds Shout', args=['run', '.'], useSolution=True,
     mutations=[dict(path='main.go', find='greet.Hello("modules")', replace='greet.Shout("modules")')], stdout='HELLO, MODULES!\n'),
],
challenge='Add func Shout(name string) string to the greet module returning the upper-case greeting followed by "!", and print greet.Shout("modules").',
question='Which version does minimal version selection choose when A needs lib v1.2.0 and B needs lib v1.3.0?',
correct='v1.3.0, the highest of the stated minimums',
wrong=['The newest published version of lib', 'v1.2.0, the lowest requested'],
reasoning='Each requirement is a minimum. MVS selects the smallest version that satisfies all of them, which is the maximum of the minimums.',
sourceURL=MOD+'#minimal-version-selection',
additionalReadings=[dict(title='Managing dependencies', url='https://go.dev/doc/modules/managing-dependencies', section='go get and go mod tidy')]),

dict(key='workspaces', stage=STAGE, title='Multi-module workspaces with go.work',
body=[
'A workspace lets you edit several modules together without replace directives. go work init ./app ./lib writes a go.work file with use lines; inside the workspace, imports of example.com/lib resolve to the local directory.',
'go.work is a developer convenience and is usually not committed for libraries. GOWORK=off disables it, which is how CI checks that each module builds on its own. Commands such as go work sync push the workspace\'s selected versions back into each module\'s go.mod.',
'Workspaces suit a service and a library changing in the same pull request, or trying a fix to a dependency before it is released.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.work', 'go 1.27\n\nuse (\n\t./app\n\t./mathx\n)\n'),
f('app/go.mod', 'module example.com/app\n\ngo 1.27\n\nrequire example.com/mathx v0.0.0\n'),
f('app/main.go', r'''package main

import (
    "fmt"

    "example.com/mathx"
)

func main() {
    fmt.Println(mathx.Clamp(15, 0, 10))
}
'''),
f('mathx/go.mod', 'module example.com/mathx\n\ngo 1.27\n'),
f('mathx/mathx.go', r'''// Package mathx holds small numeric helpers.
package mathx

// Clamp limits v to the inclusive range [lo, hi].
func Clamp(v, lo, hi int) int { return max(lo, min(v, hi)) }
'''),
],
projectSolutionFiles=[f('mathx/mathx.go', r'''// Package mathx holds small numeric helpers.
package mathx

import "cmp"

// Clamp limits v to the inclusive range [lo, hi].
func Clamp[T cmp.Ordered](v, lo, hi T) T { return max(lo, min(v, hi)) }
''')],
projectEnvironment=dict(GOWORK=None), projectVet=['vet', './app/...', './mathx/...'],
projectInstructions='Go 1.27, offline. Create both modules and go.work, then from the workspace root run:\ngo run ./app\nExpected stdout: 10. With GOWORK=off the app cannot find example.com/mathx, which shows that only the workspace connects them.\nPractice: make Clamp generic over cmp.Ordered. Replace mathx/mathx.go with the worked answer.',
projectChecks=[
dict(name='workspace resolves local module', args=['run', './app'], stdout='10\n'),
dict(name='without workspace the module is missing', dir='app', args=['build', '-o', '/dev/null', '.'], environment=dict(GOWORK='off'), exit=1, outputContains=['example.com/mathx']),
dict(name='answer generic Clamp', args=['run', './app'], useSolution=True,
     mutations=[dict(path='app/main.go', find='mathx.Clamp(15, 0, 10)', replace='mathx.Clamp(2.5, 0.0, 1.0)')], stdout='1\n'),
],
challenge='Make mathx.Clamp generic over cmp.Ordered and call it with float64 arguments 2.5, 0.0, 1.0 from the app.',
question='What does GOWORK=off do?',
correct='Ignores go.work so each module builds from its own go.mod',
wrong=['Deletes the go.work file', 'Disables module mode entirely'],
reasoning='CI often sets GOWORK=off to make sure a module does not depend on unpublished local edits.',
sourceURL='https://go.dev/doc/tutorial/workspaces',
additionalReadings=[dict(title='Workspaces reference', url=MOD+'#workspaces', section='go.work files')]),

dict(key='internal-packages', stage=STAGE, title='internal packages and enforced boundaries',
body=[
'A package whose path contains an internal element can be imported only by code rooted at the parent of that internal directory. example.com/shop/internal/db can be used by example.com/shop/... but not by other modules or sibling trees. The go command enforces it.',
'Use internal for implementation packages you want to share across your own packages without making them public API. It is the main tool for keeping a module\'s exported surface small.',
'vendor directories are a different mechanism: go mod vendor copies dependencies into vendor/ so builds need no network. Since Go 1.14 the go command uses vendor automatically when vendor/modules.txt matches go.mod.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/shop\n\ngo 1.27\n'),
f('main.go', r'''package main

import (
    "fmt"

    "example.com/shop/billing"
)

func main() {
    fmt.Println(billing.Total([]int{250, 175}))
}
'''),
f('billing/billing.go', r'''// Package billing totals orders.
package billing

import "example.com/shop/billing/internal/tax"

// Total returns the sum of cents including tax.
func Total(items []int) int {
    sum := 0
    for _, c := range items {
        sum += c
    }
    return sum + tax.On(sum)
}
'''),
f('billing/internal/tax/tax.go', r'''// Package tax is private to billing.
package tax

// On returns 20% tax, rounded down, on cents.
func On(cents int) int { return cents / 5 }
'''),
f('report/report.go', r'''// Package report is outside billing.
package report

// Name labels reports.
const Name = "report"
'''),
],
projectSolutionFiles=[f('billing/internal/tax/tax.go', r'''// Package tax is private to billing.
package tax

// On returns 20% tax on cents, rounded to the nearest cent.
func On(cents int) int { return (cents + 2) / 5 }
''')],
projectInstructions='Go 1.27, standard library only. Create the files, then run:\ngo run .\nExpected stdout: 510 (425 cents plus 85 tax).\nThe second check edits report/report.go to import billing/internal/tax; the go command rejects it because report is outside billing.\nPractice: round tax to the nearest cent. Replace billing/internal/tax/tax.go with the worked answer.',
projectChecks=[
dict(name='allowed internal import', args=['run', '.'], stdout='510\n'),
dict(name='internal import from outside is rejected', args=['build', './...'], exit=1,
     mutations=[dict(path='report/report.go', find='package report\n', replace='package report\n\nimport _ "example.com/shop/billing/internal/tax"\n')],
     outputContains=['use of internal package example.com/shop/billing/internal/tax not allowed']),
dict(name='answer rounds tax', args=['run', '.'], useSolution=True,
     mutations=[dict(path='main.go', find='[]int{250, 175}', replace='[]int{13}')], stdout='16\n'),
],
challenge='Change tax.On to round to the nearest cent instead of down, so that Total([]int{13}) returns 16.',
question='Who may import example.com/shop/billing/internal/tax?',
correct='Only packages under example.com/shop/billing',
wrong=['Any package in the example.com/shop module', 'Any package, but only in tests'],
reasoning='The rule is rooted at the parent of the internal directory, here billing, not at the module root.',
sourceURL='https://go.dev/doc/go1.4#internalpackages',
additionalReadings=[dict(title='go command: internal directories', url='https://pkg.go.dev/cmd/go#hdr-Internal_Directories', section='Internal Directories')]),

dict(key='tool-directives', stage=STAGE, title='Tracking developer tools with tool directives',
body=[
'Go 1.24 added tool directives to go.mod. go get -tool example.com/gen adds a tool line plus the requirement; go tool gen then builds and runs that exact version. Tools such as code generators and linters become versioned dependencies like any other, replacing the old tools.go blank-import convention.',
'go tool lists available tools, and go install tool installs them into GOBIN. Because tools are module requirements, go.sum verifies them and minimal version selection applies to their dependencies too.',
'This lesson uses a local replace so the tool builds offline. In real projects the tool comes from a published module.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/app\n\ngo 1.27\n\ntool example.com/stamp\n\nrequire example.com/stamp v1.0.0\n\nreplace example.com/stamp v1.0.0 => ./stamp\n'),
f('main.go', r'''package main

import "fmt"

func main() { fmt.Println("app") }
'''),
f('stamp/go.mod', 'module example.com/stamp\n\ngo 1.27\n'),
f('stamp/main.go', r'''// Command stamp prints a build label for its arguments.
package main

import (
    "fmt"
    "os"
    "strings"
)

func main() {
    fmt.Println("stamp:", strings.Join(os.Args[1:], "+"))
}
'''),
],
projectSolutionFiles=[f('stamp/main.go', r'''// Command stamp prints a build label for its arguments.
package main

import (
    "fmt"
    "os"
    "strings"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "usage: stamp label...")
        os.Exit(2)
    }
    fmt.Println("stamp:", strings.Join(os.Args[1:], "+"))
}
''')],
projectInstructions='Go 1.24+ (checked with 1.27), offline via replace. From the app module root run:\ngo tool stamp v1 linux\nExpected stdout: stamp: v1+linux\nPractice: make stamp exit with status 2 and a usage message when given no arguments. Replace stamp/main.go with the worked answer.',
projectChecks=[
dict(name='go tool runs the versioned tool', args=['tool', 'stamp', 'v1', 'linux'], stdout='stamp: v1+linux\n'),
dict(name='go tool lists it', args=['tool'], stdoutContains=['example.com/stamp']),
dict(name='answer usage status', args=['tool', 'stamp'], useSolution=True, exit=2, stdout='', stderrContains='usage: stamp'),
],
challenge='Make the stamp tool exit with status 2 and print "usage: stamp label..." to stderr when run without arguments.',
question='What does a tool line in go.mod give you over installing a tool globally?',
correct='A tool version pinned and verified with the module\'s other requirements',
wrong=['Faster tool startup', 'Automatic execution during go build'],
reasoning='go tool runs the version selected by the module graph, so every developer and CI job uses the same tool.',
sourceURL='https://go.dev/doc/modules/managing-dependencies#tools',
additionalReadings=[dict(title='Go 1.24 release notes: tools', url='https://go.dev/doc/go1.24#tools', section='Tool dependencies')]),

dict(key='semver-major-versions', stage=STAGE, title='Semantic versions, major-version paths and retract',
body=[
'Module versions are semantic: vMAJOR.MINOR.PATCH. Within a major version, newer releases must stay compatible. A v2 or later release must change the module path, for example example.com/lib/v2, so v1 and v2 can be imported side by side and old code keeps compiling.',
'Pre-release versions such as v1.3.0-rc.1 sort before v1.3.0, and pseudo-versions like v0.0.0-20261016120000-abcdef123456 identify untagged commits. v0 makes no compatibility promise.',
'A retract directive in a later release marks bad versions: go get and go list -m -u avoid them and explain why, but existing builds that require them still work. Retraction is how a maintainer withdraws a broken or accidentally published tag.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/app\n\ngo 1.27\n\nrequire (\n\texample.com/units v1.4.0\n\texample.com/units/v2 v2.0.1\n)\n\nreplace example.com/units v1.4.0 => ./units1\n\nreplace example.com/units/v2 v2.0.1 => ./units2\n'),
f('main.go', r'''package main

import (
    "fmt"

    units "example.com/units"
    unitsv2 "example.com/units/v2"
)

func main() {
    fmt.Println(units.Km(1500))
    fmt.Println(unitsv2.Km(1500))
}
'''),
f('units1/go.mod', 'module example.com/units\n\ngo 1.27\n'),
f('units1/units.go', r'''// Package units is the v1 API: whole kilometres.
package units

// Km converts metres to whole kilometres.
func Km(m int) int { return m / 1000 }
'''),
f('units2/go.mod', 'module example.com/units/v2\n\ngo 1.27\n\nretract v2.0.0 // rounded incorrectly\n'),
f('units2/units.go', r'''// Package units is the v2 API: fractional kilometres.
package units

// Km converts metres to kilometres.
func Km(m int) float64 { return float64(m) / 1000 }
'''),
],
projectSolutionFiles=[f('units2/units.go', r'''// Package units is the v2 API: fractional kilometres.
package units

import "fmt"

// Km converts metres to kilometres.
func Km(m int) float64 { return float64(m) / 1000 }

// Format renders metres as kilometres with one decimal.
func Format(m int) string { return fmt.Sprintf("%.1f km", Km(m)) }
''')],
projectInstructions='Go 1.27, offline via replace. Two major versions of the same module are used side by side. Run:\ngo run .\nExpected stdout: 1 then 1.5.\nPractice: add Format to v2 only and print unitsv2.Format(1500). Replace units2/units.go with the worked answer.',
projectChecks=[
dict(name='v1 and v2 coexist', args=['run', '.'], stdout='1\n1.5\n'),
dict(name='both majors in the build list', args=['list', '-m', 'all'], stdoutContains=['example.com/units v1.4.0 => ./units1', 'example.com/units/v2 v2.0.1 => ./units2']),
dict(name='answer Format in v2', args=['run', '.'], useSolution=True,
     mutations=[dict(path='main.go', find='fmt.Println(unitsv2.Km(1500))', replace='fmt.Println(unitsv2.Format(1500))')], stdout='1\n1.5 km\n'),
],
challenge='Add Format(m int) string to the v2 module only, returning one decimal followed by " km", and print unitsv2.Format(1500).',
question='Why does a v2 module need a /v2 suffix in its path?',
correct='So incompatible major versions are distinct import paths that can coexist',
wrong=['The proxy rejects tags above v1 otherwise', 'It enables generics in the module'],
reasoning='Semantic import versioning: an incompatible API gets a new import path, so existing importers of v1 are never broken by v2.',
sourceURL=MOD+'#major-version-suffixes',
additionalReadings=[dict(title='retract directive', url=MOD+'#go-mod-file-retract', section='retract')]),

dict(key='build-constraints', stage=STAGE, title='Build constraints, GOOS/GOARCH and file suffixes',
body=[
'A //go:build line at the top of a file decides whether the file is part of the build: //go:build linux && amd64, //go:build !windows, or a custom tag such as //go:build pro enabled with go build -tags pro. It must appear before the package clause, followed by a blank line.',
'File name suffixes are implicit constraints: net_linux.go builds only for GOOS=linux and asm_arm64.s only for GOARCH=arm64. _test.go files build only for go test.',
'Set GOOS and GOARCH to cross-compile: GOOS=linux GOARCH=arm64 go build produces a Linux binary on macOS with no extra toolchain, as long as cgo is not needed. go vet and go list with those variables check the other platform\'s files too.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/plat\n\ngo 1.27\n'),
f('main.go', r'''package main

import "fmt"

func main() {
    fmt.Println(platform(), edition)
}
'''),
f('plat_darwin.go', r'''package main

func platform() string { return "macOS" }
'''),
f('plat_linux.go', r'''package main

func platform() string { return "Linux" }
'''),
f('plat_other.go', r'''//go:build !darwin && !linux

package main

func platform() string { return "other" }
'''),
f('edition_free.go', r'''//go:build !pro

package main

const edition = "free"
'''),
f('edition_pro.go', r'''//go:build pro

package main

const edition = "pro"
'''),
],
projectSolutionFiles=[f('plat_windows.go', r'''package main

func platform() string { return "Windows" }
'''), f('plat_other.go', r'''//go:build !darwin && !linux && !windows

package main

func platform() string { return "other" }
''')],
projectInstructions='Go 1.27, checked on macOS arm64. Create the files, then run:\ngo run .\ngo run -tags pro .\nGOOS=linux go list -f "{{.GoFiles}}" .\nExpected: macOS free, macOS pro, then the Linux file list.\nPractice: add plat_windows.go and exclude Windows from plat_other.go so GOOS=windows builds the new file.',
projectChecks=[
dict(name='host build', args=['run', '.'], stdout='macOS free\n'),
dict(name='custom tag', args=['run', '-tags', 'pro', '.'], stdout='macOS pro\n'),
dict(name='linux file selection', args=['list', '-f', '{{.GoFiles}}', '.'], environment=dict(GOOS='linux'), stdout='[edition_free.go main.go plat_linux.go]\n'),
dict(name='windows falls back to other', args=['list', '-f', '{{.GoFiles}}', '.'], environment=dict(GOOS='windows'), stdout='[edition_free.go main.go plat_other.go]\n'),
dict(name='answer windows file', args=['list', '-f', '{{.GoFiles}}', '.'], environment=dict(GOOS='windows'), useSolution=True, stdout='[edition_free.go main.go plat_windows.go]\n'),
dict(name='answer cross-compiles for windows', args=['build', '-o', '/dev/null', '.'], environment=dict(GOOS='windows', GOARCH='amd64', CGO_ENABLED='0'), useSolution=True),
],
challenge='Add plat_windows.go returning "Windows" and adjust plat_other.go so GOOS=windows selects the new file.',
question='Which files does GOOS=linux go build include from plat_linux.go, plat_darwin.go and plat_other.go (//go:build !darwin && !linux)?',
correct='Only plat_linux.go',
wrong=['plat_linux.go and plat_other.go', 'All three; constraints only apply to go vet'],
reasoning='The _linux suffix selects plat_linux.go, the _darwin suffix excludes plat_darwin.go, and the expression excludes plat_other.go on Linux.',
sourceURL='https://pkg.go.dev/cmd/go#hdr-Build_constraints',
additionalReadings=[dict(title='go/build constraints', url='https://pkg.go.dev/go/build#hdr-Build_Constraints', section='Build constraints')]),
]

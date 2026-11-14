STAGE = '27 · The go command, completely'
CMD = 'https://pkg.go.dev/cmd/go'


def f(path, content):
    return dict(path=path, content=content)


GREET = r'''// Package greet is a local stand-in for a published module.
package greet

// Hello returns a greeting.
func Hello(name string) string { return "hello, " + name }
'''

APP_MAIN = r'''package main

import (
    "fmt"

    "example.com/greet"
)

func main() { fmt.Println(greet.Hello("go mod")) }
'''

LESSONS = [
dict(key='go-mod-commands', stage=STAGE, title='go mod and go get: init, edit, tidy, graph, why, verify, vendor',
body=[
'go mod init path creates go.mod. go mod edit changes it from scripts without hand-editing: -require=mod@v, -droprequire, -replace=old=new, -go=1.27, and -json to print it as JSON. go mod tidy adds missing requirements and removes unused ones, keeping go.mod and go.sum in step with the imports.',
'go mod graph prints every requirement edge; go mod why pkg explains why a package is in the build by showing an import chain from the main module; go mod verify checks that downloaded modules in the cache still match their go.sum hashes; go mod download fetches modules ahead of time; go mod vendor copies dependencies into vendor/ for builds without network access.',
'go get changes requirements: go get mod@v1.4.0 upgrades or downgrades, go get mod@latest moves to the newest release, and go get mod@none removes the requirement along with anything that needs it. Since Go 1.17 go get only edits requirements; go install builds and installs commands.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/app\n\ngo 1.27\n'),
f('main.go', APP_MAIN),
f('greet/go.mod', 'module example.com/greet\n\ngo 1.27\n'),
f('greet/greet.go', GREET),
f('fresh/main.go', 'package main\n\nfunc main() {}\n'),
],
projectSolutionFiles=[f('go.mod', 'module example.com/app\n\ngo 1.27\n\nrequire example.com/greet v1.2.0\n\nreplace example.com/greet v1.2.0 => ./greet\n')],
projectVet=[],  # the starting go.mod deliberately lacks the requirement; the checks add it
projectInstructions='Go 1.27, offline. The app imports example.com/greet but go.mod does not require it yet. From the module root run, in order:\ngo build ./...   (fails: no required module provides the package)\ngo mod edit -require=example.com/greet@v1.2.0 -replace=example.com/greet@v1.2.0=./greet\ngo mod tidy\ngo run .\ngo mod graph\ngo mod why example.com/greet\ngo mod verify\ngo mod vendor\ngo mod edit -json\ncd fresh && go mod init example.com/fresh\ngo get example.com/greet@none   (removes the requirement again; vendor/ is now inconsistent, so go list needs -mod=mod or a fresh go mod vendor)\nPractice: write the finished go.mod by hand; it should match the worked answer.',
projectChecks=[
dict(name='missing requirement', args=['build', './...'], exit=1, outputContains=['no required module provides package example.com/greet']),
dict(name='go mod edit adds require and replace', args=['mod', 'edit', '-require=example.com/greet@v1.2.0', '-replace=example.com/greet@v1.2.0=./greet']),
dict(name='go mod tidy', args=['mod', 'tidy']),
dict(name='builds after tidy', args=['run', '.'], stdout='hello, go mod\n'),
dict(name='go mod graph', args=['mod', 'graph'], stdout='example.com/app example.com/greet@v1.2.0\nexample.com/app go@1.27\nexample.com/greet@v1.2.0 go@1.27\ngo@1.27 toolchain@go1.27\n'),
dict(name='go mod why', args=['mod', 'why', 'example.com/greet'], stdout='# example.com/greet\nexample.com/app\nexample.com/greet\n'),
dict(name='go mod verify', args=['mod', 'verify'], stdout='all modules verified\n'),
dict(name='go mod vendor', args=['mod', 'vendor']),
dict(name='builds from vendor', args=['run', '-mod=vendor', '.'], stdout='hello, go mod\n'),
dict(name='go mod edit -json', args=['mod', 'edit', '-json'], outputContains=['"Path": "example.com/greet"', '"Version": "v1.2.0"']),
dict(name='go mod init in a new directory', dir='fresh', args=['mod', 'init', 'example.com/fresh'], outputContains=['creating new go.mod: module example.com/fresh']),
dict(name='go get @none removes the requirement', args=['get', 'example.com/greet@none'], outputContains=['removed example.com/greet v1.2.0']),
dict(name='build list no longer contains greet', args=['list', '-mod=mod', '-m', 'all'], stdout='example.com/app\n'),
dict(name='answer go.mod builds', args=['run', '.'], useSolution=True, stdout='hello, go mod\n'),
],
challenge='Write the finished go.mod by hand: require example.com/greet v1.2.0 and replace it with ./greet.',
question='What does go get example.com/greet@none do?',
correct='Removes the requirement, and downgrades or removes anything that depends on it',
wrong=['Deletes the module from the module cache', 'Installs the latest version'],
reasoning='@none is the version query for "not required". go get edits requirements; the cache is managed with go clean -modcache.',
sourceURL='https://go.dev/ref/mod#go-mod-file',
additionalReadings=[dict(title='go mod commands', url='https://go.dev/ref/mod#mod-commands', section='go mod'), dict(title='go get', url='https://go.dev/ref/mod#go-get', section='go get')],
minutes=40),

dict(key='go-work-commands', stage=STAGE, title='go work: init, use, edit and sync',
body=[
'go work init ./a ./b creates go.work listing modules; go work use ./c adds one (and -r adds every module below a directory); go work edit changes go.work from scripts, like go mod edit for go.mod; go work sync copies the versions selected for the whole workspace back into each module\'s go.mod. Imports of a module that is itself in the workspace resolve without any require line.',
'go work vendor vendors the dependencies of all workspace modules together. go env GOWORK shows which go.work is in effect, and GOWORK=off ignores it.',
'Workspaces are for local development across modules. Before releasing, make sure each module builds alone with GOWORK=off and real requirements.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('app/go.mod', 'module example.com/app\n\ngo 1.27\n'),
f('app/main.go', APP_MAIN),
f('greet/go.mod', 'module example.com/greet\n\ngo 1.27\n'),
f('greet/greet.go', GREET),
],
projectSolutionFiles=[f('go.work', 'go 1.27\n\nuse (\n\t./app\n\t./greet\n)\n')],
projectEnvironment=dict(GOWORK=None),
projectVet=[],  # there is no workspace until the checks create it
projectInstructions='Go 1.27, offline. From the directory containing app/ and greet/ run:\ngo work init ./app\ngo work use ./greet\ngo run ./app\ngo work edit -json\ngo env GOWORK\ngo work sync\nPractice: write the resulting go.work file by hand; it should match the worked answer.',
projectChecks=[
dict(name='go work init', args=['work', 'init', './app']),
dict(name='not yet resolvable', args=['build', './app'], exit=1, outputContains=['example.com/greet']),
dict(name='go work use', args=['work', 'use', './greet']),
dict(name='workspace builds', args=['run', './app'], stdout='hello, go mod\n'),
dict(name='go work edit -json', args=['work', 'edit', '-json'], outputContains=['"DiskPath": "./app"', '"DiskPath": "./greet"']),
dict(name='go env GOWORK', args=['env', 'GOWORK'], outputContains=['go.work']),
dict(name='go work sync', args=['work', 'sync']),
dict(name='answer go.work builds', args=['run', './app'], useSolution=True, stdout='hello, go mod\n'),
],
challenge='Write the go.work file that go work init ./app and go work use ./greet produce.',
question='What does go work sync do?',
correct='Pushes the workspace\'s selected dependency versions back into each module\'s go.mod',
wrong=['Downloads every module in the workspace', 'Deletes go.work after merging it'],
reasoning='Modules in a workspace share one build list. sync records it in each module so they build consistently on their own.',
sourceURL='https://go.dev/ref/mod#workspaces',
minutes=30),

dict(key='go-env-install-clean', stage=STAGE, title='go env, go install and go clean',
body=[
'go env prints the go command\'s configuration: GOROOT, GOPATH, GOMODCACHE, GOCACHE, GOOS, GOARCH, GOFLAGS, GOPROXY, GOTOOLCHAIN and many more; go env -json prints them all as JSON. go env -w KEY=value saves a default in the file named by GOENV (normally in the user configuration directory) and go env -u removes it. Environment variables always win over saved values.',
'go install pkg@version builds a command and puts the binary in GOBIN (default $GOPATH/bin) without touching the current module, which is how developer tools are installed globally. Inside a module, go install ./cmd/x installs that module\'s command.',
'go clean removes build products: plain go clean deletes binaries built in the package directory; -testcache expires cached test results; -cache, -modcache and -fuzzcache delete whole caches. This lesson points GOENV and GOBIN into the project, so the checks never change your real settings.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/tools\n\ngo 1.27\n'),
f('cmd/hello/main.go', r'''// Command hello is installed with go install.
package main

import "fmt"

func main() { fmt.Println("installed hello") }
'''),
],
projectSolutionFiles=[f('cmd/bye/main.go', r'''// Command bye is a second installable command.
package main

import "fmt"

func main() { fmt.Println("installed bye") }
''')],
projectInstructions='Go 1.27. These commands run with GOENV and GOBIN set inside the project, so your real configuration is untouched:\ngo env GOOS GOARCH\ngo env -json GOVERSION\nGOENV=$PWD/goenv go env -w GOFLAGS=-count=1 and go env GOFLAGS\nGOBIN=$PWD/bin go install ./cmd/hello\ngo build ./cmd/hello && go clean ./cmd/hello\nPractice: add a second command, cmd/bye, and install both with go install ./cmd/....',
projectChecks=[
dict(name='go env values', args=['env', 'GOOS', 'GOARCH'], stdout='darwin\narm64\n'),
dict(name='go env -json', args=['env', '-json', 'GOVERSION'], outputContains=['"GOVERSION": "go1.27.2"']),
dict(name='go env -w writes the GOENV file', args=['env', '-w', 'GOFLAGS=-count=1'], environment=dict(GOENV='{dir}/goenv', GOFLAGS=None)),
dict(name='saved value is read back', args=['env', 'GOFLAGS'], environment=dict(GOENV='{dir}/goenv', GOFLAGS=None), stdout='-count=1\n'),
dict(name='go env -u removes it', args=['env', '-u', 'GOFLAGS'], environment=dict(GOENV='{dir}/goenv', GOFLAGS=None)),
dict(name='removed value is gone', args=['env', 'GOFLAGS'], environment=dict(GOENV='{dir}/goenv', GOFLAGS=None), stdout='\n'),
dict(name='go install to a project GOBIN', args=['install', './cmd/hello'], environment=dict(GOBIN='{dir}/bin')),
dict(name='go build leaves a binary', args=['build', '-o', 'cmd/hello/hello', './cmd/hello']),
dict(name='go clean -n shows what it would remove', args=['clean', '-n', './cmd/hello'], outputContains=['rm -f']),
dict(name='go clean -testcache', args=['clean', '-testcache']),
dict(name='answer installs every command', args=['install', './cmd/...'], environment=dict(GOBIN='{dir}/bin'), useSolution=True),
dict(name='answer lists both commands', args=['list', './cmd/...'], useSolution=True, stdout='example.com/tools/cmd/bye\nexample.com/tools/cmd/hello\n'),
],
challenge='Add cmd/bye and install both commands with a single go install ./cmd/... into the project\'s bin directory.',
question='Which wins when GOFLAGS is set both by go env -w and in the environment?',
correct='The environment variable',
wrong=['The value saved with go env -w', 'Whichever was set most recently'],
reasoning='go env -w only provides defaults in the GOENV file. A variable set in the process environment overrides it.',
sourceURL=CMD+'#hdr-Print_Go_environment_information',
additionalReadings=[dict(title='go install', url=CMD+'#hdr-Compile_and_install_packages_and_dependencies', section='go install'), dict(title='go clean', url=CMD+'#hdr-Remove_object_files_and_cached_files', section='go clean')]),

dict(key='go-fmt-doc', stage=STAGE, title='go fmt and go doc on your own packages',
body=[
'go fmt runs gofmt -l -w on the named packages and prints the files it changed, so its output doubles as a check: an empty output means everything was already formatted. gofmt -d prints a diff instead of rewriting, and gofmt -s simplifies code such as []T{T{1}} to []T{{1}}.',
'go doc shows documentation for the current module\'s packages as well as the standard library: go doc . lists a package, go doc Type.Method shows one method, -all shows everything, -src shows source and -u includes unexported names. Since Go 1.27 go doc -ex runs examples and go doc pkg@version reads a specific module version.',
'Run both in CI: go fmt (or gofmt -l) to keep diffs clean, and go doc to check that exported names have doc comments that read well.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/shapes\n\ngo 1.27\n'),
f('shapes.go', r'''// Package shapes computes areas.
package shapes

// Rect is a rectangle.
type Rect struct{ W, H float64 }

// Area returns the rectangle's area.
func (r Rect) Area() float64 { return r.W * r.H }

func helper() int { return 1 }
'''),
],
projectSolutionFiles=[f('shapes.go', r'''// Package shapes computes areas.
package shapes

// Rect is a rectangle.
type Rect struct{ W, H float64 }

// Area returns the rectangle's area.
func (r Rect) Area() float64 { return r.W * r.H }

// Perimeter returns the rectangle's perimeter.
func (r Rect) Perimeter() float64 { return 2 * (r.W + r.H) }

func helper() int { return 1 }
''')],
projectInstructions='Go 1.27. Run:\ngo fmt ./...   (prints nothing: already formatted)\ngo doc .\ngo doc Rect.Area\ngo doc -u . (includes helper)\nA check mis-indents shapes.go to show go fmt rewriting and naming the file.\nPractice: add a documented Perimeter method and confirm go doc Rect lists it.',
projectChecks=[
dict(name='go fmt on formatted code prints nothing', args=['fmt', './...'], stdout=''),
dict(name='go fmt names the file it fixes', args=['fmt', './...'], mutations=[dict(path='shapes.go', find='func helper() int { return 1 }\n', replace='func helper()  int   { return 1 }\n')], stdout='shapes.go\n'),
dict(name='go doc package', args=['doc', '.'], outputContains=['package shapes // import "example.com/shapes"', 'Package shapes computes areas.', 'type Rect struct']),
dict(name='go doc method', args=['doc', 'Rect.Area'], outputContains=["Area returns the rectangle's area."]),
dict(name='go doc -u shows unexported names', args=['doc', '-u', '.'], outputContains=['func helper() int']),
dict(name='answer method appears in go doc', args=['doc', 'Rect'], useSolution=True, outputContains=['func (r Rect) Perimeter() float64']),
],
challenge='Add a documented Perimeter method to Rect and confirm that go doc Rect lists it.',
question='What does an empty output from go fmt ./... mean?',
correct='No file needed changes; the code was already gofmt-formatted',
wrong=['go fmt failed to find any packages', 'Formatting is disabled for the module'],
reasoning='go fmt prints the names of files it rewrote, so silence is the success case CI can check.',
sourceURL=CMD+'#hdr-Gofmt__reformat__package_sources',
additionalReadings=[dict(title='go doc', url=CMD+'#hdr-Show_documentation_for_package_or_symbol', section='go doc')]),

dict(key='go-telemetry-bug-help', stage=STAGE, title='go telemetry, go bug and go help',
body=[
'go telemetry reports the telemetry mode: off (nothing collected), local (the default: counters kept on your machine only) or on (counters periodically uploaded, after which they appear in a public dataset at telemetry.go.dev). go telemetry off, local or on changes the mode for your user account, so the checks here only read it.',
'go bug opens a pre-filled GitHub issue in your browser with go version and go env output, for reporting toolchain bugs. It is taught but never run by the validator, because it opens a browser on your behalf.',
'go help lists every subcommand, and go help topic explains concepts such as go help modules, go help packages, go help testflag, go help buildconstraint and go help environment. With the 19 subcommands covered in this guide (bug, build, clean, doc, env, fix, fmt, generate, get, install, list, mod, run, telemetry, test, tool, version, vet, work) you have used the whole go command.',
],
code='', expectedStdout='', solution='', solutionStdout='',
project=[
f('go.mod', 'module example.com/help\n\ngo 1.27\n'),
f('main.go', 'package main\n\nfunc main() {}\n'),
],
projectSolutionFiles=[f('main.go', 'package main\n\nimport "fmt"\n\nfunc main() { fmt.Println("help read") }\n')],
projectInstructions='Go 1.27. Run the read-only commands:\ngo telemetry\ngo help bug\ngo help testflag\ngo help\nDo not run go telemetry on/off/local unless you mean to change your settings, and go bug only to file a real issue.\nPractice: run go help environment and find which variable selects the toolchain (GOTOOLCHAIN).',
projectChecks=[
dict(name='go telemetry reads the mode', args=['telemetry']),
dict(name='go help bug explains go bug', args=['help', 'bug'], outputContains=['usage: go bug']),
dict(name='go help lists every subcommand', args=['help'], outputContains=['bug', 'clean', 'telemetry', 'work']),
dict(name='go help testflag', args=['help', 'testflag'], outputContains=['-race', '-count n']),
dict(name='answer go help environment documents GOTOOLCHAIN', args=['help', 'environment'], useSolution=True, outputContains=['GOTOOLCHAIN']),
],
challenge='Find, using go help environment, which environment variable selects the Go toolchain to run.',
question='Why does the validator never run go bug?',
correct='It opens a browser to file an issue on the user\'s behalf',
wrong=['go bug needs administrator rights', 'go bug was removed in Go 1.27'],
reasoning='Automated checks must not take outward-facing actions. The command is documented with go help bug instead.',
sourceURL='https://go.dev/doc/telemetry',
additionalReadings=[dict(title='go bug', url=CMD+'#hdr-Start_a_bug_report', section='go bug')]),
]

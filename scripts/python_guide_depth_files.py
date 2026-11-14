"""Original file, CLI and exception exercises with observable cleanup and boundary policies."""
from python_guide_depth import add, task

add('exception-specific', 'Tutorial 8.3: handling exceptions / narrow protected operations',
    'https://docs.python.org/3.13/tutorial/errors.html#handling-exceptions', [
    "An exception handler should describe a failure the function knows how to interpret. A parser may translate malformed integer text into a missing result, but that does not mean it should hide every TypeError, missing variable or unrelated bug from a larger block.",
    "Keep the try body small. The code inside else runs only after the try body succeeds and is not protected by the preceding handlers. This can prevent a later calculation's failure from being mistaken for an input-parsing failure.",
    "The transfer task separates the parser's policy from a caller observing a wrong-type error. Valid zero must remain successful, invalid text becomes None, and None supplied as the wrong input type propagates TypeError to the outer observer. A broad first handler would erase that distinction."
    ],
    ("Why keep an input parser's try block limited to the operation expected to fail?",
     "It prevents later unrelated failures from being misclassified as ordinary invalid input.",
     ["A larger try block makes all programming errors safe.", "except ValueError catches every exception category.", "Handlers can determine a failure's meaning without an input contract."],
     "A handler's semantic claim applies to the operations it protects. Narrow scope keeps that claim meaningful."),
    task("Transfer: let wrong-type failures escape a parser",
         "Define parse_integer(text) to return int(text), or None only for ValueError. The outer caller returns ['value', parsed_result], or ['type-error'] if TypeError propagated. data is integer text or None.",
         "def parse_integer(text):\n    try:\n        return int(text)\n    except ValueError:\n        return None\ntry:\n    result = ['value', parse_integer(data)]\nexcept TypeError:\n    result = ['type-error']",
         [('0',['value',0]),('oops',['value',None]),(None,['type-error']),(' -2 ',['value',-2])],
         ("except ValueError:","except Exception:"),
         ["The inner parser handles only invalid text values.", "The outer observer distinguishes a propagated wrong-type error.", "Do not turn a valid zero into a missing result."],
         "Valid '0' returns zero. Malformed text returns None through the declared parser policy. None is an unsupported argument type and reaches the separate outer TypeError path.",
         [['value',None],['type-error'],['value','0']]),
    ("What does a broad parser handler risk hiding?", "Wrong-type inputs and unrelated programming failures that should remain distinguishable from malformed text."))

add('exception-chaining', 'Tutorial 8.5: exception chaining / explicit causes',
    'https://docs.python.org/3.13/tutorial/errors.html#exception-chaining', [
    "An API can translate a low-level failure into a stable domain-facing error while retaining the original cause. raise NewError(...) from error sets an explicit cause that callers and tracebacks can inspect.",
    "from None suppresses display of the implicit context; it does not mean the original failure never happened. Use suppression only as a deliberate presentation decision. Replacing an explicit cause with suppression can remove information that an API or debugging workflow expects.",
    "Test a successful path as well as the translated failure. For a failure, inspect the outer error type, the explicit cause type and the stable message separately. Matching a message alone can miss lost causal structure."
    ],
    ("What evidence detects a lost explicit exception cause even when the outer message is unchanged?",
     "Inspect the outer exception's __cause__ and its type.",
     ["Only compare the outer message text.", "Assume from None preserves an explicit cause.", "Treat any raised error as the same failure."],
     "The explicit cause is structured error information. A stable message can survive a regression that removes it."),
    task("Transfer: a stable parse error with a cause",
         "data is a string. Parse with int. On success return ['ok', value]. On ValueError, raise RuntimeError('count is not integer') from the original error, then observe [outer_type_name, cause_type_name, message].",
         "try:\n    try:\n        value = int(data)\n    except ValueError as error:\n        raise RuntimeError('count is not integer') from error\n    result = ['ok', value]\nexcept RuntimeError as error:\n    result = [type(error).__name__, type(error.__cause__).__name__, str(error)]",
         [('x',['RuntimeError','ValueError','count is not integer']),('0',['ok',0]),('bad',['RuntimeError','ValueError','count is not integer']),('3',['ok',3])],
         ("from error","from None"),
         ["Translate only the expected parsing failure.", "Use from error to preserve the explicit causal relationship.", "Observe the cause's type independently of the outer message."],
         "The outer RuntimeError provides a stable domain message while its cause retains ValueError. Suppression leaves the outer message intact but changes the explicit cause to None.",
         [['RuntimeError','NoneType','count is not integer'],['ValueError','RuntimeError','count is not integer'],['ok',None]]),
    ("What does explicit exception chaining preserve?", "A stable outer error and a structured reference to the original cause, allowing diagnostics without coupling callers to a low-level message."))

add('finally-cleanup', 'Tutorial 8.7: cleanup actions / avoiding return in finally',
    'https://docs.python.org/3.13/tutorial/errors.html#defining-clean-up-actions', [
    "finally runs as control leaves a try statement, whether by normal completion, return or an exception. It is a place to release owned resources and record unconditional cleanup. It does not imply that the protected operation succeeded.",
    "A return from finally can replace an earlier return or suppress an exception. Cleanup code that reports success or supplies a new return value therefore risks disguising the original outcome. Keep teardown separate from the operation's result whenever possible.",
    "Observe both the operation's status and its cleanup events. A test that only sees a finalizer event can miss a swallowed failure; a test that only sees a result can miss skipped teardown. The transfer fixture checks the success and exceptional paths together."
    ],
    ("Why can return inside finally be dangerous?",
     "It can override a pending result or suppress an exception from the protected work.",
     ["finally never runs after a return.", "It guarantees that the original operation succeeded.", "It only changes formatting of the traceback."],
     "The finally block participates in control flow. Returning from it can replace the pending exit instead of merely performing cleanup."),
    task("Transfer: retain failure while cleaning up",
         "data is Boolean. A function records 'work', raises ValueError when data is True and otherwise returns 'ok'. Its finally records 'close' without replacing the result/error. Return [observed_status, events], with status 'error' when the caller catches ValueError.",
         "events = []\ndef work(fail):\n    try:\n        events.append('work')\n        if fail:\n            raise ValueError('bad')\n        return 'ok'\n    finally:\n        events.append('close')\ntry:\n    status = work(data)\nexcept ValueError:\n    status = 'error'\nresult = [status, events]",
         [(True,['error',['work','close']]),(False,['ok',['work','close']])],
         ("events.append('close')","return 'masked'"),
         ["Use finally only for the unconditional event.", "Catch the operation's ValueError in the caller.", "Check that cleanup does not turn the failure into a successful returned status."],
         "Both paths record close. The failure still reaches the caller and becomes error; the successful result stays ok. A return in finally would replace both outcomes and remove the cleanup event.",
         [['ok',['work','close']],['error',['work']],['masked',['work']]]),
    ("What should a cleanup regression inspect together?", "The operation's original success/failure and the teardown events. Either observation alone can hide a control-flow or resource bug."))

add('contextmanager', 'contextlib.ExitStack: partial acquisition and reverse cleanup',
    'https://docs.python.org/3.13/library/contextlib.html#contextlib.ExitStack', [
    "A context manager defines an acquisition/exit boundary. A generator-based contextmanager should put release logic in finally so exceptions thrown into the generator at its yield still trigger teardown.",
    "ExitStack can own a variable number of acquired contexts. Each successful entry is registered immediately, and exit unwinds them in reverse order. If acquiring a later resource fails, earlier successfully acquired resources are still released.",
    "Do not assume that a cleanup event proves every surrounding operation completed. The fixture distinguishes normal completion, an error before the second acquisition and an error inside both scopes. Its explicit event order checks partial ownership and reverse teardown without using sleeps."
    ],
    ("What should happen when an error occurs after the first resource is registered but before the second is entered?",
     "The first resource must be released; the second was never acquired and has no cleanup event.",
     ["Neither resource needs cleanup.", "Both resources must claim successful acquisition.", "Cleanup should wait for garbage collection."],
     "Ownership begins after successful acquisition. ExitStack remembers the already-entered contexts and unwinds only those registrations."),
    task("Transfer: partial acquisition cleanup",
         "data is 'ok', 'body-error' or 'acquire-error'. Enter outer, then inner unless acquire-error occurs first. Each resource records open/close events. Catch ValueError after the stack exits and append 'handled'. Return all events in order.",
         "events = []\n@contextmanager\ndef owned(name):\n    events.append('open:' + name)\n    try:\n        yield\n    finally:\n        events.append('close:' + name)\ntry:\n    with ExitStack() as stack:\n        stack.enter_context(owned('outer'))\n        if data == 'acquire-error':\n            raise ValueError('before inner')\n        stack.enter_context(owned('inner'))\n        if data == 'body-error':\n            raise ValueError('inside')\nexcept ValueError:\n    events.append('handled')\nresult = events",
         [('ok',['open:outer','open:inner','close:inner','close:outer']),('body-error',['open:outer','open:inner','close:inner','close:outer','handled']),('acquire-error',['open:outer','close:outer','handled'])],
         ("events.append('close:' + name)","pass"),
         ["Register each successful acquisition before attempting the next.", "Place each resource's teardown in finally around yield.", "The handled event belongs after the stack has released owned resources."],
         "Normal and body-error paths close inner before outer. The earlier acquisition error closes only outer, then records handled. The event order makes both the ownership boundary and the exceptional outcome observable.",
         [['open:outer','open:inner','close:outer','close:inner'],['open:outer','open:inner'],['handled']],
         "from contextlib import ExitStack, contextmanager"),
    ("What does ExitStack add to resource ownership?", "It registers successfully acquired contexts and unwinds them in reverse order, including when a later acquisition or the body fails."))

add('path-components', 'pathlib.PurePath: names, suffixes and lexical path handling',
    'https://docs.python.org/3.13/library/pathlib.html#pathlib.PurePath.name', [
    "A path has structured components. Its name is the final component, suffix is its final extension and stem is the name without that final suffix. A multi-extension filename such as archive.tar.gz therefore has suffix .gz and stem archive.tar.",
    "PurePosixPath performs lexical POSIX path operations without opening a file or asking the filesystem whether a target exists. It is useful when that syntax is part of the input contract, including on a host with other path conventions.",
    "Lexical inspection is not a security containment check. Parent components, symlinks, filesystem permissions and actual resolved locations require their own policies. The transfer task reports components only and does not claim that a filename is safe to open in a protected directory."
    ],
    ("What does inspecting PurePosixPath components establish?",
     "The lexical structure under POSIX path rules, without proving existence or safe filesystem containment.",
     ["That the target exists.", "That symlinks cannot escape a directory.", "That every path uses the current host's native syntax."],
     "Pure paths describe syntax. Filesystem access and security properties need additional evidence."),
    task("Transfer: lexical filename metadata",
         "data is a POSIX-style path string. Return [name, final_suffix, stem, parent_as_text] using PurePosixPath. Do not touch the filesystem.",
         "path = PurePosixPath(data)\nresult = [path.name, path.suffix, path.stem, str(path.parent)]",
         [('logs/run.csv',['run.csv','.csv','run','logs']),('archive.tar.gz',['archive.tar.gz','.gz','archive.tar','.']),('.env',['.env','','.env','.']),('', ['','','','.'])],
         ("path.suffix,","path.suffixes,"),
         ["Use the path object's components rather than manual splitting.", "The suffix field is one final suffix, not a list of all suffixes.", "A leading-dot filename can have no suffix."],
         "run.csv has the expected CSV suffix. archive.tar.gz keeps .tar in its stem because only the final suffix is removed. The hidden filename and empty lexical path expose naive split assumptions.",
         [['run.csv',['.csv'],'run','logs'],['run.csv','.csv','run.csv','logs'],['logs','.csv','run','run.csv']], "from pathlib import PurePosixPath"),
    ("Does parsing a path prove it is safe to open?", "No. Lexical components do not establish resolved containment, existence, permissions or symlink behavior."))

add('text-file', 'Tutorial 7.2: text file encoding / context closure and temporary cleanup',
    'https://docs.python.org/3.13/tutorial/inputoutput.html#reading-and-writing-files', [
    "Opening a file in text mode introduces an encoding boundary between strings and stored bytes. Specify UTF-8 when it is the file contract instead of depending on a machine's locale. A context manager closes the stream when the write scope exits, including on exceptions.",
    "Closing the stream and deleting a temporary workspace are separate ownership steps. The inner with closes the file; the TemporaryDirectory context removes the directory later. Test cleanup after leaving the outer scope, not while it still legitimately owns the files.",
    "Non-ASCII and empty fixtures matter. ASCII-only text can accidentally pass with several incompatible encodings. Byte count and code-point count need not agree. This bounded temporary-file exercise makes the chosen encoding and the final cleanup status visible without retaining personal data."
    ],
    ("Why must a temporary-directory removal check occur after its with block?",
     "The directory is expected to exist while the context owns it; cleanup happens when that scope exits.",
     ["A file can only be closed by deleting its directory.", "All with blocks defer cleanup until process exit.", "ASCII text proves that UTF-8 was used."],
     "A resource's legitimate lifetime and teardown boundary are distinct. Check the postcondition after ownership ends."),
    task("Transfer: UTF-8 file and teardown receipt",
         "data is a string. In a unique temporary directory, write and read it with explicit UTF-8. After leaving the directory context, return [read_text, stored_byte_count, path_still_exists].",
         "with tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / 'sample.txt'\n    with path.open('w', encoding='utf-8') as stream:\n        stream.write(data)\n    text = path.read_text(encoding='utf-8')\n    byte_count = len(path.read_bytes())\nresult = [text, byte_count, path.exists()]",
         [('café',['café',5,False]),('', ['',0,False]),('a\nb',['a\nb',3,False]),('🧠',['🧠',4,False])],
         ("path.open('w', encoding='utf-8')","path.open('w', encoding='latin-1')"),
         ["Close the writer before reading the file.", "Read bytes separately to measure encoded storage.", "Construct the final existence field after TemporaryDirectory has exited."],
         "café contains four code points but five UTF-8 bytes. The workspace is gone before the final existence check. A locale-like single-byte encoding cannot satisfy the accented and brain-character fixtures.",
         [['café',4,False],['café',5,True],['café',4,True]], "import tempfile\nfrom pathlib import Path"),
    ("Which two cleanup boundaries does a temporary text-file test need?", "The stream must close after writing, and the temporary workspace must be removed when its own context exits."))

add('json-boundary', 'json.loads: parsed values versus application schema',
    'https://docs.python.org/3.13/library/json.html#json.loads', [
    "Successful JSON parsing proves that text was decoded into supported values, not that those values satisfy an application's schema. A record still needs required-field, type and domain checks before business logic relies on it.",
    "In Python, bool is a subclass of int, so isinstance(True, int) is true. If a count must be an actual integer rather than a Boolean flag, use a policy that explicitly excludes booleans. Shape and exact field policy also matter: a list is not the required object and an extra field is not automatically harmless.",
    "This exercise names a deliberately strict two-field schema. It does not claim to reject duplicate textual keys before decoding; the standard decoder normally retains the last one. If duplicate detection or nonstandard numeric constants matter at a boundary, configure and test those policies separately."
    ],
    ("Why can isinstance(record['count'], int) admit an unintended Boolean count?",
     "bool is a subclass of int, so a stricter integer-only schema must explicitly exclude it.",
     ["JSON parsing converts every Boolean into text.", "A required count cannot ever be zero.", "Successful parsing validates all application fields."],
     "The parser's result type relationships and the application's allowed field types are separate contracts."),
    task("Transfer: validate an exact JSON record",
         "data is JSON text. Accept only an object with exactly name (a string) and count (a nonnegative int, excluding bool). Return the object when valid and None for parse/schema failure.",
         "try:\n    record = json.loads(data)\nexcept json.JSONDecodeError:\n    result = None\nelse:\n    valid = (isinstance(record, dict) and set(record) == {'name', 'count'}\n             and isinstance(record['name'], str) and type(record['count']) is int\n             and record['count'] >= 0)\n    result = record if valid else None",
         [('{"name":"job","count":2}',{'name':'job','count':2}),('{"name":"job","count":true}',None),('[]',None),('{"name":"job"}',None),('{',None),('{"name":"job","count":-1}',None)],
         ("type(record['count']) is int","isinstance(record['count'], int)"),
         ["Parse first, then validate the resulting shape.", "Check exact fields before indexing them.", "Exclude Boolean counts even though Python considers bool an int subclass."],
         "The complete nonnegative integer record is accepted. The Boolean, list, missing field, malformed text and negative count all take the explicit invalid path. The mutation admits a Boolean count incorrectly.",
         [None,{'name':'job','count':'2'},['job',2]]),
    ("What does a JSON parse not establish?", "Application schema, allowed field names, exact types, numeric domains and policies such as duplicate-key rejection."))

add('csv-quoting', 'csv.reader: quoting, escaped quotes and newline handling',
    'https://docs.python.org/3.13/library/csv.html#csv.reader', [
    "CSV records are not simply lines split on commas. A quoted field can contain a comma, a newline or an escaped quote. The parser has to track quoting state across those characters rather than treating each as an unconditional separator.",
    "Use a text stream and let csv.reader interpret records. When opening real files for this API, newline='' leaves newline handling to the CSV module. The transfer example uses StringIO with the same explicit newline policy and small in-memory text.",
    "Parsing CSV supplies rows of text fields; it does not infer an application schema or make a spreadsheet formula safe to open. Numeric conversion, row-width validation and exported-formula policies are separate requirements. This fixture focuses on preserving field boundaries exactly."
    ],
    ("Which fixture detects a parser that incorrectly assumes every physical line is a complete CSV record?",
     "A quoted field containing an embedded newline.",
     ["Only an unquoted row with two simple fields.", "Only a completely empty input.", "A list already parsed into Python fields."],
     "The embedded newline belongs inside one quoted field, so a line-by-line split would break the record structure."),
    task("Transfer: parse complete quoted records",
         "data is well-formed CSV text using comma delimiters and standard quotes. Return all rows as lists of text fields, preserving embedded commas/newlines and escaped quotes.",
         "result = list(csv.reader(io.StringIO(data, newline='')))",
         [('a,"b,c"\n',[['a','b,c']]),('id,note\r\n1,"line1\nline2"\r\n',[['id','note'],['1','line1\nline2']]),('',[]),('"a""b",c\n',[['a"b','c']])],
         ("list(csv.reader(io.StringIO(data, newline='')))","[line.split(',') for line in data.splitlines()]"),
         ["Pass a stream to csv.reader rather than manually splitting.", "A quoted newline is part of one field.", "Two consecutive quotes inside a quoted field represent one literal quote."],
         "The comma inside b,c stays in one field. The multiline note stays in one record. The escaped quote becomes a single quote character rather than a field separator.",
         [[['a','"b','c"']],[['a','b','c']],[['a','"b,c"']]], "import csv, io"),
    ("Which concerns remain after CSV parsing succeeds?", "Application field types, row/schema validation and any separate policy for how exported text will be interpreted by downstream software."))

add('aware-datetime', 'datetime.astimezone: preserving instants versus replacing tzinfo',
    'https://docs.python.org/3.13/library/datetime.html#datetime.datetime.astimezone', [
    "An aware timestamp includes an offset that relates its wall-clock reading to an instant. A naive timestamp lacks that information. Interpreting a naive value requires a policy; silently assuming a local timezone makes behavior machine-dependent.",
    "astimezone converts the displayed clock and offset while preserving the instant. replace(tzinfo=...) merely attaches a different timezone object without adjusting the clock. The two operations can look similar in code and represent different moments in time.",
    "Test a conversion that crosses a date boundary in each direction, plus an explicit naive-input policy. This small fixture uses fixed offsets only. It does not validate named-zone daylight-saving transitions, ambiguous local times or a timezone database version."
    ],
    ("Why is replace(tzinfo=UTC) different from converting an aware timestamp with astimezone(UTC)?",
     "Replacing the label preserves the clock fields; conversion adjusts them to preserve the instant.",
     ["Both operations always represent the same instant.", "Aware timestamps cannot cross a date boundary.", "A naive timestamp already identifies one unambiguous instant."],
     "An offset contributes to the interpretation of the clock fields. Changing the label alone can change the represented instant."),
    task("Transfer: UTC conversion with a naive policy",
         "data is a valid ISO datetime string with or without an offset. Return 'naive' if it has no usable offset; otherwise return its UTC ISO representation, preserving the instant.",
         "dt = datetime.fromisoformat(data)\nif dt.tzinfo is None or dt.utcoffset() is None:\n    result = 'naive'\nelse:\n    result = dt.astimezone(timezone.utc).isoformat()",
         [('2026-01-01T00:30:00+02:00','2025-12-31T22:30:00+00:00'),('2026-01-01T23:30:00-03:00','2026-01-02T02:30:00+00:00'),('2026-01-01T12:00:00','naive'),('2026-01-01T12:00:00+00:00','2026-01-01T12:00:00+00:00')],
         ("dt.astimezone(timezone.utc)","dt.replace(tzinfo=timezone.utc)"),
         ["Reject the missing-offset interpretation explicitly.", "Convert an existing instant rather than relabeling its clock.", "Subtract a positive offset and add the magnitude of a negative offset when reasoning about UTC."],
         "The +02:00 early-morning value moves back into the previous UTC date. The -03:00 late-night value moves into the next UTC date. A naive string is not assigned an invented instant.",
         ['2026-01-01T00:30:00+00:00','2026-01-01T02:30:00+00:00','naive'], "from datetime import datetime, timezone"),
    ("Which timezone cases require evidence beyond fixed-offset examples?", "Named-zone rules, daylight-saving transitions, ambiguous or nonexistent local times and the actual timezone database version."))

add('cli-arguments', 'argparse: parsing types versus validating the application domain',
    'https://docs.python.org/3.13/library/argparse.html#type', [
    "A command line arrives as text tokens. argparse can convert an option with type=int and report a conversion failure. Conversion and business validation are separate: an integer parser can accept a negative number that a nonnegative count contract rejects.",
    "Use a supplied argument list in a unit-sized example so it does not consume the validator's own process arguments. exit_on_error=False lets the particular invalid-integer option path here raise ArgumentError for explicit observation. Other command-line failures still need their own exit/error policy and tests.",
    "Test a positive count, valid zero, malformed integer text and a negative integer. These four cases distinguish token parsing from the nonnegative domain rule. Zero must not be rejected merely because it is falsy."
    ],
    ("Why does type=int not fully validate a nonnegative count option?",
     "It parses negative integer text successfully, so a separate domain check is still required.",
     ["int converts all negative values to zero.", "A parsed integer can never be zero.", "argparse automatically knows the application's count policy."],
     "The type conversion recognizes integer syntax. The application's allowed numeric range is an additional contract."),
    task("Transfer: a typed nonnegative count option",
         "data is ['--count', value_text]. Parse the required option as int. Return the count if nonnegative, 'negative-count' for a parsed negative value, and 'invalid-integer' for ArgumentError from malformed integer text.",
         "parser = argparse.ArgumentParser(exit_on_error=False)\nparser.add_argument('--count', type=int, required=True)\ntry:\n    args = parser.parse_args(data)\n    result = args.count if args.count >= 0 else 'negative-count'\nexcept argparse.ArgumentError:\n    result = 'invalid-integer'",
         [(['--count','3'],3),(['--count','0'],0),(['--count','x'],'invalid-integer'),(['--count','-2'],'negative-count')],
         ("args.count >= 0","args.count > 0"),
         ["Convert tokens with the parser's type argument.", "Check the nonnegative range after conversion.", "The zero fixture distinguishes >= from >."],
         "Three and zero parse and satisfy the domain. The malformed token fails conversion, while minus two parses successfully and fails only the range check.",
         ['3','negative-count','invalid-integer'], "import argparse"),
    ("What two layers should a CLI count option validate?", "Token conversion to the intended type and the application's allowed numeric domain, including legitimate boundary values such as zero."))

add('exception-groups', 'Tutorial 8.9: except* matching subgroups and preserving remainder',
    'https://docs.python.org/3.13/tutorial/errors.html#raising-and-handling-multiple-unrelated-exceptions', [
    "ExceptionGroup can carry several failures without collapsing them into one string. except* selects matching leaves and handles the matching subgroup. Nonmatching failures remain available for propagation rather than disappearing because one category was handled.",
    "An except* clause and an ordinary except cannot appear on the same try statement. A nested outer try can observe the remaining group after the inner except* has handled selected failures. This fixture deliberately uses a flat group so its counts are unambiguous.",
    "Test all-matching, mixed, no-matching and no-error cases. Catching Exception with except* instead of the intended ValueError can wrongly label TypeError failures as handled values. That is a semantic error even if the program no longer raises."
    ],
    ("What happens to nonmatching leaves after an except* ValueError handles a mixed group?",
     "They remain in an unhandled subgroup and can propagate to an outer observer.",
     ["They are silently discarded.", "They are converted into ValueError automatically.", "The first matched leaf makes the whole group successful."],
     "except* handles matching leaves while retaining the nonmatching failures. A broad handler would change that classification policy."),
    task("Transfer: handle one failure family and observe the rest",
         "data is [value_error_count, type_error_count], nonnegative small integers. Construct that flat group when nonempty. Handle ValueError leaves with except*, then observe the remaining group outside. Return ordered ['value', count] and/or ['remaining-type', count] entries; no errors gives an empty list.",
         "value_count, type_count = data\nerrors = [ValueError('v') for _ in range(value_count)] + [TypeError('t') for _ in range(type_count)]\nhandled = []\nif errors:\n    try:\n        try:\n            raise ExceptionGroup('batch', errors)\n        except* ValueError as group:\n            handled.append(['value', len(group.exceptions)])\n    except ExceptionGroup as remaining:\n        handled.append(['remaining-type', len(remaining.exceptions)])\nresult = handled",
         [([2,1],[['value',2],['remaining-type',1]]),([0,2],[['remaining-type',2]]),([1,0],[['value',1]]),([0,0],[])],
         ("except* ValueError as group:","except* Exception as group:"),
         ["Do not construct an empty ExceptionGroup.", "Handle only the intended matching leaves.", "Use an outer ordinary try to observe the unmatched flat subgroup."],
         "Two ValueErrors are handled first; the TypeError remains in a separate propagated group. A broad matching clause would count all three as values and lose the remaining-type observation.",
         [[['value',3]],[['remaining-type',3]],[['value',2]]]),
    ("Which four group shapes should a selective except* regression test?", "All matching, mixed matching/nonmatching, no matching and no errors. Nested group structure needs additional tests beyond this flat fixture."))

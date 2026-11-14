"""Original function/API transfer practice, including an actual import/script boundary."""
from python_guide_depth import add, task

add('function-return', 'Tutorial 4.8: defining functions / result values',
    'https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions', [
    "Calling a function evaluates its arguments, binds the parameter names and executes the function body. return sends a value back to the caller and stops that call. Falling off the end returns None. Printing a value has a visible side effect but does not send that value back as the function's result.",
    "Design a function from its input and output contract. State how the empty case is represented before using operations such as min or max, which require at least one item. A caller should not need to read console output to recover the answer.",
    "A result can contain several related values. The transfer function returns a two-element list when observations exist and None when no range can be computed. This makes absence distinct from a legitimate zero-width range such as [2,2]."
    ],
    ("A function computes a list but neither returns it nor prints it. What does its caller receive?",
     "None, because the function falls off the end.",
     ["The last computed expression automatically becomes the return value.", "The list is available from the terminal.", "Python guesses which local variable the caller wants."],
     "Unlike the interactive expression display, a function needs an explicit return to provide that computed value."),
    task("Transfer: a range-valued function",
         "data is an integer list. Implement bounds(values) to return [minimum, maximum], or None for empty input. Assign the function's return value to result.",
         "def bounds(values):\n    if not values:\n        return None\n    return [min(values), max(values)]\nresult = bounds(data)",
         [([2,-4,9],[-4,9]),([],None),([2],[2,2]),([0,0],[0,0])],
         ("return [min(values), max(values)]","[min(values), max(values)]"),
         ["Protect the empty case before calling min/max.", "Return the pair rather than just computing it.", "A repeated equal value still has valid minimum and maximum."],
         "The nonempty input has minimum minus four and maximum nine. A missing return loses both values despite computing them. Empty input deliberately returns None rather than inventing a numeric range.",
         [None,[9,-4],[2,9]]),
    ("Why should function tests inspect return values separately from stdout?", "Printing is a side effect. A caller receives the explicitly returned value, or None if the function falls off its end."))

add('default-factory', 'Tutorial 4.9.1: default argument evaluation / explicit shared containers',
    'https://docs.python.org/3.13/tutorial/controlflow.html#default-argument-values', [
    "Default argument expressions run when the function definition executes, not anew on each call. A list in that position can therefore accumulate state across calls. An immutable None default lets the function decide to allocate fresh storage during each call that omitted a container.",
    "Fresh storage should not erase an explicitly supplied container. Testing items is None preserves a caller's intentionally empty list, while if not items can replace that legitimate list. Distinguish the default-storage policy from a policy that always copies arguments.",
    "The transfer fixture observes independent default calls and deliberate sharing in the same program. It checks both contents and whether the explicit container is returned as the same object. Different references and equal contents answer different questions."
    ],
    ("Why must a fresh-default implementation test items is None rather than not items?",
     "An explicitly supplied empty list is a valid container that may need to be updated in place.",
     ["None is a mutable list.", "Every empty list should be discarded.", "The default expression executes on every call."],
     "The sentinel distinguishes omission from an empty caller-owned object. Truthiness conflates those cases."),
    task("Transfer: independent defaults and intentional reuse",
         "data is [first_value, second_value]. Two calls omitting items must return independent one-item lists. Two calls with one explicit shared list must update that list. Return [first_default_list, second_default_list, shared_list, explicit_return_is_shared].",
         "def collect(value, items=None):\n    if items is None:\n        items = []\n    items.append(value)\n    return items\nfirst = collect(data[0])\nsecond = collect(data[1])\nshared = []\nexplicit = collect(data[0], shared)\ncollect(data[1], shared)\nresult = [first, second, shared, explicit is shared]",
         [([1,2],[[1],[2],[1,2],True]),([0,0],[[0],[0],[0,0],True]),([-1,3],[[-1],[3],[-1,3],True])],
         ("items=None","items=[]"),
         ["Allocate only when the sentinel was supplied.", "Keep the explicit list, even when it is empty.", "Trace which calls share a container and which must allocate one."],
         "The default calls allocate separately. The explicit list receives both values and remains identical to the returned container. A mutable default joins the first two calls unexpectedly.",
         [[[1,2],[1,2],[1,2],True],[[1],[2],[1],True],[[1],[2],[1,2],False]]),
    ("When are default argument expressions evaluated?", "When the function definition executes. Use a sentinel and allocate inside a call when omitted mutable state must be fresh."))

add('keyword-only', 'Tutorial 4.9.3.3: keyword-only parameters',
    'https://docs.python.org/3.13/tutorial/controlflow.html#keyword-only-arguments', [
    "A parameter after a bare * is keyword-only. Calling the function must spell that parameter's name. This makes configuration such as a discount, encoding or timeout visible at the call site instead of depending on a reader remembering positional order.",
    "A default controls whether an argument may be omitted; keyword-only controls how a supplied argument is passed. These are separate API choices. Removing * silently expands the accepted calling forms even if valid keyword calls still compute the same values.",
    "An API contract includes rejected calls as well as successful ones. The transfer exercise runs a correct keyword call and observes that the corresponding positional call raises TypeError. Comparing only the arithmetic result of the valid call would miss the signature regression."
    ],
    ("Why is a valid keyword call insufficient to test a keyword-only API?",
     "The same call can work after the signature accidentally starts accepting positional configuration.",
     ["Keyword-only calls cannot return values.", "A default automatically makes every parameter keyword-only.", "Rejected calling forms are outside an API contract."],
     "Negative call-shape tests establish the signature boundary; successful values alone do not."),
    task("Transfer: enforce a named discount",
         "data is [amount, discount], both integers. Define quote(amount, *, discount=0). Return [valid_keyword_result, positional_discount_was_accepted]. The second element must be False.",
         "def quote(amount, *, discount=0):\n    return amount - discount\namount, discount = data\nvalid = quote(amount, discount=discount)\ntry:\n    quote(amount, discount)\n    accepted = True\nexcept TypeError:\n    accepted = False\nresult = [valid, accepted]",
         [([10,2],[8,False]),([0,0],[0,False]),([-3,2],[-5,False])],
         ("amount, *, discount=0","amount, discount=0"),
         ["Put a bare star before discount in the definition.", "Call the successful path with discount= explicitly.", "Observe rejection of the positional form without turning it into success."],
         "The arithmetic result is eight. Supplying the discount positionally must raise TypeError, yielding False in the receipt. Removing the star preserves eight but incorrectly changes the second field.",
         [[8,True],[12,False],[10,False]]),
    ("How do a default and a keyword-only marker differ?", "A default permits omission. The keyword-only marker requires a supplied value to be passed by name."))

add('positional-only', 'Tutorial 4.9.3.2: positional-only parameters and keyword dictionaries',
    'https://docs.python.org/3.13/tutorial/controlflow.html#positional-only-parameters', [
    "A slash marks earlier parameters as positional-only. Their internal names are not accepted as keywords for those parameters. This lets an API rename an internal parameter without promising that name as part of the keyword interface.",
    "A useful consequence appears with **metadata: a keyword whose spelling matches a positional-only parameter can still belong to the metadata dictionary. Without the slash, that keyword would try to bind the same ordinary parameter a second time and raise TypeError.",
    "Do not add positional-only markers indiscriminately. They make sense when names are incidental or when a separate keyword namespace is intentional. The transfer task makes that namespace distinction observable instead of treating the slash as syntax to memorize."
    ],
    ("What can a positional-only parameter allow when a function also collects **metadata?",
     "A keyword with the same spelling can be stored as metadata without rebinding that parameter.",
     ["All keywords are rejected even by **metadata.", "The positional-only value must always be numeric.", "The slash converts keyword values into positional values."],
     "The positional-only parameter's name is excluded from ordinary keyword binding, leaving that spelling available in the collected keyword dictionary."),
    task("Transfer: keep value and metadata separate",
         "data is [payload, metadata_value]. Define tagged(value, /, **metadata) and return [payload, metadata['value']] from a call that supplies payload positionally and the separate metadata using value=.",
         "def tagged(value, /, **metadata):\n    return [value, metadata['value']]\nresult = tagged(data[0], value=data[1])",
         [([7,'note'],[7,'note']),([None,0],[None,0]),([3,[]],[3,[]])],
         ("value, /, **metadata","value, **metadata"),
         ["Place value before the slash.", "The payload is positional; the matching keyword belongs to metadata.", "Removing the slash creates a duplicate binding rather than a harmless spelling change."],
         "Seven binds the positional-only parameter, while 'note' is stored under the metadata key value. An ordinary value parameter would instead receive both a positional and keyword argument.",
         [['note',7],[7,None],['value','note']]),
    ("What should be considered before making a parameter positional-only?", "Whether its name is incidental, whether keyword compatibility matters, and whether a separate keyword namespace is part of the API."))

add('argument-unpacking', 'Tutorial 4.9.5: unpacking argument lists',
    'https://docs.python.org/3.13/tutorial/controlflow.html#unpacking-argument-lists', [
    "*values expands an iterable into positional arguments at a call site. **options expands a mapping into keyword arguments. Passing values without the star sends the whole iterable as one argument rather than supplying its members separately.",
    "Unpacking still obeys the function's signature. Too many values, a missing required parameter, duplicate bindings or an unexpected keyword can raise TypeError. It is not an escape from input validation, and arbitrary external dictionaries should not be blindly forwarded to unrelated APIs.",
    "The transfer fixture combines exactly two positional numbers with one named scale. The shape of the argument list and the name of the option are explicit preconditions. This makes the distinction between packaging data and calling an API concrete."
    ],
    ("What does **options do when calling a function?",
     "It supplies mapping entries as keyword arguments, subject to the function's signature.",
     ["It passes the whole mapping as one positional argument.", "It makes unexpected keywords valid automatically.", "It deep-copies every argument."],
     "Unpacking determines the binding form; the signature still checks names, counts and duplicate bindings."),
    task("Transfer: call a configured calculation",
         "data is [numbers, options]. numbers contains exactly two integers and options contains exactly the integer key-value entry 'scale'. Define combine(a,b,*,scale) as (a+b)*scale and call it using both unpacking forms.",
         "def combine(a, b, *, scale):\n    return (a + b) * scale\nnumbers, options = data\nresult = combine(*numbers, **options)",
         [([[1,2],{'scale':3}],9),([[-2,2],{'scale':5}],0),([[3,4],{'scale':0}],0)],
         ("combine(*numbers, **options)","combine(numbers, **options)"),
         ["Expand the two-member sequence into separate positional arguments.", "Expand the option mapping into a named scale argument.", "A zero scale is a valid value rather than a missing option."],
         "One and two bind a and b; scale=3 binds the keyword-only parameter, giving nine. Passing the list as one argument leaves b missing.",
         [6,3,[3,3]]),
    ("Does argument unpacking bypass a function's input contract?", "No. Binding rules still reject missing, extra, duplicate or unexpected arguments."))

add('closure-binding', 'Programming FAQ: closures created in a loop / definition-time defaults',
    'https://docs.python.org/3.13/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result', [
    "A nested function can refer to names from an enclosing scope. The reference is a binding to look up when the function is called, not automatically a snapshot of the value when the function was created. A loop commonly reuses the same target name for every iteration.",
    "A default parameter expression is evaluated when each function is defined. Binding value=value in a generated callback therefore stores that iteration's object as a default. It snapshots a reference, not a deep copy; mutable objects can still be shared deliberately or accidentally.",
    "Call generated callbacks after the construction loop has finished to expose late binding. Calling each callback immediately inside the loop can hide the defect because the loop variable still has that iteration's value. Distinct inputs are necessary to make the difference observable."
    ],
    ("Why can calling each generated callback immediately inside its construction loop hide late binding?",
     "The shared loop name still has the current iteration's value at that moment.",
     ["A lambda cannot refer to an enclosing name.", "Closures always deep-copy every captured object.", "Late binding occurs only in threads."],
     "The defect appears when later calls observe the shared binding after the loop has moved on or finished."),
    task("Transfer: callbacks called after construction",
         "data is an integer list. Construct one callback per value; each adds its own captured value to a later argument. After the loop, call every callback with 10 and return the results in order.",
         "callbacks = []\nfor value in data:\n    callbacks.append(lambda extra, value=value: value + extra)\nresult = [callback(10) for callback in callbacks]",
         [([1,2,3],[11,12,13]),([],[]),([-2,0],[8,10]),([4,4],[14,14])],
         ("lambda extra, value=value:","lambda extra:"),
         ["Bind the iteration's value in each callback's default.", "Call callbacks only after construction is complete.", "Use distinct values to detect accidentally shared late lookup."],
         "The three callbacks retain defaults one, two and three and later add ten. Without the default binding, all three look up the final loop value three.",
         [[13,13,13],[1,2,3],[11,11,11]]),
    ("Does a default-bound closure snapshot copy a mutable object?", "No. It stores a reference evaluated at definition time; mutation of that shared object is a separate ownership question."))

add('nonlocal-state', 'Tutorial 9.2.1: scopes and namespaces / nonlocal rebinding',
    'https://docs.python.org/3.13/tutorial/classes.html#scopes-and-namespaces-example', [
    "Assigning to a name inside a function normally makes it local to that function. nonlocal declares that rebinding should instead affect an existing binding in a containing function scope. It does not select a module global, and that enclosing binding must already exist.",
    "A closure can use this rule to retain a small private counter across calls. The outer call creates the initial state once; each inner call updates the same enclosing binding. Reinitializing a local variable inside the inner call would erase the previous updates.",
    "Stateful functions need sequence-based tests. A single increment can agree with an incorrect implementation that resets before every call. The transfer fixture applies a positive, negative and later positive adjustment to verify cumulative state rather than independent calculations."
    ],
    ("What distinguishes nonlocal state from a variable reinitialized inside every callback?",
     "The nonlocal binding persists across calls to that closure and receives each update.",
     ["nonlocal always modifies a module global.", "A local assignment automatically updates every enclosing variable.", "The enclosing name need not exist."],
     "The closure refers to the enclosing call's binding. Resetting a local value each time changes the sequence contract."),
    task("Transfer: cumulative closure adjustments",
         "data is [initial, deltas], an integer and integer list. Build a counter closure and return its value after each successive adjustment.",
         "def make_counter(initial):\n    current = initial\n    def step(delta):\n        nonlocal current\n        current += delta\n        return current\n    return step\ninitial, deltas = data\ncounter = make_counter(initial)\nresult = [counter(delta) for delta in deltas]",
         [([10,[1,-2,3]],[11,9,12]),([0,[]],[]),([2,[0,0]],[2,2]),([-1,[-2,-2]],[-3,-5])],
         ("nonlocal current","current = initial"),
         ["Initialize the retained binding in the factory.", "Declare nonlocal before rebinding it inside step.", "Verify the second and third calls use earlier updates."],
         "Starting at ten gives eleven, then nine, then twelve. Resetting current to initial inside each step would produce independent results instead of a cumulative sequence.",
         [[11,8,13],[1,-2,3],[12,9,11]]),
    ("What kind of test detects an accidentally reset closure counter?", "A sequence of distinct updates checked after each call; one call cannot establish persistent cumulative state."))

add('recursive-base', 'Tutorial 4.8: function calls / base domain and decreasing subproblems',
    'https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions', [
    "A recursive function calls itself on a smaller subproblem. Correctness needs a domain, a base result and a rule that moves every recursive path toward that base. For factorial on nonnegative integers, the base value is one because it is the multiplicative identity.",
    "Rejecting a negative input prevents a recursion that moves farther from zero forever. A base case that returns zero makes every positive factorial zero. A mathematically correct recurrence also has practical recursion-depth limits; an iterative implementation is usually better for very large counts in Python.",
    "Test the base itself, the first recursive step, a larger valid input and an invalid input. These distinguish a correct base identity, a correct recurrence and an explicit domain policy. The small fixture does not claim arbitrary-depth safety."
    ],
    ("Why should factorial's negative-input policy be explicit?",
     "Repeatedly subtracting one from a negative input never reaches the nonnegative zero base case.",
     ["Every negative factorial is defined as zero by Python.", "A recursion limit proves the algorithm correct.", "A base result of zero is a multiplicative identity."],
     "A decreasing subproblem must be decreasing toward a valid terminating base within the stated domain."),
    task("Transfer: a checked recursion domain",
         "data is a small integer. Return its factorial for nonnegative values, and 'negative' for a rejected negative input. Define and call a recursive function.",
         "def factorial(n):\n    if n < 0:\n        raise ValueError('negative')\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)\ntry:\n    result = factorial(data)\nexcept ValueError:\n    result = 'negative'",
         [(0,1),(5,120),(-1,'negative'),(1,1)],
         ("if n == 0:\n        return 1","if n == 0:\n        return 0"),
         ["Reject the invalid domain before recursing.", "Use the multiplicative identity at zero.", "The recursive call moves n one step toward zero."],
         "Zero returns one directly; five multiplies down to that identity. The negative case is rejected before any recursion. Returning zero at the base collapses every nonnegative factorial.",
         [0,None,'negative']),
    ("What three facts must be explained for a recursive function?", "Its accepted domain, the correct base result, and why each recursive call approaches the base within that domain."))

add('module-main', 'Tutorial 6.1.1: executing modules as scripts / actual import side effects',
    'https://docs.python.org/3.13/tutorial/modules.html#executing-modules-as-scripts', [
    "Import executes a module's top-level definitions and statements. A main guard does not prevent all import-time execution; it prevents only the guarded script entry from running during an ordinary import. Definitions and lightweight initialization still happen.",
    "Place reusable functions outside the guard and script-only calls inside it. The imported module can then supply functions without printing a command's result, reading stdin or starting owned work merely because another module needs its definitions.",
    "The transfer program writes a temporary trusted module, imports it through Python's loader, and launches that file as a real child script. It observes quiet import, usable definitions and script output separately. The temporary directory and finite child timeout bound this authored check; it is not a learner-code execution sandbox."
    ],
    ("Does a main guard prevent all top-level statements from executing during import?",
     "No. Definitions and unguarded initialization still execute; only the guarded entry is skipped.",
     ["Yes, Python skips the entire module.", "Imports never execute Python code.", "The guard is needed only for syntax highlighting."],
     "The guard selects script-only behavior based on __name__. Reusable definitions outside it remain available to importers."),
    task("Transfer: inspect a real import and script run",
         "data is an integer. The trusted temporary module defines double and prints 'entry' only as a script. Import it quietly, call double(data), then execute its file as a child. Return [double_result, import_stdout, stripped_script_stdout].",
         "source = \"def double(value):\\n    return value * 2\\nif __name__ == '__main__':\\n    print('entry')\\n\"\nwith tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / 'lesson_module.py'\n    path.write_text(source, encoding='utf-8')\n    spec = importlib.util.spec_from_file_location('lesson_transfer_module', path)\n    module = importlib.util.module_from_spec(spec)\n    capture = io.StringIO()\n    with contextlib.redirect_stdout(capture):\n        spec.loader.exec_module(module)\n    child = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=5, check=True)\n    result = [module.double(data), capture.getvalue(), child.stdout.strip()]",
         [(3,[6,'','entry']),(0,[0,'','entry']),(-2,[-4,'','entry'])],
         ("if __name__ == '__main__':","if True:"),
         ["Keep the reusable definition outside the main guard.", "Capture import output independently from child output.", "A successful import must not emit the guarded entry message."],
         "The imported definition doubles three without printing. The child runs the same file with __name__ equal to __main__ and emits entry. An unconditional guard makes the import noisy even though the function still works.",
         [[6,'entry','entry'],[6,'',''],[3,'','entry']],
         "import contextlib, importlib.util, io, subprocess, sys, tempfile\nfrom pathlib import Path"),
    ("Which behaviors should an import/script regression distinguish?", "Quiet import, usable imported definitions, and deliberate script-only side effects. The main guard controls only the guarded code."))

add('functools-partial', 'functools.partial: prebound keyword configuration',
    'https://docs.python.org/3.13/library/functools.html#functools.partial', [
    "partial creates a callable with selected arguments already supplied. It is useful for separating configuration from the data that arrives later. The resulting object still calls the original function and does not cache its results.",
    "Prebound keyword arguments are defaults for that callable's future calls, not an immutable configuration seal. A later supplied keyword can override a prebound keyword. Mutable argument objects are stored by reference, so their ownership must still be considered.",
    "Bind configuration by name when that improves the API's readability. The transfer fixture retains the value parameter for later calls and binds factor and offset explicitly. Test a zero factor or an empty sequence so omitted work and intentional zero behavior stay distinct."
    ],
    ("Does partial cache results or make prebound keyword values impossible to override?",
     "Neither; it prebinds arguments for later calls, whose explicit keywords can override prebound keywords.",
     ["It memoizes every result automatically.", "It deep-copies all captured arguments.", "It prevents all later keyword arguments."],
     "partial controls argument binding. Caching and immutable configuration are separate concerns."),
    task("Transfer: configured numeric transformation",
         "data is [factor, offset, values], two integers and an integer list. Bind factor and offset with partial and later transform each value using value*factor+offset.",
         "def transform(value, *, factor, offset):\n    return value * factor + offset\nfactor, offset, values = data\nconfigured = functools.partial(transform, factor=factor, offset=offset)\nresult = [configured(value) for value in values]",
         [([2,1,[3,-1]],[7,-1]),([0,5,[9]],[5]),([3,0,[]],[])],
         ("offset=offset","offset=factor"),
         ["Leave the changing value argument unbound.", "Bind factor and offset using their parameter names.", "A zero factor still applies the configured offset."],
         "The configured operation is two times value plus one, producing seven and minus one. Binding the wrong offset changes both results without changing the callable's accepted shape.",
         [[8,0],[6,-2],[7,1]], "import functools"),
    ("What does functools.partial retain?", "The callable and prebound argument references. It neither caches results nor deep-copies configuration objects."))

add('import-discovery', 'importlib.import_module: controlled module and attribute selection',
    'https://docs.python.org/3.13/library/importlib.html#importlib.import_module', [
    "import_module loads a named module and returns its module object. getattr can then retrieve a specific attribute. Both names are part of the lookup contract; a module existing does not imply every requested attribute exists or is safe to call.",
    "Importing can execute code, so dynamic import is not a harmless string lookup for untrusted input. A small allowlist is appropriate for this authored dispatch example. It supports only the math module and two named functions, rejecting other choices before loading them.",
    "Discovery and execution should remain separate in larger plugin systems. Validate the selected callable's interface and ownership before invoking it. This transfer task deliberately avoids third-party plugins, package installation or a general-purpose dynamic execution feature."
    ],
    ("Why does dynamic module selection need a policy before importing arbitrary user-provided names?",
     "Import can execute module code, so it is more than reading inert metadata.",
     ["Python guarantees every installed module is side-effect free.", "getattr automatically validates a callable's entire interface.", "A module name is equivalent to a numeric array index."],
     "The import boundary can execute initialization and load dependencies. This example therefore rejects names outside its explicit allowlist."),
    task("Transfer: dispatch only approved math operations",
         "data is [module_name, operation, value]. Support only math.floor and math.ceil on finite numeric values. Return 'unsupported' for any other module or operation before importing it.",
         "module_name, operation, value = data\nif module_name != 'math' or operation not in ('floor', 'ceil'):\n    result = 'unsupported'\nelse:\n    module = importlib.import_module(module_name)\n    result = getattr(module, operation)(value)",
         [(['math','floor',2.7],2),(['math','ceil',-1.2],-1),(['os','system',0],'unsupported'),(['math','missing',0],'unsupported')],
         ("getattr(module, operation)","getattr(module, 'floor')"),
         ["Validate both names before the import path.", "Retrieve the approved operation named by the request.", "Floor and ceil differ on a non-integer value, including a negative value."],
         "Floor maps 2.7 to two; ceil maps minus 1.2 to minus one. Unapproved module or operation names take the explicit unsupported path. Always choosing floor would silently violate the approved ceil request.",
         [3,'unsupported',2.7], "import importlib"),
    ("Why does a dynamic-import allowlist belong before import_module?", "Import may execute code; rejecting an unsupported name afterward would cross the boundary before enforcing the policy."))

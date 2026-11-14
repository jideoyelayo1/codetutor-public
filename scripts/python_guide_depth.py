"""Original, section-scoped instruction and transfer practice; never execute during generation."""
import json

DEPTH = {}

def add(key, locator, url, paragraphs, reasoning, transfer, recall):
    assert key not in DEPTH
    assert len(paragraphs) >= 3
    assert transfer['mutation'][0] in transfer['body']
    DEPTH[key] = dict(locator=locator, url=url, paragraphs=paragraphs,
                      reasoning=reasoning, transfer=transfer, recall=recall)

def task(title, prompt, body, cases, mutation, hints, explanation, wrong, imports=""):
    return dict(title=title, prompt=prompt, body=body, cases=cases, mutation=mutation,
                hints=hints, explanation=explanation, wrong=wrong, imports=imports)

def transfer_program(spec, case=0, *, mutated=False, starter=False):
    body = spec['body']
    if mutated:
        body = body.replace(*spec['mutation'], 1)
    if starter:
        body = "# Write the computation for the stated input contract.\nresult = None"
    return ("import json\n" + spec['imports'] + "\ndata = " + repr(spec['cases'][case][0]) +
            "\n" + body + "\nprint(json.dumps(result, sort_keys=True, allow_nan=False))\n")

add('first-expression', 'Tutorial 3.1.1: Numbers / grouping, assignment and script output',
    'https://docs.python.org/3.13/tutorial/introduction.html#numbers', [
    "Read a program as a sequence of instructions. An expression such as 6 + 2 * 5 asks Python to calculate a value; it is not a command to display that value in a script. An assignment gives the calculated object a name. A print call requests visible output. The interactive prompt displays the value of a bare expression, which can make the distinction easy to miss when moving into a file.",
    "To trace 6 + 2 * 5, first calculate 2 * 5, obtaining 10, and then add 6, obtaining 16. The expression (6 + 2) * 5 instead calculates 8 first and produces 40. Parentheses communicate the intended calculation; they should come from the problem's units and meaning. A price per item multiplied by a count gives a subtotal. A fee charged once is added after that multiplication.",
    "Write one assignment per line while learning. Use descriptive names such as count and fee_cents, and a comment beginning with # to explain a choice. Do not copy the >>> prompt into a .py file. In the supplied programs, data is already provided and the final JSON print is the display wrapper. Changing the calculation should not require changing that wrapper. Integer cents keep this introductory billing problem exact; currency rounding policies come later."
    ],
    ("A script contains an assignment but no print call. What output should you expect from that assignment alone?",
     "No automatic display of its value.",
     ["The assigned value is automatically printed.", "The assignment is a syntax error.", "Every assignment displays None."],
     "A script executes assignment without displaying its value. A separate print call requests output; the interactive prompt has different display behavior."),
    task("Transfer: a charge applied once",
         "data is [count, unit_cents, fee_cents], all integers. Return [subtotal_cents, total_cents]. The subtotal is count times unit price; the fee is applied once, even when count is zero. Negative fees represent an explicit adjustment. Do not use floating point.",
         "count, unit_cents, fee_cents = data\nsubtotal = count * unit_cents\nresult = [subtotal, subtotal + fee_cents]",
         [([3,125,40],[375,415]),([0,125,40],[0,40]),([1,0,0],[0,0]),([2,50,-10],[100,90])],
         ("subtotal + fee_cents","subtotal + count * fee_cents"),
         ["Track the units: count times cents per item gives cents.", "Calculate the subtotal before adding a once-per-order fee.", "For [0,125,40], the subtotal is zero and the total is forty."],
         "Three items at 125 cents make 375 cents. Add the single 40-cent charge to obtain 415. Multiplying the fee by count violates the once-per-order rule; the zero-count and adjusted-fee fixtures expose that defect.",
         [[375,495],[165,495],[375,375]]),
    ("How do expression evaluation and output differ in a script?", "An expression computes a value; assignment binds it to a name; print explicitly requests output."))

add('name-rebinding', 'Tutorial 3.1.1 and 3.1.3: assignment, immutable numbers and shared lists',
    'https://docs.python.org/3.13/tutorial/introduction.html#lists', [
    "Draw names as arrows to objects. After count = 3 and saved = count, both names refer to the same integer value. Executing count = count + 2 first calculates a new value and then changes the count arrow. The saved arrow still refers to three. A name is not a box whose contents other names track automatically.",
    "An integer cannot be changed in place. The += spelling used with an integer computes and rebinds the target name. A list can be mutated: if a second name refers to the same list, appending through either name is visible through both. The spelling += therefore does not have one universal ownership meaning across all types. Start by identifying the object's type and whether the operation mutates it.",
    "In the transfer exercise, saved records an integer counter before a change. Its purpose is to retain the earlier value so that a later comparison is meaningful. The contract includes zero and negative updates, so testing only an increasing counter would leave important cases unexamined. No object identity numbers are needed to explain these integer values; value comparisons and an arrow diagram are enough."
    ],
    ("Why does changing an integer counter leave an earlier saved name unchanged?",
     "The counter name is rebound; the saved name keeps referring to the earlier immutable value.",
     ["Assignment makes every later change propagate to both names.", "Every assignment performs a deep copy.", "Integer objects are mutable containers."],
     "The distinction is rebinding versus mutation. This explains the saved integer without claiming that assigning a mutable list makes an independent copy."),
    task("Transfer: preserve the previous counter",
         "data is [initial_count, adjustment], both integers. Return [previous_count, updated_count]. Preserve the original value before applying the adjustment.",
         "counter = data[0]\nsaved = counter\ncounter = counter + data[1]\nresult = [saved, counter]",
         [([10,3],[10,13]),([0,0],[0,0]),([3,-5],[3,-2]),([-2,4],[-2,2])],
         ("saved = counter","saved = data[1]"),
         ["Bind a saved name before the update.", "The update rebinds counter; it does not rewrite the integer referred to by saved.", "With initial 3 and adjustment -5, the saved value is 3 and the updated value is -2."],
         "The two names initially refer to the initial integer. Rebinding counter after adding the adjustment leaves saved unchanged. Saving the adjustment instead of the counter can accidentally pass a symmetric input but fails the distinct-value fixtures.",
         [[3,13],[13,13],[10,10]]),
    ("Why should an alias diagram distinguish rebinding from mutation?", "Rebinding changes one name's reference. Mutation changes a shared mutable object and can be observed through other references."))

add('integer-division', 'Tutorial 3.1.1: floor division and the quotient/remainder identity',
    'https://docs.python.org/3.13/tutorial/introduction.html#numbers', [
    "The / operator performs true division; integer operands still produce a floating-point result. The // operator floors the quotient, meaning it rounds toward negative infinity. These operations answer different questions. For positive counts, floor division can count complete groups. When signed values are allowed, the direction of rounding must be stated explicitly.",
    "For -7 divided by 3, flooring gives -3 because -3 is the integer below -7/3. The remainder is 2, since (-3 * 3) + 2 reconstructs -7. Truncating toward zero would give -2 and would need a different remainder to reconstruct the input. Combining a truncated quotient with Python's % remainder mixes two different conventions.",
    "With a negative divisor, Python's nonzero remainder has the divisor's sign. Thus 7 divided by -3 gives quotient -3 and remainder -2. The useful invariant is dividend == quotient * divisor + remainder. The divisor must be nonzero; division by zero raises ZeroDivisionError. This lab intentionally states a nonzero-divisor domain instead of silently supplying a default."
    ],
    ("Which check verifies that a quotient and remainder belong to the same integer-division convention?",
     "dividend == quotient * divisor + remainder",
     ["quotient + remainder == dividend", "quotient must always round toward zero", "remainder must always be positive"],
     "Reconstruction works for either sign of nonzero divisor. A remainder need not be positive when the divisor is negative."),
    task("Transfer: signed quotient receipts",
         "data is [dividend, divisor], both integers with divisor nonzero. Return [floor_quotient, remainder, reconstructed_dividend]. Support either sign of divisor. Do not convert large integers to floats.",
         "a, b = data\nq, r = divmod(a, b)\nresult = [q, r, q * b + r]",
         [([-7,3],[-3,2,-7]),([7,-3],[-3,-2,7]),([-7,-3],[2,-1,-7]),([0,3],[0,0,0])],
         ("divmod(a, b)","(int(a / b), a % b)"),
         ["Use the pair returned by divmod so the operations share one convention.", "Flooring a negative non-integer quotient moves farther below zero.", "Check that q*b+r equals the original dividend for every receipt."],
         "For -7 and 3, q=-3 and r=2, so -9+2=-7. For 7 and -3, q=-3 and r=-2, so 9-2=7. Truncating a/b both changes signed behavior and introduces an unnecessary floating conversion.",
         [[-2,2,-4],[-3,-2,-11],[-2,-1,-7]]),
    ("What are the integer divmod invariants for a nonzero divisor?", "a == q*b+r; a nonzero remainder has b's sign and magnitude less than abs(b). The quotient is floored, not truncated."))

add('float-tolerance', 'math.isclose and Tutorial 15: relative versus absolute error near zero',
    'https://docs.python.org/3.13/library/math.html#math.isclose', [
    "A float stores a finite binary approximation. Many short decimal fractions have no exact finite binary representation, just as one third has no finite decimal expansion. The small discrepancy in 0.1 + 0.2 is a representation effect rather than random arithmetic. Display formatting can hide the discrepancy without changing the stored values.",
    "Choose a tolerance from the meaning of the measurement. math.isclose accepts a difference no larger than the greater of an absolute allowance and a relative allowance scaled by the larger magnitude. Relative tolerance is useful when values grow in scale. Near zero, a nonzero absolute tolerance is often necessary because scaling a relative tolerance by zero provides no useful error budget.",
    "A tolerance that is too generous hides real mistakes. The transfer task deliberately includes a small near-zero discrepancy that should pass, a larger one that should fail, and a large-magnitude value where the relative allowance matters. Its inputs are finite and its absolute tolerance is nonnegative. NaN, infinity, units, accumulated numerical error and domain-specific error analysis need explicit policies in later numerical lessons."
    ],
    ("Why can a comparison against zero need abs_tol even when rel_tol is nonzero?",
     "A relative allowance shrinks with the magnitudes; an absolute allowance supplies an error budget near zero.",
     ["rel_tol is ignored for all floats.", "Setting a tolerance changes the stored float.", "Every nonzero float should be considered equal to zero."],
     "isclose compares a difference with an allowed error. A nonzero relative allowance alone does not make a small nonzero value close to exactly zero under ordinary rel_tol below one."),
    task("Transfer: two measurement acceptance rules",
         "data is [observed, target, abs_allowance], with finite numeric values and abs_allowance >= 0. Return [accepted_by_isclose, exactly_equal]. Use rel_tol=1e-9 and the supplied absolute allowance.",
         "observed, target, allowance = data\naccepted = math.isclose(observed, target, rel_tol=1e-9, abs_tol=allowance)\nresult = [accepted, observed == target]",
         [([1e-12,0.0,1e-9],[True,False]),([1e-6,0.0,1e-9],[False,False]),([1000000000.5,1000000000.0,1e-9],[True,False]),([0.0,0.0,0.0],[True,True])],
         ("abs_tol=allowance","abs_tol=0.0"),
         ["Calculate the absolute difference before deciding.", "Near zero, compare the difference with the absolute allowance.", "For the large pair, the relative allowance is about one, exceeding the difference of one half."],
         "The first observation differs from zero but is within 1e-9. The second exceeds that absolute allowance. The large pair differs by 0.5, which fits the roughly 1.0 relative allowance. Exact equality is a separate Boolean in the receipt.",
         [[False,False],[True,True],[False,True]], "import math"),
    ("How should a numerical tolerance be chosen?", "From the units, scale and accepted error of the problem. Use absolute allowance near zero, relative allowance across scales, and cases that must fail as well as pass."))

add('explicit-conversion', 'Built-in int / parsing text before numeric operations',
    'https://docs.python.org/3.13/library/functions.html#int', [
    "Quotes make a numeric-looking value text. The values '12' and 12 therefore have different types and support different operations. Adding two strings concatenates them. Multiplying a string by an integer repeats it. Neither operation is a reliable way to calculate a bill or add measurements.",
    "Parse external text once where it enters the program. int accepts an integer representation, including surrounding whitespace and an optional sign. It rejects text such as '2.5' rather than rounding it. The expression int(float(text)) is a different policy: it may truncate and can lose information for large integers. Decide the accepted format before choosing a conversion.",
    "Separate valid zero from parse failure. A zero quantity is a real value in this exercise, while invalid text produces None. The try/except block is provided so the calculation can demonstrate both outcomes; later lessons explain exception control flow in depth. After conversion, arithmetic uses the parsed integers, and the result is numeric until the final display wrapper encodes it."
    ],
    ("Why should an integer-text parser reject '2.5' rather than silently convert it through float?",
     "The stated format is integer text; truncating a decimal would introduce an unstated data-loss policy.",
     ["int cannot parse a leading minus sign.", "All numeric strings have the same type as integers.", "A failed parse should always become a valid zero."],
     "Parsing implements an input contract. int('2.5') raises ValueError; accepting and truncating fractional text would change the contract."),
    task("Transfer: quantities arriving as text",
         "data is [quantity_text, unit_price_text], both strings. Parse each with int and return their numeric product. Return None if either string is not valid integer text. Whitespace and signed integer text are allowed.",
         "try:\n    quantity = int(data[0])\n    price = int(data[1])\nexcept ValueError:\n    result = None\nelse:\n    result = quantity * price",
         [(['3','12'],36),([' -2 ','5'],-10),(['0','200'],0),(['2.5','3'],None)],
         ("quantity * price","quantity + price"),
         ["Convert each input independently before doing arithmetic.", "Catch ValueError for invalid integer text; do not substitute zero.", "For '3' and '12', the numeric product is 36; string concatenation would be '312'."],
         "The conversion succeeds for signs and whitespace. Multiplication then combines numeric values. A decimal string is outside the integer-text domain and takes the explicit missing-result path. The zero case confirms that a valid zero is preserved.",
         [15,"312",None]),
    ("Why parse text at the input boundary?", "It establishes a numeric input contract before arithmetic and keeps invalid text distinct from legitimate values such as zero."))

add('string-index', 'Tutorial 3.1.2 and str / code-point indexing and empty boundaries',
    'https://docs.python.org/3.13/library/stdtypes.html#text-sequence-type-str', [
    "A string is an immutable sequence of Unicode code points. Index zero selects the first code point, and index -1 selects the last. There is no separate character type: indexing returns another string of length one. An empty string has no valid element index, so a boundary check belongs before first/last access.",
    "A code point, an encoded byte and a visible character are different units. The precomposed text é is one code point and two bytes in UTF-8. The visually similar text made from e followed by a combining acute accent has two code points and three UTF-8 bytes. A string index is not a safe cursor movement by one user-perceived character.",
    "The transfer result reports both units instead of confusing them. encode('utf-8') creates bytes for an external representation; it does not change the original string. The empty-input result preserves the absence of first/last values with None. Do not normalize user text or split grapheme clusters as an incidental fix; those choices require a policy, introduced in the text-processing stage."
    ],
    ("Two strings look like é, but one contains e plus a combining accent. What can their lengths tell you?",
     "Their code-point lengths can differ even when they look similar.",
     ["Visually similar strings must have identical lengths.", "len always returns the UTF-8 byte count.", "Every string index selects one grapheme cluster."],
     "len(str) counts code points. Encoding and grapheme segmentation use different representations and boundaries."),
    task("Transfer: a text boundary receipt",
         "data is a string, possibly empty. Return [first_code_point_or_None, last_code_point_or_None, code_point_count, UTF8_byte_count]. Preserve the original text.",
         "first = data[0] if data else None\nlast = data[-1] if data else None\nresult = [first, last, len(data), len(data.encode('utf-8'))]",
         [('é',['é','é',1,2]),('e\u0301',['e','\u0301',2,3]),('🧠',['🧠','🧠',1,4]),('',[None,None,0,0])],
         ("len(data.encode('utf-8'))","len(data)"),
         ["Guard empty text before element access.", "Count the original string and its UTF-8 encoding separately.", "The combining mark is itself the final code point in the decomposed two-code-point input."],
         "The precomposed é has one indexed element but two encoded bytes. The decomposed input exposes e and the accent separately. The empty case avoids IndexError and explicitly reports missing elements.",
         [['é','é',2,2],['é','é',1,1],['é','é',2,1]]),
    ("What does len(text) count, and what does len(text.encode('utf-8')) count?", "The first counts Unicode code points; the second counts encoded bytes. Neither generally counts user-perceived grapheme clusters."))

add('format-values', 'Tutorial 7.1.1: formatted string literals and precision',
    'https://docs.python.org/3.13/tutorial/inputoutput.html#formatted-string-literals', [
    "An f-string constructs text. Inside its braces, Python evaluates an expression; the part after a colon specifies how to display the result. The .2f format requests fixed-point text with two places after the decimal point, so 2.5 is displayed as 2.50. The resulting value is a string even when the expression was numeric.",
    "Formatting is not a calculation policy. It does not replace the stored float with the displayed value, and it does not make binary fractions exact. Later arithmetic still uses the original number unless you explicitly bind a different one. Keep numbers numeric for calculation and format at a presentation boundary.",
    "Tie rounding can surprise readers who expect every trailing five to round upward. Exact binary ties such as 1.375 round to an even final digit at two places, producing 1.38; -1.125 produces -1.12. Decimal-looking ties can also be affected by binary representation. Financial rounding rules need a deliberate decimal representation and policy, not a display format alone."
    ],
    ("What changes when value is displayed with f'{value:.2f}'?",
     "A new string is produced; the original numeric value is unchanged.",
     ["The float is permanently rounded to two places.", "The result remains an int.", "Every later calculation automatically uses the displayed text."],
     "Formatting returns text for presentation. It does not mutate an immutable float or alter the original binding."),
    task("Transfer: keep the calculation value",
         "data is a finite numeric value. Return [fixed_point_text_with_two_places, original_value]. Do not parse the formatted text back into a number.",
         "display = f'{data:.2f}'\nresult = [display, data]",
         [(2.5,['2.50',2.5]),(-1.125,['-1.12',-1.125]),(0,['0.00',0]),(1.375,['1.38',1.375])],
         ("f'{data:.2f}'","f'{data:.1f}'"),
         ["Apply .2f inside the f-string braces.", "Keep data itself as the second element.", "The trailing zero in '2.50' belongs to text, not a new floating-point precision setting."],
         "The receipt makes presentation and calculation values visible together. Fixed-point formatting supplies the requested digits; the original value, including its unrounded fraction, remains available separately.",
         [['2.5',2.5],['2.50',2],['2.50','2.50']]),
    ("Does formatting a float to two places define a financial rounding policy?", "No. It produces display text from a binary float; a financial policy also needs an explicit numeric representation and rounding rule."))

add('boolean-comparison', 'Language reference 6.10: chained comparison evaluation',
    'https://docs.python.org/3.13/reference/expressions.html#comparisons', [
    "Comparison operators ask a yes/no question about values. The interval lower <= value < upper includes the lower endpoint and excludes the upper endpoint. A half-open interval makes neighboring ranges meet without both claiming the shared boundary, which is useful for positions, age bands and time buckets.",
    "Python's chained comparison is not evaluated as if the first Boolean were then compared with upper. It has the meaning of two comparisons joined by and, with the middle expression evaluated once and the later comparison skipped if the first is false. Parenthesizing the first comparison changes the calculation because a Boolean is itself a value.",
    "A boundary-focused test table should contain a value below the lower limit, exactly at each endpoint and inside the interval. Also consider an empty interval where lower equals upper. None of its values should pass this half-open contract. Replacing < with <= can pass every interior test and still double-count the shared endpoint."
    ],
    ("For lower <= value < upper, why is testing value == upper useful?",
     "It detects an accidental inclusive upper bound that interior examples cannot distinguish.",
     ["The upper endpoint must always be accepted.", "A chained comparison first converts lower <= value into the new middle number.", "Boundary values are invalid tests."],
     "The intended upper comparison is strict. An implementation using <= at that position agrees on many interior values and fails exactly at the endpoint."),
    task("Transfer: place a value in one bucket",
         "data is [value, lower, upper], all integers with lower <= upper. Return whether value belongs to the half-open interval [lower, upper). An empty interval accepts no values.",
         "value, lower, upper = data\nresult = lower <= value < upper",
         [([5,5,8],True),([8,5,8],False),([4,5,8],False),([5,5,5],False)],
         ("value < upper","value <= upper"),
         ["Write both comparisons with value in the middle.", "Include lower with <= and exclude upper with <.", "When lower equals upper, no value satisfies both comparisons."],
         "Five belongs to [5,8), eight does not, and four lies below it. The empty [5,5) case catches the same inclusive-upper defect without needing an interior value.",
         [False,None,"5"]),
    ("Which four positions should an interval test table include?", "Below the lower bound, exactly at the lower bound, inside the interval and exactly at the upper bound; test an empty interval when allowed."))

add('none-sentinel', 'Built-in types: truth value testing / None versus falsy values',
    'https://docs.python.org/3.13/library/stdtypes.html#truth-value-testing', [
    "Missing data is a domain decision. None is Python's singleton for absence, but 0, False, empty text and empty containers are also falsy in an if condition. A test of truthiness therefore answers a broader question than whether a value is missing.",
    "Use is None when the contract specifically reserves None for absence. This identity check does not call a user-defined equality operation. Use value == 0 when asking about numeric value instead. The operators is and == answer different questions and should not be exchanged merely because a small example happens to agree.",
    "The expression data or fallback returns one of its operands. It is convenient when every falsy value should trigger a default, but it changes this task's meaning by replacing a legitimate zero or False. The transfer fixtures deliberately include multiple falsy values with different types; an answer that converts them all to a default loses information."
    ],
    ("A setting allows False but uses None for 'not supplied'. Which defaulting rule preserves that setting?",
     "fallback if value is None else value",
     ["value or fallback", "fallback if not value else value", "Always convert the setting to bool before defaulting."],
     "Only None denotes absence in this contract. Truthiness would also replace False and other valid falsy values."),
    task("Transfer: default only missing settings",
         "data may be None or any JSON value. Replace None with integer 7. Return every other value unchanged, including its type and empty-container shape.",
         "result = 7 if data is None else data",
         [(None,7),(0,0),(False,False),('', ''),([],[])],
         ("7 if data is None else data","data or 7"),
         ["State which one value represents missing data.", "Use identity with None rather than a truthiness test.", "A valid False must remain a Boolean False, and zero must remain numeric zero."],
         "None takes the default path. Zero, False, empty text and an empty list all keep their values. Strict type checks matter: treating False and zero as interchangeable would hide a contract violation.",
         [None,False,"7"]),
    ("When is value or fallback the wrong defaulting policy?", "When legitimate values such as zero, False or empty containers must survive and only None represents absence."))

add('list-first', 'Tutorial 3.1.3: list indexing, slicing and empty sequences',
    'https://docs.python.org/3.13/tutorial/introduction.html#lists', [
    "A list stores ordered references. Index zero refers to its first element regardless of that element's value. The list [0] is nonempty even though its first element is falsy. Checking the list before indexing protects the empty boundary; checking the first element's truthiness asks a different question.",
    "Indexing returns one element and raises IndexError when the position does not exist. Slicing returns a list and can safely produce an empty result: items[:1] is either a one-element list or an empty list. This makes slicing useful when the output must retain collection shape rather than collapse to a single value.",
    "An empty list and a list whose first item is None should remain distinguishable if a consumer needs to know whether an item existed. Returning both the prefix and the count preserves that distinction in the transfer exercise. The prefix is a new outer list but does not deep-copy objects stored inside it. Later collection lessons explore that ownership boundary."
    ],
    ("Why can 'if items and items[0]' incorrectly reject the first element of [0]?",
     "It tests the element's truthiness after confirming the list exists; zero is falsy but is a valid element.",
     ["[0] is an empty list.", "Index zero means the second element.", "All list elements must be truthy."],
     "Emptiness is a property of the container. The value of the stored element does not change whether its position exists."),
    task("Transfer: preserve presence and shape",
         "data is a JSON list. Return [first_one_element_slice, first_element_or_None, item_count]. Empty input has an empty prefix and no first element. Do not replace a present falsy first element.",
         "prefix = data[:1]\nfirst = data[0] if data else None\nresult = [prefix, first, len(data)]",
         [([0,8],[[0],0,2]),([],[[],None,0]),([None],[[None],None,1]),([''],[[''],'',1])],
         ("if data else None","if data and data[0] else None"),
         ["Use a slice when the output must remain a list.", "Guard the container's emptiness before indexing.", "Compare [] with [None]: the first-element field agrees, but the prefix and count do not."],
         "For [0,8], the prefix is [0], the first value is zero and the count is two. For empty input, there is no element to index. Keeping shape and count distinguishes a present None from the absence of an item.",
         [[[0],None,2],[0,0,2],[[0],0,1]]),
    ("How does items[:1] differ from items[0]?", "The slice returns a list, possibly empty, and is a shallow outer copy. Indexing returns an element and raises IndexError on empty input."))

add('error-location', 'Tutorial 8.1–8.3: syntax errors, exceptions and handlers',
    'https://docs.python.org/3.13/tutorial/errors.html#exceptions', [
    "A syntax error prevents Python from parsing a program. A runtime exception occurs while a parsed program is executing an operation. Start reading a traceback from its final exception type and message, then follow the relevant file and line back to the operation that failed. The highlighted line is evidence about where a failure surfaced, not proof of the underlying cause.",
    "int('oops') raises ValueError because the string has an unacceptable value for integer parsing. int(None) raises TypeError because the argument has the wrong kind of object. A handler for ValueError does not catch TypeError. Catching Exception around a large block can make unrelated bugs look like ordinary bad input.",
    "Keep the protected operation small and classify failures according to the input contract. In this exercise, malformed text and an unsupported input type produce distinct explicit statuses for inspection. A production parser may instead let the wrong-type failure propagate. Either policy is more informative than converting every failure into a successful zero, which would be indistinguishable from parsing the valid text '0'."
    ],
    ("How should a traceback guide the first debugging step?",
     "Identify the final exception type/message and inspect the relevant failing operation and its inputs.",
     ["Always delete the line named by the traceback.", "Catch every Exception and return zero.", "A parsed program cannot fail at runtime."],
     "A traceback localizes observed execution and reports an exception category. Investigating the operation and input distinguishes a domain error from a programming error."),
    task("Transfer: distinguish invalid value from wrong type",
         "data is integer text or None. Return ['ok', parsed_integer] for valid text, ['invalid-text', None] for text rejected by int, and ['wrong-type', None] for None. Catch the two exception categories separately.",
         "try:\n    result = ['ok', int(data)]\nexcept ValueError:\n    result = ['invalid-text', None]\nexcept TypeError:\n    result = ['wrong-type', None]",
         [('0',['ok',0]),('oops',['invalid-text',None]),(None,['wrong-type',None]),('2.5',['invalid-text',None])],
         ("except ValueError:","except Exception:"),
         ["Keep int(data) inside a small try block.", "ValueError and TypeError have different handlers in this contract.", "A broad first handler would also intercept the later wrong-type failure."],
         "Valid zero remains successful. Malformed text selects ValueError; None selects TypeError. The deliberate broad-handler mutation misclassifies None as invalid text, even though both cases execute without an unhandled exception.",
         [['invalid-text',None],['wrong-type',None],['ok',None]]),
    ("Why is catching a specific parsing error better than returning zero for every failure?", "It preserves valid zero and exposes distinct causes. Narrow handlers keep unrelated programming failures from masquerading as ordinary invalid input."))

def enrich(lesson, entry, question):
    """Append instruction/practice while preserving existing IDs, questions and exercise contracts."""
    detail = DEPTH.get(entry['key'])
    if detail is None:
        return None
    identifier = lesson['id']
    spec = detail['transfer']
    contract = '\n'.join('Input '+repr(a)+' → '+json.dumps(b,sort_keys=True,ensure_ascii=False)
                         for a,b in spec['cases'])
    lesson['body'] += detail['paragraphs']
    lesson['body'].append('Transfer walkthrough: '+spec['explanation'])
    lesson['reading'].append(dict(title='Python 3.13: audited bounded section',url=detail['url'],
                                  section=detail['locator'],
                                  note='The exact concepts and cases below are adapted and executed. This does not complete the whole reference section or its broader exercises.'))
    prompt, correct, wrong, explanation = detail['reasoning']
    lesson['quiz'].append(question(identifier,'reasoning',prompt,correct,wrong,explanation))
    expected = json.dumps(spec['cases'][0][1],sort_keys=True)
    lesson['quiz'].append(question(identifier,'transfer-boundary',
        'What exact JSON result satisfies this transfer contract?',expected,
        [json.dumps(x,sort_keys=True) for x in spec['wrong']],spec['explanation'],
        code=transfer_program(spec)))
    lesson['exercises'].append(dict(id=identifier+'.transfer',kind='Implement',title=spec['title'],
        prompt=spec['prompt']+'\nCheck all these cases:\n'+contract,
        starter=transfer_program(spec,starter=True),solution=transfer_program(spec),
        hints=spec['hints'],explanation=spec['explanation'],expectedOutput=expected))
    prompt, answer = detail['recall']
    return dict(id=identifier+'.3',trackID=lesson['trackID'],lessonID=identifier,
                prompt=prompt,answer=answer,sourceURL=detail['url'])

# Separate authoring units keep each ordered depth pack reviewable.
import python_guide_depth_control
import python_guide_depth_collections
import python_guide_depth_functions
import python_guide_depth_files
import python_guide_depth_data_model
import python_guide_depth_objects
import python_guide_depth_language
import python_guide_depth_professional
import python_guide_depth_concurrency
import python_guide_depth_math
import python_guide_depth_numpy
import python_guide_depth_numpy_advanced
import python_guide_depth_pandas
import python_guide_depth_pandas_advanced
import python_guide_depth_evaluation
import python_guide_depth_supervised
import python_guide_depth_selection
import python_guide_depth_torch
import python_guide_depth_models
import python_guide_depth_systems
import python_guide_depth_production
import python_guide_depth_capstones

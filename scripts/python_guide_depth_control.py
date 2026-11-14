"""Original transfer instruction for everyday control flow and text boundaries."""
from python_guide_depth import add, task

add('branch-order', 'Tutorial 4.1: if statements / overlapping predicates',
    'https://docs.python.org/3.13/tutorial/controlflow.html#if-statements', [
    "An if/elif/else chain checks conditions from top to bottom and executes the first matching branch. The remaining branches are skipped. Separate if statements are different: more than one of their bodies may run. Choose the form from whether your categories are exclusive or independent.",
    "Write down overlaps before coding a classification rule. A child can also be a student, so a child-first pricing rule must test age before the student flag. Invalid input should be rejected before it reaches a normal category. Reordering conditions can therefore change behavior even when every condition is individually correct.",
    "Construct a decision table with one row for each overlap and boundary. In the transfer problem, age eleven with a student flag must still be a child, age twelve with the flag is a student, and negative age is invalid. This table is a more precise specification than saying that the function should classify people sensibly."
    ],
    ("When do two overlapping predicates require a deliberate branch order?",
     "When the contract gives one category priority for inputs satisfying both predicates.",
     ["Never; Python sorts conditions by specificity.", "Every true branch in an elif chain always runs.", "Only the spelling of the category names matters."],
     "Python follows source order. Priority comes from the domain contract, so overlapping cases need explicit expected outcomes."),
    task("Transfer: classify overlapping categories",
         "data is [age, is_student], an integer and Boolean. Negative age is 'invalid'; ages below 12 are 'child'; remaining students are 'student'; everyone else is 'adult'. Child classification takes priority over the student flag.",
         "age, student = data\nif age < 0:\n    result = 'invalid'\nelif age < 12:\n    result = 'child'\nelif student:\n    result = 'student'\nelse:\n    result = 'adult'",
         [([11,True],'child'),([12,True],'student'),([20,False],'adult'),([-1,True],'invalid')],
         ("elif age < 12:","elif age < 0:"),
         ["Handle the invalid age before ordinary categories.", "Resolve the child/student overlap according to the stated priority.", "Use a single elif chain so exactly one category is selected."],
         "The eleven-year-old meets two ordinary predicates, so the child branch must win. The twelve-year-old no longer meets that branch and reaches the student flag. Invalid age is handled before either ordinary category.",
         ['student','adult','invalid']),
    ("What should a classification decision table test?", "Each category, each threshold and each overlap where branch priority changes the result."))

add('range-stop', 'Tutorial 4.3: range / positive and negative steps',
    'https://docs.python.org/3.13/tutorial/controlflow.html#the-range-function', [
    "range describes an arithmetic progression of integers without storing all its elements. Its stop value is excluded. With a positive step, values continue while below stop; with a negative step, they continue while above stop. A step of zero is invalid.",
    "The direction matters as much as the endpoints. Starting at five and stepping by minus two toward zero yields five, three and one. Starting below stop with a negative step yields no values because the initial value already fails the direction's bound. An empty range is an ordinary result, not necessarily an error.",
    "Materialize a list only when you need to inspect or retain its values. A for loop can consume range directly. For this small transfer receipt, a list makes both the sequence and its count visible. Testing an empty interval and a descending progression exposes assumptions hidden by range(n)."
    ],
    ("Why can range(0, 3, -1) be empty?",
     "Its negative step requires the current value to be above stop; the starting value already fails that bound.",
     ["Python changes a negative step to positive.", "The stop value is always yielded first.", "Empty ranges are syntax errors."],
     "The progression does not automatically choose a direction from the endpoints. The caller supplies the step and its sign controls the stopping comparison."),
    task("Transfer: inspect a stepped progression",
         "data is [start, stop, step], all integers and step nonzero. Return [all_values, value_count] for the corresponding range. Support descending and empty progressions.",
         "start, stop, step = data\nvalues = list(range(start, stop, step))\nresult = [values, len(values)]",
         [([2,8,2],[[2,4,6],3]),([5,0,-2],[[5,3,1],3]),([3,3,1],[[],0]),([0,3,-1],[[],0])],
         ("range(start, stop, step)","range(start, stop, 1)"),
         ["The caller's step is part of the contract.", "Stop is excluded in either direction.", "Check the initial value against the direction's bound before expecting any values."],
         "The upward progression excludes eight and advances by two. The descending progression excludes zero and advances by minus two. Equal endpoints and a direction pointing away from stop both produce empty lists.",
         [[[2,4,6,8],4],[[2,3,4,5,6,7],6],[[],0]]),
    ("What determines whether a range is empty?", "The start must satisfy the step direction's strict stop bound. Equal endpoints or a direction pointing away from stop produce no values."))

add('loop-accumulator', 'Tutorial 4.2 and 5.6: for traversal / prefix invariants',
    'https://docs.python.org/3.13/tutorial/controlflow.html#for-statements', [
    "A for loop obtains one value at a time from an iterable. Initialize aggregate state before the loop, update it once per accepted item and read the final result after traversal. Initializing inside the loop throws away earlier work and can leave no state at all on empty input.",
    "A loop invariant explains why an aggregate is correct. After consuming the first k items, count should equal k and total should equal the sum of that prefix. The invariant starts true at k=0, remains true after one update and describes the required answer when traversal ends.",
    "Include negative and zero contributions when they are legal. A sum is not a maximum and is not the last observed item. Returning both count and total in the transfer exercise makes those responsibilities explicit. It also gives an unambiguous result for no observations: count zero and total zero."
    ],
    ("Which invariant explains a correctly initialized counting and summing loop?",
     "After each prefix, count is the number of consumed items and total is their sum.",
     ["Total always equals the most recent item.", "Count starts at one even for empty input.", "The final assignment makes earlier updates irrelevant."],
     "A prefix invariant links each update to the whole computation and includes initialization and empty-input behavior."),
    task("Transfer: reconcile signed adjustments",
         "data is a list of integer adjustments. Return [number_of_adjustments, net_total]. Include negative and zero entries in the count.",
         "count = 0\ntotal = 0\nfor value in data:\n    count += 1\n    total += value\nresult = [count, total]",
         [([10,-3,0],[3,7]),([],[0,0]),([0],[1,0]),([2,2],[2,4])],
         ("total += value","total = value"),
         ["Define the empty-prefix state before traversal.", "A zero adjustment contributes one observation but no change to the total.", "Update total by adding to its existing value, not overwriting it."],
         "Three entries contribute ten minus three plus zero, so the receipt is [3,7]. Replacing accumulation with assignment leaves only the last item and breaks the prefix-sum invariant.",
         [[3,0],[2,7],[0,7]]),
    ("What makes a loop invariant useful for debugging?", "It states what the retained state means after every consumed prefix, allowing initialization, update and termination to be checked separately."))

add('break-search', 'Tutorial 4.4: break / first-match search',
    'https://docs.python.org/3.13/tutorial/controlflow.html#break-and-continue-statements', [
    "A first-match search has two parts: recognize a match and stop searching. Without the stop, later matching values can overwrite the answer. break leaves only the innermost enclosing loop; it is not a return from the whole function.",
    "Store the kind of result your caller needs. A value, an index and a Boolean are different contracts. A first index can be zero, so None is a useful not-found sentinel and a truthiness check on the index would be misleading.",
    "Test multiple matches to distinguish first-match behavior from last-match behavior. An empty collection and a nonempty collection with no match both yield None here. A match at position zero verifies that a valid first result is not confused with absence."
    ],
    ("Which fixture best distinguishes first matching index from last matching index?",
     "An input with at least two matching positions whose expected answer is the earlier position.",
     ["Only an input with no matches.", "Only an empty list.", "A test that accepts either matching index."],
     "The incorrect search can agree on no-match and single-match inputs. Multiple matches expose the missing stop."),
    task("Transfer: first threshold crossing",
         "data is [values, threshold], where values is an integer list. Return the first index whose value is >= threshold, or None if no item qualifies.",
         "values, threshold = data\nresult = None\nfor index, value in enumerate(values):\n    if value >= threshold:\n        result = index\n        break",
         [([[0,4,4],4],1),([[],4],None),([[1,2],9],None),([[5,6],5],0)],
         ("        break","        pass"),
         ["Track positions as well as values.", "Initialize a not-found sentinel before the loop.", "Stop immediately after storing the first qualifying position."],
         "The first threshold crossing in [0,4,4] is index one. Continuing would overwrite it with two. The final fixture makes zero a valid found index, separate from None.",
         [2,4,None]),
    ("Why should a first-match search test repeated matches?", "A missing break often passes no-match and one-match cases while returning the last match when several exist."))

add('continue-filter', 'Tutorial 4.4: continue / rejection before updates',
    'https://docs.python.org/3.13/tutorial/controlflow.html#break-and-continue-statements', [
    "continue skips the remaining statements in the current iteration and proceeds to the next item. It does not terminate traversal. Placing a rejection guard near the top of the loop lets later statements describe the accepted path without extra nesting.",
    "Decide which bookkeeping applies to rejected items. In this task, rejected_count changes before continue; appending to accepted happens only afterward. If continue is removed, the invalid item still reaches the accepted update even though its rejection was recorded.",
    "Zero belongs to the accepted domain because the rule excludes negative values, not falsy values. Keep input order and duplicates unless the contract explicitly requests sorting or deduplication. A filter changes membership; it does not silently change other properties."
    ],
    ("Where should an accepted-only state update occur in a rejection-guard loop?",
     "After the guard's continue, so rejected items cannot reach it.",
     ["Before checking the rejection condition.", "Only after the entire loop has stopped.", "Inside every rejected branch as well."],
     "continue prevents the remaining current-iteration statements from executing. Its location establishes which updates belong to accepted items."),
    task("Transfer: accepted values and rejection count",
         "data is an integer list. Return [nonnegative_values_in_original_order, number_of_negative_entries]. Retain zero and duplicates.",
         "accepted = []\nrejected = 0\nfor value in data:\n    if value < 0:\n        rejected += 1\n        continue\n    accepted.append(value)\nresult = [accepted, rejected]",
         [([-1,0,2,-3],[[0,2],2]),([],[[],0]),([0,0],[[0,0],0]),([-2],[[],1])],
         ("        continue","        pass"),
         ["Record the rejection before leaving that iteration.", "Only accepted items should reach append.", "Use value < 0, not a truthiness test, for the rejection rule."],
         "The negative values increment the rejection count and skip append. Zero remains present. Without continue, rejected values would appear in the accepted output despite being counted as rejected.",
         [[[-1,0,2,-3],2],[[2],3],[[0,2],0]]),
    ("How do break and continue differ?", "break exits the nearest loop. continue skips the rest of the current iteration and requests the next item."))

add('loop-else', 'Tutorial 4.5: else clauses on loops / exhaustion versus break',
    'https://docs.python.org/3.13/tutorial/controlflow.html#else-clauses-on-loops', [
    "A loop's else block runs when the loop finishes without break. For a for loop, that means normal exhaustion, including an iterable that was empty from the start. The else block belongs to the loop's completion condition, not to the nearest if statement.",
    "A search can use break to represent the early success path and else to represent failure after all candidates. Returning from a containing function or propagating an exception does not cause the loop's else to execute. The rule is about normal completion, not whether the loop body ever ran.",
    "In a compact example indentation makes the control structure visible. Trace an empty input, an early match and a final-position match before editing it. Replacing break with pass allows exhaustion and the else block can overwrite a previously stored success."
    ],
    ("When does a for loop's else run on an empty iterable?",
     "It runs, because normal exhaustion occurred without break.",
     ["It never runs because the body did not execute.", "It runs only after a break.", "It is attached to the last if regardless of indentation."],
     "An empty iterable is already exhausted. There is no break, so the normal-completion else path executes."),
    task("Transfer: distinguish found from exhausted",
         "data is [values, target], with an integer list and integer target. Return 'found' if a match is encountered and 'absent' otherwise. Use a loop else to represent exhaustion.",
         "values, target = data\nfor value in values:\n    if value == target:\n        result = 'found'\n        break\nelse:\n    result = 'absent'",
         [([[2,3],2],'found'),([[],2],'absent'),([[2,3],3],'found'),([[2,3],9],'absent')],
         ("        break","        pass"),
         ["Indent else with for rather than with if.", "A match must bypass the exhaustion branch.", "The empty input should take the same normal-exhaustion path as any no-match search."],
         "A match sets found and breaks, skipping else. A nonmatch search and an empty iterable reach normal exhaustion and assign absent. Pass does not bypass the else block.",
         ['absent',True,None]),
    ("What does a loop else express in a search?", "The iterable was exhausted normally without finding a condition that caused break, including the empty-input case."))

add('short-circuit', 'Built-in types: Boolean operations / left-to-right guards',
    'https://docs.python.org/3.13/library/stdtypes.html#boolean-operations-and-or-not', [
    "and evaluates its right operand only when the left operand is truthy. or evaluates its right operand only when the left operand is falsy. This allows a cheap validity guard to protect a later operation that would otherwise be invalid.",
    "Place a nonzero-denominator check before division. Reversing the two operands defeats the guard because the dangerous operation is attempted first. Replacing and with or also changes which path is evaluated and can both misclassify valid inputs and attempt division by zero.",
    "and and or return operands, not necessarily Boolean objects. This example uses comparison results on both sides, so its result is Boolean. When the contract demands a Boolean but operands are arbitrary values, make that conversion explicit. Short circuiting specifies evaluation order; it does not validate an entire input schema."
    ],
    ("Why must a denominator check appear to the left of an and guard protecting division?",
     "The right operand is evaluated only after the left guard succeeds.",
     ["Python evaluates the division first to see whether the guard is needed.", "and catches ZeroDivisionError automatically.", "or and and have identical evaluation rules."],
     "The protection comes from evaluation order and a skipped expression, not exception handling."),
    task("Transfer: a guarded ratio test",
         "data is [numerator, denominator], both finite numbers. Return False for a zero denominator; otherwise return whether their ratio is greater than two.",
         "numerator, denominator = data\nresult = denominator != 0 and numerator / denominator > 2",
         [([6,2],True),([6,0],False),([0,3],False),([-3,-1],True)],
         ("denominator != 0 and","denominator != 0 or"),
         ["Reject the zero denominator before evaluating the quotient.", "Use and to require both validity and the ratio predicate.", "A nonzero denominator alone does not imply that the ratio is greater than two."],
         "For [6,2], the guard succeeds and the ratio is three. For [6,0], the guard is false and division is skipped. For [0,3], division is valid but the final comparison is false.",
         [False,3,None]),
    ("Do and and or always return bool?", "No. They return a selected operand after short circuiting. Comparison operands happen to give a Boolean result in the guarded-ratio example."))

add('enumerate-offset', 'Tutorial 5.6 and enumerate: positions, values and start',
    'https://docs.python.org/3.13/library/functions.html#enumerate', [
    "enumerate pairs a running position with each value from an iterable. Its start parameter selects the first reported number. This avoids managing a separate counter and makes the relationship between a row and its position explicit.",
    "A reported offset does not change the underlying iterable's indexing. Starting labels at ten produces ten and eleven; it does not read elements ten and eleven from the input. Repeated values must still receive separate positions, so looking up each value with list.index is not a substitute.",
    "Choose a zero-based position for internal indexing and an explicit offset for user-facing line numbers or external record identifiers. Keep the contract clear about which one is being returned. Empty input produces no pairs regardless of the starting offset."
    ],
    ("Why is items.index(value) not a substitute for enumerate when values repeat?",
     "index finds the first equal value, so duplicate entries would receive the same position.",
     ["enumerate removes duplicate values.", "index always returns the current loop position.", "enumerate requires a list with unique values."],
     "enumerate counts traversal positions independently of equality between the stored values."),
    task("Transfer: label records with an offset",
         "data is [start_number, labels], an integer and a list of strings. Return [number, label] pairs in input order, including duplicate and empty labels.",
         "start, labels = data\nresult = [[number, label] for number, label in enumerate(labels, start=start)]",
         [([10,['a','b']],[[10,'a'],[11,'b']]),([0,[]],[]),([-2,['x']],[[-2,'x']]),([1,['x','x']],[[1,'x'],[2,'x']])],
         ("start=start","start=0"),
         ["Pass the required first number as enumerate's start.", "Keep each label attached to the position yielded with it.", "Duplicate labels are separate records and need distinct consecutive numbers."],
         "The starting offset labels the first traversed element, not a position to skip to. Each following element increments the number once, including repeated labels.",
         [[[0,'a'],[1,'b']],[[10,'b'],[11,'a']],[[10,'a'],[10,'b']]]),
    ("What changes when enumerate's start is changed?", "The reported counter labels change. The input traversal, ordering and underlying indexing do not."))

add('zip-length', 'Built-in zip: strict=True / alignment and unequal lengths',
    'https://docs.python.org/3.13/library/functions.html#zip', [
    "zip pairs corresponding items from its input iterables. By default it stops when the shortest input is exhausted, so extra items in a longer input are silently unused. That is useful for some tasks but dangerous when every field must align.",
    "strict=True raises ValueError when the iterables do not end together. The check happens while consuming the zip iterator; merely constructing it does not establish equal lengths. Materializing all pairs inside the try block ensures the complete alignment check runs here.",
    "Equal lengths do not prove semantic alignment. If two arrays have been sorted independently, their rows may still be paired incorrectly. The strict check catches a structural mismatch, while a real data pipeline also needs stable keys, ordering contracts or validated joins. The transfer problem deliberately checks only complete positional pairing."
    ],
    ("Why does creating a strict zip iterator without consuming it fail to verify alignment?",
     "Length disagreement is detected during iteration, when the inputs fail to end together.",
     ["strict=True immediately copies every input.", "zip never checks lengths even when consumed.", "An unconsumed iterator proves that all rows were processed."],
     "zip is lazy. The code must consume it to reach a later mismatch, and the failure can occur after earlier pairs have been yielded."),
    task("Transfer: reject incomplete field pairing",
         "data is [keys, values], two JSON lists. Return a list of [key, value] pairs when both lists have equal length; otherwise return 'length-mismatch'. Empty lists pair successfully.",
         "keys, values = data\ntry:\n    result = [list(pair) for pair in zip(keys, values, strict=True)]\nexcept ValueError:\n    result = 'length-mismatch'",
         [([['a','b'],[1,2]],[['a',1],['b',2]]),([[],[]],[]),([['a'],[1,2]],'length-mismatch'),([['a','b'],[1]],'length-mismatch')],
         ("strict=True","strict=False"),
         ["Consume the pairing iterator inside the error-handling scope.", "Require both iterables to finish together.", "A mismatch in either direction must be rejected, not truncated."],
         "The equal-length lists produce two ordered pairs. Either longer side violates the one-to-one contract. Default zip would silently drop an unmatched key or value.",
         [[['a',2],['b',1]],['a','b'],'length-mismatch']),
    ("What does strict zip establish, and what does it not establish?", "It checks simultaneous exhaustion during consumption. It does not prove that same-position records have matching semantic identities."))

add('unicode-normalize', 'unicodedata.normalize: canonical NFC versus compatibility NFKC',
    'https://docs.python.org/3.13/library/unicodedata.html#unicodedata.normalize', [
    "Unicode allows some visually similar text to have different code-point sequences. NFC normalization composes canonical equivalents where possible. It is useful when a contract intentionally treats canonically equivalent spellings as the same text.",
    "Compatibility normalization is a broader policy. NFKC can fold a fullwidth Latin letter into an ordinary Latin letter, while NFC retains that distinction. Normalization is also different from case folding, accent removal and grapheme segmentation. Do not treat these transformations as interchangeable cleaning operations.",
    "The transfer exercise exposes the normalized text and its code-point count. It includes both decomposed accents and a compatibility distinction, so an implementation using the wrong normalization form cannot pass by handling only common accented text. Normalization alone is not a defense against all visually confusable identifiers."
    ],
    ("Why can replacing NFC with NFKC change a data contract?",
     "NFKC also folds compatibility distinctions that NFC preserves.",
     ["NFC and NFKC are aliases.", "NFC always removes accents.", "Both forms lowercase every letter."],
     "The normalization forms define different equivalence policies. A fullwidth Latin letter distinguishes this contract's canonical normalization from compatibility normalization."),
    task("Transfer: canonical text receipt",
         "data is a string. Normalize with NFC and return [normalized_text, normalized_code_point_count]. Preserve compatibility distinctions such as fullwidth Latin letters.",
         "normalized = unicodedata.normalize('NFC', data)\nresult = [normalized, len(normalized)]",
         [('e\u0301',['é',1]),('é',['é',1]),('Ａ',['Ａ',1]),('', ['',0])],
         ("normalize('NFC', data)","normalize('NFKC', data)"),
         ["Choose the normalization form from the stated equivalence policy.", "Count the normalized text, not the original decomposed sequence.", "The fullwidth A remains fullwidth under NFC."],
         "The decomposed accent composes to one code point, matching precomposed é. Fullwidth A remains distinct because canonical normalization does not apply its compatibility mapping.",
         [['e\u0301',2],['é',2],['e',1]], "import unicodedata"),
    ("What does Unicode normalization not replace?", "An explicit policy for case folding, grapheme segmentation, compatibility distinctions and confusable identifiers."))

add('bytes-encoding', 'bytes.decode: converting bytes to text / strict UTF-8 decoding',
    'https://docs.python.org/3.13/library/stdtypes.html#bytes.decode', [
    "Text and encoded bytes are separate representations. str holds Unicode code points; bytes holds integers from zero to 255. Encoding chooses how to represent text as bytes, and decoding interprets bytes using a specified encoding.",
    "Choose UTF-8 because the input contract says UTF-8, not because a byte sequence looks readable. Strict decoding rejects an invalid sequence. Using errors='replace' keeps processing but inserts replacement characters, so it is a data-loss policy that must be deliberate and visible.",
    "The transfer input is a list of byte integers so it can be written as portable input data. bytes(data) constructs the byte sequence; decode then interprets it. An empty byte sequence decodes to empty text. Invalid UTF-8 is reported separately from that successful empty value."
    ],
    ("What policy change occurs when strict UTF-8 decoding is replaced by replacement decoding?",
     "Invalid byte sequences become replacement text instead of a reported decoding failure.",
     ["The original invalid bytes are repaired without information loss.", "All text is converted to ASCII.", "The byte sequence is guaranteed to contain valid Unicode before decoding."],
     "Replacement is a lossy recovery policy. It can be appropriate, but it does not satisfy a contract that must reject invalid encoding."),
    task("Transfer: strict UTF-8 input boundary",
         "data is a list of integers from 0 to 255. Return the decoded UTF-8 string, or 'invalid-utf8' if decoding raises UnicodeDecodeError. Use strict decoding.",
         "payload = bytes(data)\ntry:\n    result = payload.decode('utf-8', errors='strict')\nexcept UnicodeDecodeError:\n    result = 'invalid-utf8'",
         [([99,97,102,195,169],'café'),([],''),([255],'invalid-utf8'),([240,159,167,160],'🧠')],
         ("errors='strict'","errors='replace'"),
         ["Construct bytes without converting each integer to decimal text.", "Decode with the encoding and error policy named by the contract.", "Invalid input and successful empty text must remain distinguishable."],
         "The two-byte suffix represents é, and the four-byte fixture represents a single brain code point. Byte 255 is not a valid standalone UTF-8 sequence and follows the explicit error path.",
         ['cafÃ©','invalid-utf8',[99,97,102,195,169]]),
    ("Where should encoding and decoding occur?", "At boundaries between internal text and external byte representations, using an explicit encoding and error policy."))

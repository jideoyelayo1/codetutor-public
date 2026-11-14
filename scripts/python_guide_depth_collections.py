"""Original collection contracts with bounded personal-book section companions."""
from python_guide_depth import add, task, DEPTH

add('slicing-step', 'Built-in types: common sequence operations / slice bounds and steps',
    'https://docs.python.org/3.13/library/stdtypes.html#common-sequence-operations', [
    "A slice describes positions rather than element values. Its start is included, its stop is excluded, and its step controls both spacing and direction. A negative step walks toward lower positions. A zero step raises ValueError; it does not describe an empty slice.",
    "Omitted bounds are represented by None in a slice expression built from variables. For a negative step, leaving stop omitted is different from explicitly writing -1: an explicit negative index is interpreted relative to the sequence, while the omitted bound permits traversal past index zero. This explains why items[::-1] is the usual reversal spelling.",
    "Slices clamp out-of-range endpoints and preserve sequence shape; element indexing instead raises for a nonexistent position. For lists, the result is a new outer list that still refers to the selected objects. Inspect both values and length in the transfer task, including reverse and empty cases."
    ],
    ("Why can items[::-1] differ from items[len(items)-1:-1:-1]?",
     "An omitted negative-step stop differs from an explicit -1 index interpreted relative to the sequence.",
     ["A negative step always ignores both endpoints.", "Every explicit negative index means before the first item.", "A slice always includes its stop."],
     "Slice bounds are normalized with the direction. The explicit -1 identifies the final item rather than the omitted sentinel beyond index zero."),
    task("Transfer: slice receipts",
         "data is [items, start, stop, step], where items is a JSON list, start/stop are integer positions or None, and step is a nonzero integer. Return [selected_items, selected_count].",
         "items, start, stop, step = data\nselected = items[start:stop:step]\nresult = [selected, len(selected)]",
         [([[0,1,2,3,4,5],1,5,2],[[1,3],2]),([[0,1,2],None,None,-1],[[2,1,0],3]),([[],None,None,1],[[],0]),([[0,1,2],5,9,1],[[],0])],
         ("items[start:stop:step]","items[start:stop]"),
         ["Pass the supplied step into the slice.", "Keep omitted bounds as None rather than substituting a fixed index.", "A slice outside the available positions can be an empty list."],
         "The first slice visits positions one and three. The omitted-bound negative-step slice reverses the list. Empty and clamped-outside inputs produce empty lists with count zero.",
         [[[1,2,3,4],4],[[1,3,5],3],[[1,3],3]]),
    ("What three slice boundaries deserve separate tests?", "Positive stepping, negative stepping with omitted endpoints, and empty or out-of-range selection."))

add('nested-copy', 'copy: shallow versus deep copies / independently allocated nested rows',
    'https://docs.python.org/3.13/library/copy.html#copy.deepcopy', [
    "An outer list contains references to its elements. Repeating a list of one mutable row repeats the reference; it does not construct independent rows. A shallow outer copy also preserves references to the same nested objects. The resulting rows can look independent until a mutation exposes their shared identity.",
    "Create a fresh inner list on each comprehension iteration when constructing independent rows. Use deepcopy when copying an existing nested object graph actually requires that policy. Deep copying is not a universal reset: it preserves internal graph relationships with memoization and user-defined types can customize copying.",
    "A useful regression mutates one chosen row and checks every other row, not just the selected cell. Include at least two rows, since a single-row example cannot distinguish an independent construction from repeated aliases. This is the bounded ownership concept adapted from the supplied book's nested-list section."
    ],
    ("Why is a single-row fixture insufficient to detect repeated-row aliasing?",
     "There is no second row whose accidental shared mutation can be observed.",
     ["Aliasing is possible only with integer cells.", "A shallow copy always copies all nested rows.", "List repetition invokes deepcopy."],
     "The faulty and correct constructions agree when there is only one row. Multiple rows and one targeted update reveal sharing."),
    task("Transfer: independent measurement rows",
         "data is [row_count, column_count, target_row, target_column, value]. Counts are positive integers, the target is in bounds and value is an integer. Build an all-zero grid, update only the target cell and return the grid.",
         "rows, columns, r, c, value = data\ngrid = [[0] * columns for _ in range(rows)]\ngrid[r][c] = value\nresult = grid",
         [([2,3,0,1,7],[[0,7,0],[0,0,0]]),([1,1,0,0,4],[[4]]),([3,1,2,0,5],[[0],[0],[5]])],
         ("[[0] * columns for _ in range(rows)]","[[0] * columns] * rows"),
         ["Allocate a new row during each outer iteration.", "Repeating immutable zero cells is safe here; repeating the mutable row is the defect.", "After the update, inspect rows that were not targeted."],
         "Each row is a separately constructed list. Updating row zero cannot change row one. The one-row case is valid but the two- and three-row cases are required to expose the shared-row alternative.",
         [[[0,7,0],[0,7,0]],[[0,0,0],[0,7,0]],[[7,7,7],[0,0,0]]]),
    ("How can nested-list aliasing be tested observably?", "Mutate one inner list and verify that other rows keep their previous contents. Include multiple rows; comparing only initial values misses sharing."))

add('dict-counts', 'Tutorial 5.5: dictionaries / missing-key initialization',
    'https://docs.python.org/3.13/tutorial/datastructures.html#dictionaries', [
    "A dictionary associates each hashable key with a value. A frequency table uses the observed item as the key and a count as the value. get(key, 0) supplies a starting count for a missing key; adding one and assigning back records the current occurrence.",
    "Missing and present-with-zero are different states in many dictionaries, but this frequency contract deliberately treats both as the same starting count. Do not generalize that policy to every configuration or data-cleaning task. An empty string can be a legitimate key and should not be rejected by an unrelated truthiness test.",
    "Dictionary insertion order is deterministic for a given traversal, but an output sorted by key is a separate requirement. The transfer problem explicitly sorts the report without changing the counting rule. Duplicates must increase counts; replacing the stored value with one loses that information."
    ],
    ("Why is assignment of one for every observed key insufficient for a frequency table?",
     "It overwrites the previous count instead of accumulating repeated occurrences.",
     ["Dictionary keys cannot repeat in input data.", "get always mutates the dictionary.", "An empty string cannot be a key."],
     "Each occurrence must read and increment the existing count. The dictionary stores one entry per key, so frequency lives in its value."),
    task("Transfer: a deterministic frequency report",
         "data is a list of strings, including possible empty strings and duplicates. Return [key, occurrence_count] pairs sorted by key.",
         "counts = {}\nfor key in data:\n    counts[key] = counts.get(key, 0) + 1\nresult = [[key, counts[key]] for key in sorted(counts)]",
         [(['b','a','b'],[['a',1],['b',2]]),([],[]),(['',''],[['',2]]),(['0','False','0'],[['0',2],['False',1]])],
         ("counts.get(key, 0) + 1","1"),
         ["Use the whole string as the dictionary key.", "Increment the stored count for every occurrence.", "Sort keys only when constructing the final report."],
         "The traversal counts b twice and a once. Sorting the keys produces a before b in the report. Empty input gives no entries and an empty-string key remains valid.",
         [[['a',1],['b',1]],[['b',2],['a',1]],[['a',2],['b',1]]]),
    ("Which responsibilities should a frequency report keep separate?", "Counting occurrences and choosing a report order. Sorting input or keys does not itself count duplicates."))

add('set-membership', 'Tutorial 5.4: sets / difference and duplicate removal',
    'https://docs.python.org/3.13/tutorial/datastructures.html#sets', [
    "A set stores distinct hashable values. Membership answers whether a value is present, while set difference asks which values occur in one set but not the other. Neither operation preserves occurrence counts.",
    "If incoming values contain duplicates, constructing a set intentionally removes those duplicates. Subtract the known set to find previously unseen values. Union instead combines both sides and would reintroduce known values into a new-only report.",
    "Set iteration order is not an output-order contract. Sort comparable values when a deterministic report is required. If original first-seen order or multiplicity matters, use a different representation rather than relying on whichever order a set happens to display."
    ],
    ("What information is deliberately lost when incoming events become a set?",
     "Duplicate occurrence counts and a guaranteed original traversal order.",
     ["The ability to perform membership tests.", "All values that also appear in another collection.", "The values themselves are converted to strings."],
     "A set represents distinct values. Difference is a separate operation, and sorting the final set supplies an explicit report order."),
    task("Transfer: report unseen names",
         "data is [known_names, incoming_names], two lists of strings. Return sorted distinct incoming names that are absent from known_names.",
         "known, incoming = data\nresult = sorted(set(incoming) - set(known))",
         [([['a','b'],['b','c','c']],['c']),([[],[]],[]),([[],['x','x']],['x']),([['x'],[]],[])],
         ("set(incoming) - set(known)","set(incoming) | set(known)"),
         ["Deduplicate incoming names intentionally.", "Subtract known names rather than combining the sets.", "Sort only after determining the new-name set."],
         "The repeated c contributes one distinct new name. Known b is excluded. Union would incorrectly include a and b, violating the new-only condition.",
         [['a','b','c'],['c','c'],['b','c']]),
    ("When should a set be avoided for a report?", "When the report must retain duplicate counts or original occurrence order unless those properties are tracked separately."))

add('stable-sort', 'Sorting HOWTO: stability / sorted versus list.sort',
    'https://docs.python.org/3.13/howto/sorting.html#sort-stability-and-complex-sorts', [
    "sorted returns a new list. list.sort changes its target list in place and returns None. Assigning the return value of list.sort to a variable therefore does not produce the sorted list. Select the API from the ownership and return-value contract.",
    "Python sorting is stable: records with equal keys retain their input order, including when reverse=True selects descending key order. Adding an identifier as a secondary key is a different ordering policy. It can make a result look deterministic while violating the required tie order.",
    "Use equal-key records in an intentionally non-secondary-key order to test stability. Also verify whether the original list should remain unchanged. The transfer receipt reports the ranked list and an explicit unchanged-input check; it does not infer independence of the nested record objects."
    ],
    ("Why can adding an ID to a sort key violate a stable score-only ranking?",
     "It imposes a new tie-breaking rule instead of preserving arrival order for equal scores.",
     ["A tuple cannot be a sort key.", "reverse=True always destroys stability.", "sorted always mutates its input list."],
     "Stability preserves input order within equal-score groups. A secondary key can reorder those groups according to a different contract."),
    task("Transfer: stable descending scores",
         "data is a list of [name, finite_score] records. Return [records_ranked_by_descending_score, input_unchanged]. Preserve original order among equal scores and do not mutate the input list.",
         "before = [list(row) for row in data]\nranked = sorted(data, key=lambda row: row[1], reverse=True)\nresult = [ranked, data == before]",
         [([['a',2],['b',2],['z',3]],[[['z',3],['a',2],['b',2]],True]),([],[[],True]),([['x',-1]],[[['x',-1]],True])],
         ("key=lambda row: row[1]","key=lambda row: (row[1], row[0])"),
         ["Sort only on the score field.", "Use sorted when the input list must keep its order.", "Equal scores must preserve the original a-before-b order even in descending ranking."],
         "The highest score moves to the front, while the equal-score a and b records keep their arrival order. A descending secondary ID key would incorrectly reverse that pair.",
         [[[['z',3],['b',2],['a',2]],True],[[['a',2],['b',2],['z',3]],True],[[['z',3],['a',2],['b',2]],False]]),
    ("What must a sort regression check besides the keys' order?", "Tie behavior, whether input mutation is allowed, and the return-value contract of sorted versus list.sort."))

add('comprehension-filter', 'Tutorial 5.1.3: list comprehensions / selection and transformation',
    'https://docs.python.org/3.13/tutorial/datastructures.html#list-comprehensions', [
    "A comprehension combines traversal, selection and transformation into an expression. The for clause produces candidates, the if clause decides which candidates survive, and the leading expression constructs each retained result. Reading those responsibilities separately makes the compact syntax easier to trace.",
    "Filtering even integers is a numeric predicate, not a positive-value test. Negative even values and zero satisfy the evenness rule. Duplicates and traversal order remain unless another operation explicitly changes them.",
    "Prefer an ordinary loop when branching or side effects make the comprehension difficult to explain. A shorter expression is not automatically clearer. The transfer task is intentionally a simple pure transformation, so a comprehension expresses its contract without hidden updates."
    ],
    ("Which value exposes a mistaken positive-only filter in a task selecting even integers?",
     "A negative even integer such as -2.",
     ["Only a positive even integer.", "Only an empty list.", "An input with no numbers."],
     "The sign and parity predicates are independent. A negative even value must survive the stated parity filter."),
    task("Transfer: transform only even observations",
         "data is an integer list. Return twice each even value, retaining original order and duplicates. Negative even numbers and zero qualify.",
         "result = [value * 2 for value in data if value % 2 == 0]",
         [([-2,-1,0,2],[-4,0,4]),([],[]),([1,3],[]),([2,2],[4,4])],
         ("if value % 2 == 0","if value > 0"),
         ["Decide membership before applying the doubling expression.", "Use remainder to test parity.", "Preserve negative even values, zero and repeated accepted inputs."],
         "Minus two, zero and two survive the evenness predicate and are doubled. The positive-only alternative discards a valid negative and zero while admitting positive odd values.",
         [[4],[-4,0,2],[-2,0,2]]),
    ("How can a comprehension be traced in a readable order?", "Follow each candidate from the for clause, apply the filter, then evaluate the output expression only for retained candidates."))

add('deque-queue', 'collections.deque: FIFO removal and bounded end operations',
    'https://docs.python.org/3.13/library/collections.html#collections.deque', [
    "A FIFO queue removes the oldest pending item. Appending on the right and removing with popleft on the left implements that order. Removing with pop from the right instead gives stack behavior. The same container can support different policies; the operation pair defines which one is being used.",
    "Removing index zero from a list also gives FIFO order, but it shifts remaining references. deque supports efficient operations at both ends. This is an algorithmic data-structure distinction, not a measured throughput claim for every workload or a guarantee about a compound multi-step threaded operation.",
    "Source correction: the supplied first edition describes append followed by pop(0) as LIFO in its queue discussion. The actual operation sequence is FIFO. The original exercise below checks this observable ordering using fresh work IDs rather than reproducing the book's example. Bounded deque eviction and thread coordination have separate contracts."
    ],
    ("Which operation pair implements FIFO when new items are appended on the right?",
     "append for arrival and popleft for removal.",
     ["append and pop on the same right end.", "Sort all pending items before every removal.", "Choose whichever end contains the numerically smallest item."],
     "FIFO is arrival order, not reverse arrival or priority order. Removing from the opposite end of insertion retrieves the oldest item."),
    task("Transfer: dispatch the first two pending jobs",
         "data is a list of job IDs in arrival order. Process at most two jobs in FIFO order. Return [processed_IDs, remaining_IDs] without changing the original list.",
         "pending = deque(data)\nprocessed = []\nfor _ in range(min(2, len(pending))):\n    processed.append(pending.popleft())\nresult = [processed, list(pending)]",
         [(['a','b','c'],[['a','b'],['c']]),([],[[],[]]),(['x'],[['x'],[]]),(['a','b','c','d'],[['a','b'],['c','d']])],
         ("pending.popleft()","pending.pop()"),
         ["Copy the incoming sequence into an owned deque.", "Bound the number of removals by the pending length.", "The earliest two arrivals must appear first in the processed receipt."],
         "Appending arrivals a, b and c and removing from the left processes a then b. Removing from the right would process c then b. The empty and one-job fixtures protect the removal boundary.",
         [[['c','b'],['a']],[['a'],['b','c']],[['a','b','c'],[]]], "from collections import deque"),
    ("How can FIFO behavior be distinguished from stack behavior?", "Use at least two distinct arrivals and check removal order. Appending right and removing left is FIFO; appending and popping right is LIFO."))

add('heap-smallest', 'heapq: heap invariant and heappop',
    'https://docs.python.org/3.13/library/heapq.html#heapq.heapify', [
    "A min heap maintains a partial ordering that puts a smallest item at the root. It does not store every item in globally sorted order. heapify establishes the heap invariant, and heappop both removes the root and restores the invariant for the remaining items.",
    "Copy input values when the caller's list must remain unchanged. Calling heappop repeatedly on the copy yields values in ascending order, including duplicates. Indexing the internal heap array or removing arbitrary positions is not a substitute for the heap operations.",
    "State how many results are requested and what happens when fewer items exist. The transfer task returns at most k items, so k=0 and an empty input are legitimate boundaries. It uses a trusted small fixture rather than claiming any measured performance advantage."
    ],
    ("Why is reading the first k positions of a heap array not equivalent to k heappop calls?",
     "The heap only partially orders the array; each pop restores the invariant before the next minimum is retrieved.",
     ["heapify sorts every position globally.", "heappop removes the largest value.", "Duplicate values cannot be stored in a heap."],
     "Only the root minimum is guaranteed directly. Repeated removal and rebalancing produce the ordered sequence of minima."),
    task("Transfer: take up to k smallest values",
         "data is [values, k], an integer list and a nonnegative integer. Return the smallest min(k, len(values)) values in ascending order, retaining duplicates and leaving the input list unchanged.",
         "values, k = data\nheap = list(values)\nheapq.heapify(heap)\nresult = [heapq.heappop(heap) for _ in range(min(k, len(heap)))]",
         [([[4,1,3,1],3],[1,1,3]),([[],2],[]),([[3,2],0],[]),([[-1,-2,0],8],[-2,-1,0])],
         ("heapq.heapify(heap)","pass"),
         ["Establish the heap invariant before removal.", "Use the initial heap length to bound requested pops.", "Retrieve each minimum with heappop instead of taking an array prefix."],
         "Heapifying makes one a root minimum and each pop restores the invariant. Two equal minima are both retained. Bounding the count avoids popping from an exhausted heap.",
         [[4,1,1],[1,3,4],[1,3]] , "import heapq"),
    ("What ordering does a min heap guarantee?", "A smallest item is at the root under the heap invariant; the entire underlying array is not necessarily sorted."))

add('binary-search', 'bisect: bisect_left partition versus membership',
    'https://docs.python.org/3.13/library/bisect.html#bisect.bisect_left', [
    "Binary search relies on sorted input. bisect_left returns the first insertion position that keeps ascending order, putting an equal value at or after that boundary. An insertion position can be valid even when the searched value does not exist.",
    "For membership or a first equal index, check both that the position is in bounds and that the value there equals the target. With duplicates, bisect_left identifies the first equal position while bisect_right identifies the position after the equal run. They are not interchangeable.",
    "Do not silently sort an input when the required output is an index into its existing order. Sortedness is an explicit precondition in this exercise. Binary search locates a position efficiently; inserting into a Python list can still shift later elements, so search and insertion have different costs."
    ],
    ("Why must equality be checked after bisect_left returns an in-bounds index?",
     "An absent target can have an insertion point before a different existing value.",
     ["Every in-bounds insertion point is necessarily a match.", "bisect_left always returns -1 when absent.", "The input need not be sorted."],
     "For [1,3,5] and target 2, the insertion point is one but the stored value is three. Position validity alone does not establish membership."),
    task("Transfer: first equal index among duplicates",
         "data is [sorted_values, target], an ascending integer list and integer. Return the first equal index or None when absent. Do not change the input order.",
         "items, target = data\ni = bisect.bisect_left(items, target)\nresult = i if i < len(items) and items[i] == target else None",
         [([[1,3,3,5],3],1),([[1,3,5],2],None),([[],1],None),([[1,3],4],None)],
         ("bisect.bisect_left(items, target)","bisect.bisect_right(items, target)"),
         ["Use the left partition boundary to find the first duplicate.", "Protect the upper-end boundary before indexing.", "An insertion position is not a membership verdict until equality is checked."],
         "Three's equal run starts at index one. The right boundary would land after both equal entries and fail the first-equal contract. Interior and end absence cases must both return None.",
         [2,3,None], "import bisect"),
    ("How do binary-search membership and insertion differ?", "Insertion needs a sorted-order boundary. Membership additionally requires a valid position whose value equals the target."))

add('hash-equality', 'Data model: object.__hash__ / equal numeric mapping keys',
    'https://docs.python.org/3.13/reference/datamodel.html#object.__hash__', [
    "Hash-based containers use both hashes and equality. Equal hashable values must have equal hashes, but unequal values can share a hash. A hash is a lookup aid, not a unique identity or proof of equality.",
    "Some values of different numeric types compare equal. In Python, True, 1 and 1.0 are equal as mapping keys and occupy one entry. Text '1' is a different key. Converting keys to text would change those equivalence rules and can both split equal numeric keys and merge unequal text/numeric keys.",
    "A mutable object's changing equality-relevant state makes hashing difficult; a key must remain usable throughout its lifetime in the container. The transfer lab uses immutable JSON scalar keys and observes key equivalence only. It does not prescribe a hash implementation for arbitrary user-defined mutable classes."
    ],
    ("Why is converting every mapping key to str a change in equality policy?",
     "It can merge unequal text/numeric keys and split numerically equal values with different string representations.",
     ["str preserves every object's equality relationships.", "Hash equality is a unique identity check.", "Python forbids mixed types in mapping keys."],
     "The dictionary's original hash/equality behavior is part of the input contract. A text conversion creates a new key domain."),
    task("Transfer: count distinct native mapping keys",
         "data is a list of hashable JSON scalars, excluding containers. Return the number of distinct dictionary keys under Python's normal equality/hash rules. Do not stringify values.",
         "seen = {}\nfor value in data:\n    seen[value] = True\nresult = len(seen)",
         [([True,1,1.0],1),([0,False],1),(['1',1],2),([],0)],
         ("seen[value] = True","seen[str(value)] = True"),
         ["Use each original scalar as the key.", "Remember that Boolean and integer values can compare numerically equal.", "Keep the string '1' distinct from numeric one."],
         "True, one and one-point-zero represent one native mapping key. Zero and False also share a key, while text '1' and numeric one remain separate. Stringification violates both kinds of distinction.",
         [3,2,0]),
    ("What implication holds between equality and hashing?", "Equal hashable values must have equal hashes. Equal hashes do not prove equality because collisions are possible."))

add('linear-prefix', 'itertools.accumulate: accumulated sums / prefix-difference range queries',
    'https://docs.python.org/3.13/library/itertools.html#itertools.accumulate', [
    "A prefix-sum table stores a total for each prefix. Including an initial zero makes prefix[k] the sum of the first k items. This aligns positions with half-open intervals and handles empty prefixes naturally.",
    "The sum over values[start:stop] is prefix[stop] minus prefix[start]. Subtracting removes the contribution before start. An empty interval has equal prefix positions and therefore sum zero, even when earlier values are nonzero.",
    "Building the table takes one traversal and retains one more total than the number of items. Each later valid range query needs two table reads and a subtraction. This is an operation-count argument for repeated queries, not a measured timing result or a reason to allocate a table for every one-off sum."
    ],
    ("Why does a prefix table start with zero before any input values?",
     "It makes prefix[k] the first-k-items total and lets ranges beginning at zero use the same subtraction rule.",
     ["It forces every range total to be nonnegative.", "It removes the need to validate query bounds.", "It changes the original input values."],
     "The zero encodes the empty prefix. Negative contributions remain valid and query bounds are still a precondition."),
    task("Transfer: a half-open range total",
         "data is [integer_values, start, stop] with 0 <= start <= stop <= len(values). Build a leading-zero prefix table and return the sum over [start, stop).",
         "values, start, stop = data\nprefix = [0]\nfor value in values:\n    prefix.append(prefix[-1] + value)\nresult = prefix[stop] - prefix[start]",
         [([[2,-1,4,3],1,3],3),([[],0,0],0),([[5],0,1],5),([[1,2,3],2,2],0)],
         ("prefix[stop] - prefix[start]","prefix[stop] + prefix[start]"),
         ["Add one prefix entry after consuming each item.", "The interval excludes stop, matching the prefix positions.", "Subtract the total before start from the total before stop."],
         "The first range includes minus one and four, totaling three. Prefix[3] is five and prefix[1] is two, so their difference is three. The empty-interval fixture checks exact cancellation.",
         [7,5,2]),
    ("What cost tradeoff does a prefix table make?", "One traversal and O(n) retained totals support constant-count operations per later range query; a one-off query may not justify the retained table."))


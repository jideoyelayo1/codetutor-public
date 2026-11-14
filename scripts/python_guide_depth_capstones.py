"""Original Stage 24 capstone depth: integrated pure-Python checks that accompany the eight checked projects."""
from python_guide_depth import add, task

PY = 'https://docs.python.org/3.13/'

add('capstone-cli', 'argparse exit_on_error: testable command-line errors',
    PY+'library/argparse.html#exit-on-error', [
    "A command-line tool's interface is a contract: arguments, types, defaults and error behaviour. argparse validates types such as int and reports usage errors; by default it prints a message and exits with status 2, which is right for users but awkward inside tests.",
    "ArgumentParser(exit_on_error=False) raises argparse.ArgumentError for invalid values instead of exiting, so the parsing logic can be unit-tested and the CLI layer decides how to report the error. Keep the pure computation, here counting words, in a separate function that tests call directly.",
    "Test the installed command too, with subprocess, to cover packaging, the entry point and the real exit codes; the capstone project does exactly that. Output should be deterministic: most_common orders ties by first occurrence.",
    "The transfer parses arguments, counts the most common words and reports a type error without exiting."
    ],
    ("What does ArgumentParser(exit_on_error=False) change when --top receives 'x' with type=int?",
     "It raises argparse.ArgumentError instead of printing usage and exiting.",
     ["It silently uses the default value.", "It converts 'x' to 0.", "It exits with status 0."],
     "Raising lets tests and callers handle the error."),
    task("Transfer: a testable word-count CLI",
         "data is a list of argument lists. Parse [--top N] text with exit_on_error=False and return the top-N words with counts, or 'usage-error' on ArgumentError.",
         "parser = argparse.ArgumentParser(prog='wc', exit_on_error=False)\nparser.add_argument('--top', type=int, default=2)\nparser.add_argument('text')\ndef run(argv):\n    try:\n        args = parser.parse_args(argv)\n    except argparse.ArgumentError:\n        return 'usage-error'\n    return Counter(args.text.split()).most_common(args.top)\nresult = [run(a) for a in data]",
         [([['red blue red'],['--top','1','a b b'],['--top','x','a']],[[['red',2],['blue',1]],[['b',2]],'usage-error']),([['one']],[[['one',1]]]),([['--top','3','x y x z']],[[['x',2],['y',1],['z',1]]])],
         ("most_common(args.top)","most_common()"),
         ["type=int validates --top.", "exit_on_error=False raises instead of exiting.", "most_common(n) returns the n most frequent words."],
         "The default --top 2 lists red and blue; --top 1 keeps only b; a non-integer --top is reported as a usage error. Ignoring --top would return every word.",
         [[[['red',2],['blue',1]],[['b',2],['a',1]],'usage-error'],[[['red',2]],[['b',2]],'usage-error'],[[['red',2],['blue',1]],[['b',2]],[['a',1]]]],
         "import argparse\nfrom collections import Counter"),
    ("Why separate argument parsing from the CLI's computation?", "So the computation can be unit-tested directly and parsing errors handled without exiting."))

add('capstone-numerics', 'math.isclose: gradient-checked linear regression from scratch',
    PY+'library/math.html#math.isclose', [
    "Implementing linear regression by gradient descent from scratch ties together the loss, its gradient and the update rule. For mean squared error, dL/dw = (2/n) Σ (w·x + b - y)·x and dL/db = (2/n) Σ (w·x + b - y).",
    "Before trusting a hand-derived gradient, compare it with central differences at a test point using math.isclose and a relative tolerance. Dropping the factor x from dL/dw is a classic error: the code still runs and descends, but to the wrong answer.",
    "After the check passes, run enough iterations with a stable learning rate and compare the fitted parameters with the known answer on exact data. The capstone extends this with residual analysis and a NumPy cross-check.",
    "The transfer checks the analytic gradient numerically and fits a line exactly."
    ],
    ("Why check an analytic gradient against central differences before training?",
     "A wrong gradient can still decrease the loss and converge to the wrong parameters; the check catches it directly.",
     ["Central differences are faster to train with.", "It replaces the need for a loss function.", "It guarantees the learning rate is stable."],
     "Gradient checks validate derivations on small inputs."),
    task("Transfer: verify, then fit",
         "data is [xs, ys]. Check the analytic MSE gradient at (w, b) = (0.5, 0) against central differences with rel_tol=1e-5, then run 2000 steps of gradient descent with rate 0.05 from (0, 0). Return [gradient check passed, w rounded to 3 places, b rounded to 3 places].",
         "xs, ys = data\ndef loss(w, b):\n    return sum((w * x + b - y) ** 2 for x, y in zip(xs, ys)) / len(xs)\ndef grad(w, b):\n    n = len(xs)\n    return (sum(2 * (w * x + b - y) * x for x, y in zip(xs, ys)) / n, sum(2 * (w * x + b - y) for x, y in zip(xs, ys)) / n)\nh = 1e-6\ngw, gb = grad(0.5, 0.0)\nnumeric = ((loss(0.5 + h, 0) - loss(0.5 - h, 0)) / (2 * h), (loss(0.5, h) - loss(0.5, -h)) / (2 * h))\nw = b = 0.0\nfor _ in range(2000):\n    dw, db = grad(w, b)\n    w, b = w - 0.05 * dw, b - 0.05 * db\nresult = [math.isclose(gw, numeric[0], rel_tol=1e-5) and math.isclose(gb, numeric[1], rel_tol=1e-5), round(w, 3), round(b, 3)]",
         [([[0,1,2],[1,3,5]],[True,2.0,1.0]),([[1,2,3],[2,4,6]],[True,2.0,0.0]),([[0,1,2,3],[3,2,1,0]],[True,-1.0,3.0])],
         ("sum(2 * (w * x + b - y) * x for","sum(2 * (w * x + b - y) for"),
         ["dL/dw includes the factor x.", "Compare with central differences at a test point.", "Exact data should be fitted exactly."],
         "The analytic and numeric gradients agree, and descent recovers y = 2x + 1. Dropping the x factor fails the check and fits the wrong line.",
         [[False,2.0,1.0],[True,1.0,2.0],[True,2.0,0.0]],
         "import math"),
    ("What does dropping x from dL/dw do to gradient descent?", "It still runs and converges, but to wrong parameters; a gradient check catches it."))

add('capstone-pandas', 'csv.DictReader: audited ingestion with per-row rejection reasons',
    PY+'library/csv.html#csv.DictReader', [
    "A data pipeline's first stage decides which records are trusted. Check required columns once, then validate each row: parse types, enforce key uniqueness and record why every rejected row was rejected, with its line number.",
    "Rejecting a row is safer than guessing a fix, but silently dropping it hides data-quality problems. A rejection report, counts by reason with example line numbers, lets someone fix the source and shows when quality changes.",
    "csv.DictReader maps each row to a dictionary keyed by the header. Line numbers start at 2 because the header is line 1. The capstone builds the same audit with pandas, typed columns and validated joins.",
    "The transfer ingests CSV text, keeps valid unique rows and reports rejections."
    ],
    ("Why record a reason and line number for every rejected row?",
     "So data-quality problems are visible and the source can be fixed, instead of rows disappearing silently.",
     ["Because csv requires it.", "To make the pipeline faster.", "So rejected rows can be kept anyway."],
     "An audit trail turns silent loss into actionable evidence."),
    task("Transfer: validated CSV ingestion",
         "data is CSV text. Require columns id and value. Keep rows whose value parses as float and whose id is new; reject others as 'bad-value' or 'duplicate-id' with their line numbers. Return [sorted missing columns, kept [id, value] rows, rejections].",
         "reader = csv.DictReader(io.StringIO(data))\nmissing = {'id', 'value'} - set(reader.fieldnames or [])\nseen, clean, rejected = set(), [], []\nif not missing:\n    for line, row in enumerate(reader, start=2):\n        try:\n            value = float(row['value'])\n        except ValueError:\n            rejected.append([line, 'bad-value'])\n            continue\n        if row['id'] in seen:\n            rejected.append([line, 'duplicate-id'])\n            continue\n        seen.add(row['id'])\n        clean.append([row['id'], value])\nresult = [sorted(missing), clean, rejected]",
         [('id,value\na,1\nb,x\na,2\n',[[],[['a',1.0]],[[3,'bad-value'],[4,'duplicate-id']]]),('id,amount\na,1\n',[['value'],[],[]]),('id,value\nz,0.5\ny,-1\n',[[],[['z',0.5],['y',-1.0]],[]])],
         ("if row['id'] in seen:","if False:"),
         ["Check required columns before reading rows.", "Line numbers start at 2 after the header.", "Reject duplicates rather than overwriting."],
         "Row a is kept, b's value cannot be parsed and the second a is a duplicate, each reported with its line. A file without a value column is rejected as a whole. Skipping the duplicate check would keep two records for a.",
         [[[],[['a',1.0],['a',2.0]],[[3,'bad-value']]],[[],[['a',1.0]],[[2,'bad-value'],[3,'duplicate-id']]],[['id'],[],[]]],
         "import csv, io"),
    ("What should a validating ingestion step output besides clean rows?", "A rejection report with reasons and line numbers."))

add('capstone-tabular', 'hashlib: deterministic hash-based train/test assignment',
    PY+'library/hashlib.html#hashlib.sha256', [
    "Random splits change when the data changes or a seed is forgotten, and a record can move from test into training between runs, leaking evaluation data. Assigning each record by a hash of its stable identifier makes the split deterministic and independent of row order.",
    "Python's built-in hash() is randomized per process for strings, so it must not be used for persistent assignment. A cryptographic digest such as SHA-256, reduced modulo 100, gives a stable bucket; buckets below 20 form a 20% test set.",
    "The proportion is approximate for small datasets, and records of one entity must share an identifier so they land on the same side. Check disjointness and stability in tests, as the capstone does before fitting its pipeline.",
    "The transfer assigns synthetic user ids by hash and checks coverage, disjointness, stability and proportion."
    ],
    ("Why not use Python's built-in hash() to assign records to splits?",
     "String hashes are randomized per process, so assignments would change between runs.",
     ["hash() is too slow.", "hash() only works on integers.", "hash() always returns 0 for strings."],
     "Use a stable digest such as hashlib.sha256."),
    task("Transfer: stable hash splits",
         "data is a record count. Assign ids 'user-0', 'user-1', ... to test when sha256(id) mod 100 < 20. Return [all ids assigned, train and test disjoint, assignment repeatable, test share between 10% and 30%].",
         "def bucket(identifier):\n    return int(hashlib.sha256(identifier.encode()).hexdigest(), 16) % 100\nids = [f'user-{i}' for i in range(data)]\ntest = {i for i in ids if bucket(i) < 20}\ntrain = set(ids) - test\nagain = {i for i in ids if bucket(i) < 20}\nresult = [len(train) + len(test) == data, train.isdisjoint(test), test == again, 10 <= len(test) * 100 // data <= 30]",
         [(200,[True,True,True,True]),(500,[True,True,True,True]),(1000,[True,True,True,True])],
         ("bucket(i) < 20}\ntrain","bucket(i) < 2}\ntrain"),
         ["A digest of a stable id gives a stable bucket.", "Test and train must be disjoint.", "The share is approximately the bucket threshold."],
         "Every id lands on exactly one side, the same ids are chosen on every run, and about 20% go to test. A threshold of 2 would produce a test set of about 2%.",
         [[True,True,False,True],[True,False,True,True],[True,True,True,False]],
         "import hashlib"),
    ("How do you make a train/test split stable across runs and data updates?", "Assign by a stable digest of each record's identifier, not by random shuffling."))

add('capstone-vision', 'A pure-Python valid convolution with a shape contract',
    PY+'library/functions.html#sum', [
    "A 'valid' 2-D convolution slides a kh × kw kernel over an H × W image without padding, producing an (H - kh + 1) × (W - kw + 1) output. Each output value is the sum of elementwise products under the kernel, which is what deep-learning libraries call convolution (technically cross-correlation, without flipping the kernel).",
    "Writing it out in plain Python makes the indexing explicit: output (i, j) uses image rows i..i+kh-1 and columns j..j+kw-1. Off-by-one errors in these ranges produce the wrong shape or silently read the wrong pixels.",
    "Use such a reference implementation to test faster versions: the capstone's PyTorch classifier checks its layer shapes, and a slow, obvious implementation is the best oracle for a fast one.",
    "The transfer convolves a small image with a difference kernel and reports shape and values."
    ],
    ("A 3 × 3 image is convolved (valid) with a 2 × 2 kernel. What is the output shape?",
     "2 × 2.",
     ["3 × 3.", "1 × 1.", "4 × 4."],
     "Valid convolution gives (H - kh + 1) × (W - kw + 1)."),
    task("Transfer: reference convolution",
         "data is [image, kernel] as nested lists. Compute the valid cross-correlation. Return [[output height, output width], output values].",
         "image, kernel = data\nkh, kw = len(kernel), len(kernel[0])\nout = [[sum(image[i + a][j + b] * kernel[a][b] for a in range(kh) for b in range(kw)) for j in range(len(image[0]) - kw + 1)] for i in range(len(image) - kh + 1)]\nresult = [[len(out), len(out[0]) if out else 0], out]",
         [([[[1,2,3],[4,5,6],[7,8,9]],[[1,0],[0,-1]]],[[2,2],[[-4,-4],[-4,-4]]]),([[[1,2],[3,4]],[[1,1],[1,1]]],[[1,1],[[10]]]),([[[0,1,0,1]],[[1,-1]]],[[1,3],[[-1,1,-1]]])],
         ("image[i + a][j + b]","image[i][j]"),
         ["Output size is H - kh + 1 by W - kw + 1.", "Offset the image index by the kernel position.", "Sum the elementwise products."],
         "Each output subtracts the pixel diagonally below-right from the current one, giving -4 everywhere for this image. Forgetting the kernel offset multiplies the same pixel by every kernel entry.",
         [[[3,3],[[-4,-4],[-4,-4]]],[[2,2],[[0,0],[0,0]]],[[2,2],[[4,4],[4,4]]]]),
    ("What output shape does a valid convolution produce?", "(H - kh + 1) × (W - kw + 1) for an H × W input and kh × kw kernel."))

add('capstone-text', 'Tokenize, truncate, pad and mask a batch',
    PY+'library/stdtypes.html#str.split', [
    "Before text reaches a model, each sentence is normalized (here lowercased), split into tokens, mapped to ids with an unknown fallback, truncated to a maximum length and padded to a common length.",
    "The attention mask marks real tokens with 1 and padding with 0, so attention and losses can ignore the padding. Truncation must happen before padding, or long sentences produce rows longer than the batch length.",
    "Keep this preprocessing in one function used for training and serving, and test it with empty, short, exact-length and overlong inputs. The capstone's attention model consumes exactly these ids and masks.",
    "The transfer encodes a batch with truncation, padding and masks."
    ],
    ("Why must truncation happen before padding?",
     "Otherwise overlong rows stay longer than the batch length and the batch is not rectangular.",
     ["Padding removes tokens.", "Truncation only works on padded rows.", "The order does not matter."],
     "Truncate to the maximum length, then pad shorter rows."),
    task("Transfer: encode a text batch",
         "data is [sentences, max_length]. Lowercase and split each sentence, map tokens with vocabulary {<pad>: 0, <unk>: 1, good: 2, bad: 3}, truncate to max_length, pad with 0 and build masks. Return [padded ids, masks].",
         "vocab = {'<pad>': 0, '<unk>': 1, 'good': 2, 'bad': 3}\nsentences, length = data\nids = [[vocab.get(t, 1) for t in s.lower().split()][:length] for s in sentences]\npadded = [row + [0] * (length - len(row)) for row in ids]\nmask = [[int(t != 0) for t in row] for row in padded]\nresult = [padded, mask]",
         [([['Good movie','bad bad bad bad'],3],[[[2,1,0],[3,3,3]],[[1,1,0],[1,1,1]]]),([[''],2],[[[0,0]],[[0,0]]]),([['GOOD'],1],[[[2]],[[1]]])],
         ("[:length]",""),
         ["Unknown words map to id 1.", "Truncate before padding.", "The mask is 1 for real tokens."],
         "'Good movie' becomes [2, 1] padded to [2, 1, 0], and the four-word sentence is truncated to three tokens. Without truncation the second row would have four entries.",
         [[[[2,1,0],[3,3,3,3]],[[1,1,0],[1,1,1,1]]],[[[2,0,0],[3,3,3]],[[1,0,0],[1,1,1]]],[[[2,1,0],[3,3,3]],[[1,1,1],[1,1,1]]]]),
    ("What does an attention mask mark?", "Real tokens with 1 and padding with 0."))

add('capstone-forecast', 'statistics.fmean: rolling-origin evaluation without look-ahead',
    PY+'library/statistics.html#statistics.fmean', [
    "Rolling-origin evaluation simulates deployment: for each forecast origin t, fit or compute the forecast using only observations before t, predict t and record the error. Averaging over origins gives a realistic estimate of forecasting skill.",
    "Including the value being forecast in the history, an off-by-one in the slice, makes errors shrink dramatically and the model look excellent. Every slice should be series[:t], never series[:t + 1].",
    "Compare candidates with simple baselines such as the last value and the historical mean. On trending data, the last value usually wins; a model that cannot beat it has not learned anything useful.",
    "The transfer evaluates last-value and historical-mean forecasts with rolling origins."
    ],
    ("Forecasting time t, which observations may the history include?",
     "Only those before t: series[:t].",
     ["Everything up to and including t.", "The whole series.", "Only observation t."],
     "Including t leaks the answer into the forecast."),
    task("Transfer: rolling-origin baselines",
         "data is [series, first origin]. For each origin t, forecast with the last observed value and with the mean of series[:t]. Return [number of origins, mean absolute error of each baseline rounded to 4 places].",
         "series, start = data\nnaive_errors, mean_errors = [], []\nfor t in range(start, len(series)):\n    history = series[:t]\n    naive_errors.append(abs(series[t] - history[-1]))\n    mean_errors.append(abs(series[t] - statistics.fmean(history)))\nresult = [len(naive_errors), round(statistics.fmean(naive_errors), 4), round(statistics.fmean(mean_errors), 4)]",
         [([[1,2,3,4,5],2],[3,1.0,2.0]),([[5,5,5,5],1],[3,0.0,0.0]),([[0,10,0,10],2],[2,10.0,5.8333])],
         ("history = series[:t]","history = series[:t + 1]"),
         ["The history excludes the value being forecast.", "The last value often wins on trends.", "Average errors over all origins."],
         "On a steady trend the last value errs by 1 each time while the growing mean lags by 1.5, 2 and 2.5. On an alternating series the mean does better. Including t in the history makes the last-value forecast perfect, a sure sign of leakage.",
         [[3,0.0,1.5],[3,2.0,1.0],[2,1.0,2.0]],
         "import statistics"),
    ("What is the signature of look-ahead leakage in forecasting evaluation?", "Implausibly small errors, especially a perfect last-value baseline."))

add('capstone-production', 'json: a request handler with explicit status codes',
    PY+'library/json.html#json.loads', [
    "A prediction service must treat every request as untrusted input. Parse the body, validate that it is an object with exactly the expected fields and numeric types, and only then call the model.",
    "Different failures deserve different answers: malformed JSON is a client syntax error (400), a well-formed body with the wrong fields or types is unprocessable (422), and only valid requests get a prediction (200). In Python, bool is a subclass of int, so a type check that accepts int also accepts true unless it excludes bool explicitly.",
    "Return the model version with every prediction so results can be traced to an artifact. The capstone service adds health checks, artifact digests, bounded logging and monitoring around this core.",
    "The transfer handles valid, incomplete, malformed and Boolean-valued requests."
    ],
    ("Why exclude bool explicitly when validating numeric fields in Python?",
     "bool is a subclass of int, so isinstance(True, int) is True.",
     ["Booleans cannot be parsed from JSON.", "Booleans are always strings in JSON.", "There is no need; isinstance rejects them."],
     "Check isinstance(v, (int, float)) and not isinstance(v, bool)."),
    task("Transfer: validate before predicting",
         "data is a list of request bodies. handle(body) returns [400, 'invalid-json'], [422, 'schema-mismatch'], [422, 'non-numeric'] or [200, {version, score}] with score = age·0.1 + income·0.01.",
         "META = {'version': '1.0', 'features': ['age', 'income']}\ndef handle(body):\n    try:\n        payload = json.loads(body)\n    except json.JSONDecodeError:\n        return [400, 'invalid-json']\n    if not isinstance(payload, dict) or set(payload) != set(META['features']):\n        return [422, 'schema-mismatch']\n    if not all(isinstance(payload[k], (int, float)) and not isinstance(payload[k], bool) for k in META['features']):\n        return [422, 'non-numeric']\n    return [200, {'version': META['version'], 'score': payload['age'] * 0.1 + payload['income'] * 0.01}]\nresult = [handle(b) for b in data]",
         [(['{\"age\": 30, \"income\": 100}','{\"age\": 30}','not json','{\"age\": true, \"income\": 1}'],[[200,{'score':4.0,'version':'1.0'}],[422,'schema-mismatch'],[400,'invalid-json'],[422,'non-numeric']]),(['[1, 2]'],[[422,'schema-mismatch']]),(['{\"age\": 0, \"income\": 0}'],[[200,{'score':0.0,'version':'1.0'}]])],
         (" and not isinstance(payload[k], bool)",""),
         ["Parse first; malformed JSON is a 400.", "Require exactly the expected fields.", "bool passes isinstance(x, int)."],
         "The valid request scores 3 + 1 = 4 with the model version; the missing field and the malformed body are rejected with different codes; true is rejected as non-numeric. Without the bool check, true would be scored as 1.",
         [[[200,{'score':4.0,'version':'1.0'}],[200,{'score':3.0,'version':'1.0'}],[400,'invalid-json'],[422,'non-numeric']],[[200,{'score':4.0,'version':'1.0'}],[422,'schema-mismatch'],[422,'invalid-json'],[422,'non-numeric']],[[200,{'score':4.0,'version':'1.0'}],[422,'schema-mismatch'],[400,'invalid-json'],[200,{'score':0.11,'version':'1.0'}]]],
         ""),
    ("Which HTTP-style status fits a well-formed request with the wrong fields?", "422 (unprocessable), distinct from 400 for malformed JSON."))

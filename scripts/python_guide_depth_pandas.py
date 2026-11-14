"""Original Stage 13 pandas foundations depth: pandas 2.3 sections with executed transfer practice."""
from python_guide_depth import add, task

PD = "import pandas as pd"
DOCS = 'https://pandas.pydata.org/pandas-docs/version/2.3/'

add('series-labels', 'Indexing: loc label slices include the end, iloc position slices do not',
    DOCS+'user_guide/indexing.html#different-choices-for-indexing', [
    "A Series pairs values with index labels. .loc selects by label and .iloc by integer position. With an integer index such as [30, 10, 20], s.loc[10] means the label 10, the second element, while s.iloc[0] means the first position.",
    "Slices follow different rules. A label slice s.loc[30:10] includes both endpoints, because labels need not be consecutive integers and 'up to but excluding' a label is rarely what you mean. A position slice s.iloc[0:1] excludes its end, like ordinary Python slicing.",
    "Plain s[...] can mean either labels or positions depending on the index type, and pandas has been tightening that behaviour. Write .loc or .iloc explicitly in data code, especially after filtering or sorting, when labels no longer match positions.",
    "The transfer contrasts label and position access on an unsorted integer index."
    ],
    ("For s with index [30, 10, 20], how many elements does s.loc[30:10] return?",
     "Two: label slices include both endpoints.",
     ["One, because the end label is excluded.", "Zero, because 30 > 10.", "Three, the whole Series."],
     ".loc slices by label in index order and include the end label."),
    task("Transfer: labels versus positions",
         "data is three values; the index is [30, 10, 20]. Return [s.loc[10], s.iloc[0], s.loc[30:10] values, s.iloc[0:1] values].",
         "s = pd.Series(data, index=[30, 10, 20])\nresult = [int(s.loc[10]), int(s.iloc[0]), s.loc[30:10].tolist(), s.iloc[0:1].tolist()]",
         [([1,2,3],[2,1,[1,2],[1]]),([7,8,9],[8,7,[7,8],[7]]),([0,-1,5],[-1,0,[0,-1],[0]])],
         ("s.loc[30:10].tolist()","s.iloc[0:1].tolist()"),
         ["loc uses labels; iloc uses positions.", "Label slices include the end label.", "Position slices exclude the end position."],
         "Label 10 is the second value, while position 0 is the first. The label slice from 30 to 10 includes both labels, but the position slice 0:1 contains one element.",
         [[1,1,[1,2],[1]],[2,1,[1],[1]],[2,2,[1,2],[1,2]]],
         PD),
    ("Do .loc slices include the end label?", "Yes; .loc label slices include both endpoints, unlike .iloc position slices."))

add('frame-columns', 'Indexing basics: Series versus DataFrame selection and select_dtypes',
    DOCS+'user_guide/indexing.html#basics', [
    "frame['x'] returns a Series, one column without its two-dimensional structure. frame[['x']] returns a DataFrame with a single column. Code that later expects .columns or two dimensions needs the list form.",
    "Each column has its own dtype. frame.dtypes lists them, and select_dtypes('number') picks numeric columns, which is how preprocessing code separates numeric features from text. Boolean columns are not included in 'number'.",
    "Text columns in pandas 2.3 default to object dtype unless the string dtype is requested. Check dtypes after loading data instead of assuming them, because a single malformed value can turn a numeric column into object.",
    "The transfer selects columns both ways and identifies numeric features in mixed tables."
    ],
    ("What is the type of frame[['x']]?",
     "A DataFrame with one column.",
     ["A Series.", "A list.", "A NumPy array."],
     "A list of labels keeps the two-dimensional DataFrame structure."),
    task("Transfer: select columns and numeric features",
         "data is a column dictionary. Return [type name of frame['x'], type name of frame[['x']], sorted numeric column names, {column: dtype string}].",
         "frame = pd.DataFrame(data)\nresult = [type(frame['x']).__name__, type(frame[['x']]).__name__, sorted(frame.select_dtypes('number').columns), {c: str(t) for c, t in frame.dtypes.items()}]",
         [({'x':[1,2],'y':[0.5,1.5],'name':['a','b']},['Series','DataFrame',['x','y'],{'name':'object','x':'int64','y':'float64'}]),({'x':[1],'flag':[True]},['Series','DataFrame',['x'],{'flag':'bool','x':'int64'}]),({'x':[1.0,2.0]},['Series','DataFrame',['x'],{'x':'float64'}])],
         ("select_dtypes('number')","select_dtypes('int')"),
         ["A single label gives a Series; a list gives a DataFrame.", "'number' covers integer and float columns.", "Boolean columns are not numeric for select_dtypes."],
         "x and y are numeric while name is text. The Boolean flag is excluded from numeric features. Selecting only integers would drop the float column y.",
         [['DataFrame','DataFrame',['x','y'],{'name':'object','x':'int64','y':'float64'}],['Series','DataFrame',['name','x','y'],{'name':'object','x':'int64','y':'float64'}],['Series','DataFrame',['x'],{'name':'object','x':'int64','y':'float64'}]],
         PD),
    ("How do you select only numeric feature columns?", "frame.select_dtypes('number'), after checking the loaded dtypes."))

add('label-alignment', 'Vectorized operations and label alignment: NaN for missing labels and fill_value',
    DOCS+'user_guide/dsintro.html#vectorized-operations-and-label-alignment-with-series', [
    "Arithmetic between Series aligns on index labels. The result's index is the union of both indexes, and a label present on only one side produces NaN, because there is nothing to combine it with.",
    "left.add(right, fill_value=0) treats a missing label on one side as 0 before adding, so one-sided entries keep their value. Whether 0 is right is a domain decision: it suits counts, not temperatures or prices.",
    "Alignment is usually what you want, but it surprises code ported from NumPy, where position decides pairing. After a merge or filter, check the index before combining Series, and count NaNs created by misalignment.",
    "The transfer adds two partly overlapping Series with and without a fill value."
    ],
    ("Series {'a': 1, 'b': 2} plus Series {'b': 10, 'c': 5}: what is the result at 'a'?",
     "NaN, because 'a' has no partner on the right.",
     ["1, because missing values count as zero.", "11, by position.", "A KeyError."],
     "Arithmetic aligns on labels; unmatched labels produce NaN unless a fill_value is given."),
    task("Transfer: aligned addition with a fill policy",
         "data is [left_dict, right_dict]. Return [sorted labels of left + right, number of NaN results, left.add(right, fill_value=0) sorted by label].",
         "a, b = data\nleft = pd.Series(a, dtype=float)\nright = pd.Series(b, dtype=float)\nplain = left + right\nfilled = left.add(right, fill_value=0)\nresult = [sorted(plain.index), int(plain.isna().sum()), filled.sort_index().tolist()]",
         [([{'a':1,'b':2},{'b':10,'c':5}],[['a','b','c'],2,[1.0,12.0,5.0]]),([{'x':1},{'x':2}],[['x'],0,[3.0]]),([{},{'z':4}],[['z'],1,[4.0]])],
         ("fill_value=0","fill_value=1"),
         ["The result index is the union of both indexes.", "Unmatched labels become NaN in plain addition.", "fill_value substitutes for the missing side only."],
         "Only b exists on both sides, giving 12; a and c are NaN in plain addition and keep their own values with fill_value=0. A fill of 1 would inflate one-sided entries.",
         [[['a','b','c'],0,[1.0,12.0,5.0]],[['b'],2,[12.0]],[['a','b','c'],2,[2.0,12.0,6.0]]],
         PD),
    ("What does Series arithmetic do with labels present on only one side?", "Produces NaN for them unless an operation method is given a fill_value."))

add('missing-data', 'Missing data: fit imputation values on training data only',
    DOCS+'user_guide/missing_data.html#filling-missing-data', [
    "fillna replaces missing values with a chosen value. Filling with the column mean is common, but the mean must come from the training data. Computing it over training and test data together leaks information about the test set into the model.",
    "Treat imputation as a fitted step: learn the fill value on the training split, then apply that same value to validation, test and production data. This is the same discipline scikit-learn pipelines enforce with SimpleImputer.",
    "Count missing values before and after, and keep a record of which rows were imputed, because missingness itself can be informative. Do not fill with zero by default; zero is a real value with meaning.",
    "The transfer fits a mean on training data, applies it to test data and reports how many values were filled."
    ],
    ("Why compute an imputation mean on the training data only?",
     "Using test data leaks information about the evaluation set into preprocessing, biasing the evaluation.",
     ["Because test data never contains missing values.", "Because pandas cannot combine Series.", "It makes no difference to evaluation."],
     "Every fitted preprocessing statistic must come from the training split."),
    task("Transfer: leak-free mean imputation",
         "data is [train, test] lists with None for missing. Fit the fill value as the training mean and apply it to test. Return [fill value rounded to 6 places, filled test values, number of missing test values].",
         "train, test = (pd.Series(x, dtype=float) for x in data)\nfill = train.mean()\nresult = [round(float(fill), 6), test.fillna(fill).round(6).tolist(), int(test.isna().sum())]",
         [([[1,None,3],[None,10]],[2.0,[2.0,10.0],1]),([[4,4],[None]],[4.0,[4.0],1]),([[0,10],[5]],[5.0,[5.0],0])],
         ("fill = train.mean()","fill = pd.concat([train, test]).mean()"),
         ["mean skips missing values by default.", "Fit the statistic on train only.", "Apply the same value to the test split."],
         "The training mean of 1 and 3 is 2, which fills the test gap. Including the test value 10 would shift the fill to about 4.67, leaking test information.",
         [[4.666667,[4.666667,10.0],1],[2.0,[0.0,10.0],1],[2.0,[2.0,10.0],0]],
         PD),
    ("Which split provides fitted preprocessing statistics?", "The training split only; apply them unchanged to validation, test and production data."))

add('nullable-integers', 'Nullable integer data type: Int64 keeps integers exact alongside NA',
    DOCS+'user_guide/integer_na.html#nullable-integer-data-type', [
    "A NumPy-backed int64 column cannot hold a missing value, so pandas converts integers with None to float64 and uses NaN. That changes the dtype and can lose precision: float64 represents integers exactly only up to 2**53.",
    "The nullable Int64 extension dtype stores integers plus a separate mask of missing positions, shown as <NA>. Values stay exact integers, and reductions such as sum skip missing entries by default.",
    "Converting an Int64 column with missing values to plain int64 raises, because there is no integer to put in the missing slot. Decide the policy explicitly: fill, drop or keep the nullable type through to the output.",
    "The transfer compares default and nullable construction, including a large integer that float64 cannot represent exactly."
    ],
    ("pd.Series([1, None, 3]) is created with default settings. What dtype results?",
     "float64, with NaN for the missing value.",
     ["int64, with None stored directly.", "Int64, the nullable type.", "object, always."],
     "Plain NumPy integers cannot represent missing values, so pandas upcasts to float."),
    task("Transfer: exact integers with missing values",
         "data is a list of integers and None. Return [default dtype, nullable dtype, sum of the Int64 series, 'ok' or 'cannot-convert-NA' for astype('int64')].",
         "plain = pd.Series(data)\nnullable = pd.Series(data, dtype='Int64')\ntry:\n    nullable.astype('int64')\n    converted = 'ok'\nexcept ValueError:\n    converted = 'cannot-convert-NA'\nresult = [str(plain.dtype), str(nullable.dtype), int(nullable.sum()), converted]",
         [([1,None,3],['float64','Int64',4,'cannot-convert-NA']),([1,2],['int64','Int64',3,'ok']),([9007199254740993,None],['float64','Int64',9007199254740993,'cannot-convert-NA'])],
         ("pd.Series(data, dtype='Int64')","pd.Series(data, dtype='float64')"),
         ["Missing values push plain integers to float64.", "Int64 keeps exact integers and skips NA in sums.", "astype('int64') cannot represent NA."],
         "Missing values make the default column float, while Int64 keeps exact integers. 2**53 + 1 survives in Int64 but would round to 2**53 as a float.",
         [['Int64','Int64',4,'cannot-convert-NA'],['float64','Int64',4,'ok'],['float64','float64',4,'cannot-convert-NA']],
         PD),
    ("Why use Int64 instead of float64 for integer IDs with gaps?", "It keeps values exact (no float rounding above 2**53) and represents missing values as <NA>."))

add('string-operations', 'Working with text: normalize, match case-insensitively and keep missing explicit',
    DOCS+'user_guide/text.html#string-methods', [
    "The .str accessor applies string methods elementwise. Chaining str.strip().str.lower() normalizes whitespace and case before comparisons, so ' Cat ' and 'cat' are treated alike.",
    "With the dedicated 'string' dtype, missing values are <NA>, and string methods return <NA> for them. A Boolean predicate such as str.contains then needs na=False (or True) to produce a definite result usable as a filter.",
    "str.contains treats its pattern as a regular expression by default. Pass regex=False for literal text, so characters such as '.' or '+' are not interpreted. Note that substring matching also hits words like 'concat'; use a word-boundary pattern when that matters.",
    "The transfer normalizes text, matches a literal substring and counts missing entries."
    ],
    ("Why pass na=False to str.contains on a string column?",
     "Missing entries otherwise give <NA>, which cannot be used directly as a Boolean filter.",
     ["It removes missing rows from the Series.", "It makes the match case-insensitive.", "It disables regular expressions."],
     "na sets the predicate's value for missing entries."),
    task("Transfer: normalize and match text",
         "data is a list of strings or None. Using dtype 'string', strip and lowercase, test for the literal 'cat' with na=False, and return [normalized values with '<missing>' for NA, matches, missing count].",
         "s = pd.Series(data, dtype='string')\nclean = s.str.strip().str.lower()\nhas_cat = clean.str.contains('cat', regex=False, na=False)\nresult = [clean.fillna('<missing>').tolist(), has_cat.tolist(), int(clean.isna().sum())]",
         [([' Cat ',None,'DOG','concat'],[['cat','<missing>','dog','concat'],[True,False,False,True],1]),([],[[],[],0]),(['CATS'],[['cats'],[True],0])],
         ("s.str.strip().str.lower()","s.str.strip()"),
         ["Normalize before matching.", "na=False gives missing entries a definite False.", "Substring matching also finds 'cat' inside other words."],
         "' Cat ' normalizes to 'cat' and matches; 'concat' also matches as a substring; the missing value stays missing. Without lowercasing, 'Cat' and 'CATS' would not match.",
         [[['Cat','<missing>','DOG','concat'],[False,False,False,True],1],[['cat','<missing>','dog','concat'],[True,True,False,True],1],[['cat','<missing>','dog','concat'],[True,False,False,False],0]],
         PD),
    ("What does str.contains treat its pattern as by default?", "A regular expression; pass regex=False for literal text."))

add('categorical-codes', 'Categorical data: ordered categories, unknown values and comparisons',
    DOCS+'user_guide/categorical.html#sorting-and-order', [
    "A categorical stores each value as an integer code into a fixed list of categories. Values outside the declared categories become missing, with code -1. This is a quick way to detect unexpected labels in a supposedly closed vocabulary.",
    "ordered=True makes the category list an order. Sorting then follows that order rather than alphabetical order, and comparisons such as s >= 'medium' become valid. Unordered categoricals reject such comparisons.",
    "Codes are storage, not measurements. Feeding codes 0, 1, 2 to a model implies equal spacing and an order; that is only reasonable for genuinely ordinal data. For nominal labels, use one-hot encoding instead.",
    "The transfer encodes ordered levels, detects an unknown label, sorts by level and compares against a threshold."
    ],
    ("A value 'huge' is not among the categories ['low', 'medium', 'high']. What is its code?",
     "-1, because it becomes missing.",
     ["3, appended as a new category.", "0, the first category.", "A ValueError is raised."],
     "Undeclared values are treated as missing in a categorical."),
    task("Transfer: ordered levels",
         "data is a list of level names. Build an ordered categorical with levels low < medium < high. Return [codes, values sorted by level without missing, whether each value >= 'medium', missing count].",
         "levels = ['low', 'medium', 'high']\ns = pd.Series(pd.Categorical(data, categories=levels, ordered=True))\nresult = [s.cat.codes.tolist(), s.sort_values().dropna().tolist(), (s >= 'medium').tolist(), int(s.isna().sum())]",
         [(['high','low','huge','medium'],[[2,0,-1,1],['low','medium','high'],[True,False,False,True],1]),([],[[],[],[],0]),(['low'],[[0],['low'],[False],0])],
         ("ordered=True","ordered=False"),
         ["Undeclared values become missing with code -1.", "Ordered categoricals sort by declared order.", "Comparisons need ordered=True."],
         "The codes follow the declared order, 'huge' is missing, sorting uses low < medium < high and the threshold comparison marks high and medium. An unordered categorical would reject the comparison.",
         [[[2,0,3,1],['low','medium','high'],[True,False,True,True],0],[[2,0,-1,1],['high','low','medium'],[True,False,False,True],1],[[1,0,-1,2],['low','medium','high'],[True,False,False,True],1]],
         PD),
    ("What happens to values outside a categorical's categories?", "They become missing (code -1); declare categories to detect unexpected labels."))

add('join-cardinality', 'Merging: left joins, validate= and the _merge indicator',
    DOCS+'user_guide/merging.html#checking-for-duplicate-keys', [
    "A left join keeps every row of the left table and attaches matching columns from the right. With a many-to-one relationship, such as orders to customers, the row count must not change. If the right side has duplicate keys, rows multiply and totals silently inflate.",
    "validate='many_to_one' makes pandas check that the right keys are unique and raise MergeError otherwise. indicator=True adds a _merge column saying whether each row matched ('both') or not ('left_only'), so unmatched keys can be counted and investigated.",
    "Choose the join type from the requirement. An inner join drops unmatched rows, which may silently remove data you meant to keep. Assert the row count after joins in pipelines.",
    "The transfer joins orders to customers, preserves the row count and reports unmatched customers."
    ],
    ("Orders are inner-joined to customers, and one order has an unknown customer ID. What happens to that order?",
     "It is dropped from the result.",
     ["It is kept with missing customer columns.", "The join raises MergeError.", "It is duplicated."],
     "Inner joins keep only matching keys; use a left join with an indicator to keep and report unmatched rows."),
    task("Transfer: a validated left join",
         "data is a list of customer IDs, one per order. Left-join orders to customers 1–3 (regions n, s, n) with validate='many_to_one' and indicator=True. Return [order count, joined count, unmatched count, regions with '?' for missing].",
         "orders = pd.DataFrame({'order': range(len(data)), 'customer': data})\ncustomers = pd.DataFrame({'customer': [1, 2, 3], 'region': ['n', 's', 'n']})\njoined = orders.merge(customers, on='customer', how='left', validate='many_to_one', indicator=True)\nresult = [len(orders), len(joined), int((joined['_merge'] == 'left_only').sum()), joined['region'].fillna('?').tolist()]",
         [([1,1,4,2],[4,4,1,['n','n','?','s']]),([3],[1,1,0,['n']]),([5,5],[2,2,2,['?','?']])],
         ("how='left'","how='inner'"),
         ["A left join keeps every order.", "validate checks the right keys are unique.", "_merge marks unmatched rows as left_only."],
         "All four orders survive, customer 4 is unmatched and reported, and the region list keeps positions. An inner join would drop the unmatched order and hide it.",
         [[4,3,0,['n','n','s']],[4,4,0,['n','n','?','s']],[4,5,1,['n','n','n','?','s']]],
         PD),
    ("What does validate='many_to_one' check?", "That the right-hand join keys are unique, so a left join cannot multiply rows."))

add('row-filter', 'Boolean indexing: isin, between and inclusive bounds',
    DOCS+'user_guide/indexing.html#boolean-indexing', [
    "Filter rows with a Boolean Series built from column conditions. isin tests membership in a list, and between(low, high) tests a range, inclusive at both ends by default. Combine conditions with & and |, parenthesizing each one.",
    "Being explicit about inclusivity avoids boundary errors. between(0, 20) keeps exactly 0 and 20; inclusive='neither' excludes both, and 'left' or 'right' exclude one. Write the requirement down and test the boundaries.",
    "Use .loc[mask, column] to select filtered rows and a column in one step. This avoids chained indexing such as frame[mask][column], which is less clear and was a source of copy warnings before copy-on-write.",
    "The transfer filters by city membership and an inclusive temperature range, with values exactly on the boundaries."
    ],
    ("Does frame['t'].between(0, 20) keep rows where t is exactly 20?",
     "Yes; between is inclusive at both ends by default.",
     ["No; the upper bound is excluded.", "Only if t is an integer.", "No; both bounds are excluded."],
     "Use inclusive='left', 'right' or 'neither' to change the default."),
    task("Transfer: membership and inclusive ranges",
         "data is a list of [city, temp] rows. Keep rows where city is oslo or rome and temp is between 0 and 20 inclusive. Return the matching cities in order.",
         "frame = pd.DataFrame(data, columns=['city', 'temp'])\nmask = frame['city'].isin(['oslo', 'rome']) & frame['temp'].between(0, 20)\nresult = frame.loc[mask, 'city'].tolist()",
         [([['oslo',-5],['rome',20],['lima',10],['oslo',0]],['rome','oslo']),([],[]),([['rome',21]],[])],
         ("frame['temp'].between(0, 20)","frame['temp'].between(0, 20, inclusive='neither')"),
         ["isin tests list membership.", "between includes both bounds by default.", "Combine masks with & and parentheses."],
         "Rome at exactly 20 and Oslo at exactly 0 are kept; Oslo at -5 and Lima are excluded. Excluding both bounds would drop the two boundary rows.",
         [['rome','lima','oslo'],['oslo','rome','oslo'],['oslo']],
         PD),
    ("What is between's default inclusivity?", "Both bounds included; use inclusive= to change it."))

add('deduplicate-records', 'drop_duplicates: keep the latest record by timestamp, not arrival order',
    DOCS+'reference/api/pandas.DataFrame.drop_duplicates.html#pandas.DataFrame.drop_duplicates', [
    "drop_duplicates(subset, keep='last') keeps the last row for each key in the current row order. If records arrive out of order, 'last' means 'arrived last', not 'most recent'. Sort by the key and timestamp first so that position reflects time.",
    "duplicated(subset, keep=False) marks every row whose key appears more than once. Reporting those keys shows how often conflicting records occur, which is useful data-quality evidence before choosing a policy.",
    "Write the policy down: latest by event time, first seen, or reject conflicting records. Each one yields a different training set. Ties in timestamp need a further rule.",
    "The transfer keeps the latest value per ID when records arrive out of order and reports the IDs with conflicts."
    ],
    ("Records for one ID arrive as (ts=5, 'new') then (ts=2, 'old'). What does drop_duplicates('id', keep='last') keep without sorting?",
     "The 'old' record, because it arrived last.",
     ["The 'new' record, because it has the later timestamp.", "Both records.", "Neither record."],
     "keep='last' refers to row order; sort by timestamp first to keep the most recent."),
    task("Transfer: latest record by event time",
         "data is a list of [id, ts, value] rows in arrival order. Keep the record with the largest ts per id. Return [[id, value] pairs sorted by id, sorted ids that had duplicates].",
         "frame = pd.DataFrame(data, columns=['id', 'ts', 'value'])\nlatest = frame.sort_values(['id', 'ts']).drop_duplicates('id', keep='last')\nconflicts = sorted(frame.loc[frame.duplicated('id', keep=False), 'id'].unique().tolist())\nresult = [[list(pair) for pair in zip(latest['id'].tolist(), latest['value'].tolist())], conflicts]",
         [([[1,5,'new'],[1,2,'old'],[2,1,'x']],[[[1,'new'],[2,'x']],[1]]),([],[[],[]]),([[3,1,'a']],[[[3,'a']],[]])],
         ("frame.sort_values(['id', 'ts'])","frame"),
         ["Sort by key and timestamp before deduplicating.", "keep='last' then keeps the most recent row per key.", "duplicated(keep=False) flags every member of a duplicate group."],
         "After sorting, ID 1's latest record is 'new' at ts 5, and ID 1 is reported as a conflict. Without sorting, the arrival-order last row 'old' would win.",
         [[[[1,'old'],[2,'x']],[1]],[[[1,'new'],[2,'x']],[]],[[[1,'new'],[1,'old'],[2,'x']],[1]]],
         PD),
    ("What does keep='last' mean in drop_duplicates?", "The last row in the current order, so sort by timestamp first when you mean most recent."))

add('csv-roundtrip', 'IO tools: CSV loses dtypes; specify dtype= and parse_dates=',
    DOCS+'user_guide/io.html#specifying-column-data-types', [
    "CSV stores text without types. read_csv infers types, and inference can change data: ZIP codes such as 02139 become the integer 2139, losing the leading zero, and dates stay as text strings.",
    "Pass dtype={'zip': 'string'} for identifiers that look numeric but are labels, and parse_dates=['day'] for date columns. Declaring the schema at read time keeps it consistent across files and machines.",
    "Write index=False unless the index carries meaning, or the next read will add an unnamed column. For data that must preserve dtypes exactly between pandas runs, prefer a typed format such as Parquet, and keep CSV for interchange.",
    "The transfer writes identifiers and dates to CSV and reads them back naively and with an explicit schema."
    ],
    ("A CSV column contains '02139'. What does read_csv produce by default?",
     "The integer 2139; the leading zero is lost.",
     ["The string '02139'.", "A float 2139.0 with the zero kept in metadata.", "A parsing error."],
     "Declare identifier columns as strings with dtype=."),
    task("Transfer: preserve identifiers and dates",
         "data is a list of ZIP code strings. Write them with dates 2026-01-01, 2026-01-02, ... to CSV, then read back naively and with dtype={'zip': 'string'} and parse_dates=['day']. Return [naive zips, typed zips, typed day dtype, naive day dtype].",
         "frame = pd.DataFrame({'zip': data, 'day': ['2026-01-0' + str(i + 1) for i in range(len(data))]})\nstream = io.StringIO()\nframe.to_csv(stream, index=False)\nstream.seek(0)\nnaive = pd.read_csv(stream)\nstream.seek(0)\ntyped = pd.read_csv(stream, dtype={'zip': 'string'}, parse_dates=['day'])\nresult = [naive['zip'].tolist(), typed['zip'].tolist(), str(typed['day'].dtype), str(naive['day'].dtype)]",
         [(['02139','10001'],[[2139,10001],['02139','10001'],'datetime64[ns]','object']),(['00501'],[[501],['00501'],'datetime64[ns]','object']),(['90210','00000','12345'],[[90210,0,12345],['90210','00000','12345'],'datetime64[ns]','object'])],
         ("dtype={'zip': 'string'}","dtype={'zip': 'int64'}"),
         ["read_csv infers numeric types for digit strings.", "dtype= declares identifiers as strings.", "parse_dates converts date columns."],
         "The naive read turns 02139 into 2139 and keeps dates as text. Declaring the schema preserves the ZIP codes and parses the dates. Declaring zip as int64 reproduces the loss.",
         [[['02139','10001'],['02139','10001'],'datetime64[ns]','object'],[[2139,10001],[2139,10001],'datetime64[ns]','object'],[[2139,10001],['02139','10001'],'object','object']],
         PD+"\nimport io"),
    ("How do you keep leading zeros in an ID column from CSV?", "Read it with dtype={'col': 'string'} (or str)."))

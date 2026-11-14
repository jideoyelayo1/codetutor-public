"""Original Stage 14 pandas advanced depth: pandas 2.3 sections with executed transfer practice."""
from python_guide_depth import add, task

PD = "import pandas as pd"
DOCS = 'https://pandas.pydata.org/pandas-docs/version/2.3/'

add('group-aggregate', 'GroupBy: named aggregation and missing group keys',
    DOCS+'user_guide/groupby.html#named-aggregation', [
    "groupby splits rows by key, applies an aggregation to each group and combines one row per group. Named aggregation, agg(n=('score', 'size'), mean=('score', 'mean')), produces clearly named output columns in a single pass.",
    "By default, rows whose group key is missing are dropped from groupby results. A summary built that way silently omits those rows. dropna=False keeps a separate group for the missing key, so totals still add up to the input.",
    "size counts rows, including those with missing values in the aggregated column; count counts only non-missing values. Choose deliberately, and pass sort=True when output order must be deterministic.",
    "The transfer summarizes scores per team, including a row without a team."
    ],
    ("What does groupby do with rows whose key is NaN by default?",
     "Drops them from the result.",
     ["Puts them in a group named 'nan'.", "Raises a KeyError.", "Assigns them to the first group."],
     "Use dropna=False to keep a group for missing keys."),
    task("Transfer: named aggregation with a missing key",
         "data is a list of [team, score] rows, team possibly None. Group with sort=True and dropna=False and compute n (size), mean and best (max). Return [group labels as strings, n, means rounded to 6 places, best].",
         "frame = pd.DataFrame(data, columns=['team', 'score'])\nsummary = frame.groupby('team', sort=True, dropna=False).agg(n=('score', 'size'), mean=('score', 'mean'), best=('score', 'max'))\nresult = [[str(k) for k in summary.index], summary['n'].tolist(), summary['mean'].round(6).tolist(), summary['best'].tolist()]",
         [([['b',3],['a',1],['a',5],[None,7]],[['a','b','nan'],[2,1,1],[3.0,3.0,7.0],[5,3,7]]),([['x',2]],[['x'],[1],[2.0],[2]]),([['a',1],['a',2],['a',3]],[['a'],[3],[2.0],[3]])],
         ("dropna=False","dropna=True"),
         ["Named aggregation maps output names to (column, function).", "dropna=False keeps a group for the missing key.", "size counts rows in each group."],
         "Team a has two scores averaging 3 with best 5, b has one, and the row without a team forms its own group. With dropna=True that row would vanish from the summary.",
         [[['a','b'],[2,1],[3.0,3.0],[5,3]],[['a','b','nan'],[2,1,1],[6.0,3.0,7.0],[5,3,7]],[['a','b','nan'],[1,1,1],[3.0,3.0,7.0],[5,3,7]]],
         PD),
    ("How do you keep rows with a missing group key in a groupby summary?", "Pass dropna=False."))

add('group-transform', 'GroupBy transformation: within-group centring and shares',
    DOCS+'user_guide/groupby.html#transformation', [
    "groupby(...).transform(f) computes a group-level statistic and broadcasts it back to every row of that group. The result has the same length and index as the input, so it can be assigned as a new column.",
    "This is how group-relative features are built: value minus the group mean, value divided by the group total, or a rank within the group. Aggregation would instead return one row per group, which cannot be assigned back without a merge.",
    "Group statistics used as model features must also follow the train/test discipline: compute them from training data, or in a way that does not peek at the target or the future. Within one table, transform keeps rows aligned automatically.",
    "The transfer centres each value on its group mean and computes each value's share of its group total."
    ],
    ("What length does frame.groupby('g')['v'].transform('mean') have?",
     "The same length as the frame, with each row receiving its group's mean.",
     ["One row per group.", "One value in total.", "The number of distinct values."],
     "transform broadcasts group results back to the original rows."),
    task("Transfer: group-relative features",
         "data is a list of [group, value] rows. Add centered = value - group mean and share = value / group total using transform. Return [row count, centered rounded to 6 places, share rounded to 6 places].",
         "frame = pd.DataFrame(data, columns=['group', 'value'])\ngrouped = frame.groupby('group')['value']\nframe['centered'] = frame['value'] - grouped.transform('mean')\nframe['share'] = frame['value'] / grouped.transform('sum')\nresult = [len(frame), frame['centered'].round(6).tolist(), frame['share'].round(6).tolist()]",
         [([['a',1],['b',4],['a',3]],[3,[-1.0,0.0,1.0],[0.25,1.0,0.75]]),([['x',2],['x',2]],[2,[0.0,0.0],[0.5,0.5]]),([['z',5]],[1,[0.0],[1.0]])],
         ("grouped.transform('sum')","frame['value'].sum()"),
         ["transform keeps one value per original row.", "Group a has mean 2 and total 4.", "Divide by the group's total, not the whole column's."],
         "Group a's values 1 and 3 centre to -1 and 1 with shares 0.25 and 0.75; b's single value is its whole group. Dividing by the grand total would mix groups together.",
         [[2,[-1.0,1.0],[0.25,0.75]],[3,[-1.0,0.0,1.0],[0.125,0.5,0.375]],[3,[1.0,0.0,-1.0],[0.25,1.0,0.75]]],
         PD),
    ("When should you use transform instead of agg?", "When the group statistic must be attached to every original row, keeping the input's length and index."))

add('pivot-duplicates', 'Reshaping: pivot_table aggregation, size counts and fill_value',
    DOCS+'user_guide/reshaping.html#pivot-tables', [
    "pivot requires exactly one value per (row, column) cell and raises on duplicates. pivot_table aggregates duplicates with aggfunc, which changes the meaning of the table: a cell becomes a mean, sum or count over several records.",
    "Pair a mean table with a count table (aggfunc='size') so readers can see how many records each cell summarizes. A mean of one record and a mean of a thousand look identical otherwise.",
    "fill_value replaces empty cells, which have no records at all. Filling with 0 is right for counts and often misleading for means; document the choice, or leave such cells missing.",
    "The transfer builds mean and count pivot tables from records with a duplicate cell."
    ],
    ("Two records share the same (row, column) pair. What does pivot do?",
     "Raises ValueError, because a cell would need two values.",
     ["Keeps the first record.", "Averages them.", "Creates a MultiIndex column."],
     "pivot reshapes only; pivot_table aggregates duplicates."),
    task("Transfer: mean and count tables",
         "data is a list of [row, column, value] records. Build pivot_table means and sizes with fill_value=0. Return [column labels, mean values, count values].",
         "frame = pd.DataFrame(data, columns=['row', 'column', 'value'])\nmeans = frame.pivot_table(index='row', columns='column', values='value', aggfunc='mean', fill_value=0)\ncounts = frame.pivot_table(index='row', columns='column', values='value', aggfunc='size', fill_value=0)\nresult = [list(means.columns), means.values.tolist(), counts.values.tolist()]",
         [([['a','x',1],['a','x',3],['b','y',5]],[['x','y'],[[2.0,0.0],[0.0,5.0]],[[2,0],[0,1]]]),([['r','c',4]],[['c'],[[4.0]],[[1]]]),([['a','x',2],['b','x',6]],[['x'],[[2.0],[6.0]],[[1],[1]]])],
         ("aggfunc='mean', fill_value=0","aggfunc='sum', fill_value=0"),
         ["pivot_table aggregates duplicate cells.", "aggfunc='size' counts the records per cell.", "fill_value fills cells with no records."],
         "Cell (a, x) averages 1 and 3 to 2 from two records; (b, y) has one record. Summing instead would report 4 for (a, x).",
         [[['x','y'],[[4.0,0.0],[0.0,5.0]],[[2,0],[0,1]]],[['x','y'],[[2.0,0.0],[0.0,5.0]],[[1,0],[0,1]]],[['a','b'],[[2.0,0.0],[0.0,5.0]],[[2,0],[0,1]]]],
         PD),
    ("Why publish a count table beside a pivot of means?", "To show how many records each mean summarizes; a single record and many look identical otherwise."))

add('melt-long', 'Reshaping: melt to long form and pivot back without loss',
    DOCS+'user_guide/reshaping.html#reshaping-by-melt', [
    "melt turns a wide table, one column per measurement, into a long table with one row per (identifier, measurement) pair. id_vars lists the identifier columns to keep; var_name and value_name name the new columns.",
    "Long form suits grouping, plotting and storing sparse measurements. pivot reverses it when each (identifier, variable) pair is unique. Checking that pivoting a melted table reproduces the original is a cheap test that no identifier was accidentally melted or lost.",
    "After pivot, the column index carries a name (here 'metric'), and the identifier is in the index. reset_index and clearing columns.name restore the original layout for comparison. DataFrame.equals compares values, labels and dtypes.",
    "The transfer melts a wide table, counts the long rows and confirms a lossless round trip."
    ],
    ("A wide table has 2 rows, an id column and measurement columns a and b. How many rows does melt(id_vars=['id']) produce?",
     "4: one per row and measurement.",
     ["2, the original row count.", "6, one per cell including id.", "3, one per column."],
     "Long form has rows × measured columns rows."),
    task("Transfer: lossless melt and pivot",
         "data is a column dictionary with an 'id' column. Melt with var_name='metric', value_name='value', then pivot back. Return [long row count, sorted metric names, whether the round trip equals the original].",
         "wide = pd.DataFrame(data)\nlong = wide.melt(id_vars=['id'], var_name='metric', value_name='value')\nback = long.pivot(index='id', columns='metric', values='value').reset_index()\nback.columns.name = None\nresult = [len(long), sorted(long['metric'].unique().tolist()), back[wide.columns].equals(wide)]",
         [({'id':[1,2],'a':[3,4],'b':[5,6]},[4,['a','b'],True]),({'id':[7],'temp':[20]},[1,['temp'],True]),({'id':[1,2,3],'x':[0,0,1]},[3,['x'],True])],
         ("id_vars=['id']","id_vars=None"),
         ["id_vars keeps identifier columns out of the melt.", "pivot needs unique (id, metric) pairs.", "Clear the column index name before comparing."],
         "Two rows with two measurements give four long rows, and pivoting back reproduces the table. Melting without id_vars turns id into a measurement and the pivot back fails.",
         [[2,['a','b'],True],[4,['a','b','id'],True],[4,['a','b'],False]],
         PD),
    ("How can you test that a reshape lost nothing?", "Reverse it (e.g. melt then pivot) and compare with the original using DataFrame.equals."))

add('multi-index', 'MultiIndex: cross-sections with xs and level-wise aggregation',
    DOCS+'user_guide/advanced.html#cross-section', [
    "A MultiIndex labels each row with a tuple such as (store, day). Selecting a complete key returns one value. s.xs('a', level='store') returns every row for store a, dropping that level, and s.xs(1, level='day') returns every store on day 1.",
    "groupby(level='store') aggregates across the other levels, for example total sales per store over all days. Naming levels makes code readable and robust to level order.",
    "Sort a MultiIndex with sort_index before slicing; many selections are faster and some partial slices require a sorted index. When a hierarchy gets complicated, plain columns plus groupby are often clearer.",
    "The transfer selects by each level and aggregates by store."
    ],
    ("s has a MultiIndex (store, day). What does s.xs(1, level='day') return?",
     "All rows for day 1, one per store, with the day level removed.",
     ["The first row only.", "The row at position 1.", "A KeyError, because 1 is not a store."],
     "xs selects a cross-section on the named level."),
    task("Transfer: cross-sections and level sums",
         "data is a list of [[store, day], sales]; every input has store 'a' and day 1. Return [sales for store 'a' by day, sales on day 1 by store, total sales per store in sorted store order].",
         "index = pd.MultiIndex.from_tuples([tuple(k) for k, _ in data], names=['store', 'day'])\ns = pd.Series([v for _, v in data], index=index).sort_index()\nresult = [s.xs('a', level='store').tolist(), s.xs(1, level='day').tolist(), s.groupby(level='store').sum().tolist()]",
         [([[['a',1],10],[['b',1],5],[['a',2],7]],[[10,7],[10,5],[17,5]]),([[['a',1],2]],[[2],[2],[2]]),([[['a',1],1],[['a',2],2],[['c',1],4]],[[1,2],[1,4],[3,4]])],
         ("groupby(level='store')","groupby(level='day')"),
         ["xs on 'store' drops the store level.", "xs on 'day' returns one row per store.", "groupby(level=...) aggregates over the remaining levels."],
         "Store a sold 10 and 7 on its two days; day 1 had sales of 10 and 5; store totals are 17 and 5. Grouping by day would total per day instead.",
         [[[10,5],[10,7],[17,5]],[[10,7],[10,5],[15,7]],[[17],[10,5],[17,5]]],
         PD),
    ("What does xs(key, level=name) do?", "Selects all rows matching key on that level and drops the level from the result."))

add('rolling-window', 'Windowing: time-based windows and past-only features with shift',
    DOCS+'user_guide/window.html#rolling-window', [
    "rolling(2) uses the last two rows, whatever their timestamps. With irregular timestamps, a time-based window such as rolling('2D') uses all observations in the preceding two days, (t - 2 days, t], which is usually what 'recent history' means.",
    "A rolling statistic at time t includes the value at t. Used as a feature to predict that same value, it leaks the target. shift(1) moves each statistic one step later, so the feature at t uses only earlier observations.",
    "The first rows have no history; decide how to represent that (missing, a default or dropping the rows) and keep it consistent between training and serving. min_periods controls how much history is required before a value is emitted.",
    "The transfer computes a time-based rolling sum and a past-only rolling mean feature on irregular timestamps."
    ],
    ("Why apply shift(1) to a rolling mean used as a feature for predicting the current value?",
     "Without the shift, the window includes the current value, leaking the target into the feature.",
     ["Shift makes the rolling mean smoother.", "Rolling windows require a shift to compute.", "It converts the index to timestamps."],
     "Past-only features must exclude the observation being predicted."),
    task("Transfer: time windows and leakage-free features",
         "data is [timestamps, values]. Index a float Series by the timestamps. Return [rolling('2D').sum(), rolling(2, min_periods=1).mean().shift(1) with missing as -1].",
         "times = pd.to_datetime(data[0])\ns = pd.Series(data[1], index=times, dtype=float)\nby_time = s.rolling('2D').sum()\npast_only = s.rolling(2, min_periods=1).mean().shift(1)\nresult = [by_time.tolist(), past_only.fillna(-1).tolist()]",
         [([['2026-01-01','2026-01-02','2026-01-05'],[1,2,4]],[[1.0,3.0,4.0],[-1.0,1.0,1.5]]),([['2026-03-01'],[5]],[[5.0],[-1.0]]),([['2026-01-01','2026-01-03'],[2,6]],[[2.0,6.0],[-1.0,2.0]])],
         (".shift(1)",""),
         ["A '2D' window covers the previous two days up to and including t.", "A count window ignores gaps in time.", "shift(1) excludes the current value."],
         "The Jan 5 value has no neighbour within two days, so its time-window sum is just 4, while a two-row window would include Jan 2. Without the shift, the feature for each row would include that row's own value.",
         [[[1.0,3.0,6.0],[-1.0,1.0,1.5]],[[1.0,3.0,4.0],[1.0,1.5,3.0]],[[1.0,3.0,4.0],[-1.0,1.5,3.0]]],
         PD),
    ("How do you make a rolling feature past-only?", "Compute the rolling statistic and shift it by one step so the current value is excluded."))

add('resample-time', 'Time series: time zones change which day a timestamp belongs to',
    DOCS+'user_guide/timeseries.html#resampling', [
    "resample('D') groups timestamps into calendar days. A calendar day depends on the time zone: 02:00 UTC on 1 January is still 31 December in New York. Daily totals computed in UTC and in local time can differ.",
    "Store timestamps in UTC with an explicit zone, and convert with tz_convert to the zone whose days the business question uses, such as a store's local trading day. Naive timestamps without a zone leave that choice implicit and error-prone.",
    "Bin edges and labels are part of the definition: resample bins are closed on the left and labelled by their start by default. Daylight-saving transitions make some local days 23 or 25 hours long. State the zone and binning in reports.",
    "The transfer aggregates the same UTC events by UTC day and by New York day."
    ],
    ("An event at 2026-01-01 02:00 UTC is aggregated by New York calendar day. Which day does it fall on?",
     "31 December 2025, because New York is five hours behind UTC in January.",
     ["1 January 2026, the UTC date.", "2 January 2026.", "It is dropped as ambiguous."],
     "Calendar-day bins depend on the time zone used."),
    task("Transfer: daily totals in two time zones",
         "data is [UTC timestamps, values]. Return [daily sums in UTC, New York day labels as MM-DD, daily sums in New York time].",
         "index = pd.DatetimeIndex(data[0], tz='UTC')\ns = pd.Series(data[1], index=index)\nutc_days = s.resample('D').sum()\nlocal = s.tz_convert('America/New_York').resample('D').sum()\nresult = [utc_days.tolist(), [d.strftime('%m-%d') for d in local.index], local.tolist()]",
         [([['2026-01-01T02:00','2026-01-01T20:00','2026-01-02T03:00'],[1,2,4]],[[3,4],['12-31','01-01'],[1,6]]),([['2026-06-01T12:00'],[5]],[[5],['06-01'],[5]]),([['2026-03-01T04:00','2026-03-01T06:00'],[1,1]],[[2],['02-28','03-01'],[1,1]])],
         ("s.tz_convert('America/New_York')","s"),
         ["Daily bins follow the series' time zone.", "tz_convert changes the zone without changing the instant.", "New York is UTC-5 in winter and UTC-4 in summer."],
         "In UTC the events total 3 on 1 January and 4 on 2 January. In New York, the 02:00 UTC event belongs to 31 December and the other two to 1 January. Skipping the conversion reports UTC days as local ones.",
         [[[3,4],['01-01','01-02'],[3,4]],[[1,6],['12-31','01-01'],[1,6]],[[3,4],['12-31','01-01'],[3,4]]],
         PD),
    ("Why convert time zones before daily resampling?", "Calendar days depend on the zone; the same instants fall into different days in UTC and local time."))

add('asof-direction', 'merge_asof: backward matches with a staleness tolerance',
    DOCS+'user_guide/merging.html#merging-asof', [
    "merge_asof matches each left row to the nearest right row by an ordered key, typically time. direction='backward' uses the latest right observation at or before the left time, which is the only choice that avoids using future information.",
    "A backward match can be arbitrarily old. tolerance limits how stale a match may be; beyond it the result is missing. Without a tolerance, a trade could be joined to a price from hours earlier and look perfectly valid.",
    "Both inputs must be sorted by the key, and the key dtypes must match. Use by= to match within groups such as ticker symbols. Report how many rows went unmatched instead of filling them silently.",
    "The transfer matches trades to the latest quote no more than three time units earlier."
    ],
    ("Why is direction='backward' the safe default for joining features to events?",
     "It only uses observations at or before each event, so no future information leaks in.",
     ["It is faster than forward matching.", "It always finds a match.", "It matches the closest value in either direction."],
     "Forward or nearest matches can use data that was not yet available at the event time."),
    task("Transfer: as-of matching with tolerance",
         "data is a sorted list of trade times. Quotes are at t = 0, 5 and 10 with prices 100, 101 and 102. Match each trade backward with tolerance=3 and return prices, using -1 when there is no match.",
         "quotes = pd.DataFrame({'t': [0, 5, 10], 'price': [100, 101, 102]})\ntrades = pd.DataFrame({'t': data})\nmatched = pd.merge_asof(trades, quotes, on='t', direction='backward', tolerance=3)\nresult = matched['price'].fillna(-1).tolist()",
         [([1,6,9,12],[100.0,101.0,-1.0,102.0]),([0],[100.0]),([4,14],[-1.0,-1.0])],
         ("tolerance=3","tolerance=10"),
         ["Backward matching uses the last quote at or before the trade.", "tolerance limits how old that quote may be.", "Unmatched rows become missing."],
         "Trade 9's latest quote is at 5, four units earlier, which exceeds the tolerance. A larger tolerance would attach that stale price.",
         [[100.0,101.0,101.0,102.0],[100.0,101.0,102.0,102.0],[100.0,100.0,-1.0,102.0]],
         PD),
    ("What does tolerance= add to merge_asof?", "A maximum allowed distance; matches staler than that become missing."))

add('copy-on-write', 'Copy-on-Write: derived frames are independent; modify the parent with .loc',
    DOCS+'user_guide/copy_on_write.html#copy-on-write-cow', [
    "Under Copy-on-Write, any DataFrame or Series derived from another behaves as an independent copy. Modifying a filtered subset never changes the parent; pandas copies lazily, only when one side is written.",
    "This removes the old ambiguity of chained assignment, where frame[mask]['col'] = value sometimes worked and sometimes silently did nothing. To change the original frame, assign through it directly: frame.loc[mask, 'col'] = value.",
    "Copy-on-Write is optional in pandas 2.3 and becomes the default in pandas 3.0. Pin the option in code that depends on it, and test that modifications land in the frame you intend.",
    "The transfer modifies a filtered subset and the parent frame, and checks which changes are visible where."
    ],
    ("Under Copy-on-Write, subset = frame[frame.x > 1]; subset.loc[:, 'y'] = 1. Does frame change?",
     "No; subset is independent, so only subset changes.",
     ["Yes, subset is a view of frame.", "Yes, but only for the first row.", "It raises SettingWithCopyError."],
     "Modify the parent directly with frame.loc[mask, col] = value."),
    task("Transfer: where modifications land",
         "data is a list of x values; y starts at 0. With copy-on-write enabled, set y = 1 in a filtered subset (x > 1), then set y = 2 in the parent where x > 2 via .loc. Return [parent y, subset y].",
         "with pd.option_context('mode.copy_on_write', True):\n    frame = pd.DataFrame({'x': data, 'y': [0] * len(data)})\n    subset = frame[frame['x'] > 1]\n    subset.loc[:, 'y'] = 1\n    frame.loc[frame['x'] > 2, 'y'] = 2\n    result = [frame['y'].tolist(), subset['y'].tolist()]",
         [([1,2,3],[[0,0,2],[1,1]]),([5],[[2],[1]]),([0],[[0],[]])],
         ("frame.loc[frame['x'] > 2, 'y'] = 2","subset.loc[subset['x'] > 2, 'y'] = 2"),
         ["The filtered subset is independent of the parent.", "Assign through the parent with .loc to change it.", "Later parent changes do not reach the earlier subset."],
         "The subset's change stays in the subset, and the parent's .loc assignment changes only the parent. Writing to the subset instead would leave the parent untouched.",
         [[[0,1,2],[1,1]],[[0,0,2],[1,2]],[[0,1,1],[1,1]]],
         PD),
    ("How do you modify rows of the original DataFrame under Copy-on-Write?", "Assign through it with frame.loc[mask, column] = value, never through a derived subset."))

add('sparse-storage', 'Sparse data: the fill value decides what is stored',
    DOCS+'user_guide/sparse.html#sparsearray', [
    "A SparseArray stores only the entries that differ from its fill_value, plus their positions. For mostly-zero data with fill_value=0, that saves memory in proportion to the density, the fraction of stored entries.",
    "The default fill value for floats is NaN, not 0. A float array of zeros with the default fill stores every zero explicitly and saves nothing. Choose the fill value to match the data's most common value.",
    "Sparse storage helps only when density is low; many operations convert back to dense, which can use more memory than the original. to_dense() must reproduce the original values exactly, which is a simple correctness check.",
    "The transfer compares stored-entry counts for zero and default fill values and verifies the dense round trip."
    ],
    ("A float SparseArray is built from [0, 0, 0, 5] with the default fill value. How many entries are stored?",
     "4, because the default float fill is NaN, so zeros are stored explicitly.",
     ["1, only the 5.", "0, because the array is sparse.", "3, the zeros."],
     "Set fill_value=0 to store only the non-zero entries."),
    task("Transfer: choose the fill value",
         "data is a list of numbers. Build SparseArray with fill_value=0.0 and with the default fill. Return [stored points with fill 0, density with fill 0 rounded to 6 places, stored points with default fill, whether to_dense() round-trips].",
         "dense = np.asarray(data, dtype=float)\nzero_fill = pd.arrays.SparseArray(dense, fill_value=0.0)\nnan_fill = pd.arrays.SparseArray(dense)\nresult = [zero_fill.sp_index.npoints, round(float(zero_fill.density), 6), nan_fill.sp_index.npoints, zero_fill.to_dense().tolist() == dense.tolist()]",
         [([0,0,0,5],[1,0.25,4,True]),([0,0],[0,0.0,2,True]),([1,2],[2,1.0,2,True])],
         ("fill_value=0.0","fill_value=5.0"),
         ["Only entries different from the fill value are stored.", "Default float fill is NaN.", "Density is stored entries divided by length."],
         "With fill 0 only the 5 is stored, density 0.25; with the default NaN fill all four values are stored. A fill of 5 would store the three zeros instead.",
         [[4,1.0,4,True],[1,0.25,1,True],[3,0.75,4,True]],
         PD+"\nimport numpy as np"),
    ("What is the default fill value of a float SparseArray?", "NaN, so zeros are stored explicitly unless fill_value=0 is given."))

add('chunked-aggregation', 'IO tools: chunked reading with combinable sufficient statistics',
    DOCS+'user_guide/io.html#iterating-through-files-chunk-by-chunk', [
    "read_csv(..., chunksize=n) returns an iterator of DataFrames, so a file larger than memory can be processed piece by piece. Only statistics that can be combined across chunks give correct overall results.",
    "Counts, sums and sums of squares combine by addition. From them, the mean is sum / count and the population variance is E[x²] - mean². Averaging per-chunk means is wrong when chunks have different sizes, which the last chunk usually does.",
    "The sum-of-squares formula can lose precision when values are large relative to their spread. Welford's algorithm, or combining per-chunk means and variances with counts, is more stable; use it for production data. Compare against a full computation on a sample in tests.",
    "The transfer streams a CSV in chunks, combines sufficient statistics and checks them against the full computation."
    ],
    ("Chunks [1, 3] and [8] have means 2 and 8. Why is (2 + 8) / 2 = 5 not the overall mean?",
     "The chunks have different sizes; the overall mean is the total 12 divided by the count 3, which is 4.",
     ["Because means can never be combined.", "It is correct; chunk means can be averaged.", "Because the last chunk should be discarded."],
     "Combine counts and sums, not unweighted chunk means."),
    task("Transfer: streaming mean and variance",
         "data is [values, chunksize]. Read 'value' from CSV text in chunks, accumulating count, sum and sum of squares. Return [count, mean, population variance from the sums, full pandas var(ddof=0)], all rounded to 6 places.",
         "stream = io.StringIO('value\\n' + '\\n'.join(str(v) for v in data[0]))\ncount = total = squares = 0\nfor chunk in pd.read_csv(stream, chunksize=data[1]):\n    values = chunk['value']\n    count += len(values)\n    total += values.sum()\n    squares += (values ** 2).sum()\nmean = total / count\nvariance = squares / count - mean ** 2\nfull = pd.Series(data[0], dtype=float)\nresult = [count, round(float(mean), 6), round(float(variance), 6), round(float(full.var(ddof=0)), 6)]",
         [([[1,2,3,4,10],2],[5,4.0,10.0,10.0]),([[5],3],[1,5.0,0.0,0.0]),([[2,4,6],1],[3,4.0,2.666667,2.666667])],
         ("total += values.sum()","total += values.mean()"),
         ["Accumulate count, sum and sum of squares.", "Mean is total sum divided by total count.", "Variance is E[x²] minus the squared mean."],
         "The five values sum to 20 with squares summing to 130, so the mean is 4 and the variance 26 - 16 = 10, matching pandas. Adding chunk means instead of sums gives a wrong total.",
         [[5,4.6,10.0,10.0],[5,4.0,26.0,10.0],[3,4.0,10.0,10.0]],
         PD+"\nimport io"),
    ("Which statistics combine across chunks by simple addition?", "Counts, sums and sums of squares (or per-chunk means/variances weighted by counts)."))

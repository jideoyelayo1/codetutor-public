"""Original Stage 23 production-ML depth: schemas, artifacts, parity, monitoring and rollout gates with scikit-learn 1.7."""
from python_guide_depth import add, task

NP = "import numpy as np"
SK = 'https://scikit-learn.org/1.7/'

add('schema-boundary', 'feature_names_in_: reorder to the training schema, reject missing fields',
    SK+'glossary.html#term-feature_names_in_', [
    "An estimator fitted on a DataFrame records its column names in feature_names_in_. At prediction time scikit-learn checks that a DataFrame has the same names in the same order, and raises ValueError otherwise.",
    "Requests arrive as dictionaries whose key order is arbitrary. Reindexing each request to feature_names_in_ puts the columns in training order; a missing field becomes NaN, which this model rejects. That turns schema problems into explicit errors at the service boundary instead of silent wrong predictions.",
    "Validate types and ranges too, and decide whether extra fields are ignored or rejected. Log rejected requests with a reason, without logging sensitive values.",
    "The transfer serves records with reordered and missing fields through a schema-aligned predictor."
    ],
    ("A model was fitted on columns ['age', 'income']. A request DataFrame has ['income', 'age']. What happens without reordering?",
     "scikit-learn raises ValueError because the feature names are not in the fitted order.",
     ["It silently swaps the columns back.", "It predicts with the columns swapped.", "It ignores column names entirely."],
     "Reindex requests to feature_names_in_ before predicting."),
    task("Transfer: a schema-aligned predictor",
         "data is a list of request dictionaries. A LinearRegression is fitted on columns age and income. Reindex each request to feature_names_in_ and predict, returning 'schema-rejected' on ValueError. Return [the fitted feature names, predictions rounded to 4 places].",
         "train = pd.DataFrame({'age': [20, 30, 40], 'income': [1.0, 3.0, 2.0]})\nmodel = LinearRegression().fit(train, [1, 2, 3])\ndef predict(record):\n    frame = pd.DataFrame([record]).reindex(columns=model.feature_names_in_)\n    try:\n        return round(float(model.predict(frame)[0]), 4)\n    except ValueError:\n        return 'schema-rejected'\nresult = [list(model.feature_names_in_), [predict(r) for r in data]]",
         [([{'age':30,'income':3.0},{'income':3.0,'age':30},{'age':25}],[['age','income'],[2.0,2.0,'schema-rejected']]),([{'age':20,'income':1.0}],[['age','income'],[1.0]]),([{'income':2.0}],[['age','income'],['schema-rejected']])],
         ("pd.DataFrame([record]).reindex(columns=model.feature_names_in_)","pd.DataFrame([record])"),
         ["feature_names_in_ records the training column order.", "reindex puts request fields in that order.", "A missing field becomes NaN and is rejected."],
         'The training row (30, 3.0) predicts 2 whichever order its keys arrive in, because reindexing restores the fitted column order; the record without income is rejected. Without reindexing, scikit-learn rejects the reordered record too.',
         [[['age','income'],[2.0,'schema-rejected','schema-rejected']],[['income','age'],[2.0,2.0,'schema-rejected']],[['age','income'],[2.0,2.0,2.0]]],
         NP+"\nimport pandas as pd\nfrom sklearn.linear_model import LinearRegression"),
    ("How should a service align request fields with a model?", "Reindex to the fitted feature_names_in_ and reject requests with missing fields."))

add('feature-order', 'n_features_in_: arrays carry no names, so order is the contract',
    SK+'glossary.html#term-n_features_in_', [
    "A model fitted on a NumPy array knows only how many features it expects, n_features_in_, not what they mean. Column order is the entire contract: a request vector with two features swapped is accepted and gives a wrong prediction.",
    "Building the vector from a dictionary with list(record.values()) depends on insertion order, which varies between clients. Store the training schema, an ordered list of names, with the model and build every vector from it.",
    "Prefer fitting on DataFrames so scikit-learn checks names for you, and test the serving path with a request whose keys are deliberately out of order.",
    "The transfer predicts the same record built in schema order and in arbitrary insertion order."
    ],
    ("A model fitted on a NumPy array receives features in the wrong order. What happens?",
     "It predicts without error, but the prediction is wrong.",
     ["It raises a ValueError.", "It reorders them automatically.", "It returns NaN."],
     "Arrays carry no names; the stored schema must define the order."),
    task("Transfer: schema order versus insertion order",
         "data is a record dictionary. A LinearRegression is fitted on arrays with columns [age, income]. Return [prediction from a vector built in schema order, prediction from list(record.values())], rounded to 4 places.",
         "schema = ['age', 'income']\nmodel = LinearRegression().fit(np.array([[20, 1], [30, 5], [40, 2]]), [1, 2, 3])\nrecord = data\nordered = np.array([[record[name] for name in schema]])\ninsertion = np.array([list(record.values())])\nresult = [round(float(model.predict(ordered)[0]), 4), round(float(model.predict(insertion)[0]), 4)]",
         [({'income':5,'age':30},[2.0,-0.5]),({'age':30,'income':5},[2.0,2.0]),({'income':1,'age':20},[1.0,-0.9])],
         ("[record[name] for name in schema]","list(record.values())"),
         ["Build vectors from the stored schema.", "Dictionary insertion order is not a contract.", "Swapped features are accepted silently."],
         'Built in schema order, the training row (30, 5) predicts 2. The same record with income first is fed as (5, 30) and silently predicts -0.5. When keys already happen to be in schema order, both paths agree, which is why the bug survives casual testing.',
         [[-0.5,2.0],[2.0,2.0],[-0.5,-0.5]],
         NP+"\nfrom sklearn.linear_model import LinearRegression"),
    ("Why store a feature schema with an array-trained model?", "The model only knows the feature count; the schema defines which value goes in which position."))

add('artifact-integrity', 'Model persistence: verify a digest before unpickling',
    SK+'model_persistence.html#security-maintainability-limitations', [
    "scikit-learn models are commonly saved with pickle or joblib. Unpickling can execute arbitrary code, so never load an artifact from an untrusted source, and verify that a trusted artifact has not changed before loading it.",
    "Record a SHA-256 digest of the artifact bytes when it is created, store it in trusted metadata and compare before loading. Any change, even a single byte, produces a different digest, and the load is refused.",
    "A matching digest proves the bytes are unchanged, not that they are safe or compatible. Also record the library versions used to save the model, and consider skops or ONNX when artifacts cross trust boundaries.",
    "The transfer saves a model, records its digest and loads the original and a tampered copy."
    ],
    ("What does a matching SHA-256 digest prove about a model artifact?",
     "That its bytes are identical to the recorded artifact, not that the artifact is safe.",
     ["That it was created by scikit-learn.", "That it contains no malicious code.", "That it is compatible with the installed version."],
     "Integrity checks detect changes; trust and compatibility need separate checks."),
    task("Transfer: verified loading",
         "data is an input value. Fit LinearRegression on y = 2x, pickle it and record the digest. load(candidate) refuses bytes whose digest differs, else predicts data. Return [load of the original, load of the original plus one extra byte].",
         "model = LinearRegression().fit([[0], [1]], [0, 2])\nblob = pickle.dumps(model)\nexpected = hashlib.sha256(blob).hexdigest()\ndef load(candidate):\n    if hashlib.sha256(candidate).hexdigest() != expected:\n        return 'digest-mismatch'\n    return round(float(pickle.loads(candidate).predict([[data]])[0]), 4)\nresult = [load(blob), load(blob + b' ')]",
         [(3,[6.0,'digest-mismatch']),(0,[0.0,'digest-mismatch']),(-1.5,[-3.0,'digest-mismatch'])],
         ("if hashlib.sha256(candidate).hexdigest() != expected:","if False:"),
         ["Record the digest when the artifact is created.", "Compare before unpickling.", "Any byte change alters the digest."],
         "The original artifact loads and predicts 2x. One appended byte changes the digest and the load is refused before unpickling. Skipping the check would unpickle modified bytes.",
         [[6.0,6.0],['digest-mismatch','digest-mismatch'],[3.0,'digest-mismatch']],
         "import hashlib, pickle\nfrom sklearn.linear_model import LinearRegression"),
    ("Why verify an artifact digest before unpickling?", "Unpickling can run code; verifying first ensures the bytes are exactly the trusted artifact."))

add('environment-contract', 'Model persistence: refuse loads across incompatible library versions',
    SK+'model_persistence.html#summarizing-the-key-points', [
    "scikit-learn does not guarantee that a model pickled with one version loads or behaves the same in another. Save the library versions with every artifact and check them before loading.",
    "Compare versions numerically, by major and minor components. String comparison misorders versions such as 1.10 and 1.1: '1.10.0'[:3] is '1.1'. A minor-version mismatch is a reason to refuse the load or retrain, not to hope.",
    "Pin the serving environment to the training versions and record the actual installed versions in deployment receipts. This guide's tests run on its pinned scikit-learn 1.7.2.",
    "The transfer checks saved versus running versions, including a case where string slicing gives the wrong answer."
    ],
    ("Why compare '1.1.0' and '1.10.0' numerically rather than by string prefix?",
     "Their three-character prefixes are both '1.1', hiding that the minor versions are 1 and 10.",
     ["String comparison is always correct for versions.", "They are the same version.", "Python cannot parse version strings."],
     "Parse versions into integer components before comparing."),
    task("Transfer: version compatibility gate",
         "data is [saved version, running version]. Compare (major, minor) as integers and return ['compatible' or 'refuse-load', whether the installed scikit-learn is 1.7].",
         "saved, running = data\ndef minor(v):\n    return tuple(int(p) for p in v.split('.')[:2])\nresult = ['compatible' if minor(saved) == minor(running) else 'refuse-load', sklearn.__version__.split('.')[:2] == ['1', '7']]",
         [(['1.7.2','1.7.0'],['compatible',True]),(['1.6.1','1.7.2'],['refuse-load',True]),(['1.1.0','1.10.0'],['refuse-load',True])],
         ("minor(saved) == minor(running)","saved[:3] == running[:3]"),
         ["Compare major and minor as integers.", "Patch releases within a minor version are treated as compatible here.", "String prefixes misorder two-digit components."],
         "1.7.2 and 1.7.0 share a minor version; 1.6 and 1.7 do not; 1.1 and 1.10 differ although their string prefixes match. The guide's pinned environment is scikit-learn 1.7.",
         [['refuse-load',True],['compatible',False],['refuse-load',False]],
         "import sklearn"),
    ("What should a model artifact record about its environment?", "The exact library versions used to train and save it, checked before loading."))

add('batch-online-parity', 'Pipelines: one fitted object for batch and online prediction',
    SK+'modules/compose.html#pipeline-chaining-estimators', [
    "Training/serving skew happens when the online service computes features differently from the batch training code. A fitted Pipeline avoids it by packaging preprocessing and the model as one object used by both paths.",
    "A common skew bug calls only the final estimator online, skipping the scaler or encoder. The service still returns numbers, but they are computed on unscaled inputs and do not match batch predictions.",
    "Test parity directly: run the same records through the batch and online code paths and assert the predictions match. Run this test whenever either path changes.",
    "The transfer compares batch predictions with per-record online predictions from the same pipeline."
    ],
    ("Online code calls pipeline[-1].predict(x) instead of pipeline.predict(x). What goes wrong?",
     "Preprocessing steps are skipped, so the model receives untransformed features.",
     ["Nothing; the last step contains the whole pipeline.", "Predictions become faster but identical.", "The pipeline refits itself."],
     "Always call the full pipeline in every serving path."),
    task("Transfer: batch/online parity",
         "data is a list of input values. A StandardScaler + LinearRegression pipeline is fitted on x = 0, 10, 20 with y = 0, 1, 2. Return [batch predictions rounded to 4 places, whether per-record online predictions match].",
         "x = np.array([[0.0], [10.0], [20.0]])\nmodel = make_pipeline(StandardScaler(), LinearRegression()).fit(x, [0, 1, 2])\nbatch = model.predict(np.array([[v] for v in data]))\nonline = [model.predict(np.array([[v]]))[0] for v in data]\nresult = [[round(float(b), 4) for b in batch], bool(np.allclose(batch, online))]",
         [([5,15],[[0.5,1.5],True]),([0],[[0.0],True]),([20,30],[[2.0,3.0],True])],
         ("online = [model.predict(np.array([[v]]))[0] for v in data]","online = [model[-1].predict(np.array([[v]]))[0] for v in data]"),
         ["Use the same fitted pipeline in both paths.", "Calling only the final step skips scaling.", "Assert parity in a test."],
         "Both paths use the full pipeline, so 5 and 15 predict 0.5 and 1.5 either way. Calling only the regression step feeds raw values to a model trained on standardized ones.",
         [[[0.5,1.5],False],[[5.0,15.0],True],[[1.5,0.5],True]],
         NP+"\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LinearRegression"),
    ("How do you prevent training/serving skew in feature computation?", "Serve the same fitted Pipeline used for evaluation, and test batch/online parity."))

add('drift-statistics', 'Population stability index on reference-quantile bins',
    SK+'modules/preprocessing.html#discretization', [
    "Monitoring compares live feature distributions with a reference, usually the training data. The population stability index (PSI) bins values, here by the reference's quartiles, and sums (current - reference) · ln(current / reference) over the bins.",
    "Bin edges must come from the reference, not the current data; otherwise every current sample looks evenly spread and drift disappears. Clip empty-bin proportions to a small value before taking logarithms.",
    "A common rule of thumb treats PSI above 0.2 as significant drift, but thresholds should be validated per feature. Drift is a signal to investigate, not proof that model accuracy dropped; pair it with delayed-label performance metrics.",
    "The transfer computes PSI for unchanged, shifted and heavily shifted data."
    ],
    ("Why must PSI bin edges come from the reference distribution?",
     "Bins from the current data would spread current values evenly and hide the shift.",
     ["Reference data has fewer values.", "Quantiles cannot be computed on current data.", "It makes PSI negative."],
     "Fix the bins on the reference, then compare proportions."),
    task("Transfer: compute PSI",
         "data is [reference values, current values]. Bin by the reference's quartiles (open-ended outer bins), clip proportions at 1e-6 and compute PSI. Return [PSI rounded to 4 places, PSI > 0.2].",
         "reference, current = (np.asarray(v, dtype=float) for v in data)\nedges = np.quantile(reference, [0, 0.25, 0.5, 0.75, 1.0])\nedges[0], edges[-1] = -np.inf, np.inf\nref = np.histogram(reference, edges)[0] / len(reference)\ncur = np.histogram(current, edges)[0] / len(current)\nref, cur = np.clip(ref, 1e-6, None), np.clip(cur, 1e-6, None)\npsi = float(np.sum((cur - ref) * np.log(cur / ref)))\nresult = [round(psi, 4), psi > 0.2]",
         [([list(range(8)),list(range(8))],[0.0,False]),([list(range(8)),[0,0,0,0,1,1,1,1]],[10.3616,True]),([list(range(8)),[20]*8],[10.3616,True])],
         ("np.quantile(reference,","np.quantile(current,"),
         ["Bin edges come from the reference quartiles.", "Clip empty bins before taking logarithms.", "PSI sums (cur - ref) · ln(cur / ref)."],
         'Identical data gives PSI 0. When every current value falls into a single reference bin, the other three bins are empty and PSI is about 10, far above 0.2. Building bins from the current data would measure a different, smaller number.',
         [[0.7297,True],[0.0,True],[10.3616,False]],
         NP),
    ("What does a high PSI tell you?", "The live distribution has moved from the reference; investigate, and check performance with labels when available."))

add('monitoring-rates', 'Windowed error rates with a no-traffic policy and minimum volume',
    SK+'modules/model_evaluation.html#classification-metrics', [
    "An error rate divides errors by requests in the same time window. A window with no requests has no rate; report it as missing rather than 0, which would look like perfect health.",
    "Small windows are noisy: 3 errors out of 4 requests is a 75% rate but weak evidence. Require a minimum request count before alerting, so a quiet period does not page someone at 3 a.m.",
    "Alert definitions are product decisions: thresholds, minimum volumes and window lengths should be documented and reviewed. Keep the raw counts, so rates can be recomputed with different policies.",
    "The transfer computes per-window rates and alerts with a threshold and minimum volume."
    ],
    ("A monitoring window has zero requests. What should its error rate be reported as?",
     "Missing (no rate), because there is nothing to divide by.",
     ["0%, meaning no errors.", "100%, to be safe.", "The previous window's rate."],
     "No traffic is a different condition from no errors."),
    task("Transfer: alerting on error rates",
         "data is [windows of [errors, total], threshold, minimum requests]. For each window return [rate rounded to 4 places or None, alert], where an alert needs a rate above the threshold and at least the minimum requests.",
         "windows, threshold, min_requests = data\nreport = []\nfor errors, total in windows:\n    rate = errors / total if total else None\n    alert = rate is not None and total >= min_requests and rate > threshold\n    report.append([None if rate is None else round(rate, 4), alert])\nresult = report",
         [([[[2,10],[0,0],[3,4],[30,100]],0.2,10],[[0.2,False],[None,False],[0.75,False],[0.3,True]]),([[[0,5]],0.1,1],[[0.0,False]]),([[[5,5]],0.5,5],[[1.0,True]])],
         ("total >= min_requests and ",""),
         ["No requests means no rate.", "Require a minimum volume before alerting.", "The threshold is exceeded only when strictly greater."],
         "A 20% rate does not exceed 0.2; the empty window has no rate; 3 of 4 is high but below the minimum volume; 30 of 100 alerts. Dropping the volume check would alert on the four-request window.",
         [[[0.2,True],[None,False],[0.75,True],[0.3,True]],[[0.2,False],[0.0,False],[0.75,False],[0.3,True]],[[0.2,False],[None,False],[0.75,True],[0.3,True]]]),
    ("Why require a minimum request count before alerting?", "Rates from few requests are noisy and cause false alarms."))

add('rollback-policy', 'Bootstrap gates: accept a candidate only when the improvement is credible',
    SK+'modules/generated/sklearn.utils.resample.html#sklearn.utils.resample', [
    "A candidate model that scores higher on a small evaluation sample may be lucky. Bootstrapping resamples the evaluation records with replacement many times and recomputes the paired difference each time, giving a distribution of plausible improvements.",
    "A gate that accepts only when the lower confidence bound (for example the 5th percentile) is above zero rejects improvements that could easily be noise. With more evaluation data, the same average improvement becomes credible.",
    "Resample pairs, keeping each record's baseline and candidate results together, so the comparison is paired. Fix the random states for reproducibility, and record the gate's rule and result with every rollout decision.",
    "The transfer applies a bootstrap gate to paired correctness on small and larger evaluation sets."
    ],
    ("A candidate improves accuracy by 0.2 on 10 paired examples, but the bootstrap 5th percentile is 0. Should a lower-bound gate accept it?",
     "No; the improvement could plausibly be zero, so the gate keeps the baseline.",
     ["Yes; the average improved.", "Yes, if the candidate is newer.", "Only after retraining the baseline."],
     "Require the lower bound, not just the mean, to clear the bar."),
    task("Transfer: a bootstrap rollout gate",
         "data is [baseline correctness, candidate correctness] on the same records. Resample record indices with resample(random_state=seed) for seeds 0–199, compute the mean paired difference and take its 5th percentile. Return ['accept' if it is above 0 else 'rollback', the observed mean difference rounded to 4 places].",
         "baseline, candidate = (np.asarray(v, dtype=float) for v in data)\ndiffs = []\nfor seed in range(200):\n    idx = resample(np.arange(len(candidate)), random_state=seed)\n    diffs.append(candidate[idx].mean() - baseline[idx].mean())\nlower = float(np.percentile(diffs, 5))\nresult = ['accept' if lower > 0 else 'rollback', round(float(candidate.mean() - baseline.mean()), 4)]",
         [([[1,0,1,1,0,1,1,0,1,1],[1,1,1,1,1,1,1,0,1,1]],['rollback',0.2]),([[1,0,1,1,0,1,1,0,1,1]*5,[1,1,1,1,1,1,1,0,1,1]*5],['accept',0.2]),([[1,1,1,1],[1,0,1,0]],['rollback',-0.5])],
         ("lower > 0","candidate.mean() > baseline.mean()"),
         ["Resample paired records together.", "Use a lower percentile of the bootstrap differences.", "More data narrows the interval."],
         'On 10 records the candidate fixes two errors, but resamples without those records are common, so the 5th percentile is 0 and the gate rolls back. The same pattern over 50 records gives a positive lower bound and is accepted. Gating on the mean alone would accept the 10-record result.',
         [['accept',0.2],['rollback',0.0],['accept',-0.2]],
         NP+"\nfrom sklearn.utils import resample"),
    ("Why gate on a bootstrap lower bound instead of the mean improvement?", "A small sample's mean can improve by chance; the lower bound requires a credible improvement."))

add('request-idempotency', 'Idempotent prediction requests with canonical JSON digests',
    SK+'computing/computational_performance.html#prediction-latency', [
    "Clients retry requests after timeouts, so a service can receive the same request several times. An idempotency key lets it return the stored result instead of recomputing or double-counting side effects.",
    "Deriving the key from the payload requires a canonical encoding: JSON with sorted keys and fixed separators, so {'x': 1, 'id': 'a'} and {'id': 'a', 'x': 1} produce identical bytes and digests. Plain json.dumps preserves insertion order and gives different keys for equal payloads.",
    "Bound the cache (size and lifetime) and include the model version in the key, so a new model does not return stale predictions. Do not put secrets into keys that are logged.",
    "The transfer serves repeated and reordered requests through a digest-keyed cache and counts model calls."
    ],
    ("Two payloads contain the same keys and values in different orders. Why canonicalize before hashing?",
     "So equivalent payloads produce the same bytes and therefore the same idempotency key.",
     ["To compress the payload.", "Because JSON forbids unordered keys.", "To encrypt the request."],
     "json.dumps(payload, sort_keys=True, separators=(',', ':')) gives a canonical form."),
    task("Transfer: an idempotency cache",
         "data is a list of request dictionaries. Key each by the SHA-256 of canonical JSON, compute x · 2 only on a cache miss and record the call. Return [responses, number of model calls].",
         "calls = []\ncache = {}\ndef predict(payload):\n    key = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()\n    if key not in cache:\n        calls.append(payload)\n        cache[key] = payload['x'] * 2\n    return cache[key]\nresult = [[predict(p) for p in data], len(calls)]",
         [([{'x':1,'id':'a'},{'id':'a','x':1},{'x':2,'id':'b'}],[[2,2,4],2]),([{'x':5}],[[10],1]),([{'x':1,'id':'a'},{'x':1,'id':'b'}],[[2,2],2])],
         ("json.dumps(payload, sort_keys=True, separators=(',', ':'))","json.dumps(payload)"),
         ["Sort keys before hashing.", "Equal payloads must give equal keys.", "Different ids are different requests."],
         "The reordered duplicate hits the cache, so two calls serve three requests. Without sorted keys, the reordered payload hashes differently and is recomputed.",
         [[[2,2,4],3],[[2,4,4],2],[[2,2,4],1]],
         "import hashlib"),
    ("What makes an idempotency key stable across clients?", "Hashing a canonical encoding: sorted keys and fixed separators."))

add('latency-budgets', 'Prediction latency: tail percentiles against a budget',
    SK+'computing/computational_performance.html#prediction-latency', [
    "Latency distributions have long tails: most requests are fast, a few are very slow. The mean hides the tail and the median ignores it, so service budgets are stated as percentiles such as p95 or p99.",
    "np.percentile with method='nearest' returns an observed value, which is easy to explain in an incident report. With 100 samples, p99 is decided by the slowest couple of requests, so measure over enough requests for the percentile to be meaningful.",
    "Report the measurement window, sample count, hardware and whether the first (warm-up) requests were included. Compare budgets against the same percentile in every release.",
    "The transfer computes mean and tail percentiles for a skewed sample and checks a p99 budget."
    ],
    ("98 requests take 10 ms and 2 take 500 ms and 1000 ms. Which statistic reveals the slow tail?",
     "A high percentile such as p99.",
     ["The median, 10 ms.", "The minimum.", "The mode."],
     "Tail percentiles capture the slow requests users notice."),
    task("Transfer: tail latency against a budget",
         "data is [latencies in ms, p99 budget]. Return [mean, [p50, p95, p99] with method='nearest', whether p99 is within the budget].",
         "latencies = np.asarray(data[0], dtype=float)\nbudget = data[1]\np50, p95, p99 = np.percentile(latencies, [50, 95, 99], method='nearest')\nresult = [float(latencies.mean()), [float(p50), float(p95), float(p99)], bool(p99 <= budget)]",
         [([[10]*98+[500,1000],200],[24.8,[10.0,10.0,500.0],False]),([[5,5,5,5],10],[5.0,[5.0,5.0,5.0],True]),([[1,2,3,4,100],50],[22.0,[3.0,100.0,100.0],False])],
         ("[50, 95, 99]","[50, 95, 90]"),
         ["The mean is pulled up but still hides the tail.", "p99 reflects the slowest requests.", "method='nearest' returns an observed value."],
         "The median and p95 are 10 ms, but p99 is 500 ms, far over the 200 ms budget, while the mean of 24.8 ms looks fine. Checking p90 instead would miss the tail.",
         [[24.8,[10.0,10.0,10.0],True],[10.0,[10.0,10.0,500.0],False],[24.8,[10.0,500.0,1000.0],False]],
         NP),
    ("Why state latency budgets as percentiles?", "Means hide slow tails; p95/p99 describe what the slowest users experience."))

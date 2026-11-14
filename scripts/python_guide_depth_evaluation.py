"""Original Stage 15 ML framing/evaluation depth: scikit-learn 1.7 sections with executed transfer practice."""
from python_guide_depth import add, task

NP = "import numpy as np"
SK = 'https://scikit-learn.org/1.7/'

add('holdout-disjoint', 'train_test_split with stratify: class balance in a small holdout',
    SK+'modules/generated/sklearn.model_selection.train_test_split.html#sklearn.model_selection.train_test_split', [
    "A holdout set estimates performance on data the model never saw, so its records must be disjoint from training. train_test_split shuffles and splits indices or arrays; random_state makes the split reproducible.",
    "With imbalanced classes, a purely random split can put few or no minority examples in a small test set, making metrics unstable or undefined. stratify=y keeps the class proportions in both parts as closely as the sizes allow.",
    "Disjoint rows are not always enough. Duplicated records, several rows per customer or time ordering can still leak information; those need group-aware or time-aware splits, covered next. Record the split seed and sizes with every result.",
    "The transfer makes a stratified split of an imbalanced label vector and checks sizes, minority count and overlap."
    ],
    ("Why pass stratify=y when splitting an imbalanced classification dataset?",
     "To keep class proportions similar in train and test, so the small test set still contains minority examples.",
     ["To make the split faster.", "To remove duplicate rows.", "To guarantee the model performs equally on both classes."],
     "Stratification controls label balance across the split; it does not address grouped or temporal leakage."),
    task("Transfer: a stratified holdout",
         "data is a binary label list. Split the indices with test_size=0.25, stratify=y and random_state=7. Return [train size, test size, positives in test, overlap size].",
         "y = np.array(data)\nidx = np.arange(len(y))\ntrain, test = train_test_split(idx, test_size=0.25, stratify=y, random_state=7)\nresult = [len(train), len(test), int(y[test].sum()), len(set(train) & set(test))]",
         [([0]*12+[1]*4,[12,4,1,0]),([0]*6+[1]*6,[9,3,2,0]),([0]*20+[1]*4,[18,6,1,0])],
         ("test_size=0.25, stratify=y, ","test_size=0.25, "),
         ["test_size=0.25 sends a quarter of the rows to test.", "stratify keeps the positive rate in each part.", "Train and test indices must not overlap."],
         "Sixteen labels with a 25% positive rate give a test set of four containing exactly one positive, and no shared indices. Without stratification, the number of positives in a small test set depends on chance.",
         [[12,4,0,0],[12,4,2,0],[13,3,1,0]],
         NP+"\nfrom sklearn.model_selection import train_test_split"),
    ("What does stratify=y guarantee, and what not?", "Similar class proportions in each split; not protection against grouped, duplicated or temporal leakage."))

add('temporal-split', 'TimeSeriesSplit: expanding windows with a gap',
    SK+'modules/cross_validation.html#time-series-split', [
    "For time-ordered data, validation must come after training, as it will in production. TimeSeriesSplit produces expanding training windows, each followed by a later test window, and never shuffles.",
    "Features computed from recent history, such as rolling means or lagged targets, can still connect the end of training to the start of the test window. gap=k drops k samples between them so that no test example's features overlap the training period.",
    "Each fold's test window has the same size, n_samples // (n_splits + 1) by default. Report per-fold results, because performance often drifts over time, and the last fold is the most realistic estimate of the next period.",
    "The transfer lists the last training index and the test window of each fold, with and without a gap."
    ],
    ("Why add gap= to TimeSeriesSplit?",
     "To leave samples out between train and test so features built from recent history cannot overlap the test period.",
     ["To shuffle the samples within each fold.", "To make the test windows larger.", "To repeat the split with different seeds."],
     "A gap removes the boundary samples whose lagged features would span both periods."),
    task("Transfer: fold boundaries over time",
         "data is [n_samples, n_splits, gap]. For each TimeSeriesSplit fold return [last train index, first test index, last test index].",
         "folds = []\nfor train, test in TimeSeriesSplit(n_splits=data[1], gap=data[2]).split(np.arange(data[0])):\n    folds.append([int(train.max()), int(test.min()), int(test.max())])\nresult = folds",
         [([10,2,1],[[2,4,6],[5,7,9]]),([9,2,0],[[2,3,5],[5,6,8]]),([12,3,2],[[0,3,5],[3,6,8],[6,9,11]])],
         ("gap=data[2]","gap=0"),
         ["Test windows have n_samples // (n_splits + 1) samples.", "Training always ends before the test window.", "The gap removes samples just before each test window."],
         "With ten samples and two splits, test windows are 4–6 and 7–9; a gap of one ends training at 2 and 5 instead of 3 and 6.",
         [[[3,4,6],[6,7,9]],[[2,3,6],[5,7,9]],[[2,4,6]]],
         NP+"\nfrom sklearn.model_selection import TimeSeriesSplit"),
    ("What must hold for every time-series fold?", "Training indices precede test indices, optionally separated by a gap."))

add('group-split', 'GroupKFold: preventing entity leakage across folds',
    SK+'modules/cross_validation.html#group-k-fold', [
    "Several rows often belong to one entity: scans of the same patient, sessions of the same user, photos of the same object. If an entity appears in both training and test folds, the model can memorize it, and the score overstates performance on new entities.",
    "GroupKFold assigns whole groups to folds, so no group is split. Plain KFold splits rows and can cut a group in half, especially when rows of a group are adjacent or shuffled.",
    "Use the entity that will be new in production as the group: if the model will see new patients, group by patient. Combine with stratification (StratifiedGroupKFold) when classes are also imbalanced.",
    "The transfer counts folds in which some group appears on both sides, for KFold and for GroupKFold."
    ],
    ("A dataset has two rows per patient. Why can KFold overestimate performance on new patients?",
     "A patient's rows can land in both train and test folds, letting the model recognize that patient.",
     ["KFold always shuffles rows.", "KFold uses fewer folds than GroupKFold.", "KFold drops duplicated rows."],
     "Split by the entity that must be unseen at prediction time."),
    task("Transfer: count leaking folds",
         "data is a list of group labels, one per row. Count folds where some group appears in both train and test, for KFold(n_splits=2) and GroupKFold(n_splits=2). Return [kfold leaks, groupkfold leaks].",
         "groups = np.array(data)\nx = np.zeros((len(groups), 1))\ndef leaks(splitter):\n    return sum(bool(set(groups[a]) & set(groups[b])) for a, b in splitter.split(x, groups=groups))\nresult = [leaks(KFold(n_splits=2)), leaks(GroupKFold(n_splits=2))]",
         [(['p1','p1','p2','p2','p3','p3'],[2,0]),(['a','b','a','b'],[2,0]),(['x','x','y','y'],[0,0])],
         ("set(groups[a]) & set(groups[b])","set(groups[a]) | set(groups[b])"),
         ["Leakage means a group on both sides of one fold.", "KFold splits rows in order without regard to groups.", "GroupKFold keeps every group on one side."],
         "KFold cuts patient p2 across the halves, so both folds leak; interleaved rows leak too. GroupKFold never splits a group. When groups happen to align with the KFold halves, neither leaks.",
         [[0,0],[2,2],[1,0]],
         NP+"\nfrom sklearn.model_selection import KFold, GroupKFold"),
    ("Which entity should define groups for GroupKFold?", "The entity that will be new at prediction time, such as patient or user."))

add('fit-training-only', 'StandardScaler: fit on training data, transform test data',
    SK+'modules/generated/sklearn.preprocessing.StandardScaler.html#sklearn.preprocessing.StandardScaler', [
    "fit learns statistics from data; transform applies them. A StandardScaler learns mean_ and scale_ during fit and then maps x to (x - mean_) / scale_. Fitting on training data only and transforming test data with those statistics mirrors deployment, where future data is unknown.",
    "Fitting on all data before splitting leaks test information into training: the test set influenced the centring and scaling, so evaluation is optimistic. With small datasets or outliers in the test set, the effect can be large.",
    "A feature with zero variance in training gets scale_ = 1, so transformed values are just centred differences. Test values can legitimately fall far outside the training range; standardized values beyond ±3 are a useful drift signal.",
    "The transfer fits a scaler on training data and transforms a test point, comparing with a leaked fit."
    ],
    ("You fit StandardScaler on the full dataset before train_test_split. What is wrong?",
     "The test data influenced the fitted mean and scale, leaking information into training and evaluation.",
     ["Nothing; scaling is not a learned step.", "StandardScaler cannot be fit on more than one split.", "It makes training slower."],
     "Fit preprocessing inside the training split, ideally with a Pipeline."),
    task("Transfer: train-fitted scaling",
         "data is [train, test] value lists. Fit StandardScaler on train only. Return [mean_, scale_ rounded to 6 places, transformed test values rounded to 6 places].",
         "train, test = (np.asarray(v, dtype=float).reshape(-1, 1) for v in data)\nscaler = StandardScaler().fit(train)\nresult = [scaler.mean_.tolist(), scaler.scale_.round(6).tolist(), scaler.transform(test).ravel().round(6).tolist()]",
         [([[0,2],[100]],[[1.0],[1.0],[99.0]]),([[1,3,5],[3,7]],[[3.0],[1.632993],[0.0,2.44949]]),([[10,10],[10]],[[10.0],[1.0],[0.0]])],
         ("StandardScaler().fit(train)","StandardScaler().fit(np.vstack([train, test]))"),
         ["Fit only on the training rows.", "scale_ is the population standard deviation.", "A zero-variance feature gets scale 1."],
         "The training mean 1 and scale 1 map the test value 100 to 99, which correctly flags it as far outside training. Fitting on all three values would shrink that signal and leak the test point.",
         [[[34.0],[46.669048],[1.414214]],[[1.0],[1.0],[100.0]],[[1.0],[2.0],[49.5]]],
         NP+"\nfrom sklearn.preprocessing import StandardScaler"),
    ("Which data may a preprocessing step's fit see?", "Only the training split; validation and test data are transformed with the fitted statistics."))

add('accuracy-imbalance', 'Balanced accuracy versus accuracy on imbalanced labels',
    SK+'modules/model_evaluation.html#balanced-accuracy-score', [
    "Accuracy counts correct predictions over all examples. When 80% of labels are negative, predicting negative for everything scores 80% accuracy while never finding a positive.",
    "Balanced accuracy averages recall over classes. The all-negative predictor gets recall 1 on negatives and 0 on positives, so its balanced accuracy is 0.5, the same as random guessing. Two models with identical accuracy can differ substantially in balanced accuracy.",
    "Always compare a model with the majority-class baseline, and report per-class metrics for imbalanced problems. Choose the headline metric from the cost of each error type, not from habit.",
    "The transfer compares a majority-class predictor and a model that finds some positives, using both metrics."
    ],
    ("80% of labels are 0 and a model predicts 0 for every example. What are its accuracy and balanced accuracy?",
     "Accuracy 0.8 and balanced accuracy 0.5.",
     ["Both 0.8.", "Accuracy 0.5 and balanced accuracy 0.8.", "Both 0.5."],
     "Balanced accuracy averages per-class recall: (1 + 0) / 2."),
    task("Transfer: compare against the majority baseline",
         "data is [actual, predicted]. Return [majority-class accuracy, majority-class balanced accuracy, model accuracy, model balanced accuracy], all rounded to 6 places; the majority predictor always predicts 0.",
         "actual, predicted = (np.asarray(v) for v in data)\nmajority = np.zeros_like(actual)\nresult = [round(float(accuracy_score(actual, majority)), 6), round(float(balanced_accuracy_score(actual, majority)), 6), round(float(accuracy_score(actual, predicted)), 6), round(float(balanced_accuracy_score(actual, predicted)), 6)]",
         [([[0,0,0,0,0,0,0,0,1,1],[0,0,0,0,0,0,0,1,1,0]],[0.8,0.5,0.8,0.6875]),([[0,1],[1,0]],[0.5,0.5,0.0,0.0]),([[1,1,0],[1,1,0]],[0.333333,0.5,1.0,1.0])],
         ("balanced_accuracy_score(actual, predicted)","accuracy_score(actual, predicted)"),
         ["The majority predictor never finds a positive.", "Balanced accuracy averages recall per class.", "Equal accuracy can hide different minority recall."],
         "Both the baseline and the model have accuracy 0.8, but the model finds one of two positives, giving balanced accuracy (0.875 + 0.5) / 2 = 0.6875 against the baseline's 0.5.",
         [[0.8,0.8,0.8,0.8],[0.8,0.5,0.8,0.8],[0.5,0.5,0.8,0.6875]],
         NP+"\nfrom sklearn.metrics import accuracy_score, balanced_accuracy_score"),
    ("What is the balanced accuracy of a constant majority-class predictor?", "1 / number_of_classes, e.g. 0.5 for binary labels."))

add('precision-recall', 'F1 and F-beta: weighting precision and recall',
    SK+'modules/model_evaluation.html#precision-recall-and-f-measures', [
    "Precision is the fraction of predicted positives that are correct; recall is the fraction of actual positives that are found. F1 is their harmonic mean, which is low whenever either one is low.",
    "F-beta weights recall beta times as much as precision. beta = 2 suits problems where missing a positive is worse than a false alarm, such as screening; beta = 0.5 suits problems where false alarms are costly.",
    "With no predicted positives, precision is undefined; zero_division=0 records it as 0 instead of warning. Report precision and recall alongside any F score, because the same F1 can come from very different trade-offs.",
    "The transfer computes precision, recall, F1 and F2 for a classifier that misses most positives."
    ],
    ("When is F2 more appropriate than F1?",
     "When missing a positive (low recall) is costlier than a false positive.",
     ["When false positives are costlier.", "When classes are perfectly balanced.", "When there are more than two classes."],
     "F-beta weights recall beta times as much as precision; beta = 2 favours recall."),
    task("Transfer: precision, recall and F-scores",
         "data is [actual, predicted]. Return [precision, recall, F1, F2], rounded to 6 places with zero_division=0.",
         "actual, predicted = data\np = precision_score(actual, predicted, zero_division=0)\nr = recall_score(actual, predicted, zero_division=0)\nresult = [round(float(p), 6), round(float(r), 6), round(float(f1_score(actual, predicted, zero_division=0)), 6), round(float(fbeta_score(actual, predicted, beta=2, zero_division=0)), 6)]",
         [([[1,1,1,0,0],[1,0,0,1,0]],[0.5,0.333333,0.4,0.357143]),([[1,0],[0,0]],[0.0,0.0,0.0,0.0]),([[1,1],[1,1]],[1.0,1.0,1.0,1.0])],
         ("beta=2","beta=0.5"),
         ["Precision divides by predicted positives.", "Recall divides by actual positives.", "F2 weights recall more heavily than precision."],
         "One of two predicted positives is correct (precision 0.5) and one of three actual positives is found (recall 1/3). F1 is 0.4 and F2, which weights the weak recall more, is lower at about 0.357.",
         [[0.333333,0.5,0.4,0.357143],[0.5,0.333333,0.416667,0.357143],[0.5,0.333333,0.4,0.454545]],
         "from sklearn.metrics import precision_score, recall_score, f1_score, fbeta_score"),
    ("What do precision and recall divide by?", "Precision by predicted positives; recall by actual positives."))

add('regression-losses', 'Regression metrics: MAE favours the median, MSE the mean',
    SK+'modules/model_evaluation.html#regression-metrics', [
    "Mean absolute error averages |y - ŷ|; mean squared error averages (y - ŷ)². Squaring makes large errors dominate, so MSE is far more sensitive to outliers than MAE.",
    "The best constant prediction differs between them: the median minimizes MAE and the mean minimizes MSE. A dataset with one extreme value shows the gap clearly, and explains why a model trained on MSE chases outliers.",
    "Pick the loss that matches the cost of errors in the application, report it in the target's units (RMSE or MAE) and compare models against a constant baseline. Never compare MSE values across differently scaled targets.",
    "The transfer evaluates constant median and mean predictions under both losses on data with an outlier."
    ],
    ("Which constant prediction minimizes mean absolute error?",
     "The median of the targets.",
     ["The mean of the targets.", "Zero.", "The maximum target."],
     "The median minimizes absolute deviations; the mean minimizes squared deviations."),
    task("Transfer: constant baselines under two losses",
         "data is a list of targets. Return [MAE of the constant median, MAE of the constant mean, MSE of the constant mean, MSE of the constant median], rounded to 6 places.",
         "y = np.asarray(data, dtype=float)\nconst_mean = np.full_like(y, y.mean())\nconst_median = np.full_like(y, np.median(y))\nresult = [round(float(mean_absolute_error(y, const_median)), 6), round(float(mean_absolute_error(y, const_mean)), 6), round(float(mean_squared_error(y, const_mean)), 6), round(float(mean_squared_error(y, const_median)), 6)]",
         [([1,2,3,100],[25.0,36.75,1801.25,2377.25]),([5,5],[0.0,0.0,0.0,0.0]),([0,10],[5.0,5.0,25.0,25.0])],
         ("np.median(y)","y.mean()"),
         ["The median here is 2.5 and the mean 26.5.", "MAE is lower for the median; MSE is lower for the mean.", "One outlier dominates MSE."],
         "With the outlier, the median gives MAE 25 against 36.75 for the mean, while the mean gives MSE about 1801 against about 2378 for the median. Each loss prefers its own optimal constant.",
         [[36.75,25.0,1801.25,2377.25],[25.0,36.75,2377.25,1801.25],[25.0,25.0,1801.25,1801.25]],
         NP+"\nfrom sklearn.metrics import mean_absolute_error, mean_squared_error"),
    ("Why is MSE sensitive to outliers?", "Squaring makes large errors dominate the average."))

add('ranking-auc', 'ROC AUC as pairwise ranking probability',
    SK+'modules/model_evaluation.html#roc-metrics', [
    "ROC AUC equals the probability that a randomly chosen positive example receives a higher score than a randomly chosen negative one, counting ties as half. It measures ranking quality across all thresholds.",
    "Because it depends only on the order of scores, any strictly increasing transformation, such as exp or a logistic squashing, leaves AUC unchanged. AUC therefore says nothing about whether scores are calibrated probabilities.",
    "AUC is undefined when only one class is present, and a high AUC can coexist with poor performance at the operating threshold you actually use. Pair it with threshold-specific metrics and calibration checks.",
    "The transfer computes AUC with scikit-learn, by counting correctly ordered pairs, and after a monotonic transformation."
    ],
    ("You apply np.exp to every score. What happens to ROC AUC?",
     "Nothing; exp is strictly increasing, so the ranking is unchanged.",
     ["It increases, because scores grow.", "It decreases, because differences grow.", "It becomes undefined."],
     "AUC depends only on the order of the scores."),
    task("Transfer: AUC by pair counting",
         "data is [labels, scores]. Return [roc_auc_score, the fraction of positive/negative pairs ordered correctly (ties count 0.5), AUC of exp(scores)], rounded to 6 places.",
         "actual, scores = (np.asarray(v, dtype=float) for v in data)\nauc = roc_auc_score(actual, scores)\npos, neg = scores[actual == 1], scores[actual == 0]\npairs = np.mean([1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg])\nresult = [round(float(auc), 6), round(float(pairs), 6), round(float(roc_auc_score(actual, np.exp(scores))), 6)]",
         [([[0,0,1,1],[0.1,0.4,0.35,0.8]],[0.75,0.75,0.75]),([[0,1],[0.5,0.5]],[0.5,0.5,0.5]),([[1,0,1],[3,1,2]],[1.0,1.0,1.0])],
         ("1.0 if p > n else 0.5 if p == n else 0.0","1.0 if p >= n else 0.0"),
         ["Compare every positive score with every negative score.", "A tie counts as half a correct ordering.", "Monotonic transforms keep the order."],
         "Three of four positive/negative pairs are ordered correctly, so AUC is 0.75 by both methods and after exp. Counting ties as correct would turn the tied case's 0.5 into 1.",
         [[0.75,0.5,0.75],[0.75,0.75,0.9],[1.0,0.75,0.75]],
         NP+"\nfrom sklearn.metrics import roc_auc_score"),
    ("What probability does ROC AUC measure?", "That a random positive is scored above a random negative (ties count half)."))

add('threshold-policy', 'Choosing a decision threshold from error costs on validation data',
    SK+'modules/classification_threshold.html#post-tuning-the-decision-threshold', [
    "A classifier's scores become decisions only through a threshold. 0.5 is a convention, not an optimum. The right threshold depends on what false positives and false negatives cost in the application.",
    "Given costs, compute the total cost at each candidate threshold on validation data and choose the cheapest. When missing a positive costs ten times a false alarm, the best threshold is usually much lower than 0.5.",
    "Choose the threshold on validation data and then measure it once on test data; tuning on the test set makes the reported cost optimistic. scikit-learn's TunedThresholdClassifierCV automates the cross-validated version.",
    "The transfer searches a small grid of thresholds for the lowest total cost under two cost settings."
    ],
    ("False negatives cost 10 and false positives cost 1. Should the threshold usually move above or below 0.5?",
     "Below, so more cases are flagged positive and fewer positives are missed.",
     ["Above, to reduce false positives.", "It should stay at 0.5.", "Costs do not affect the threshold."],
     "Expensive misses push the threshold down."),
    task("Transfer: cost-based threshold choice",
         "data is [labels, scores, cost_fp, cost_fn]. For thresholds 0.1, 0.3, 0.5, 0.7 and 0.9, compute total cost. Return [cheapest threshold (smallest on ties), its cost, the cost at 0.5].",
         "labels, scores, cost_fp, cost_fn = data\nlabels, scores = np.asarray(labels), np.asarray(scores)\ncosts = {}\nfor t in [0.1, 0.3, 0.5, 0.7, 0.9]:\n    pred = scores >= t\n    costs[t] = int(cost_fp * np.sum(pred & (labels == 0)) + cost_fn * np.sum(~pred & (labels == 1)))\nbest = min(costs, key=lambda t: (costs[t], t))\nresult = [best, costs[best], costs[0.5]]",
         [([[0,0,1,1,0],[0.2,0.4,0.35,0.8,0.6],1,10],[0.3,2,11]),([[0,0,1,1,0],[0.2,0.4,0.35,0.8,0.6],1,1],[0.7,1,2]),([[1,0],[0.9,0.1],1,1],[0.3,0,0])],
         ("min(costs, key=lambda t: (costs[t], t))","max(costs, key=lambda t: (costs[t], t))"),
         ["Count false positives and false negatives at each threshold.", "Weight each error type by its cost.", "Break ties by the smaller threshold."],
         "With costly misses, threshold 0.3 catches both positives at the price of two false alarms, costing 2 against 11 at 0.5. With equal costs, 0.7 is cheapest.",
         [[0.5,11,11],[0.1,3,11],[0.3,2,2]],
         NP),
    ("Where should a decision threshold be tuned?", "On validation data (or cross-validation), using the application's error costs; then evaluate once on test."))

add('confusion-counts', 'confusion_matrix: tn/fp/fn/tp order and normalize="true"',
    SK+'modules/model_evaluation.html#confusion-matrix', [
    "For binary labels ordered [0, 1], confusion_matrix rows are actual classes and columns predicted ones, so ravel() returns tn, fp, fn, tp. Passing labels= fixes that order even when one class is absent from a batch.",
    "normalize='true' divides each row by its total, turning counts into per-class rates: the diagonal holds specificity and recall. A row with no examples has no rates; scikit-learn reports zeros there.",
    "Reading the raw counts beside the rates prevents misinterpretation: a rate of 1.0 from two examples is weak evidence. Put labels in a fixed order in every report so that columns mean the same thing across runs.",
    "The transfer unpacks the four counts and computes row-normalized rates."
    ],
    ("With labels=[0, 1], what does confusion_matrix(...).ravel() return?",
     "tn, fp, fn, tp.",
     ["tp, fp, fn, tn.", "tp, fn, fp, tn.", "fp, tn, tp, fn."],
     "Rows are actual classes and columns predicted classes, in the given label order."),
    task("Transfer: counts and per-class rates",
         "data is [actual, predicted]. Return [[tn, fp, fn, tp], confusion_matrix normalized by true class, rounded to 6 places].",
         "actual, predicted = data\ntn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel().tolist()\nrates = confusion_matrix(actual, predicted, labels=[0, 1], normalize='true').round(6).tolist()\nresult = [[tn, fp, fn, tp], rates]",
         [([[0,0,1,1,1],[0,1,1,1,0]],[[1,1,1,2],[[0.5,0.5],[0.333333,0.666667]]]),([[0,0],[0,0]],[[2,0,0,0],[[1.0,0.0],[0.0,0.0]]]),([[1,0,1],[1,0,1]],[[1,0,0,2],[[1.0,0.0],[0.0,1.0]]])],
         ("labels=[0, 1]).ravel()","labels=[1, 0]).ravel()"),
         ["Rows are actual classes; columns are predicted.", "labels= fixes the order of classes.", "normalize='true' divides each row by its total."],
         "One negative is correct and one is a false positive; two of three positives are found. Each row of rates sums to one. Reversing the label order would unpack the counts as tp, fn, fp, tn.",
         [[[2,1,1,1],[[0.5,0.5],[0.333333,0.666667]]],[[1,1,1,2],[[0.5,0.333333],[0.5,0.666667]]],[[1,1,2,1],[[0.5,0.5],[0.333333,0.666667]]]],
         "from sklearn.metrics import confusion_matrix"),
    ("What do confusion-matrix rows and columns mean in scikit-learn?", "Rows are actual classes and columns predicted classes, in the order given by labels=."))

add('dummy-baseline', 'DummyClassifier baselines inside cross-validation',
    SK+'modules/model_evaluation.html#dummy-estimators', [
    "A DummyClassifier predicts without using features: the most frequent class, a stratified random guess or a constant. Its cross-validated score is the bar any real model must clear.",
    "Evaluate the baseline with exactly the same splits and metric as the model. A model scoring 0.9 accuracy is unimpressive if predicting the majority class also scores 0.9. A model that does not beat the baseline has learned nothing useful from its features.",
    "Report the baseline next to every result. For regression, DummyRegressor(strategy='mean') gives an R² of about zero, which is the corresponding reference point.",
    "The transfer cross-validates a majority baseline and a logistic regression on informative and uninformative features."
    ],
    ("Why compare a model against DummyClassifier(strategy='most_frequent')?",
     "It shows the score achievable without using features; a useful model must exceed it.",
     ["It is always the best model for imbalanced data.", "It tunes the model's hyperparameters.", "It removes class imbalance."],
     "Baselines turn an isolated score into evidence of learning."),
    task("Transfer: does the model beat the baseline?",
         "data is [x values, labels]. Using cross_val_score with cv=2, return [mean baseline accuracy, mean logistic-regression accuracy, model > baseline], rounded to 6 places.",
         "x = np.asarray(data[0], dtype=float).reshape(-1, 1)\ny = np.asarray(data[1])\nbaseline = cross_val_score(DummyClassifier(strategy='most_frequent'), x, y, cv=2).mean()\nmodel = cross_val_score(LogisticRegression(), x, y, cv=2).mean()\nresult = [round(float(baseline), 6), round(float(model), 6), bool(model > baseline)]",
         [([[-3,-2,-1,1,2,3],[0,0,0,1,1,1]],[0.333333,1.0,True]),([[1,2,3,4,5,6,7,8],[0,1,0,1,0,1,0,1]],[0.5,0.5,False]),([[0,1,2,3,10,11,12,13],[0,0,0,0,1,1,1,1]],[0.5,1.0,True])],
         ("strategy='most_frequent'","strategy='constant', constant=1"),
         ["Use the same CV splits for the baseline and the model.", "Cross-validation fits a fresh copy in each fold.", "An uninformative feature should not beat the baseline."],
         "On the separable data, each stratified training fold holds two of one class and one of the other, so the majority baseline predicts the class that is the minority in its test fold and scores 1/3, while logistic regression scores 1.0. With alternating labels the feature carries no usable signal and the model only ties the baseline. A constant-1 baseline would score differently, which is why the baseline strategy must be stated.",
         [[0.5,1.0,True],[0.333333,0.5,True],[0.333333,1.0,False]],
         NP+"\nfrom sklearn.dummy import DummyClassifier\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.model_selection import cross_val_score"),
    ("What does a model that fails to beat DummyClassifier tell you?", "It has not learned anything useful from its features under that metric and split."))

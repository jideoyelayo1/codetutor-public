"""Original Stage 17 model-selection/unsupervised depth: scikit-learn 1.7 sections with executed transfer practice."""
from python_guide_depth import add, task

NP = "import numpy as np"
SK = 'https://scikit-learn.org/1.7/'
API = SK+'modules/generated/'

add('stratified-cv', 'StratifiedKFold versus KFold on sorted labels',
    SK+'modules/cross_validation.html#stratified-k-fold', [
    "KFold without shuffling takes consecutive blocks of rows. If the data is sorted by label, as exported tables often are, a test fold can contain only one class, and its accuracy or AUC is misleading or undefined.",
    "StratifiedKFold assigns rows so that each fold's class proportions match the whole dataset as closely as possible. For classification, scikit-learn's cross_val_score uses stratified folds by default when given an integer cv.",
    "Stratification balances labels, nothing more. Grouped or time-ordered data still needs GroupKFold, StratifiedGroupKFold or TimeSeriesSplit. Shuffle with a fixed random_state when row order carries no meaning.",
    "The transfer counts positives in each test fold for KFold and StratifiedKFold on sorted labels."
    ],
    ("Labels are sorted with all negatives first. What can unshuffled KFold(n_splits=2) produce?",
     "Test folds containing only one class.",
     ["Perfectly balanced folds.", "An error, because labels are sorted.", "Folds that overlap."],
     "Consecutive blocks follow the row order; stratification or shuffling is needed."),
    task("Transfer: positives per test fold",
         "data is [negatives, positives]; labels are sorted with negatives first. Return [positives per test fold for KFold(2), positives per test fold for StratifiedKFold(2)].",
         "y = np.array([0] * data[0] + [1] * data[1])\nx = np.zeros((len(y), 1))\nplain = [int(y[test].sum()) for _, test in KFold(n_splits=2).split(x)]\nstrat = [int(y[test].sum()) for _, test in StratifiedKFold(n_splits=2).split(x, y)]\nresult = [plain, strat]",
         [([6,2],[[0,2],[1,1]]),([4,4],[[0,4],[2,2]]),([3,3],[[0,3],[1,2]])],
         ("StratifiedKFold(n_splits=2).split(x, y)","KFold(n_splits=2).split(x)"),
         ["KFold takes consecutive blocks.", "Sorted labels make each block one class.", "StratifiedKFold splits each class across folds."],
         "With six negatives then two positives, KFold puts both positives in the second fold, while stratification places one in each. Replacing the stratified splitter with KFold reproduces the imbalance.",
         [[[1,1],[1,1]],[[0,2],[0,2]],[[2,0],[1,1]]],
         NP+"\nfrom sklearn.model_selection import KFold, StratifiedKFold"),
    ("What does stratification balance, and what not?", "Class proportions per fold; not groups or time order."))

add('grid-search', 'GridSearchCV: ranks, refit and the best_estimator_',
    API+'sklearn.model_selection.GridSearchCV.html#sklearn.model_selection.GridSearchCV', [
    "GridSearchCV evaluates each parameter combination with cross-validation and records the mean scores in cv_results_. rank_test_score orders candidates, with 1 for the best. Nested parameter names use step__parameter, such as logisticregression__C.",
    "With refit=True (the default), the best combination is refitted on all the data passed to fit, available as best_estimator_. predict and score on the search object use that refitted model.",
    "best_score_ is the cross-validated score of the winner, chosen because it was highest, so it is optimistic. Report performance on a separate test set or with nested cross-validation. Keep grids small and meaningful; huge grids also overfit the validation folds.",
    "The transfer searches regularization strengths for a logistic regression and inspects the ranking."
    ],
    ("Why is GridSearchCV's best_score_ an optimistic estimate?",
     "It is the maximum over candidates evaluated on the same folds, so selection inflates it.",
     ["It is computed on training data only.", "It ignores the last fold.", "It uses a different metric."],
     "Estimate final performance on data not used for selection."),
    task("Transfer: rank candidates in a grid search",
         "data is a sample count. Build x evenly spaced in [-3, 3] and imbalanced labels x > 1.5. Search logisticregression__C in [0.001, 1, 100] with cv=3 in a scaling pipeline. Return [best C, rank of each candidate, whether best_estimator_ exists].",
         "x = np.linspace(-3, 3, data).reshape(-1, 1)\ny = (x.ravel() > 1.5).astype(int)\nsearch = GridSearchCV(make_pipeline(StandardScaler(), LogisticRegression()), {'logisticregression__C': [0.001, 1.0, 100.0]}, cv=3).fit(x, y)\nresult = [search.best_params_['logisticregression__C'], search.cv_results_['rank_test_score'].tolist(), hasattr(search, 'best_estimator_')]",
         [(30,[1.0,[3,1,2],True]),(60,[1.0,[3,1,2],True]),(90,[1.0,[3,1,2],True])],
         ("'logisticregression__C': [0.001, 1.0, 100.0]","'logisticregression__C': [0.001, 1.0]"),
         ["Nested parameters use step__name.", "rank 1 is the best mean CV score.", "refit=True stores the winner as best_estimator_."],
         'Only a quarter of the labels are positive. With C = 0.001 the penalty flattens the slope so the model mostly predicts the majority class, ranking last; C = 1 ranks first and is refitted as best_estimator_. Dropping a candidate changes the ranking list itself.',
         [[0.001,[1,3,2],True],[100.0,[3,2,1],True],[1.0,[3,1,2],False]],
         NP+"\nfrom sklearn.model_selection import GridSearchCV\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression"),
    ("What does refit=True give you after a grid search?", "best_estimator_, the winning configuration refitted on all the data passed to fit."))

add('nested-cv', 'Nested cross-validation: the inner choice can differ per outer fold',
    SK+'auto_examples/model_selection/plot_nested_cross_validation_iris.html#nested-versus-non-nested-cross-validation', [
    "Nested cross-validation puts a whole model-selection procedure, such as a GridSearchCV, inside an outer cross-validation loop. Each outer fold runs its own inner search on its training part and is then scored on its held-out part.",
    "The outer score estimates how well the procedure, search included, generalizes. It is the honest number to report when hyperparameters were tuned. The inner best scores are biased upward by selection.",
    "Different outer folds may select different hyperparameters. That variation is informative: it shows how stable the choice is. return_estimator=True keeps the fitted inner searches so you can inspect each choice.",
    "The transfer runs a tree-depth search inside stratified outer folds and reports the per-fold choices and the outer mean."
    ],
    ("In nested cross-validation, what does the outer score estimate?",
     "The generalization of the whole tuning-plus-fitting procedure.",
     ["The performance of one fixed hyperparameter setting.", "The training accuracy.", "The inner best score."],
     "Tuning is part of the procedure being evaluated."),
    task("Transfer: per-fold choices in nested CV",
         "data is a sample count. x = 0..n-1 and labels (x mod 7) > 3. Run GridSearchCV over max_depth [1, 2, 3] (cv=3) inside cross_validate with StratifiedKFold(3, shuffle=True, random_state=7). Return [number of outer scores, chosen depth per outer fold, outer mean accuracy rounded to 4 places].",
         "x = np.arange(data, dtype=float).reshape(-1, 1)\ny = ((x.ravel() % 7) > 3).astype(int)\ninner = GridSearchCV(DecisionTreeClassifier(random_state=7), {'max_depth': [1, 2, 3]}, cv=3)\nouter = cross_validate(inner, x, y, cv=StratifiedKFold(3, shuffle=True, random_state=7), return_estimator=True)\nresult = [len(outer['test_score']), [int(e.best_params_['max_depth']) for e in outer['estimator']], round(float(outer['test_score'].mean()), 4)]",
         [(21,[3,[3,1,2],0.4286]),(35,[3,[1,1,2],0.5429]),(42,[3,[1,1,2],0.5238])],
         ("cv=StratifiedKFold(3, shuffle=True, random_state=7)","cv=StratifiedKFold(2, shuffle=True, random_state=7)"),
         ["Each outer fold runs its own inner search.", "return_estimator keeps each fitted search.", "Report the outer mean, not inner best scores."],
         'The periodic target cannot be captured by a shallow tree on x, so each outer fold picks a different depth and the honest outer mean stays near chance. That instability is exactly what nested CV reveals and an inner best score would hide. Two outer folds would change both the count and the choices.',
         [[2,[3,1,2],0.4286],[3,[3,3,3],0.4286],[3,[3,1,2],0.75]],
         NP+"\nfrom sklearn.model_selection import GridSearchCV, cross_validate, StratifiedKFold\nfrom sklearn.tree import DecisionTreeClassifier"),
    ("Why report the outer score of nested CV?", "Inner best scores are inflated by selection; the outer score evaluates the full procedure on unseen folds."))

add('learning-curves', 'learning_curve: reading the train/validation gap',
    API+'sklearn.model_selection.learning_curve.html#sklearn.model_selection.learning_curve', [
    "A learning curve plots training and validation scores as the training set grows. It separates two failure modes: high bias, where both scores are low and close, and high variance, where training is high but validation lags behind.",
    "If validation keeps improving with more data, collecting data will help. If the curves have converged at a poor score, a more expressive model or better features are needed instead. An unconstrained decision tree typically shows perfect training scores at every size.",
    "Shuffle with a fixed random_state when the data is ordered, otherwise early training subsets are unrepresentative. The returned arrays have one row per training size and one column per CV fold; average across columns.",
    "The transfer computes learning curves for an unconstrained tree on a periodic target."
    ],
    ("Training accuracy is 1.0 at every size while validation accuracy is much lower. What does this indicate?",
     "High variance (overfitting); more data or regularization may help.",
     ["High bias; the model is too simple.", "A bug in learning_curve.", "Perfect generalization."],
     "A persistent train/validation gap is the signature of variance."),
    task("Transfer: learning-curve diagnostics",
         "data is a sample count. x = 0..n-1 and labels sin(x) > 0. Run learning_curve for an unconstrained DecisionTreeClassifier with cv=3, train_sizes [0.5, 1.0], shuffle=True, random_state=7. Return [absolute train sizes, mean training scores rounded to 3 places, whether training scores >= validation scores at every size].",
         "x = np.arange(data, dtype=float).reshape(-1, 1)\ny = (np.sin(x.ravel()) > 0).astype(int)\nsizes, train, valid = learning_curve(DecisionTreeClassifier(random_state=7), x, y, cv=3, train_sizes=[0.5, 1.0], shuffle=True, random_state=7)\nresult = [sizes.tolist(), train.mean(axis=1).round(3).tolist(), bool(np.all(train.mean(axis=1) >= valid.mean(axis=1)))]",
         [(30,[[10,20],[1.0,1.0],True]),(60,[[20,40],[1.0,1.0],True]),(90,[[30,60],[1.0,1.0],True])],
         ("train_sizes=[0.5, 1.0]","train_sizes=[0.3, 1.0]"),
         ["Sizes are fractions of the training part of each fold.", "Average scores across the fold columns.", "An unconstrained tree fits its training data perfectly."],
         'Each fold trains on two thirds of the data, so the sizes are half of that and all of it. The unconstrained tree scores 1.0 on its training data at both sizes, while validation is lower: a variance gap. Changing the fractions changes the absolute sizes.',
         [[[15,30],[1.0,1.0],True],[[10,20],[0.5,1.0],True],[[10,20],[1.0,1.0],False]],
         NP+"\nfrom sklearn.model_selection import learning_curve\nfrom sklearn.tree import DecisionTreeClassifier"),
    ("How does a learning curve distinguish bias from variance?", "Low, converged curves indicate bias; a high training score with a validation gap indicates variance."))

add('calibration-error', 'Brier score and log loss: same decisions, different probability quality',
    API+'sklearn.metrics.brier_score_loss.html#sklearn.metrics.brier_score_loss', [
    "Two models can make identical class decisions at a 0.5 threshold yet give very different probabilities. Accuracy cannot tell them apart; proper scoring rules such as the Brier score and log loss can.",
    "The Brier score is the mean squared difference between predicted probability and outcome. Log loss is the mean negative log probability of the true outcome, and it punishes confident mistakes very heavily: predicting 0.01 for an event that happens costs about 4.6.",
    "When probabilities feed decisions, such as expected cost, risk scores or ranking by likelihood, evaluate them with these metrics and inspect calibration curves. CalibratedClassifierCV can recalibrate a model's scores on validation data.",
    "The transfer compares an overconfident and a hedged model that make the same decisions."
    ],
    ("Two models make identical predictions at threshold 0.5. Can their Brier scores differ?",
     "Yes; the Brier score measures probability quality, not just the decisions.",
     ["No; identical decisions imply identical Brier scores.", "Only if the classes are imbalanced.", "Only for multiclass problems."],
     "Proper scoring rules evaluate the probabilities themselves."),
    task("Transfer: score probability quality",
         "data is [labels, confident probabilities, hedged probabilities]. Return [whether both models make the same 0.5-threshold decisions, Brier confident, Brier hedged, log loss confident, log loss hedged], rounded to 6 places.",
         "actual, confident, hedged = (np.asarray(v, dtype=float) for v in data)\nsame_decisions = bool(np.array_equal(confident >= 0.5, hedged >= 0.5))\nresult = [same_decisions, round(float(brier_score_loss(actual, confident)), 6), round(float(brier_score_loss(actual, hedged)), 6), round(float(log_loss(actual, confident)), 6), round(float(log_loss(actual, hedged)), 6)]",
         [([[1,0,1,0],[0.99,0.01,0.01,0.99],[0.7,0.3,0.4,0.6]],[True,0.4901,0.225,2.30761,0.636483]),([[1,0],[0.9,0.1],[0.6,0.4]],[True,0.01,0.16,0.105361,0.510826]),([[0,1],[0.2,0.8],[0.4,0.6]],[True,0.04,0.16,0.223144,0.510826])],
         ("brier_score_loss(actual, hedged)","brier_score_loss(1 - actual, hedged)"),
         ["Both models predict [1, 0, 0, 1] at 0.5.", "Brier is the mean squared probability error.", "Log loss explodes for confident mistakes."],
         "Both models predict [1, 0, 0, 1], so accuracy cannot separate them. The confident model's two 0.99-wrong answers give Brier 0.49 and log loss 2.31, while the hedged model scores 0.225 and 0.64. When the confident model is right, as in the other cases, it scores better.",
         [[True,0.225,0.4901,0.636483,2.30761],[False,0.4901,0.225,2.30761,0.636483],[True,0.4901,0.225,0.4901,0.225]],
         NP+"\nfrom sklearn.metrics import brier_score_loss, log_loss"),
    ("Why evaluate probabilities with log loss or the Brier score?", "They measure probability quality, which accuracy ignores; confident mistakes are penalized heavily."))

add('feature-variance', 'VarianceThreshold for near-constant binary features',
    API+'sklearn.feature_selection.VarianceThreshold.html#sklearn.feature_selection.VarianceThreshold', [
    "VarianceThreshold removes features whose training variance does not exceed a threshold. The default of 0 drops only constant columns, which carry no information for any model.",
    "For a binary feature that is 1 with frequency p, the variance is p(1 - p). A threshold of 0.8 × 0.2 = 0.16 removes features where one value occurs in more than 80% of rows, a common way to drop near-constant indicator columns.",
    "The selector is fitted, so put it inside a Pipeline to compute variances on training folds only. get_support shows which columns survived, and variances_ records the values the decision was based on.",
    "The transfer applies an 80% threshold to binary features and reports kept columns and variances."
    ],
    ("What is the variance of a binary feature that equals 1 in 5 of 6 rows?",
     "5/6 × 1/6 ≈ 0.139.",
     ["5/6 ≈ 0.833.", "0.25.", "0, because it is binary."],
     "Bernoulli variance is p(1 - p)."),
    task("Transfer: drop near-constant indicators",
         "data is a binary matrix. Fit VarianceThreshold(threshold=0.8 × 0.2). Return [kept-column mask, variances rounded to 6 places, number of kept columns].",
         "x = np.asarray(data, dtype=float)\nselector = VarianceThreshold(threshold=0.8 * (1 - 0.8)).fit(x)\nresult = [selector.get_support().tolist(), selector.variances_.round(6).tolist(), selector.transform(x).shape[1]]",
         [([[1,1,1],[1,1,0],[1,1,1],[1,1,0],[1,1,1],[1,0,0]],[[False,False,True],[0.0,0.138889,0.25],1]),([[0,1],[1,0]],[[True,True],[0.25,0.25],2]),([[1,0],[1,0],[1,0],[1,1]],[[False,True],[0.0,0.1875],1])],
         ("threshold=0.8 * (1 - 0.8)","threshold=0.0"),
         ["Bernoulli variance is p(1 - p).", "Features must exceed the threshold to be kept.", "The default threshold removes only constant columns."],
         "The constant column has variance 0 and the 5-of-6 column 0.139, both at or below 0.16, so only the balanced column is kept. A zero threshold would keep the near-constant column too.",
         [[[False,True,True],[0.0,0.138889,0.25],2],[[False,False,True],[0.0,0.833333,0.5],1],[[True,True,True],[0.0,0.138889,0.25],3]],
         NP+"\nfrom sklearn.feature_selection import VarianceThreshold"),
    ("Which variance threshold removes binary features where one value exceeds 80%?", "0.8 × (1 - 0.8) = 0.16."))

add('pca-components', 'PCA: explained variance ratio, choosing components and reconstruction error',
    API+'sklearn.decomposition.PCA.html#sklearn.decomposition.PCA', [
    "PCA finds orthogonal directions of maximum variance in centred data. explained_variance_ratio_ gives the fraction of total variance captured by each component, in decreasing order.",
    "Passing a float such as n_components=0.95 keeps the smallest number of components that together explain at least 95% of the variance. That turns an arbitrary choice into a stated criterion.",
    "inverse_transform maps the reduced representation back to the original space; the mean squared difference from the input is the information lost. PCA is sensitive to feature scale, so standardize first when features have different units, and fit it on training data only.",
    "The transfer fits PCA to nearly collinear points, chooses components by variance and measures reconstruction error."
    ],
    ("What does PCA(n_components=0.95) do?",
     "Keeps the fewest components whose explained variance ratios sum to at least 0.95.",
     ["Keeps 95 components.", "Keeps 95% of the rows.", "Removes components with variance below 0.95."],
     "A float in (0, 1) selects components by cumulative explained variance."),
    task("Transfer: choose components by variance",
         "data is a 2-D list. Return [explained variance ratios of a full PCA rounded to 4 places, components chosen by n_components=0.95, mean squared reconstruction error of that choice rounded to 6 places].",
         "x = np.asarray(data, dtype=float)\nfull = PCA().fit(x)\nchosen = PCA(n_components=0.95).fit(x)\nrecon = chosen.inverse_transform(chosen.transform(x))\nresult = [full.explained_variance_ratio_.round(4).tolist(), int(chosen.n_components_), round(float(np.mean((x - recon) ** 2)), 6)]",
         [([[1,1],[2,2.1],[3,2.9],[4,4]],[[0.9991,0.0009],1,0.001147]),([[1,0],[-1,0],[0,1],[0,-1]],[[0.5,0.5],2,0.0]),([[0,0],[1,1],[2,2]],[[1.0,0.0],1,0.0])],
         ("n_components=0.95","n_components=0.9999"),
         ["Ratios are sorted from largest to smallest.", "The float picks the fewest components reaching 95%.", "Reconstruction error measures what the dropped components held."],
         'The nearly collinear points put 99.9% of the variance on one component, so one component is kept with a tiny reconstruction error. Symmetric points need both components. Asking for 99.99% would keep both and reconstruct exactly.',
         [[[0.9991,0.0009],2,0.0],[[0.5,0.5],1,0.001147],[[0.0009,0.9991],1,0.001147]],
         NP+"\nfrom sklearn.decomposition import PCA"),
    ("How do you measure what PCA discarded?", "Reconstruct with inverse_transform and compute the error against the original data."))

add('cluster-labels', 'KMeans labels are arbitrary: evaluate with adjusted_rand_score',
    API+'sklearn.metrics.adjusted_rand_score.html#sklearn.metrics.adjusted_rand_score', [
    "Cluster numbers are arbitrary names. KMeans may call the same group 0 in one run and 1 in another, so comparing labels directly with reference classes, as in accuracy, can report 0% for a perfect clustering.",
    "adjusted_rand_score compares two partitions by asking which pairs of points are grouped together. It is invariant to renaming clusters: 1.0 means identical partitions, about 0 means chance agreement and negative values mean worse than chance.",
    "Without reference labels, use internal measures such as the silhouette score, and check stability across seeds. Fix random_state and n_init for reproducibility, and remember that KMeans assumes roughly spherical clusters of similar size.",
    "The transfer clusters one-dimensional points and evaluates the result with ARI and with permutation-aware accuracy."
    ],
    ("KMeans labels a perfect clustering as [1, 1, 0, 0] while the reference is [0, 0, 1, 1]. What is the adjusted Rand index?",
     "1.0, because the partitions are identical up to renaming.",
     ["0.0, because every label differs.", "0.5.", "-1.0."],
     "ARI compares co-membership of pairs, not label names."),
    task("Transfer: label-invariant cluster evaluation",
         "data is [points, reference labels]. Fit KMeans(n_clusters=2, n_init=10, random_state=7). Return [ARI of the labels, ARI of the swapped labels 1 - labels, best accuracy over both namings], rounded to 6 places.",
         "x = np.asarray(data[0], dtype=float).reshape(-1, 1)\ntruth = np.asarray(data[1])\nlabels = KMeans(n_clusters=2, n_init=10, random_state=7).fit_predict(x)\nresult = [round(float(adjusted_rand_score(truth, labels)), 6), round(float(adjusted_rand_score(truth, 1 - labels)), 6), round(float(max(accuracy_score(truth, labels), accuracy_score(truth, 1 - labels))), 6)]",
         [([[0,0.2,10,10.3],[1,1,0,0]],[1.0,1.0,1.0]),([[0,0.2,10,10.3],[1,0,1,0]],[-0.5,-0.5,0.5]),([[0,1,2,50,51],[0,0,0,1,1]],[1.0,1.0,1.0])],
         ("adjusted_rand_score(truth, 1 - labels)","adjusted_rand_score(truth, np.zeros_like(labels))"),
         ["Cluster ids are arbitrary names.", "ARI is unchanged by swapping names.", "Accuracy needs the best matching of names."],
         'KMeans recovers the two groups perfectly; ARI is 1 whichever way the clusters are named, and best-naming accuracy is 1. When the reference labels cut across the natural groups, ARI is negative. Comparing with a constant labelling instead gives 0.',
         [[1.0,0.0,1.0],[0.0,1.0,0.0],[1.0,1.0,0.5]],
         NP+"\nfrom sklearn.cluster import KMeans\nfrom sklearn.metrics import adjusted_rand_score, accuracy_score"),
    ("Why not score clusters with plain accuracy against reference labels?", "Cluster ids are arbitrary; use label-invariant measures such as the adjusted Rand index."))

add('density-noise', 'DBSCAN: eps depends on feature scale',
    API+'sklearn.cluster.DBSCAN.html#sklearn.cluster.DBSCAN', [
    "DBSCAN groups points that have at least min_samples neighbours within distance eps, called core points, plus points reachable from them. Points in no dense region are labelled -1, noise. The number of clusters is not fixed in advance.",
    "eps is a distance in the units of the features. The same eps can merge everything on one scale and isolate every point on another. Standardizing features first makes eps comparable across features, but it still has to be tuned for the data.",
    "core_sample_indices_ lists the core points; border points belong to a cluster without being core. A k-distance plot (distance to the k-th neighbour, sorted) is a common way to pick eps.",
    "The transfer clusters the same points before and after standardization with a fixed eps."
    ],
    ("What label does DBSCAN give a point that belongs to no dense region?",
     "-1, meaning noise.",
     ["0, the first cluster.", "A new singleton cluster id.", "It raises an error."],
     "DBSCAN explicitly reports noise rather than forcing every point into a cluster."),
    task("Transfer: eps under two scales",
         "data is a 2-D list. Run DBSCAN(eps=0.5, min_samples=2) on the raw and the standardized data. Return [raw labels, standardized labels, number of raw core samples].",
         "x = np.asarray(data, dtype=float)\nraw = DBSCAN(eps=0.5, min_samples=2).fit(x)\nscaled = DBSCAN(eps=0.5, min_samples=2).fit(StandardScaler().fit_transform(x))\nresult = [raw.labels_.tolist(), scaled.labels_.tolist(), int(len(raw.core_sample_indices_))]",
         [([[0],[0.3],[5],[5.2],[20]],[[0,0,1,1,-1],[0,0,1,1,-1],4]),([[0],[1],[2],[3]],[[-1,-1,-1,-1],[-1,-1,-1,-1],0]),([[0],[3],[6],[100]],[[-1,-1,-1,-1],[0,0,0,-1],0])],
         ("DBSCAN(eps=0.5, min_samples=2).fit(x)","DBSCAN(eps=5.0, min_samples=2).fit(x)"),
         ["eps is measured in feature units.", "Points without dense neighbourhoods are -1.", "Standardizing changes the distances eps is compared with."],
         'Raw points 0 and 0.3, and 5 and 5.2, are within 0.5 of each other, forming two clusters with 20 as noise. For 0, 3, 6, 100, raw spacing exceeds eps so everything is noise, but after standardization the first three are close and form a cluster. A larger raw eps merges the first two groups.',
         [[[0,0,0,0,-1],[0,0,1,1,-1],4],[[0,0,1,1,-1],[0,0,0,0,-1],4],[[0,0,1,1,2],[0,0,1,1,2],5]],
         NP+"\nfrom sklearn.cluster import DBSCAN\nfrom sklearn.preprocessing import StandardScaler"),
    ("Why must eps be chosen after deciding on feature scaling?", "eps is a distance in feature units; rescaling the features changes which points are neighbours."))

add('novelty-detection', 'LocalOutlierFactor with novelty=True for new observations',
    API+'sklearn.neighbors.LocalOutlierFactor.html#sklearn.neighbors.LocalOutlierFactor', [
    "Outlier detection looks for unusual points within the training data itself; novelty detection trains on clean data and asks whether new observations differ from it. The two tasks need different usage.",
    "LocalOutlierFactor compares each point's local density with its neighbours'. With novelty=False (the default), it only labels the training set via fit_predict. With novelty=True, it exposes predict, decision_function and score_samples for new data, returning 1 for inliers and -1 for novelties.",
    "Calling predict on a model fitted with novelty=False is an error, which prevents silently scoring new data with the wrong procedure. Scale features first, and validate thresholds on held-out normal and abnormal examples where available.",
    "The transfer fits on evenly spaced normal points and classifies new queries inside and outside that range."
    ],
    ("What does LocalOutlierFactor(novelty=True).predict return for a new point far from the training data?",
     "-1, marking it as a novelty.",
     ["0.", "The distance to the nearest neighbour.", "It raises, because LOF cannot score new points."],
     "novelty=True enables predict for new observations; 1 is inlier and -1 novelty."),
    task("Transfer: score new observations",
         "data is a list of query values. Fit LocalOutlierFactor(n_neighbors=5, novelty=True) on 21 evenly spaced points in [0, 1]. Return predict for the queries.",
         "train = np.linspace(0, 1, 21).reshape(-1, 1)\nnovelty = LocalOutlierFactor(n_neighbors=5, novelty=True).fit(train)\nqueries = np.asarray(data, dtype=float).reshape(-1, 1)\nresult = novelty.predict(queries).tolist()",
         [([0.5,5,-3],[1,-1,-1]),([0.25],[1]),([2,0.9],[-1,1])],
         ("novelty=True","novelty=False"),
         ["Fit only on normal data.", "predict returns 1 for inliers and -1 for novelties.", "predict is unavailable when novelty=False."],
         "0.5 sits inside the training range and is an inlier; 5 and -3 are far outside. With novelty=False the model cannot score new points at all.",
         [[1,1,1],[-1,-1,-1],[1,-1,1]],
         NP+"\nfrom sklearn.neighbors import LocalOutlierFactor"),
    ("Outlier versus novelty detection?", "Outlier detection labels the training data; novelty detection trains on clean data and scores new points (novelty=True)."))

add('permutation-importance', 'Permutation importance on held-out data',
    SK+'modules/permutation_importance.html#permutation-feature-importance', [
    "Permutation importance shuffles one feature's values and measures how much the model's score drops. A large drop means the model relies on that feature; no drop means it does not.",
    "Compute it on held-out data. On training data, an overfitted model can appear to rely on features that do not help it generalize. n_repeats averages several shuffles and gives a spread to report.",
    "Correlated features share importance: shuffling one leaves the other to carry the signal, so both can look unimportant. Importance describes the model, not causal effects in the world.",
    "The transfer fits a linear model where only one feature matters and measures importance on a held-out split."
    ],
    ("Why compute permutation importance on held-out data?",
     "Training-set importance can reflect overfitting rather than what helps the model generalize.",
     ["Shuffling is only possible on test data.", "It is faster on smaller sets.", "Training data has no features."],
     "Importance should describe the model's behaviour on data it was not fitted to."),
    task("Transfer: which feature matters?",
         "data is a seed. Generate 200 rows with a signal and a noise feature and y = 3·signal + small noise. Fit LinearRegression on the first 150 rows and compute permutation importance on the last 50 (n_repeats=5). Return [index of the most important feature, noise importance < 0.05, signal importance > 1].",
         "rng = np.random.default_rng(data)\nsignal = rng.normal(size=200)\nnoise = rng.normal(size=200)\nx = np.column_stack([signal, noise])\ny = 3 * signal + rng.normal(scale=0.1, size=200)\nmodel = LinearRegression().fit(x[:150], y[:150])\nimp = permutation_importance(model, x[150:], y[150:], n_repeats=5, random_state=7)\nresult = [int(np.argmax(imp.importances_mean)), bool(imp.importances_mean[1] < 0.05), bool(imp.importances_mean[0] > 1.0)]",
         [(0,[0,True,True]),(1,[0,True,True]),(2,[0,True,True])],
         ("y = 3 * signal","y = 3 * noise"),
         ["Shuffle each feature on the held-out rows.", "The score drop measures reliance on that feature.", "An unused feature has importance near zero."],
         "Shuffling the signal destroys the R² on held-out rows, so its importance is large; shuffling the noise changes almost nothing. If the target depended on the noise column instead, the ranking would flip.",
         [[1,True,True],[0,False,True],[0,True,False]],
         NP+"\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.inspection import permutation_importance"),
    ("What does permutation importance measure?", "The drop in a held-out score when one feature's values are shuffled; it describes the model, not causation."))

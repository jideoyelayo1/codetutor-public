"""Original Stage 16 supervised-learning depth: scikit-learn 1.7 sections with executed transfer practice."""
from python_guide_depth import add, task

NP = "import numpy as np"
SK = 'https://scikit-learn.org/1.7/'
API = SK+'modules/generated/'

add('standard-scaler', 'StandardScaler: with_mean, zero-variance columns and inverse_transform',
    API+'sklearn.preprocessing.StandardScaler.html#sklearn.preprocessing.StandardScaler', [
    "StandardScaler centres each column on its training mean and divides by its training standard deviation. Models that use distances or gradient-based optimization, such as k-nearest neighbours, SVMs and regularized linear models, are sensitive to feature scale; tree models are not.",
    "with_mean=False skips centring and only divides by the standard deviation. It is required for sparse input, where subtracting a mean would fill every zero, but it changes the transformed values, so it must be a deliberate choice.",
    "A column with zero variance is left with scale 1, so it becomes all zeros after centring rather than dividing by zero. inverse_transform maps scaled values back to original units, which is how predictions or cluster centres are reported to people.",
    "The transfer scales a matrix with a constant column and checks the inverse round trip."
    ],
    ("Why does StandardScaler offer with_mean=False?",
     "Centring sparse data would turn its zeros into non-zeros and destroy sparsity.",
     ["To make the scaler run faster on dense data.", "To avoid dividing by the standard deviation.", "Because centring is never useful."],
     "Without centring, only the division by the standard deviation remains."),
    task("Transfer: scale and invert",
         "data is a 2-D list. Fit StandardScaler. Return [scale_ rounded to 6 places, transformed values rounded to 6 places, whether inverse_transform recovers the input].",
         "x = np.asarray(data, dtype=float)\nscaler = StandardScaler().fit(x)\nz = scaler.transform(x)\nresult = [scaler.scale_.round(6).tolist(), z.round(6).tolist(), bool(np.allclose(scaler.inverse_transform(z), x))]",
         [([[1,5],[3,5]],[[1.0,1.0],[[-1.0,0.0],[1.0,0.0]],True]),([[0],[2],[4]],[[1.632993],[[-1.224745],[0.0],[1.224745]],True]),([[2,4]],[[1.0,1.0],[[0.0,0.0]],True])],
         ("StandardScaler()","StandardScaler(with_mean=False)"),
         ["scale_ is the population standard deviation, or 1 for a constant column.", "Centring subtracts the training mean.", "inverse_transform multiplies back and adds the mean."],
         "Column one has mean 2 and standard deviation 1, giving -1 and 1; the constant column becomes zeros with scale 1. The inverse recovers the input. Skipping centring would only divide, leaving 1 and 3 unchanged.",
         [[[1.0,0.0],[[-1.0,0.0],[1.0,0.0]],True],[[1.0,1.0],[[1.0,5.0],[3.0,5.0]],True],[[1.0,1.0],[[-1.0,0.0],[1.0,0.0]],False]],
         NP+"\nfrom sklearn.preprocessing import StandardScaler"),
    ("Which model families need feature scaling, and which do not?", "Distance- and gradient-based models (kNN, SVM, regularized linear) need it; trees do not."))

add('median-imputer', 'SimpleImputer: fitted statistics and add_indicator',
    API+'sklearn.impute.SimpleImputer.html#sklearn.impute.SimpleImputer', [
    "SimpleImputer learns a replacement value per column during fit, such as the median, and uses it during transform. The median is robust to outliers; the mean of [1, 2, 100] is pulled to about 34.",
    "add_indicator=True appends a 0/1 column marking which values were missing, so a model can learn whether missingness itself is informative. By default the indicator is only added for columns that had missing values during fit.",
    "Fit the imputer on training data only and apply it unchanged to new data, ideally inside a Pipeline so cross-validation refits it per fold. Inspect statistics_ to see the learned replacements.",
    "The transfer imputes test values with training medians and shows when the missing-value indicator appears."
    ],
    ("A column had no missing values during fit. Does SimpleImputer(add_indicator=True) add an indicator for it?",
     "No; by default indicators are added only for columns that had missing values in training.",
     ["Yes, every column always gets an indicator.", "Only if the test data has missing values.", "It raises an error."],
     "features='missing-only' is the default for the indicator."),
    task("Transfer: impute with a learned median",
         "data is [train, test] value lists with None for missing. Fit SimpleImputer(strategy='median', add_indicator=True) on train. Return [learned median, transformed test rows].",
         "def column(values):\n    return np.array([np.nan if v is None else v for v in values], dtype=float).reshape(-1, 1)\ntrain, test = (column(v) for v in data)\nimputer = SimpleImputer(strategy='median', add_indicator=True).fit(train)\nresult = [float(imputer.statistics_[0]), imputer.transform(test).tolist()]",
         [([[1,2,100,None],[None,5]],[2.0,[[2.0,1.0],[5.0,0.0]]]),([[1,3],[None]],[2.0,[[2.0]]]),([[None,4,6,8],[7]],[6.0,[[7.0,0.0]]])],
         ("strategy='median'","strategy='mean'"),
         ["The median ignores the outlier 100.", "The indicator marks imputed positions with 1.", "Without training gaps, no indicator column is added."],
         "The training median 2 fills the missing test value and the indicator marks it. A training column without gaps gets no indicator. The mean would be pulled to about 34.3 by the outlier.",
         [[34.333333,[[34.333333,1.0],[5.0,0.0]]],[2.0,[[2.0],[5.0]]],[2.0,[[2.0,0.0],[5.0,1.0]]]],
         NP+"\nfrom sklearn.impute import SimpleImputer"),
    ("What does add_indicator=True add?", "A 0/1 column per feature that had missing training values, marking which entries were imputed."))

add('one-hot-unknown', 'OneHotEncoder: feature names and the unknown-category policy',
    API+'sklearn.preprocessing.OneHotEncoder.html#sklearn.preprocessing.OneHotEncoder', [
    "OneHotEncoder learns the categories seen during fit and creates one 0/1 column for each. get_feature_names_out reports names such as color_blue, which keep model inputs traceable.",
    "A category that never appeared in training must be handled at prediction time. The default handle_unknown='error' raises ValueError, which is safe but can break a production service. handle_unknown='ignore' encodes it as all zeros, an explicit 'none of the known categories' representation.",
    "Whichever policy you choose, monitor how often unknown categories occur: a rising rate signals drift. Rare categories can be grouped with min_frequency so the encoder does not create columns for one-off values.",
    "The transfer encodes known and unknown colours under both policies."
    ],
    ("OneHotEncoder(handle_unknown='ignore') sees a new category at transform time. What does it output?",
     "A row of all zeros for that feature's columns.",
     ["A new column for the category.", "A ValueError.", "The encoding of the most frequent category."],
     "Ignored unknowns map to no known category; the default policy raises instead."),
    task("Transfer: encode with an unknown policy",
         "data is [train categories, test categories]. Fit a tolerant encoder (handle_unknown='ignore') and a strict default encoder. Return [feature names with prefix 'color', tolerant test encoding, 'ok' or 'unknown-rejected' for the strict encoder].",
         "encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False).fit(np.array(data[0]).reshape(-1, 1))\nstrict = OneHotEncoder(sparse_output=False).fit(np.array(data[0]).reshape(-1, 1))\ntry:\n    strict.transform(np.array(data[1]).reshape(-1, 1))\n    strict_result = 'ok'\nexcept ValueError:\n    strict_result = 'unknown-rejected'\nresult = [encoder.get_feature_names_out(['color']).tolist(), encoder.transform(np.array(data[1]).reshape(-1, 1)).tolist(), strict_result]",
         [([['red','blue','red'],['blue','green']],[['color_blue','color_red'],[[1.0,0.0],[0.0,0.0]],'unknown-rejected']),([['a'],['a']],[['color_a'],[[1.0]],'ok']),([['x','y'],['y']],[['color_x','color_y'],[[0.0,1.0]],'ok'])],
         ("handle_unknown='ignore', ",""),
         ["Categories are learned during fit, sorted.", "An ignored unknown becomes all zeros.", "The default policy raises ValueError for unknowns."],
         "Blue encodes as [1, 0] and the unseen green as all zeros, while the strict encoder rejects green. Without the ignore policy, the first encoder would raise too.",
         [[['color_red','color_blue'],[[1.0,0.0],[0.0,0.0]],'unknown-rejected'],[['color_blue','color_red'],[[1.0,0.0],[0.0,1.0]],'unknown-rejected'],[['color_blue','color_red'],[[1.0,0.0],[0.0,0.0]],'ok']],
         NP+"\nfrom sklearn.preprocessing import OneHotEncoder"),
    ("What is OneHotEncoder's default handle_unknown, and its risk?", "'error': safe, but an unseen category raises at prediction time."))

add('column-transformer', 'ColumnTransformer: heterogeneous columns with named outputs',
    SK+'modules/compose.html#columntransformer-for-heterogeneous-data', [
    "Real tables mix numeric and categorical columns that need different preprocessing. ColumnTransformer applies each transformer to its own named columns and concatenates the outputs.",
    "get_feature_names_out prefixes each output with its transformer's name, such as num__age and cat__city_a, so model coefficients and importances can be traced back to inputs.",
    "Columns not listed are dropped by default (remainder='drop'); pass remainder='passthrough' only when unlisted columns are genuinely ready to use. Put the ColumnTransformer inside a Pipeline with the model so every step is fitted on training folds only.",
    "The transfer scales a numeric column and one-hot encodes a categorical column from a DataFrame."
    ],
    ("What happens to a column that a ColumnTransformer does not mention?",
     "It is dropped, because remainder='drop' is the default.",
     ["It is passed through unchanged.", "It is one-hot encoded automatically.", "It raises an error."],
     "List every column you need, or set remainder explicitly."),
    task("Transfer: mixed-type preprocessing",
         "data is a list of [age, city] rows. Scale age and one-hot encode city in a ColumnTransformer. Return [output feature names, transformed rows rounded to 6 places].",
         "frame = pd.DataFrame(data, columns=['age', 'city'])\ntransform = ColumnTransformer([('num', StandardScaler(), ['age']), ('cat', OneHotEncoder(sparse_output=False), ['city'])])\nout = transform.fit_transform(frame)\nresult = [transform.get_feature_names_out().tolist(), out.round(6).tolist()]",
         [([[20,'a'],[40,'b']],[['num__age','cat__city_a','cat__city_b'],[[-1.0,1.0,0.0],[1.0,0.0,1.0]]]),([[30,'x']],[['num__age','cat__city_x'],[[0.0,1.0]]]),([[1,'p'],[3,'q'],[5,'p']],[['num__age','cat__city_p','cat__city_q'],[[-1.224745,1.0,0.0],[0.0,0.0,1.0],[1.224745,1.0,0.0]]])],
         ("('num', StandardScaler(), ['age'])","('num', 'passthrough', ['age'])"),
         ["Each transformer receives only its listed columns.", "Output names carry the transformer prefix.", "Outputs are concatenated in transformer order."],
         "Ages 20 and 40 scale to -1 and 1, followed by one-hot city columns. Passing age through unscaled would leave 20 and 40 in the first column.",
         [[['age','city_a','city_b'],[[-1.0,1.0,0.0],[1.0,0.0,1.0]]],[['num__age','cat__city_a','cat__city_b'],[[20.0,1.0,0.0],[40.0,0.0,1.0]]],[['num__age','cat__city_a','cat__city_b'],[[-1.0,0.0,1.0],[1.0,1.0,0.0]]]],
         "import pandas as pd\nfrom sklearn.compose import ColumnTransformer\nfrom sklearn.preprocessing import StandardScaler, OneHotEncoder"),
    ("Why use get_feature_names_out after a ColumnTransformer?", "To trace each model input back to its source column and transformer."))

add('pipeline-fit', 'Pipeline: cross_val_score fits clones, not your object',
    SK+'modules/compose.html#pipeline-chaining-estimators', [
    "A Pipeline chains preprocessing and a final estimator into one object. Fitting it fits each step in order on the same training data; predicting applies the fitted steps in order. Inside cross-validation, every fold refits the whole chain on that fold's training part, which prevents preprocessing leakage.",
    "cross_val_score clones the estimator for each fold. The object you passed in is not fitted afterwards. Call fit separately to obtain the final model, typically on all training data once evaluation is done.",
    "named_steps gives access to fitted steps, for example to read the learned scaler mean or the model coefficients. Step names default to the lower-cased class names when you use make_pipeline.",
    "The transfer cross-validates a pipeline, then fits it and inspects the learned scaler mean and predictions at the extremes."
    ],
    ("After cross_val_score(model, x, y), is model fitted?",
     "No; cross_val_score fits clones in each fold and leaves the original unfitted.",
     ["Yes, on the last fold.", "Yes, on all the data.", "Only its preprocessing steps are fitted."],
     "Fit the final model explicitly after evaluation."),
    task("Transfer: evaluate, then fit the final pipeline",
         "data is [x values, labels]. Cross-validate make_pipeline(StandardScaler(), LogisticRegression()) with cv=2, then fit it on all data. Return [number of CV scores, learned scaler mean rounded to 6 places, predictions at min(x) and max(x)].",
         "x = np.asarray(data[0], dtype=float).reshape(-1, 1)\ny = np.asarray(data[1])\nmodel = make_pipeline(StandardScaler(), LogisticRegression())\nscores = cross_val_score(model, x, y, cv=2)\nmodel.fit(x, y)\nresult = [len(scores), round(float(model.named_steps['standardscaler'].mean_[0]), 6), model.predict([[min(data[0])], [max(data[0])]]).tolist()]",
         [([[-3,-2,-1,1,2,3],[0,0,0,1,1,1]],[2,0.0,[0,1]]),([[0,1,2,10,11,12],[0,0,0,1,1,1]],[2,6.0,[0,1]]),([[5,6,7,8],[1,1,0,0]],[2,6.5,[1,0]])],
         ("model.fit(x, y)\n",""),
         ["cross_val_score returns one score per fold.", "Fit the pipeline yourself after evaluating.", "named_steps uses lower-cased class names."],
         "Two folds give two scores; the final fit learns the mean of all x values and predicts the classes at both extremes. Skipping the explicit fit leaves the scaler unfitted, so reading mean_ fails.",
         [[1,0.0,[0,1]],[2,0.0,[1,0]],[2,1.0,[0,1]]],
         NP+"\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.model_selection import cross_val_score"),
    ("Why fit preprocessing inside a Pipeline during cross-validation?", "Each fold refits preprocessing on its own training part, so validation data never influences it."))

add('linear-regression', 'LinearRegression: coefficients, intercept and R²',
    API+'sklearn.linear_model.LinearRegression.html#sklearn.linear_model.LinearRegression', [
    "LinearRegression finds coefficients and an intercept minimizing squared error. coef_ is the change in prediction per unit change of each feature, and intercept_ is the prediction when all features are zero.",
    "score returns R², the fraction of target variance explained relative to predicting the mean. R² of 1 is a perfect fit; 0 is no better than the mean; on new data it can be negative.",
    "fit_intercept=False forces predictions through the origin. Only use it when theory demands a zero intercept; otherwise the slope absorbs the missing offset and the fit degrades. Evaluate R² on held-out data, not just the training set.",
    "The transfer fits lines with and without an intercept and compares their training R²."
    ],
    ("What does an R² of 0 mean?",
     "The model explains no more variance than always predicting the mean of the target.",
     ["The model's predictions are all zero.", "The model fits perfectly.", "The coefficients are zero."],
     "R² compares squared error with that of the constant mean predictor."),
    task("Transfer: with and without an intercept",
         "data is [x values, y values]. Fit LinearRegression with and without an intercept. Return [slope, intercept, R² with intercept, R² without intercept], rounded to 6 places.",
         "x = np.asarray(data[0], dtype=float).reshape(-1, 1)\ny = np.asarray(data[1], dtype=float)\nwith_b = LinearRegression().fit(x, y)\nwithout_b = LinearRegression(fit_intercept=False).fit(x, y)\nresult = [round(float(with_b.coef_[0]), 6), round(float(with_b.intercept_), 6), round(float(with_b.score(x, y)), 6), round(float(without_b.score(x, y)), 6)]",
         [([[0,1,2],[1,3,5]],[2.0,1.0,1.0,0.85]),([[1,2,3,4],[2,4,6,8]],[2.0,0.0,1.0,1.0]),([[0,1,2,3],[0,1,1,2]],[0.6,0.1,0.9,0.892857])],
         ("with_b = LinearRegression().fit(x, y)","with_b = LinearRegression(fit_intercept=False).fit(x, y)"),
         ["coef_ is the slope; intercept_ the offset.", "R² compares with the mean predictor.", "Forcing the line through zero lowers R² when the data has an offset."],
         "y = 2x + 1 fits exactly with an intercept. Through the origin, the best slope is 2.6 and R² drops to 0.85. When the data truly passes through zero, both fits agree.",
         [[2.6,0.0,0.85,0.85],[2.0,1.0,1.0,1.0],[2.0,1.0,0.85,1.0]],
         NP+"\nfrom sklearn.linear_model import LinearRegression"),
    ("When is fit_intercept=False appropriate?", "Only when theory requires predictions to be zero when all features are zero."))

add('ridge-shrinkage', 'Ridge: the coefficient path and the unpenalized intercept',
    API+'sklearn.linear_model.Ridge.html#sklearn.linear_model.Ridge', [
    "Ridge regression minimizes squared error plus alpha times the sum of squared coefficients. Larger alpha shrinks coefficients toward zero, trading a little bias for lower variance and more stable estimates with correlated features.",
    "For one centred feature, the ridge slope is Σxy / (Σx² + alpha): as alpha grows, the slope shrinks smoothly toward zero but never exactly reaches it. Tracing coefficients over a range of alphas, the regularization path, shows this monotone shrinkage.",
    "The intercept is not penalized, so heavy regularization pulls predictions toward the mean of y rather than toward zero. Penalties depend on feature scale, so standardize features before comparing alphas or coefficients.",
    "The transfer computes slopes for increasing alpha and checks shrinkage and the intercept."
    ],
    ("With very large alpha, what does a ridge model predict for every input?",
     "Approximately the mean of the training targets, because slopes shrink toward zero but the intercept is unpenalized.",
     ["Zero.", "The largest training target.", "It raises a convergence error."],
     "Shrinking slopes leaves only the intercept, which fits the target mean."),
    task("Transfer: trace the ridge path",
         "data is a list of x values; y = 2x + 5. Return [slopes for alpha 0, 1, 10, 1000 rounded to 4 places, whether their magnitudes never increase, intercept at alpha 1000 rounded to 4 places].",
         "x = np.asarray(data, dtype=float).reshape(-1, 1)\ny = 2 * x.ravel() + 5\npath = [round(float(Ridge(alpha=a).fit(x, y).coef_[0]), 4) for a in (0.0, 1.0, 10.0, 1000.0)]\nintercept = round(float(Ridge(alpha=1000.0).fit(x, y).intercept_), 4)\nresult = [path, all(abs(b) <= abs(a) for a, b in zip(path, path[1:])), intercept]",
         [([-2,-1,1,2],[[2.0,1.8182,1.0,0.0198],True,5.0]),([0,1,2,3],[[2.0,1.6667,0.6667,0.01],True,7.9851]),([-1,1],[[2.0,1.3333,0.3333,0.004],True,5.0])],
         ("y = 2 * x.ravel() + 5","y = 2 * x.ravel()"),
         ["Ridge slope = Σ(x - x̄)y / (Σ(x - x̄)² + alpha).", "Larger alpha shrinks the slope monotonically.", "The intercept is not penalized."],
         "For x = -2, -1, 1, 2, Σx² = 10, so the slopes are 20/10, 20/11, 20/20 and 20/1010, and the intercept stays at the mean of y, 5. Without the +5 offset the intercept would be 0.",
         [[[2.0,1.8182,1.0,0.0198],True,0.0],[[2.0,2.0,2.0,2.0],True,5.0],[[2.0,1.8182,1.0,0.0198],False,5.0]],
         NP+"\nfrom sklearn.linear_model import Ridge"),
    ("Is the ridge intercept penalized?", "No; only coefficients are shrunk, so strong regularization drives predictions toward the target mean."))

add('lasso-sparsity', 'Lasso versus Ridge: exact zeros for irrelevant features',
    API+'sklearn.linear_model.Lasso.html#sklearn.linear_model.Lasso', [
    "Lasso penalizes the sum of absolute coefficients. Unlike the squared ridge penalty, the absolute value has a corner at zero, so for a sufficiently large alpha, coefficients of weakly useful features become exactly zero. This performs feature selection as part of fitting.",
    "Ridge shrinks coefficients but leaves them non-zero, so every feature keeps some influence. With many irrelevant features, Lasso produces a sparse, interpretable model; with groups of correlated useful features, it tends to pick one arbitrarily, where Elastic Net is often steadier.",
    "Lasso also shrinks the coefficients it keeps, so the surviving coefficient is slightly smaller than the true effect. Choose alpha by cross-validation (LassoCV) and standardize features first.",
    "The transfer fits Lasso and Ridge to data where only one of three features matters."
    ],
    ("Why can Lasso set coefficients exactly to zero while Ridge does not?",
     "The absolute-value penalty has a corner at zero, so small coefficients are pulled exactly onto it.",
     ["Lasso uses a larger alpha by default.", "Ridge cannot fit more than one feature.", "Lasso removes features with missing values."],
     "The L1 geometry produces sparse solutions; the L2 penalty only shrinks."),
    task("Transfer: sparse versus shrunk coefficients",
         "data is a seed. Generate 50 rows of 3 standard-normal features with y = 3·x0 + small noise. Fit Lasso(alpha=0.1) and Ridge(alpha=0.1). Return [Lasso zero coefficients, Ridge zero coefficients, Lasso coefficient for x0 rounded to 1 place].",
         "rng = np.random.default_rng(data)\nx = rng.normal(size=(50, 3))\ny = 3 * x[:, 0] + rng.normal(scale=0.1, size=50)\nlasso = Lasso(alpha=0.1).fit(x, y)\nridge = Ridge(alpha=0.1).fit(x, y)\nresult = [int(np.sum(lasso.coef_ == 0)), int(np.sum(ridge.coef_ == 0)), round(float(lasso.coef_[0]), 1)]",
         [(0,[2,0,2.9]),(1,[2,0,2.9]),(2,[2,0,2.9])],
         ("Lasso(alpha=0.1)","Lasso(alpha=0.0001)"),
         ["Only x0 influences y.", "Lasso can return exact zeros.", "Ridge keeps every coefficient non-zero."],
         "For every seed, Lasso sets both irrelevant coefficients exactly to zero and keeps x0 at about 2.9, slightly below the true 3 because the penalty also shrinks it. Ridge leaves all three non-zero. A tiny alpha would keep every coefficient non-zero as well.",
         [[0,0,3.0],[2,2,2.9],[1,0,2.9]],
         NP+"\nfrom sklearn.linear_model import Lasso, Ridge"),
    ("What does Lasso do to irrelevant features at a suitable alpha?", "Sets their coefficients exactly to zero; Ridge only shrinks them."))

add('nearest-neighbors', 'KNeighborsClassifier: unscaled features dominate distances',
    API+'sklearn.neighbors.KNeighborsClassifier.html#sklearn.neighbors.KNeighborsClassifier', [
    "k-nearest neighbours predicts from the closest training points under a distance metric. With Euclidean distance, a feature measured in tens of thousands, such as income, outweighs one measured in tens, such as age, regardless of which matters more.",
    "Standardizing features puts them on comparable scales, so each contributes according to its spread rather than its units. The same query can then have a different nearest neighbour and a different predicted class.",
    "k, the distance metric and the feature scaling are all modelling choices; tune them with cross-validation inside a pipeline. kNN stores the training set, so prediction cost and memory grow with data size.",
    "The transfer classifies a query with and without standardization where the two disagree."
    ],
    ("Income ranges over thousands and age over tens. What dominates an unscaled Euclidean distance?",
     "Income, because its numeric differences are far larger.",
     ["Age, because it has fewer distinct values.", "Both equally.", "Neither; kNN normalizes automatically."],
     "Scale features so distances reflect comparable units."),
    task("Transfer: scaling changes the nearest neighbour",
         "data is [training points, labels, query]. Predict the query's class with 1-NN on raw features and with a StandardScaler + 1-NN pipeline. Return [raw prediction, scaled prediction].",
         "x = np.asarray(data[0], dtype=float)\ny = np.asarray(data[1])\nquery = np.asarray([data[2]], dtype=float)\nraw = KNeighborsClassifier(n_neighbors=1).fit(x, y).predict(query)[0]\nscaled = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1)).fit(x, y).predict(query)[0]\nresult = [int(raw), int(scaled)]",
         [([[[50000,20],[51000,60]],[0,1],[50900,21]],[1,0]),([[[0,0],[10,10]],[0,1],[1,1]],[0,0]),([[[0,0],[10,10]],[0,1],[9,9]],[1,1])],
         ("make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))","KNeighborsClassifier(n_neighbors=1)"),
         ["Raw distance is dominated by income.", "After scaling, the 39-year age gap matters.", "Comparable scales give comparable influence."],
         "Unscaled, the query is 100 income units from the second point versus 900 from the first, so income decides. After standardization, the age difference outweighs the income difference and the first point is nearer.",
         [[0,0],[1,1],[0,1]],
         NP+"\nfrom sklearn.neighbors import KNeighborsClassifier\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.preprocessing import StandardScaler"),
    ("Why scale features before kNN?", "Distances otherwise reflect units, letting large-range features dominate."))

add('support-vectors', 'SVC: support vectors and the role of C',
    API+'sklearn.svm.SVC.html#sklearn.svm.SVC', [
    "A linear support vector classifier finds the separating boundary with the widest margin. Only the points nearest the boundary, the support vectors, determine it; moving other points slightly does not change the model.",
    "C controls the penalty for margin violations. Large C insists on classifying training points correctly, giving a narrow margin decided by a few support vectors. Small C allows violations, widening the margin and making many points support vectors.",
    "decision_function returns the signed distance-like score; its sign is the predicted side. With separable one-dimensional data, the boundary lies midway between the closest points of each class. Scale features first, as with any distance-based method.",
    "The transfer fits a hard-margin linear SVC and inspects its support vectors and decision signs near the boundary."
    ],
    ("With very large C on separable data, which points determine a linear SVC's boundary?",
     "The closest points of each class to the boundary, the support vectors.",
     ["Every training point equally.", "The points farthest from the boundary.", "The class means."],
     "Only support vectors enter the solution."),
    task("Transfer: a hard-margin boundary",
         "data is a list of x values; labels are x > 0. Fit SVC(kernel='linear', C=1000). Return [support-vector count per class, sign of decision_function at -0.1 and 0.1, sorted support-vector values].",
         "x = np.asarray(data, dtype=float).reshape(-1, 1)\ny = (x.ravel() > 0).astype(int)\nmodel = SVC(kernel='linear', C=1000).fit(x, y)\nresult = [model.n_support_.tolist(), np.sign(model.decision_function([[-0.1], [0.1]])).astype(int).tolist(), sorted(model.support_vectors_.ravel().tolist())]",
         [([-3,-1,2,5],[[1,1],[-1,-1],[-1.0,2.0]]),([-2,-1,1,2],[[1,1],[-1,1],[-1.0,1.0]]),([-4,1],[[1,1],[1,1],[-4.0,1.0]])],
         ("C=1000","C=0.001"),
         ["Support vectors are the closest points from each class.", "The boundary sits midway between them.", "Small C lets many points violate the margin."],
         "The closest points of each class, -1 and 2, are the only support vectors, so the boundary sits at 0.5: both -0.1 and 0.1 fall on the negative side. With symmetric data the boundary is at 0, and with -4 and 1 it is at -1.5. A tiny C makes every point a support vector.",
         [[[2,2],[-1,-1],[-3.0,-1.0,2.0,5.0]],[[1,1],[-1,1],[-1.0,2.0]],[[1,1],[-1,-1],[-3.0,5.0]]],
         NP+"\nfrom sklearn.svm import SVC"),
    ("What does a small C do in an SVM?", "Allows more margin violations, widening the margin and increasing the number of support vectors."))

add('decision-tree', 'DecisionTreeClassifier: unlimited depth memorizes noise',
    API+'sklearn.tree.DecisionTreeClassifier.html#sklearn.tree.DecisionTreeClassifier', [
    "A decision tree splits the feature space with threshold rules until its leaves are pure or a limit is reached. With no limit, it can isolate every training point, including mislabelled ones, and reach perfect training accuracy.",
    "Perfect training accuracy is not evidence of a good model. Leaves built around noisy points give wrong predictions in their neighbourhoods on new data. Limiting max_depth or min_samples_leaf forces the tree to capture broad structure instead.",
    "get_depth reports how deep the fitted tree grew. Compare training and held-out scores: a large gap signals overfitting. Ensembles such as random forests and boosting reduce the variance of individual deep trees.",
    "The transfer fits a deep tree and a stump to labels with two noisy points and compares their held-out accuracy."
    ],
    ("A deep decision tree reaches 100% training accuracy on noisy labels. What should you expect on new data?",
     "Lower accuracy, because some leaves encode the noise.",
     ["100%, because the tree is perfect.", "Exactly the same as a depth-one tree.", "50%, always."],
     "Training accuracy of a fully grown tree says little about generalization."),
    task("Transfer: deep tree versus stump",
         "data is [train x, train y, test x, test y]. Fit an unlimited tree and a depth-1 tree. Return [deep tree depth, deep train accuracy, deep test accuracy, stump test accuracy].",
         "x_train, y_train, x_test, y_test = (np.asarray(v) for v in data)\nx_train, x_test = x_train.reshape(-1, 1), x_test.reshape(-1, 1)\ndeep = DecisionTreeClassifier(random_state=7).fit(x_train, y_train)\nstump = DecisionTreeClassifier(max_depth=1, random_state=7).fit(x_train, y_train)\nresult = [deep.get_depth(), float(deep.score(x_train, y_train)), float(deep.score(x_test, y_test)), float(stump.score(x_test, y_test))]",
         [([[0,1,2,3,4,5,6,7],[0,0,0,1,0,1,1,1],[3.2,4.2,1.5,6.5],[0,1,0,1]],[3,1.0,0.5,0.75]),([[0,1,2,3],[0,0,1,1],[0.5,2.5],[0,1]],[1,1.0,1.0,1.0]),([[0,1,2,3,4,5],[0,1,0,1,0,1],[0.2,4.8],[0,1]],[5,1.0,1.0,1.0])],
         ("deep = DecisionTreeClassifier(random_state=7)","deep = DecisionTreeClassifier(max_depth=1, random_state=7)"),
         ["An unlimited tree splits until its leaves are pure.", "Noisy points get their own leaves.", "Compare held-out accuracy, not training accuracy."],
         "The unlimited tree grows to depth 3 to isolate the two noisy labels at 3 and 4, reaching perfect training accuracy, but misclassifies 3.2 and 4.2 for a test accuracy of 0.5; the stump scores 0.75. On clean data both trees agree. Capping the deep tree at depth 1 turns it into the stump.",
         [[3,1.0,1.0,0.75],[1,0.875,0.75,0.75],[3,1.0,0.75,0.5]],
         NP+"\nfrom sklearn.tree import DecisionTreeClassifier"),
    ("What does a large train/test gap in a decision tree indicate?", "Overfitting; limit depth or leaf size, or use an ensemble."))

add('random-forest', 'RandomForestClassifier: reproducibility, out-of-bag score and averaged probabilities',
    API+'sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier', [
    "A random forest trains many trees on bootstrap samples with random feature subsets and averages their predicted probabilities. Averaging reduces the variance of individual deep trees.",
    "Each tree leaves out about a third of the rows. The out-of-bag (OOB) score evaluates every row using only trees that did not see it, giving a built-in validation estimate without a separate holdout when oob_score=True.",
    "Randomness makes results depend on random_state. Fixing it makes runs reproducible: two forests with the same data and seed produce identical probabilities. Changing n_estimators changes the model, so record it with every result.",
    "The transfer fits two identically seeded forests, inspects the tree count, predictions at both ends and the OOB score."
    ],
    ("What does a random forest's out-of-bag score estimate?",
     "Generalization accuracy, by scoring each row with trees that did not train on it.",
     ["Training accuracy.", "The accuracy of the single best tree.", "The fraction of features used."],
     "Bootstrap sampling leaves rows out of each tree; those rows act as validation data for it."),
    task("Transfer: a reproducible forest",
         "data is a list of x values; labels are x >= 5. Fit two RandomForestClassifier(n_estimators=25, random_state=7, oob_score=True) models. Return [identical probabilities, tree count, predicted classes at 0 and 9, OOB score >= 0.8].",
         "x = np.asarray(data, dtype=float).reshape(-1, 1)\ny = (x.ravel() >= 5).astype(int)\na = RandomForestClassifier(n_estimators=25, random_state=7, oob_score=True).fit(x, y)\nb = RandomForestClassifier(n_estimators=25, random_state=7, oob_score=True).fit(x, y)\nproba = a.predict_proba([[0], [9]])\nresult = [bool(np.array_equal(a.predict_proba(x), b.predict_proba(x))), len(a.estimators_), proba.argmax(axis=1).tolist(), bool(a.oob_score_ >= 0.8)]",
         [(list(range(10)),[True,25,[0,1],True]),(list(range(0,10,2)) + list(range(1,10,2)),[True,25,[0,1],True]),([0,1,2,3,4,5,6,7,8,9,0,9],[True,25,[0,1],True])],
         ("a = RandomForestClassifier(n_estimators=25,","a = RandomForestClassifier(n_estimators=24,"),
         ["The same seed and data give the same forest.", "estimators_ holds one fitted tree per estimator.", "Out-of-bag rows validate each tree."],
         "Identically seeded forests produce identical probabilities, there are 25 trees, the extremes are classified correctly and the OOB estimate is high on this separable data. Changing the tree count changes the model.",
         [[False,25,[0,1],True],[True,24,[0,1],True],[True,25,[1,0],True]],
         NP+"\nfrom sklearn.ensemble import RandomForestClassifier"),
    ("How do you make a random forest reproducible?", "Fix random_state (and record n_estimators and the data); the same inputs then give identical models."))

add('gradient-boosting', 'GradientBoostingRegressor: staged predictions and the learning rate',
    API+'sklearn.ensemble.GradientBoostingRegressor.html#sklearn.ensemble.GradientBoostingRegressor', [
    "Gradient boosting starts from a constant prediction and adds small trees one at a time, each fitted to the current residuals. The learning rate scales each tree's contribution, so many small steps approach the target gradually.",
    "staged_predict yields the predictions after each stage, which shows how the training error falls as trees are added. On a step function with depth-one trees and learning rate 0.5, each stage halves the remaining residual, so the mean squared error falls by a factor of four per stage.",
    "A lower learning rate needs more trees for the same fit but usually generalizes better; n_estimators and learning_rate must be tuned together, typically with early stopping on validation data. Watching only training error hides overfitting.",
    "The transfer tracks staged training error for a boosted model on a step function."
    ],
    ("What does the learning rate in gradient boosting control?",
     "How much each new tree's correction contributes to the prediction.",
     ["The number of trees.", "The depth of each tree.", "The fraction of rows sampled."],
     "Smaller steps need more trees but are usually more robust."),
    task("Transfer: staged boosting error",
         "data is the number of stages. Fit GradientBoostingRegressor(n_estimators=data, max_depth=1, learning_rate=0.5) to y = 0 for x < 4 and 10 otherwise on x = 0..7. Return [number of stages, whether training MSE never increases, final MSE rounded to 4 places].",
         "x = np.arange(8, dtype=float).reshape(-1, 1)\ny = np.where(x.ravel() < 4, 0.0, 10.0)\nmodel = GradientBoostingRegressor(n_estimators=data, max_depth=1, learning_rate=0.5, random_state=7).fit(x, y)\nerrors = [float(np.mean((y - p) ** 2)) for p in model.staged_predict(x)]\nresult = [len(errors), all(b <= a + 1e-12 for a, b in zip(errors, errors[1:])), round(errors[-1], 4)]",
         [(3,[3,True,0.3906]),(1,[1,True,6.25]),(5,[5,True,0.0244])],
         ("learning_rate=0.5","learning_rate=0.1"),
         ["The initial prediction is the mean, 5.", "A stump splits at x = 3.5 and fits the residuals ±5.", "Each stage multiplies the residual by (1 - learning_rate)."],
         "After one stage the residual is 2.5, MSE 6.25; after three it is 0.625, MSE about 0.39. A learning rate of 0.1 shrinks the residual far more slowly.",
         [[3,True,6.25],[3,False,0.3906],[3,True,1.5625]],
         NP+"\nfrom sklearn.ensemble import GradientBoostingRegressor"),
    ("How do learning_rate and n_estimators interact in boosting?", "Lower learning rates need more trees; tune them together, ideally with early stopping on validation data."))

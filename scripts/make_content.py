"""Build original, attributed seed content. Sources are links, never copied chapters."""
import json
from pathlib import Path
tracks=[]; lessons=[]; cards=[]
def track(id,name,mode,subtitle,symbol,color,resources,**extra):
    tracks.append(dict(id=id,name=name,mode=mode,subtitle=subtitle,symbol=symbol,color=color,resources=[dict(title=t,url=u,kind=k) for t,u,k in resources],**extra))
def lesson(track_id,slug,title,summary,body,code,challenge,solution,question,options,answer,explanation,recall,source_url=None):
    id=f'{track_id}.{slug}'
    lessons.append(dict(id=id,trackID=track_id,title=title,summary=summary,body=body,code=code,challenge=challenge,solution=solution,question=question,options=options,answerIndex=answer,explanation=explanation,minutes=8,order=len([l for l in lessons if l['trackID']==track_id])+1,sourceURL=source_url or next(t for t in tracks if t['id']==track_id)['resources'][0]['url']))
    for n,(prompt,response) in enumerate(recall):
        cards.append(dict(id=f'{id}.{n+1}',trackID=track_id,lessonID=id,prompt=prompt,answer=response,sourceURL=lessons[-1]['sourceURL']))
track('python','Python','retain','Objects, iterators, and asynchronous work','chevron.left.forwardslash.chevron.right','F4C95D',[('Python tutorial','https://docs.python.org/3/tutorial/','Reference'),('Python data model','https://docs.python.org/3/reference/datamodel.html','Reference'),('Exercism Python','https://github.com/exercism/python','Exercises')])
track('numpy','NumPy','retain','Shapes, broadcasting, and array ownership','square.grid.3x3','5BB9DD',[('NumPy user guide','https://numpy.org/doc/stable/user/','Reference'),('NumPy exercises','https://github.com/rougier/numpy-100','Exercises')])
track('pandas','pandas','retain','Indexing, joins, and split–apply–combine','tablecells','B09AE8',[('pandas user guide','https://pandas.pydata.org/docs/user_guide/index.html','Reference'),('pandas getting started','https://pandas.pydata.org/docs/getting_started/index.html','Tutorial')])
track('sklearn','scikit-learn','retain','Validation, pipelines, and useful metrics','chart.xyaxis.line','F4AC6F',[('scikit-learn user guide','https://scikit-learn.org/stable/user_guide.html','Reference'),('Common pitfalls','https://scikit-learn.org/stable/common_pitfalls.html','Tutorial')])
track('pytorch','PyTorch','retain','Autograd, tensor shapes, and training loops','brain','EF927C',[('PyTorch tutorials','https://docs.pytorch.org/tutorials/','Tutorial'),('PyTorch examples','https://github.com/pytorch/examples','Projects')])
track('cpp','C++','retain','Lifetime, value semantics, and concurrency','memorychip','84A7F7',[('C++ Core Guidelines','https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines','Reference'),('Exercism C++','https://github.com/exercism/cpp','Exercises')])
track('csharp','C#','retain','LINQ, asynchronous work, and resource lifetime','number.square','BCA4F3',[('C# guide','https://learn.microsoft.com/en-us/dotnet/csharp/','Reference'),('Exercism C#','https://github.com/exercism/csharp','Exercises')])
track('go','Go','retain','Slices, interfaces, and concurrency','arrow.triangle.branch','68CCD3',[('A Tour of Go','https://go.dev/tour/','Tutorial'),('Effective Go','https://go.dev/doc/effective_go','Reference'),('Exercism Go','https://github.com/exercism/go','Exercises')])
track('javascript','JavaScript','retain','Closures, promises, and event-loop ordering','curlybraces','E9CD66',[('MDN JavaScript guide','https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide','Reference'),('Exercism JavaScript','https://github.com/exercism/javascript','Exercises')])
track('rust','Rust','learn','From C++ ownership to compiler-checked borrowing','shield.lefthalf.filled','E8A078',[('The Rust Book','https://doc.rust-lang.org/book/','Book'),('Rustlings','https://github.com/rust-lang/rustlings','Exercises'),('Rust by Example','https://doc.rust-lang.org/rust-by-example/','Tutorial'),('Rust Playground','https://play.rust-lang.org/','Playground')])
track('ocaml','OCaml','learn','From familiar functions to algebraic data types','function','E9BB76',[('Learn OCaml','https://ocaml.org/docs','Tutorial'),('Cornell CS 3110 textbook','https://cs3110.github.io/textbook/cover.html','Book'),('Real World OCaml','https://dev.realworldocaml.org/','Book'),('Exercism OCaml','https://github.com/exercism/ocaml','Exercises'),('Learn-OCaml','https://github.com/ocaml-sf/learn-ocaml','Platform')])
track('lean','Lean 4','learn','From typed functions to checked mathematical proofs','checkmark.seal','9ACBB7',[('Functional Programming in Lean','https://lean-lang.org/functional_programming_in_lean/','Book'),('Theorem Proving in Lean 4','https://lean-lang.org/theorem_proving_in_lean4/','Book'),('Mathematics in Lean','https://leanprover-community.github.io/mathematics_in_lean/','Book'),('Natural Number Game','https://adam.math.hhu.de/#/g/leanprover-community/nng4','Game'),('Lean live editor','https://live.lean-lang.org/','Playground')])
track('bash','Bash','learn','From first command to robust, debuggable automation','terminal','8FD694',[('GNU Bash manual','https://www.gnu.org/software/bash/manual/bash.html','Reference'),('POSIX Shell Command Language','https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html','Reference'),('ShellCheck wiki','https://www.shellcheck.net/wiki/','Reference'),('BashGuide and BashPitfalls','https://mywiki.wooledge.org/BashGuide','Tutorial')])
lesson('python','aliasing','Identity is not equality','Predict how aliases and copies behave.',[
'A variable names an object. Assignment binds another name; it does not copy the object. Mutating a shared list is visible through every alias.',
'Equality asks whether values compare equal. Identity asks whether two references point to the same object. Use `is` for sentinels such as None, and `==` for values.',
'A shallow copy creates a new outer container but shares its nested objects. Choose a deep copy only when you actually need independent nested mutable state.'],
'a = [[1], [2]]\nb = a.copy()\nb[0].append(3)\nprint(a)\nprint(a is b)',
'Change the example so that appending to b[0] leaves a unchanged.',
'import copy\na = [[1], [2]]\nb = copy.deepcopy(a)\nb[0].append(3)\nprint(a)',
'After a shallow copy of a nested list, which objects are independent?', ['Only the outer list','Every nested object','No objects','Only immutable elements'],0,'The new outer list stores references to the original nested objects.', [('What does Python assignment copy?','Assignment binds a name to an object. It does not copy the object.'),('When can a shallow list copy still share mutations?','When a nested mutable object is shared between the original and the copy.')])
lesson('python','generators','Iterators remember their position','Recognize single-pass and lazy behavior.',[
'An iterable can provide an iterator. The iterator supplies values through next() and eventually raises StopIteration.',
'A generator suspends execution at yield and resumes with its local state intact. It is usually single-pass. Laziness saves storage, but it does not make a previously consumed generator restart.',
'Use a generator for streaming transforms, and materialize a list when consumers need repeated traversal.'],
'g = (x * x for x in range(3))\nprint(list(g))\nprint(list(g))', 'Write a generator function yielding the first n squares.',
'def squares(n):\n    for i in range(n):\n        yield i * i\nprint(list(squares(4)))',
'What does a second list(g) return after fully consuming a generator?', ['The same values','An empty list','A copy of the generator','A TypeError'],1,'The generator is exhausted; a new instance is needed to iterate again.', [('What state does a generator retain between yields?','Its execution position and local variables.'),('What is the difference between iterable and iterator?','An iterable can produce an iterator; an iterator tracks traversal and supplies the next value.')])
lesson('python','async','Concurrency needs suspension points','Separate cooperative async tasks from CPU parallelism.',[
'Calling an async function creates a coroutine. It runs when awaited or scheduled as a task.',
'An event loop can switch to other tasks when a coroutine suspends. Blocking calls inside a coroutine still block the loop.',
'asyncio is useful for overlapping waiting. CPU-bound work needs a suitable executor or process strategy; merely adding async does not parallelize it.'],
'import asyncio\nasync def work(n):\n    await asyncio.sleep(0.01)\n    return n * 2\nasync def main():\n    print(await asyncio.gather(work(2), work(3)))\nasyncio.run(main())', 'Run three waiting tasks concurrently and print their results.',
'import asyncio\nasync def task(n):\n    await asyncio.sleep(0.01)\n    return n\nasync def main():\n    print(await asyncio.gather(*(task(n) for n in range(3))))\nasyncio.run(main())',
'What happens when time.sleep() runs directly inside an asyncio coroutine?', ['The event loop is blocked','It becomes a background thread','All tasks become parallel','It returns a Future'],0,'A synchronous sleep blocks its thread, including the event loop on that thread.', [('Does calling an async function execute its body immediately?','No. It creates a coroutine, which must be awaited or scheduled.'),('Why is blocking I/O inside an async coroutine a problem?','It blocks the event-loop thread and prevents other tasks on that loop from progressing.')])
lesson('numpy','broadcasting','Read shapes from the right','Check broadcasting before writing vectorized code.',[
'NumPy compares shapes from the trailing dimensions. A pair of dimensions is compatible when sizes match or one is 1. Missing leading dimensions behave as 1.',
'Broadcasting expresses repetition without manually building repeated arrays. It is about compatible shapes, not matching the number of elements.',
'Adding a (3, 1) column and a (1, 4) row produces a (3, 4) grid. State intended axes explicitly to avoid a computation that runs but means the wrong thing.'],
'import numpy as np\na = np.arange(3).reshape(3, 1)\nb = np.arange(4).reshape(1, 4)\nprint((a + b).shape)\nprint(a + b)', 'Subtract each column mean from a 2D array without a Python loop.',
'import numpy as np\nx = np.array([[1., 2.], [3., 6.]])\nprint(x - x.mean(axis=0, keepdims=True))',
'What shape results from (3, 1) + (1, 4)?', ['(3, 4)','(1, 1)','(4, 3)','An error'],0,'Each size-1 dimension expands to match its corresponding non-1 dimension.', [('Which dimensions does broadcasting compare first?','The trailing dimensions, working toward the leading dimensions.'),('When are two broadcast dimensions compatible?','When their sizes match, or one of the sizes is 1.')])
lesson('numpy','views','A slice can share memory','Distinguish views from independent arrays.',[
'Basic slicing generally returns a view. Mutating that view can mutate the source array.',
'Advanced indexing generally returns a copy. Do not infer ownership just from whether two arrays look different.',
'Use copy() to make independence explicit, and shares_memory() when investigating memory relationships.'],
'import numpy as np\na = np.arange(5)\nb = a[1:3]\nb[0] = 99\nprint(a)', 'Create an independent slice before changing its first element.',
'import numpy as np\na = np.arange(5)\nb = a[1:3].copy()\nb[0] = 99\nprint(a)',
'What does basic NumPy slicing generally return?', ['A view','A deep copy','A Python list','A generator'],0,'The view can refer to the original storage.', [('How do you make an independent NumPy slice?','Call .copy() on the slice.'),('Why can writing through a NumPy view change another array?','The arrays share underlying memory.')])
lesson('numpy','axes','Axis means the dimension you reduce','Predict reductions and preserve useful dimensions.',[
'For a 2D array, reducing axis 0 combines rows for each column. Reducing axis 1 combines columns for each row.',
'keepdims=True retains a size-1 dimension at the reduced axis. This often makes later broadcasting unambiguous.',
'Shapes are part of the contract of numerical code. Check them alongside values, especially when writing batch computations.'],
'import numpy as np\nx = np.array([[1, 2], [3, 4]])\nprint(x.sum(axis=0))\nprint(x.sum(axis=1))', 'Normalize each row by its row sum, preserving a dimension for broadcasting.',
'import numpy as np\nx = np.array([[1., 2.], [3., 4.]])\nprint(x / x.sum(axis=1, keepdims=True))',
'For a 2D array, axis=0 produces sums for each…', ['Column','Row','Individual cell','Diagonal'],0,'The row dimension is reduced, leaving one value per column.', [('Why use keepdims=True in a reduction?','It preserves reduced axes as size-1 dimensions for predictable broadcasting.'),('What is reduced by axis=1 in a 2D array?','The column dimension, yielding a result for each row.')])
lesson('pandas','indexing','Labels and positions are different','Choose loc and iloc deliberately.',[
'loc selects by labels. iloc selects by integer positions. An integer index label does not automatically mean a row position.',
'Label slices with loc include their end label when present; positional slices with iloc follow Python’s usual excluded-stop convention.',
'Assign through a single loc operation. Avoid relying on chained assignment behavior, which also interacts with pandas copy-on-write semantics.'],
'import pandas as pd\ns = pd.Series([10, 20, 30], index=[100, 200, 300])\nprint(s.loc[200])\nprint(s.iloc[1])', 'Select rows with score >= 2 and assign their flag to True using loc.',
'import pandas as pd\ndf = pd.DataFrame({"score": [1, 2, 3], "flag": [False]*3})\ndf.loc[df["score"] >= 2, "flag"] = True\nprint(df)',
'Which selector uses integer positions?', ['loc','iloc','Both always','Neither'],1,'iloc selects by position regardless of the labels in the index.', [('How do loc and iloc differ?','loc uses labels; iloc uses integer positions.'),('How should you update a filtered set of pandas rows?','Use a single df.loc[mask, column] assignment.')])
lesson('pandas','joins','Validate the relationship before joining','Catch accidental row multiplication.',[
'A join can multiply rows when keys are duplicated on both sides. This is valid many-to-many behavior, but it may violate the relationship you intended.',
'merge(validate=...) checks an expected cardinality such as one_to_one or many_to_one. Use indicator=True to inspect matched and unmatched rows.',
'Check key uniqueness and null handling before interpreting aggregates after a join.'],
'import pandas as pd\na = pd.DataFrame({"id": [1, 1], "x": [2, 3]})\nb = pd.DataFrame({"id": [1, 1], "y": [4, 5]})\nprint(len(a.merge(b, on="id")))', 'Join repeated event IDs to unique account IDs with a many_to_one check.',
'import pandas as pd\nevents = pd.DataFrame({"id": [1, 1, 2]})\naccounts = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})\nprint(events.merge(accounts, on="id", validate="many_to_one"))',
'Two rows with key 1 on each side produce how many matching rows?', ['1','2','4','0'],2,'Each left matching row pairs with each right matching row.', [('What catches an unexpected many-to-many merge?','Use merge(validate=...) with the intended key relationship.'),('Why might a join unexpectedly inflate an aggregate?','Duplicate keys can multiply rows during the join.')])
lesson('pandas','groups','Aggregation shrinks; transform aligns','Use the right shape for grouped results.',[
'groupby().agg() produces results per group. groupby().transform() returns a result aligned with the original rows.',
'Use transform when you want to attach a group statistic to every row, such as each item’s deviation from its group mean.',
'Before assigning a grouped result, ask whether you need one row per group or one value per original observation.'],
'import pandas as pd\ndf = pd.DataFrame({"team": ["A", "A", "B"], "score": [1, 3, 9]})\ndf["centered"] = df["score"] - df.groupby("team")["score"].transform("mean")\nprint(df)', 'Add each team’s total to every original row.',
'import pandas as pd\ndf = pd.DataFrame({"team": ["A", "A", "B"], "score": [1, 3, 9]})\ndf["total"] = df.groupby("team")["score"].transform("sum")\nprint(df)',
'Which operation returns results aligned with the original rows?', ['agg','transform','drop_duplicates','A cross join'],1,'transform broadcasts a group result back to its original rows.', [('When should you use groupby transform?','When the result should align with each original row.'),('How does groupby agg change the result’s granularity?','It usually yields one summary row per group.')])
lesson('sklearn','leakage','Fit preprocessing on training data','Keep evaluation genuinely unseen.',[
'A scaler, imputer, or feature selector learns information when fitted. Fitting it before splitting allows evaluation data to influence the model-building process.',
'Place preprocessing and the estimator in a Pipeline. Cross-validation then fits the complete pipeline separately inside each training fold.',
'Even unsupervised preprocessing can leak information. Treat every learned transformation as part of the model.'],
'from sklearn.pipeline import make_pipeline\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\nmodel = make_pipeline(StandardScaler(), LogisticRegression())\nprint(model)', 'Build a pipeline with a median imputer and logistic regression.',
'from sklearn.pipeline import make_pipeline\nfrom sklearn.impute import SimpleImputer\nfrom sklearn.linear_model import LogisticRegression\nprint(make_pipeline(SimpleImputer(strategy="median"), LogisticRegression()))',
'Where should preprocessing be fitted during cross-validation?', ['On the entire dataset','Inside each training fold','Only on the test set','It never needs fitting'],1,'The validation fold must not influence learned preprocessing.', [('Can fitting a scaler on all data cause leakage?','Yes. Validation or test statistics can influence preprocessing.'),('What does a scikit-learn Pipeline help protect during cross-validation?','It fits preprocessing and the estimator together within each training fold.')])
lesson('sklearn','metrics','Accuracy can hide the wrong failure','Choose metrics that match the cost of mistakes.',[
'With rare positives, predicting only the majority class can achieve high accuracy while finding none of the cases you care about.',
'Precision describes how many predicted positives are correct. Recall describes how many actual positives were found.',
'Select a threshold and metric using validation data, guided by the cost of false positives and false negatives. Keep the final test set for evaluation.'],
'from sklearn.metrics import precision_score, recall_score\ny = [1, 1, 0, 0]\np = [1, 0, 1, 0]\nprint(precision_score(y, p), recall_score(y, p))', 'Compute recall when one of three actual positives is found.',
'from sklearn.metrics import recall_score\nprint(recall_score([1, 1, 1, 0], [1, 0, 0, 0]))',
'Which metric answers “How many actual positives did we find?”', ['Precision','Recall','Accuracy','Specificity'],1,'Recall is true positives divided by actual positives.', [('What is precision?','The fraction of predicted positives that are actually positive.'),('Why can accuracy mislead on imbalanced data?','A majority-only predictor can score well while missing the rare class.')])
lesson('sklearn','validation','Choose splits that resemble deployment','Preserve time and entity boundaries.',[
'Random splits assume examples can be mixed without violating the deployment setting. That fails for future prediction when later observations reveal information about earlier ones.',
'Use time-aware splits for temporal prediction, and group-aware splits when several rows come from the same person, device, or other entity.',
'Hyperparameters are chosen with validation or cross-validation. Repeatedly choosing them based on the test score turns the test set into training feedback.'],
'from sklearn.model_selection import TimeSeriesSplit\nimport numpy as np\nfor train, test in TimeSeriesSplit(n_splits=3).split(np.arange(8)):\n    print(train.tolist(), test.tolist())', 'Explain which splitter you would use for multiple records per patient.',
'from sklearn.model_selection import GroupKFold\nprint(GroupKFold(n_splits=3))',
'What split is suitable when patient IDs repeat across rows?', ['A random row split','A group-aware split','Sort by label then split','Use every row in every fold'],1,'Keeping each patient within a single side avoids leakage between correlated records.', [('When is a time-aware split useful?','When deployment predicts future observations from past observations.'),('Why should the test set not choose hyperparameters?','Repeated tuning to its score makes it a source of training feedback.')])
lesson('pytorch','gradients','Gradients accumulate until cleared','Understand each stage of a training step.',[
'backward() accumulates gradients in leaf tensors that require them. It does not automatically clear previous gradients.',
'A common training step clears gradients, computes predictions and loss, runs backward(), then steps the optimizer.',
'Zeroing to None can avoid unnecessary writes and distinguish missing gradients from zero-valued gradients.'],
'import torch\nx = torch.tensor(3.0, requires_grad=True)\n(x*x).backward()\nprint(x.grad.item())\n(x*x).backward()\nprint(x.grad.item())', 'Clear x.grad before the second backward call.',
'import torch\nx = torch.tensor(3.0, requires_grad=True)\n(x*x).backward()\nx.grad = None\n(x*x).backward()\nprint(x.grad.item())',
'Without clearing, what does a second backward call do to leaf gradients?', ['Replaces them','Accumulates them','Deletes them','Moves them to a GPU'],1,'backward adds the new contribution to existing gradients.', [('Does backward() clear old gradients?','No. Gradients accumulate until cleared.'),('What is a conventional optimizer step order?','Clear gradients; compute predictions and loss; call backward(); call optimizer.step().')])
lesson('pytorch','evaluation','Evaluation mode and no-grad do different jobs','Separate layer behavior from autograd tracking.',[
'model.eval() changes modules such as dropout and batch normalization to evaluation behavior. It does not disable gradient recording.',
'no_grad() disables gradient recording in its scope. inference_mode() offers a stricter inference context with additional restrictions.',
'For typical inference, set evaluation mode and use an appropriate inference context. Return to train() before training again.'],
'import torch\nmodel = torch.nn.Dropout(p=0.5)\nmodel.eval()\nwith torch.no_grad():\n    print(model(torch.ones(4)))', 'Run a small linear layer with eval and inference_mode.',
'import torch\nmodel = torch.nn.Linear(2, 1)\nmodel.eval()\nwith torch.inference_mode():\n    print(model(torch.ones(1, 2)))',
'Does model.eval() disable autograd?', ['Yes, for all tensors','No','Only on the CPU','Only for parameters'],1,'eval changes module behavior; autograd is controlled separately.', [('What does model.eval() change?','The training/evaluation behavior of modules such as dropout and batch normalization.'),('What does torch.no_grad() change?','It disables gradient recording in its scope.')])
lesson('pytorch','shapes','Treat tensor shapes as contracts','Check batch and feature dimensions explicitly.',[
'A linear layer transforms the last dimension. For input (batch, features), Linear(features, outputs) produces (batch, outputs).',
'Broadcasting can silently make a loss compare the wrong elements. Check predicted and target shapes before computing it.',
'Reshape may return a view or copy depending on layout. Do not assume reshaping guarantees independent storage.'],
'import torch\nlayer = torch.nn.Linear(3, 2)\nx = torch.ones(4, 3)\nprint(layer(x).shape)', 'Create five examples with four features and a layer producing one output.',
'import torch\nx = torch.ones(5, 4)\nprint(torch.nn.Linear(4, 1)(x).shape)',
'Linear(3, 2) applied to a (4, 3) tensor returns which shape?', ['(3, 2)','(4, 2)','(2, 4)','(4, 3)'],1,'The last feature dimension is transformed, preserving the batch dimension.', [('Which dimension does torch.nn.Linear transform?','The last dimension.'),('Why check prediction and target shapes before a loss?','Broadcasting may otherwise compute a valid but unintended comparison.')])
lesson('cpp','raii','Lifetime owns cleanup','Use destructors to make resource release dependable.',[
'RAII ties resource lifetime to an object. Construction acquires or establishes ownership, and destruction releases it.',
'Stack unwinding destroys fully constructed local objects when an exception leaves their scope. Destructors should generally not throw.',
'Prefer unique_ptr for exclusive heap ownership, and use shared_ptr only when shared ownership is part of the design.'],
'#include <iostream>\n#include <memory>\nint main() {\n    auto n = std::make_unique<int>(42);\n    std::cout << *n << "\\n";\n}', 'Own a dynamic integer with unique_ptr, then move ownership to another variable.',
'#include <iostream>\n#include <memory>\n#include <utility>\nint main() {\n    auto a = std::make_unique<int>(7);\n    auto b = std::move(a);\n    std::cout << *b << "\\n";\n}',
'Which smart pointer models exclusive ownership?', ['shared_ptr','unique_ptr','weak_ptr','A raw pointer always'],1,'unique_ptr expresses one owner and transfers ownership through moves.', [('What does RAII connect?','Resource acquisition and release to object construction and destruction.'),('When is shared_ptr appropriate?','When shared ownership is a real requirement, rather than just to avoid deciding who owns a resource.')])
lesson('cpp','move','Moving permits resource transfer','A cast does not itself move a resource.',[
'std::move casts an expression to an rvalue reference. It enables overload resolution to select a move operation.',
'Whether resources actually move depends on the selected constructor or assignment operator. A const source may still lead to copying.',
'A moved-from standard library object is generally valid but has an unspecified value unless a stronger guarantee is documented. Do not assume a moved-from string is empty.'],
'#include <iostream>\n#include <string>\n#include <utility>\nint main() {\n    std::string a = "hello";\n    std::string b = std::move(a);\n    std::cout << b << "\\n";\n}', 'Move a vector into a second vector and print the second vector’s size.',
'#include <iostream>\n#include <vector>\n#include <utility>\nint main() {\n    std::vector<int> a{1,2,3};\n    auto b = std::move(a);\n    std::cout << b.size() << "\\n";\n}',
'What does std::move itself do?', ['Transfers bytes','Deletes the source','Casts to an rvalue reference','Allocates new memory'],2,'The selected move constructor or assignment performs any transfer.', [('Does std::move itself transfer ownership?','No. It casts the expression; an appropriate move operation may then transfer resources.'),('Can you assume a moved-from std::string is empty?','No. It remains valid, but its value is generally unspecified.')])
lesson('cpp','races','Thread safety requires a memory model','Shared writes need a synchronization strategy.',[
'A data race involves conflicting operations in different threads, at least one a write, without the required synchronization and with non-atomic access. In C++, a data race yields undefined behavior.',
'A mutex protects a compound invariant when every relevant access follows the same locking discipline. An atomic protects its own operations; it does not automatically protect a larger data structure.',
'Choose synchronization based on the invariant first. Avoid guessing that relaxed atomic ordering makes a compound protocol correct.'],
'#include <atomic>\n#include <iostream>\nint main() {\n    std::atomic<int> count{0};\n    count.fetch_add(1);\n    std::cout << count.load() << "\\n";\n}', 'Use lock_guard to protect a counter increment.',
'#include <mutex>\n#include <iostream>\nint main() {\n    std::mutex m; int count = 0;\n    { std::lock_guard<std::mutex> lock(m); ++count; }\n    std::cout << count << "\\n";\n}',
'What is the language-level consequence of a C++ data race?', ['Only a stale read','Undefined behavior','Automatic locking','A compiler warning always'],1,'The program no longer has defined behavior under the C++ memory model.', [('What does a mutex protect when used consistently?','A critical section and the shared invariant that all accesses obey.'),('Does one atomic variable make a whole data structure thread-safe?','No. Compound invariants need an appropriate synchronization protocol.')])
lesson('csharp','linq','A query may execute later','Understand deferred execution before mutating inputs.',[
'Many LINQ operators return a deferred sequence. Enumeration executes the query, which can reflect the source state at enumeration time.',
'ToList() materializes results at that point. Use it when you need a snapshot or want to avoid repeating an expensive traversal.',
'Not every LINQ operation is deferred. Terminal operators such as Count() generally compute their result when called.'],
'using System;\nusing System.Linq;\nusing System.Collections.Generic;\nclass Program { static void Main() {\n    var xs = new List<int>{1,2};\n    var q = xs.Where(x => x > 1);\n    xs.Add(3);\n    Console.WriteLine(string.Join(",", q));\n}}', 'Materialize the query before adding another source element.',
'using System;\nusing System.Linq;\nusing System.Collections.Generic;\nclass Program { static void Main() {\n    var xs = new List<int>{1,2};\n    var q = xs.Where(x => x > 1).ToList();\n    xs.Add(3);\n    Console.WriteLine(string.Join(",", q));\n}}',
'What typically turns a deferred LINQ query into a snapshot?', ['Where','Select','ToList','AsEnumerable'],2,'ToList enumerates immediately and stores the resulting elements.', [('When does a deferred LINQ query execute?','When it is enumerated.'),('Why materialize a LINQ query with ToList()?','To take a result snapshot or avoid repeated enumeration.')])
lesson('csharp','async','A Task is a handle to completion','Await asynchronous work without blocking the caller.',[
'Task represents eventual completion, possibly with a result. await asynchronously waits and resumes when the task completes.',
'async does not automatically create a new thread. Asynchronous I/O can complete without dedicating a blocked thread to each operation.',
'Prefer async Task over async void except for event handlers. Task-returning methods allow callers to await completion and observe exceptions.'],
'using System;\nusing System.Threading.Tasks;\nclass Program { static async Task Main() {\n    await Task.Delay(10);\n    Console.WriteLine("done");\n}}', 'Await two tasks using Task.WhenAll.',
'using System;\nusing System.Threading.Tasks;\nclass Program { static async Task Main() {\n    await Task.WhenAll(Task.Delay(10), Task.Delay(20));\n    Console.WriteLine("both done");\n}}',
'Which return type usually lets callers observe asynchronous errors?', ['void','Task','int only','IEnumerable only'],1,'Callers can await a Task and receive exceptions from it.', [('Does async always start a new thread in C#?','No. async changes how the method handles suspension and continuation.'),('Why avoid async void outside event handlers?','Callers cannot await completion and handle its exceptions through a returned Task.')])
lesson('csharp','dispose','Resource lifetime is explicit','Use using for deterministic disposal.',[
'Garbage collection reclaims managed memory. It does not guarantee timely release of an unmanaged resource such as a file handle.',
'A using statement or declaration disposes an IDisposable object when its scope ends, including exceptional exits.',
'Use await using for IAsyncDisposable resources whose cleanup is asynchronous.'],
'using System;\nusing System.IO;\nclass Program { static void Main() {\n    using var reader = new StringReader("hello");\n    Console.WriteLine(reader.ReadLine());\n}}', 'Read two lines from a StringReader inside a using scope.',
'using System;\nusing System.IO;\nclass Program { static void Main() {\n    using var r = new StringReader("a\\nb");\n    Console.WriteLine(r.ReadLine());\n    Console.WriteLine(r.ReadLine());\n}}',
'What does using guarantee for IDisposable?', ['Immediate garbage collection','Disposal at scope exit','A new thread','Immutable contents'],1,'The generated cleanup calls Dispose even when the scope exits through an exception.', [('How does disposal differ from garbage collection?','Disposal releases resources deterministically; garbage collection reclaims managed memory at an unspecified time.'),('When is await using appropriate?','For an IAsyncDisposable resource that needs asynchronous cleanup.')])
lesson('go','slices','Slices describe shared storage','Track length, capacity, and the backing array.',[
'A slice is a descriptor for an underlying array segment. Copying a slice value copies that descriptor, not the elements.',
'append may reuse capacity or allocate a new backing array. Aliasing behavior can therefore change after an append.',
'Use make and copy to create independent storage when that is part of your function’s contract.'],
'package main\nimport "fmt"\nfunc main() {\n a := []int{1,2,3}; b := a[:2]\n b[0] = 9\n fmt.Println(a)\n}', 'Copy a slice so that modifying the copy does not change the original.',
'package main\nimport "fmt"\nfunc main() {\n a := []int{1,2,3}; b := make([]int, len(a)); copy(b,a)\n b[0] = 9; fmt.Println(a,b)\n}',
'What does assigning a Go slice value copy?', ['All elements','The slice descriptor','The entire backing array','Nothing at all'],1,'The new descriptor can refer to the same backing array.', [('Can two Go slices share mutations?','Yes, when their descriptors reference overlapping backing-array storage.'),('When can append change a slice’s backing array?','When existing capacity is insufficient and a new array is allocated.')])
lesson('go','interfaces','An interface can hold a typed nil','Separate interface emptiness from its dynamic value.',[
'An interface value carries a dynamic type and a dynamic value. It equals nil only when both are absent.',
'An interface holding a nil pointer still has a dynamic type, so the interface itself is not nil.',
'This often appears when returning a typed nil pointer as an error. Return a literal nil when there is no error.'],
'package main\nimport "fmt"\nfunc main() {\n var p *int = nil\n var x any = p\n fmt.Println(p == nil, x == nil)\n}', 'Explain why the interface prints false when compared to nil.',
'package main\nimport "fmt"\nfunc main() {\n var x any = nil\n fmt.Println(x == nil)\n}',
'Is an interface holding a typed nil pointer equal to nil?', ['Always','No','Only on 64-bit systems','Only before a type assertion'],1,'Its dynamic type is present even though the stored pointer is nil.', [('When is a Go interface value nil?','When it has neither a dynamic type nor a dynamic value.'),('What should an error-returning function return on success?','A literal nil error, rather than a typed nil pointer wrapped in an interface.')])
lesson('go','channels','Channels coordinate progress','Know which sends can block and who closes.',[
'An unbuffered send requires a receiving operation to rendezvous. Buffered sends can proceed until the buffer is full.',
'Closing a channel signals that no more values will be sent. Receivers can drain buffered values, then observe the closed state.',
'The sending side generally owns closing. Sending to a closed channel panics; receiving from a closed, drained channel yields a zero value with ok=false.'],
'package main\nimport "fmt"\nfunc main() {\n ch := make(chan int, 1)\n ch <- 7; close(ch)\n v, ok := <-ch; fmt.Println(v,ok)\n v, ok = <-ch; fmt.Println(v,ok)\n}', 'Start a producer goroutine that sends three values, closes, and lets main range over them.',
'package main\nimport "fmt"\nfunc main() {\n ch := make(chan int)\n go func() { for i:=0;i<3;i++ { ch<-i }; close(ch) }()\n for v := range ch { fmt.Println(v) }\n}',
'What happens on a send to a closed channel?', ['It returns false','It panics','It silently discards','It reopens the channel'],1,'Sending after closure is a programming error and panics.', [('What happens on receiving from a closed and drained channel?','It returns the element type’s zero value with ok=false.'),('Who should generally close a Go channel?','The sending side, once all sends are complete.')])
lesson('javascript','closures','A closure retains access to bindings','Predict captured state across calls.',[
'A closure retains access to the lexical environment in which a function was created. It captures bindings, not a frozen snapshot of every value.',
'An inner function can therefore observe a later update to a captured variable. Separate closure instances can retain independent environments.',
'Block-scoped let declarations make each for-loop iteration binding distinct in the common closure-over-loop pattern.'],
'function counter() {\n  let n = 0;\n  return () => ++n;\n}\nconst next = counter();\nconsole.log(next(), next());', 'Create two counters and show that their states are independent.',
'function counter() { let n=0; return () => ++n; }\nconst a=counter(), b=counter();\nconsole.log(a(), a(), b());',
'What does a closure retain access to?', ['Only copied constants','Its lexical bindings','Only global variables','A new thread'],1,'Bindings in its lexical environment remain accessible.', [('Does a JavaScript closure capture a frozen snapshot of mutable variables?','No. It retains access to lexical bindings and can observe updates.'),('Why can two calls to a counter factory create independent counters?','Each call creates a separate lexical environment.')])
lesson('javascript','promises','Promise reactions run after synchronous code','Recognize microtask ordering.',[
'Promise callbacks are scheduled as microtasks after the current synchronous work completes.',
'await suspends the async function while allowing its caller and other work to proceed. Awaiting an already resolved promise still resumes asynchronously.',
'For several independent operations, Promise.all waits for all results and rejects if an input rejects. It does not itself start a function that has not been called.'],
'console.log("A");\nPromise.resolve().then(() => console.log("B"));\nconsole.log("C");', 'Await two resolved promises together and print the results.',
'const results = await Promise.all([Promise.resolve(2), Promise.resolve(3)]);\nconsole.log(results);',
'What is the output order of the example?', ['A B C','B A C','A C B','C B A'],2,'The synchronous A and C execute before the promise reaction B.', [('When do promise reactions run relative to the current synchronous code?','After it completes, through the microtask queue.'),('What happens if one input of Promise.all rejects?','The returned promise rejects; this does not automatically cancel the other operations.')])
lesson('javascript','equality','Identity matters for reference values','Separate coercion, value equality, and object identity.',[
'=== compares without type coercion. For objects, arrays, and functions, it compares identity rather than structural content.',
'Two array literals with the same elements are different objects. To compare contents, define the equality appropriate to your data.',
'Object.is differs from === for NaN and signed zero. Choose the comparison that matches the intended semantics.'],
'console.log([1,2] === [1,2]);\nconsole.log(NaN === NaN);\nconsole.log(Object.is(NaN, NaN));', 'Compare two short arrays element by element.',
'const a=[1,2], b=[1,2];\nconsole.log(a.length === b.length && a.every((x,i) => x === b[i]));',
'Why is [1] === [1] false?', ['Arrays cannot be compared','Different object identities','1 is coerced to text','An exception is thrown'],1,'The two literals create distinct array objects.', [('What does === compare for objects?','Object identity, without structural comparison.'),('How does Object.is handle NaN?','Object.is(NaN, NaN) returns true.')])
lesson('rust','ownership','Ownership makes lifetime visible','Map C++ value semantics onto Rust moves.',[
'Each value has an owner responsible for its lifetime. A non-Copy value such as String is typically moved when assigned to another binding.',
'After a move, the old binding cannot be used as if it still owned the value. clone() explicitly duplicates data when the type supports it.',
'This resembles exclusive ownership in C++, but Rust checks many invalid uses before execution. Small Copy values such as integers behave differently from String.'],
'fn main() {\n    let first = String::from("hello");\n    let second = first;\n    println!("{}", second);\n}', 'Keep first usable by cloning it into second, then print both.',
'fn main() {\n    let first = String::from("hello");\n    let second = first.clone();\n    println!("{} {}", first, second);\n}',
'After moving a String from first into second, can first still be used?', ['Yes, always','No, unless reinitialized appropriately','Only in debug builds','Only when the string is short'],1,'The first binding no longer owns the moved value.', [('What normally happens when assigning a Rust String to another binding?','Ownership moves to the new binding.'),('How do you explicitly duplicate a Rust String?','Call .clone() when an independent copy is needed.')])
lesson('rust','borrowing','Borrow access without taking ownership','Learn shared and exclusive reference rules.',[
'A shared reference borrows read access. A mutable reference borrows exclusive access to the value for its active lifetime.',
'At a given time, you can have multiple shared references or one mutable reference to the same value. The compiler tracks when borrows are actually used, so their active lifetimes may end before a block ends.',
'Think of &T as temporary access and &mut T as temporary exclusive access. Neither automatically transfers ownership.'],
'fn length(s: &str) -> usize { s.len() }\nfn main() {\n    let s = String::from("hello");\n    println!("{} {}", length(&s), s);\n}', 'Write a function that appends ! through a mutable String reference.',
'fn emphasize(s: &mut String) { s.push(\'!\'); }\nfn main() {\n    let mut s = String::from("hello");\n    emphasize(&mut s);\n    println!("{}", s);\n}',
'Which accesses can coexist to the same value during their active lifetimes?', ['Two mutable references','A mutable and shared reference','Several shared references','Any references with any writes'],2,'Shared references permit concurrent read access; a mutable reference requires exclusivity.', [('Does borrowing normally transfer ownership?','No. A reference borrows access for a limited lifetime.'),('What is the core shared-versus-mutable borrowing rule?','Multiple shared references or one exclusive mutable reference during active borrows, subject to Rust’s rules.')])
lesson('rust','results','Make missing values and failures explicit','Use enums and exhaustive matching.',[
'Option<T> represents a value that may be absent. Result<T, E> represents success or a failure value.',
'match handles variants explicitly and is checked for exhaustiveness. The ? operator propagates compatible errors from a Result-returning function.',
'Prefer an explicit failure contract over panicking with unwrap() when failure is expected input behavior. This connects naturally to Go’s returned errors, but Rust’s enums encode the alternatives in one type.'],
'fn main() {\n    let value: Result<i32, _> = "42".parse();\n    match value {\n        Ok(n) => println!("{}", n),\n        Err(e) => println!("{}", e),\n    }\n}', 'Parse a number in a function returning Result and propagate the parse error with ?.',
'fn parse(s: &str) -> Result<i32, std::num::ParseIntError> {\n    let n = s.parse::<i32>()?;\n    Ok(n * 2)\n}\nfn main() { println!("{:?}", parse("21")); }',
'Which type expresses success or a failure value?', ['Option<T>','Result<T, E>','&mut T','usize'],1,'Result has Ok and Err variants.', [('How do Option and Result differ?','Option encodes presence or absence; Result encodes success or a failure value.'),('What does ? do on a Result in a compatible Result-returning function?','It extracts an Ok value or returns early with a converted Err.')])
lesson('ocaml','functions','Expressions return values','Begin with immutable bindings and inference.',[
'An OCaml let binding gives a name to a value. A function definition uses the same expression-oriented style, and types are often inferred.',
'Function application uses spaces rather than a parenthesized argument list. A function of several arguments can be partially applied to produce another function.',
'Unlike a Python reassignment, a later let with the same name creates a new binding. Prefer immutable data transformations until mutation is a deliberate requirement.'],
'let add x y = x + y\nlet add_two = add 2\nlet () = Printf.printf "%d\\n" (add_two 5)', 'Define a function multiplying two integers, then partially apply it to make a double function.',
'let multiply x y = x * y\nlet double = multiply 2\nlet () = Printf.printf "%d\\n" (double 6)',
'What is the result of partially applying add 2?', ['An error','A function waiting for the other argument','The integer 2','A mutable reference'],1,'A curried function can return another function after receiving one argument.', [('How is function application written in OCaml?','By placing arguments after the function, separated by spaces.'),('What does partial application produce?','A function with some arguments already supplied.')])
lesson('ocaml','variants','Describe alternatives with variants','Replace fragile flags with explicit cases.',[
'A variant type names the possible alternatives of a value. Each constructor can carry different data.',
'Pattern matching inspects the constructor and extracts its data. Exhaustiveness checking helps reveal missing cases.',
'Compared with a collection of booleans and optional fields, a variant can make invalid combinations impossible to represent. Rust enums share this useful idea.'],
' type shape = Circle of float | Rectangle of float * float\nlet area = function\n | Circle r -> Float.pi *. r *. r\n | Rectangle (w, h) -> w *. h\nlet () = Printf.printf "%.1f\\n" (area (Rectangle (3., 4.)))', 'Add a Square constructor carrying a side length and handle it in area.',
' type shape = Circle of float | Rectangle of float * float | Square of float\nlet area = function\n | Circle r -> Float.pi *. r *. r\n | Rectangle (w,h) -> w *. h\n | Square s -> s *. s\nlet () = Printf.printf "%.1f\\n" (area (Square 3.))',
'What useful property does an exhaustive match provide?', ['Every constructor has a handled case','Every function is tail-recursive','All values are mutable','No allocation occurs'],0,'Matching each possible alternative prevents an omitted constructor case.', [('What does a variant type describe?','A value drawn from explicitly named alternatives, whose constructors may carry data.'),('Why prefer a variant over loosely related flags?','It can encode valid alternatives while excluding invalid combinations.')])
lesson('ocaml','recursion','Lists are built from head and tail','Use structural recursion and accumulators.',[
'An OCaml list is either empty or a head element followed by another list. Pattern matching mirrors that recursive structure.',
'Tail recursion places the recursive call in the final return position. An accumulator can make a computation tail-recursive.',
'Prepending with :: is efficient. Repeatedly appending to the end can make a list-building algorithm unnecessarily expensive.'],
'let rec sum acc = function\n | [] -> acc\n | x :: xs -> sum (acc + x) xs\nlet () = Printf.printf "%d\\n" (sum 0 [1; 2; 3])', 'Implement a tail-recursive list length with an accumulator.',
'let length xs =\n let rec go n = function\n | [] -> n\n | _ :: rest -> go (n + 1) rest\n in go 0 xs\nlet () = Printf.printf "%d\\n" (length [1; 2; 3])',
'Which expression constructs a list by prepending x to xs?', ['x + xs','x :: xs','xs(x)','x && xs'],1,':: is the list constructor for a head and a tail.', [('What are the two structural cases of an OCaml list?','The empty list [], or a head and tail x :: xs.'),('When is a recursive call in tail position?','When its result is returned directly with no further work after the call.')])
lesson('lean','functions','Lean is also a programming language','Start with typed functions before proofs.',[
'Lean 4 supports functional programming as well as theorem proving. A definition uses a name, typed parameters, a result type, and an expression.',
'Natural numbers Nat are non-negative integers. A program can evaluate pure definitions with #eval.',
'Your OCaml and Rust work with typed functions transfers here. The later step is to express a claim about a function as a type and construct a term proving it.'],
'def double (n : Nat) : Nat := n + n\n#eval double 7', 'Define square on Nat and evaluate square 5.',
'def square (n : Nat) : Nat := n * n\n#eval square 5',
'What does #eval ask Lean to do?', ['Check a theorem without running anything','Evaluate an expression','Create an axiom','Import every Mathlib module'],1,'#eval computes an expression and displays its result.', [('What two roles does Lean 4 combine?','Functional programming and interactive theorem proving.'),('What values inhabit Nat?','The non-negative integers, including zero.')])
lesson('lean','proofs','A proof is a term of a proposition','Connect propositions with their evidence.',[
'A theorem states a proposition and supplies a term inhabiting that proposition. Lean checks the term against the claimed type.',
'For a hypothesis h : P, the term h itself proves P. Tactic mode lets you build proof terms through commands such as intro and exact.',
'A proof exercise must not count an accepted sorry as mastery: Lean can accept a placeholder with a warning. Completion should require a checked proof without placeholders or unapproved axioms.'],
'theorem identity (P : Prop) : P → P := by\n  intro h\n  exact h', 'Prove P → Q → P by introducing both assumptions and returning the proof of P.',
'theorem keep_left (P Q : Prop) : P → Q → P := by\n  intro hp hq\n  exact hp',
'Given h : P, which tactic can close a goal P?', ['exact h','intro P always','#eval P','sorry as a completed proof'],0,'h is already a term of the proposition required by the goal.', [('What does h : P mean when P is a proposition?','h is a proof term of P.'),('Why must a learning app treat sorry differently from a completed proof?','sorry supplies a placeholder that can be accepted with a warning without constructing the intended proof.')])
lesson('lean','equality','Definitional equality can close simple goals','Know when rfl is enough and when a theorem is needed.',[
'rfl closes a goal when both sides are definitionally equal after Lean’s reductions.',
'Not every mathematically true equality is definitional. Some require rewriting, simplification, or induction using established theorems.',
'When a tactic fails, inspect the goal and hypotheses before trying random commands. The proof-state panel is part of the learning experience.'],
'def increment (n : Nat) : Nat := n + 1\nexample : increment 2 = 3 := by\n  rfl', 'Prove that evaluating your double function at 3 yields 6.',
'def double (n : Nat) : Nat := n + n\nexample : double 3 = 6 := by\n  rfl',
'When is rfl typically sufficient?', ['For all true equations','When both sides are definitionally equal','Only with Mathlib','Only for floating point values'],1,'Reflexivity works when reduction makes the sides the same.', [('What kind of equality does rfl use?','Definitional equality after Lean’s reductions.'),('Why is the current proof goal useful after a tactic error?','It shows exactly which proposition remains and which hypotheses are available.')])
# Append new-language content without replacing existing progress identifiers.
pack=json.loads(Path(__file__).with_name('learning_pack.json').read_text())
for entry in pack['lessons']:
    lesson(entry['trackID'],entry['slug'],entry['title'],entry['summary'],
           entry['body'],entry['code'],entry['challenge'],entry['solution'],
           entry['question'],entry['options'],entry['answerIndex'],
           entry['explanation'],entry['recall'],source_url=entry['sourceURL'])
from add_readings import apply
content=apply(dict(schemaVersion=1,tracks=tracks,lessons=lessons,cards=cards))
from add_source_courses import apply as add_source_courses
content=add_source_courses(content)
from rust_guide import apply as add_rust_guide
content=add_rust_guide(content)
from ocaml_guide import apply as add_ocaml_guide
content=add_ocaml_guide(content)
from lean_guide import apply as add_lean_guide
content=add_lean_guide(content)
from python_guide import apply as add_python_guide
content=add_python_guide(content)
from cpp_guide import apply as add_cpp_guide
content=add_cpp_guide(content)
from csharp_guide import apply as add_csharp_guide
content=add_csharp_guide(content)
from go_guide import apply as add_go_guide
content=add_go_guide(content)
from bash_guide import apply as add_bash_guide
content=add_bash_guide(content)
import sys
generated=json.dumps(content,indent=2,ensure_ascii=False)+'\n'
if '--check' in sys.argv:
    if Path('CodingTeacher/curriculum.json').read_text() != generated:
        raise SystemExit('Bundled curriculum differs from reproducible generation')
else:
    Path('CodingTeacher/curriculum.json').write_text(generated)
print(f'{len(content["tracks"])} tracks, {len(content["lessons"])} lessons, {len(content["cards"])} recall cards, {len(content["sourceCourses"])} source courses')

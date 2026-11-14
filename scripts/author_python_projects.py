"""Original complete local projects and displayed replacement answers."""
import json
from pathlib import Path
PROJECTS={}

def project(key,title,module,tests,answer,answer_tests,challenge,mutation,dependencies,notes):
    files={title+'.py':module,'tests/test_project.py':tests,
           'pyproject.toml':'[build-system]\nrequires = ["setuptools>=68"]\nbuild-backend = "setuptools.build_meta"\n\n[project]\nname = "codingteacher-'+key+'"\nversion = "0.1.0"\nrequires-python = ">=3.13"\ndependencies = '+json.dumps(dependencies)+'\n\n[tool.setuptools]\npy-modules = ["'+title+'"]\n',
           'README.md':'# '+key+'\n\nOriginal CodingTeacher local CPU project. Create the displayed files in a fresh directory. Use the documented pinned Python/ML environment.\n\nRun `python -m unittest discover -s tests -v`. Optional packaging: `python -m pip install --no-deps --no-build-isolation .` in a disposable virtual environment.\n\n'+notes+'\n\nPractice extension: '+challenge+'\n'}
    PROJECTS[key]=dict(projectFiles=[dict(path=p,content=v) for p,v in files.items()],
        projectSolutionFiles=[dict(path=title+'.py',content=answer),dict(path='tests/test_project.py',content=answer_tests)],
        projectInstructions='Local project: Python 3.13 and '+(', '.join(dependencies) if dependencies else 'the standard library')+'. Create every displayed file, then run python -m unittest discover -s tests -v. The single-file Lab does not install or execute these projects. '+notes,
        rubric=['Run every base test, then apply the replacement answer files and run the answer tests.','Explain the input/schema, algorithm and resource contracts, including the negative cases.','Run the documented counterexample and show that the regression rejects it.','Record versions, split/evaluation assumptions and numerical tolerances.','Demonstrate the practice extension and document remaining production/hardware limitations.'],minutes=90,
        body=[notes,'Create the complete project files and keep domain logic separate from the command or model boundary. Read the tests before editing; they specify success and failure behavior.',
              'First run the base tests unchanged. Trace one positive input and one rejected input through the actual implementation. A small passing dataset establishes only this project contract.',
              'The practice extension is: '+challenge+' Attempt it before revealing the complete replacement answer files. The replacement includes its own executable regression tests.',
              'Review cleanup and reproducibility: use scoped temporary files, finish owned work, preserve feature/token order and store the intended model state. Avoid treating deterministic CPU behavior as evidence for a different device.',
              'Evaluate the project with the rubric. Code execution, observed test results and self-assessed project review remain distinct in the app.'])
    PROJECTS[key]['validationMutation']=dict(path=title+'.py',old=mutation[0],new=mutation[1])

CLI='''"""A small installed-module-friendly text CLI with explicit failures."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

def counts(text, minimum=1):
    if minimum < 1:
        raise ValueError("minimum must be positive")
    return {word:count for word,count in sorted(Counter(text.split()).items()) if count>=minimum}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("path",type=Path)
    parser.add_argument("--minimum",type=int,default=1)
    args=parser.parse_args(argv)
    try:
        result=counts(args.path.read_text(encoding="utf-8"),args.minimum)
    except (OSError,UnicodeError,ValueError) as error:
        print(type(error).__name__+": invalid input",file=sys.stderr)
        return 2
    print(json.dumps(result,sort_keys=True,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
'''
CLI_TEST='''import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from texttool import counts
class Tests(unittest.TestCase):
    def test_counts_and_empty(self):
        self.assertEqual(counts("red blue red"),{"blue":1,"red":2})
        self.assertEqual(counts(""),{})
        self.assertEqual(counts("x x y",2),{"x":2})
    def test_rejects_invalid_minimum(self):
        with self.assertRaises(ValueError):counts("x",0)
    def test_real_cli_streams_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"input.txt"
            path.write_text("café café tea",encoding="utf-8")
            run=subprocess.run([sys.executable,"-m","texttool",str(path),"--minimum","2"],capture_output=True,text=True,timeout=5)
            self.assertEqual(run.returncode,0)
            self.assertEqual(json.loads(run.stdout),{"café":2})
            self.assertEqual(run.stderr,"")
            failure=subprocess.run([sys.executable,"-m","texttool",str(path)+".missing"],capture_output=True,text=True,timeout=5)
            self.assertEqual(failure.returncode,2)
            self.assertEqual(failure.stdout,"")
            self.assertIn("invalid input",failure.stderr)
'''
CLI_ANSWER=CLI.replace('minimum=1):','minimum=1,lower=False):').replace('Counter(text.split())','Counter((text.casefold() if lower else text).split())').replace('    args=parser.parse_args(argv)','    parser.add_argument("--lower",action="store_true")\n    args=parser.parse_args(argv)').replace('args.minimum)','args.minimum,args.lower)')
project('capstone-cli','texttool',CLI,CLI_TEST,CLI_ANSWER,CLI_TEST+'''\n    def test_casefold_extension(self):
        self.assertEqual(counts("Straße STRASSE",lower=True),{"strasse":2})
        self.assertEqual(counts("A a"),{"A":1,"a":1})
''','Add an opt-in --lower mode using Unicode casefold while preserving existing defaults.',('if count>=minimum','if count>minimum'),[], 'This CLI tests UTF-8 input, deterministic JSON, minimum counts and actual stdout/stderr/exit-code behavior. Splitting on whitespace is an explicit tokenizer policy, not a universal linguistic definition of a word.')

NUM='''import numpy as np

def validate(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if x.ndim!=2 or y.ndim!=1 or len(x)!=len(y) or not len(y):
        raise ValueError("shape")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("nonfinite")
    return x,y

def loss(x,y,w):
    return float(np.mean((x@w-y)**2))

def gradient(x,y,w):
    return 2*x.T@(x@w-y)/len(y)

def fit(x,y,rate=0.1,steps=500):
    x,y=validate(x,y)
    if not np.isfinite(rate) or rate<=0 or not isinstance(steps,int) or isinstance(steps,bool) or steps<1:raise ValueError("optimizer")
    w=np.zeros(x.shape[1])
    for _ in range(steps):
        w -= rate*gradient(x,y,w)
    return w
'''
NUM_TEST='''import unittest,numpy as np
from numerics import gradient,loss,fit,validate
class Tests(unittest.TestCase):
    def setUp(self):
        self.x=np.array([[1,-1],[1,0],[1,1]],dtype=float)
        self.y=np.array([-1,1,3],dtype=float)
    def test_gradient_and_fit(self):
        w=np.array([0.3,-0.2]);h=1e-5
        numeric=np.array([(loss(self.x,self.y,w+np.eye(2)[i]*h)-loss(self.x,self.y,w-np.eye(2)[i]*h))/(2*h) for i in range(2)])
        np.testing.assert_allclose(gradient(self.x,self.y,w),numeric,rtol=1e-5,atol=1e-6)
        fitted=fit(self.x,self.y)
        oracle=np.linalg.lstsq(self.x,self.y,rcond=None)[0]
        np.testing.assert_allclose(fitted,oracle,atol=1e-6)
        self.assertLess(loss(self.x,self.y,fitted),1e-10)
    def test_bad_shapes_and_nonfinite(self):
        for rate in [0,float("nan")]:
            with self.assertRaises(ValueError):fit(self.x,self.y,rate=rate)
        for x,y in [([],[]),([[1]],[1,2]),([[float("nan")]],[1])]:
            with self.assertRaises(ValueError):validate(x,y)
'''
NUM_ANSWER=NUM.replace('def loss(x,y,w):','def loss(x,y,w,penalty=0.0):').replace('float(np.mean((x@w-y)**2))','float(np.mean((x@w-y)**2)+penalty*np.sum(w[1:]**2))').replace('def gradient(x,y,w):\n    return 2*x.T@(x@w-y)/len(y)','def gradient(x,y,w,penalty=0.0):\n    regularized=w.copy();regularized[0]=0\n    return 2*x.T@(x@w-y)/len(y)+2*penalty*regularized')
project('capstone-numerics','numerics',NUM,NUM_TEST,NUM_ANSWER,NUM_TEST+'''\n    def test_regularized_gradient(self):
        w=np.array([0.3,-0.2]);h=1e-5;penalty=0.7
        numeric=np.array([(loss(self.x,self.y,w+np.eye(2)[i]*h,penalty)-loss(self.x,self.y,w-np.eye(2)[i]*h,penalty))/(2*h) for i in range(2)])
        np.testing.assert_allclose(gradient(self.x,self.y,w,penalty),numeric,atol=1e-6)
''','Add an L2-regularized loss and gradient that exempt the intercept, and verify the gradient numerically.',('return 2*x.T@','return x.T@'),['numpy==2.2.6'],'An explicit intercept column and a small well-conditioned full-rank matrix keep this CPU optimization experiment interpretable. This project checks central-difference gradients and a least-squares oracle; it makes no convergence guarantee for arbitrary data or learning rates.')

PANDAS='''from dataclasses import dataclass
import pandas as pd

def validate(frame):
    if set(frame.columns)!={"id","value"} or frame.id.isna().any() or frame.id.duplicated().any():
        raise ValueError("schema or duplicate key")
    values=pd.to_numeric(frame.value,errors="raise")
    if values.dropna().isin([float("inf"),float("-inf")]).any():raise ValueError("nonfinite")
    return values

@dataclass(frozen=True)
class Cleaner:
    median:float
    @classmethod
    def fit(cls,frame):
        values=validate(frame)
        median=values.median()
        if pd.isna(median):raise ValueError("no observed training values")
        return cls(float(median))
    def transform(self,frame):
        values=validate(frame)
        result=frame.copy()
        result["value"]=values.fillna(self.median)
        return result

def clean_and_join(cleaner,frame,lookup):
    if set(lookup.columns)!={"id","group"}:raise ValueError("lookup schema")
    return cleaner.transform(frame).merge(lookup,on="id",how="left",validate="many_to_one")
'''
PANDAS_TEST='''import unittest,pandas as pd
from cleaning import Cleaner,clean_and_join
class Tests(unittest.TestCase):
    def test_training_only_median_and_original_preserved(self):
        train=pd.DataFrame({"id":[1,2,3],"value":[1,None,3]})
        cleaner=Cleaner.fit(train)
        test=pd.DataFrame({"id":[4,5],"value":[None,100]})
        result=cleaner.transform(test)
        self.assertEqual(result.value.tolist(),[2,100])
        self.assertTrue(pd.isna(test.value.iloc[0]))
    def test_cardinality_and_schema(self):
        frame=pd.DataFrame({"id":[1,2],"value":[1,3]})
        cleaner=Cleaner.fit(frame)
        lookup=pd.DataFrame({"id":[1,1],"group":["a","b"]})
        with self.assertRaises(pd.errors.MergeError):clean_and_join(cleaner,frame,lookup)
        with self.assertRaises(ValueError):cleaner.transform(pd.DataFrame({"id":[1,1],"value":[2,3]}))
        with self.assertRaises(ValueError):Cleaner.fit(pd.DataFrame({"id":[1],"value":[None]}))
'''
PANDAS_ANSWER=PANDAS.replace('def clean_and_join(cleaner,frame,lookup):','def clean_and_join(cleaner,frame,lookup,require_match=False):').replace('    return cleaner.transform(frame).merge(lookup,on="id",how="left",validate="many_to_one")','    result=cleaner.transform(frame).merge(lookup,on="id",how="left",validate="many_to_one",indicator=True)\n    if require_match and (result["_merge"]!="both").any():raise ValueError("unmatched key")\n    return result.drop(columns="_merge")')
project('capstone-pandas','cleaning',PANDAS,PANDAS_TEST,PANDAS_ANSWER,PANDAS_TEST+'''\n    def test_strict_lookup_coverage(self):
        frame=pd.DataFrame({"id":[1,2],"value":[1,3]})
        lookup=pd.DataFrame({"id":[1],"group":["a"]})
        with self.assertRaises(ValueError):clean_and_join(Cleaner.fit(frame),frame,lookup,require_match=True)
''','Add an opt-in strict lookup-coverage policy without changing the existing left-join behavior.',('values.fillna(self.median)','values.fillna(values.median())'),['pandas==2.3.3','numpy==2.2.6'],'This pipeline fits missing-value policy using training data only, preserves its input frame and validates key cardinality. It uses a tiny synthetic table; timestamp joins, large-data behavior and every book-specific data pipeline remain further work.')

TAB='''import hashlib,json
from pathlib import Path
import joblib,numpy as np,sklearn
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
FEATURES=["signal","context"]

def fit_and_evaluate(seed=7):
    rng=np.random.default_rng(seed)
    x=rng.normal(size=(160,2));y=(x[:,0]+0.5*x[:,1]>0).astype(int)
    train,test=train_test_split(np.arange(len(y)),test_size=0.25,random_state=seed,stratify=y)
    model=make_pipeline(StandardScaler(),LogisticRegression(random_state=seed)).fit(x[train],y[train])
    baseline=DummyClassifier(strategy="most_frequent").fit(x[train],y[train])
    return model,{"accuracy":model.score(x[test],y[test]),"baseline":baseline.score(x[test],y[test]),"train":train.tolist(),"test":test.tolist()}

def features(records):
    if any(set(row)!=set(FEATURES) for row in records):raise ValueError("schema")
    values=np.array([[row[name] for name in FEATURES] for row in records],dtype=float)
    if not np.isfinite(values).all():raise ValueError("nonfinite")
    return values

def save(model,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    path=directory/"model.joblib";joblib.dump(model,path)
    receipt={"features":FEATURES,"sklearn":sklearn.__version__,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (directory/"receipt.json").write_text(json.dumps(receipt,sort_keys=True))

def load_owned(directory):
    directory=Path(directory);path=directory/"model.joblib"
    receipt=json.loads((directory/"receipt.json").read_text())
    if receipt["features"]!=FEATURES or receipt["sklearn"]!=sklearn.__version__:raise ValueError("compatibility")
    if hashlib.sha256(path.read_bytes()).hexdigest()!=receipt["sha256"]:raise ValueError("checksum")
    return joblib.load(path) # Only this application's owned artifact; never accept untrusted pickle/joblib.
'''
TAB_TEST='''import tempfile,unittest,numpy as np
from pathlib import Path
from tabular import fit_and_evaluate,features,save,load_owned
class Tests(unittest.TestCase):
    def test_holdout_and_artifact(self):
        model,report=fit_and_evaluate()
        self.assertTrue(set(report["train"]).isdisjoint(report["test"]))
        self.assertGreater(report["accuracy"],0.85)
        self.assertGreater(report["accuracy"],report["baseline"])
        x=features([{"context":0,"signal":-2},{"signal":2,"context":0}])
        self.assertEqual(model.predict(x).tolist(),[0,1])
        with tempfile.TemporaryDirectory() as directory:
            save(model,directory)
            np.testing.assert_array_equal(load_owned(directory).predict(x),model.predict(x))
            path=Path(directory)/"model.joblib";path.write_bytes(path.read_bytes()+b"tampered")
            with self.assertRaises(ValueError):load_owned(directory)
    def test_schema_and_nonfinite(self):
        for rows in [[{"signal":1}],[{"signal":float("nan"),"context":0}]]:
            with self.assertRaises(ValueError):features(rows)
'''
TAB_ANSWER=TAB.replace('def fit_and_evaluate(seed=7):','def fit_and_evaluate(seed=7,class_weight=None):').replace('LogisticRegression(random_state=seed)','LogisticRegression(random_state=seed,class_weight=class_weight)')
project('capstone-tabular','tabular',TAB,TAB_TEST,TAB_ANSWER,TAB_TEST+'''\n    def test_balanced_option(self):
        model,report=fit_and_evaluate(class_weight="balanced")
        self.assertEqual(model.named_steps["logisticregression"].class_weight,"balanced")
        self.assertGreater(report["accuracy"],0.85)
''','Add an explicit class-weight option and preserve leakage-safe evaluation and artifact compatibility.',('x[train],y[train]','x[train],1-y[train]'),['numpy==2.2.6','scikit-learn==1.7.2','joblib==1.5.2'],'A deterministic synthetic classifier compares a fitted pipeline with a dummy baseline on disjoint held-out IDs. Checksums and version metadata detect accidental corruption; joblib remains executable deserialization and is used only for locally owned artifacts.')

VISION='''import torch

def examples(seed,n=32):
    generator=torch.Generator().manual_seed(seed)
    y=torch.arange(n)%2
    x=torch.zeros(n,1,4,4)
    x[y==0,:,:,1]=1
    x[y==1,:,1,:]=1
    return x+torch.randn(x.shape,generator=generator)*0.03,y

class Vision(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.network=torch.nn.Sequential(torch.nn.Conv2d(1,4,3,padding=1),torch.nn.ReLU(),torch.nn.Flatten(),torch.nn.Linear(64,2))
    def forward(self,x):return self.network(x)

def train(steps=50):
    if not isinstance(steps,int) or isinstance(steps,bool) or steps<1:raise ValueError("steps")
    torch.set_num_threads(1);torch.manual_seed(7)
    x,y=examples(7);model=Vision()
    optimizer=torch.optim.Adam(model.parameters(),lr=0.03)
    for step in range(steps):
        model.train();optimizer.zero_grad(set_to_none=True)
        loss=torch.nn.functional.cross_entropy(model(x),y)
        loss.backward();optimizer.step()
    model.eval()
    test,target=examples(9)
    with torch.no_grad():accuracy=float((model(test).argmax(1)==target).float().mean())
    return model,{"loss":float(loss.detach()),"accuracy":accuracy,"steps":step+1}

def predict(model,x):
    if x.ndim!=4 or tuple(x.shape[1:])!=(1,4,4) or not torch.isfinite(x).all():raise ValueError("image shape or nonfinite")
    model.eval()
    with torch.inference_mode():return model(x).argmax(1)

def save(model,path):torch.save(model.state_dict(),path)
def load(path):
    model=Vision();model.load_state_dict(torch.load(path,map_location="cpu",weights_only=True));model.eval();return model
'''
VISION_TEST='''import tempfile,unittest,torch
from pathlib import Path
from vision import train,predict,examples,save,load
class Tests(unittest.TestCase):
    def test_training_and_reload(self):
        model,report=train()
        self.assertGreater(report["accuracy"],0.95);self.assertLess(report["loss"],0.05)
        x,y=examples(11)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"weights.pt";save(model,path)
            self.assertTrue(torch.equal(predict(model,x),predict(load(path),x)))
        with self.assertRaises(ValueError):predict(model,torch.zeros(2,4,4))
        with self.assertRaises(ValueError):train(steps=0)
'''
VISION_ANSWER=VISION.replace('def train(steps=50):','def train(steps=50,target_loss=None):').replace('loss.backward();optimizer.step()','loss.backward();optimizer.step()\n        if target_loss is not None and float(loss.detach())<target_loss:break')
project('capstone-vision','vision',VISION,VISION_TEST,VISION_ANSWER,VISION_TEST+'''\n    def test_optional_early_stop(self):
        model,report=train(steps=50,target_loss=2.0)
        self.assertEqual(report["steps"],1)
''','Add opt-in early stopping on the training loss, explicitly labelling it as a diagnostic rather than validation-based model selection.',('model(x),y','model(x),1-y'),['torch==2.8.0'],'Train a real small CNN on generated horizontal/vertical stripe images and evaluate on independently seeded images. This checks mechanics and checkpoint parity on CPU, not real-world vision generalization, pretrained weights or accelerator behavior.')

TEXT='''import torch
VOCAB={"<pad>":0,"<unk>":1,"good":2,"bright":3,"bad":4,"dark":5,"movie":6}

def encode(texts):
    ids=[[(VOCAB.get(token,1) if token!="<pad>" else 1) for token in text.split()][:6] for text in texts]
    if any(not row for row in ids):raise ValueError("empty text")
    width=max(map(len,ids))
    return torch.tensor([row+[0]*(width-len(row)) for row in ids])

class TextModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding=torch.nn.Embedding(len(VOCAB),8,padding_idx=0)
        self.attention=torch.nn.MultiheadAttention(8,2,batch_first=True,dropout=0)
        self.output=torch.nn.Linear(8,2)
    def forward(self,ids):
        if ids.ndim!=2 or ids.numel()==0 or bool((ids.ne(0).sum(1)==0).any()):raise ValueError("all-padding sequence")
        mask=ids==0;values=self.embedding(ids)
        attended,_=self.attention(values,values,values,key_padding_mask=mask,need_weights=False)
        pooled=(attended*(~mask).unsqueeze(-1)).sum(1)/(~mask).sum(1,keepdim=True)
        return self.output(pooled)

def train():
    torch.set_num_threads(1);torch.manual_seed(7)
    texts=["good movie","bright","bad movie","dark"]*4
    target=torch.tensor([1,1,0,0]*4);ids=encode(texts)
    model=TextModel();optimizer=torch.optim.Adam(model.parameters(),lr=0.03)
    for _ in range(60):
        optimizer.zero_grad(set_to_none=True)
        loss=torch.nn.functional.cross_entropy(model(ids),target)
        loss.backward();optimizer.step()
    model.eval()
    return model,float(loss.detach())

def predict(model,texts):
    if not texts:return []
    model.eval()
    with torch.inference_mode():return model(encode(texts)).argmax(1).tolist()
'''
TEXT_TEST='''import unittest,torch
from textmodel import train,predict,encode,VOCAB
class Tests(unittest.TestCase):
    def test_fit_masks_unknowns_and_reload(self):
        model,loss=train();self.assertLess(loss,0.02)
        self.assertEqual(predict(model,["good movie","bad movie","bright","dark"]),[1,0,1,0])
        self.assertEqual(int(encode(["new"])[0,0]),VOCAB["<unk>"])
        alone=predict(model,["bright"])
        padded=predict(model,["bright","good movie"])
        self.assertEqual(alone[0],padded[0])
        self.assertEqual(predict(model,[]),[])
        special=encode(["<pad>","<pad> <pad>"])
        self.assertEqual(int(special[0,0]),VOCAB["<unk>"])
        self.assertTrue(bool(torch.isfinite(model(special)).all()))
        with self.assertRaises(ValueError):model(torch.zeros(1,2,dtype=torch.long))
        with self.assertRaises(ValueError):encode([""])
        from textmodel import TextModel
        other=TextModel();other.load_state_dict(model.state_dict())
        self.assertEqual(predict(model,["dark"]),predict(other,["dark"]))
'''
TEXT_ANSWER=TEXT+'''\ndef predict_batched(model,texts,batch_size=2):
    if batch_size<1:raise ValueError("batch size")
    result=[]
    for offset in range(0,len(texts),batch_size):
        result.extend(predict(model,texts[offset:offset+batch_size]))
    return result
'''
project('capstone-text','textmodel',TEXT,TEXT_TEST,TEXT_ANSWER,TEXT_TEST+'''\n    def test_bounded_inference_parity(self):
        from textmodel import predict_batched
        model,_=train();texts=["good movie","dark","bright"]
        self.assertEqual(predict(model,texts),predict_batched(model,texts,1))
        with self.assertRaises(ValueError):predict_batched(model,texts,0)
''','Add bounded inference batches and prove predictions agree across different padding/batch compositions.',('return self.output(pooled)','return self.output(pooled)*0'),['torch==2.8.0'],'A tiny attention classifier uses a fixed train-only vocabulary, an unknown token, padding masks and masked pooling. The artificial sentiment words establish a small mechanics test, not language understanding or unseen-domain NLP quality.')

FORECAST='''import numpy as np

def evaluate(values,window=3):
    values=np.asarray(values,dtype=float)
    if values.ndim!=1 or len(values)<=window or window<1 or not np.isfinite(values).all():raise ValueError("series")
    predictions=[];baseline=[];targets=[];origins=[]
    for origin in range(window,len(values)):
        history=values[:origin]
        predictions.append(float(history[-window:].mean()))
        baseline.append(float(history[-1]))
        targets.append(float(values[origin]));origins.append(origin)
    errors=np.abs(np.asarray(predictions)-targets)
    return {"origins":origins,"predictions":predictions,"baseline":baseline,"targets":targets,"mae":float(errors.mean())}
'''
FORECAST_TEST='''import unittest
from forecasting import evaluate
class Tests(unittest.TestCase):
    def test_expected_forecasts_and_future_isolation(self):
        report=evaluate([1,2,3,4,5],2)
        self.assertEqual(report["predictions"],[1.5,2.5,3.5])
        self.assertEqual(report["targets"],[3,4,5])
        self.assertEqual(report["mae"],1.5)
        changed=evaluate([1,2,3,400,500],2)
        self.assertEqual(report["predictions"][:2],changed["predictions"][:2])
        self.assertEqual(report["baseline"],[2,3,4])
    def test_invalid_series(self):
        for series in [[],[1,2],[1,float("nan"),3,4]]:
            with self.assertRaises(ValueError):evaluate(series)
'''
FORECAST_ANSWER=FORECAST.replace('def evaluate(values,window=3):','def evaluate(values,window=3,horizon=1):').replace('len(values)<=window or window<1','len(values)<window+horizon or window<1 or horizon<1').replace('range(window,len(values))','range(window,len(values)-horizon+1)').replace('values[origin]','values[origin+horizon-1]')
project('capstone-forecast','forecasting',FORECAST,FORECAST_TEST,FORECAST_ANSWER,FORECAST_TEST+'''\n    def test_horizon_two(self):
        report=evaluate([1,2,3,4,5],window=2,horizon=2)
        self.assertEqual(report["predictions"],[1.5,2.5])
        self.assertEqual(report["targets"],[4,5])
''','Generalize to a positive forecast horizon without exposing future observations to the history window.',('history=values[:origin]','history=values[:origin+1]'),['numpy==2.2.6'],'Rolling-origin evaluation compares a trailing-mean candidate with a last-observation baseline. Future-perturbation tests expose leakage. Neither baseline nor candidate is guaranteed to win on an arbitrary series; seasonality, uncertainty intervals and nonstationary regimes remain separate work.')

# The service project is authored below; every project stays local and CPU-only.
SERVICE='''from collections import deque
from contextlib import contextmanager
import hashlib,json,math,socket,threading
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import numpy as np
FEATURES=["signal","context"]

def features(record):
    if not isinstance(record,dict) or set(record)!=set(FEATURES):raise ValueError("schema")
    row=[record[name] for name in FEATURES]
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in row):raise ValueError("numeric")
    return row

def train(records,targets,directory):
    x=np.asarray([features(row) for row in records],dtype=float);y=np.asarray(targets,dtype=float)
    if x.ndim!=2 or y.shape!=(len(x),) or not len(y) or not np.isfinite(y).all():raise ValueError("training")
    design=np.column_stack([np.ones(len(x)),x])
    weights,_,rank,_=np.linalg.lstsq(design,y,rcond=None)
    if rank!=3:raise ValueError("rank")
    payload={"version":"1","features":FEATURES,"weights":weights.tolist(),"reference":float(x[:,0].mean())}
    raw=json.dumps(payload,sort_keys=True,allow_nan=False).encode()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    (directory/"model.json").write_bytes(raw)
    (directory/"manifest.json").write_text(json.dumps({"sha256":hashlib.sha256(raw).hexdigest()}))

class Model:
    def __init__(self,payload):
        if payload["version"]!="1" or payload["features"]!=FEATURES or len(payload["weights"])!=3:raise ValueError("compatibility")
        if not all(math.isfinite(x) for x in payload["weights"]+[payload["reference"]]):raise ValueError("nonfinite")
        self.payload=payload
    def predict(self,record):
        row=features(record);weights=self.payload["weights"]
        result=weights[0]+sum(a*b for a,b in zip(weights[1:],row,strict=True))
        if not math.isfinite(result):raise ValueError("nonfinite prediction")
        return result

def load(directory):
    directory=Path(directory)
    with (directory/"model.json").open("rb") as stream:raw=stream.read(65537)
    if len(raw)>65536:raise ValueError("artifact size")
    expected=json.loads((directory/"manifest.json").read_text())["sha256"]
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("checksum")
    return Model(json.loads(raw))

@contextmanager
def serving(model,connected=None):
    window=deque(maxlen=128);count=[0]
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            self.request.settimeout(1.0)
            super().setup()
            if connected is not None:connected.set()
        def log_message(self,*args):pass
        def reply(self,status,value):
            raw=json.dumps(value,allow_nan=False).encode()
            self.send_response(status);self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(raw)));self.end_headers()
            try:self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            if self.path=="/health":self.reply(200,{"status":"ok","version":"1"})
            elif self.path=="/metrics":
                mean=sum(window)/len(window) if window else model.payload["reference"]
                self.reply(200,{"count":count[0],"window":len(window),"drift":abs(mean-model.payload["reference"])>5})
            else:self.reply(404,{"error":"unknown route"})
        def do_POST(self):
            if self.path!="/predict":self.reply(404,{"error":"unknown route"});return
            try:
                length=int(self.headers.get("Content-Length","-1"))
                if length<0 or length>1024 or self.headers.get("Transfer-Encoding"):
                    self.reply(413,{"error":"body limit"});return
                request=json.loads(self.rfile.read(length).decode("utf-8"))
                prediction=model.predict(request)
                window.append(request["signal"]);count[0]+=1
                self.reply(200,{"prediction":prediction,"version":"1"})
            except (ValueError,KeyError,TypeError,socket.timeout,OverflowError):
                self.reply(400,{"error":"invalid request"})
    class Server(HTTPServer):request_queue_size=4
    server=Server(("127.0.0.1",0),Handler)
    thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.02},name="codingteacher-model-"+str(id(server)))
    thread.start()
    try:yield server.server_address
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
        if thread.is_alive():raise RuntimeError("server thread did not finish")
'''
SERVICE_TEST='''import hashlib,json,socket,tempfile,threading,time,unittest,urllib.request,urllib.error
from pathlib import Path
from service import train,load,serving
class Tests(unittest.TestCase):
    def artifact(self,directory):
        rows=[{"signal":0,"context":0},{"signal":1,"context":0},{"signal":0,"context":1},{"signal":2,"context":1}]
        train(rows,[1,3,0,4],directory)
        return load(directory)
    def request(self,address,path,record=None):
        data=None if record is None else json.dumps(record).encode()
        request=urllib.request.Request("http://%s:%s%s"%(*address,path),data=data,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(request,timeout=3) as response:return json.load(response)
    def test_train_http_parity_drift_and_teardown(self):
        before={t.ident for t in threading.enumerate()}
        with tempfile.TemporaryDirectory() as directory:
            model=self.artifact(directory)
            record={"context":1,"signal":2}
            self.assertAlmostEqual(model.predict(record),4)
            with serving(model) as address:
                self.assertEqual(self.request(address,"/health")["status"],"ok")
                self.assertAlmostEqual(self.request(address,"/predict",record)["prediction"],model.predict(record))
                for _ in range(130):self.request(address,"/predict",{"signal":100,"context":0})
                metrics=self.request(address,"/metrics")
                self.assertEqual(metrics["count"],131);self.assertEqual(metrics["window"],128);self.assertTrue(metrics["drift"])
                with self.assertRaises(urllib.error.HTTPError) as error:self.request(address,"/predict",{"signal":1})
                self.assertEqual(error.exception.code,400)
                with self.assertRaises(urllib.error.HTTPError) as error:self.request(address,"/predict",{"signal":True,"context":0})
                self.assertEqual(error.exception.code,400)
            self.assertFalse(any(t.name.startswith("codingteacher-model-") and t.ident not in before for t in threading.enumerate()))
            path=Path(directory)/"model.json";path.write_bytes(path.read_bytes()+b" ")
            with self.assertRaises(ValueError):load(directory)
    def test_idle_connection_has_bounded_teardown(self):
        with tempfile.TemporaryDirectory() as directory:
            model=self.artifact(directory)
            connected=threading.Event()
            scope=serving(model,connected);address=scope.__enter__()
            client=socket.create_connection(address,timeout=2)
            client.sendall(b"GET /health HTTP/1.0\\r\\n")
            self.assertTrue(connected.wait(2),"server must accept the held-open client")
            finished=threading.Event();failures=[]
            def stop():
                try:scope.__exit__(None,None,None)
                except BaseException as error:failures.append(error)
                finally:finished.set()
            stopper=threading.Thread(target=stop)
            stopper.start()
            try:
                stopped=finished.wait(3)
            finally:
                client.close();stopper.join(timeout=3)
            self.assertTrue(stopped,"teardown must finish while the client remains open")
            self.assertFalse(stopper.is_alive())
            self.assertEqual(failures,[])
'''
SERVICE_ANSWER=SERVICE.replace('if self.path!="/predict":','if self.path not in ("/predict","/batch"):').replace('                prediction=model.predict(request)\n                window.append(request["signal"]);count[0]+=1\n                self.reply(200,{"prediction":prediction,"version":"1"})','''                if self.path=="/batch":
                    if not isinstance(request,list) or not 1<=len(request)<=16:raise ValueError("batch")
                    predictions=[model.predict(row) for row in request]
                    for row in request:window.append(row["signal"])
                    count[0]+=len(request)
                    self.reply(200,{"predictions":predictions,"version":"1"})
                else:
                    prediction=model.predict(request)
                    window.append(request["signal"]);count[0]+=1
                    self.reply(200,{"prediction":prediction,"version":"1"})''')
project('capstone-production','service',SERVICE,SERVICE_TEST,SERVICE_ANSWER,SERVICE_TEST+'''\n    def test_bounded_batch_parity_and_no_partial_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            model=self.artifact(directory)
            with serving(model) as address:
                rows=[{"signal":1,"context":0},{"signal":2,"context":1}]
                response=self.request(address,"/batch",rows)
                self.assertEqual(len(response["predictions"]),2)
                for actual,row in zip(response["predictions"],rows):self.assertAlmostEqual(actual,model.predict(row))
                with self.assertRaises(urllib.error.HTTPError):self.request(address,"/batch",rows+[{}])
                self.assertEqual(self.request(address,"/metrics")["count"],2)
''','Add a batch endpoint capped at 16 records; validate the whole batch before committing any monitor observations.',('weights[0]+sum(a*b','weights[0]-sum(a*b'),['numpy==2.2.6'],'This local single-request HTTP service trains a linear model, loads JSON with an independently stored checksum, validates feature schemas, caps bodies and monitor history, and joins its server thread. It binds only loopback. The tests include real HTTP, malformed input, drift, tampered artifacts and an unread client. It is a local teaching service, not a deployed production platform. Runbook: retain a previous owned model/manifest pair; stop the server before replacing both files; verify load and smoke predictions before restart; restore both files on a failed gate. TLS, authentication, hostile public traffic, persistent telemetry and crash-safe atomic artifact publication require separate deployment work.')

if __name__=='__main__':
    Path(__file__).with_name('python_projects.json').write_text(json.dumps(PROJECTS,indent=2)+'\n')
    print('Authored',len(PROJECTS),'complete base/answer projects')

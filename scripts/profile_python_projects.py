"""Scoped CPU project ownership/RSS observation; not a native heap or GPU leak proof."""
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time
import tracemalloc
import weakref
import torch

ROOT=Path(__file__).resolve().parent.parent

def main():
    assert sys.platform=='darwin','This receipt records macOS ru_maxrss bytes'
    curriculum_path=ROOT/'CodingTeacher/curriculum.json'
    curriculum=json.loads(curriculum_path.read_text())
    torch.set_num_threads(1)
    modules={}
    for key,filename in [('capstone-vision','vision.py'),('capstone-text','textmodel.py')]:
        lesson=next(l for l in curriculum['lessons'] if l['id']=='guide.python.'+key)
        content=next(f['content'] for f in lesson['projectFiles'] if f['path']==filename)
        directory=ROOT/'.build/python-memory-projects'/key
        directory.mkdir(parents=True,exist_ok=True)
        path=directory/filename;path.write_text(content)
        name='profile_'+key.replace('-','_')
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        modules[key]=module
    rows=[]
    tracemalloc.start()
    for iteration in range(1,4):
        for key,module in modules.items():
            started=time.monotonic()
            model,receipt=module.train()
            reference=weakref.ref(model)
            del model;gc.collect()
            alive=reference() is not None
            assert not alive,(key,'trained model retained after owner release')
            current,peak=tracemalloc.get_traced_memory()
            rows.append(dict(project=key,iteration=iteration,modelStillAlive=alive,
                             pythonTracedCurrentBytes=current,pythonTracedPeakBytes=peak,
                             processPeakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                             seconds=round(time.monotonic()-started,3)))
    tracemalloc.stop()
    report=dict(scope='Three sequential train/release/GC rounds each for the exact bundled vision and text CPU base projects. Six weak model references released. Process peak RSS and Python tracemalloc include startup/cache effects; tracemalloc excludes most tensor/native allocation. No universal leak freedom, GPU, process-worker, long-running service or native-app heap claim.',
                python=sys.version.split()[0],torch=torch.__version__,curriculumSHA256=hashlib.sha256(curriculum_path.read_bytes()).hexdigest(),measurements=rows)
    (ROOT/'docs/python-memory-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

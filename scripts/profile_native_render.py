"""Run one serial native suite and sample selected simulator-app RSS, never heap contents."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid
from owned_process import run_owned

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, type=uuid.UUID)
    args = parser.parse_args()
    if sys.platform != 'darwin':
        raise SystemExit('This development observation requires macOS and an installed iOS simulator.')
    device = str(args.device).upper()
    env = dict(os.environ, DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer')
    xcode = '/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild'
    command = [xcode,'-project','CodingTeacher.xcodeproj','-scheme','CodingTeacher',
               '-destination','platform=iOS Simulator,id='+device,'-parallel-testing-enabled','NO',
               '-derivedDataPath','.build/ios','-clonedSourcePackagesDirPath',
               str(ROOT/'.build/ios/SourcePackages'),
               'ONLY_ACTIVE_ARCH=YES','ARCHS=arm64','CODE_SIGNING_ALLOWED=YES','test']
    workspace = ROOT/'.build/python-native-observations'
    workspace.mkdir(parents=True,exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='run-',dir=workspace))
    stop = threading.Event()
    observations = {}
    errors = []
    def sample():
        while not stop.is_set():
            try:
                snapshot = subprocess.run(['/bin/ps','-axww','-o','pid=','-o','rss=','-o','comm='],
                                          capture_output=True,text=True,timeout=2,check=True)
                for line in snapshot.stdout.splitlines():
                    fields = line.strip().split(None,2)
                    if len(fields)!=3: continue
                    pid,rss,path = fields
                    if device.lower() not in path.lower() or not path.endswith('/CodingTeacher.app/CodingTeacher'): continue
                    value = int(rss)*1024
                    row = observations.setdefault(pid,dict(samples=0,firstRSSBytes=value,sampledPeakRSSBytes=value,lastRSSBytes=value))
                    row['samples'] += 1
                    row['sampledPeakRSSBytes'] = max(row['sampledPeakRSSBytes'],value)
                    row['lastRSSBytes'] = value
            except (OSError,ValueError,subprocess.SubprocessError) as error:
                errors.append(type(error).__name__)
                return
            stop.wait(0.5)
    version = run_owned([xcode,'-version'],cwd=ROOT,env=env,timeout=10,input='').stdout.strip()
    with ThreadPoolExecutor(max_workers=1,thread_name_prefix='native-rss') as pool:
        worker = pool.submit(sample)
        try:
            result = run_owned(command,cwd=ROOT,env=env,timeout=600,input='')
        finally:
            stop.set()
            worker.result(timeout=5)
    # The worker is joined before reading its locally owned observations or ending the run.
    (directory/'native.log').write_text(result.stdout+result.stderr)
    paths = ['CodingTeacherTests/SourcePresentationTests.swift','CodingTeacherTests/PythonPracticeTests.swift',
             'CodingTeacherTests/SnapshotTestSupport.swift','CodingTeacher/AssessmentModels.swift','CodingTeacher/SourceCourseViews.swift']
    report = dict(scope='One serial native-suite run. Half-second ps RSS samples for matching app processes on the selected simulator, including startup/prior process effects. Excludes WebKit/renderer/compiler processes and GPU allocations. Not a heap/leak detector, settled baseline or universal memory guarantee.',
                  command=command,xcode=version,device=device,intervalSeconds=0.5,
                  returnCode=result.returncode,processesObserved=len(observations),
                  samples=sum(r['samples'] for r in observations.values()),
                  sampledPeakRSSBytes=max((r['sampledPeakRSSBytes'] for r in observations.values()),default=None),
                  samplingErrors=errors,samplerJoined=worker.done(),
                  curriculumSHA256=hashlib.sha256((ROOT/'CodingTeacher/curriculum.json').read_bytes()).hexdigest(),
                  sourceHashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (directory/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (directory/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    print(json.dumps(dict(report,logDirectory=str(directory)),indent=2))
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()

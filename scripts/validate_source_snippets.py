"""Run original executable source-study companions and check exact outputs locally."""
import datetime,json,os,shutil,subprocess,sys
from pathlib import Path
from source_snippets import SNIPPETS
from source_topics import records
ROOT=Path(__file__).resolve().parent.parent
content=json.loads((ROOT/'CodingTeacher/curriculum.json').read_text())
tracks={x['key']:x['trackID'] for x in records()}
env=os.environ.copy();env['ELAN_HOME']=str(ROOT/'.build/toolchains/elan')
tools={'python':sys.executable,'cpp':shutil.which('clang++'),'rust':shutil.which('rustc'),'lean':str(ROOT/'.build/toolchains/elan/bin/lean')}
results=[]
for key,(source,expected) in SNIPPETS.items():
    language=tracks[key];id='source.'+key
    bundled=next(l for l in content['lessons'] if l['id']==id)
    assert bundled['code']==source, id
    directory=ROOT/'.build/source-snippets'/key;directory.mkdir(parents=True,exist_ok=True)
    path=directory/('Main.lean' if language=='lean' else 'main.'+{'python':'py','cpp':'cpp','rust':'rs'}[language]);path.write_text(source)
    command=[tools[language],str(path)]
    if language=='lean':command=[tools[language],'-DwarningAsError=true',str(path)]
    if language in ['cpp','rust']:
        binary=directory/'program'
        command=[tools[language],'-std=c++20','-pthread',str(path),'-o',str(binary)] if language=='cpp' else [tools[language],'--edition=2021',str(path),'-o',str(binary)]
    try:
        compiled=subprocess.run(command,capture_output=True,text=True,env=env,timeout=30)
        result=subprocess.run([str(binary)],capture_output=True,text=True,env=env,timeout=10) if language in ['cpp','rust'] and compiled.returncode==0 else compiled
        passed=compiled.returncode==0 and result.returncode==0 and result.stdout==expected
        entry=dict(lessonID=id,language=language,passed=passed,stdout=result.stdout,expectedStdout=expected,stderr=result.stderr,exitCode=result.returncode)
    except Exception as e:entry=dict(lessonID=id,language=language,passed=False,error=str(e))
    results.append(entry)
    if not entry['passed']:print(json.dumps(entry),flush=True)
report=dict(checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Original source-study example programs only; local checks, not remote execution or open-answer grading',total=len(results),passed=sum(x['passed'] for x in results),cases=results)
(ROOT/'.build/source-snippet-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Source programs:',report['passed'],'/',report['total'])
raise SystemExit(0 if report['passed']==report['total'] else 1)

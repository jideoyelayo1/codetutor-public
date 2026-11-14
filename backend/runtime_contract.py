"""Fixed app-to-engine contract shared by the gateway and deployment checks."""
from pathlib import Path
import re
ALIASES = {
    'python': ['python', 'python3'], 'python-ml': ['python-ml'],
    'cpp': ['c++', 'cpp'], 'rust': ['rust'],
    'ocaml': ['ocaml'], 'lean': ['lean4', 'lean'],
}
FILENAMES = {'python':'main.py', 'python-ml':'main.py', 'cpp':'main.cpp', 'rust':'main.rs', 'ocaml':'main.ml', 'lean':'Main.lean'}
MINIMUMS = {'python':(3,13), 'python-ml':(3,13), 'rust':(1,99), 'ocaml':(4,14), 'lean':(4,35)}
ML_PYTHON_VERSION = '3.13.14'
# Read the same lock used for package builds; normalize CPU wheel local versions.
ML_VERSIONS = {}
for line in (Path(__file__).parent/'runtimes/python-ml/requirements.lock').read_text().splitlines():
    match=re.match(r'^([A-Za-z0-9-]+)==([0-9A-Za-z.+]+)',line)
    if match:
        name,version=match.groups()
        normalized=version.removesuffix('+cpu')
        if name in ML_VERSIONS and ML_VERSIONS[name] != normalized:
            raise ValueError('Conflicting ML lock versions')
        ML_VERSIONS[name]=normalized

LINUX_ML_VERSIONS = {**ML_VERSIONS, 'torch':ML_VERSIONS['torch']+'+cpu'}


def numeric_version(version):
    try: return tuple(int(p) for p in version.split('.')[:3])
    except ValueError: return (0,)


def candidates(language, runtimes):
    matches = [r for r in runtimes if set(ALIASES[language]) & {r['language'], *r.get('aliases', [])}]
    return sorted((r for r in matches if numeric_version(r['version']) >= MINIMUMS.get(language, (0,))),
                  key=lambda r: numeric_version(r['version']), reverse=True)


def choose_runtime(language, runtimes):
    return next(iter(candidates(language, runtimes)), None)


def execution_payload(language, source, runtime, stdin=''):
    return {'language':runtime['language'], 'version':runtime['version'],
            'files':[{'name':FILENAMES[language], 'content':source}], 'stdin':stdin, 'args':[],
            'compile_timeout':15000, 'run_timeout':8000 if language in ['lean','python-ml'] else 3000,
            'compile_memory_limit':1073741824,
            'run_memory_limit':1073741824 if language in ['lean','python-ml'] else 268435456}

"""Load host-owned acceptance records; never treat an installed alias as verification."""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from runtime_cases import ROOT, all_cases
from runtime_contract import ALIASES, LINUX_ML_VERSIONS, candidates

@dataclass(frozen=True)
class VerifiedRuntime:
    id: str
    language: str
    version: str
    packages: tuple[str, ...] = ()


def engine_url(value):
    parsed=urlsplit(value)
    if parsed.scheme not in ['http','https'] or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('PISTON_URL must be an HTTP(S) engine URL without credentials, query, or fragment')
    return value.rstrip('/')


def checks_digest():
    paths=['CodingTeacher/curriculum.json','scripts/learning_pack.json','scripts/source_snippets.py','scripts/rust_guide.py','scripts/rust_guide_content.json','scripts/lean_guide.py','scripts/lean_guide_content.json','scripts/guide_builder.py',
           'backend/runtime_cases.py','backend/runtime_contract.py','backend/runtime_verification.py',
           'backend/verify_engine.py','backend/gateway.py',
           'backend/runtimes/python-ml/requirements.lock',
           'backend/runtimes/python-ml/run','backend/runtimes/lean4/run',
           'scripts/ocaml_guide.py',
           *sorted(str(p.relative_to(ROOT)) for p in (ROOT/'scripts/ocaml_guide_content').glob('*.json'))]
    digest=hashlib.sha256()
    for name in paths:
        digest.update(name.encode()+b'\0')
        digest.update((ROOT/name).read_bytes()+b'\0')
    return digest.hexdigest()


def load_verification(path: Path, piston_url: str):
    data=json.loads(path.read_text())
    if (data.get('schemaVersion') != 1 or data.get('engineURL') != engine_url(piston_url)
            or data.get('checksDigest') != checks_digest()):
        raise ValueError('Runtime verification is stale or belongs to another engine; rerun verify_engine.py')
    counts=Counter(c.language for c in all_cases())
    verified=[]
    for item in data['runtimes']:
        if (item['id'] not in ALIASES or item['id'] in {r.id for r in verified}
                or item['caseCount'] != counts[item['id']]
                or item.get('passed') is not True
                or not isinstance(item['language'],str) or not isinstance(item['version'],str)):
            raise ValueError('Invalid verified runtime record')
        packages=item['packages']
        if not isinstance(packages,list) or not all(isinstance(p,str) for p in packages):
            raise ValueError('Invalid package metadata')
        if item['id']=='python-ml':
            actual=dict(p.split('==',1) for p in packages)
            if actual != LINUX_ML_VERSIONS:
                raise ValueError('ML versions do not match the checked profile')
        elif packages:
            raise ValueError('Unexpected package metadata for a standard runtime')
        verified.append(VerifiedRuntime(item['id'],item['language'],item['version'],tuple(packages)))
    return tuple(verified)


def select_verified(language, installed, verified):
    for record in verified:
        if record.id == language:
            return next((r for r in candidates(language,installed)
                         if r['language']==record.language and r['version']==record.version),None)
    return None

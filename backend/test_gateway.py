import httpx
import pytest
from fastapi.testclient import TestClient
from gateway import Config, create_app, choose_runtime, normalize
from runtime_verification import VerifiedRuntime
TOKEN='t'*40
HEADERS={'Authorization':'Bearer '+TOKEN}
VERIFIED=(VerifiedRuntime('python','python','3.13.14'),VerifiedRuntime('rust','rust','1.99.0'))

def mock_engine(request):
    if request.url.path.endswith('runtimes'):
        return httpx.Response(200,json=[{'language':'python','version':'3.13.14','aliases':['py']},{'language':'go','version':'1.16.2','aliases':[]},{'language':'rust','version':'1.99.0','aliases':[]}])
    return httpx.Response(200,json={'run':{'stdout':'42\n','stderr':'','code':0,'signal':None}})

@pytest.fixture
def client():
    with TestClient(create_app(Config(TOKEN,verified_runtimes=VERIFIED),transport=httpx.MockTransport(mock_engine))) as c: yield c

def test_requires_auth(client):
    assert client.get('/v1/runtimes').status_code == 401

def test_discovery_only_advertises_verified_requested_languages(client):
    result=client.get('/v1/runtimes',headers=HEADERS).json()
    assert [r['id'] for r in result['runtimes']] == ['python','rust']

def test_executes_only_through_piston(client):
    r=client.post('/v1/execute',headers=HEADERS,json={'language':'python','source':'print(42)'})
    assert r.status_code == 200 and r.json()['stdout'] == '42\n'

def test_unknown_language_rejected(client):
    assert client.post('/v1/execute',headers=HEADERS,json={'language':'bash','source':'echo x'}).status_code == 422

def test_missing_runtime_rejected(client):
    assert client.post('/v1/execute',headers=HEADERS,json={'language':'lean','source':'#eval 2'}).status_code == 422

def test_actual_byte_limit(client):
    assert client.post('/v1/execute',headers=HEADERS,json={'language':'python','source':'é'*40000}).status_code == 413

def test_body_limit(client):
    assert client.post('/v1/execute',headers=HEADERS,content=b'x'*100001).status_code == 413

def test_compile_failure_is_preserved():
    r=normalize({'compile':{'stdout':'','stderr':'syntax error','code':1}},'rust 1.99','rust')
    assert r.exitCode == 1 and r.stderr == 'syntax error'

def test_timeout_is_not_reported_as_success():
    r=normalize({'run':{'stdout':'','stderr':'','code':None,'signal':'SIGKILL'}},'python','python')
    assert r.exitCode == 124

def test_lean_placeholder_is_not_a_completed_proof():
    r=normalize({'run':{'stdout':"warning: declaration uses 'sorry'",'stderr':'','code':0}},'lean','lean')
    assert r.exitCode == 1 and 'placeholder' in r.diagnostics

def test_resource_limits_and_filenames_cannot_be_supplied(client):
    sent=[]
    def engine(req):
        if req.url.path.endswith('execute'):
            import json
            sent.append(json.loads(req.content))
        return mock_engine(req)
    with TestClient(create_app(Config(TOKEN,verified_runtimes=VERIFIED),transport=httpx.MockTransport(engine))) as c:
        c.post('/v1/execute',headers=HEADERS,json={'language':'python','source':'print(42)','run_timeout':999999,'filename':'/tmp/evil'})
    assert sent[0]['run_timeout'] == 3000 and sent[0]['files'][0]['name'] == 'main.py'

def test_rate_limit():
    with TestClient(create_app(Config(TOKEN,requests_per_minute=1,verified_runtimes=VERIFIED),transport=httpx.MockTransport(mock_engine))) as c:
        assert c.get('/v1/runtimes',headers=HEADERS).status_code == 200
        assert c.get('/v1/runtimes',headers=HEADERS).status_code == 429

def test_short_token_fails_closed():
    with pytest.raises(ValueError): Config('short')

def test_selects_newest_compatible_alias():
    assert choose_runtime('cpp',[{'language':'gcc','version':'12.2.0','aliases':['cpp']},{'language':'c++','version':'13.2.0'}])['version'] == '13.2.0'

def test_output_is_bounded():
    result=normalize({'run':{'stdout':'x'*100000,'stderr':'','code':0}},'python','python')
    assert len(result.stdout) < 33000 and 'truncated' in result.stdout


@pytest.mark.parametrize('language',['csharp','go','javascript','java'])
def test_excluded_languages_are_rejected_without_engine_requests(language):
    def engine(request):
        raise AssertionError('Excluded code must never reach the engine')
    with TestClient(create_app(Config(TOKEN,verified_runtimes=VERIFIED),transport=httpx.MockTransport(engine))) as c:
        assert c.post('/v1/execute',headers=HEADERS,json={'language':language,'source':'old code'}).status_code==422


def test_verification_inventory_contains_only_requested_runtimes():
    from runtime_contract import ALIASES
    from runtime_cases import all_cases
    assert set(ALIASES)=={'python','python-ml','cpp','rust','ocaml','lean'}
    cases=all_cases()
    assert {c.language for c in cases}==set(ALIASES)
    assert len([c for c in cases if not c.json_result])==1159
    assert all(c.expected is not None for c in cases if c.json_result)
    guides=[c for c in cases if c.id.startswith('guide.rust.')]
    assert len(guides)==210
    assert all(c.language=='rust' and c.expected is not None for c in guides)
    # Project lessons have no single-file program, so only single-file lessons are hosted cases.
    ocaml_guides=[c for c in cases if c.id.startswith('guide.ocaml.')]
    assert len(ocaml_guides)==206
    assert all(c.language=='ocaml' and c.expected is not None for c in ocaml_guides)

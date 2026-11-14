import asyncio
from collections import Counter
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from gateway import Config, create_app, normalize
from runtime_cases import all_cases, ML_ASSERTIONS, Case, result_passes
from runtime_contract import ML_VERSIONS, LINUX_ML_VERSIONS
from runtime_verification import VerifiedRuntime, load_verification, checks_digest, select_verified
from verify_engine import atomic_json, verify_runtime
from test_gateway import TOKEN, HEADERS, VERIFIED, mock_engine

URL='http://127.0.0.1:2000/api/v2'


def manifest(id='python',language='python',version='3.13.14',packages=None):
    return {'schemaVersion':1,'engineURL':URL,'checksDigest':checks_digest(),
            'runtimes':[{'id':id,'language':language,'version':version,
                         'caseCount':Counter(c.language for c in all_cases())[id],
                         'passed':True,'packages':packages or []}]}


def test_no_verification_disables_installed_runtimes():
    with TestClient(create_app(Config(TOKEN),transport=httpx.MockTransport(mock_engine))) as c:
        assert c.get('/v1/runtimes',headers=HEADERS).json()=={'runtimes':[]}
        assert c.post('/v1/execute',headers=HEADERS,json={'language':'python','source':'print(42)'}).status_code==422


def test_only_the_verified_version_is_selected():
    runtimes=[{'language':'c++','version':'12.2.0'},{'language':'c++','version':'13.2.0'}]
    verified=(VerifiedRuntime('cpp','c++','12.2.0'),)
    assert select_verified('cpp',runtimes,verified)['version']=='12.2.0'
    assert select_verified('cpp',runtimes[1:],verified) is None

def test_older_rust_is_not_advertised_for_current_guide():
    runtimes=[{'language':'rust','version':'1.97.0'}, {'language':'rust','version':'1.99.0'}]
    old=(VerifiedRuntime('rust','rust','1.97.0'),)
    assert select_verified('rust',runtimes,old) is None
    current=(VerifiedRuntime('rust','rust','1.99.0'),)
    assert select_verified('rust',runtimes,current)['version']=='1.99.0'


def test_missing_verified_version_is_hidden_and_rejected():
    def changed(req):
        if req.url.path.endswith('runtimes'):
            return httpx.Response(200,json=[{'language':'python','version':'3.13.15'}])
        raise AssertionError('An unverified execution was delegated')
    with TestClient(create_app(Config(TOKEN,verified_runtimes=VERIFIED),transport=httpx.MockTransport(changed))) as c:
        assert c.get('/v1/runtimes',headers=HEADERS).json()=={'runtimes':[]}
        assert c.post('/v1/execute',headers=HEADERS,json={'language':'python','source':'print(42)'}).status_code==422


def test_verified_ml_packages_match_response_contract():
    packages=tuple(k+'=='+v for k,v in ML_VERSIONS.items())
    record=VerifiedRuntime('python-ml','python-ml','3.13.14',packages)
    def engine(req):
        if req.url.path.endswith('runtimes'):
            return httpx.Response(200,json=[{'language':'python-ml','version':'3.13.14'}])
        return mock_engine(req)
    with TestClient(create_app(Config(TOKEN,verified_runtimes=(record,)),transport=httpx.MockTransport(engine))) as c:
        assert c.get('/v1/runtimes',headers=HEADERS).json()=={'runtimes':[{'id':'python-ml','version':'3.13.14','packages':list(packages)}]}


def test_load_verification(tmp_path):
    path=tmp_path/'record.json'; atomic_json(path,manifest())
    assert load_verification(path,URL)==(VerifiedRuntime('python','python','3.13.14'),)
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize('field,value',[('checksDigest','stale'),('engineURL','http://other/api/v2'),('schemaVersion',2)])
def test_stale_or_wrong_host_verification_rejected(tmp_path,field,value):
    data=manifest(); data[field]=value
    path=tmp_path/'record.json'; atomic_json(path,data)
    with pytest.raises(ValueError): load_verification(path,URL)


@pytest.mark.parametrize('field,value',[('caseCount',0),('passed',False),('packages',['torch==1.0'])])
def test_incomplete_records_rejected(tmp_path,field,value):
    data=manifest(); data['runtimes'][0][field]=value
    path=tmp_path/'record.json'; atomic_json(path,data)
    with pytest.raises(ValueError): load_verification(path,URL)


def test_ml_metadata_must_match_locked_profile(tmp_path):
    packages=[k+'=='+v for k,v in LINUX_ML_VERSIONS.items()]
    path=tmp_path/'record.json'
    data=manifest('python-ml','python-ml','3.13.14',packages)
    atomic_json(path,data)
    assert load_verification(path,URL)[0].packages==tuple(packages)
    data['runtimes'][0]['packages'][0]='numpy==1.0'
    atomic_json(path,data)
    with pytest.raises(ValueError): load_verification(path,URL)


def test_full_ml_examples_have_behavior_checks():
    cases=[c for c in all_cases() if c.language=='python-ml' and c.id!='ml.smoke']
    legacy=[c for c in cases if not c.json_result]
    guide=[c for c in cases if c.json_result]
    assert len(legacy)==24
    assert len({c.id for c in all_cases()})==len(all_cases())
    assert {c.id.rsplit('.',1)[0] for c in legacy} == set(ML_ASSERTIONS)
    assert all('assert' in c.source for c in legacy)
    assert guide and all(c.expected is not None for c in guide)
    curriculum=json.loads((__import__('pathlib').Path(__file__).parent.parent/'CodingTeacher/curriculum.json').read_text())
    expected={lesson['id']+'.'+variant for lesson in curriculum['lessons'] if lesson.get('exercises') for variant in ['code','solution']}
    transfers={e['id']+'.solution':e for lesson in curriculum['lessons'] for e in lesson.get('exercises',[]) if e['id'].endswith('.transfer')}
    expected.update(transfers)
    assert {c.id for c in all_cases() if c.json_result}==expected
    by_id={c.id:c for c in all_cases()}
    for identifier,exercise in transfers.items():
        assert by_id[identifier].source==exercise['solution']
        assert by_id[identifier].expected==exercise['expectedOutput']
        assert by_id[identifier].json_result


def test_guide_json_output_rejects_wrong_shape_boolean_and_nonfinite():
    case=Case('numeric-contract','python-ml','trusted source','[1, 2]',json_result=True)
    def result(output):return normalize({'run':{'stdout':output,'stderr':'','code':0}},'3.13.14','python-ml')
    assert result_passes(case,result('[1.000001, 2.0]'))
    for output in ['[true, 2]','[1]','[1, 3]','[NaN, 2]','[Infinity, 2]','not JSON']:
        assert not result_passes(case,result(output))
    null=Case('null','python','source','null',json_result=True)
    assert result_passes(null,result('null'))
    assert not result_passes(null,result('0'))


def test_guide_python_requires_supported_interpreter():
    from runtime_contract import choose_runtime
    assert choose_runtime('python',[{'language':'python','version':'3.12.9'}]) is None
    assert choose_runtime('python',[{'language':'python','version':'3.13.14'}]) is not None


def test_verifier_rejects_incorrect_output_or_unexpected_success():
    runtime={'language':'lean4','version':'4.35.0'}
    cases=[Case('right-output','lean','#eval 42','42\n'),
           Case('negative','lean','bad',succeeds=False,diagnostic='error')]
    def engine(req):
        return httpx.Response(200,json={'run':{'stdout':'41\n','stderr':'','code':0}})
    with httpx.Client(base_url=URL+'/',transport=httpx.MockTransport(engine)) as c:
        record,rows=verify_runtime(c,'lean',runtime,cases)
    assert record is None and not any(r['passed'] for r in rows)


def test_verifier_records_only_all_passing_cases():
    runtime={'language':'python','version':'3.13.14'}
    with httpx.Client(base_url=URL+'/',transport=httpx.MockTransport(mock_engine)) as c:
        record,rows=verify_runtime(c,'python',runtime,[Case('output','python','print(42)','42\n')])
    assert record['caseCount']==1 and record['passed']
    assert all(r['passed'] for r in rows)


def test_ml_import_versions_must_be_observed():
    runtime={'language':'python-ml','version':'3.13.14'}
    def engine(req):
        return httpx.Response(200,json={'run':{'stdout':json.dumps({'python':'3.13.14','packages':{'torch':'2.8.0'}}),'stderr':'','code':0}})
    with httpx.Client(base_url=URL+'/',transport=httpx.MockTransport(engine)) as c:
        record,rows=verify_runtime(c,'python-ml',runtime,[Case('smoke','python-ml','pass')])
    assert record is None and rows[0]['id']=='ml.versions' and not rows[0]['passed']


@pytest.mark.parametrize('payload',[[],{'run':[]},{'run':{'stdout':None}},{'run':{'code':'0'}},{'run':{'signal':[]}}])
def test_malformed_engine_response_is_a_gateway_error(payload):
    with pytest.raises(HTTPException) as error: normalize(payload,'python','python')
    assert error.value.status_code==502


@pytest.mark.parametrize('aliases',[None,'python',[None],[{}]])
def test_invalid_alias_payload_is_a_service_error(aliases):
    def engine(req):
        return httpx.Response(200,json=[{'language':'python','version':'3.13.14','aliases':aliases}])
    with TestClient(create_app(Config(TOKEN,verified_runtimes=VERIFIED),transport=httpx.MockTransport(engine))) as c:
        assert c.get('/v1/runtimes',headers=HEADERS).status_code==503


def test_cancelled_execution_releases_slot_and_closes_client():
    async def check():
        started=asyncio.Event(); release=asyncio.Event(); active=0; cancelled=0
        async def engine(req):
            nonlocal active,cancelled
            if req.url.path.endswith('runtimes'): return mock_engine(req)
            active+=1
            try:
                started.set()
                await release.wait()
                return mock_engine(req)
            except asyncio.CancelledError:
                cancelled+=1
                raise
            finally: active-=1
        app=create_app(Config(TOKEN,max_parallel=1,verified_runtimes=VERIFIED),transport=httpx.MockTransport(engine))
        async with app.router.lifespan_context(app):
            upstream=app.state.client
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as c:
                body={'language':'python','source':'print(42)'}
                first=asyncio.create_task(c.post('/v1/execute',headers=HEADERS,json=body))
                await asyncio.wait_for(started.wait(),2)
                assert (await c.post('/v1/execute',headers=HEADERS,json=body)).status_code==429
                first.cancel()
                with pytest.raises(asyncio.CancelledError): await first
                assert active==0 and cancelled==1
                release.set()
                assert (await c.post('/v1/execute',headers=HEADERS,json=body)).status_code==200
                assert active==0
        assert upstream.is_closed
    asyncio.run(check())


@pytest.mark.parametrize('signal', ['SIGKILL','SIGTERM'])
@pytest.mark.parametrize('stage', ['compile','run'])
def test_signaled_output_cannot_receive_verification(signal,stage):
    def engine(req):
        payload={'run':{'stdout':'42\n','stderr':'','code':0}}
        payload[stage]={'stdout':'42\n','stderr':'','code':0,'signal':signal}
        return httpx.Response(200,json=payload)
    with httpx.Client(base_url=URL+'/',transport=httpx.MockTransport(engine)) as c:
        record,rows=verify_runtime(c,'python',{'language':'python','version':'3.13.14'},[Case('killed','python','print(42)','42\n')])
    assert record is None and not rows[0]['passed'] and rows[0]['exitCode'] != 0


@pytest.mark.parametrize('torch_version,passes',[('2.8.0',False),('2.8.0+cu128',False),('2.8.0+cpu',True)])
def test_engine_requires_the_exact_linux_cpu_build(torch_version,passes):
    versions={**ML_VERSIONS,'torch':torch_version}
    def engine(req):
        source=json.loads(req.content)['files'][0]['content']
        if 'platform.python_version' in source:
            return httpx.Response(200,json={'run':{'stdout':json.dumps({'python':'3.13.14','packages':versions}),'stderr':'','code':0}})
        return mock_engine(req)
    with httpx.Client(base_url=URL+'/',transport=httpx.MockTransport(engine)) as c:
        record,rows=verify_runtime(c,'python-ml',{'language':'python-ml','version':'3.13.14'},[Case('smoke','python-ml','print(42)','42\n')])
    assert (record is not None)==passes
    if passes: assert 'torch==2.8.0+cpu' in record['packages']

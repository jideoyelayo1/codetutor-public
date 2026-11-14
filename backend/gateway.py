"""Authenticated, bounded gateway. Piston executes code; this process never does."""
from __future__ import annotations
import asyncio
import hmac
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal
from pathlib import Path
from runtime_contract import ALIASES, choose_runtime, execution_payload
from runtime_verification import VerifiedRuntime, engine_url, load_verification, select_verified
import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

Language = Literal['python', 'python-ml', 'cpp', 'rust', 'ocaml', 'lean']
@dataclass(frozen=True)
class Config:
    token: str
    piston_url: str = 'http://127.0.0.1:2000/api/v2'
    requests_per_minute: int = 30
    max_parallel: int = 2
    verified_runtimes: tuple[VerifiedRuntime, ...] = ()
    def __post_init__(self):
        if len(self.token) < 32:
            raise ValueError('RUNNER_TOKEN must contain at least 32 characters')
        engine_url(self.piston_url)
        if self.max_parallel < 1 or self.requests_per_minute < 1:
            raise ValueError('Runner limits must be positive')

class ExecuteRequest(BaseModel):
    language: Language
    source: str = Field(min_length=1, max_length=65536)
    stdin: str = Field(default='', max_length=8192)

class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    exitCode: int
    runtime: str
    diagnostics: str | None = None


def normalize(payload: dict, runtime: str, language: str) -> ExecutionResult:
    if not isinstance(payload, dict):
        raise HTTPException(502, 'The execution engine returned an invalid result.')
    for name in ['compile', 'run']:
        stage = payload.get(name)
        if stage is None: continue
        if (not isinstance(stage,dict)
                or not all(isinstance(stage.get(key,''),str) for key in ['stdout','stderr'])
                or (stage.get('code') is not None and type(stage['code']) is not int)
                or (stage.get('signal') is not None and not isinstance(stage['signal'],str))):
            raise HTTPException(502, 'The execution engine returned an invalid result.')
    compile_stage = payload.get('compile') or {}
    run_stage = payload.get('run') or {}
    failed_compile = compile_stage and (compile_stage.get('code') != 0 or compile_stage.get('signal'))
    stage = compile_stage if failed_compile else run_stage
    if not stage:
        raise HTTPException(502, 'The execution engine returned no result.')
    code = stage.get('code')
    if code is None or (code == 0 and stage.get('signal')):
        code = 124 if stage.get('signal') == 'SIGKILL' else 128
    diagnostics = (compile_stage.get('stderr', '') + compile_stage.get('stdout', '')) if not failed_compile else ''
    if stage.get('signal'): diagnostics += '\nSignal: ' + stage['signal']
    # Batch checking cannot judge proofs, so flag placeholders explicitly.
    combined = (stage.get('stdout','') + stage.get('stderr','') + diagnostics).lower()
    if language == 'lean' and ("uses 'sorry'" in combined or 'sorryax' in combined):
        code = 1
        diagnostics += '\nProof contains a placeholder; this is not a completed proof.'
    def clipped(value: str) -> str:
        raw = value.encode('utf-8')
        return raw[:32768].decode('utf-8', errors='replace') + ('\n[output truncated]' if len(raw) > 32768 else '')
    return ExecutionResult(stdout=clipped(stage.get('stdout','')), stderr=clipped(stage.get('stderr','')), exitCode=code, runtime=runtime, diagnostics=clipped(diagnostics) or None)


def create_app(config: Config, transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(base_url=config.piston_url.rstrip('/')+'/', timeout=30, transport=transport, trust_env=False) as client:
            app.state.client = client
            yield
    app = FastAPI(title='CodingTeacher runner gateway', lifespan=lifespan, docs_url=None, redoc_url=None)
    recent: deque[float] = deque()
    slots = asyncio.Semaphore(config.max_parallel)

    @app.middleware('http')
    async def body_limit(request: Request, call_next):
        # Count real bytes, including streamed bodies, and cache them for parsing.
        if request.method == 'POST':
            chunks=[]; size=0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 100000:
                    from starlette.responses import JSONResponse
                    return JSONResponse({'detail':'Request body exceeds 100 KB.'}, status_code=413)
                chunks.append(chunk)
            request._body = b''.join(chunks)
        return await call_next(request)

    def authorize(authorization: str | None):
        expected='Bearer '+config.token
        if not authorization or not hmac.compare_digest(authorization.encode(), expected.encode()):
            raise HTTPException(401, 'A valid runner access token is required.')
        now=time.monotonic()
        while recent and recent[0] <= now-60: recent.popleft()
        if len(recent) >= config.requests_per_minute:
            raise HTTPException(429, 'Runner rate limit reached. Try again shortly.')
        recent.append(now)

    async def available() -> list[dict]:
        try:
            response=await app.state.client.get('runtimes'); response.raise_for_status()
            data=response.json()
            if not isinstance(data,list) or not all(isinstance(r,dict) and isinstance(r.get('language'),str) and isinstance(r.get('version'),str) and isinstance(r.get('aliases',[]),list) and all(isinstance(a,str) for a in r.get('aliases',[])) for r in data): raise ValueError()
            return data
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(503, 'Execution engine is unavailable.') from exc

    @app.get('/health')
    async def health(): return {'status':'ok'}

    @app.get('/v1/runtimes')
    async def runtimes(authorization: str | None = Header(default=None)):
        authorize(authorization)
        installed=await available(); result=[]
        for language in ALIASES:
            runtime=select_verified(language,installed,config.verified_runtimes)
            if runtime:
                record=next(r for r in config.verified_runtimes if r.id==language)
                result.append({'id':language,'version':runtime['version'],'packages':list(record.packages)})
        return {'runtimes':result}

    @app.post('/v1/execute', response_model=ExecutionResult)
    async def execute(body: ExecuteRequest, authorization: str | None = Header(default=None)):
        authorize(authorization)
        if len(body.source.encode()) > 65536 or len(body.stdin.encode()) > 8192:
            raise HTTPException(413, 'Source or input exceeds its byte limit.')
        if slots.locked(): raise HTTPException(429, 'Runner is busy. Try again shortly.')
        async with slots:
            runtime=select_verified(body.language,await available(),config.verified_runtimes)
            if runtime is None:
                raise HTTPException(422, f'{body.language} has no installed runtime verified against this curriculum.')
            # Users cannot set commands, filesystem paths, compiler flags, or resource limits.
            payload=execution_payload(body.language,body.source,runtime,body.stdin)
            try:
                response=await app.state.client.post('execute',json=payload); response.raise_for_status()
                data=response.json()
            except httpx.TimeoutException as exc: raise HTTPException(504,'Execution engine timed out.') from exc
            except (httpx.HTTPError,ValueError) as exc: raise HTTPException(502,'Execution engine request failed.') from exc
            return normalize(data, f"{runtime['language']} {runtime['version']}", body.language)
    return app


def from_environment() -> FastAPI:
    url=os.environ.get('PISTON_URL','http://127.0.0.1:2000/api/v2')
    path=os.environ.get('RUNTIME_VERIFICATION')
    verified=load_verification(Path(path),url) if path else ()
    return create_app(Config(token=os.environ.get('RUNNER_TOKEN',''), piston_url=url, verified_runtimes=verified))

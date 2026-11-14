# Gateway API

Base URL: your HTTPS endpoint in front of `uvicorn`. Protected routes need `Authorization: Bearer <RUNNER_TOKEN>`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | no | Liveness only: `{"status":"ok"}` |
| GET | `/v1/runtimes` | yes | Runtimes that are installed and verified: `{"runtimes":[{"id","version","packages"}]}` |
| POST | `/v1/execute` | yes | Run one file |

Languages: `python`, `python-ml`, `cpp`, `rust`, `ocaml`, `lean`.

```json
POST /v1/execute
{"language": "rust", "source": "fn main() { println!(\"42\"); }", "stdin": ""}

200
{"stdout": "42\n", "stderr": "", "exitCode": 0, "runtime": "rust 1.99.0", "diagnostics": null}
```

Callers cannot choose executables, paths, compiler flags or limits.

## Limits

- Request body 100 KB, source 64 KiB, stdin 8 KiB; output is truncated at 32 KiB per stream.
- 30 requests a minute and 2 concurrent jobs per process. Run a single worker: the quota is in memory.
- A Lean result that contains `sorry` is reported as a failure.

## Errors

| Status | Meaning |
|---|---|
| 401 | Missing or wrong token |
| 413 | Body, source or stdin too large |
| 422 | No verified runtime for that language |
| 429 | Rate limit reached or runner busy |
| 502 / 503 / 504 | Engine returned an invalid result, is unavailable, or timed out |

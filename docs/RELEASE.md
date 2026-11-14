# Release

## App

1. Regenerate and check the curriculum: `python3 scripts/make_content.py --check`.
2. Run the simulator tests (see the README).
3. Bump `MARKETING_VERSION` in the Xcode project, archive with your signing team and install. App Store distribution has not been set up.

## Execution host

The engine is not deployed yet. To deploy:

1. Use a dedicated Linux x86_64 host with cgroup v2 for [Piston](https://github.com/engineer-man/piston). Keep its API on loopback or a private network and disable networking for jobs.
2. Build the pinned Python ML and Lean 4 packages with a Debian builder image pinned by digest:
   ```sh
   docker buildx build --platform linux/amd64 \
     --build-arg BUILD_IMAGE="<image>@sha256:<digest>" \
     --file backend/runtimes/Dockerfile --target packages \
     --output type=local,dest=.build/runtime-artifacts .
   ```
   Check the archives against `SHA256SUMS` and extract them to `/piston/packages/python-ml/3.13.14/` and `/piston/packages/lean4/4.35.0/`. Install the standard Python, C++ (C++20), Rust (1.99, edition 2024) and OCaml runtimes separately.
3. Set `PISTON_MAX_CONCURRENT_JOBS=2`, `PISTON_OUTPUT_MAX_SIZE=32768` and `run_cpu_time`/`run_timeout` of 8000 ms for `python-ml` and `lean4` through `PISTON_LIMIT_OVERRIDES`.
4. Verify the engine from the same repository revision, then start the gateway with the record:
   ```sh
   python backend/verify_engine.py --engine-url http://127.0.0.1:2000/api/v2 \
     --verification .build/runtime-verification.json --report .build/engine-acceptance.json
   ```
   Rerun verification and restart the gateway whenever packages, the curriculum or the gateway change; stale records stop the gateway from starting.
5. Put the gateway behind HTTPS and test the app against it.

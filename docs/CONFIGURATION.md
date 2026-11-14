# Configuration

No credentials are committed. Supply these values yourself.

## Gateway (`backend/.env`, copied from `backend/.env.example`)

| Variable | Required | Meaning |
|---|---|---|
| `RUNNER_TOKEN` | yes | Random secret, at least 32 characters. The app sends it as `Authorization: Bearer <token>`. |
| `PISTON_URL` | no | Piston API base, default `http://127.0.0.1:2000/api/v2`. Keep it on a private network. |
| `RUNTIME_VERIFICATION` | for execution | Absolute path to the record written by `backend/verify_engine.py`. Without it no runtime is offered. |

Generate a token with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. Keep `.env` and the verification record out of Git (both are ignored).

## App

- **Settings → Runner**: the gateway's HTTPS base URL (no user name, query or fragment) and the same token. The token lives in the Keychain, scoped to that URL.
- **Signing**: simulator builds need nothing. For a device, choose your team under Signing & Capabilities and, if needed, change the bundle identifier `com.jideoyelayo.CodingTeacher`.

## Optional offline Rust manuals

The offline reader uses the official Rust 1.99 documentation, which is not committed:

```sh
RUSTUP_HOME="$PWD/.build/toolchains/rustup" rustup toolchain install 1.99.0 --profile minimal --component rust-docs
python3 scripts/prepare_offline_rust.py
```

This fills the ignored `CodingTeacher/OfflineReferenceResources/`. Six simulator tests (`OfflineReferenceTests`, `SourcePresentationTests`) need it and fail without it.

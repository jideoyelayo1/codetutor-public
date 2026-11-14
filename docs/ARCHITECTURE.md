# Architecture

```
iPhone/iPad app (SwiftUI)  --HTTPS + bearer token-->  gateway (FastAPI)  --HTTP, private network-->  Piston engine
   bundled curriculum.json                               backend/gateway.py                          runs the code
   progress on device                                    limits, auth, verified runtimes
```

## App (`CodingTeacher/`)

- `curriculum.json` holds every track, lesson, recall card, problem and quiz. It is generated; do not edit it by hand.
- `LearningStore.swift` keeps progress, drafts and history in a local JSON file, schedules recall with FSRS 6 and exports or imports backups.
- `LearningViews.swift`, `PracticeViews.swift` and `SourceCourseViews.swift` are the Today, Learn, Recall and practice screens.
- `ExecutionService.swift` and `LabExecutionController.swift` send code to the gateway. The gateway URL and token are entered in Settings; the token is stored in the Keychain and left out of backups.
- `BookLibrary.swift` and `BookViews.swift` are a PDFKit reader for PDFs the user imports. The bundled catalogue is empty.
- `OfflineReferences.swift` reads the official Rust manuals offline when they have been staged (see [CONFIGURATION.md](CONFIGURATION.md)).

The app works offline except for code execution and GitHub repository search (`api.github.com`).

## Gateway (`backend/`)

`gateway.py` never runs learner code. It checks the token, enforces size, rate and concurrency limits, picks a runtime that has a passing verification record and forwards the job to Piston. `runtime_contract.py` maps app languages to engine runtimes and time limits. `verify_engine.py` runs the bundled examples against a real engine and writes the verification record that enables each runtime. `runtimes/` holds pinned build recipes for the Python ML and Lean 4 engine packages.

## Content pipeline (`scripts/`)

`scripts/make_content.py` builds `CodingTeacher/curriculum.json` from the authored modules in `scripts/` (`*_guide.py`, `*_guide_content/`, `source_*`, `learning_pack.json`). Generation is deterministic and needs no network:

```sh
python3 scripts/make_content.py          # write curriculum.json
python3 scripts/make_content.py --check  # fail if the bundled file is stale
```

`scripts/validate_*.py` compile and run each guide's examples with the real toolchains and write receipts. `docs/ocaml-guide-validation.json` and `docs/offline-rust-coverage.json` are receipts that other scripts read; the rest are written under `.build/` or regenerated on demand.

Keep track, lesson, card and problem IDs stable: saved progress refers to them.

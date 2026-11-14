# Open-source components

| Component | Pin | Use | Licence |
|---|---|---|---|
| [Runestone](https://github.com/simonbs/Runestone) | 0.5.2 | Code editor | MIT |
| [TreeSitterLanguages](https://github.com/simonbs/TreeSitterLanguages) | 0.1.10 | Syntax highlighting | MIT, plus grammar notices |
| [Tree-sitter](https://github.com/tree-sitter/tree-sitter) | see `Package.resolved` | Parsing under Runestone | MIT |
| [Swift FSRS](https://github.com/open-spaced-repetition/swift-fsrs) | 4fbaf20 | Recall scheduling | MIT |
| [Piston](https://github.com/engineer-man/piston) | not bundled | Code execution engine | MIT |
| [XcodeProj](https://github.com/tuist/XcodeProj) | 8.27.7 | `scripts/ProjectTools` only | MIT |

`CodingTeacher/ThirdPartyNotices.txt` carries the full notices and is shown in Settings. The swift-fsrs revision is pinned because the latest tag kept the needed APIs internal. Backend Python packages are pinned in `backend/requirements*.txt`; include their notices in any distributed image. The offline Rust manuals, when staged, keep their MIT/Apache notices. Linked exercise sites (Rustlings, Exercism, Learn-OCaml, Lean4Web) are not vendored.

import SwiftUI

struct RunnerExamplesView: View {
    var body: some View {
        Page {
            Text("Ways to run your code").font(.largeTitle.bold())
            Text("The Lab sends code to your configured personal server. Lessons, guides and books work offline. Save a server connection in Settings before running these examples.").foregroundStyle(Palette.muted)
            ForEach(CodeLanguage.executionLanguages) { language in
                Panel {
                    SectionLabel(title: language.title)
                    CodeBlock(code: language.starter)
                    Text("Expected output: \(language == .pythonML ? "2.0" : "42")\(language == .lean ? "; the equality proof must also check." : ".")").font(.caption).foregroundStyle(Palette.muted)
                    NavigationLink("Try in the Lab") { LabView(initialLanguage: language, initialSource: language.starter) }
                }
            }
            SectionLabel(title: "Browser runners")
            Text("These separate services are useful for experiments while the personal server is being prepared. Their versions, packages and project support vary; compare them with the lesson’s requirements.").foregroundStyle(Palette.muted)
            Link("Rust Playground · Rust", destination: URL(string: "https://play.rust-lang.org/")!)
            Link("Compiler Explorer · C++ and compiler inspection", destination: URL(string: "https://godbolt.org/")!)
            Link("OCaml Playground · OCaml", destination: URL(string: "https://ocaml.org/play")!)
            Link("Lean Web · Lean proofs and evaluation", destination: URL(string: "https://live.lean-lang.org/")!)
            SectionLabel(title: "Personal server")
            Text("The gateway uses a private Piston engine for Python, Python ML, C++, Rust, OCaml and Lean. Rust’s new guide needs 1.99 and edition 2024. Cargo and Dune workspaces and Lean/Mathlib projects need project environments; the current Lab accepts one source file per run.").foregroundStyle(Palette.muted)
            Link("Piston project and setup", destination: URL(string: "https://github.com/engineer-man/piston")!)
        }.navigationTitle("Runner examples").navigationBarTitleDisplayMode(.inline)
    }
}

import SwiftUI

struct LabView: View {
    @Environment(LearningStore.self) private var store
    @State private var language: CodeLanguage
    @State private var source = ""
    @State private var stdin = ""
    @State private var execution = LabExecutionController()
    @State private var initialized = false
    @State private var history = false
    @State private var showReset = false
    let initialSource: String?
    let exercise: String?
    init(initialLanguage: CodeLanguage = .python, initialSource: String? = nil, exercise: String? = nil) {
        _language = State(initialValue: initialLanguage.supportsExecution ? initialLanguage : .python)
        self.initialSource = initialLanguage.supportsExecution ? initialSource : nil
        self.exercise = initialLanguage.supportsExecution ? exercise : nil
    }
    var body: some View {
        Page {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 6) {
                    SectionLabel(title: "Your pocket playground")
                    Text("Think it. Run it.").font(.largeTitle.bold())
                }
                Spacer()
                Button { history = true } label: { Image(systemName: "clock.arrow.circlepath").font(.title3) }.accessibilityLabel("Run history")
            }
            if let exercise { Panel { Label("Practice", systemImage: "lightbulb").font(.headline); Text(exercise) } }
            HStack {
                Picker("Language", selection: $language) { ForEach(CodeLanguage.executionLanguages) { Text($0.title).tag($0) } }.tint(Palette.mint).disabled(execution.running)
                Spacer()
                Label("Server", systemImage: "network").font(.caption).foregroundStyle(Palette.muted)
            }
            VStack(spacing: 0) {
                HStack { Text(language.filename).font(.caption.monospaced()); Spacer(); Button { showReset = true } label: { Image(systemName: "arrow.counterclockwise") }.accessibilityLabel("Reset code") }.padding(14).background(Palette.panel)
                CodeEditor(text: $source, language: language).frame(height: 310)
            }.clipShape(RoundedRectangle(cornerRadius: 18))
            TextField("Standard input (optional)", text: $stdin, axis: .vertical).font(.system(.callout,design:.monospaced)).padding(14).background(Palette.panel, in: RoundedRectangle(cornerRadius: 12))
            if store.state.serverURL.isEmpty { Label("Connect your runner in Settings to execute \(language.title).", systemImage: "info.circle").font(.caption).foregroundStyle(Palette.muted) }
            else { Text("Run sends this snippet and input to your configured runner. Drafts stay on this device.").font(.caption).foregroundStyle(Palette.muted) }
            if execution.running { ActionButton(title: "Stop execution", icon: "stop.fill") { execution.cancel() } }
            else { ActionButton(title: language == .lean ? "Check Lean code" : "Run code", icon: "play.fill") { run() }.disabled(source.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty) }
            if let runError = execution.error { Label(runError, systemImage: "exclamationmark.triangle").font(.subheadline).foregroundStyle(.orange) }
            if let result = execution.result {
                Panel {
                    HStack { Label(result.succeeded ? "Finished" : "Needs attention", systemImage: result.succeeded ? "checkmark.circle" : "xmark.circle").foregroundStyle(result.succeeded ? Palette.mint : .orange); Spacer(); Text("exit \(result.exitCode)").font(.caption.monospaced()) }
                    Text(result.runtime).font(.caption).foregroundStyle(Palette.muted)
                    CodeBlock(code: result.output.isEmpty ? "(No output)" : result.output)
                }
            }
            if language == .lean {
                Panel {
                    Label("See the proof state", systemImage: "checkmark.seal").font(.headline)
                    Text("For live goals, tactic feedback, and Mathlib, use the existing Lean web editor. It runs Lean on its own server.").font(.subheadline).foregroundStyle(Palette.muted)
                    Link("Open Lean live editor ↗", destination: URL(string:"https://live.lean-lang.org/")!)
                    ShareLink(item: source) { Label("Share or copy this snippet",systemImage:"square.and.arrow.up") }
                }
            }
        }.navigationTitle("Code lab").navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .topBarTrailing) { NavigationLink("Examples") { RunnerExamplesView() } } }
        .onAppear { if !initialized { source = initialSource ?? store.state.drafts[language.rawValue] ?? language.starter; initialized = true } }
        .onChange(of: language) { old, new in store.draft(source, language: old); source = store.state.drafts[new.rawValue] ?? new.starter; execution.clear() }
        .onChange(of: source) { _, new in if initialized { store.draft(new, language: language) } }
        .onDisappear { execution.cancel(showMessage: false); store.save() }
        .confirmationDialog("Replace this draft with the starter example?", isPresented: $showReset, titleVisibility: .visible) { Button("Reset draft", role: .destructive) { source = language.starter }; Button("Cancel", role: .cancel) {} }
        .sheet(isPresented: $history) {
            NavigationStack {
                List {
                    if store.state.attempts.isEmpty { ContentUnavailableView("No runs yet", systemImage: "terminal", description: Text("Run a snippet to save its source and output here.")) }
                    ForEach(store.state.attempts) { attempt in
                        NavigationLink {
                            Page { Text(attempt.language.title).font(.title.bold()); Text(attempt.date.formatted()).font(.caption); CodeBlock(code: attempt.source); SectionLabel(title: "Output"); CodeBlock(code: attempt.output); if attempt.language.supportsExecution { ActionButton(title: "Restore this draft", icon: "arrow.uturn.backward") { language = attempt.language; source = attempt.source; history = false } } else { ShareLink(item: attempt.source) { Label("Share or copy this snippet", systemImage: "square.and.arrow.up") } } }
                        } label: { VStack(alignment: .leading, spacing: 5) { Label(attempt.language.title, systemImage: attempt.succeeded ? "checkmark.circle" : "xmark.circle"); Text(attempt.date.formatted()).font(.caption).foregroundStyle(.secondary) } }
                    }
                }.navigationTitle("Run history").toolbar { ToolbarItem(placement: .topBarTrailing) { Button("Done") { history = false } } }
            }
        }
    }
    private func run() {
        let capturedLanguage = language, capturedSource = source
        let learningStore = store
        execution.start(language: language, source: source, stdin: stdin, base: store.state.serverURL) { output in
            learningStore.recordAttempt(language: capturedLanguage, source: capturedSource, result: output)
        }
    }
}

import SwiftUI
import UniformTypeIdentifiers

struct SettingsView: View {
    @Environment(LearningStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var server = ""
    @State private var token = ""
    @State private var connected: [RunnerCapability] = []
    @State private var status: String?
    @State private var connectionStatus: String?
    @State private var checking = false
    @State private var backup: URL?
    @State private var importFile = false
    @State private var about = false
    @State private var connectionRequest: ConnectionRequest?
    private struct ConnectionRequest: Equatable { let id = UUID(); let base: String }
    var body: some View {
        @Bindable var store = store
        Form {
            Section("Your daily rhythm") {
                Stepper("\(store.state.dailyMinutes) minutes a day",value:$store.state.dailyMinutes,in:5...60,step:5)
                Stepper("\(store.state.dailyReviewGoal) review goal",value:$store.state.dailyReviewGoal,in:4...40,step:2)
                Stepper("Up to \(store.state.dailyNewLimit) new cards",value:$store.state.dailyNewLimit,in:1...20)
            }
            Section {
                ForEach(store.curriculum.tracks) { track in
                    Toggle(track.name,isOn:Binding(get:{ store.state.enabledTracks.contains(track.id) },set:{ enabled in if enabled { store.state.enabledTracks.insert(track.id) } else { store.state.enabledTracks.remove(track.id) }; store.save() }))
                }
            } header: { Text("Subjects in your recall queue") } footer: { Text("New-language cards enter recall after you complete their lesson. Existing-language cards are available from the start.") }
            Section {
                TextField("https://your-runner.example",text:$server).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                SecureField("Runner access token",text:$token).textInputAutocapitalization(.never).autocorrectionDisabled()
                Button(checking ? "Checking…" : "Save & check connection") { connect() }.disabled(checking)
                if let status = connectionStatus { Text(status).font(.caption) }
                ForEach(connected) { runtime in VStack(alignment:.leading,spacing:4) { Text("\(runtime.id) · \(runtime.version)").font(.caption.monospaced()); if !runtime.packages.isEmpty { Text(runtime.packages.joined(separator:", ")).font(.caption2).foregroundStyle(.secondary) } } }
            } header: { Text("Code runner") } footer: { Text("Python, Python ML, C++, Rust, OCaml, and Lean 4 use your HTTPS runner. Tokens are stored in the iOS Keychain and are excluded from backups. A connection check sends the token to this URL.") }
            Section("Your data") {
                Button("Prepare progress backup") { do { backup=try store.exportURL() } catch { status=error.localizedDescription } }
                if let backup { ShareLink("Export backup",item:backup) }
                Button("Import progress backup") { importFile=true }
                Text("Reviews, completed lessons, code drafts, and the most recent 100 runs stay on this device. Import keeps a copy of your previous progress.").font(.caption).foregroundStyle(.secondary)
                if let status { Text(status).font(.caption) }
            }
            Section("About") {
                Text("\(store.curriculum.tracks.count) tracks · \(store.curriculum.lessons.count) lessons · \(store.curriculum.cards.count) recall cards").font(.caption)
                Text("FSRS 6 scheduling · Runestone editor").font(.caption)
                Button("Open-source acknowledgements") { about=true }
            }
        }.navigationTitle("Make it yours").toolbar { ToolbarItem(placement:.topBarTrailing) { Button("Done") { store.save(); dismiss() } } }
        .onAppear { server=store.state.serverURL; token=RunnerCredential.read(base:server) ?? "" }
        .task(id: connectionRequest) {
            guard let request = connectionRequest else { return }
            defer { if connectionRequest?.id == request.id { checking = false } }
            do {
                let runtimes = try await RemoteExecutionService().capabilities(base: request.base)
                try Task.checkCancellation()
                guard connectionRequest?.id == request.id else { return }
                connected = runtimes; connectionStatus = "Connected · \(runtimes.count) available runtimes."
            } catch is CancellationError { }
            catch {
                guard !Task.isCancelled, connectionRequest?.id == request.id else { return }
                connectionStatus = error.localizedDescription
            }
        }
        .onDisappear { connectionRequest = nil; checking = false }
        .onChange(of:server) { _, new in connectionRequest = nil; checking = false; connected = []; connectionStatus = nil; token=RunnerCredential.read(base:new) ?? "" }
        .onChange(of:store.state.dailyMinutes) { _,_ in store.save() }
        .onChange(of:store.state.dailyReviewGoal) { _,_ in store.save() }
        .onChange(of:store.state.dailyNewLimit) { _,_ in store.save() }
        .fileImporter(isPresented:$importFile,allowedContentTypes:[.json]) { outcome in
            do { try store.importBackup(from:outcome.get()); server=store.state.serverURL; status="Progress imported." }
            catch { status="Import failed: \(error.localizedDescription)" }
        }
        .sheet(isPresented:$about) { NavigationStack { Page { Text("Built with open source").font(.largeTitle.bold()); Text("Third-party code is licensed by its respective authors. The full license notices are bundled below."); Text(notices).font(.caption).textSelection(.enabled) }.toolbar { ToolbarItem(placement:.topBarTrailing) { Button("Done") { about=false } } } } }
    }
    private var notices: String {
        guard let url=Bundle.main.url(forResource:"ThirdPartyNotices",withExtension:"txt"), let text=try? String(contentsOf:url,encoding:.utf8) else { return "See docs/OPEN_SOURCE.md for license details." }; return text
    }
    private func connect() {
        checking = true; connectionStatus = nil; connected = []
        do {
            let base = server.trimmingCharacters(in: .whitespacesAndNewlines)
            _ = try RemoteExecutionService.endpoint(base: base, path: "v1/runtimes")
            // This button authorizes saving the provided connection and checking it.
            try RunnerCredential.save(token, base: base)
            store.state.serverURL = base; store.save()
            connectionRequest = ConnectionRequest(base: base)
        } catch { checking = false; connectionStatus = error.localizedDescription }
    }
}

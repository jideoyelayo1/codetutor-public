import SwiftUI

@main struct CodingTeacherApp: App {
    @Environment(\.scenePhase) private var scenePhase
    @State private var store: LearningStore?
    @State private var loadingError: String?
    @State private var bookLibrary = BookLibrary()
    private let offlineReferences = OfflineReferenceLibrary.load()
    init() {
        do { _store = State(initialValue: LearningStore(curriculum: try Curriculum.load())) }
        catch { _loadingError = State(initialValue: error.localizedDescription) }
    }
    var body: some Scene {
        WindowGroup {
            if let store { RootView().environment(store).environment(bookLibrary).environment(\.offlineReferences, offlineReferences).preferredColorScheme(.dark).onChange(of: scenePhase) { _, phase in if phase != .active { store.save() } } }
            else { ContentUnavailableView("Curriculum unavailable", systemImage: "exclamationmark.triangle", description: Text(loadingError ?? "The content bundle could not be loaded.")) }
        }
    }
}
struct RootView: View {
    @Environment(LearningStore.self) private var store
    @State private var settings = false
    @State private var selection = 0
    var body: some View {
        TabView(selection: $selection) {
            NavigationStack { TodayView(selection: $selection).toolbar { settingsButton } }.tabItem { Label("Today", systemImage: "sun.max") }.tag(0)
            NavigationStack { LearnView().toolbar { settingsButton } }.tabItem { Label("Learn", systemImage: "map") }.tag(1)
            NavigationStack { RecallView().toolbar { settingsButton } }.tabItem { Label("Recall", systemImage: "rectangle.on.rectangle") }.tag(2)
            NavigationStack { LabView().toolbar { settingsButton } }.tabItem { Label("Lab", systemImage: "terminal") }.tag(3)
            NavigationStack { LibraryView().toolbar { settingsButton } }.tabItem { Label("Library", systemImage: "books.vertical") }.tag(4)
        }
        .tint(Palette.mint)
        .sheet(isPresented: $settings) { NavigationStack { SettingsView() } }
        .alert("Progress needs attention", isPresented: Binding(get: { store.errorMessage != nil }, set: { if !$0 { store.errorMessage = nil } })) { Button("OK") { store.errorMessage = nil } } message: { Text(store.errorMessage ?? "") }
    }
    private var settingsButton: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) { Button { settings = true } label: { Image(systemName: "slider.horizontal.3") }.accessibilityLabel("Settings") }
    }
}
enum Palette {
    static let background = Color(hex: "0C1419")
    static let panel = Color(hex: "152127")
    static let mint = Color(hex: "A6D9C3")
    static let muted = Color(hex: "94A7AD")
}
struct Page<Content: View>: View {
    @ViewBuilder var content: () -> Content
    var body: some View { ScrollView { VStack(alignment: .leading, spacing: 24, content: content).padding(20).frame(maxWidth: 780, alignment: .leading).frame(maxWidth: .infinity) }.background(Palette.background) }
}
struct SectionLabel: View {
    let title: String
    var body: some View { Text(title.uppercased()).font(.caption.weight(.semibold)).tracking(2).foregroundStyle(Palette.muted) }
}
struct Panel<Content: View>: View {
    @ViewBuilder var content: () -> Content
    var body: some View { VStack(alignment: .leading, spacing: 16, content: content).padding(20).frame(maxWidth: .infinity, alignment: .leading).background(Palette.panel, in: RoundedRectangle(cornerRadius: 22)) }
}
struct TrackBadge: View {
    let track: LearningTrack
    var body: some View {
        // Bundled track-<id> artwork wins; a track without it keeps its SF Symbol. The track name sits beside the badge.
        Group {
            if let icon = UIImage(named: "track-\(track.id)") {
                Image(uiImage: icon).resizable().scaledToFit().frame(width: 44, height: 44).clipShape(RoundedRectangle(cornerRadius: 13))
            } else {
                Image(systemName: track.symbol).font(.title3).foregroundStyle(track.tint).frame(width: 44, height: 44).background(track.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 13))
            }
        }.accessibilityHidden(true)
    }
}
struct CodeBlock: View {
    let code: String
    var body: some View { ScrollView(.horizontal) { Text(code).font(.system(.callout, design: .monospaced)).textSelection(.enabled).padding(16) }.frame(maxWidth: .infinity, alignment: .leading).background(Color(hex: "111B21"), in: RoundedRectangle(cornerRadius: 14)) }
}
struct ActionButton: View {
    let title: String
    let icon: String
    var action: () -> Void
    var body: some View { Button(action: action) { Label(title, systemImage: icon).font(.headline).frame(maxWidth: .infinity).padding(.vertical, 10) }.buttonStyle(.borderedProminent).tint(Palette.mint).foregroundStyle(Palette.background) }
}

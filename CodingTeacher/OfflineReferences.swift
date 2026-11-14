import Foundation
import SwiftUI
import Observation
@preconcurrency import WebKit

struct ReferenceHeading: Codable, Hashable { let anchor, title: String }
struct ReferencePage: Codable, Hashable, Identifiable {
    let id, bookID, title, filename, sourceURL, relativePath: String
    let headings: [ReferenceHeading]
    let wordCount: Int
}
struct ReferenceBook: Codable, Hashable, Identifiable {
    let id, title, authors, version, license, licenseFilename: String
    let pages: [ReferencePage]
}
struct ReferenceCatalog: Codable { let schemaVersion: Int; let version: String; let books: [ReferenceBook] }

// One immutable metadata index per app session. HTML is loaded one page at a time.
struct OfflineReferenceLibrary {
    let books: [ReferenceBook]
    let resourceRoot: URL?
    private let paths: [String: ReferencePage]
    private let filenames: [String: ReferencePage]
    var pageNames: Set<String> { Set(filenames.keys) }
    static let empty = OfflineReferenceLibrary(books: [], resourceRoot: nil)
    init(books: [ReferenceBook], resourceRoot: URL?) {
        self.books = books; self.resourceRoot = resourceRoot
        let pages = books.flatMap(\.pages)
        filenames = Dictionary(pages.map { ($0.filename, $0) }, uniquingKeysWith: { first, _ in first })
        var index = Dictionary(pages.map { ("/" + $0.relativePath, $0) }, uniquingKeysWith: { first, _ in first })
        for book in books {
            if let first = book.pages.first, let directory = first.relativePath.split(separator: "/").first {
                index["/\(directory)/index.html"] = index["/\(directory)/index.html"] ?? first
            }
        }
        paths = index
    }
    static func load(bundle: Bundle = .main) -> Self {
        guard let url = bundle.url(forResource: "offline-reference-catalog", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let catalog = try? JSONDecoder().decode(ReferenceCatalog.self, from: data), catalog.schemaVersion == 1 else { return .empty }
        return Self(books: catalog.books, resourceRoot: bundle.resourceURL)
    }
    func page(filename: String) -> ReferencePage? { filenames[filename] }
    func practice(for page: ReferencePage, lessons: [Lesson]) -> [Lesson] {
        lessons.filter { lesson in
            ([lesson.sourceURL] + (lesson.reading ?? []).compactMap(\.url)).contains {
                self.page(source: $0)?.id == page.id
            }
        }.sorted { lhs, rhs in
            if lhs.trackID != rhs.trackID { return lhs.trackID < rhs.trackID }
            if lhs.order != rhs.order { return lhs.order < rhs.order }
            return lhs.id < rhs.id
        }
    }
    func page(source: String) -> ReferencePage? {
        guard let url = URL(string: source), ["http", "https"].contains(url.scheme), url.host == "doc.rust-lang.org" else { return nil }
        var components = url.path.split(separator: "/").map(String.init)
        if let first = components.first, ["stable", "latest", "1.99.0"].contains(first) { components.removeFirst() }
        if components.count == 1 || url.hasDirectoryPath { components.append("index.html") }
        return paths["/" + components.joined(separator: "/")]
    }
    func resourceURL(filename: String) -> URL? {
        guard !filename.isEmpty, filename.utf8.allSatisfy({ (97...122).contains($0) || (48...57).contains($0) || [45,46].contains($0) }),
              !filename.contains(".."), let resourceRoot else { return nil }
        for directory in [resourceRoot, resourceRoot.appendingPathComponent("OfflineReferenceResources")] {
            let url = directory.appendingPathComponent(filename)
            if FileManager.default.fileExists(atPath: url.path) { return url }
        }
        return nil
    }
}
private struct OfflineReferencesKey: EnvironmentKey { static let defaultValue = OfflineReferenceLibrary.empty }
extension EnvironmentValues {
    var offlineReferences: OfflineReferenceLibrary {
        get { self[OfflineReferencesKey.self] }
        set { self[OfflineReferencesKey.self] = newValue }
    }
}

@MainActor @Observable final class ReferenceNavigation {
    var filename: String
    var canGoBack = false
    var canGoForward = false
    @ObservationIgnored weak var webView: WKWebView?
    init(filename: String) { self.filename = filename }
    func back() { webView?.goBack() }
    func forward() { webView?.goForward() }
}

struct ReferenceHTMLView: UIViewRepresentable {
    let url: URL
    let allowedNames: Set<String>
    let navigation: ReferenceNavigation
    func makeCoordinator() -> Coordinator { Coordinator(root: url.deletingLastPathComponent(), names: allowedNames, navigation: navigation) }
    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = false
        configuration.websiteDataStore = .nonPersistent()
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.navigationDelegate = context.coordinator
        navigation.webView = view
        view.isOpaque = false
        return view
    }
    func updateUIView(_ view: WKWebView, context: Context) {
        context.coordinator.navigation = navigation
        navigation.webView = view
        let target = Self.baseURL(url)
        if context.coordinator.loadedURL != target {
            context.coordinator.loadedURL = target
            view.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
    }
    static func baseURL(_ url: URL) -> URL {
        var components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        components?.fragment = nil; components?.query = nil
        return components?.url ?? url
    }
    static func dismantleUIView(_ view: WKWebView, coordinator: Coordinator) {
        view.stopLoading(); view.navigationDelegate = nil; view.uiDelegate = nil
        if coordinator.navigation?.webView === view { coordinator.navigation?.webView = nil }
        coordinator.navigation = nil; coordinator.loadedURL = nil
        view.loadHTMLString("", baseURL: nil)
    }
    @MainActor final class Coordinator: NSObject, WKNavigationDelegate {
        let root: URL
        let names: Set<String>
        weak var navigation: ReferenceNavigation?
        var loadedURL: URL?
        init(root: URL, names: Set<String>, navigation: ReferenceNavigation) {
            self.root = root.standardizedFileURL.resolvingSymlinksInPath(); self.names = names; self.navigation = navigation
        }
        func allows(_ url: URL) -> Bool {
            url.isFileURL && Self.resourceBase(url).deletingLastPathComponent().path == root.path && names.contains(url.lastPathComponent)
        }
        private static func resourceBase(_ url: URL) -> URL { ReferenceHTMLView.baseURL(url).standardizedFileURL.resolvingSymlinksInPath() }
        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let navigation, navigation.webView === webView, let target = action.request.url else { decisionHandler(.cancel); return }
            if allows(target) {
                loadedURL = ReferenceHTMLView.baseURL(target)
                navigation.filename = target.lastPathComponent
                decisionHandler(.allow)
            } else {
                decisionHandler(.cancel)
                if action.navigationType == .linkActivated, ["https", "http", "mailto"].contains(target.scheme) { UIApplication.shared.open(target) }
            }
        }
        func webView(_ webView: WKWebView, didFinish navigationEvent: WKNavigation!) {
            guard let navigation, navigation.webView === webView else { return }
            navigation.canGoBack = webView.canGoBack; navigation.canGoForward = webView.canGoForward
        }
    }
}

struct ReferenceLibraryView: View {
    @Environment(\.offlineReferences) private var library
    @State private var query = ""
    var body: some View {
        Page {
            Text("Detailed references, offline.").font(.largeTitle.bold())
            Text("Read the complete packaged chapters, examples, diagrams and reference sections alongside your practice. Source reading and tested exercise completion are different parts of learning.").foregroundStyle(Palette.muted)
            if library.books.isEmpty { ContentUnavailableView("References unavailable", systemImage: "books.vertical", description: Text("The reference library is not included in this build.")) }
            ForEach(library.books) { book in
                let matches = book.pages.filter { query.isEmpty || ([$0.title] + $0.headings.map(\.title)).joined(separator: " ").localizedCaseInsensitiveContains(query) }
                if !matches.isEmpty {
                    SectionLabel(title: book.title)
                    Text("\(book.version) · \(book.pages.count) pages · \(book.authors)").font(.caption).foregroundStyle(Palette.muted)
                    LazyVStack(spacing: 10) {
                        ForEach(matches) { page in
                            NavigationLink { ReferenceReaderView(page: page) } label: {
                                HStack { Text(page.title).multilineTextAlignment(.leading); Spacer(); Image(systemName: "chevron.right").font(.caption) }.padding(14).background(Palette.panel, in: RoundedRectangle(cornerRadius: 12))
                            }.buttonStyle(.plain)
                        }
                    }
                }
            }
        }.navigationTitle("Offline references").navigationBarTitleDisplayMode(.inline).searchable(text: $query, prompt: "Find a chapter or detailed section")
    }
}

struct ReferenceReaderView: View {
    @Environment(\.offlineReferences) private var library
    let page: ReferencePage
    let initialAnchor: String?
    @State private var navigation: ReferenceNavigation
    @State private var showingLicense = false
    init(page: ReferencePage, anchor: String? = nil) {
        self.page = page; initialAnchor = anchor
        _navigation = State(initialValue: ReferenceNavigation(filename: page.filename))
    }
    private var current: ReferencePage { library.page(filename: navigation.filename) ?? page }
    private var url: URL? {
        guard let file = library.resourceURL(filename: current.filename) else { return nil }
        guard current.filename == page.filename, let initialAnchor else { return file }
        var components = URLComponents(url: file, resolvingAgainstBaseURL: false); components?.fragment = initialAnchor
        return components?.url
    }
    var body: some View {
        Group {
            if let url { ReferenceHTMLView(url: url, allowedNames: library.pageNames, navigation: navigation) }
            else { ContentUnavailableView("Page unavailable", systemImage: "doc.text") }
        }.navigationTitle(current.title).navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                NavigationLink("Practice") { ReferencePracticeView(page: current) }
            }
        }
        .safeAreaInset(edge: .bottom) {
            HStack {
                Button { navigation.back() } label: { Image(systemName: "chevron.left") }.disabled(!navigation.canGoBack).accessibilityLabel("Previous reference page")
                Button { navigation.forward() } label: { Image(systemName: "chevron.right") }.disabled(!navigation.canGoForward).accessibilityLabel("Next reference page")
                Spacer()
                if let source = URL(string: current.sourceURL) { Link("Source", destination: source) }
                Button("License") { showingLicense = true }
            }.buttonStyle(.bordered).padding(.horizontal).padding(.vertical, 8).background(.bar)
        }
        .sheet(isPresented: $showingLicense) {
            NavigationStack { Page {
                if let book = library.books.first(where: { $0.id == current.bookID }), let url = library.resourceURL(filename: book.licenseFilename) {
                    Text(book.title).font(.title.bold()); Text(book.authors); Text((try? String(contentsOf: url, encoding: .utf8)) ?? "License unavailable").textSelection(.enabled)
                }
            }.navigationTitle("Source attribution").toolbar { Button("Done") { showingLicense = false } } }
        }
    }
}

struct ReferencePracticeView: View {
    @Environment(LearningStore.self) private var store
    @Environment(\.offlineReferences) private var library
    let page: ReferencePage
    private var lessons: [Lesson] { library.practice(for: page, lessons: store.curriculum.lessons) }
    var body: some View {
        Page {
            Text(page.title).font(.title.bold())
            Text("Lessons that use this page. Reading and practice progress are separate.")
                .foregroundStyle(.secondary)
            if lessons.isEmpty {
                ContentUnavailableView("Practice is still being written", systemImage: "pencil.and.outline",
                    description: Text("You can read the full page now. Guided exercises for this page are not available yet."))
            }
            ForEach(lessons) { lesson in
                if let track = store.track(lesson.trackID) {
                    NavigationLink { LessonView(lesson: lesson, track: track) } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(lesson.title).font(.headline)
                                Text("\(track.name) · \(lesson.minutes) min").font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right").font(.caption)
                        }.multilineTextAlignment(.leading).padding(14)
                            .background(Palette.panel, in: RoundedRectangle(cornerRadius: 12))
                    }.buttonStyle(.plain)
                }
            }
        }.navigationTitle("Practice").navigationBarTitleDisplayMode(.inline)
    }
}

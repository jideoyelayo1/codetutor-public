import SwiftUI

struct GitHubRepository: Decodable, Identifiable {
    let id: Int
    let fullName: String
    let htmlURL: URL
    let description: String?
    let stars: Int
    let language: String?
    let license: License?
    let updatedAt: String
    struct License: Decodable { let spdxID: String?; enum CodingKeys: String, CodingKey { case spdxID = "spdx_id" } }
    enum CodingKeys: String, CodingKey { case id, description, language, license; case fullName = "full_name", htmlURL = "html_url", stars = "stargazers_count", updatedAt = "updated_at" }
}
struct GitHubSearchResponse: Decodable { let items: [GitHubRepository] }
struct GitHubSearchService {
    func search(query: String) async throws -> [GitHubRepository] {
        var components = URLComponents(string:"https://api.github.com/search/repositories")!
        components.queryItems = [URLQueryItem(name:"q",value:query), URLQueryItem(name:"sort",value:"stars"),URLQueryItem(name:"per_page",value:"20")]
        var request = URLRequest(url:components.url!); request.timeoutInterval = 15
        request.setValue("application/vnd.github+json", forHTTPHeaderField:"Accept")
        request.setValue("CodingTeacher-iOS", forHTTPHeaderField:"User-Agent")
        let (data,response) = try await URLSession.shared.data(for:request)
        guard let http = response as? HTTPURLResponse else { throw ExecutionError.unavailable("GitHub did not respond.") }
        guard http.statusCode == 200 else { throw ExecutionError.unavailable(http.statusCode == 403 || http.statusCode == 429 ? "GitHub’s public API rate limit was reached. Open the web search or try again later." : "GitHub search failed (\(http.statusCode)).") }
        return try JSONDecoder().decode(GitHubSearchResponse.self, from:data).items
    }
}
struct LibraryView: View {
    @Environment(LearningStore.self) private var store
    @State private var mode = 0
    @State private var query = "rust exercises"
    @State private var repositories: [GitHubRepository] = []
    @State private var loading = false
    @State private var searched = false
    @State private var searchError: String?
    @State private var searchRequest: SearchRequest?
    private struct SearchRequest: Equatable { let id = UUID(); let query: String }
    init(initialMode: Int = 0) { _mode = State(initialValue:initialMode) }
    var body: some View {
        Page {
            Text("Good foundations,\nready to use.").font(.largeTitle.bold())
            Picker("Library", selection: $mode) { Text("Resources").tag(0); Text("Books").tag(1); Text("GitHub").tag(2) }.pickerStyle(.segmented)
            if mode == 0 {
                NavigationLink("Read the detailed references offline") { ReferenceLibraryView() }
                Text("Official references and established practice projects, curated for your stack.").foregroundStyle(Palette.muted)
                ForEach(store.curriculum.tracks) { track in
                    SectionLabel(title:track.name)
                    ForEach(track.resources) { resource in
                        Link(destination:URL(string:resource.url)!) { HStack { VStack(alignment:.leading,spacing:5) { Text(resource.title).font(.headline); Text(resource.kind).font(.caption).foregroundStyle(Palette.muted) }; Spacer(); Image(systemName:"arrow.up.right") }.padding(16).background(Palette.panel,in:RoundedRectangle(cornerRadius:14)) }.foregroundStyle(.primary)
                    }
                }
            } else if mode == 1 {
                BookShelfView()
            } else {
                Text("Search public projects for exercises, reference implementations, and reusable tools.").foregroundStyle(Palette.muted)
                TextField("Search GitHub repositories",text:$query).textInputAutocapitalization(.never).autocorrectionDisabled().submitLabel(.search).padding(14).background(Palette.panel,in:RoundedRectangle(cornerRadius:12)).onSubmit { search() }
                ScrollView(.horizontal) { HStack { ForEach(["rust exercises", "ocaml examples", "lean theorem proving", "ios code editor"],id:\.self) { preset in Button(preset) { query=preset; search() }.buttonStyle(.bordered).font(.caption) } } }
                ActionButton(title:loading ? "Searching…" : "Search GitHub",icon:"magnifyingglass") { search() }.disabled(loading || query.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)
                if let searchError { Text(searchError).foregroundStyle(.orange).font(.subheadline) }
                if loading { ProgressView().frame(maxWidth:.infinity) }
                if searched && repositories.isEmpty && !loading && searchError == nil { ContentUnavailableView.search(text:query) }
                ForEach(repositories) { repo in
                    Link(destination:repo.htmlURL) {
                        Panel {
                            HStack { Text(repo.fullName).font(.headline); Spacer(); Image(systemName:"arrow.up.right") }
                            if let description=repo.description { Text(description).font(.subheadline).foregroundStyle(Palette.muted).lineLimit(4) }
                            HStack { Label("\(repo.stars)",systemImage:"star"); Text(repo.language ?? "Mixed"); Spacer(); Text(repo.license?.spdxID ?? "License not listed") }.font(.caption).foregroundStyle(Palette.muted)
                        }
                    }.foregroundStyle(.primary)
                }
                Link("Open this search on GitHub ↗", destination: webSearchURL).font(.subheadline)
                Text("Results come from GitHub’s public API. Check licenses, maintenance, and compatibility before reusing code. Searching never downloads or runs a repository.").font(.caption).foregroundStyle(Palette.muted)
            }
        }.navigationTitle("Library").navigationBarTitleDisplayMode(.inline)
        .task(id: searchRequest) {
            guard let request = searchRequest else { return }
            defer { if searchRequest?.id == request.id { loading = false; searched = true } }
            do {
                let results = try await GitHubSearchService().search(query: request.query)
                try Task.checkCancellation()
                guard searchRequest?.id == request.id else { return }
                repositories = results
            } catch is CancellationError { }
            catch {
                guard !Task.isCancelled, searchRequest?.id == request.id else { return }
                repositories = []; searchError = error.localizedDescription
            }
        }
        .onChange(of: mode) { _, new in if new != 2 { searchRequest = nil; loading = false } }
        .onDisappear { searchRequest = nil; loading = false }
    }
    private var webSearchURL: URL { var c=URLComponents(string:"https://github.com/search")!; c.queryItems=[URLQueryItem(name:"q",value:query),URLQueryItem(name:"type",value:"repositories")]; return c.url! }
    private func search() {
        guard !loading else { return }
        let captured = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !captured.isEmpty else { return }
        loading = true; searchError = nil
        searchRequest = SearchRequest(query: captured)
    }
}

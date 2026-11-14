import XCTest
import WebKit
@testable import CodingTeacher

@MainActor final class OfflineReferenceTests: XCTestCase {
    func testPracticeMatchesPrimaryAndCompanionPagesWithoutDuplicates() throws {
        let library = OfflineReferenceLibrary.load()
        let curriculum = try Curriculum.load()
        let environment = try XCTUnwrap(library.page(source: "https://doc.rust-lang.org/stable/book/ch12-05-working-with-environment-variables.html#working-with-environment-variables"))
        let matches = library.practice(for: environment, lessons: curriculum.lessons)
        XCTAssertTrue(matches.contains { $0.id == "guide.rust.environment-cli-project" })
        XCTAssertEqual(matches.count, Set(matches.map(\.id)).count)
        XCTAssertEqual(library.practice(for: environment, lessons: Array(curriculum.lessons.reversed())).map(\.id), matches.map(\.id))
        let companion = try XCTUnwrap(library.page(source: "https://doc.rust-lang.org/book/ch21-02-multithreaded.html"))
        XCTAssertTrue(library.practice(for: companion, lessons: curriculum.lessons).contains { $0.id == "guide.rust.http-server-project" })
        XCTAssertTrue(library.practice(for: environment, lessons: []).isEmpty)
    }
    func testCompletePackAndSourceResolution() throws {
        let library = OfflineReferenceLibrary.load()
        XCTAssertEqual(library.books.count, 6)
        let pages = library.books.flatMap(\.pages)
        XCTAssertEqual(pages.count, 643)
        XCTAssertEqual(Set(pages.map(\.id)).count, pages.count)
        XCTAssertEqual(Set(pages.map(\.filename)).count, pages.count)
        XCTAssertEqual(pages.flatMap(\.headings).count, 3845)
        for book in library.books { XCTAssertNotNil(library.resourceURL(filename: book.licenseFilename)) }
        for page in pages {
            let url = try XCTUnwrap(library.resourceURL(filename: page.filename))
            let html = try String(contentsOf: url, encoding: .utf8)
            XCTAssertTrue(html.contains("<!doctype html>"))
            XCTAssertFalse(html.contains("<script"), page.id)
            XCTAssertFalse(html.contains("<iframe"), page.id)
            XCTAssertFalse(html.contains("javascript:"), page.id)
        }
        let live = try XCTUnwrap(library.page(source: "https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html#ownership-rules"))
        XCTAssertEqual(library.page(source: "https://doc.rust-lang.org/1.99.0/book/ch04-01-what-is-ownership.html")?.id, live.id)
        XCTAssertNotNil(library.page(source: "https://doc.rust-lang.org/rust-by-example/"))
        XCTAssertNil(library.page(source: "https://doc.rust-lang.org/1.80.0/book/ch04-01-what-is-ownership.html"))
        XCTAssertNil(library.page(source: "https://example.com/book/ch04-01-what-is-ownership.html"))
        XCTAssertNil(library.resourceURL(filename: "../curriculum.json"))
        XCTAssertNil(library.resourceURL(filename: "/etc/passwd"))
    }
    func testNavigationAllowsOnlyPackagedPageFiles() throws {
        let root = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let owner = ReferenceNavigation(filename: "ref-test.html")
        let coordinator = ReferenceHTMLView.Coordinator(root: root, names: ["ref-test.html"], navigation: owner)
        XCTAssertTrue(coordinator.allows(root.appendingPathComponent("ref-test.html")))
        XCTAssertFalse(coordinator.allows(root.appendingPathComponent("unknown.html")))
        XCTAssertFalse(coordinator.allows(root.appendingPathComponent("../ref-test.html")))
        XCTAssertFalse(coordinator.allows(URL(string: "javascript:alert(1)")!))
        XCTAssertFalse(coordinator.allows(URL(string: "https://example.com/")!))
    }
    func testCoordinatorDoesNotRetainOwnerAndIgnoresOldView() {
        var owner: ReferenceNavigation? = ReferenceNavigation(filename: "new.html")
        let weakOwner = ReferenceWeakBox(owner)
        let coordinator = ReferenceHTMLView.Coordinator(root: URL.temporaryDirectory, names: ["new.html"], navigation: owner!)
        let old = WKWebView(); let current = WKWebView()
        owner?.webView = current; owner?.canGoBack = true
        coordinator.webView(old, didFinish: nil)
        XCTAssertEqual(owner?.canGoBack, true)
        owner = nil
        XCTAssertNil(weakOwner.value)
        XCTAssertNil(coordinator.navigation)
    }
    func testReaderTeardownReleasesWebViewCoordinatorAndOwner() async throws {
        let library = OfflineReferenceLibrary.load()
        let page = try XCTUnwrap(library.books.first?.pages.first)
        let url = try XCTUnwrap(library.resourceURL(filename: page.filename))
        var owner: ReferenceNavigation? = ReferenceNavigation(filename: page.filename)
        var coordinator: ReferenceHTMLView.Coordinator? = .init(root: url.deletingLastPathComponent(), names: library.pageNames, navigation: owner!)
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = false
        configuration.websiteDataStore = .nonPersistent()
        var view: WKWebView? = WKWebView(frame: .zero, configuration: configuration)
        let weakView = ReferenceWeakBox(view)
        let weakCoordinator = ReferenceWeakBox(coordinator)
        let weakOwner = ReferenceWeakBox(owner)
        view?.navigationDelegate = coordinator
        owner?.webView = view
        view?.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        XCTAssertFalse(view!.configuration.defaultWebpagePreferences.allowsContentJavaScript)
        ReferenceHTMLView.dismantleUIView(view!, coordinator: coordinator!)
        XCTAssertNil(view?.navigationDelegate)
        XCTAssertNil(owner?.webView)
        view = nil; coordinator = nil; owner = nil
        for _ in 0..<100 where weakView.value != nil { try await Task.sleep(for: .milliseconds(20)) }
        XCTAssertNil(weakView.value)
        XCTAssertNil(weakCoordinator.value)
        XCTAssertNil(weakOwner.value)
    }
}

private final class ReferenceWeakBox<Value: AnyObject> {
    weak var value: Value?
    init(_ value: Value?) { self.value = value }
}

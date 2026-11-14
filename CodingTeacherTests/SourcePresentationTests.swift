import XCTest
import SwiftUI
import UIKit
import WebKit
@testable import CodingTeacher

@MainActor final class SourcePresentationTests: XCTestCase {
    private enum PresentationGroup: Equatable { case source, projects, references }

    func testSourceScreensRenderAndReleaseTheirHosts() async throws {
        try await renderAndRelease(group: .source)
    }
    func testProjectScreensRenderAndReleaseTheirHosts() async throws {
        try await renderAndRelease(group: .projects)
    }
    func testReferenceScreensRenderAndReleaseTheirHosts() async throws {
        try await renderAndRelease(group: .references)
    }

    private func renderAndRelease(group: PresentationGroup) async throws {
        let curriculum = try Curriculum.load()
        let store = LearningStore(curriculum: curriculum, fileURL: URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
        let library = BookLibrary(root: URL.temporaryDirectory.appendingPathComponent(UUID().uuidString))
        let course = try XCTUnwrap(curriculum.courses.first { $0.id == "hayden" })
        let lesson = try XCTUnwrap(curriculum.lessons.first { $0.id == "source.cpp-sequences" })
        let track = try XCTUnwrap(store.track(lesson.trackID))
        let methodLesson = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.python.descriptor-access" })
        let guide = try XCTUnwrap(curriculum.courses.first { $0.id == "guide.rust" })
        let guideLesson = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.first-program" })
        let projectLesson = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.procedural-macros" })
        let cliProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.minigrep-project" })
        let httpProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.http-server-project" })
        let environmentProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.environment-cli-project" })
        let stdioProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.stdio-cli-project" })
        let iteratorProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.iterator-cli-project" })
        let streamingProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.streaming-file-project" })
        let stagedProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.staged-file-project" })
        let htmlProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.html-server-project" })
        let ffiProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.ffi-buffer-project" })
        let nostdProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.nostd-ring-project" })
        let ownedProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.owned-server-project" })
        let rust = try XCTUnwrap(store.track("rust"))
        let ocaml = try XCTUnwrap(store.track("ocaml"))
        let ocamlGuide = try XCTUnwrap(curriculum.courses.first { $0.id == "guide.ocaml" })
        let ocamlLesson = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.ocaml.first-program" })
        let duneProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.ocaml.ppx-shout" })
        let leanGuide = try XCTUnwrap(curriculum.courses.first { $0.id == "guide.lean" })
        let leanTrack = try XCTUnwrap(store.track("lean"))
        let leanLesson = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.lean.s01-eval-and-check" })
        let leanMathlib = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.lean.s10-automation" })
        let leanProject = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.lean.s14-custom-tactic-project" })
        let references = OfflineReferenceLibrary.load()
        let referencePage = try XCTUnwrap(references.books.first?.pages.first)
        let practicePage = try XCTUnwrap(references.page(source: "https://doc.rust-lang.org/book/ch12-05-working-with-environment-variables.html"))
        let emptyPracticePage = try XCTUnwrap(references.books.flatMap(\.pages).first { references.practice(for: $0, lessons: curriculum.lessons).isEmpty })
        let diagramPage = try XCTUnwrap(references.page(source: "https://doc.rust-lang.org/reference/tokens.html"))
        let cases: [(String, AnyView)] = [
            ("source-courses", AnyView(NavigationStack { Page { SourceCourseList() } })),
            ("source-chapters", AnyView(NavigationStack { SourceCourseDetailView(course: course) })),
            ("source-assignment", AnyView(NavigationStack { SourceChapterView(chapter: course.chapters[1], course: course) })),
            ("source-study", AnyView(NavigationStack { LessonView(lesson: lesson, track: track) })),
            ("source-python-methods", AnyView(NavigationStack { LessonView(lesson: methodLesson, track: store.track("python")!) })),
            ("language-guides", AnyView(NavigationStack { Page { SourceCourseList(guideKind: SourceCourse.languageGuide) } })),
            ("rust-guide", AnyView(NavigationStack { SourceCourseDetailView(course: guide) })),
            ("rust-stage", AnyView(NavigationStack { SourceChapterView(chapter: guide.chapters[0], course: guide) })),
            ("rust-guide-lesson", AnyView(NavigationStack { LessonView(lesson: guideLesson, track: rust) })),
            ("rust-cargo-project", AnyView(NavigationStack { LessonView(lesson: projectLesson, track: rust) })),
            ("rust-cli-project", AnyView(NavigationStack { LessonView(lesson: cliProject, track: rust) })),
            ("rust-http-project", AnyView(NavigationStack { LessonView(lesson: httpProject, track: rust) })),
            ("rust-environment-project", AnyView(NavigationStack { LessonView(lesson: environmentProject, track: rust) })),
            ("rust-stdio-project", AnyView(NavigationStack { LessonView(lesson: stdioProject, track: rust) })),
            ("rust-iterator-project", AnyView(NavigationStack { LessonView(lesson: iteratorProject, track: rust) })),
            ("rust-streaming-project", AnyView(NavigationStack { LessonView(lesson: streamingProject, track: rust) })),
            ("rust-staged-project", AnyView(NavigationStack { LessonView(lesson: stagedProject, track: rust) })),
            ("rust-html-project", AnyView(NavigationStack { LessonView(lesson: htmlProject, track: rust) })),
            ("rust-ffi-buffer-project", AnyView(NavigationStack { LessonView(lesson: ffiProject, track: rust) })),
            ("rust-nostd-ring-project", AnyView(NavigationStack { LessonView(lesson: nostdProject, track: rust) })),
            ("rust-owned-server-project", AnyView(NavigationStack { LessonView(lesson: ownedProject, track: rust) })),
            ("ocaml-guide", AnyView(NavigationStack { SourceCourseDetailView(course: ocamlGuide) })),
            ("ocaml-guide-lesson", AnyView(NavigationStack { LessonView(lesson: ocamlLesson, track: ocaml) })),
            ("ocaml-dune-project", AnyView(NavigationStack { LessonView(lesson: duneProject, track: ocaml) })),
            ("lean-guide", AnyView(NavigationStack { SourceCourseDetailView(course: leanGuide) })),
            ("lean-stage", AnyView(NavigationStack { SourceChapterView(chapter: leanGuide.chapters[0], course: leanGuide) })),
            ("lean-guide-lesson", AnyView(NavigationStack { LessonView(lesson: leanLesson, track: leanTrack) })),
            ("lean-mathlib-lesson", AnyView(NavigationStack { LessonView(lesson: leanMathlib, track: leanTrack) })),
            ("lean-lake-project", AnyView(NavigationStack { LessonView(lesson: leanProject, track: leanTrack) })),
            ("runner-examples", AnyView(NavigationStack { RunnerExamplesView() })),
            ("offline-reference-library", AnyView(NavigationStack { ReferenceLibraryView() })),
            ("offline-reference-practice", AnyView(NavigationStack { ReferencePracticeView(page: practicePage) })),
            ("offline-reference-no-practice", AnyView(NavigationStack { ReferencePracticeView(page: emptyPracticePage) })),
            ("offline-reference-reader", AnyView(NavigationStack { ReferenceReaderView(page: referencePage) })),
            ("offline-reference-diagram", AnyView(NavigationStack { ReferenceReaderView(page: diagramPage, anchor: "railroad-Token") }))
        ]
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        // Split the cases into groups to bound screenshot work per test.
        let selected = cases.filter { name, _ in
            let category: PresentationGroup = name.hasPrefix("offline-reference") ? .references : name.hasSuffix("-project") ? .projects : .source
            return category == group
        }
        let expected: Int
        switch group { case .source: expected = 16; case .projects: expected = 14; case .references: expected = 5 }
        XCTAssertEqual(cases.count, 40)
        XCTAssertEqual(Set(cases.map(\.0)).count, cases.count)
        XCTAssertEqual(selected.count, expected)
        for (name, screen) in selected {
            print("Presentation begin:", name)
            var host: UIHostingController<AnyView>? = UIHostingController(rootView: AnyView(screen.environment(store).environment(library).environment(\.offlineReferences, references).preferredColorScheme(.dark)))
            let reference = PresentationWeakReference(host)
            let window = UIWindow(windowScene: scene)
            window.frame = CGRect(x: 0, y: 0, width: 393, height: 852)
            window.rootViewController = host
            window.isHidden = false
            host?.view.frame = window.bounds
            window.layoutIfNeeded()
            try await Task.sleep(for: .milliseconds(200))
            if name == "offline-reference-reader" || name == "offline-reference-diagram" {
                let webView = try XCTUnwrap(findWebView(in: host!.view))
                for _ in 0..<100 where webView.isLoading || webView.url == nil {
                    try await Task.sleep(for: .milliseconds(50))
                }
                XCTAssertFalse(webView.isLoading, "Reference did not finish loading: \(name)")
                XCTAssertNotNil(webView.url)
                if name == "offline-reference-diagram" {
                    // Test-only DOM inspection; document scripts stay disabled.
                    let geometry = try await webView.evaluateJavaScript("JSON.stringify(Array.from(document.querySelectorAll('svg')).slice(0,1).map(s => ({rect:s.getBoundingClientRect().toJSON(), paths:s.querySelectorAll('path').length, display:getComputedStyle(s).display, visibility:getComputedStyle(s).visibility, canvas:getComputedStyle(s.querySelector('rect')).fill})))")
                    let diagnostic = XCTAttachment(string: String(describing: geometry))
                    diagnostic.name = "offline-diagram-geometry"; diagnostic.lifetime = .keepAlways
                    add(diagnostic)
                    let json = try XCTUnwrap(geometry as? String)
                    let diagrams = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(json.utf8)) as? [[String: Any]])
                    let first = try XCTUnwrap(diagrams.first)
                    XCTAssertGreaterThan(try XCTUnwrap(first["paths"] as? Int), 0)
                    XCTAssertEqual(first["visibility"] as? String, "visible")
                    let bounds = try XCTUnwrap(first["rect"] as? [String: Any])
                    XCTAssertGreaterThan(try XCTUnwrap(bounds["width"] as? Double), 100)
                    XCTAssertGreaterThan(try XCTUnwrap(bounds["height"] as? Double), 100)
                }
                try await Task.sleep(for: .milliseconds(300))
                let content = try await webView.takeSnapshot(configuration: nil)
                let pageAttachment = XCTAttachment(data: try XCTUnwrap(content.pngData()), uniformTypeIdentifier: "public.png")
                pageAttachment.name = name + "-web-content"; pageAttachment.lifetime = .keepAlways
                add(pageAttachment)
                if name == "offline-reference-reader" {
                    let originalURL = try XCTUnwrap(webView.url)
                    let selected = try await webView.evaluateJavaScript("(() => { const a=Array.from(document.querySelectorAll('a[href]')).find(a => a.getAttribute('href').startsWith('ref-') && new URL(a.href).pathname !== location.pathname); if (!a) return null; const target=a.href; a.click(); return target; })()")
                    let target = try XCTUnwrap(selected as? String)
                    for _ in 0..<100 where webView.url?.absoluteString != target || webView.isLoading {
                        try await Task.sleep(for: .milliseconds(50))
                    }
                    XCTAssertEqual(webView.url?.absoluteString, target)
                    XCTAssertTrue(webView.url?.isFileURL == true)
                    XCTAssertTrue(webView.canGoBack)
                    webView.goBack()
                    for _ in 0..<100 where webView.url != originalURL || webView.isLoading {
                        try await Task.sleep(for: .milliseconds(50))
                    }
                    XCTAssertEqual(webView.url, originalURL)
                }
            }
            let attachment = try makePNGTestAttachment(named: name) {
                UIGraphicsImageRenderer(size: window.bounds.size).image { _ in
                    window.drawHierarchy(in: window.bounds, afterScreenUpdates: true)
                }
            }
            add(attachment)
            window.isHidden = true
            window.rootViewController = nil
            host = nil
            try await Task.sleep(for: .milliseconds(200))
            XCTAssertNil(reference.value, "Presentation host retained after teardown: \(name)")
            print("Presentation end:", name)
        }
    }
    private func findWebView(in view: UIView) -> WKWebView? {
        if let webView = view as? WKWebView { return webView }
        for child in view.subviews { if let found = findWebView(in: child) { return found } }
        return nil
    }
}
private final class PresentationWeakReference<T: AnyObject> {
    weak var value: T?
    init(_ value: T?) { self.value = value }
}

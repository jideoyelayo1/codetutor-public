import XCTest
@testable import CodingTeacher

@MainActor final class SourceCourseTests: XCTestCase {
    private func makeStore(fileURL: URL? = nil) throws -> LearningStore {
        LearningStore(curriculum: try Curriculum.load(), fileURL: fileURL ?? URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
    }
    func testAllSuppliedSourcesHaveReachableChapterPractice() throws {
        let content = try Curriculum.load()
        let supplied = content.courses.filter { !$0.isGuide }
        XCTAssertEqual(supplied.count, 8)
        XCTAssertEqual(supplied.flatMap(\.chapters).count, 188)
        XCTAssertEqual(Set(content.courses.map(\.id)).count, content.courses.count)
        let chapters = content.courses.flatMap(\.chapters)
        XCTAssertEqual(Set(chapters.map(\.id)).count, chapters.count)
        let courseIDs = Set(content.courses.map(\.id))
        XCTAssertTrue(Set(["rust-book", "rust-example", "rust-video", "learninglad", "hayden", "lean-fpil", "lean-tpil", "lean-mil"]).isSubset(of: courseIDs))
        var reachable = Set<String>()
        for chapter in chapters {
            XCTAssertFalse(chapter.lessonIDs.isEmpty)
            for id in chapter.lessonIDs {
                XCTAssertNotNil(content.lessons.first { $0.id == id })
                reachable.insert(id)
            }
            if let bookID = chapter.reading.bookID {
                let book = try XCTUnwrap(content.bookCatalog.first { $0.id == bookID })
                let page = try XCTUnwrap(chapter.reading.pdfPage)
                XCTAssertTrue((1...book.pdfPages).contains(page))
            } else {
                XCTAssertEqual(URL(string: try XCTUnwrap(chapter.reading.url))?.scheme, "https")
            }
        }
        XCTAssertTrue(Set(content.lessons.filter { $0.isSourceStudy == true }.map(\.id)).isSubset(of: reachable))
        let videos = content.courses.first { $0.id == "rust-video" }!
        XCTAssertEqual(videos.chapters.first { $0.title == "Borrowing" }?.reading.url, "https://www.youtube.com/watch?v=BpPEoZW5IiY&t=8646s")
        XCTAssertEqual(content.courses.first { $0.id == "learninglad" }?.chapters.count, 58)
        XCTAssertEqual(content.courses.first { $0.id == "hayden" }?.chapters.count, 14)
    }
    func testSourceCardsForKnownLanguagesRequireCompletion() throws {
        let store = try makeStore()
        let lesson = try XCTUnwrap(store.curriculum.lessons.first { $0.id == "source.cpp-templates" })
        let cards = store.curriculum.cards.filter { $0.lessonID == lesson.id }
        XCTAssertEqual(cards.count, 2)
        XCTAssertTrue(cards.allSatisfy { !store.isEligible($0) })
        store.complete(lesson)
        XCTAssertTrue(cards.allSatisfy { store.isEligible($0) })
        store.state.enabledTracks.remove("cpp")
        XCTAssertTrue(cards.allSatisfy { !store.isEligible($0) })
    }
    func testReadingAndSharedPracticeRemainIndependent() throws {
        let store = try makeStore()
        let chapter = store.curriculum.courses.first { $0.id == "hayden" }!.chapters[0]
        store.markSourceRead(chapter.id, read: true)
        XCTAssertTrue(store.state.readSourceChapters?.contains(chapter.id) == true)
        XCTAssertFalse(store.state.completedLessons.contains(chapter.lessonIDs[0]))
        store.markSourceRead(chapter.id, read: false)
        let lesson = try XCTUnwrap(store.curriculum.lessons.first { $0.id == chapter.lessonIDs[0] })
        store.complete(lesson)
        XCTAssertFalse(store.state.readSourceChapters?.contains(chapter.id) == true)
        XCTAssertEqual(store.curriculum.cards.filter { $0.lessonID == lesson.id }.count, 2)
        // Shared chapter mappings do not duplicate cards or change daily-path progress.
        XCTAssertEqual(store.lessons(for: "cpp").count, 3)
    }
    func testNotesAndReadingRoundTripThroughProgressAndBackup() throws {
        let url = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json")
        let store = try makeStore(fileURL: url)
        store.studyNote("An acquire observes a published release.", id: "source.cpp-templates")
        store.markSourceRead("hayden.section-005", read: true)
        let restored = try makeStore(fileURL: url)
        XCTAssertEqual(restored.state.studyNotes?["source.cpp-templates"], "An acquire observes a published release.")
        XCTAssertTrue(restored.state.readSourceChapters?.contains("hayden.section-005") == true)
        let target = try makeStore()
        try target.importBackup(from: store.exportURL())
        XCTAssertEqual(target.state.studyNotes, store.state.studyNotes)
        XCTAssertEqual(target.state.readSourceChapters, store.state.readSourceChapters)
    }
    func testLongNotesRemainCompleteAfterSaveReloadAndBackup() throws {
        let url = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json")
        let store = try makeStore(fileURL: url)
        let note = String(repeating: "🧠 e\u{301} __getattr__\n", count: 2_000) + "END_OF_LESSON"
        let chapterNote = note + "\nEND_OF_CHAPTER"
        XCTAssertGreaterThan(note.count, 20_000)
        store.studyNote(note, id: "source.rs-smart")
        store.studyNote(chapterNote, id: "hayden.section-012")
        store.save()
        let restored = try makeStore(fileURL: url)
        XCTAssertEqual(restored.state.studyNotes?["source.rs-smart"], note)
        XCTAssertEqual(restored.state.studyNotes?["hayden.section-012"], chapterNote)
        let target = try makeStore()
        try target.importBackup(from: store.exportURL())
        XCTAssertEqual(target.state.studyNotes?["source.rs-smart"], note)
        XCTAssertEqual(target.state.studyNotes?["hayden.section-012"], chapterNote)
    }
    func testSourceSpecialMethodNamesRenderVerbatim() throws {
        let content = try Curriculum.load()
        let names: [String: [String]] = [
            "guide.python.sequence-protocol": ["__getitem__"],
            "guide.python.context-exit": ["__enter__"],
            "guide.python.descriptor-access": ["__get__"],
            "guide.python.metaclass-creation": ["__init_subclass__"]
        ]
        for (id, identifiers) in names {
            let lesson = try XCTUnwrap(content.lessons.first { $0.id == id })
            let original = lesson.body.joined(separator: "\n")
            let rendered = lesson.body.map { String(lesson.paragraphText($0).characters) }.joined(separator: "\n")
            XCTAssertEqual(rendered, original, id)
            for identifier in identifiers { XCTAssertTrue(rendered.contains(identifier), "Missing \(identifier) in \(id)") }
        }
    }
    func testDailyLessonInlineCodeFormattingRemainsAvailable() throws {
        let lesson = try XCTUnwrap(Curriculum.load().lessons.first { $0.id == "python.aliasing" })
        let text = lesson.paragraphText(lesson.body[1])
        XCTAssertTrue(text.runs.contains { $0.inlinePresentationIntent?.contains(.code) == true })
        XCTAssertTrue(String(text.characters).contains("Use is for sentinels"))
        XCTAssertFalse(String(text.characters).contains("`is`"))
    }
    func testPreviousStateAndCurriculumDecodeWithoutSourceFields() throws {
        let store = try makeStore()
        var state = try JSONSerialization.jsonObject(with: JSONEncoder().encode(store.state)) as! [String: Any]
        state.removeValue(forKey: "studyNotes"); state.removeValue(forKey: "readSourceChapters")
        let restored = try JSONDecoder().decode(LearningState.self, from: JSONSerialization.data(withJSONObject: state))
        XCTAssertNil(restored.studyNotes); XCTAssertNil(restored.readSourceChapters)
        var curriculum = try JSONSerialization.jsonObject(with: JSONEncoder().encode(store.curriculum)) as! [String: Any]
        curriculum.removeValue(forKey: "sourceCourses")
        let old = try JSONDecoder().decode(Curriculum.self, from: JSONSerialization.data(withJSONObject: curriculum))
        XCTAssertTrue(old.courses.isEmpty)
    }
    func testPendingStudyNoteSaveDoesNotRetainStore() async throws {
        var store: LearningStore? = try makeStore()
        let reference = StudyWeakReference(store)
        store?.studyNote("A pending note", id: "chapter")
        store = nil
        XCTAssertNil(reference.value)
        try await Task.sleep(for: .milliseconds(450))
        XCTAssertNil(reference.value)
    }
}

private final class StudyWeakReference<T: AnyObject> {
    weak var value: T?
    init(_ value: T?) { self.value = value }
}

import XCTest
@testable import CodingTeacher

@MainActor final class LearningTests: XCTestCase {
    private func makeStore() throws -> LearningStore {
        let directory = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        return LearningStore(curriculum: try Curriculum.load(), fileURL: directory.appendingPathComponent("progress.json"))
    }
    func testTracksUseBundledIcons() throws {
        for track in try Curriculum.load().tracks {
            let icon = try XCTUnwrap(UIImage(named: "track-\(track.id)"), track.id)
            XCTAssertEqual(icon.size.width, icon.size.height, track.id)
        }
    }
    func testContentHasValidRelationshipsAndUniqueIDs() throws {
        let content = try Curriculum.load()
        XCTAssertEqual(content.lessons.count,1311)
        XCTAssertEqual(content.cards.count,3131)
        XCTAssertTrue(content.lessons.allSatisfy { lesson in content.cards.filter { $0.lessonID == lesson.id }.count >= 2 })
        XCTAssertEqual(content.tracks.count,13)
        XCTAssertEqual(Set(content.cards.map(\.id)).count,content.cards.count)
        XCTAssertEqual(Set(content.lessons.map(\.id)).count,content.lessons.count)
        for lesson in content.lessons {
            XCTAssertTrue(content.tracks.contains { $0.id == lesson.trackID })
            XCTAssertTrue(lesson.options.indices.contains(lesson.answerIndex))
            if lesson.isSourceStudy == true {
                XCTAssertFalse(try XCTUnwrap(lesson.workedExample).isEmpty)
                XCTAssertFalse(try XCTUnwrap(lesson.practiceAnswer).isEmpty)
            } else { XCTAssertFalse(lesson.code.isEmpty) }
            XCTAssertNotNil(URL(string:lesson.sourceURL))
        }
        for card in content.cards { XCTAssertTrue(content.lessons.contains { $0.id == card.lessonID && $0.trackID == card.trackID }) }
        for track in content.tracks {
            let lessons = content.lessons.filter { $0.trackID == track.id }.sorted { $0.order < $1.order }
            XCTAssertEqual(lessons.map(\.order),Array(1...lessons.count))
            // Bash is taught only through its guide, so it has no daily-path lessons.
            XCTAssertEqual(lessons.filter { $0.isSourceStudy != true }.count,track.id == "bash" ? 0 : track.isNew ? 9 : 3)
        }
    }
    func testBashIsAGuideOnlyTrack() throws {
        let store = try makeStore()
        let track = try XCTUnwrap(store.track("bash"))
        XCTAssertEqual(track.language, .bash)
        XCTAssertFalse(track.language.supportsExecution)
        let lessons = store.lessons(for: "bash")
        XCTAssertEqual(lessons.count, 64)
        XCTAssertTrue(lessons.allSatisfy { $0.id.hasPrefix("guide.bash.") })
        let guide = try XCTUnwrap(store.curriculum.courses.first { $0.id == "guide.bash" })
        XCTAssertEqual(guide.chapters.count, 12)
        XCTAssertEqual(guide.chapters.flatMap(\.lessonIDs), lessons.map(\.id))
        XCTAssertEqual(lessons.filter { $0.projectFiles != nil }.count, 5)
        store.complete(lessons[0])
        XCTAssertEqual(store.completion(for: "bash"), 1.0/64, accuracy: 0.0001)
    }
    func testLearnPathsExcludeConceptTracks() throws {
        let store = try makeStore()
        let learn = store.tracks(mode: "learn") + store.tracks(mode: "retain")
        XCTAssertEqual(learn.count, 13)
        XCTAssertFalse(learn.contains { $0.isConcept })
    }
    func testTrackWithoutLanguageOrSubjectDecodes() throws {
        let json = #"{"id":"numpy","name":"NumPy","mode":"retain","subtitle":"Arrays","symbol":"square","color":"5BB9DD","resources":[]}"#
        let track = try JSONDecoder().decode(LearningTrack.self, from: Data(json.utf8))
        XCTAssertNil(track.subject)
        XCTAssertEqual(track.language, .pythonML)
        let explicit = try JSONDecoder().decode(LearningTrack.self, from: Data(json.replacingOccurrences(of: #""resources":[]"#, with: #""resources":[],"language":"cpp","subject":"Systems""#).utf8))
        XCTAssertEqual(explicit.language, .cpp)
        XCTAssertEqual(explicit.subject, "Systems")
        XCTAssertEqual(try JSONDecoder().decode(LearningTrack.self, from: JSONEncoder().encode(explicit)), explicit)
    }
    func testNewTracksAreEnabledOnceWithoutOverridingChoices() throws {
        let file = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json")
        try FileManager.default.createDirectory(at: file.deletingLastPathComponent(), withIntermediateDirectories: true)
        var legacy = LearningState()
        legacy.enabledTracks = LearningState.originalTracks.subtracting(["rust"])
        XCTAssertNil(legacy.knownTracks)
        try JSONEncoder().encode(legacy).write(to: file)
        let first = LearningStore(curriculum: try Curriculum.load(), fileURL: file)
        XCTAssertTrue(first.state.enabledTracks.contains("bash"))
        XCTAssertFalse(first.state.enabledTracks.contains("rust"))
        first.state.enabledTracks.remove("bash")
        first.save()
        let second = LearningStore(curriculum: try Curriculum.load(), fileURL: file)
        XCTAssertFalse(second.state.enabledTracks.contains("bash"))
        XCTAssertFalse(second.state.enabledTracks.contains("rust"))
    }
    func testNewLanguageCardsRequireLessonCompletion() throws {
        let store = try makeStore()
        let card = store.curriculum.cards.first { $0.trackID == "rust" }!
        XCTAssertFalse(store.isEligible(card))
        store.complete(store.curriculum.lessons.first { $0.id == card.lessonID }!)
        XCTAssertTrue(store.isEligible(card))
        let lastLesson = store.lessons(for:"rust").last!
        let lastCards = store.curriculum.cards.filter { $0.lessonID == lastLesson.id }
        XCTAssertFalse(lastCards.isEmpty)
        XCTAssertTrue(lastCards.allSatisfy { !store.isEligible($0) })
        store.complete(lastLesson)
        XCTAssertTrue(lastCards.allSatisfy { store.isEligible($0) })
        XCTAssertEqual(store.completion(for:"rust"),2.0/Double(store.lessons(for:"rust").count),accuracy:0.0001)
    }
    func testReviewMixesSubjectsAndRespectsDailyNewLimit() throws {
        let store=try makeStore(); let now=Date(timeIntervalSince1970:1_800_000_000)
        store.state.dailyNewLimit=3
        let initial=store.reviewQueue(now:now)
        XCTAssertEqual(initial.count,3)
        XCTAssertEqual(Set(initial.map(\.trackID)).count,3)
        for card in initial { XCTAssertTrue(store.review(card,grade:.good,now:now)) }
        XCTAssertTrue(store.reviewQueue(now:now).isEmpty)
        XCTAssertGreaterThan(store.reviewQueue(now:now.addingTimeInterval(86400)).count,0)
    }
    func testDisablingSubjectExcludesItsCards() throws {
        let store=try makeStore(); store.state.enabledTracks=["go"]
        XCTAssertTrue(store.reviewQueue().allSatisfy { $0.trackID == "go" })
    }
    func testNewLessonCardsGetIncludedInNextMixedSession() throws {
        let store=try makeStore()
        store.complete(store.curriculum.lessons.first { $0.trackID == "lean" }!)
        XCTAssertTrue(store.reviewQueue().contains { $0.trackID == "lean" })
    }
    func testReviewPersistsAndUndoRestoresQueue() throws {
        let content=try Curriculum.load()
        let url=URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("state.json")
        let store=LearningStore(curriculum:content,fileURL:url)
        let now=Date(timeIntervalSince1970:1_800_000_000)
        let card=store.reviewQueue(now:now).first!
        XCTAssertTrue(store.review(card,grade:.good,now:now))
        let restored=LearningStore(curriculum:content,fileURL:url)
        XCTAssertEqual(restored.state.reviews.count,1)
        XCTAssertGreaterThan(restored.state.schedules[card.id]!.due,now)
        store.undoReview()
        XCTAssertEqual(store.state.reviews.count,0)
        XCTAssertNil(store.state.schedules[card.id])
    }
    func testBackupRejectsInvalidSettingsBeforeReplacingProgress() throws {
        let store=try makeStore(); store.state.completedLessons=["rust.ownership"]
        var invalid=LearningState(); invalid.dailyNewLimit=1000
        let url=URL.temporaryDirectory.appendingPathComponent(UUID().uuidString+".json")
        try JSONEncoder().encode(invalid).write(to:url)
        XCTAssertThrowsError(try store.importBackup(from:url))
        XCTAssertTrue(store.state.completedLessons.contains("rust.ownership"))
    }
    func testCorruptProgressIsPreserved() throws {
        let content=try Curriculum.load(); let url=URL.temporaryDirectory.appendingPathComponent(UUID().uuidString+".json")
        let corrupt=Data("not JSON".utf8); try corrupt.write(to:url)
        let store=LearningStore(curriculum:content,fileURL:url)
        XCTAssertFalse(store.loadedSuccessfully)
        store.save()
        XCTAssertEqual(try Data(contentsOf:url),corrupt)
    }
    func testRunnerRejectsInsecureOrCredentialBearingURLs() {
        for url in ["http://example.com", "https://user:pass@example.com", "https://example.com?secret=x", "https://example.com#fragment", ""] {
            XCTAssertThrowsError(try RemoteExecutionService.endpoint(base:url,path:"v1/execute"))
        }
        XCTAssertEqual(try RemoteExecutionService.endpoint(base:"https://runner.example/api",path:"v1/execute").absoluteString,"https://runner.example/api/v1/execute")
    }
    func testGitHubParsesLicenseAndRepositoryURL() throws {
        let data=Data(#"{"items":[{"id":1,"full_name":"rust-lang/rustlings","html_url":"https://github.com/rust-lang/rustlings","description":"Exercises","stargazers_count":10,"language":"Rust","license":{"spdx_id":"MIT"},"updated_at":"2026-10-13T00:00:00Z"}]}"#.utf8)
        let response=try JSONDecoder().decode(GitHubSearchResponse.self,from:data)
        XCTAssertEqual(response.items[0].license?.spdxID,"MIT")
        XCTAssertEqual(response.items[0].htmlURL.host,"github.com")
    }
}

@MainActor final class CredentialTests: XCTestCase {
    func testRunnerTokensAreScopedToTheirServerAndExcludedFromBackups() throws {
        let base="https://\(UUID().uuidString.lowercased()).example/runner"
        let token="test-token-"+UUID().uuidString
        defer { try? RunnerCredential.save("",base:base) }
        try RunnerCredential.save(token,base:base)
        XCTAssertEqual(RunnerCredential.read(base:base),token)
        XCTAssertEqual(RunnerCredential.read(base:base+"/"),token)
        XCTAssertNil(RunnerCredential.read(base:"https://different.example/runner"))
        let backup=String(data:try JSONEncoder().encode(LearningState()),encoding:.utf8)!
        XCTAssertFalse(backup.contains(token))
    }
}

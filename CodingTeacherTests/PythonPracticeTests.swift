import XCTest
import SwiftUI
@testable import CodingTeacher

@MainActor final class PythonPracticeTests: XCTestCase {
    private func makeStore() throws -> LearningStore {
        LearningStore(curriculum: try Curriculum.load(), fileURL: URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
    }
    func testGuideReferencesPrerequisitesAndAssessmentContracts() throws {
        let c = try Curriculum.load()
        let guide = try XCTUnwrap(c.courses.first { $0.id == "guide.python-ml" })
        let ids = guide.chapters.flatMap(\.lessonIDs)
        XCTAssertFalse(ids.isEmpty)
        XCTAssertEqual(ids.count, Set(ids).count)
        var seen: Set<String> = []
        for id in ids {
            let lesson = try XCTUnwrap(c.lessons.first { $0.id == id })
            XCTAssertTrue(Set(lesson.prerequisiteIDs ?? []).isSubset(of: seen))
            seen.insert(id)
            XCTAssertGreaterThanOrEqual(lesson.exercises?.count ?? 0, 3)
            XCTAssertGreaterThanOrEqual(lesson.quiz?.count ?? 0, 5)
            XCTAssertTrue(lesson.requiresCompletionForRecall)
            for item in lesson.quiz ?? [] {
                XCTAssertTrue(item.options.indices.contains(item.answerIndex))
                XCTAssertEqual(item.options.count, Set(item.options).count)
            }
        }
    }
    func testCumulativeAssessmentsAndDiagnosticDoNotChangeProgress() throws {
        let store = try makeStore()
        let c = store.curriculum
        let guide = try XCTUnwrap(c.courses.first { $0.id == "guide.python-ml" })
        XCTAssertEqual(guide.chapters.count, 24)
        XCTAssertEqual(c.pythonDiagnostic.count, guide.chapters.count)
        let last = try XCTUnwrap(guide.chapters.last)
        let items = c.assessment(for: last, course: guide)
        XCTAssertEqual(Set(items.map(\.id)).count, items.count)
        let firstID = try XCTUnwrap(guide.chapters[0].lessonIDs.last)
        XCTAssertTrue(items.contains { $0.id.hasPrefix(firstID+".") })
        // Stage 06 ends with optional supplements; review must sample its core exit lesson instead.
        XCTAssertTrue(items.contains { $0.id.hasPrefix("guide.python.context-exit.") })
        XCTAssertFalse(items.contains { $0.id.hasPrefix("guide.python.magnitude-protocol.") })
        let opening = try XCTUnwrap(guide.chapters.first)
        let openingID = try XCTUnwrap(opening.lessonIDs.first)
        let openingItems = c.assessment(for: opening, course: guide)
        XCTAssertTrue(openingItems.contains { $0.id == openingID+".q.reasoning" })
        XCTAssertTrue(openingItems.contains { $0.id == openingID+".q.transfer-boundary" })
        XCTAssertEqual(c.pythonDiagnostic.first?.id, openingID+".q.reasoning")
        let diagnostic = c.pythonDiagnostic
        let answers = Dictionary(uniqueKeysWithValues: diagnostic.map { ($0.id, $0.answerIndex) })
        XCTAssertNotNil(store.recordQuiz(scopeID: "guide.python-ml.diagnostic", items: diagnostic, answers: answers))
        XCTAssertTrue(store.state.completedLessons.isEmpty)
        XCTAssertNil(store.state.reviewedExercises)
    }
    func testLegacyProgressDecodesAndNewAssessmentsRoundTripSeparately() throws {
        let store = try makeStore()
        var object = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(LearningState())) as? [String: Any])
        for key in ["exerciseDrafts", "reviewedExercises", "reviewedProjects", "exerciseRuns", "quizAttempts"] { object.removeValue(forKey: key) }
        object["drafts"] = ["javascript": "old saved draft", "python": "print(7)"]
        let legacy = try JSONDecoder().decode(LearningState.self, from: JSONSerialization.data(withJSONObject: object))
        store.state = legacy
        let lesson = try XCTUnwrap(store.curriculum.lessons.first { $0.exercises != nil })
        let exercise = try XCTUnwrap(lesson.exercises?.first)
        let items = try XCTUnwrap(lesson.quiz)
        XCTAssertNil(store.recordQuiz(scopeID: lesson.id, items: items, answers: [:]))
        var answers = Dictionary(uniqueKeysWithValues: items.map { ($0.id, $0.answerIndex) })
        answers[items[0].id] = 100
        XCTAssertNil(store.recordQuiz(scopeID: lesson.id, items: items, answers: answers))
        answers[items[0].id] = items[0].answerIndex
        let score = try XCTUnwrap(store.recordQuiz(scopeID: lesson.id, items: items, answers: answers))
        XCTAssertEqual(score.correct, items.count)
        XCTAssertFalse(store.state.completedLessons.contains(lesson.id))
        store.exerciseDraft("my separate draft", id: exercise.id)
        store.recordExerciseRun(id: exercise.id, source: "print(0)", result: ExecutionResult(stdout: "0", stderr: "", exitCode: 0, runtime: "test", diagnostics: nil))
        XCTAssertNil(store.state.reviewedExercises)
        store.markExerciseReviewed(exercise.id, reviewed: true)
        let decoded = try JSONDecoder().decode(LearningState.self, from: JSONEncoder().encode(store.state))
        XCTAssertEqual(decoded.drafts["javascript"], "old saved draft")
        XCTAssertEqual(decoded.exerciseDrafts?[exercise.id], "my separate draft")
        XCTAssertEqual(decoded.quizAttempts?.first?.correct, items.count)
        XCTAssertEqual(decoded.exerciseRuns?.first?.exitCode, 0)
        XCTAssertTrue(decoded.reviewedExercises?.contains(exercise.id) == true)
        XCTAssertFalse(decoded.completedLessons.contains(lesson.id))
        let backup = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString+".json")
        try JSONEncoder().encode(decoded).write(to: backup)
        let restored = try makeStore()
        try restored.importBackup(from: backup)
        XCTAssertEqual(restored.state.exerciseDrafts, decoded.exerciseDrafts)
        XCTAssertEqual(restored.state.quizAttempts?.first?.id, score.id)
    }
    func testTransferPracticePreservesEarlierDraftsScoresAndRecall() throws {
        let store = try makeStore()
        let lesson = try XCTUnwrap(store.curriculum.lessons.first { ($0.exercises ?? []).contains { $0.id.hasSuffix(".transfer") } })
        let original = try XCTUnwrap(lesson.exercises?.first)
        let transfer = try XCTUnwrap(lesson.exercises?.first { $0.id.hasSuffix(".transfer") })
        let items = try XCTUnwrap(lesson.quiz)
        XCTAssertEqual(items.count, 7)
        XCTAssertEqual(lesson.exercises?.count, 4)
        let originalItems = Array(items.prefix(5))
        let oldAnswers = Dictionary(uniqueKeysWithValues: originalItems.map { ($0.id, $0.answerIndex) })
        let earlier = try XCTUnwrap(store.recordQuiz(scopeID: lesson.id, items: originalItems, answers: oldAnswers))
        store.exerciseDraft("original saved work", id: original.id)
        store.exerciseDraft("new transfer work", id: transfer.id)
        store.markExerciseReviewed(original.id, reviewed: true)
        let answers = Dictionary(uniqueKeysWithValues: items.map { ($0.id, $0.answerIndex) })
        XCTAssertNotNil(store.recordQuiz(scopeID: lesson.id, items: items, answers: answers))
        let state = try JSONDecoder().decode(LearningState.self, from: JSONEncoder().encode(store.state))
        XCTAssertEqual(state.exerciseDrafts?[original.id], "original saved work")
        XCTAssertEqual(state.exerciseDrafts?[transfer.id], "new transfer work")
        XCTAssertTrue(state.reviewedExercises?.contains(original.id) == true)
        XCTAssertFalse(state.reviewedExercises?.contains(transfer.id) == true)
        XCTAssertEqual(state.quizAttempts?.first { $0.id == earlier.id }?.questionIDs, originalItems.map(\.id))
        let addedCard = try XCTUnwrap(store.curriculum.cards.first { $0.id == lesson.id+".3" })
        XCTAssertFalse(store.isEligible(addedCard))
        XCTAssertFalse(state.completedLessons.contains(lesson.id))
    }
    func testMalformedQuizBackupDoesNotReplaceProgress() throws {
        let store = try makeStore()
        store.state.completedLessons = ["python.aliasing"]
        var invalid = LearningState()
        invalid.quizAttempts = [QuizAttempt(scopeID: "bad", questionIDs: ["one"], answers: [0], correct: 2)]
        let path = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString+".json")
        try JSONEncoder().encode(invalid).write(to: path)
        XCTAssertThrowsError(try store.importBackup(from: path))
        XCTAssertTrue(store.state.completedLessons.contains("python.aliasing"))
    }
    func testLeavingExerciseCancelsPendingRunAndReleasesController() async throws {
        let store = try makeStore()
        let lesson = try XCTUnwrap(store.curriculum.lessons.first { $0.exercises != nil })
        let exercise = try XCTUnwrap(lesson.exercises?.first)
        let started = expectation(description: "practice operation started")
        let cancelled = expectation(description: "practice operation cancelled on dismissal")
        var controller: LabExecutionController? = LabExecutionController(operation: { _, _, _, _ in
            started.fulfill()
            do { try await Task.sleep(for: .seconds(30)) }
            catch { cancelled.fulfill(); throw error }
            return ExecutionResult(stdout: "late", stderr: "", exitCode: 0, runtime: "test", diagnostics: nil)
        })
        weak var weakController = controller
        var host: UIHostingController<AnyView>? = UIHostingController(rootView: AnyView(PracticeExerciseView(exercise: exercise, lesson: lesson, execution: controller!).environment(store)))
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(x: 0, y: 0, width: 393, height: 852)
        window.rootViewController = host; window.isHidden = false
        host?.view.frame = window.bounds; window.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(150))
        controller?.start(language: .python, source: "pending", stdin: "", base: "") { _ in XCTFail("dismissed practice must not publish") }
        await fulfillment(of: [started], timeout: 2)
        controller = nil
        window.rootViewController = nil; window.isHidden = true; host = nil
        await fulfillment(of: [cancelled], timeout: 2)
        for _ in 0..<50 where weakController != nil { try await Task.sleep(for: .milliseconds(20)) }
        XCTAssertNil(weakController)
    }
    func testPracticeScreensRenderAndReleaseHosts() async throws {
        let store = try makeStore()
        let lesson = try XCTUnwrap(store.curriculum.lessons.first { $0.exercises != nil })
        let exercise = try XCTUnwrap(lesson.exercises?.first)
        let guide = try XCTUnwrap(store.curriculum.courses.first { $0.id == "guide.python-ml" })
        let library = BookLibrary(root: URL.temporaryDirectory.appendingPathComponent(UUID().uuidString))
        let screens: [(String, AnyView)] = [
            ("python-data-model", AnyView(NavigationStack { LessonView(lesson: store.curriculum.lessons.first { $0.id == "guide.python.numeric-dispatch" }!, track: store.track("python")!) })),
            ("python-capstone", AnyView(NavigationStack { LessonView(lesson: store.curriculum.lessons.first { $0.id == "guide.python.capstone-production" }!, track: store.track("python")!) })),
            ("python-path", AnyView(NavigationStack { SourceCourseDetailView(course: guide) })),
            ("python-problems", AnyView(NavigationStack { PythonPracticeBank() })),
            ("python-lesson", AnyView(NavigationStack { LessonView(lesson: lesson, track: store.track(lesson.trackID)!) })),
            ("python-exercise", AnyView(NavigationStack { PracticeExerciseView(exercise: exercise, lesson: lesson) })),
            ("python-quiz", AnyView(NavigationStack { QuizPracticeView(scopeID: lesson.id, title: lesson.title, items: lesson.quiz!) }))
        ]
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        for (name, screen) in screens {
            var host: UIHostingController<AnyView>? = UIHostingController(rootView: AnyView(screen.environment(store).environment(library).preferredColorScheme(.dark)))
            weak var weakHost = host
            let window = UIWindow(windowScene: scene)
            window.frame = CGRect(x: 0, y: 0, width: 393, height: 852)
            window.rootViewController = host
            window.isHidden = false
            host?.view.frame = window.bounds
            window.layoutIfNeeded()
            host?.view.layoutIfNeeded()
            try await Task.sleep(for: .milliseconds(250))
            let attachment = try makePNGTestAttachment(named: name) {
                UIGraphicsImageRenderer(bounds: window.bounds).image { _ in window.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
            }
            add(attachment)
            window.rootViewController = nil; window.isHidden = true; host = nil
            for _ in 0..<50 where weakHost != nil { try await Task.sleep(for: .milliseconds(20)) }
            XCTAssertNil(weakHost, name+" host retained")
        }
    }
}

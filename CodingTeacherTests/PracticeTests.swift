import XCTest
import SwiftUI
import UIKit
@testable import CodingTeacher

@MainActor final class PracticeTests: XCTestCase {
    private func store(url: URL? = nil) throws -> LearningStore {
        LearningStore(curriculum: try Curriculum.load(), fileURL: url ?? URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
    }
    func testCppGuideRelationshipsRequirementsAndRecallGating() throws {
        let store = try store()
        let guide = try XCTUnwrap(store.curriculum.courses.first { $0.id == "guide.cpp" })
        XCTAssertEqual(guide.chapters.count, 11)
        let ids = guide.chapters.flatMap(\.lessonIDs)
        XCTAssertGreaterThan(ids.count, 100)
        XCTAssertEqual(Set(ids).count, ids.count)
        let problems = try XCTUnwrap(store.curriculum.problems)
        XCTAssertEqual(Set(problems.map(\.id)).count, problems.count)
        let guideProblems = problems
        let guided = guideProblems.filter { !$0.id.contains(".drill.") }
        XCTAssertEqual(guided.count, ids.count)
        XCTAssertGreaterThan(guideProblems.count - guided.count, 2 * ids.count, "Each lesson should carry drills")
        XCTAssertTrue(guideProblems.allSatisfy { ids.contains($0.lessonID) && $0.options.indices.contains($0.answerIndex) })
        let positions = Dictionary(uniqueKeysWithValues: ids.enumerated().map { ($0.element, $0.offset) })
        for id in ids {
            let lesson = try XCTUnwrap(store.curriculum.lessons.first { $0.id == id })
            let requirements = try XCTUnwrap(lesson.requirements)
            XCTAssertTrue([14, 17, 20, 23, 26].contains(requirements.standard))
            XCTAssertTrue(requirements.prerequisiteLessonIDs.allSatisfy { positions[$0, default: Int.max] < positions[id, default: 0] })
            XCTAssertTrue(lesson.requiresCompletionForRecall)
            XCTAssertGreaterThanOrEqual(lesson.body.count, 3)
            let cards = store.curriculum.cards.filter { $0.lessonID == id }
            XCTAssertEqual(cards.count, 2)
            XCTAssertTrue(cards.allSatisfy { !store.isEligible($0) })
            if requirements.standard == 26 { XCTAssertFalse(requirements.serverDefaultCompatible); XCTAssertTrue(lesson.code.isEmpty) }
        }
        let first = try XCTUnwrap(store.curriculum.lessons.first { $0.id == ids[0] })
        store.complete(first)
        XCTAssertTrue(store.curriculum.cards.filter { $0.lessonID == first.id }.allSatisfy { store.isEligible($0) })
        XCTAssertEqual(store.lessons(for: "cpp").count, 3)
        for problem in guided where !problem.starter.isEmpty {
            let card = try XCTUnwrap(store.curriculum.cards.first { $0.id == problem.lessonID + ".1" })
            XCTAssertTrue(card.prompt.contains(problem.starter), "Recall lacks program context: \(card.id)")
        }
        for quiz in store.curriculum.quizzes ?? [] {
            XCTAssertEqual(Set(quiz.questionIDs).count, quiz.questionIDs.count)
            XCTAssertTrue(quiz.questionIDs.allSatisfy { id in problems.contains { $0.id == id } })
            if quiz.id.hasPrefix("quiz.cpp.stage-") { XCTAssertEqual(quiz.questionIDs.count, 10); XCTAssertEqual(quiz.durationSeconds, 900) }
            if quiz.id.hasPrefix("quiz.cpp.drills-") { XCTAssertEqual(quiz.questionIDs.count, 15); XCTAssertNotNil(quiz.stageID) }
            if quiz.id.hasPrefix("quiz.cpp.mock-") { XCTAssertEqual(quiz.questionIDs.count, 25); XCTAssertEqual(quiz.durationSeconds, 1800) }
        }
    }
    func testFiltersCombineTopicVersionSourceDifficultyAndAttemptStatus() throws {
        let problem = try XCTUnwrap(try store().curriculum.problems?.first)
        XCTAssertTrue(problem.matches(query: "program", standard: 14, difficulty: "Beginner", source: "hayden", status: "Unattempted", attempted: false))
        XCTAssertFalse(problem.matches(query: "program", standard: 23, difficulty: nil, source: nil, status: nil, attempted: false))
        XCTAssertFalse(problem.matches(query: "", standard: nil, difficulty: nil, source: "unknown-source", status: nil, attempted: false))
        XCTAssertFalse(problem.matches(query: "", standard: nil, difficulty: nil, source: nil, status: "Unattempted", attempted: true))
    }
    func testProblemDraftsAttemptsAndBackupRemainIsolatedFromLanguageDrafts() throws {
        let url = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json")
        let original = try store(url: url)
        let problems = try XCTUnwrap(original.curriculum.problems)
        original.draft("my existing C++ code", language: .cpp)
        original.practiceDraft("first answer", problemID: problems[0].id)
        original.practiceDraft("second answer", problemID: problems[1].id)
        original.recordPractice("first answer", problemID: problems[0].id, assessment: "Needs more practice")
        original.save()
        let reloaded = try store(url: url)
        XCTAssertEqual(reloaded.state.drafts["cpp"], "my existing C++ code")
        XCTAssertEqual(reloaded.state.problemDrafts?[problems[0].id], "first answer")
        XCTAssertEqual(reloaded.state.problemDrafts?[problems[1].id], "second answer")
        let restored = try store()
        try restored.importBackup(from: original.exportURL())
        XCTAssertEqual(restored.state.practiceAttempts?.first?.response, "first answer")
        XCTAssertEqual(restored.state.problemDrafts, original.state.problemDrafts)
    }
    func testLegacyStateAndCurriculumDecodeWithoutNewFields() throws {
        var state = LearningState()
        state.drafts["javascript"] = "preserve this excluded runner draft"
        var json = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(state)) as? [String: Any])
        for key in ["problemDrafts", "practiceAttempts", "quizSessions"] { json.removeValue(forKey: key) }
        let restored = try JSONDecoder().decode(LearningState.self, from: JSONSerialization.data(withJSONObject: json))
        XCTAssertEqual(restored.drafts["javascript"], state.drafts["javascript"])
        XCTAssertNil(restored.quizSessions)
        var curriculum = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(try Curriculum.load())) as? [String: Any])
        curriculum.removeValue(forKey: "problems"); curriculum.removeValue(forKey: "quizzes")
        let decoded = try JSONDecoder().decode(Curriculum.self, from: JSONSerialization.data(withJSONObject: curriculum))
        XCTAssertNil(decoded.problems)
        XCTAssertNil(decoded.quizzes)
    }
    func testTimedQuizPersistsExpiresExactlyOnceAndRejectsLateAnswers() throws {
        let original = try store()
        let quiz = try XCTUnwrap(original.curriculum.quizzes?.first { $0.stageID != nil })
        let now = Date(timeIntervalSince1970: 1_800_000_000)
        let id = original.startQuiz(quiz, timed: true, now: now)
        let question = try XCTUnwrap(original.curriculum.problems?.first { $0.id == quiz.questionIDs[0] })
        original.answerQuiz(id, questionID: question.id, option: question.answerIndex, now: now.addingTimeInterval(10))
        let restored = try store()
        try restored.importBackup(from: original.exportURL())
        XCTAssertEqual(restored.startQuiz(quiz, timed: false, now: now.addingTimeInterval(20)), id)
        restored.expireQuiz(id, now: now.addingTimeInterval(901))
        let completed = try XCTUnwrap(restored.quizSession(id))
        XCTAssertEqual(completed.finishedAt, now.addingTimeInterval(900))
        XCTAssertEqual(completed.correctCount(in: restored.curriculum.problems ?? []), 1)
        XCTAssertEqual(completed.percent(in: restored.curriculum.problems ?? []), 10)
        restored.answerQuiz(id, questionID: quiz.questionIDs[1], option: 0, now: now.addingTimeInterval(902))
        restored.finishQuiz(id, now: now.addingTimeInterval(903))
        XCTAssertEqual(restored.quizSession(id)?.responses.count, 1)
        XCTAssertEqual(restored.quizSession(id)?.finishedAt, completed.finishedAt)
        let newer = restored.startQuiz(quiz, timed: true, now: now.addingTimeInterval(904))
        restored.expireQuiz(id, now: now.addingTimeInterval(2_000))
        XCTAssertNotEqual(newer, id)
        XCTAssertNil(restored.quizSession(newer)?.finishedAt)
    }
    func testUntimedPlacementAndInvalidOptions() throws {
        let store = try store()
        let quiz = try XCTUnwrap(store.curriculum.quizzes?.first { $0.stageID == nil })
        let now = Date()
        let id = store.startQuiz(quiz, timed: true, now: now)
        XCTAssertNil(store.quizSession(id)?.deadline)
        store.answerQuiz(id, questionID: quiz.questionIDs[0], option: 999, now: now)
        store.answerQuiz(id, questionID: "unknown", option: 0, now: now)
        XCTAssertTrue(store.quizSession(id)?.responses.isEmpty == true)
        store.expireQuiz(id, now: now.addingTimeInterval(100_000))
        XCTAssertNil(store.quizSession(id)?.finishedAt)
        store.finishQuiz(id, now: now)
        XCTAssertEqual(store.quizSession(id)?.percent(in: store.curriculum.problems ?? []), 0)
    }
    func testPlacementSuggestsEarliestMissedStageWithoutUnlockingLessons() throws {
        let store = try store()
        let quiz = try XCTUnwrap(store.curriculum.quizzes?.first { $0.stageID == nil })
        let id = store.startQuiz(quiz, timed: false)
        let stages = try XCTUnwrap(store.curriculum.courses.first { $0.id == "guide.cpp" }?.chapters)
        XCTAssertNil(store.quizSession(id)?.suggestedRevisionStage(in: store.curriculum))
        for questionID in quiz.questionIDs.prefix(2) {
            let problem = try XCTUnwrap(store.curriculum.problems?.first { $0.id == questionID })
            store.answerQuiz(id, questionID: questionID, option: problem.answerIndex)
        }
        store.finishQuiz(id)
        XCTAssertEqual(store.quizSession(id)?.suggestedRevisionStage(in: store.curriculum)?.id, stages[1].id)
        XCTAssertTrue(store.state.completedLessons.isEmpty)
        let perfect = store.startQuiz(quiz, timed: false)
        for questionID in quiz.questionIDs {
            let problem = try XCTUnwrap(store.curriculum.problems?.first { $0.id == questionID })
            store.answerQuiz(perfect, questionID: questionID, option: problem.answerIndex)
        }
        store.finishQuiz(perfect)
        XCTAssertNil(store.quizSession(perfect)?.suggestedRevisionStage(in: store.curriculum))
        XCTAssertTrue(store.state.completedLessons.isEmpty)
    }
    func testPracticeDebounceDoesNotRetainStore() throws {
        var store: LearningStore? = try self.store()
        weak var reference = store
        store?.practiceDraft("pending response", problemID: "problem.cpp.first-program")
        store = nil
        XCTAssertNil(reference)
    }
    func testPracticeScreensRenderAndReleaseIncludingActiveCountdown() async throws {
        let store = try store()
        let library = BookLibrary(root: URL.temporaryDirectory.appendingPathComponent(UUID().uuidString))
        let problem = try XCTUnwrap(store.curriculum.problems?.first)
        let quiz = try XCTUnwrap(store.curriculum.quizzes?.first { $0.stageID != nil })
        let id = store.startQuiz(quiz, timed: true)
        let reviewQuiz = try XCTUnwrap(store.curriculum.quizzes?.last)
        let reviewID = store.startQuiz(reviewQuiz, timed: false)
        store.finishQuiz(reviewID)
        let cpp = try XCTUnwrap(store.track("cpp"))
        let project = try XCTUnwrap(store.curriculum.lessons.first { $0.id == "guide.cpp.coroutine-project" })
        let screens: [(String, AnyView)] = [
            ("cpp-practice-library", AnyView(PracticeLibraryView())),
            ("cpp-problem", AnyView(PracticeProblemView(problem: problem))),
            ("cpp-quiz-entry", AnyView(Page { QuizEntryView(quiz: quiz) })),
            ("cpp-active-quiz", AnyView(QuizSessionView(quiz: quiz, timed: true, existingID: id))),
            ("cpp-finished-quiz", AnyView(QuizSessionView(quiz: reviewQuiz, timed: false, existingID: reviewID))),
            ("cpp-coroutine-project", AnyView(LessonView(lesson: project, track: cpp)))
        ]
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        for (name, screen) in screens {
            var host: UIHostingController<AnyView>? = UIHostingController(rootView: AnyView(NavigationStack { screen }.environment(store).environment(library)))
            weak var reference = host
            let window = UIWindow(windowScene: scene)
            window.frame = CGRect(x: 0, y: 0, width: 393, height: 852)
            window.rootViewController = host; window.isHidden = false
            window.layoutIfNeeded()
            try await Task.sleep(for: .milliseconds(250))
            let image = UIGraphicsImageRenderer(size: window.bounds.size).image { _ in window.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
            let attachment = XCTAttachment(image: image); attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
            window.isHidden = true; window.rootViewController = nil; host = nil
            try await Task.sleep(for: .milliseconds(250))
            XCTAssertNil(reference, "Retained practice host: \(name)")
        }
        store.finishQuiz(id)
    }
}

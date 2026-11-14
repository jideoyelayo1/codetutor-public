import Foundation

struct LessonRequirements: Codable, Hashable {
    let standard: Int
    let difficulty: String
    let topics, prerequisiteLessonIDs, sourceIDs: [String]
    let support, compileCommand: String
    let serverDefaultCompatible: Bool
}

struct PracticeProblem: Codable, Identifiable, Hashable {
    let id, lessonID, title, prompt, kind, difficulty: String
    let standard: Int
    let topics, sourceIDs, hints, rubric, edgeCases: [String]
    let starter, solution, explanation, quizExplanation, complexity: String
    let question: String
    let options: [String]
    let answerIndex: Int

    func matches(query: String, standard: Int?, difficulty: String?, source: String?, status: String?, attempted: Bool) -> Bool {
        (standard == nil || self.standard == standard) &&
        (difficulty == nil || self.difficulty == difficulty) &&
        (source == nil || sourceIDs.contains(source!)) &&
        (status == nil || (status == "Attempted" ? attempted : !attempted)) &&
        (query.isEmpty || ([title, prompt, kind, self.difficulty] + topics + sourceIDs).joined(separator: " ").localizedCaseInsensitiveContains(query))
    }
}

struct PracticeQuiz: Codable, Identifiable, Hashable {
    let id, title: String
    let stageID: String?
    let questionIDs: [String]
    let durationSeconds: Int
    let passPercent: Int
}

struct PracticeAttempt: Codable, Identifiable {
    var id = UUID()
    let problemID: String
    let date: Date
    let response: String
    let selfAssessment: String
}

struct QuizSession: Codable, Identifiable {
    var id = UUID()
    let quizID: String
    let questionIDs: [String]
    let startedAt: Date
    let deadline: Date?
    var responses: [String: Int] = [:]
    var finishedAt: Date?

    func isExpired(at date: Date) -> Bool { deadline.map { date >= $0 } ?? false }
    func correctCount(in problems: [PracticeProblem]) -> Int {
        let answers = Dictionary(problems.map { ($0.id, $0.answerIndex) }, uniquingKeysWith: { first, _ in first })
        return questionIDs.filter { id in
            guard let expected = answers[id], let response = responses[id] else { return false }
            return expected == response
        }.count
    }
    func percent(in problems: [PracticeProblem]) -> Int {
        questionIDs.isEmpty ? 0 : correctCount(in: problems) * 100 / questionIDs.count
    }
    func suggestedRevisionStage(in curriculum: Curriculum) -> SourceChapter? {
        guard finishedAt != nil else { return nil }
        let problems = Dictionary((curriculum.problems ?? []).map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
        let missedLessons = Set(questionIDs.compactMap { id -> String? in
            guard let problem = problems[id] else { return nil }
            return responses[id] == problem.answerIndex ? nil : problem.lessonID
        })
        return curriculum.courses.first { $0.id == "guide.cpp" }?.chapters.first {
            !missedLessons.isDisjoint(with: $0.lessonIDs)
        }
    }
}

extension LearningStore {
    func practiceDraft(_ response: String, problemID: String) {
        state.problemDrafts = state.problemDrafts ?? [:]
        state.problemDrafts?[problemID] = response
        // Reuse the weak, cancellable debounce owned by the store.
        schedulePracticeSave()
    }
    func recordPractice(_ response: String, problemID: String, assessment: String, now: Date = .now) {
        guard curriculum.problems?.contains(where: { $0.id == problemID }) == true else { return }
        state.practiceAttempts = state.practiceAttempts ?? []
        state.practiceAttempts?.insert(PracticeAttempt(problemID: problemID, date: now, response: response, selfAssessment: assessment), at: 0)
        save()
    }
    @discardableResult func startQuiz(_ quiz: PracticeQuiz, timed: Bool, now: Date = .now) -> UUID {
        state.quizSessions = state.quizSessions ?? []
        if let existing = state.quizSessions?.first(where: { $0.quizID == quiz.id && $0.finishedAt == nil }) {
            expireQuiz(existing.id, now: now)
            return existing.id
        }
        let session = QuizSession(quizID: quiz.id, questionIDs: quiz.questionIDs, startedAt: now,
                                  deadline: timed && quiz.durationSeconds > 0 ? now.addingTimeInterval(Double(quiz.durationSeconds)) : nil)
        state.quizSessions?.insert(session, at: 0)
        save()
        return session.id
    }
    func quizSession(_ id: UUID?) -> QuizSession? { state.quizSessions?.first { $0.id == id } }
    func answerQuiz(_ id: UUID, questionID: String, option: Int, now: Date = .now) {
        expireQuiz(id, now: now)
        guard let index = state.quizSessions?.firstIndex(where: { $0.id == id }),
              let session = state.quizSessions?[index], session.finishedAt == nil,
              session.questionIDs.contains(questionID),
              let question = curriculum.problems?.first(where: { $0.id == questionID }),
              question.options.indices.contains(option) else { return }
        state.quizSessions?[index].responses[questionID] = option
        save()
    }
    func finishQuiz(_ id: UUID, now: Date = .now) {
        guard let index = state.quizSessions?.firstIndex(where: { $0.id == id }),
              let session = state.quizSessions?[index], session.finishedAt == nil else { return }
        state.quizSessions?[index].finishedAt = max(session.startedAt, session.deadline.map { min(now, $0) } ?? now)
        save()
    }
    func expireQuiz(_ id: UUID, now: Date = .now) {
        guard let session = quizSession(id), session.finishedAt == nil, session.isExpired(at: now) else { return }
        finishQuiz(id, now: now)
    }
}

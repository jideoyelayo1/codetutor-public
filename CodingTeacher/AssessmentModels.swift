import Foundation

/// Authored practice. Execution results never certify that the exercise contract is met.
struct PracticeExercise: Codable, Identifiable, Hashable {
    let id, kind, title, prompt, starter, solution, explanation: String
    let hints: [String]
    let expectedOutput: String?
}
struct QuizItem: Codable, Identifiable, Hashable {
    let id, question, explanation: String
    let code: String?
    let options: [String]
    let answerIndex: Int
}
struct ExerciseRun: Codable, Identifiable {
    var id = UUID()
    let exerciseID, source, output, runtime: String
    let exitCode: Int
    var date = Date()
}
struct QuizAttempt: Codable, Identifiable {
    var id = UUID()
    let scopeID: String
    let questionIDs: [String]
    let answers: [Int]
    let correct: Int
    var date = Date()
    var isValid: Bool {
        !questionIDs.isEmpty && Set(questionIDs).count == questionIDs.count &&
        answers.count == questionIDs.count && answers.allSatisfy { (0..<10).contains($0) } &&
        (0...questionIDs.count).contains(correct) && date.timeIntervalSince1970.isFinite
    }
}


extension Curriculum {
    /// Extra authored practice inside a source chapter's page range; existing assignments keep their IDs.
    func additionalSourcePractice(for chapter: SourceChapter, course: SourceCourse) -> [Lesson] {
        guard course.chapters.contains(where: { $0.id == chapter.id }),
              let bookID = chapter.reading.bookID, let start = chapter.reading.pdfPage else { return [] }
        let end = course.chapters.compactMap { candidate -> Int? in
            guard candidate.reading.bookID == bookID, let page = candidate.reading.pdfPage, page > start else { return nil }
            return page
        }.min() ?? Int.max
        let assigned = Set(chapter.lessonIDs)
        return lessons.filter { lesson in
            lesson.exercises != nil && !assigned.contains(lesson.id) && (lesson.reading ?? []).contains { reading in
                guard reading.bookID == bookID, let page = reading.pdfPage else { return false }
                return start <= page && page < end
            }
        }
    }
    /// Current-stage questions plus a sample from every preceding stage; no progress is inferred.
    func assessment(for chapter: SourceChapter, course: SourceCourse) -> [QuizItem] {
        let byID = Dictionary(uniqueKeysWithValues: lessons.map { ($0.id, $0) })
        let current = chapter.lessonIDs.compactMap { byID[$0] }
        guard course.id.hasPrefix("guide.python-ml"),
              let path = courses.first(where: { $0.id == "guide.python-ml" }),
              let position = path.chapters.firstIndex(where: { $0.lessonIDs == chapter.lessonIDs }) else {
            return current.flatMap { ($0.quiz ?? []).prefix(1) }
        }
        let earlier = path.chapters.prefix(position).enumerated().compactMap { index, stage -> QuizItem? in
            // Optional supplements are appended to a stage; its core exit lesson is the next stage's prerequisite.
            let next = path.chapters[index + 1].lessonIDs.first.flatMap { byID[$0] }
            guard let id = next?.prerequisiteIDs?.first(where: stage.lessonIDs.contains) ?? stage.lessonIDs.last else { return nil }
            return byID[id]?.quiz?.last
        }
        return current.flatMap { lesson in
            let quiz = lesson.quiz ?? []
            let reasoning = quiz.filter { $0.id.hasSuffix(".q.reasoning") || $0.id.hasSuffix(".q.transfer-boundary") }
            return Array(quiz.prefix(2)) + reasoning
        } + earlier
    }
    var pythonDiagnostic: [QuizItem] {
        guard let guide = courses.first(where: { $0.id == "guide.python-ml" }) else { return [] }
        let byID = Dictionary(uniqueKeysWithValues: lessons.map { ($0.id, $0) })
        return guide.chapters.compactMap { chapter in
            let quiz = chapter.lessonIDs.flatMap { byID[$0]?.quiz ?? [] }
            return quiz.first { $0.id.hasSuffix(".q.reasoning") } ?? quiz.first
        }
    }
}

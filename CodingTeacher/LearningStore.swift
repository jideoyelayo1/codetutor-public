import Foundation
import Observation
import FSRS

@MainActor @Observable final class LearningStore {
    let curriculum: Curriculum
    @ObservationIgnored private let gatedSourceLessonIDs: Set<String>
    var state: LearningState
    var errorMessage: String?
    var loadedSuccessfully = true
    private let fileURL: URL
    private var undoState: LearningState?
    @ObservationIgnored private var draftSaveTask: Task<Void, Never>?
    private let scheduler = FSRS(parameters: .init(w: FSRSDefaults.defaultWv6))

    init(curriculum: Curriculum, fileURL: URL? = nil) {
        self.curriculum = curriculum
        gatedSourceLessonIDs = Set(curriculum.lessons.filter { $0.requiresCompletionForRecall }.map(\.id))
        self.fileURL = fileURL ?? URL.applicationSupportDirectory.appendingPathComponent("CodingTeacher/progress.json")
        state = LearningState()
        if FileManager.default.fileExists(atPath: self.fileURL.path) {
            do {
                let restored = try JSONDecoder().decode(LearningState.self, from: Data(contentsOf: self.fileURL))
                guard restored.schemaVersion == 1 else { throw CocoaError(.coderReadCorrupt) }
                state = restored
            } catch {
                loadedSuccessfully = false
                errorMessage = "Your saved progress could not be read. The original file is preserved. Export it from Settings before repairing it. \(error.localizedDescription)"
            }
        }
        if loadedSuccessfully { state.enableNewTracks(curriculum.tracks.map(\.id)) }
    }
    deinit { draftSaveTask?.cancel() }
    func track(_ id: String) -> LearningTrack? { curriculum.tracks.first { $0.id == id } }
    // Learn lists "learn" and "retain" tracks.
    func tracks(mode: String, matching query: String = "") -> [LearningTrack] {
        curriculum.tracks.filter { $0.mode == mode && (query.isEmpty || ($0.name + " " + $0.subtitle).localizedCaseInsensitiveContains(query)) }
    }
    func lessons(for track: String, includingSourceStudies: Bool = false) -> [Lesson] {
        let all = curriculum.lessons.filter { $0.trackID == track }.sorted { $0.order < $1.order }
        let core = all.filter { $0.isSourceStudy != true }
        // A guide-only track such as Bash has no daily path, so its guide lessons are the path.
        return includingSourceStudies || core.isEmpty ? all : core
    }
    func completion(for track: String) -> Double {
        let all = lessons(for: track)
        return all.isEmpty ? 0 : Double(all.filter { state.completedLessons.contains($0.id) }.count) / Double(all.count)
    }
    func isEligible(_ card: RecallCard) -> Bool {
        guard state.enabledTracks.contains(card.trackID) else { return false }
        let requiresCompletion = gatedSourceLessonIDs.contains(card.lessonID)
        return (!requiresCompletion && track(card.trackID)?.isNew == false) || state.completedLessons.contains(card.lessonID)
    }
    func reviewQueue(now: Date = Date()) -> [RecallCard] {
        let eligible = curriculum.cards.filter(isEligible)
        let due = eligible.filter { state.schedules[$0.id].map { $0.due <= now } ?? false }.sorted {
            state.schedules[$0.id]!.due < state.schedules[$1.id]!.due
        }
        let introducedToday = Set(state.reviews.filter { Calendar.current.isDate($0.date, inSameDayAs: now) && $0.log.state == .new }.map(\.cardID)).count
        let remaining = max(0, state.dailyNewLimit - introducedToday)
        // Round-robin across tracks so a daily session is not consumed by one language.
        var unseen: [RecallCard] = []
        let groups = curriculum.tracks.filter { state.enabledTracks.contains($0.id) }.sorted { ($0.isNew ? 0 : 1) < ($1.isNew ? 0 : 1) }.map { t in
            eligible.filter { $0.trackID == t.id && state.schedules[$0.id] == nil }
        }
        for offset in 0..<(groups.map(\.count).max() ?? 0) {
            for group in groups where offset < group.count { unseen.append(group[offset]) }
        }
        return due + unseen.prefix(remaining)
    }
    func intervalLabel(for card: RecallCard, grade: RecallGrade, now: Date = Date()) -> String {
        guard let next = try? scheduler.next(card: state.schedules[card.id] ?? Card(due: now), now: now, grade: grade.rating).card else { return "—" }
        let seconds = max(0, next.due.timeIntervalSince(now))
        if seconds < 3600 { return "\(max(1, Int(seconds / 60)))m" }
        if seconds < 86400 { return "\(Int(seconds / 3600))h" }
        return "\(Int((seconds / 86400).rounded()))d"
    }
    @discardableResult func review(_ card: RecallCard, grade: RecallGrade, now: Date = Date()) -> Bool {
        do {
            let result = try scheduler.next(card: state.schedules[card.id] ?? Card(due: now), now: now, grade: grade.rating)
            undoState = state
            state.schedules[card.id] = result.card
            state.reviews.append(ReviewEvent(cardID: card.id, date: now, grade: grade.rawValue, log: result.log))
            save()
            return true
        } catch { errorMessage = error.localizedDescription; return false }
    }
    var canUndo: Bool { undoState != nil }
    func undoReview() {
        guard let old = undoState else { return }
        state = old; undoState = nil; save()
    }
    func complete(_ lesson: Lesson) { state.completedLessons.insert(lesson.id); save() }
    func draft(_ source: String, language: CodeLanguage) {
        state.drafts[language.rawValue] = source
        scheduleDraftSave()
    }
    func studyNote(_ note: String, id: String) {
        if state.studyNotes == nil { state.studyNotes = [:] }
        state.studyNotes?[id] = note
        scheduleDraftSave()
    }
    func markSourceRead(_ chapterID: String, read: Bool) {
        if state.readSourceChapters == nil { state.readSourceChapters = [] }
        if read { state.readSourceChapters?.insert(chapterID) }
        else { state.readSourceChapters?.remove(chapterID) }
        save()
    }
    func exerciseDraft(_ text: String, id: String) {
        if state.exerciseDrafts == nil { state.exerciseDrafts = [:] }
        state.exerciseDrafts?[id] = text
        scheduleDraftSave()
    }
    func markExerciseReviewed(_ id: String, reviewed: Bool) {
        if state.reviewedExercises == nil { state.reviewedExercises = [] }
        if reviewed { state.reviewedExercises?.insert(id) }
        else { state.reviewedExercises?.remove(id) }
        save()
    }
    func markProjectReviewed(_ id: String, reviewed: Bool) {
        if state.reviewedProjects == nil { state.reviewedProjects = [] }
        if reviewed { state.reviewedProjects?.insert(id) }
        else { state.reviewedProjects?.remove(id) }
        save()
    }
    func recordExerciseRun(id: String, source: String, result: ExecutionResult) {
        if state.exerciseRuns == nil { state.exerciseRuns = [] }
        state.exerciseRuns?.insert(ExerciseRun(exerciseID: id, source: source, output: result.output,
                                             runtime: result.runtime, exitCode: result.exitCode), at: 0)
        state.exerciseRuns = Array((state.exerciseRuns ?? []).prefix(100))
        save()
    }
    @discardableResult func recordQuiz(scopeID: String, items: [QuizItem], answers: [String: Int]) -> QuizAttempt? {
        guard !items.isEmpty, Set(items.map(\.id)).count == items.count,
              items.allSatisfy({ item in
                  item.options.indices.contains(item.answerIndex) &&
                  answers[item.id].map { item.options.indices.contains($0) } == true
              }) else { return nil }
        let choices = items.map { answers[$0.id]! }
        let correct = zip(items, choices).filter { $0.0.answerIndex == $0.1 }.count
        let attempt = QuizAttempt(scopeID: scopeID, questionIDs: items.map(\.id), answers: choices, correct: correct)
        if state.quizAttempts == nil { state.quizAttempts = [] }
        state.quizAttempts?.insert(attempt, at: 0)
        state.quizAttempts = Array((state.quizAttempts ?? []).prefix(200))
        save()
        return attempt
    }
    private func scheduleDraftSave() {
        draftSaveTask?.cancel()
        draftSaveTask = Task { [weak self] in
            try? await Task.sleep(for: .milliseconds(400))
            guard !Task.isCancelled else { return }
            self?.save()
        }
    }
    func schedulePracticeSave() { scheduleDraftSave() }
    func recordAttempt(language: CodeLanguage, source: String, result: ExecutionResult) {
        state.attempts.insert(Attempt(date: Date(), language: language, source: source, output: result.output, succeeded: result.succeeded), at: 0)
        state.attempts = Array(state.attempts.prefix(100)); save()
    }
    func reviewsToday(now: Date = Date()) -> Int { state.reviews.filter { Calendar.current.isDate($0.date, inSameDayAs: now) }.count }
    func streak(now: Date = Date()) -> Int {
        let calendar = Calendar.current
        let days = Set(state.reviews.map { calendar.startOfDay(for: $0.date) })
        var day = calendar.startOfDay(for: now)
        if !days.contains(day) { day = calendar.date(byAdding: .day, value: -1, to: day)! }
        var count = 0
        while days.contains(day) { count += 1; day = calendar.date(byAdding: .day, value: -1, to: day)! }
        return count
    }
    var recallRate: Double? {
        let recent = state.reviews.suffix(100)
        guard !recent.isEmpty else { return nil }
        return Double(recent.filter { $0.grade >= RecallGrade.good.rawValue }.count) / Double(recent.count)
    }
    func save() {
        draftSaveTask?.cancel(); draftSaveTask = nil
        guard loadedSuccessfully else { return }
        do {
            try FileManager.default.createDirectory(at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            try encoder.encode(state).write(to: fileURL, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
        } catch { errorMessage = "Progress could not be saved: \(error.localizedDescription)" }
    }
    func exportURL() throws -> URL {
        let target = URL.temporaryDirectory.appendingPathComponent("CodingTeacher-backup.json")
        if !loadedSuccessfully { try Data(contentsOf: fileURL).write(to: target, options: .atomic) }
        else { let e = JSONEncoder(); e.outputFormatting = .prettyPrinted; try e.encode(state).write(to: target, options: .atomic) }
        return target
    }
    func importBackup(from url: URL) throws {
        let access = url.startAccessingSecurityScopedResource(); defer { if access { url.stopAccessingSecurityScopedResource() } }
        let data = try Data(contentsOf: url)
        guard data.count < 10_000_000 else { throw CocoaError(.fileReadTooLarge) }
        let restored = try JSONDecoder().decode(LearningState.self, from: data)
        guard (restored.quizAttempts ?? []).allSatisfy(\.isValid), restored.schemaVersion == 1, (1...30).contains(restored.dailyNewLimit), (1...100).contains(restored.dailyReviewGoal), (5...120).contains(restored.dailyMinutes), restored.schedules.values.allSatisfy({ $0.stability.isFinite && $0.difficulty.isFinite }) else {
            throw CocoaError(.coderReadCorrupt)
        }
        // Keep a recoverable copy before replacing local progress.
        if FileManager.default.fileExists(atPath: fileURL.path) {
            try Data(contentsOf: fileURL).write(to: fileURL.deletingLastPathComponent().appendingPathComponent("progress-before-import.json"), options: .atomic)
        }
        state = restored; state.enableNewTracks(curriculum.tracks.map(\.id)); loadedSuccessfully = true; undoState = nil; save()
    }
}

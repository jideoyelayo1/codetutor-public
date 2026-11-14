import SwiftUI

struct PythonPracticeBank: View {
    @Environment(LearningStore.self) private var store
    @State private var query = ""
    @State private var kind = "All"
    @State private var trackID = "all"
    private var lessons: [Lesson] {
        store.curriculum.lessons.filter { lesson in
            lesson.exercises != nil && (trackID == "all" || lesson.trackID == trackID) &&
            (query.isEmpty || ([lesson.title, lesson.summary] + (lesson.learningObjectives ?? [])).joined(separator: " ").localizedCaseInsensitiveContains(query))
        }
    }
    var body: some View {
        Page {
            Text("Python & ML practice").font(.largeTitle.bold())
            Text("Choose a problem, write a solution, then compare its contract and edge cases. Reviews are self-assessed; a successful run only reports process execution.").foregroundStyle(Palette.muted)
            Picker("Library", selection: $trackID) {
                Text("All libraries").tag("all")
                ForEach(store.curriculum.tracks.filter { ["python", "numpy", "pandas", "sklearn", "pytorch"].contains($0.id) }) { Text($0.name).tag($0.id) }
            }
            Picker("Problem type", selection: $kind) {
                ForEach(["All", "Implement", "Predict", "Debug"], id: \.self) { Text($0).tag($0) }
            }
            LazyVStack(alignment: .leading, spacing: 16) {
                ForEach(lessons) { lesson in
                    ForEach((lesson.exercises ?? []).filter { kind == "All" || $0.kind == kind }) { exercise in
                        NavigationLink { PracticeExerciseView(exercise: exercise, lesson: lesson) } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(exercise.title).font(.headline)
                                Text("\(lesson.title) · \(exercise.kind)").font(.caption).foregroundStyle(Palette.muted)
                                if store.state.reviewedExercises?.contains(exercise.id) == true { Text("Self-reviewed").font(.caption) }
                            }.frame(maxWidth: .infinity, alignment: .leading).padding(14).background(Palette.panel, in: RoundedRectangle(cornerRadius: 12))
                        }.buttonStyle(.plain)
                    }
                }
            }
            if lessons.isEmpty { ContentUnavailableView.search(text: query) }
        }.searchable(text: $query, prompt: "Search concepts").navigationTitle("Problems")
    }
}

struct PracticeExerciseView: View {
    @Environment(LearningStore.self) private var store
    let exercise: PracticeExercise
    let lesson: Lesson
    @State private var draft = ""
    @State private var initialized = false
    @State private var hintCount = 0
    @State private var reveal = false
    @State private var execution = LabExecutionController()
    init(exercise: PracticeExercise, lesson: Lesson, execution: LabExecutionController? = nil) {
        self.exercise = exercise
        self.lesson = lesson
        _execution = State(initialValue: execution ?? LabExecutionController())
    }
    private var language: CodeLanguage { lesson.trackID == "python" ? .python : .pythonML }
    var body: some View {
        Page {
            SectionLabel(title: "\(exercise.kind) · \(lesson.title)")
            Text(exercise.title).font(.largeTitle.bold())
            Text(exercise.prompt).textSelection(.enabled)
            if exercise.kind == "Predict" {
                CodeBlock(code: exercise.starter)
                StudyNoteEditor(note: $draft, title: "Prediction and reasoning", prompt: "Predict before revealing the answer. Explain each step and the relevant invariant.")
            } else {
                CodeEditor(text: $draft, language: language).frame(minHeight: 300)
                Text("Run sends your code to the configured server. No hidden grader is installed; compare the contract and test cases yourself.").font(.caption).foregroundStyle(Palette.muted)
                if execution.running {
                    ActionButton(title: "Stop", icon: "stop") { execution.cancel() }
                } else {
                    ActionButton(title: "Run code", icon: "play") { run() }.disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
            if let error = execution.error { Text(error).foregroundStyle(.orange) }
            if let result = execution.result {
                Text("Process exit \(result.exitCode) · \(result.runtime)").font(.caption)
                CodeBlock(code: result.output.isEmpty ? "(No output)" : result.output)
            }
            ForEach(Array(exercise.hints.prefix(hintCount).enumerated()), id: \.offset) { _, hint in Text(hint) }
            if hintCount < exercise.hints.count { Button("Reveal next hint") { hintCount += 1 } }
            DisclosureGroup("Worked solution and explanation", isExpanded: $reveal) {
                if exercise.kind == "Predict" { Text(exercise.solution).textSelection(.enabled) }
                else { CodeBlock(code: exercise.solution) }
                Text(exercise.explanation)
                if let expected = exercise.expectedOutput { Text("Expected worked-example output"); CodeBlock(code: expected) }
            }
            Toggle("I compared my reasoning and edge cases (self-review)", isOn: Binding(
                get: { store.state.reviewedExercises?.contains(exercise.id) == true },
                set: { store.markExerciseReviewed(exercise.id, reviewed: $0) }
            ))
            let runs = (store.state.exerciseRuns ?? []).filter { $0.exerciseID == exercise.id }
            if !runs.isEmpty {
                DisclosureGroup("Previous runs (\(runs.count))") {
                    ForEach(runs) { run in
                        Text("\(run.date.formatted()) · exit \(run.exitCode)").font(.caption)
                        CodeBlock(code: run.source)
                        CodeBlock(code: run.output)
                    }
                }
            }
        }.navigationTitle("Practice").navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if !initialized {
                draft = store.state.exerciseDrafts?[exercise.id] ?? (exercise.kind == "Predict" ? "" : exercise.starter)
                initialized = true
            }
        }
        .onChange(of: draft) { _, value in
            execution.clear()
            if initialized { store.exerciseDraft(value, id: exercise.id) }
        }
        .onDisappear { execution.cancel(showMessage: false); store.save() }
    }
    private func run() {
        let capturedSource = draft, capturedID = exercise.id
        execution.start(language: language, source: capturedSource, stdin: "", base: store.state.serverURL) { [weak store] result in
            store?.recordExerciseRun(id: capturedID, source: capturedSource, result: result)
        }
    }
}

struct QuizPracticeView: View {
    @Environment(LearningStore.self) private var store
    let scopeID, title: String
    let items: [QuizItem]
    @State private var answers: [String: Int] = [:]
    @State private var result: QuizAttempt?
    var body: some View {
        Page {
            Text(title).font(.largeTitle.bold())
            Text("Answer every question before submitting. Scores measure this quiz; they do not mark code problems or projects complete.").foregroundStyle(Palette.muted)
            ForEach(items) { item in
                Panel {
                    Text(item.question).font(.headline).textSelection(.enabled)
                    if let code = item.code { CodeBlock(code: code) }
                    ForEach(Array(item.options.enumerated()), id: \.offset) { index, option in
                        Button {
                            answers[item.id] = index
                        } label: {
                            HStack(alignment: .top) {
                                Image(systemName: answers[item.id] == index ? "largecircle.fill.circle" : "circle")
                                Text(option).multilineTextAlignment(.leading)
                            }.frame(maxWidth: .infinity, alignment: .leading).padding(8)
                        }.disabled(result != nil)
                    }
                    if result != nil { Text("Answer: \(item.options[item.answerIndex])\n\(item.explanation)").textSelection(.enabled) }
                }
            }
            if let result {
                Text("\(result.correct) / \(result.questionIDs.count) correct").font(.title2.bold())
                let missed = items.filter { answers[$0.id] != $0.answerIndex }
                ForEach(missed) { item in
                    if let lesson = store.curriculum.lessons.first(where: { ($0.quiz ?? []).contains { $0.id == item.id } }), let track = store.track(lesson.trackID) {
                        NavigationLink("Revisit: \(lesson.title)") { LessonView(lesson: lesson, track: track) }
                    }
                }
                Button("Try a new attempt") { self.result = nil; answers = [:] }
            } else {
                ActionButton(title: "Submit quiz", icon: "checkmark") {
                    result = store.recordQuiz(scopeID: scopeID, items: items, answers: answers)
                }.disabled(items.isEmpty || items.contains { answers[$0.id] == nil })
            }
            let attempts = (store.state.quizAttempts ?? []).filter { $0.scopeID == scopeID }
            if !attempts.isEmpty {
                DisclosureGroup("Saved scores") {
                    ForEach(attempts) { attempt in Text("\(attempt.date.formatted()) · \(attempt.correct)/\(attempt.questionIDs.count)") }
                }
            }
        }.navigationTitle("Quiz").navigationBarTitleDisplayMode(.inline)
    }
}

struct PracticeLibraryView: View {
    @Environment(LearningStore.self) private var store
    @State private var query = ""
    @State private var standard = 0
    @State private var difficulty = "All"
    @State private var source = "All"
    @State private var status = "All"
    @State private var mode = 0
    private var attempted: Set<String> { Set((store.state.practiceAttempts ?? []).map(\.problemID)) }
    private var problems: [PracticeProblem] {
        (store.curriculum.problems ?? []).filter {
            $0.matches(query: query, standard: standard == 0 ? nil : standard,
                       difficulty: difficulty == "All" ? nil : difficulty,
                       source: source == "All" ? nil : source,
                       status: status == "All" ? nil : status, attempted: attempted.contains($0.id))
        }
    }
    private var quizzes: [PracticeQuiz] {
        (store.curriculum.quizzes ?? []).filter { query.isEmpty || $0.title.localizedCaseInsensitiveContains(query) }
    }
    var body: some View {
        Page {
            Text("Practice C++").font(.largeTitle.bold())
            Text("Explain, predict, debug, and build. Everything here is available offline; code execution uses your optional server.").foregroundStyle(Palette.muted)
            Picker("Practice mode", selection: $mode) { Text("Problems").tag(0); Text("Quizzes").tag(1) }.pickerStyle(.segmented)
            if mode == 0 {
                filters
                Text("\(problems.count) problems · attempts are self-assessed").font(.caption).foregroundStyle(Palette.muted)
                if problems.isEmpty { ContentUnavailableView.search(text: query) }
                LazyVStack(spacing: 12) {
                    ForEach(problems) { problem in
                        NavigationLink { PracticeProblemView(problem: problem) } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(problem.title).font(.headline)
                                Text("C++\(problem.standard) · \(problem.difficulty) · \(problem.kind)").font(.caption).foregroundStyle(Palette.muted)
                                Text(problem.topics.joined(separator: " · ")).font(.caption).foregroundStyle(Palette.mint)
                                if attempted.contains(problem.id) { Label("Self-reviewed attempt saved", systemImage: "pencil.and.list.clipboard").font(.caption) }
                            }.frame(maxWidth: .infinity, alignment: .leading).padding(16).background(Palette.panel, in: RoundedRectangle(cornerRadius: 16))
                        }.buttonStyle(.plain)
                    }
                }
            } else {
                Text("Quizzes score objective questions. Scores guide revision and never lock lessons.").foregroundStyle(Palette.muted)
                LazyVStack(spacing: 12) {
                    ForEach(quizzes) { quiz in QuizEntryView(quiz: quiz) }
                }
                if quizzes.isEmpty { ContentUnavailableView.search(text: query) }
            }
        }.navigationTitle("C++ practice").navigationBarTitleDisplayMode(.inline)
        .searchable(text: $query, prompt: "Topic, problem, difficulty, or source")
    }
    private var filters: some View {
        VStack(alignment: .leading) {
            LabeledContent("Standard") { Picker("Standard", selection: $standard) {
                Text("All standards").tag(0)
                ForEach([14, 17, 20, 23, 26], id: \.self) { Text("C++\($0)").tag($0) }
            }.labelsHidden() }
            LabeledContent("Difficulty") { Picker("Difficulty", selection: $difficulty) {
                ForEach(["All", "Beginner", "Intermediate", "Advanced", "Expert"], id: \.self) { Text($0).tag($0) }
            }.labelsHidden() }
            LabeledContent("Source") { Picker("Source", selection: $source) {
                Text("All sources").tag("All")
                ForEach(store.curriculum.courses.filter { $0.trackIDs.contains("cpp") && $0.kind != "Language guide" }) { Text($0.title).tag($0.id) }
            }.labelsHidden() }
            LabeledContent("Status") { Picker("Status", selection: $status) { ForEach(["All", "Unattempted", "Attempted"], id: \.self) { Text($0).tag($0) } }.labelsHidden() }
        }.pickerStyle(.menu).tint(Palette.mint)
    }
}

struct LessonRequirementsView: View {
    @Environment(LearningStore.self) private var store
    let requirements: LessonRequirements
    var body: some View {
        Panel {
            Label("C++\(requirements.standard) · \(requirements.difficulty)", systemImage: "wrench.and.screwdriver").font(.headline)
            Text(requirements.support).font(.subheadline).foregroundStyle(Palette.muted)
            Text(requirements.compileCommand).font(.system(.caption, design: .monospaced)).textSelection(.enabled)
            ForEach(requirements.prerequisiteLessonIDs, id: \.self) { id in
                if let lesson = store.curriculum.lessons.first(where: { $0.id == id }), let track = store.track(lesson.trackID) {
                    NavigationLink("Suggested prerequisite: " + lesson.title) { LessonView(lesson: lesson, track: track) }.font(.caption)
                }
            }
        }
    }
}

struct PracticeProblemView: View {
    @Environment(LearningStore.self) private var store
    let problem: PracticeProblem
    @State private var response = ""
    @State private var hintCount = 0
    @State private var revealed = false
    @State private var loaded = false
    private var lesson: Lesson? { store.curriculum.lessons.first { $0.id == problem.lessonID } }
    var body: some View {
        Page {
            SectionLabel(title: "C++\(problem.standard) · \(problem.kind) · \(problem.difficulty)")
            Text(problem.title).font(.largeTitle.bold())
            Text(problem.prompt).lineSpacing(5)
            if let requirements = lesson?.requirements { LessonRequirementsView(requirements: requirements) }
            if !problem.starter.isEmpty { CodeBlock(code: problem.starter) }
            StudyNoteEditor(note: $response, title: "Your solution and reasoning", prompt: "Write code or explain the invariant, edge cases, and tradeoffs before revealing an answer.")
            ForEach(Array(problem.hints.prefix(hintCount).enumerated()), id: \.offset) { _, hint in Text(hint).foregroundStyle(Palette.muted) }
            if hintCount < problem.hints.count { Button("Reveal next hint") { hintCount += 1 } }
            Button(revealed ? "Hide worked answer" : "Reveal worked answer") { revealed.toggle() }
            if revealed {
                Text(problem.explanation).lineSpacing(5).textSelection(.enabled)
                if !problem.solution.isEmpty { CodeBlock(code: problem.solution) }
                Text("Review your solution").font(.headline)
                ForEach(problem.rubric, id: \.self) { Text("• " + $0) }
                Text("Edge cases: " + problem.edgeCases.joined(separator: "; ")).font(.subheadline)
                Text(problem.complexity).font(.subheadline).foregroundStyle(Palette.muted)
                Button("Save attempt · needs more practice") { store.recordPractice(response, problemID: problem.id, assessment: "Needs more practice") }.disabled(response.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                Button("Save attempt · explained independently") { store.recordPractice(response, problemID: problem.id, assessment: "Explained independently (self-assessed)") }.disabled(response.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            if let lesson, let track = store.track(lesson.trackID) { NavigationLink("Review the lesson and recall cards") { LessonView(lesson: lesson, track: track) } }
            let attempts = (store.state.practiceAttempts ?? []).filter { $0.problemID == problem.id }
            Text("\(attempts.count) saved self-assessed attempts. Running code is separate from checking correctness.").font(.caption).foregroundStyle(Palette.muted)
            ForEach(attempts.prefix(3)) { attempt in
                DisclosureGroup(attempt.date.formatted() + " · " + attempt.selfAssessment) { Text(attempt.response).textSelection(.enabled) }
            }
        }.navigationTitle("Problem").navigationBarTitleDisplayMode(.inline)
        .onAppear { if !loaded { response = store.state.problemDrafts?[problem.id] ?? ""; loaded = true } }
        .onChange(of: response) { _, value in if loaded { store.practiceDraft(value, problemID: problem.id) } }
        .onDisappear { store.save() }
    }
}

struct QuizEntryView: View {
    @Environment(LearningStore.self) private var store
    let quiz: PracticeQuiz
    @State private var timed = false
    var body: some View {
        Panel {
            Text(quiz.title).font(.headline)
            Text("\(quiz.questionIDs.count) questions · \(quiz.passPercent)% revision target · all lessons stay open").font(.caption).foregroundStyle(Palette.muted)
            if quiz.durationSeconds > 0 { Toggle("\(quiz.durationSeconds / 60)-minute timer", isOn: $timed) }
            NavigationLink("Start or resume") { QuizSessionView(quiz: quiz, timed: timed) }
            ForEach((store.state.quizSessions ?? []).filter { $0.quizID == quiz.id && $0.finishedAt != nil }.prefix(3)) { session in
                NavigationLink("\(session.startedAt.formatted()) · \(session.percent(in: store.curriculum.problems ?? []))%") {
                    QuizSessionView(quiz: quiz, timed: false, existingID: session.id)
                }.font(.caption)
            }
        }
    }
}

struct QuizSessionView: View {
    @Environment(LearningStore.self) private var store
    @Environment(\.scenePhase) private var scenePhase
    let quiz: PracticeQuiz
    let timed: Bool
    var existingID: UUID?
    @State private var sessionID: UUID?
    @State private var questionIndex = 0
    var body: some View {
        Page {
            Text(quiz.title).font(.largeTitle.bold())
            if let session = store.quizSession(sessionID) {
                if session.finishedAt != nil {
                    Text("\(session.correctCount(in: store.curriculum.problems ?? []))/\(session.questionIDs.count) · \(session.percent(in: store.curriculum.problems ?? []))%").font(.title.bold())
                    Text(session.percent(in: store.curriculum.problems ?? []) >= quiz.passPercent ? "Revision target reached. Apply these ideas in code and revisit them later." : "Review the explanations below and revisit the linked lessons. All stages remain available.").foregroundStyle(Palette.muted)
                    if let stage = session.suggestedRevisionStage(in: store.curriculum),
                       let guide = store.curriculum.courses.first(where: { $0.id == "guide.cpp" }) {
                        NavigationLink("Suggested revision: " + stage.title) { SourceChapterView(chapter: stage, course: guide) }
                    }
                } else if let deadline = session.deadline {
                    TimelineView(.periodic(from: .now, by: 1)) { context in
                        Text("\(max(0, Int(ceil(deadline.timeIntervalSince(context.date))))) seconds remaining").monospacedDigit()
                            .onChange(of: context.date) { _, date in store.expireQuiz(session.id, now: date) }
                    }
                    Text("The timer continues while the app is closed or in the background.").font(.caption).foregroundStyle(Palette.muted)
                }
                if session.finishedAt == nil {
                    Text("Question \(questionIndex + 1) of \(session.questionIDs.count) · \(session.responses.count) answered").font(.caption).foregroundStyle(Palette.muted)
                }
                let visible = session.finishedAt == nil ? Array(session.questionIDs.dropFirst(questionIndex).prefix(1)) : session.questionIDs
                ForEach(visible, id: \.self) { id in
                    if let problem = store.curriculum.problems?.first(where: { $0.id == id }) {
                        QuizQuestionView(problem: problem, session: session)
                    }
                }
                if session.finishedAt == nil {
                    HStack {
                        Button("Previous") { questionIndex -= 1 }.disabled(questionIndex == 0)
                        Spacer()
                        Button("Next") { questionIndex += 1 }.disabled(questionIndex >= session.questionIDs.count - 1)
                    }
                    Button("Submit quiz") { store.finishQuiz(session.id) }.buttonStyle(.borderedProminent)
                }
            }
        }.navigationTitle("Quiz").navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if sessionID == nil { sessionID = existingID ?? store.startQuiz(quiz, timed: timed) }
            if let sessionID {
                store.expireQuiz(sessionID)
                if let session = store.quizSession(sessionID) {
                    questionIndex = session.questionIDs.firstIndex { session.responses[$0] == nil } ?? 0
                }
            }
        }
        .onChange(of: scenePhase) { _, phase in if phase == .active, let sessionID { store.expireQuiz(sessionID) } }
        .onDisappear { store.save() }
    }
}

private struct QuizQuestionView: View {
    @Environment(LearningStore.self) private var store
    let problem: PracticeProblem
    let session: QuizSession
    var body: some View {
        Panel {
            Text(problem.question).font(.headline)
            if !problem.starter.isEmpty { CodeBlock(code: problem.starter) }
            ForEach(Array(problem.options.enumerated()), id: \.offset) { index, option in
                Button {
                    store.answerQuiz(session.id, questionID: problem.id, option: index)
                } label: {
                    HStack { Text(option).multilineTextAlignment(.leading); Spacer(); if session.responses[problem.id] == index { Image(systemName: "checkmark.circle.fill") } }
                        .frame(maxWidth: .infinity, alignment: .leading)
                }.buttonStyle(.bordered).disabled(session.finishedAt != nil)
            }
            if session.finishedAt != nil {
                Text("Answer: " + problem.options[problem.answerIndex]).foregroundStyle(Palette.mint)
                Text(problem.quizExplanation).font(.subheadline)
                NavigationLink("Review this topic") { PracticeProblemView(problem: problem) }
            }
        }
    }
}

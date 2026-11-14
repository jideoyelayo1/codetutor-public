import SwiftUI

struct TodayView: View {
    @Environment(LearningStore.self) private var store
    @Binding var selection: Int
    var body: some View {
        Page {
            VStack(alignment: .leading, spacing: 10) {
                SectionLabel(title: Date.now.formatted(.dateTime.weekday(.wide).month().day()))
                Text("Keep what you know.\nBuild what’s next.").font(.largeTitle.bold()).tracking(-1)
                Text("A little recall. A new idea. Code that makes it stick.").foregroundStyle(Palette.muted)
            }
            Panel {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 8) {
                        SectionLabel(title: "Your daily session")
                        Text("\(store.state.dailyMinutes) minutes for future you").font(.title2.bold())
                        Text("\(store.reviewQueue().count) cards ready · 1 lesson to explore").font(.subheadline).foregroundStyle(Palette.muted)
                    }
                    Spacer()
                    Image(systemName: "sparkle").font(.largeTitle).foregroundStyle(Palette.mint)
                }
                HStack(spacing: 18) {
                    ZStack {
                        Circle().stroke(Palette.mint.opacity(0.1), lineWidth: 6)
                        Circle().trim(from: 0, to: min(1, Double(store.reviewsToday())/Double(max(1,store.state.dailyReviewGoal)))).stroke(Palette.mint, style: StrokeStyle(lineWidth: 6, lineCap: .round)).rotationEffect(.degrees(-90))
                        Text("\(store.reviewsToday())").font(.title.bold().monospacedDigit())
                    }.frame(width: 62, height: 62).accessibilityLabel("\(store.reviewsToday()) of \(store.state.dailyReviewGoal) daily reviews")
                    VStack(alignment: .leading, spacing: 4) { Text("\(store.state.dailyReviewGoal) reviews is your goal").font(.headline); Text("Recall before you reveal.").font(.subheadline).foregroundStyle(Palette.muted) }
                }
                ActionButton(title: "Start recall", icon: "arrow.right") { selection = 2 }
            }
            HStack {
                metric("\(store.streak())", "day streak", "flame")
                metric("\(store.state.completedLessons.count)", "lessons completed", "checkmark.circle")
                metric(store.recallRate.map { "\(Int($0*100))%" } ?? "—", "recent recall", "brain")
            }
            SectionLabel(title: "Your next language")
            ForEach(store.curriculum.tracks.filter { $0.isNew && store.state.enabledTracks.contains($0.id) }) { track in
                NavigationLink { TrackDetailView(track: track) } label: { TrackRow(track: track) }.buttonStyle(.plain)
            }
            Panel {
                Label("Same idea, new language", systemImage: "arrow.triangle.branch").font(.headline).foregroundStyle(Palette.mint)
                Text("C++ lifetime → Rust ownership\nPython functions → OCaml pattern matching\nTyped functions → Lean proof terms").font(.subheadline).lineSpacing(6)
                Button("Explore learning paths") { selection = 1 }.font(.subheadline.weight(.semibold))
            }
        }.navigationTitle("Coding Teacher").navigationBarTitleDisplayMode(.inline)
    }
    private func metric(_ value: String, _ label: String, _ icon: String) -> some View {
        VStack(alignment: .leading, spacing: 6) { Image(systemName: icon).foregroundStyle(Palette.mint); Text(value).font(.title2.bold()); Text(label).font(.caption).foregroundStyle(Palette.muted) }.frame(maxWidth: .infinity, alignment: .leading)
    }
}
struct TrackRow: View {
    @Environment(LearningStore.self) private var store
    let track: LearningTrack
    var body: some View {
        HStack(spacing: 14) {
            TrackBadge(track: track)
            VStack(alignment: .leading, spacing: 6) {
                HStack { Text(track.name).font(.headline); Spacer(); Text("\(Int(store.completion(for:track.id)*100))%").font(.caption.monospacedDigit()).foregroundStyle(Palette.muted) }
                Text(track.subtitle).font(.caption).foregroundStyle(Palette.muted).fixedSize(horizontal: false, vertical: true)
                ProgressView(value: store.completion(for: track.id)).tint(track.tint)
            }
            Image(systemName: "chevron.right").font(.caption).foregroundStyle(Palette.muted)
        }.padding(16).background(Palette.panel, in: RoundedRectangle(cornerRadius: 18))
    }
}
struct LearnView: View {
    @Environment(LearningStore.self) private var store
    @State private var query = ""
    @State private var mode = 0
    var body: some View {
        Page {
            Text("Build on your experience.").font(.largeTitle.bold())
            Text("Lessons pair concepts with worked examples, practice, checkpoints, and recall cards.").foregroundStyle(Palette.muted)
            NavigationLink("Python & ML problem bank") { PythonPracticeBank() }
            NavigationLink("C++ problems and quizzes") { PracticeLibraryView() }
            Picker("Learning", selection: $mode) { Text("Daily paths").tag(0); Text("Sources").tag(1); Text("Guides").tag(2) }.pickerStyle(.segmented)
            if mode == 1 { SourceCourseList(query: query) }
            else if mode == 2 { SourceCourseList(query: query, guideKind: SourceCourse.languageGuide) } else {
            ForEach(["learn", "retain"], id: \.self) { mode in
                SectionLabel(title: mode == "learn" ? "Learn something new" : "Keep your edge")
                ForEach(store.tracks(mode: mode, matching: query)) { track in
                    NavigationLink { TrackDetailView(track: track) } label: { TrackRow(track: track) }.buttonStyle(.plain)
                }
            }
            }
        }.navigationTitle("Learning paths").navigationBarTitleDisplayMode(.inline).searchable(text: $query, prompt: "Find a language or library")
    }
}
struct TrackDetailView: View {
    @Environment(LearningStore.self) private var store
    let track: LearningTrack
    private var lessons: [Lesson] { store.lessons(for: track.id) }
    private var cardCount: Int { let ids = Set(lessons.map(\.id)); return store.curriculum.cards.filter { ids.contains($0.lessonID) }.count }
    var body: some View {
        Page {
            TrackBadge(track: track)
            Text(track.name).font(.largeTitle.bold())
            Text(track.subtitle).font(.title3).foregroundStyle(Palette.muted)
            HStack { Label("\(lessons.count) lessons", systemImage: "book"); Spacer(); Label("\(cardCount) recall cards", systemImage: "rectangle.on.rectangle") }.font(.caption).foregroundStyle(Palette.muted)
            ProgressView(value: store.completion(for: track.id)).tint(track.tint)
            if let guide = store.curriculum.courses.first(where: { $0.isGuide && $0.trackIDs.contains(track.id) }) {
                NavigationLink("Study the \(guide.kind.lowercased())") { Page { SourceCourseList(trackID: track.id, guideKind: guide.kind) }.navigationTitle(guide.kind + "s") }
            }
            SectionLabel(title: "The path")
            ForEach(lessons) { lesson in
                NavigationLink { LessonView(lesson: lesson, track: track) } label: {
                    HStack(spacing: 16) {
                        Text(store.state.completedLessons.contains(lesson.id) ? "✓" : "\(lesson.order)").font(.title3.bold().monospacedDigit()).foregroundStyle(track.tint).frame(width: 34)
                        VStack(alignment: .leading, spacing: 6) { Text(lesson.title).font(.headline); Text(lesson.summary).font(.caption).foregroundStyle(Palette.muted); Text("\(lesson.minutes) min · checkpoint + practice").font(.caption2).foregroundStyle(Palette.muted) }
                        Spacer(); Image(systemName: "chevron.right").font(.caption)
                    }.padding(18).background(Palette.panel, in: RoundedRectangle(cornerRadius: 18))
                }.buttonStyle(.plain)
            }
            if store.curriculum.courses.contains(where: { !$0.isGuide && $0.trackIDs.contains(track.id) }) {
                NavigationLink("Study the source courses") { Page { SourceCourseList(trackID: track.id) }.navigationTitle("Source courses") }
            }
            SectionLabel(title: "Go deeper")
            ForEach(track.resources) { resource in
                Link(destination: URL(string: resource.url)!) { HStack { VStack(alignment: .leading, spacing: 4) { Text(resource.title); Text(resource.kind).font(.caption).foregroundStyle(Palette.muted) }; Spacer(); Image(systemName: "arrow.up.right") }.padding(.vertical, 7) }
            }
        }.navigationTitle(track.name).navigationBarTitleDisplayMode(.inline)
    }
}
/// Explains why completion is still locked when the main checkpoint is right but extra questions are not.
struct ExtraQuizHint: View {
    let remaining: Int
    var body: some View {
        Text(remaining == 1 ? "Answer 1 more extra question correctly to unlock completion." : "Answer \(remaining) more extra questions correctly to unlock completion.")
            .font(.caption).foregroundStyle(Palette.muted)
    }
}
struct LessonView: View {
    @Environment(LearningStore.self) private var store
    let lesson: Lesson
    let track: LearningTrack
    @State private var selected: Int?
    @State private var passed = false
    @State private var extraAnswers: [Int: Int] = [:]
    @State private var showSolution = false
    @State private var practice = false
    @State private var studyNote = ""
    var body: some View {
        Page {
            SectionLabel(title: lesson.id.hasPrefix("guide.") || lesson.id.hasPrefix("concept.") ? "\(track.name) · Guided lesson" : lesson.isSourceStudy == true ? "\(track.name) · Source study" : "\(track.name) · Lesson \(lesson.order)")
            Text(lesson.title).font(.largeTitle.bold())
            if let requirements = lesson.requirements { LessonRequirementsView(requirements: requirements) }
            if lesson.isSourceStudy != true { Text(lesson.summary).font(.title3).foregroundStyle(Palette.muted) }
            if let objectives = lesson.learningObjectives {
                Panel {
                    SectionLabel(title: "Learning objectives")
                    ForEach(objectives, id: \.self) { Text($0) }
                }
            }
            if let ids = lesson.prerequisiteIDs, !ids.isEmpty {
                DisclosureGroup("Recommended prerequisites") {
                    ForEach(ids, id: \.self) { id in
                        if let previous = store.curriculum.lessons.first(where: { $0.id == id }), let previousTrack = store.track(previous.trackID) {
                            NavigationLink(previous.title) { LessonView(lesson: previous, track: previousTrack) }
                        }
                    }
                }
            }
            ForEach(lesson.body, id: \.self) { paragraph in Text(lesson.paragraphText(paragraph)).font(.body).lineSpacing(5) }
            if let worked = lesson.workedExample {
                Panel { SectionLabel(title: "Worked example"); Text(worked).lineSpacing(5) }
            }
            if !lesson.code.isEmpty {
                SectionLabel(title: "Try the idea")
                CodeBlock(code: lesson.code)
            }
            if let files = lesson.projectFiles {
                SectionLabel(title: "Complete project")
                Text(lesson.projectInstructions ?? "Create these files with the displayed relative paths. Run cargo run --offline -p guide-demo with Rust 1.99. This workspace needs Cargo; the single-file Lab does not build projects.").foregroundStyle(Palette.muted).textSelection(.enabled)
                ForEach(files) { file in
                    DisclosureGroup(file.path) { CodeBlock(code: file.content) }
                }
            }
            if let exercises = lesson.exercises {
                ForEach(exercises) { exercise in
                    NavigationLink(exercise.title) { PracticeExerciseView(exercise: exercise, lesson: lesson) }
                }
            }
            if let quiz = lesson.quiz, !quiz.isEmpty {
                NavigationLink("Take the lesson quiz (\(quiz.count) questions)") { QuizPracticeView(scopeID: lesson.id, title: lesson.title, items: quiz) }
            }
            Panel {
                Label("Make it yours", systemImage: lesson.code.isEmpty ? "pencil" : "terminal").font(.headline).foregroundStyle(track.tint)
                Text(lesson.challenge)
                if !lesson.code.isEmpty {
                    if track.language.supportsExecution && (lesson.requirements?.serverDefaultCompatible ?? true) {
                        ActionButton(title: lesson.requirements == nil ? "Open in the lab" : "Run with server defaults", icon: "play") { practice = true }
                        if lesson.requirements != nil { Text("The server chooses compiler flags. This run does not verify the lesson's stated standard.").font(.caption).foregroundStyle(Palette.muted) }
                    }
                    else { Text("Predict the output and compare your reasoning with the solution.").font(.caption).foregroundStyle(Palette.muted) }
                }
                Button(showSolution ? "Hide one solution" : "Show one solution") { showSolution.toggle() }.font(.subheadline)
                if showSolution {
                    if let answer = lesson.practiceAnswer { Text(answer).lineSpacing(5).textSelection(.enabled) }
                    if !lesson.solution.isEmpty { CodeBlock(code: lesson.solution) }
                    if let files = lesson.projectSolutionFiles {
                        Text("Replace the listed files to apply this worked solution. Keep the other project files.").font(.caption).foregroundStyle(Palette.muted)
                        ForEach(files) { file in
                            DisclosureGroup(file.path) { CodeBlock(code: file.content) }
                        }
                    }
                }
            }
            if lesson.isSourceStudy == true { StudyNoteEditor(note: $studyNote, title: "Your practice answer", prompt: "Work through the challenge before revealing the answer. Record your reasoning and any edge cases.") }
            Panel {
                SectionLabel(title: "Checkpoint")
                Text(lesson.question).font(.headline)
                ForEach(Array(lesson.options.enumerated()), id: \.offset) { index, option in
                    Button {
                        selected = index
                        passed = index == lesson.answerIndex
                    } label: {
                        HStack { Text(option).multilineTextAlignment(.leading); Spacer(); if selected == index { Image(systemName: passed ? "checkmark.circle.fill" : "xmark.circle.fill") } }.frame(maxWidth: .infinity, alignment: .leading).padding(14).background(selected == index ? (passed ? Color.mint.opacity(0.15) : Color.red.opacity(0.15)) : Color.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 12))
                    }.buttonStyle(.plain)
                }
                if selected != nil { Text(passed ? lesson.explanation : "Try again. Explain why each alternative would or would not work.").font(.subheadline).foregroundStyle(Palette.muted) }
                ForEach(Array((lesson.extraQuizzes ?? []).enumerated()), id: \.offset) { number, quiz in
                    Divider()
                    Text(quiz.question).font(.headline)
                    ForEach(Array(quiz.options.enumerated()), id: \.offset) { index, option in
                        let chosen = extraAnswers[number] == index
                        Button { extraAnswers[number] = index } label: {
                            HStack { Text(option).multilineTextAlignment(.leading); Spacer(); if chosen { Image(systemName: index == quiz.answerIndex ? "checkmark.circle.fill" : "xmark.circle.fill") } }.frame(maxWidth: .infinity, alignment: .leading).padding(14).background(chosen ? (index == quiz.answerIndex ? Color.mint.opacity(0.15) : Color.red.opacity(0.15)) : Color.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 12))
                        }.buttonStyle(.plain)
                    }
                    if let chosen = extraAnswers[number] { Text(chosen == quiz.answerIndex ? quiz.explanation : "Try again. Explain why each alternative would or would not work.").font(.subheadline).foregroundStyle(Palette.muted) }
                }
                let extrasPassed = (lesson.extraQuizzes ?? []).enumerated().allSatisfy { extraAnswers[$0.offset] == $0.element.answerIndex }
                if passed && !extrasPassed { ExtraQuizHint(remaining: lesson.remainingExtraQuizzes(answers: extraAnswers)) }
                ActionButton(title: store.state.completedLessons.contains(lesson.id) ? "Completed · cards added" : "Complete & add recall cards", icon: "checkmark") { store.complete(lesson) }.disabled(!(passed && extrasPassed) || store.state.completedLessons.contains(lesson.id))
            }
            if let rubric = lesson.rubric {
                Panel {
                    SectionLabel(title: "Project review rubric")
                    ForEach(rubric, id: \.self) { Text($0) }
                    Toggle("I reviewed the project evidence (self-assessed)", isOn: Binding(
                        get: { store.state.reviewedProjects?.contains(lesson.id) == true },
                        set: { store.markProjectReviewed(lesson.id, reviewed: $0) }
                    ))
                }
            }
            if let readings = lesson.reading, !readings.isEmpty { CompanionReadings(readings: readings) }
            Link("Read the source resource ↗", destination: URL(string: lesson.sourceURL)!).font(.subheadline)
        }.navigationBarTitleDisplayMode(.inline)
        .onAppear { studyNote = store.state.studyNotes?[lesson.id] ?? "" }
        .onChange(of: studyNote) { _, value in store.studyNote(value, id: lesson.id) }
        .onDisappear { store.save() }
        .sheet(isPresented: $practice) { NavigationStack { LabView(initialLanguage: track.language, initialSource: lesson.code, exercise: lesson.challenge).toolbar { ToolbarItem(placement: .topBarLeading) { Button("Done") { practice = false } } } } }
    }
}
struct RecallView: View {
    @Environment(LearningStore.self) private var store
    @State private var queue: [RecallCard] = []
    @State private var index = 0
    @State private var revealed = false
    @State private var response = ""
    @State private var initialized = false
    var body: some View {
        Page {
            SectionLabel(title: "Active recall")
            Text("Remember first.\nThen check.").font(.largeTitle.bold())
            if index < queue.count {
                let card = queue[index]
                HStack { Text("\(index+1) / \(queue.count)").font(.caption.monospacedDigit()); Spacer(); Text(store.track(card.trackID)?.name ?? card.trackID).font(.caption.bold()).foregroundStyle(Palette.mint) }
                ProgressView(value: Double(index), total: Double(max(1,queue.count))).tint(Palette.mint)
                Panel {
                    Text(card.prompt).font(.title2.weight(.semibold)).fixedSize(horizontal: false, vertical: true)
                    if !revealed {
                        Text("Say it out loud, or jot down your answer.").font(.caption).foregroundStyle(Palette.muted)
                        TextEditor(text: $response).frame(minHeight: 100).scrollContentBackground(.hidden).padding(8).background(Color.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 12)).accessibilityLabel("Your recalled answer")
                        ActionButton(title: "Reveal answer", icon: "eye") { revealed = true }
                    } else {
                        Divider()
                        Text(card.answer).font(.body).lineSpacing(5).textSelection(.enabled)
                        Text("How well did you remember? Rate recall, not how familiar the answer looks.").font(.caption).foregroundStyle(Palette.muted)
                        LazyVGrid(columns: [GridItem(.flexible()),GridItem(.flexible())], spacing: 10) {
                            ForEach(RecallGrade.allCases) { grade in
                                Button {
                                    if store.review(card, grade: grade) { index += 1; revealed = false; response = "" }
                                } label: { VStack(spacing: 5) { Text(grade.title).font(.headline); Text(store.intervalLabel(for: card, grade: grade)).font(.caption.monospacedDigit()) }.frame(maxWidth: .infinity).padding(14).background(grade.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 12)).foregroundStyle(grade.tint) }.buttonStyle(.plain)
                            }
                        }
                        Link("Reference ↗", destination: URL(string: card.sourceURL)!).font(.caption)
                    }
                }
            } else {
                Panel {
                    Image(systemName: index > 0 ? "checkmark.circle" : "leaf").font(.largeTitle).foregroundStyle(Palette.mint)
                    Text(index > 0 ? "Session complete." : "You’re caught up.").font(.title2.bold())
                    Text(index > 0 ? "Your next reviews are scheduled. Take a new lesson, or come back when a card is due." : "Learn a new concept to add cards. Existing reviews return when they are due.").foregroundStyle(Palette.muted)
                    ActionButton(title: "Check for ready cards", icon: "arrow.clockwise") { restart() }
                }
            }
            if index > 0 && store.canUndo { Button("Undo last rating") { store.undoReview(); index -= 1; revealed = true }.font(.subheadline) }
            Text("Scheduling uses FSRS 6 with a 90% target retention setting. This is a scheduling target, not a measured guarantee.").font(.caption).foregroundStyle(Palette.muted)
        }.navigationTitle("Recall").navigationBarTitleDisplayMode(.inline)
        .onAppear { if !initialized { restart(); initialized = true } }
    }
    private func restart() { queue = store.reviewQueue(); index = 0; revealed = false; response = "" }
}

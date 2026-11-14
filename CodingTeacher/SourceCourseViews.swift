import SwiftUI

struct SourceCourseList: View {
    @Environment(LearningStore.self) private var store
    var query = ""
    var trackID: String?
    // nil lists the supplied source courses; otherwise only guides of this kind.
    var guideKind: String?
    private var guidesOnly: Bool { guideKind != nil }
    private var courses: [SourceCourse] {
        store.curriculum.courses.filter { course in
            (guideKind.map { course.kind == $0 } ?? !course.isGuide) &&
            (trackID.map { course.trackIDs.contains($0) } ?? true) &&
            (query.isEmpty || ([course.title, course.kind] + course.chapters.flatMap { [$0.title] + $0.sections }).joined(separator: " ").localizedCaseInsensitiveContains(query))
        }
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text(guideKind == SourceCourse.conceptGuide ? "Master a book step by step." : guidesOnly ? "Learn a language step by step." : "Learn through your sources.").font(.title2.bold())
            Text(guidesOnly ? "Start with the foundations, then build toward advanced reasoning and complete projects. Practice, checkpoints, and recall accompany each lesson." : "Read or watch each assigned chapter, work through its related lessons, and keep your own notes. Reading and practice progress are tracked separately.").foregroundStyle(Palette.muted)
            if courses.isEmpty { ContentUnavailableView.search(text: query) }
            LazyVStack(spacing: 12) {
                ForEach(courses) { course in
                    NavigationLink { SourceCourseDetailView(course: course) } label: {
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: course.kind.contains("Video") ? "play.rectangle" : "books.vertical").foregroundStyle(Palette.mint)
                            VStack(alignment: .leading, spacing: 6) {
                                Text(course.title).font(.headline)
                                Text("\(course.kind) · \(course.chapters.count) \(guidesOnly ? "stages" : "assignments")").font(.caption).foregroundStyle(Palette.muted)
                                Text("\(readCount(course)) read · \(practiceCount(course))/\(practiceIDs(course).count) practice lessons").font(.caption).foregroundStyle(Palette.mint)
                            }
                            Spacer(minLength: 0)
                            Image(systemName: "chevron.right").font(.caption)
                        }.padding(16).background(Palette.panel, in: RoundedRectangle(cornerRadius: 16))
                    }.buttonStyle(.plain)
                }
            }
        }
    }
    private func readCount(_ course: SourceCourse) -> Int { course.chapters.filter { store.state.readSourceChapters?.contains($0.id) == true }.count }
    private func practiceIDs(_ course: SourceCourse) -> Set<String> { Set(course.chapters.flatMap(\.lessonIDs)) }
    private func practiceCount(_ course: SourceCourse) -> Int { practiceIDs(course).intersection(store.state.completedLessons).count }
}

struct SourceCourseDetailView: View {
    @Environment(LearningStore.self) private var store
    @Environment(\.offlineReferences) private var references
    let course: SourceCourse
    @State private var query = ""
    private var chapters: [SourceChapter] {
        course.chapters.filter { query.isEmpty || ([$0.title] + $0.sections).joined(separator: " ").localizedCaseInsensitiveContains(query) }
    }
    var body: some View {
        Page {
            SectionLabel(title: course.kind)
            Text(course.title).font(.largeTitle.bold())
            Text(course.edition).font(.caption).foregroundStyle(Palette.muted)
            Text(course.scope).foregroundStyle(Palette.muted)
            if course.id == "guide.python-ml" {
                NavigationLink("Starting-point diagnostic (\(store.curriculum.pythonDiagnostic.count) questions)") {
                    QuizPracticeView(scopeID: course.id+".diagnostic", title: "Find topics to revisit", items: store.curriculum.pythonDiagnostic)
                }
                Text("Stage assessments include earlier-stage questions. A diagnostic score recommends review; it never marks lessons or problems complete.").font(.caption).foregroundStyle(Palette.muted)
            }

            if course.id == "guide.cpp" { NavigationLink("C++ problems, placement, and stage quizzes") { PracticeLibraryView() } }
            Text("Shared concepts reuse the same practice lesson and recall cards across courses.").font(.caption).foregroundStyle(Palette.muted)
            if let address = course.sourceURL, let page = references.page(source: address) {
                NavigationLink("Read the source offline") { ReferenceReaderView(page: page, anchor: URL(string: address)?.fragment) }
            } else if let address = course.sourceURL, let url = URL(string: address) { Link("Open the source ↗", destination: url) }
            LazyVStack(spacing: 12) {
                ForEach(chapters) { chapter in
                    NavigationLink { SourceChapterView(chapter: chapter, course: course) } label: {
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: store.state.readSourceChapters?.contains(chapter.id) == true ? "book.closed.fill" : "book").foregroundStyle(Palette.mint)
                            VStack(alignment: .leading, spacing: 6) {
                                Text(chapter.title).font(.headline)
                                let done = chapter.lessonIDs.filter { store.state.completedLessons.contains($0) }.count
                                Text("\(done)/\(chapter.lessonIDs.count) related practice lessons complete").font(.caption).foregroundStyle(Palette.muted)
                                if !chapter.sections.isEmpty { Text("\(chapter.sections.count) source sections").font(.caption2).foregroundStyle(Palette.muted) }
                            }
                            Spacer(minLength: 0); Image(systemName: "chevron.right").font(.caption)
                        }.padding(16).background(Palette.panel, in: RoundedRectangle(cornerRadius: 16))
                    }.buttonStyle(.plain)
                }
            }
        }.navigationTitle(course.kind == "Language guide" ? "Language guide" : "Source course").navigationBarTitleDisplayMode(.inline)
        .searchable(text: $query, prompt: "Find a chapter or section")
    }
}

struct SourceChapterView: View {
    @Environment(LearningStore.self) private var store
    let chapter: SourceChapter
    let course: SourceCourse
    @State private var note = ""
    private var lessons: [Lesson] { chapter.lessonIDs.compactMap { id in store.curriculum.lessons.first { $0.id == id } } }
    var body: some View {
        Page {
            SectionLabel(title: course.title)
            Text(chapter.title).font(.largeTitle.bold())
            Text(chapter.note).foregroundStyle(Palette.muted)
            CompanionReadings(readings: [chapter.reading])
            Toggle("I have read or watched this assignment", isOn: Binding(
                get: { store.state.readSourceChapters?.contains(chapter.id) == true },
                set: { store.markSourceRead(chapter.id, read: $0) }
            )).tint(Palette.mint)
            if !chapter.sections.isEmpty {
                DisclosureGroup("Source section checklist") {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(Array(chapter.sections.enumerated()), id: \.offset) { _, title in Text(title).font(.subheadline) }
                    }.frame(maxWidth: .infinity, alignment: .leading).padding(.top, 12)
                }
            }
            let stageQuestions = store.curriculum.assessment(for: chapter, course: course)
            if !stageQuestions.isEmpty {
                NavigationLink("Stage assessment (\(stageQuestions.count) questions)") {
                    QuizPracticeView(scopeID: chapter.id, title: chapter.title, items: stageQuestions)
                }
            }
            SectionLabel(title: "Apply and recall")
            ForEach(lessons) { lesson in
                if let track = store.track(lesson.trackID) {
                    NavigationLink { LessonView(lesson: lesson, track: track) } label: {
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: store.state.completedLessons.contains(lesson.id) ? "checkmark.circle.fill" : "circle").foregroundStyle(Palette.mint)
                            VStack(alignment: .leading, spacing: 6) {
                                Text(lesson.title).font(.headline)
                                Text("Worked example · practice · checkpoint · recall").font(.caption).foregroundStyle(Palette.muted)
                            }
                            Spacer(minLength: 0); Image(systemName: "chevron.right").font(.caption)
                        }.padding(16).background(Palette.panel, in: RoundedRectangle(cornerRadius: 16))
                    }.buttonStyle(.plain)
                }
            }
            let additional = store.curriculum.additionalSourcePractice(for: chapter, course: course)
            if !additional.isEmpty {
                SectionLabel(title: "More practice from this chapter")
                Text("These lessons focus on selected concepts. Other chapter sections and exercises still need practice.").font(.caption).foregroundStyle(Palette.muted)
                ForEach(additional) { lesson in
                    if let track = store.track(lesson.trackID) {
                        NavigationLink { LessonView(lesson: lesson, track: track) } label: {
                            Label(lesson.title, systemImage: store.state.completedLessons.contains(lesson.id) ? "checkmark.circle.fill" : "circle")
                        }
                    }
                }
            }
            StudyNoteEditor(note: $note, title: "Chapter notes", prompt: "Explain the chapter's main ideas in your own words. Record unanswered questions and one example that connects to your code.")
        }.navigationTitle("Chapter study").navigationBarTitleDisplayMode(.inline)
        .onAppear { note = store.state.studyNotes?[chapter.id] ?? "" }
        .onChange(of: note) { _, value in store.studyNote(value, id: chapter.id) }
        .onDisappear { store.save() }
    }
}

struct StudyNoteEditor: View {
    @Binding var note: String
    let title, prompt: String
    var body: some View {
        Panel {
            SectionLabel(title: title)
            Text(prompt).font(.subheadline).foregroundStyle(Palette.muted)
            TextEditor(text: $note).frame(minHeight: 150).scrollContentBackground(.hidden)
                .padding(8).background(Color.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 12))
                .accessibilityLabel(title)
            Text("Saved locally and included in progress backups.").font(.caption).foregroundStyle(Palette.muted)
        }
    }
}

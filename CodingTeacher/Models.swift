import Foundation
import SwiftUI
import FSRS

struct Curriculum: Codable {
    let schemaVersion: Int
    let tracks: [LearningTrack]
    let lessons: [Lesson]
    let cards: [RecallCard]
    let books: [BookSource]?
    let sourceCourses: [SourceCourse]?
    var problems: [PracticeProblem]?
    var quizzes: [PracticeQuiz]?
    var courses: [SourceCourse] { sourceCourses ?? [] }
    var bookCatalog: [BookSource] { books ?? [] }
    static func load(bundle: Bundle = .main) throws -> Curriculum {
        guard let url = bundle.url(forResource: "curriculum", withExtension: "json") else {
            throw CocoaError(.fileNoSuchFile)
        }
        let content = try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
        guard content.schemaVersion == 1 else { throw CocoaError(.coderReadCorrupt) }
        return content
    }
}
struct LearningTrack: Codable, Identifiable, Hashable {
    let id, name, mode, subtitle, symbol, color: String
    let resources: [LearningResource]
    // Optional so curriculum files written before concept tracks still decode.
    let subject: String?
    private let languageID: String?
    enum CodingKeys: String, CodingKey { case id, name, mode, subtitle, symbol, color, resources, subject, languageID = "language" }
    var isNew: Bool { mode == "learn" }
    var isConcept: Bool { mode == "concept" }
    var tint: Color { Color(hex: color) }
    var language: CodeLanguage {
        if let languageID, let explicit = CodeLanguage(rawValue: languageID) { return explicit }
        switch id {
        case "numpy", "pandas", "sklearn", "pytorch": return .pythonML
        default: return CodeLanguage(rawValue: id) ?? .python
        }
    }
}
struct LearningResource: Codable, Hashable, Identifiable {
    let title, url, kind: String
    var id: String { url }
}
struct ExtraQuiz: Codable, Hashable {
    let question: String
    let options: [String]
    let answerIndex: Int
    let explanation: String
}
struct Lesson: Codable, Identifiable, Hashable {
    let id, trackID, title, summary: String
    let body: [String]
    let code, challenge, solution, question: String
    let options: [String]
    let answerIndex: Int
    let explanation: String
    let minutes, order: Int
    let sourceURL: String
    let reading: [ReadingAssignment]?
    let isSourceStudy: Bool?
    let workedExample, practiceAnswer: String?
    let extraQuizzes: [ExtraQuiz]?
    let learningObjectives, prerequisiteIDs, rubric: [String]?
    let exercises: [PracticeExercise]?
    let quiz: [QuizItem]?
    let projectFiles: [GuideProjectFile]?
    let projectInstructions: String?
    let projectSolutionFiles: [GuideProjectFile]?
    var requirements: LessonRequirements?
    var requiresCompletionForRecall: Bool { isSourceStudy == true }
    /// Extra checkpoint questions that are still unanswered or answered wrongly; `answers` maps question index to chosen option.
    func remainingExtraQuizzes(answers: [Int: Int]) -> Int {
        (extraQuizzes ?? []).enumerated().filter { answers[$0.offset] != $0.element.answerIndex }.count
    }
    func paragraphText(_ paragraph: String) -> AttributedString {
        // Source-study prose contains literal identifiers, including Python dunder names.
        if isSourceStudy == true { return AttributedString(paragraph) }
        return (try? AttributedString(markdown: paragraph,
            options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace))) ?? AttributedString(paragraph)
    }
}
struct GuideProjectFile: Codable, Hashable, Identifiable {
    let path, content: String
    var id: String { path }
}
struct RecallCard: Codable, Identifiable, Hashable {
    let id, trackID, lessonID, prompt, answer, sourceURL: String
}
enum RecallGrade: Int, CaseIterable, Identifiable {
    case again = 1, hard, good, easy
    var id: Int { rawValue }
    var title: String { ["", "Again", "Hard", "Good", "Easy"][rawValue] }
    var rating: Rating { Rating(rawValue: rawValue)! }
    var tint: Color { [.clear, .red, .orange, .mint, .blue][rawValue] }
}
struct ReviewEvent: Codable, Identifiable {
    var id = UUID()
    let cardID: String
    let date: Date
    let grade: Int
    let log: ReviewLog
}
struct Attempt: Codable, Identifiable {
    var id = UUID()
    let date: Date
    let language: CodeLanguage
    let source, output: String
    let succeeded: Bool
}
struct LearningState: Codable {
    var schemaVersion = 1
    var schedules: [String: Card] = [:]
    var reviews: [ReviewEvent] = []
    var completedLessons: Set<String> = []
    static let originalTracks: Set<String> = ["python", "numpy", "pandas", "sklearn", "pytorch", "cpp", "csharp", "go", "javascript", "rust", "ocaml", "lean"]
    var enabledTracks: Set<String> = originalTracks.union(["bash"])
    var drafts: [String: String] = [:]
    var attempts: [Attempt] = []
    var dailyNewLimit = 8
    var dailyReviewGoal = 12
    var dailyMinutes = 20
    var serverURL = ""
    var studyNotes: [String: String]?
    var readSourceChapters: Set<String>?
    var exerciseDrafts: [String: String]?
    var reviewedExercises: Set<String>?
    var reviewedProjects: Set<String>?
    var exerciseRuns: [ExerciseRun]?
    var quizAttempts: [QuizAttempt]?
    var problemDrafts: [String: String]?
    var practiceAttempts: [PracticeAttempt]?
    var quizSessions: [QuizSession]?
    var knownTracks: Set<String>?
    // Enable tracks added after this progress was saved without re-enabling ones the user turned off.
    mutating func enableNewTracks(_ ids: [String]) {
        let known = knownTracks ?? Self.originalTracks
        for id in ids where !known.contains(id) { enabledTracks.insert(id) }
        knownTracks = known.union(ids)
    }
}
enum CodeLanguage: String, Codable, CaseIterable, Identifiable {
    case python, pythonML = "python-ml", cpp, csharp, go, javascript, rust, ocaml, lean, bash
    // Keep legacy cases Codable for saved drafts/history; only these six execute. Bash is guide-only.
    static let executionLanguages: [CodeLanguage] = [.python, .pythonML, .cpp, .rust, .ocaml, .lean]
    var supportsExecution: Bool { Self.executionLanguages.contains(self) }
    var id: String { rawValue }
    var title: String {
        switch self {
        case .python: return "Python"
        case .pythonML: return "Python · ML"
        case .cpp: return "C++"
        case .csharp: return "C#"
        case .go: return "Go"
        case .javascript: return "JavaScript"
        case .rust: return "Rust"
        case .ocaml: return "OCaml"
        case .lean: return "Lean 4"
        case .bash: return "Bash"
        }
    }
    var filename: String {
        switch self {
        case .python, .pythonML: return "main.py"
        case .cpp: return "main.cpp"
        case .csharp: return "Main.cs"
        case .go: return "main.go"
        case .javascript: return "main.js"
        case .rust: return "main.rs"
        case .ocaml: return "main.ml"
        case .lean: return "Main.lean"
        case .bash: return "main.sh"
        }
    }
    var starter: String {
        switch self {
        case .python: return "def double(n):\n    return n * 2\n\nprint(double(21))"
        case .pythonML: return "import numpy as np\n\nx = np.array([1, 2, 3])\nprint(x.mean())"
        case .cpp: return "#include <iostream>\n\nint main() {\n    std::cout << 21 * 2 << \"\\n\";\n}"
        case .csharp: return "using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine(21 * 2);\n    }\n}"
        case .go: return "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(21 * 2)\n}"
        case .javascript: return "const double = n => n * 2;\n\nconsole.log(double(21));"
        case .rust: return "fn main() {\n    println!(\"{}\", 21 * 2);\n}"
        case .ocaml: return "let double n = n * 2\n\nlet () = Printf.printf \"%d\\n\" (double 21)"
        case .lean: return "def double (n : Nat) : Nat := n + n\n#eval double 21\n\nexample : double 3 = 6 := by\n  rfl"
        case .bash: return "#!/usr/bin/env bash\ndouble() { echo $(( $1 * 2 )); }\ndouble 21"
        }
    }
    var githubLanguage: String { self == .pythonML ? "Python" : self == .lean ? "Lean" : title }
}
struct ExecutionResult: Codable {
    let stdout, stderr: String
    let exitCode: Int
    let runtime: String
    let diagnostics: String?
    var succeeded: Bool { exitCode == 0 }
    var output: String {
        [stdout, stderr, diagnostics ?? ""].filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.joined(separator: "\n")
    }
}
extension Color {
    init(hex: String) {
        let value = UInt64(hex, radix: 16) ?? 0x92CEBB
        self.init(red: Double((value >> 16) & 255)/255, green: Double((value >> 8) & 255)/255, blue: Double(value & 255)/255)
    }
}

struct BookSource: Codable, Identifiable, Hashable {
    let id, title, authors, edition, filename: String
    let pdfPages: Int
    let trackIDs: [String]
    let note: String
    let sha256: String?
}
struct ReadingAssignment: Codable, Hashable, Identifiable {
    let title: String
    let url: String?
    let bookID: String?
    let section: String
    let pdfPage: Int?
    let note: String?
    var id: String { "\(bookID ?? url ?? title)#\(section)#\(pdfPage ?? 0)" }
}


struct SourceCourse: Codable, Identifiable, Hashable {
    let id, title, kind, edition, scope: String
    let trackIDs: [String]
    let sourceURL: String?
    let chapters: [SourceChapter]
    static let languageGuide = "Language guide", conceptGuide = "Concept guide"
    var isGuide: Bool { kind == Self.languageGuide || kind == Self.conceptGuide }
}
struct SourceChapter: Codable, Identifiable, Hashable {
    let id, title, coverage, note: String
    let sections, lessonIDs: [String]
    let reading: ReadingAssignment
}

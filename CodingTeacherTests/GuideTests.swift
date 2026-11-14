import XCTest
@testable import CodingTeacher

@MainActor final class GuideTests: XCTestCase {
    func testRustGuideIsOrderedReachableAndGatesRecall() throws {
        try assertGuide(id:"guide.rust",track:"rust",chapters:19,lessons:130)
    }
    func testLeanGuideIsOrderedReachableAndGatesRecall() throws {
        try assertGuide(id:"guide.lean",track:"lean",chapters:14,lessons:76)
        // Lake projects keep every file so learners can reopen the whole starter.
        let projects=try Curriculum.load().lessons.filter { $0.id.hasPrefix("guide.lean.") && $0.projectFiles != nil }
        XCTAssertEqual(projects.map(\.id).sorted(),["guide.lean.s04-lake-executable-project","guide.lean.s14-custom-tactic-project","guide.lean.s14-verified-algorithm-project"])
        for lesson in projects {
            let paths=try XCTUnwrap(lesson.projectFiles).map(\.path)
            XCTAssertTrue(paths.contains("lakefile.toml") && paths.contains("lean-toolchain") && paths.contains("Main.lean"))
            XCTAssertFalse(try XCTUnwrap(lesson.projectSolutionFiles).isEmpty)
        }
    }
    private func assertGuide(id guideID: String, track: String, chapters: Int, lessons: Int) throws {
        let curriculum=try Curriculum.load()
        let guide=try XCTUnwrap(curriculum.courses.first { $0.id == guideID })
        XCTAssertEqual(guide.kind,"Language guide")
        XCTAssertEqual(guide.chapters.count,chapters)
        XCTAssertEqual(guide.chapters.map(\.title),guide.chapters.map(\.title).sorted())
        let ids=guide.chapters.flatMap(\.lessonIDs)
        XCTAssertEqual(ids.count,lessons)
        XCTAssertEqual(Set(ids).count,lessons)
        let store=LearningStore(curriculum:curriculum,fileURL:URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
        for id in ids {
            let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == id })
            XCTAssertEqual(lesson.trackID,track)
            XCTAssertTrue(lesson.requiresCompletionForRecall)
            XCTAssertGreaterThanOrEqual(lesson.body.count,3)
            XCTAssertFalse(lesson.challenge.isEmpty)
            XCTAssertTrue(lesson.options.indices.contains(lesson.answerIndex))
            let cards=curriculum.cards.filter { $0.lessonID == id }
            XCTAssertEqual(cards.count,2+(lesson.extraQuizzes?.count ?? 0))
            XCTAssertTrue(cards.allSatisfy { !store.isEligible($0) })
        }
        let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == ids[0] })
        store.complete(lesson)
        XCTAssertTrue(curriculum.cards.filter { $0.lessonID == lesson.id }.allSatisfy { store.isEligible($0) })
        XCTAssertEqual(store.lessons(for:track).count,9)
    }
    func testExtraQuizzesAreWellFormedAndEachHasARecallCard() throws {
        let curriculum=try Curriculum.load()
        let withExtras=curriculum.lessons.filter { $0.extraQuizzes != nil }
        XCTAssertFalse(withExtras.isEmpty)
        for lesson in withExtras {
            let extras=try XCTUnwrap(lesson.extraQuizzes)
            XCTAssertTrue((2...4).contains(extras.count),lesson.id)
            for quiz in extras {
                XCTAssertEqual(quiz.options.count,4,lesson.id)
                XCTAssertEqual(Set(quiz.options).count,4,lesson.id)
                XCTAssertTrue(quiz.options.indices.contains(quiz.answerIndex),lesson.id)
                XCTAssertFalse(quiz.explanation.isEmpty,lesson.id)
            }
            let cards=curriculum.cards.filter { $0.lessonID == lesson.id }
            XCTAssertEqual(cards.count,2+extras.count,lesson.id)
            XCTAssertEqual(Set(cards.map(\.id)),Set((1...(2+extras.count)).map { "\(lesson.id).\($0)" }),lesson.id)
        }
        let restored=try JSONDecoder().decode(Curriculum.self,from:JSONEncoder().encode(curriculum))
        XCTAssertEqual(restored.lessons.filter { $0.extraQuizzes != nil }.count,withExtras.count)
    }
    func testQuantStagesAddSixtyOneLessonsEachWithExtraQuizzes() throws {
        let curriculum=try Curriculum.load()
        let guide=try XCTUnwrap(curriculum.courses.first { $0.id == "guide.rust" })
        let stages=guide.chapters.suffix(5)
        XCTAssertEqual(stages.map { String($0.title.prefix(2)) },["15","16","17","18","19"])
        XCTAssertEqual(stages.map { $0.lessonIDs.count },[12,12,12,13,12])
        for id in stages.flatMap(\.lessonIDs) {
            let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == id })
            XCTAssertTrue((2...4).contains(lesson.extraQuizzes?.count ?? 0),id)
            XCTAssertGreaterThanOrEqual(lesson.body.count,4,id)
            XCTAssertFalse(lesson.explanation.isEmpty,id)
        }
        // Lesson order must follow the stage order so the guide reads from language depth to quant drills.
        let orders=stages.flatMap(\.lessonIDs).compactMap { id in curriculum.lessons.first { $0.id == id }?.order }
        XCTAssertEqual(orders,orders.sorted())
    }
    func testQuantCargoProjectsAreCompleteAndSafelyPathed() throws {
        let curriculum=try Curriculum.load()
        let keys=["derive-macro-project","attribute-macro-diagnostics","build-profiles-lto-pgo","rayon-crossbeam-project","criterion-bench-project",
                  "ndarray-nalgebra-project","serde-data-model-project","matching-engine-project","event-driven-backtester-project",
                  "market-data-feed-threads-project","property-testing-matching-project","low-latency-pipeline-capstone-project"]
        for key in keys {
            let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust."+key },key)
            let files=try XCTUnwrap(lesson.projectFiles,key)
            let solution=try XCTUnwrap(lesson.projectSolutionFiles,key)
            XCTAssertTrue(lesson.code.isEmpty,key)
            XCTAssertTrue(lesson.projectInstructions?.contains("cargo") == true,key)
            XCTAssertTrue(files.contains { $0.path.hasSuffix("Cargo.toml") },key)
            XCTAssertEqual(Set(files.map(\.path)).count,files.count,key)
            XCTAssertTrue(Set(solution.map(\.path)).isSubset(of: Set(files.map(\.path))),key)
            for file in files+solution {
                XCTAssertFalse(file.path.hasPrefix("/"),key)
                XCTAssertFalse(file.path.split(separator:"/").contains(".."),key)
                XCTAssertFalse(file.content.isEmpty,key)
            }
        }
        // Projects that use third-party crates ship a lock file so every build resolves the same graph.
        for key in ["rayon-crossbeam-project","criterion-bench-project","ndarray-nalgebra-project","serde-data-model-project","property-testing-matching-project"] {
            let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust."+key },key)
            XCTAssertTrue(try XCTUnwrap(lesson.projectFiles).contains { $0.path == "Cargo.lock" },key)
        }
    }
    func testGoGuideIsOrderedReachableReadOnlyAndGatesRecall() throws {
        let curriculum=try Curriculum.load()
        let guide=try XCTUnwrap(curriculum.courses.first { $0.id == "guide.go" })
        XCTAssertEqual(guide.kind,"Language guide")
        XCTAssertEqual(guide.trackIDs,["go"])
        XCTAssertEqual(guide.chapters.count,27)
        XCTAssertEqual(guide.chapters.map(\.title),guide.chapters.map(\.title).sorted())
        let ids=guide.chapters.flatMap(\.lessonIDs)
        XCTAssertEqual(ids.count,195)
        XCTAssertEqual(Set(ids).count,195)
        // The Go guide is read-and-predict only; there is no Go runner.
        XCTAssertFalse(CodeLanguage.go.supportsExecution)
        let store=LearningStore(curriculum:curriculum,fileURL:URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
        var projects=0
        for id in ids {
            let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == id })
            XCTAssertEqual(lesson.trackID,"go")
            XCTAssertTrue(lesson.requiresCompletionForRecall)
            XCTAssertGreaterThanOrEqual(lesson.body.count,3)
            XCTAssertFalse(lesson.challenge.isEmpty)
            XCTAssertTrue(lesson.options.indices.contains(lesson.answerIndex))
            XCTAssertEqual(lesson.options.count,3)
            if let files=lesson.projectFiles {
                projects+=1
                XCTAssertTrue(lesson.code.isEmpty)
                XCTAssertTrue(lesson.projectInstructions?.contains("Go 1.2") == true)
                XCTAssertFalse(lesson.projectInstructions?.contains("cargo") == true)
                // The workspace lesson starts without go.work; its checks create it.
                XCTAssertTrue(files.contains { $0.path == "go.mod" || $0.path == "go.work" } || id == "guide.go.go-work-commands")
                for file in files + (lesson.projectSolutionFiles ?? []) {
                    XCTAssertFalse(file.path.hasPrefix("/"))
                    XCTAssertFalse(file.path.split(separator: "/").contains(".."))
                }
            } else {
                XCTAssertTrue(lesson.code.hasPrefix("package main"))
                XCTAssertTrue(lesson.solution.hasPrefix("package main"))
            }
            let cards=curriculum.cards.filter { $0.lessonID == id }
            XCTAssertEqual(cards.count,2)
            XCTAssertTrue(cards.allSatisfy { !store.isEligible($0) })
        }
        XCTAssertEqual(projects,42)
        let first=try XCTUnwrap(curriculum.lessons.first { $0.id == ids[0] })
        store.complete(first)
        XCTAssertTrue(curriculum.cards.filter { $0.lessonID == first.id }.allSatisfy { store.isEligible($0) })
        XCTAssertEqual(store.lessons(for:"go").count,3)
    }
    func testCargoProjectPreservesAllFilesInCurriculumRoundTrip() throws {
        let curriculum=try Curriculum.load()
        let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.rust.procedural-macros" })
        let files=try XCTUnwrap(lesson.projectFiles)
        XCTAssertEqual(files.count,5)
        XCTAssertTrue(lesson.code.isEmpty)
        XCTAssertEqual(Set(files.map(\.path)).count,5)
        XCTAssertTrue(files.contains { $0.path == "lesson-macros/Cargo.toml" && $0.content.contains("proc-macro = true") })
        let restored=try JSONDecoder().decode(Curriculum.self,from:JSONEncoder().encode(curriculum))
        XCTAssertEqual(restored.lessons.first { $0.id == lesson.id }?.projectFiles,files)
    }
    func testProjectSolutionsAndInstructionsRoundTripWithoutChangingLegacyProject() throws {
        let curriculum = try Curriculum.load()
        let restored = try JSONDecoder().decode(Curriculum.self, from: JSONEncoder().encode(curriculum))
        for (key, minutes) in [("minigrep-project", 60), ("cargo-workspace-project", 60), ("http-server-project", 90), ("environment-cli-project", 60), ("stdio-cli-project", 60), ("iterator-cli-project", 60), ("streaming-file-project", 75), ("staged-file-project", 75), ("html-server-project", 90), ("owned-server-project", 90), ("nostd-ring-project", 90), ("ffi-buffer-project", 90)] {
            let id = "guide.rust." + key
            let lesson = try XCTUnwrap(curriculum.lessons.first { $0.id == id })
            let files = try XCTUnwrap(lesson.projectFiles)
            let solution = try XCTUnwrap(lesson.projectSolutionFiles)
            XCTAssertTrue(lesson.projectInstructions?.contains("cargo") == true)
            XCTAssertTrue(lesson.code.isEmpty)
            XCTAssertGreaterThanOrEqual(lesson.body.count, 6)
            XCTAssertEqual(lesson.minutes, minutes)
            XCTAssertEqual(Set(files.map(\.path)).count, files.count)
            for file in files + solution {
                XCTAssertFalse(file.path.hasPrefix("/"))
                XCTAssertFalse(file.path.split(separator: "/").contains(".."))
                XCTAssertFalse(file.content.isEmpty)
            }
            XCTAssertTrue(Set(solution.map(\.path)).isSubset(of: Set(files.map(\.path))))
            let decoded = try XCTUnwrap(restored.lessons.first { $0.id == id })
            XCTAssertEqual(decoded.projectFiles, files)
            XCTAssertEqual(decoded.projectSolutionFiles, solution)
            XCTAssertEqual(decoded.projectInstructions, lesson.projectInstructions)
        }
        let legacy = try XCTUnwrap(restored.lessons.first { $0.id == "guide.rust.procedural-macros" })
        XCTAssertNil(legacy.projectInstructions)
        XCTAssertNil(legacy.projectSolutionFiles)
    }
    func testOcamlGuideIsOrderedReachableAndGatesRecall() throws {
        let curriculum=try Curriculum.load()
        let guide=try XCTUnwrap(curriculum.courses.first { $0.id == "guide.ocaml" })
        XCTAssertEqual(guide.kind,"Language guide")
        XCTAssertEqual(guide.trackIDs,["ocaml"])
        XCTAssertEqual(guide.chapters.count,22)
        XCTAssertEqual(guide.chapters.map(\.title),guide.chapters.map(\.title).sorted())
        let ids=guide.chapters.flatMap(\.lessonIDs)
        XCTAssertEqual(ids.count,133)
        XCTAssertEqual(Set(ids).count,133)
        let store=LearningStore(curriculum:curriculum,fileURL:URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
        for id in ids {
            let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == id })
            XCTAssertEqual(lesson.trackID,"ocaml")
            XCTAssertTrue(id.hasPrefix("guide.ocaml."))
            XCTAssertTrue(lesson.requiresCompletionForRecall)
            XCTAssertGreaterThanOrEqual(lesson.body.count,3)
            XCTAssertFalse(lesson.challenge.isEmpty)
            XCTAssertTrue(lesson.options.indices.contains(lesson.answerIndex))
            let cards=curriculum.cards.filter { $0.lessonID == id }
            XCTAssertEqual(cards.count,2)
            XCTAssertTrue(cards.allSatisfy { !store.isEligible($0) })
        }
        let lesson=try XCTUnwrap(curriculum.lessons.first { $0.id == ids[0] })
        store.complete(lesson)
        XCTAssertTrue(curriculum.cards.filter { $0.lessonID == lesson.id }.allSatisfy { store.isEligible($0) })
        // The nine-lesson starter path keeps its identifiers and its size.
        XCTAssertEqual(store.lessons(for:"ocaml").count,9)
    }
    func testDuneProjectsKeepEveryFileAndSolutionThroughRoundTrip() throws {
        let curriculum = try Curriculum.load()
        let restored = try JSONDecoder().decode(Curriculum.self, from: JSONEncoder().encode(curriculum))
        let keys = ["dune-first-project", "expect-tests", "alcotest-suite", "format-docs-opam", "core-or-error", "ppx-jane-derivers", "core-command-cli", "async-timers", "domains-parallel-sum", "atomic-counter", "effect-generators", "c-stubs-ffi", "ppx-shout", "capstone-interpreter", "capstone-leftist-heap", "capstone-typed-format", "capstone-parallel-wordcount", "compilation-units-and-interfaces", "json-with-yojson", "lexer-and-parser-generators", "compiler-front-end", "compiler-back-end", "unix-library", "str-library", "threads-library", "dynlink-plugins", "runtime-events-tracing", "toplevel-depend-and-doc-tools", "debugging-and-profiling", "merlin-editor-support"]
        for key in keys {
            let id = "guide.ocaml." + key
            let lesson = try XCTUnwrap(curriculum.lessons.first { $0.id == id })
            let files = try XCTUnwrap(lesson.projectFiles)
            let solution = try XCTUnwrap(lesson.projectSolutionFiles)
            XCTAssertFalse(lesson.projectInstructions?.isEmpty ?? true)
            XCTAssertTrue(lesson.code.isEmpty)
            XCTAssertTrue(files.contains { $0.path == "dune-project" })
            XCTAssertEqual(Set(files.map(\.path)).count, files.count)
            for file in files + solution {
                XCTAssertFalse(file.path.hasPrefix("/"))
                XCTAssertFalse(file.path.split(separator: "/").contains(".."))
                XCTAssertFalse(file.content.isEmpty)
            }
            XCTAssertFalse(solution.isEmpty)
            XCTAssertTrue(Set(solution.map(\.path)).isSubset(of: Set(files.map(\.path))))
            let decoded = try XCTUnwrap(restored.lessons.first { $0.id == id })
            XCTAssertEqual(decoded.projectFiles, files)
            XCTAssertEqual(decoded.projectSolutionFiles, solution)
            XCTAssertEqual(decoded.projectInstructions, lesson.projectInstructions)
        }
        // Single-file lessons ship runnable code and no project payload.
        let single = try XCTUnwrap(curriculum.lessons.first { $0.id == "guide.ocaml.first-program" })
        XCTAssertFalse(single.code.isEmpty)
        XCTAssertNil(single.projectFiles)
    }
}

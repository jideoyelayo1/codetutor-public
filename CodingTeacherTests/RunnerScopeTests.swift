import XCTest
@testable import CodingTeacher

@MainActor final class RunnerScopeTests: XCTestCase {
    func testRunnerSelectionContainsOnlyRequestedLanguages() {
        XCTAssertEqual(CodeLanguage.executionLanguages.map(\.rawValue), ["python", "python-ml", "cpp", "rust", "ocaml", "lean"])
        for language in [CodeLanguage.csharp, .go, .javascript] {
            XCTAssertFalse(language.supportsExecution)
        }
        XCTAssertNil(CodeLanguage(rawValue: "java"))
    }

    func testLegacyDraftsAndHistorySurvivePersistenceAndBackup() throws {
        let curriculum = try Curriculum.load()
        let directory = URL.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let url = directory.appendingPathComponent("progress.json")
        let store = LearningStore(curriculum: curriculum, fileURL: url)
        for language in [CodeLanguage.csharp, .go, .javascript] {
            store.draft("saved " + language.rawValue, language: language)
            store.recordAttempt(language: language, source: "history " + language.rawValue,
                result: ExecutionResult(stdout: "old output", stderr: "", exitCode: 0, runtime: "legacy", diagnostics: nil))
        }
        let restored = LearningStore(curriculum: curriculum, fileURL: url)
        XCTAssertTrue(restored.loadedSuccessfully)
        XCTAssertEqual(restored.state.drafts, store.state.drafts)
        XCTAssertEqual(restored.state.attempts.map(\.language), store.state.attempts.map(\.language))
        let imported = LearningStore(curriculum: curriculum, fileURL: directory.appendingPathComponent("imported.json"))
        try imported.importBackup(from: store.exportURL())
        XCTAssertEqual(imported.state.drafts, store.state.drafts)
        XCTAssertEqual(imported.state.attempts.map(\.source), store.state.attempts.map(\.source))
        XCTAssertEqual(imported.state.attempts.map(\.language), store.state.attempts.map(\.language))
        for id in ["csharp", "go", "javascript"] {
            XCTAssertTrue(curriculum.tracks.contains { $0.id == id })
            XCTAssertFalse(restored.lessons(for: id).isEmpty)
        }
    }

    func testRemovedLanguagesAreRejectedBeforeURLOrNetworkUse() async throws {
        for language in [CodeLanguage.csharp, .go, .javascript] {
            do {
                _ = try await RemoteExecutionService().run(language: language, source: "old source", stdin: "", base: "")
                XCTFail("Removed language must not execute")
            } catch ExecutionError.unsupportedLanguage(let title) {
                XCTAssertEqual(title, language.title)
            }
        }
    }

    func testControllerDoesNotInvokeOperationsForRemovedLanguages() async {
        var called = false
        let owner = LabExecutionController(operation: { _, _, _, _ in
            called = true
            return ExecutionResult(stdout: "", stderr: "", exitCode: 0, runtime: "test", diagnostics: nil)
        })
        for language in [CodeLanguage.csharp, .go, .javascript] {
            owner.start(language: language, source: "", stdin: "", base: "") { _ in XCTFail("Removed run must not publish output") }
            await Task.yield()
            XCTAssertFalse(owner.running)
            XCTAssertNil(owner.result)
            XCTAssertNotNil(owner.error)
        }
        XCTAssertFalse(called)
    }

    func testDiscoveryFiltersOldServerCapabilitiesToCurrentScope() throws {
        let ids = ["python", "python-ml", "cpp", "csharp", "go", "javascript", "java", "rust", "ocaml", "lean"]
        let encoded = try JSONEncoder().encode(CapabilitiesResponse(runtimes: ids.map {
            RunnerCapability(id: $0, version: "1.0.0", packages: [])
        }))
        let filtered = try RemoteExecutionService.decodeCapabilities(encoded)
        XCTAssertEqual(filtered.map(\.id), CodeLanguage.executionLanguages.map(\.rawValue))
    }
}

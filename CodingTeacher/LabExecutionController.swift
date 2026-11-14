import Foundation
import Observation

/// Owns one run without making the task retain its UI owner.
@MainActor @Observable final class LabExecutionController {
    typealias Operation = @MainActor (CodeLanguage, String, String, String) async throws -> ExecutionResult
    private(set) var running = false
    private(set) var result: ExecutionResult?
    private(set) var error: String?
    @ObservationIgnored private var task: Task<Void, Never>?
    @ObservationIgnored private var activeID: UUID?
    @ObservationIgnored private let operation: Operation
    init(operation: Operation? = nil) { self.operation = operation ?? Self.execute }
    deinit { task?.cancel() }
    func start(language: CodeLanguage, source: String, stdin: String, base: String,
               onSuccess: @escaping @MainActor (ExecutionResult) -> Void) {
        cancel(showMessage: false)
        result = nil; error = nil
        guard language.supportsExecution else {
            error = ExecutionError.unsupportedLanguage(language.title).localizedDescription
            return
        }
        let id = UUID(); activeID = id; running = true
        let operation = operation
        task = Task { @MainActor [weak self] in
            do {
                let output = try await operation(language, source, stdin, base)
                try Task.checkCancellation()
                guard let self, self.activeID == id else { return }
                self.result = output; self.running = false; self.activeID = nil; self.task = nil
                onSuccess(output)
            } catch {
                guard let self, self.activeID == id else { return }
                self.error = error is CancellationError ? "Execution stopped." : error.localizedDescription
                self.running = false; self.activeID = nil; self.task = nil
            }
        }
    }
    func cancel(showMessage: Bool = true) {
        let wasRunning = running
        activeID = nil; task?.cancel(); task = nil; running = false
        if showMessage && wasRunning { error = "Execution stopped." }
    }
    func clear() { cancel(showMessage: false); result = nil; error = nil }
    private static func execute(language: CodeLanguage, source: String, stdin: String, base: String) async throws -> ExecutionResult {
        try Task.checkCancellation()
        return try await RemoteExecutionService().run(language: language, source: source, stdin: stdin, base: base)
    }
}

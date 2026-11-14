import XCTest
import SwiftUI
import PDFKit
@testable import CodingTeacher

private final class WeakReference<T: AnyObject> {
    weak var value: T?
    init(_ value: T?) { self.value = value }
}
private final class LifetimeMarker: @unchecked Sendable { }

@MainActor final class MemoryTests: XCTestCase {
    private func eventually(timeout: TimeInterval = 3, _ condition: () -> Bool) async throws -> Bool {
        let deadline = Date().addingTimeInterval(timeout)
        while !condition() && Date() < deadline { try await Task.sleep(for: .milliseconds(20)) }
        return condition()
    }
    func testExecutionOwnerDeallocatesAndCancelsItsTask() async throws {
        let cancelled = expectation(description: "Owner cancellation reaches the operation")
        var owner: LabExecutionController? = LabExecutionController(operation: { _, _, _, _ in
            do { try await Task.sleep(for: .seconds(30)) }
            catch { cancelled.fulfill(); throw error }
            return ExecutionResult(stdout: "", stderr: "", exitCode: 0, runtime: "test", diagnostics: nil)
        })
        let weakOwner = WeakReference(owner)
        owner?.start(language: .rust, source: "", stdin: "", base: "") { _ in XCTFail("Cancelled owner must not publish output") }
        await Task.yield()
        owner = nil
        XCTAssertNil(weakOwner.value, "The task must not retain its controller across suspension")
        await fulfillment(of: [cancelled], timeout: 2)
    }
    func testStoppedRunCannotClearOrOverwriteANewerRun() async throws {
        var pending: [String: CheckedContinuation<ExecutionResult, Error>] = [:]
        let owner = LabExecutionController(operation: { _, source, _, _ in
            try await withCheckedThrowingContinuation { pending[source] = $0 }
        })
        var completed: [String] = []
        owner.start(language: .rust, source: "old", stdin: "", base: "") { completed.append($0.stdout) }
        let first = try await eventually { pending["old"] != nil }; XCTAssertTrue(first)
        owner.cancel()
        owner.start(language: .rust, source: "new", stdin: "", base: "") { completed.append($0.stdout) }
        let second = try await eventually { pending["new"] != nil }; XCTAssertTrue(second)
        pending.removeValue(forKey: "old")?.resume(throwing: CancellationError())
        await Task.yield(); await Task.yield()
        XCTAssertTrue(owner.running)
        XCTAssertNil(owner.error)
        pending.removeValue(forKey: "new")?.resume(returning: ExecutionResult(stdout: "new output", stderr: "", exitCode: 0, runtime: "test", diagnostics: nil))
        let finished = try await eventually { !owner.running }; XCTAssertTrue(finished)
        XCTAssertEqual(owner.result?.stdout, "new output")
        XCTAssertEqual(completed, ["new output"])
    }
    func testExcludedRunCancelsPendingWorkAndReleasesOwner() async throws {
        let started = expectation(description: "Supported operation started")
        let cancelled = expectation(description: "Pending operation cancelled")
        var owner: LabExecutionController? = LabExecutionController(operation: { _, _, _, _ in
            started.fulfill()
            do { try await Task.sleep(for: .seconds(30)) }
            catch { cancelled.fulfill(); throw error }
            return ExecutionResult(stdout: "", stderr: "", exitCode: 0, runtime: "test", diagnostics: nil)
        })
        let weakOwner = WeakReference(owner)
        owner?.start(language: .python, source: "", stdin: "", base: "") { _ in XCTFail("Cancelled output must not be saved") }
        await fulfillment(of: [started], timeout: 2)
        owner?.start(language: .javascript, source: "", stdin: "", base: "") { _ in XCTFail("Excluded output must not be saved") }
        XCTAssertFalse(owner?.running ?? true)
        XCTAssertNotNil(owner?.error)
        owner = nil
        XCTAssertNil(weakOwner.value)
        await fulfillment(of: [cancelled], timeout: 2)
    }
    func testPDFTeardownReleasesDocumentAndCallbackCapture() async throws {
        let view = PDFView()
        var marker: LifetimeMarker? = LifetimeMarker()
        let weakMarker = WeakReference(marker)
        let coordinator = PDFReader.Coordinator(onPageChange: { [capture = marker!] _, _ in _ = capture })
        marker = nil
        let data = UIGraphicsPDFRenderer(bounds: CGRect(x: 0, y: 0, width: 200, height: 300)).pdfData { context in
            context.beginPage(); ("Lifetime test" as NSString).draw(at: CGPoint(x: 20, y: 20))
        }
        view.document = PDFDocument(data: data)
        let document = WeakReference(view.document)
        XCTAssertNotNil(document.value); XCTAssertNotNil(weakMarker.value)
        PDFReader.dismantleUIView(view, coordinator: coordinator)
        let released = try await eventually { document.value == nil && weakMarker.value == nil }
        XCTAssertTrue(released, "Dismantling must release a potentially large document and its UI callback")
    }
    func testPDFCoordinatorDeinitUnregistersItsObserver() async throws {
        var marker: LifetimeMarker? = LifetimeMarker()
        let weakMarker = WeakReference(marker)
        var coordinator: PDFReader.Coordinator? = PDFReader.Coordinator(onPageChange: { _, _ in })
        coordinator?.observer = NotificationCenter.default.addObserver(forName: .PDFViewPageChanged, object: nil, queue: .main) { [capture = marker!] _ in _ = capture }
        marker = nil
        XCTAssertNotNil(weakMarker.value)
        coordinator = nil
        let released = try await eventually { weakMarker.value == nil }
        XCTAssertTrue(released, "NotificationCenter must not retain the callback after its coordinator dies")
    }
    func testDraftDebounceDoesNotRetainItsStore() async throws {
        var store: LearningStore? = LearningStore(curriculum: try Curriculum.load(), fileURL: URL.temporaryDirectory.appendingPathComponent(UUID().uuidString).appendingPathComponent("progress.json"))
        let weakStore = WeakReference(store)
        store?.draft("print(42)", language: .python)
        store = nil
        XCTAssertNil(weakStore.value)
    }
}

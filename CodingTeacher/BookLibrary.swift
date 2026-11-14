import Foundation
import Observation
import PDFKit
import CryptoKit

enum BookLibraryError: LocalizedError {
    case invalidBookID, notPDF, lockedPDF, tooLarge
    var errorDescription: String? {
        switch self {
        case .invalidBookID: return "This book’s library entry is invalid."
        case .notPDF: return "Choose a readable PDF with at least one page."
        case .lockedPDF: return "This PDF is locked. Import a copy you can open without a password."
        case .tooLarge: return "Choose a PDF smaller than 500 MB."
        }
    }
}
@MainActor @Observable final class BookLibrary {
    private let root: URL
    private let bundledRoot: URL?
    @ObservationIgnored private var digests: [String:String] = [:]
    private(set) var positions: [String: Int] = [:]
    private(set) var revision = 0
    var errorMessage: String?
    init(root: URL? = nil, bundledRoot: URL? = Bundle.main.resourceURL) {
        self.root = root ?? URL.applicationSupportDirectory.appendingPathComponent("CodingTeacher/Books")
        self.bundledRoot = bundledRoot
        if let data = try? Data(contentsOf: self.root.appendingPathComponent("positions.json")), let positions = try? JSONDecoder().decode([String:Int].self,from:data) {
            self.positions = positions.filter { $0.value >= 0 }
        }
    }
    static func validID(_ id: String) -> Bool {
        !id.isEmpty && id.utf8.allSatisfy { (97...122).contains($0) || (48...57).contains($0) || $0 == 45 }
    }
    func fileURL(for id: String) -> URL? {
        _ = revision
        guard Self.validID(id) else { return nil }
        let url = root.appendingPathComponent(id + ".pdf")
        if FileManager.default.fileExists(atPath:url.path) { return url }
        // An imported replacement wins; bundled personal copies remain read-only.
        guard let bundledRoot else { return nil }
        for directory in [bundledRoot.appendingPathComponent("PersonalBooks"), bundledRoot] {
            let bundled = directory.appendingPathComponent(id + ".pdf")
            if FileManager.default.fileExists(atPath:bundled.path) { return bundled }
        }
        return nil
    }
    func importPDF(from source: URL, for bookID: String) throws {
        guard Self.validID(bookID) else { throw BookLibraryError.invalidBookID }
        let access = source.startAccessingSecurityScopedResource()
        defer { if access { source.stopAccessingSecurityScopedResource() } }
        let size = try source.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0
        guard size < 500_000_000 else { throw BookLibraryError.tooLarge }
        try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        let staging = root.appendingPathComponent(UUID().uuidString + ".pdf")
        defer { try? FileManager.default.removeItem(at:staging) }
        try FileManager.default.copyItem(at:source,to:staging)
        guard let document = PDFDocument(url:staging), document.pageCount > 0 else { throw BookLibraryError.notPDF }
        guard !document.isLocked else { throw BookLibraryError.lockedPDF }
        let digest = try Self.fingerprint(staging)
        let target = root.appendingPathComponent(bookID + ".pdf")
        if FileManager.default.fileExists(atPath:target.path) { _ = try FileManager.default.replaceItemAt(target,withItemAt:staging) }
        else { try FileManager.default.moveItem(at:staging,to:target) }
        digests[bookID] = digest
        positions[bookID] = 0; revision += 1; savePositions()
    }
    static func fingerprint(_ url: URL) throws -> String {
        let handle = try FileHandle(forReadingFrom:url)
        defer { try? handle.close() }
        var hash = SHA256()
        while let chunk = try handle.read(upToCount:1_048_576), !chunk.isEmpty { hash.update(data:chunk) }
        return hash.finalize().map { String(format:"%02x",$0) }.joined()
    }
    func matchesReference(_ book: BookSource) -> Bool {
        guard let expected=book.sha256, let url=fileURL(for:book.id) else { return false }
        if digests[book.id] == nil { digests[book.id] = try? Self.fingerprint(url) }
        return digests[book.id] == expected
    }
    func remember(pageIndex: Int, bookID: String) {
        guard Self.validID(bookID), pageIndex >= 0, positions[bookID] != pageIndex else { return }
        positions[bookID] = pageIndex; savePositions()
    }
    static func openingPage(requestedPDFPage: Int?, rememberedIndex: Int?, actualCount: Int, expectedCount: Int, referenceMatches: Bool) -> Int {
        guard actualCount > 0 else { return 0 }
        let target: Int
        if let requestedPDFPage, referenceMatches, actualCount == expectedCount { target = requestedPDFPage - 1 }
        else { target = rememberedIndex ?? 0 }
        return min(max(0,target),actualCount-1)
    }
    private func savePositions() {
        do {
            try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
            try JSONEncoder().encode(positions).write(to:root.appendingPathComponent("positions.json"),options:[.atomic,.completeFileProtectionUntilFirstUserAuthentication])
        } catch { errorMessage = "Your reading position could not be saved. \(error.localizedDescription)" }
    }
}

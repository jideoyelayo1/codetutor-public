import XCTest
import UIKit
import SwiftUI
import PDFKit
@testable import CodingTeacher

@MainActor final class BookTests: XCTestCase {
    private func temporaryRoot() -> URL { URL.temporaryDirectory.appendingPathComponent(UUID().uuidString) }
    private func specimenPDF(at url:URL, pages:Int=2) throws -> Data {
        let renderer=UIGraphicsPDFRenderer(bounds:CGRect(x:0,y:0,width:200,height:300))
        let data=renderer.pdfData { context in
            for index in 0..<pages { context.beginPage(); ("Specimen page \(index+1)" as NSString).draw(at:CGPoint(x:20,y:20),withAttributes:[.font:UIFont.systemFont(ofSize:14)]) }
        }
        try data.write(to:url); return data
    }
    func testReadingReferencesPointToKnownBooksAndValidPages() throws {
        let c=try Curriculum.load()
        XCTAssertTrue(c.bookCatalog.isEmpty)
        XCTAssertEqual(c.lessons.filter { $0.isSourceStudy != true }.flatMap { $0.reading ?? [] }.count,19)
        for lesson in c.lessons {
            for reading in lesson.reading ?? [] {
                if let id=reading.bookID {
                    let book=try XCTUnwrap(c.bookCatalog.first { $0.id==id })
                    if let page=reading.pdfPage { XCTAssertTrue((1...book.pdfPages).contains(page)) }
                } else { XCTAssertEqual(URL(string:try XCTUnwrap(reading.url))?.scheme,"https") }
            }
        }
        XCTAssertTrue(c.tracks.first { $0.id=="lean" }!.resources.contains { $0.url=="https://lean-lang.org/learn/" })
    }
    func testPreviousCurriculumWithoutBooksStillDecodes() throws {
        let original=try Curriculum.load()
        var data=try JSONSerialization.jsonObject(with:JSONEncoder().encode(original)) as! [String:Any]
        data.removeValue(forKey:"books")
        data["lessons"]=(data["lessons"] as! [[String:Any]]).map { lesson in var old=lesson; old.removeValue(forKey:"reading"); return old }
        let restored=try JSONDecoder().decode(Curriculum.self,from:JSONSerialization.data(withJSONObject:data))
        XCTAssertTrue(restored.bookCatalog.isEmpty)
        XCTAssertEqual(original.lessons.map(\.id),restored.lessons.map(\.id))
    }
    func testPathTraversalIsRejected() throws {
        let library=BookLibrary(root:temporaryRoot())
        for id in ["../book", "a/b", "", ".hidden", "book.pdf"] { XCTAssertFalse(BookLibrary.validID(id)); XCTAssertNil(library.fileURL(for:id)) }
        XCTAssertTrue(BookLibrary.validID("another-book"))
    }
    func testBundledCopyOpensWithoutImportAndReplacementWins() throws {
        let root=temporaryRoot()
        defer { try? FileManager.default.removeItem(at:root) }
        let bundle=root.appendingPathComponent("bundle/PersonalBooks")
        try FileManager.default.createDirectory(at:bundle,withIntermediateDirectories:true)
        let originalURL=bundle.appendingPathComponent("specimen-book.pdf")
        let original=try specimenPDF(at:originalURL,pages:2)
        let shelf=BookLibrary(root:root.appendingPathComponent("shelf"),bundledRoot:bundle.deletingLastPathComponent())
        XCTAssertEqual(shelf.fileURL(for:"specimen-book"),originalURL)
        shelf.remember(pageIndex:1,bookID:"specimen-book")
        XCTAssertEqual(shelf.positions["specimen-book"],1)
        let replacement=root.appendingPathComponent("replacement.pdf")
        _ = try specimenPDF(at:replacement,pages:3)
        try shelf.importPDF(from:replacement,for:"specimen-book")
        XCTAssertNotEqual(shelf.fileURL(for:"specimen-book"),originalURL)
        XCTAssertEqual(PDFDocument(url:try XCTUnwrap(shelf.fileURL(for:"specimen-book")))?.pageCount,3)
        XCTAssertEqual(try Data(contentsOf:originalURL),original)
        XCTAssertEqual(shelf.positions["specimen-book"],0)
        let restored=BookLibrary(root:root.appendingPathComponent("shelf"),bundledRoot:bundle.deletingLastPathComponent())
        XCTAssertEqual(restored.fileURL(for:"specimen-book"),shelf.fileURL(for:"specimen-book"))
    }
    func testChapterJumpsRequireMatchingCopyAndClampPageRange() {
        XCTAssertEqual(BookLibrary.openingPage(requestedPDFPage:245,rememberedIndex:10,actualCount:766,expectedCount:766,referenceMatches:true),244)
        XCTAssertEqual(BookLibrary.openingPage(requestedPDFPage:245,rememberedIndex:10,actualCount:500,expectedCount:766,referenceMatches:true),10)
        XCTAssertEqual(BookLibrary.openingPage(requestedPDFPage:245,rememberedIndex:10,actualCount:766,expectedCount:766,referenceMatches:false),10)
        XCTAssertEqual(BookLibrary.openingPage(requestedPDFPage:999,rememberedIndex:nil,actualCount:20,expectedCount:20,referenceMatches:true),19)
        XCTAssertEqual(BookLibrary.openingPage(requestedPDFPage:nil,rememberedIndex:999,actualCount:20,expectedCount:20,referenceMatches:true),19)
    }
    func testPDFImportAndReadingPositionPersistWithoutChangingSource() throws {
        let root=temporaryRoot(); try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        let source=root.appendingPathComponent("source.pdf")
        let original=try specimenPDF(at:source)
        let shelfRoot=root.appendingPathComponent("shelf")
        let shelf=BookLibrary(root:shelfRoot)
        try shelf.importPDF(from:source,for:"another-book")
        let imported=try XCTUnwrap(shelf.fileURL(for:"another-book"))
        XCTAssertEqual(PDFDocument(url:imported)?.pageCount,2)
        XCTAssertEqual(try Data(contentsOf:source),original)
        shelf.remember(pageIndex:1,bookID:"another-book")
        let restored=BookLibrary(root:shelfRoot)
        XCTAssertEqual(restored.positions["another-book"],1)
        XCTAssertNotNil(restored.fileURL(for:"another-book"))
    }
    func testInvalidReplacementPreservesImportedBook() throws {
        let root=temporaryRoot(); try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        let source=root.appendingPathComponent("source.pdf"); let original=try specimenPDF(at:source)
        let shelf=BookLibrary(root:root.appendingPathComponent("shelf"))
        try shelf.importPDF(from:source,for:"specimen-book")
        let invalid=root.appendingPathComponent("invalid.pdf"); try Data("This is not a PDF".utf8).write(to:invalid)
        XCTAssertThrowsError(try shelf.importPDF(from:invalid,for:"specimen-book"))
        XCTAssertEqual(try Data(contentsOf:XCTUnwrap(shelf.fileURL(for:"specimen-book"))),original)
    }
    func testValidReplacementUpdatesStoredBook() throws {
        let root=temporaryRoot(); try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        let source=root.appendingPathComponent("source.pdf"); _=try specimenPDF(at:source)
        let shelf=BookLibrary(root:root.appendingPathComponent("shelf")); try shelf.importPDF(from:source,for:"specimen-book")
        let replacement=root.appendingPathComponent("replacement.pdf"); _=try specimenPDF(at:replacement,pages:3)
        try shelf.importPDF(from:replacement,for:"specimen-book")
        XCTAssertEqual(PDFDocument(url:try XCTUnwrap(shelf.fileURL(for:"specimen-book")))?.pageCount,3)
    }
    func testSamePageCountDoesNotIdentifyAReferenceCopy() throws {
        let root=temporaryRoot(); try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        let source=root.appendingPathComponent("reference.pdf"); _=try specimenPDF(at:source)
        let book=BookSource(id:"specimen",title:"",authors:"",edition:"",filename:"",pdfPages:2,trackIDs:[],note:"",sha256:try BookLibrary.fingerprint(source))
        let library=BookLibrary(root:root.appendingPathComponent("shelf"))
        try library.importPDF(from:source,for:book.id)
        XCTAssertTrue(library.matchesReference(book))
        XCTAssertTrue(BookLibrary(root:root.appendingPathComponent("shelf")).matchesReference(book))
        let other=root.appendingPathComponent("different.pdf")
        let renderer=UIGraphicsPDFRenderer(bounds:CGRect(x:0,y:0,width:200,height:300))
        try renderer.pdfData { context in for _ in 0..<2 { context.beginPage(); ("Different edition" as NSString).draw(at:CGPoint(x:20,y:20),withAttributes:[.font:UIFont.systemFont(ofSize:14)]) } }.write(to:other)
        try library.importPDF(from:other,for:book.id)
        XCTAssertEqual(PDFDocument(url:try XCTUnwrap(library.fileURL(for:book.id)))?.pageCount,2)
        XCTAssertFalse(library.matchesReference(book))
    }
    func testReaderOpensAssignedPDFPage() async throws {
        let root=temporaryRoot(); try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        let file=root.appendingPathComponent("specimen.pdf"); _=try specimenPDF(at:file)
        let book=BookSource(id:"specimen",title:"Test PDF",authors:"",edition:"",filename:"specimen.pdf",pdfPages:2,trackIDs:[],note:"",sha256:try BookLibrary.fingerprint(file))
        let library=BookLibrary(root:root.appendingPathComponent("shelf"))
        try library.importPDF(from:file,for:book.id)
        let imported=try XCTUnwrap(library.fileURL(for:book.id))
        let host=UIHostingController(rootView:NavigationStack { BookReaderView(book:book,url:imported,requestedPDFPage:2) }.environment(library))
        let window=UIWindow(frame:CGRect(x:0,y:0,width:402,height:874)); window.rootViewController=host; window.makeKeyAndVisible()
        defer { window.isHidden=true }
        host.view.frame=window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for:.milliseconds(800))
        func findPDF(_ view:UIView) -> PDFView? { if let pdf=view as? PDFView { return pdf }; for child in view.subviews { if let pdf=findPDF(child) { return pdf } }; return nil }
        let pdf=try XCTUnwrap(findPDF(host.view)); let doc=try XCTUnwrap(pdf.document)
        XCTAssertEqual(doc.index(for:try XCTUnwrap(pdf.currentPage)),1)
        XCTAssertEqual(library.positions[book.id],1)
        let readerImage=UIGraphicsImageRenderer(bounds:host.view.bounds).image { _ in host.view.drawHierarchy(in:host.view.bounds,afterScreenUpdates:true) }
        try XCTUnwrap(readerImage.pngData()).write(to:URL.documentsDirectory.appendingPathComponent("reader-preview.png"))
        let restored=BookLibrary(root:root.appendingPathComponent("shelf"))
        let resumed=UIHostingController(rootView:NavigationStack { BookReaderView(book:book,url:imported,requestedPDFPage:nil) }.environment(restored))
        window.rootViewController=resumed; resumed.view.frame=window.bounds; resumed.view.layoutIfNeeded()
        try await Task.sleep(for:.milliseconds(500))
        let resumedPDF=try XCTUnwrap(findPDF(resumed.view)); let resumedDocument=try XCTUnwrap(resumedPDF.document)
        XCTAssertEqual(resumedDocument.index(for:try XCTUnwrap(resumedPDF.currentPage)),1)
        // Capture the real library UI for visual QA after exercising the reader.
        let store=LearningStore(curriculum:try Curriculum.load(),fileURL:root.appendingPathComponent("progress.json"))
        let shelf=UIHostingController(rootView:NavigationStack { LibraryView(initialMode:1) }.environment(store).environment(library).preferredColorScheme(.dark))
        window.rootViewController=shelf; shelf.view.frame=window.bounds; shelf.view.layoutIfNeeded()
        try await Task.sleep(for:.milliseconds(300))
        let image=UIGraphicsImageRenderer(bounds:shelf.view.bounds).image { _ in shelf.view.drawHierarchy(in:shelf.view.bounds,afterScreenUpdates:true) }
        let png=try XCTUnwrap(image.pngData()); try png.write(to:URL.documentsDirectory.appendingPathComponent("books-preview.png"))
        print("BOOKS_PREVIEW_PATH=",URL.documentsDirectory.appendingPathComponent("books-preview.png").path)
    }
}

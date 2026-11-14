import SwiftUI
import PDFKit
import UniformTypeIdentifiers

struct BookShelfView: View {
    @Environment(LearningStore.self) private var store
    @Environment(BookLibrary.self) private var library
    var body: some View {
        VStack(alignment:.leading,spacing:18) {
            Text("Your own reading shelf.").font(.title2.bold())
            Text("Your books open here offline. Lessons can take you directly to a mapped chapter. You can also replace a copy with another PDF.").foregroundStyle(Palette.muted)
            ForEach(store.curriculum.bookCatalog) { book in
                NavigationLink { BookDetailView(book:book) } label: {
                    HStack(alignment:.top,spacing:14) {
                        Image(systemName:"book.closed").foregroundStyle(Palette.mint).font(.title2)
                        VStack(alignment:.leading,spacing:5) {
                            Text(book.title).font(.headline)
                            Text(book.authors).font(.caption).foregroundStyle(Palette.muted)
                            Text(book.edition).font(.caption2).foregroundStyle(Palette.muted)
                            Label(library.fileURL(for:book.id) == nil ? "Import your copy" : "Available offline",systemImage:library.fileURL(for:book.id) == nil ? "plus.circle" : "checkmark.circle").font(.caption).foregroundStyle(Palette.mint)
                        }
                        Spacer(); Image(systemName:"chevron.right").font(.caption)
                    }.padding(16).background(Palette.panel,in:RoundedRectangle(cornerRadius:16))
                }.buttonStyle(.plain)
            }
            Text("PDF page numbers refer to the exact copies inspected in your Mac’s Books folder. Printed page numbers can differ. PDFs and reading positions stay on this device and are separate from progress backups.").font(.caption).foregroundStyle(Palette.muted)
        }
    }
}
struct CompanionReadings: View {
    @Environment(LearningStore.self) private var store
    @Environment(\.offlineReferences) private var references
    let readings: [ReadingAssignment]
    var body: some View {
        VStack(alignment:.leading,spacing:12) {
            SectionLabel(title:"Companion reading & watching")
            ForEach(readings) { reading in
                if let bookID=reading.bookID, let book=store.curriculum.bookCatalog.first(where:{$0.id==bookID}) {
                    NavigationLink { BookDetailView(book:book,requestedPDFPage:reading.pdfPage,section:reading.section) } label: { row(reading,icon:"book") }.buttonStyle(.plain)
                } else if let address=reading.url, let page=references.page(source:address) {
                    NavigationLink { ReferenceReaderView(page:page,anchor:URL(string:address)?.fragment) } label: { row(reading,icon:"doc.text") }.buttonStyle(.plain)
                } else if let address=reading.url, let url=URL(string:address) {
                    Link(destination:url) { row(reading,icon:address.contains("youtube.com") ? "play.rectangle" : "arrow.up.right") }.foregroundStyle(.primary)
                }
            }
        }
    }
    private func row(_ reading: ReadingAssignment, icon: String) -> some View {
        HStack(alignment:.top,spacing:12) {
            Image(systemName:icon).foregroundStyle(Palette.mint)
            VStack(alignment:.leading,spacing:5) {
                Text(reading.title).font(.headline)
                Text(reading.section).font(.subheadline).foregroundStyle(Palette.muted)
                if let page=reading.pdfPage { Text("PDF page \(page)").font(.caption.monospacedDigit()).foregroundStyle(Palette.mint) }
                if let note=reading.note { Text(note).font(.caption).foregroundStyle(Palette.muted) }
            }
            Spacer(minLength:0)
        }.padding(16).background(Palette.panel,in:RoundedRectangle(cornerRadius:16))
    }
}
struct BookDetailView: View {
    @Environment(BookLibrary.self) private var library
    @Environment(LearningStore.self) private var store
    let book: BookSource
    var requestedPDFPage: Int? = nil
    var section: String? = nil
    @State private var importing = false
    @State private var reading = false
    @State private var status: String?
    var body: some View {
        Page {
            Image(systemName:"book.closed").font(.largeTitle).foregroundStyle(Palette.mint)
            Text(book.title).font(.largeTitle.bold())
            Text(book.authors).font(.title3).foregroundStyle(Palette.muted)
            Text(book.edition).font(.subheadline).foregroundStyle(Palette.muted)
            Panel {
                if let section { Text(section).font(.headline); if let page=requestedPDFPage { Text("Mapped to PDF page \(page) in your Mac copy.").font(.caption).foregroundStyle(Palette.muted) } }
                Text(book.note).font(.subheadline)
                if library.fileURL(for:book.id) != nil {
                    ActionButton(title:section == nil ? "Continue reading" : "Open assigned section",icon:"book") { reading=true }
                    Button("Import a different copy") { importing=true }.font(.caption)
                } else {
                    ActionButton(title:"Import your PDF",icon:"square.and.arrow.down") { importing=true }
                    Text("Transfer your Mac copy to the iPhone with AirDrop or Files, then select it here.").font(.caption).foregroundStyle(Palette.muted)
                    Text(book.filename).font(.caption2).foregroundStyle(Palette.muted).textSelection(.enabled)
                }
                if let status { Text(status).font(.caption).foregroundStyle(.orange) }
            }
            if let course = store.curriculum.courses.first(where: { $0.id == book.id }) {
                NavigationLink("Open the chapter learning path") { SourceCourseDetailView(course: course) }
            }
            Text("Chapter links use the exact \(book.pdfPages)-page copy inspected on your Mac. Other copies open at your saved position; you can choose a page manually.").font(.caption).foregroundStyle(Palette.muted)
        }.navigationTitle("Your book").navigationBarTitleDisplayMode(.inline)
        .fileImporter(isPresented:$importing,allowedContentTypes:[.pdf]) { outcome in
            do { try library.importPDF(from:outcome.get(),for:book.id); status=nil; reading=true }
            catch { status=error.localizedDescription }
        }
        .fullScreenCover(isPresented:$reading) {
            if let url=library.fileURL(for:book.id) { NavigationStack { BookReaderView(book:book,url:url,requestedPDFPage:requestedPDFPage).toolbar { ToolbarItem(placement:.topBarLeading) { Button("Done") { reading=false } } } } }
        }
    }
}
struct BookReaderView: View {
    @Environment(BookLibrary.self) private var library
    let book: BookSource
    let url: URL
    let requestedPDFPage: Int?
    @State private var currentPage = 0
    @State private var pageCount = 0
    @State private var jumpToPage = ""
    @State private var jumpRequest: PDFPageJump?
    @FocusState private var pageFieldFocused: Bool
    var body: some View {
        let referenceMatches = library.matchesReference(book)
        VStack(spacing:0) {
            if !referenceMatches || (pageCount > 0 && pageCount != book.pdfPages) { Text("This copy has no verified chapter map. Choose a PDF page below.").font(.caption).padding(8).frame(maxWidth:.infinity).background(Color.orange.opacity(0.12)) }
            HStack(spacing:12) {
                Text("\(currentPage+1) / \(pageCount)").font(.subheadline.monospacedDigit())
                Spacer()
                TextField("",text:$jumpToPage,prompt:Text("Page").foregroundStyle(Palette.muted)).keyboardType(.numberPad).focused($pageFieldFocused).frame(width:80).font(.subheadline).padding(8).background(Palette.background,in:RoundedRectangle(cornerRadius:8)).accessibilityLabel("Go to PDF page")
                Button("Go") { if let page=Int(jumpToPage), page > 0, page <= pageCount { pageFieldFocused=false; jumpRequest=PDFPageJump(index:page-1) } }.font(.subheadline.bold()).tint(Palette.mint).disabled(pageCount == 0)
            }.padding(12).background(Palette.panel)
            PDFReader(url:url,initialPage:requestedPDFPage,rememberedIndex:library.positions[book.id],expectedCount:book.pdfPages,referenceMatches:referenceMatches,jumpRequest:jumpRequest) { index,count in
                currentPage=index; pageCount=count; library.remember(pageIndex:index,bookID:book.id)
            }
            if let message=library.errorMessage { Text(message).font(.caption).foregroundStyle(.orange).padding(8) }
        }.navigationTitle(book.title).navigationBarTitleDisplayMode(.inline).background(Palette.background)
    }
}
struct PDFPageJump { let id=UUID(); let index:Int }
struct PDFReader: UIViewRepresentable {
    let url: URL
    let initialPage: Int?
    let rememberedIndex: Int?
    let expectedCount: Int
    let referenceMatches: Bool
    let jumpRequest: PDFPageJump?
    let onPageChange: (Int,Int) -> Void
    func makeCoordinator() -> Coordinator { Coordinator(onPageChange:onPageChange) }
    func makeUIView(context:Context) -> PDFView {
        let view=PDFView(); view.autoScales=true; view.displayMode = .singlePageContinuous; view.displayDirection = .vertical
        view.backgroundColor = UIColor(Palette.background)
        view.accessibilityLabel="Book PDF reader"
        context.coordinator.observer=NotificationCenter.default.addObserver(forName:.PDFViewPageChanged,object:view,queue:.main) { [weak view,weak coordinator=context.coordinator] _ in
            guard let view, let doc=view.document, let page=view.currentPage else { return }
            let index=doc.index(for:page)
            let count=doc.pageCount
            DispatchQueue.main.async { coordinator?.onPageChange?(index,count) }
        }
        return view
    }
    func updateUIView(_ view:PDFView,context:Context) {
        context.coordinator.onPageChange=onPageChange
        if context.coordinator.loadedURL != url {
            context.coordinator.loadedURL=url
            view.document=PDFDocument(url:url)
            if let document=view.document {
                let index=BookLibrary.openingPage(requestedPDFPage:initialPage,rememberedIndex:rememberedIndex,actualCount:document.pageCount,expectedCount:expectedCount,referenceMatches:referenceMatches)
                // PDFKit resets its scroll during layout, so navigate once SwiftUI supplies the bounds.
                DispatchQueue.main.async { [weak view, weak coordinator=context.coordinator] in
                    guard let view, coordinator?.loadedURL == url, view.document === document else { return }
                    view.layoutIfNeeded()
                    view.layoutDocumentView()
                    if let page=document.page(at:index) { view.go(to:page) }
                    coordinator?.onPageChange?(index,document.pageCount)
                }
            }
        }
        if let request=jumpRequest, context.coordinator.lastJump != request.id, let page=view.document?.page(at:request.index) {
            context.coordinator.lastJump=request.id; view.go(to:page)
        }
    }
    static func dismantleUIView(_ view:PDFView,coordinator:Coordinator) {
        coordinator.invalidate()
        view.document = nil
    }
    class Coordinator {
        var onPageChange:((Int,Int)->Void)?
        var observer:NSObjectProtocol?
        var loadedURL:URL?
        var lastJump:UUID?
        init(onPageChange:@escaping(Int,Int)->Void) { self.onPageChange=onPageChange }
        func invalidate() {
            if let observer { NotificationCenter.default.removeObserver(observer) }
            observer = nil; onPageChange = nil; loadedURL = nil; lastJump = nil
        }
        deinit { if let observer { NotificationCenter.default.removeObserver(observer) } }
    }
}

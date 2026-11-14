import SwiftUI
import Runestone
import TreeSitterPythonRunestone
import TreeSitterCPPRunestone
import TreeSitterCSharpRunestone
import TreeSitterGoRunestone
import TreeSitterJavaScriptRunestone
import TreeSitterOCamlRunestone
import TreeSitterRustRunestone

struct CodeEditor: UIViewRepresentable {
    @Binding var text: String
    let language: CodeLanguage
    func makeCoordinator() -> Coordinator { Coordinator(self) }
    func makeUIView(context: Context) -> TextView {
        let editor = TextView()
        editor.editorDelegate = context.coordinator
        editor.showLineNumbers = true
        editor.isFindInteractionEnabled = true
        editor.autocorrectionType = .no
        editor.autocapitalizationType = .none
        editor.smartQuotesType = .no
        editor.smartDashesType = .no
        editor.spellCheckingType = .no
        editor.backgroundColor = UIColor(Color(hex: "111B21"))
        editor.setState(makeState())
        editor.accessibilityLabel = "Code editor"
        return editor
    }
    func updateUIView(_ editor: TextView, context: Context) {
        context.coordinator.parent = self
        if context.coordinator.language != language {
            context.coordinator.language = language
            editor.setState(makeState())
        } else if editor.text != text { editor.text = text }
    }
    static func dismantleUIView(_ editor: TextView, coordinator: Coordinator) {
        editor.editorDelegate = nil
        editor.resignFirstResponder()
    }
    private func makeState() -> TextViewState {
        let grammar: TreeSitterLanguage?
        switch language {
        case .python, .pythonML: grammar = .python
        case .cpp: grammar = .cpp
        case .csharp: grammar = .cSharp
        case .go: grammar = .go
        case .javascript: grammar = .javaScript
        case .rust: grammar = .rust
        case .ocaml: grammar = .ocaml
        case .lean, .bash: grammar = nil
        }
        if let grammar { return TextViewState(text: text, theme: EditorTheme(), language: grammar) }
        return TextViewState(text: text, theme: EditorTheme())
    }
    class Coordinator: NSObject, TextViewDelegate {
        var parent: CodeEditor
        var language: CodeLanguage
        init(_ parent: CodeEditor) { self.parent = parent; language = parent.language }
        func textViewDidChange(_ textView: TextView) { parent.text = textView.text }
    }
}
final class EditorTheme: Runestone.Theme {
    let font = UIFont.monospacedSystemFont(ofSize: 15, weight: .regular)
    let textColor = UIColor(red: 0.84, green: 0.88, blue: 0.91, alpha: 1)
    let gutterBackgroundColor = UIColor(red: 0.065, green: 0.106, blue: 0.129, alpha: 1)
    let gutterHairlineColor = UIColor.clear
    let lineNumberColor = UIColor.systemGray
    let lineNumberFont = UIFont.monospacedSystemFont(ofSize: 12, weight: .regular)
    let selectedLineBackgroundColor = UIColor.white.withAlphaComponent(0.04)
    let selectedLinesLineNumberColor = UIColor.white
    let selectedLinesGutterBackgroundColor = UIColor.clear
    let invisibleCharactersColor = UIColor.systemGray
    let pageGuideHairlineColor = UIColor.clear
    let pageGuideBackgroundColor = UIColor.clear
    let markedTextBackgroundColor = UIColor.systemGray
    func textColor(for highlightName: String) -> UIColor? {
        if highlightName.hasPrefix("comment") { return .systemGray }
        if highlightName.hasPrefix("string") { return .systemGreen }
        if highlightName.hasPrefix("keyword") { return .systemPurple }
        if highlightName.hasPrefix("number") || highlightName.hasPrefix("constant") { return .systemOrange }
        if highlightName.hasPrefix("function") { return .systemTeal }
        if highlightName.hasPrefix("type") { return .systemYellow }
        return nil
    }
}

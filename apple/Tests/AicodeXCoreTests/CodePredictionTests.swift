import XCTest
@testable import AicodeXCore

final class CodePredictionTests: XCTestCase {

    // MARK: - LanguageCatalog

    func testCatalogHasWorldLanguages() {
        let catalog = LanguageCatalog()
        for name in ["python", "javascript", "typescript", "swift", "rust", "go",
                     "java", "c", "cpp", "csharp", "ruby", "php", "sql", "html"] {
            XCTAssertNotNil(catalog.get(name), name)
        }
    }

    func testVariantsAndFormats() {
        let catalog = LanguageCatalog()
        XCTAssertTrue(catalog.variants("swift").contains("swiftui"))
        XCTAssertTrue(catalog.formats("python").contains("source"))
    }

    func testByExtension() {
        let catalog = LanguageCatalog()
        XCTAssertEqual(catalog.byExtension("py")?.name, "python")
        XCTAssertEqual(catalog.byExtension(".rs")?.name, "rust")
        XCTAssertNil(catalog.byExtension("nope"))
    }

    // MARK: - CodePredictor

    func testPythonDetection() {
        let predictor = CodePredictor()
        let code = "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    return sorted(arr)\n"
        let pred = predictor.predict(code, filename: "s.py")
        XCTAssertEqual(pred.language, "python")
        XCTAssertEqual(pred.variant, "cpython")
        XCTAssertGreaterThan(pred.languageConfidence, 0.0)
        XCTAssertEqual(pred.algorithm, "sorting")
    }

    func testSwiftUIDetection() {
        let predictor = CodePredictor()
        let code = "import SwiftUI\nstruct V: View {\n  @State var n = 0\n  var body: some View { Text(\"hi\") }\n}\n"
        let pred = predictor.predict(code, filename: "V.swift")
        XCTAssertEqual(pred.language, "swift")
        XCTAssertEqual(pred.variant, "swiftui")
    }

    func testSQLDetection() {
        let predictor = CodePredictor()
        let pred = predictor.predict("SELECT name FROM users WHERE id = 1;", filename: "q.sql")
        XCTAssertEqual(pred.language, "sql")
        XCTAssertEqual(pred.format, "sql")
    }

    func testJSONFormatDetection() {
        let predictor = CodePredictor()
        let code = "import json\nlet data = json.loads(payload)\nprint(json.dumps(data))"
        let pred = predictor.predict(code, filename: "p.py")
        XCTAssertEqual(pred.format, "json")
    }

    func testEmptySubmission() {
        let predictor = CodePredictor()
        let pred = predictor.predict("   ")
        XCTAssertEqual(pred.language, "unknown")
        XCTAssertEqual(pred.languageConfidence, 0.0)
        XCTAssertTrue(pred.rationale.contains("Empty"))
    }

    func testExtensionHintBoostsLanguage() {
        let predictor = CodePredictor()
        let pred = predictor.predict("print(1)", filename: "script.py")
        XCTAssertEqual(pred.language, "python")
    }

    // MARK: - ProviderKind coverage

    func testNewProviderKindsPresent() {
        let kinds = Set(ProviderKind.allCases.map { $0.rawValue })
        XCTAssertTrue(kinds.isSuperset(of: [
            "grok4", "openrouter", "gemini", "chatgptcodex", "chatgpt6luna",
            "claudecoder", "codex", "minstrel", "kodex", "xcode", "generic",
        ]))
    }
}

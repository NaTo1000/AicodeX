import XCTest
@testable import AicodeXCore

final class AicodeXCoreTests: XCTestCase {

    // MARK: - SHA-256

    func testSHA256Empty() {
        XCTAssertEqual(
            HandBrakeChecker.sha256Hex(Data()),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
    }

    func testSHA256ABC() {
        XCTAssertEqual(
            HandBrakeChecker.sha256Hex(Data("abc".utf8)),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )
    }

    func testSHA256MultiBlock() {
        let message = String(repeating: "a", count: 1_000_000)
        XCTAssertEqual(
            HandBrakeChecker.sha256Hex(Data(message.utf8)),
            "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"
        )
    }

    // MARK: - HandBrakeChecker

    func testVersionSummaryParity() {
        let checker = HandBrakeChecker()
        let summary = checker.versionSummary()
        XCTAssertTrue(summary.contains("1.10.2"))
        XCTAssertTrue(summary.contains(HandBrakeChecker.latestRelease.downloadURL.absoluteString))
    }

    func testInfoDictionary() {
        let info = HandBrakeChecker().info()
        XCTAssertEqual(info["version"], "1.10.2")
        XCTAssertEqual(info["sha256"], HandBrakeChecker.latestRelease.sha256)
        XCTAssertNotNil(info["download_url"])
    }

    func testVerifyMatchingData() async throws {
        let payload = Data("handbrake".utf8)
        let release = HandBrakeRelease(
            version: "0.0.0",
            downloadURL: URL(string: "https://example.com/x")!,
            sha256: HandBrakeChecker.sha256Hex(payload)
        )
        let checker = HandBrakeChecker { _ in payload }
        XCTAssertTrue(checker.verify(data: payload, for: release))
        let downloaded = try await checker.downloadAndVerify(release)
        XCTAssertEqual(downloaded, payload)
    }

    func testDownloadChecksumMismatchThrows() async {
        let release = HandBrakeRelease(
            version: "0.0.0",
            downloadURL: URL(string: "https://example.com/x")!,
            sha256: String(repeating: "0", count: 64)
        )
        let checker = HandBrakeChecker { _ in Data("tampered".utf8) }
        do {
            _ = try await checker.downloadAndVerify(release)
            XCTFail("Expected checksumMismatch")
        } catch let HandBrakeChecker.HandBrakeError.checksumMismatch(expected, actual) {
            XCTAssertEqual(expected, release.sha256)
            XCTAssertEqual(actual, HandBrakeChecker.sha256Hex(Data("tampered".utf8)))
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }

    // MARK: - Settings

    func testDefaultSettingsMatchPythonConfig() {
        let s = AppSettings.default
        XCTAssertEqual(s.window.width, 400)
        XCTAssertEqual(s.window.height, 600)
        XCTAssertEqual(s.window.opacity, 0.95, accuracy: 0.0001)
        XCTAssertEqual(s.theme.background, "#2b2b2b")
        XCTAssertEqual(s.theme.accent, "#007acc")
        XCTAssertEqual(s.snippets.count, 4)
        XCTAssertTrue(s.features.handbrakeIntegration)
        XCTAssertEqual(s.hotkeys.count, 3)
    }

    func testOpacityClamping() {
        XCTAssertEqual(WindowSettings.clampOpacity(0.1), 0.5)
        XCTAssertEqual(WindowSettings.clampOpacity(1.5), 1.0)
        XCTAssertEqual(WindowSettings.clampOpacity(0.75), 0.75)
    }

    func testSettingsRoundTrip() throws {
        let tmp = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathComponent("settings.json")
        let store = SettingsStore(url: tmp)
        store.updateOpacity(0.8)
        try store.save()

        let reloaded = SettingsStore(url: tmp)
        XCTAssertEqual(reloaded.settings.window.opacity, 0.8, accuracy: 0.0001)
        XCTAssertEqual(reloaded.settings.snippets.count, 4)

        try? FileManager.default.removeItem(at: tmp.deletingLastPathComponent())
    }

    func testHotkeyLookup() {
        let store = SettingsStore(settings: .default)
        XCTAssertEqual(store.hotkey(for: .toggleOverlay)?.keyCombo, "ctrl+shift+o")
        XCTAssertEqual(store.hotkey(for: .insertSnippet)?.keyCombo, "ctrl+shift+s")
        XCTAssertEqual(store.hotkey(for: .formatCode)?.keyCombo, "ctrl+shift+f")
    }

    // MARK: - SnippetLibrary

    func testSnippetSearchFilters() {
        let lib = SnippetLibrary()
        XCTAssertEqual(lib.search("").count, 4)
        XCTAssertEqual(lib.search("python").count, 3)
        XCTAssertEqual(lib.search("javascript").count, 1)
        XCTAssertEqual(lib.search("nonexistent-xyz").count, 0)
    }

    func testSnippetLanguages() {
        let lib = SnippetLibrary()
        XCTAssertEqual(lib.languages, ["javascript", "python"])
        XCTAssertEqual(lib.snippets(forLanguage: "PYTHON").count, 3)
    }

    func testSnippetAddRemove() {
        var lib = SnippetLibrary(snippets: [])
        let snippet = Snippet(name: "X", code: "y", language: "swift")
        lib.add(snippet)
        XCTAssertEqual(lib.snippets.count, 1)
        lib.remove(id: snippet.id)
        XCTAssertTrue(lib.snippets.isEmpty)
    }

    // MARK: - QuickAction

    func testQuickActionDefaultsMirrorPython() {
        let titles = QuickAction.defaults.map(\.title)
        XCTAssertTrue(titles.contains("Check HandBrake Version"))
        XCTAssertTrue(titles.contains("Format Code"))
        XCTAssertTrue(titles.contains("Generate Docstring"))
        XCTAssertTrue(titles.contains("Refactor Selection"))
    }
}

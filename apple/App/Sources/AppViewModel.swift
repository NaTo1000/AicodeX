import Foundation
import Combine
import AicodeXCore

/// Observable view-model backing the SwiftUI app.
///
/// Wraps the pure-Foundation `SettingsStore`/`SnippetLibrary` from `AicodeXCore`
/// and exposes UI-friendly published state plus clipboard/handbrake actions.
@MainActor
final class AppViewModel: ObservableObject {
    @Published private(set) var settings: AppSettings
    @Published var searchText: String = ""
    @Published var selectedSnippet: Snippet?
    @Published var statusMessage: String?
    @Published var overlayVisible: Bool = true

    private let store: SettingsStore
    private(set) var library: SnippetLibrary
    private let handbrake = HandBrakeChecker()

    init(store: SettingsStore) {
        self.store = store
        self.settings = store.settings
        self.library = SnippetLibrary(snippets: store.settings.snippets)
    }

    /// Convenience initializer that resolves a platform-appropriate on-disk location.
    convenience init() {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        let url = base
            .appendingPathComponent("AicodeX", isDirectory: true)
            .appendingPathComponent("settings.json")
        self.init(store: SettingsStore(url: url))
    }

    // MARK: - Snippets

    var filteredSnippets: [Snippet] {
        library.search(searchText)
    }

    func copyToPasteboard(_ text: String) {
        PlatformPasteboard.copy(text)
        statusMessage = "Copied to clipboard"
    }

    func insertSnippet(_ snippet: Snippet) {
        copyToPasteboard(snippet.code)
        statusMessage = "Inserted snippet: \(snippet.name)"
    }

    // MARK: - Actions

    func run(_ action: QuickAction) {
        switch action.kind {
        case .checkHandbrake:
            statusMessage = handbrake.versionSummary()
        case .formatCode:
            statusMessage = "Format code action"
        case .generateDocstring:
            statusMessage = "Generate docstring action"
        case .refactorSelection:
            statusMessage = "Refactor action"
        }
    }

    // MARK: - Settings

    func setOpacity(_ value: Double) {
        store.updateOpacity(value)
        persist()
    }

    func toggleOverlay() {
        overlayVisible.toggle()
    }

    func persist() {
        settings = store.settings
        library = SnippetLibrary(snippets: settings.snippets)
        try? store.save()
    }
}

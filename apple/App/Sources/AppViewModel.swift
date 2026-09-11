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
    private let analyzer = IncomingDataAnalyzer()
    private var matcher = SolutionMatcher()

    /// The assistant persona driving the UI's presentation style.
    @Published private(set) var persona: PersonaStyle = .default

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

    // MARK: - Assistant (Persona & Analysis)

    /// Analyse incoming text, match a performance solution (or explain why none
    /// fits), and surface the result as a status message. Returns the match so
    /// an Assistant view can render the full explanation.
    @discardableResult
    func analyzeIncoming(_ text: String) -> SolutionMatch {
        let profile = analyzer.analyze(text)
        let match = matcher.match(profile)
        if match.matched {
            statusMessage = "Solution: \(match.solution)"
        } else {
            statusMessage = "No solution: \(match.explanation)"
        }
        return match
    }

    /// Fine-tune the assistant/UI persona style.
    func fineTunePersona(name: String? = nil, tone: String? = nil, traits: [String: Double] = [:]) {
        persona = persona.merging(name: name, tone: tone, traits: traits)
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

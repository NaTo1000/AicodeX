import Foundation

/// Loads and persists `AppSettings` as JSON, a Swift port of the Python `Config` class.
///
/// Pure Foundation so it runs on Linux for CI tests. On Apple platforms the app layer
/// supplies a URL inside the app's Application Support / Documents container.
public final class SettingsStore {
    public private(set) var settings: AppSettings
    public let url: URL

    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    /// - Parameters:
    ///   - url: Location of the JSON settings file.
    ///   - loadDefaultsIfMissing: When `true` (default), missing/unreadable files fall back to defaults.
    public init(url: URL, loadDefaultsIfMissing: Bool = true) {
        self.url = url
        self.encoder = JSONEncoder()
        self.encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        self.decoder = JSONDecoder()

        if loadDefaultsIfMissing,
           let data = try? Data(contentsOf: url),
           let loaded = try? decoder.decode(AppSettings.self, from: data) {
            self.settings = loaded
        } else {
            self.settings = .default
        }
    }

    /// In-memory store seeded with explicit settings (used by tests and previews).
    public init(settings: AppSettings) {
        self.url = URL(fileURLWithPath: "/dev/null")
        self.settings = settings
        self.encoder = JSONEncoder()
        self.encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        self.decoder = JSONDecoder()
    }

    /// Persist current settings to disk, creating intermediate directories as needed.
    @discardableResult
    public func save() throws -> Data {
        let data = try encoder.encode(settings)
        let directory = url.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        try data.write(to: url, options: .atomic)
        return data
    }

    /// Reload settings from disk. Returns `false` when the file cannot be read/decoded.
    @discardableResult
    public func reload() -> Bool {
        guard let data = try? Data(contentsOf: url),
              let loaded = try? decoder.decode(AppSettings.self, from: data) else {
            return false
        }
        settings = loaded
        return true
    }

    public func hotkey(for action: Hotkey.Action) -> Hotkey? {
        settings.hotkeys.first { $0.action == action }
    }

    public func updateOpacity(_ value: Double) {
        settings.window.opacity = WindowSettings.clampOpacity(value)
    }
}

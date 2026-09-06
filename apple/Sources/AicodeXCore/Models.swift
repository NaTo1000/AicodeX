import Foundation

/// A reusable code snippet, ported from the Python `config.py` snippet model.
public struct Snippet: Codable, Equatable, Identifiable, Hashable {
    public var id: UUID
    public var name: String
    public var code: String
    public var language: String

    public init(id: UUID = UUID(), name: String, code: String, language: String = "plaintext") {
        self.id = id
        self.name = name
        self.code = code
        self.language = language
    }
}

/// A one-tap quick action surfaced in the Actions tab.
public struct QuickAction: Codable, Equatable, Identifiable, Hashable {
    public enum Kind: String, Codable, CaseIterable {
        case checkHandbrake
        case formatCode
        case generateDocstring
        case refactorSelection
    }

    public var id: Kind { kind }
    public let kind: Kind
    public let title: String
    public let systemImage: String

    public init(kind: Kind, title: String, systemImage: String) {
        self.kind = kind
        self.title = title
        self.systemImage = systemImage
    }

    /// The default set of quick actions, mirroring the Python overlay's action list.
    public static let defaults: [QuickAction] = [
        QuickAction(kind: .checkHandbrake, title: "Check HandBrake Version", systemImage: "opticaldisc"),
        QuickAction(kind: .formatCode, title: "Format Code", systemImage: "wand.and.stars"),
        QuickAction(kind: .generateDocstring, title: "Generate Docstring", systemImage: "doc.text"),
        QuickAction(kind: .refactorSelection, title: "Refactor Selection", systemImage: "arrow.triangle.branch")
    ]
}

/// A configurable keyboard shortcut.
public struct Hotkey: Codable, Equatable, Identifiable, Hashable {
    public enum Action: String, Codable, CaseIterable {
        case toggleOverlay = "toggle_overlay"
        case insertSnippet = "insert_snippet"
        case formatCode = "format_code"
    }

    public var id: Action { action }
    public let action: Action
    public var keyCombo: String

    public init(action: Action, keyCombo: String) {
        self.action = action
        self.keyCombo = keyCombo
    }

    /// Human-readable label for the action (used in Settings).
    public var displayName: String {
        switch action {
        case .toggleOverlay: return "Toggle Overlay"
        case .insertSnippet: return "Insert Snippet"
        case .formatCode: return "Format Code"
        }
    }
}

/// App color theme, expressed as hex strings so it round-trips with the JSON config.
public struct AppTheme: Codable, Equatable, Hashable {
    public var background: String
    public var foreground: String
    public var accent: String

    public init(background: String = "#2b2b2b", foreground: String = "#ffffff", accent: String = "#007acc") {
        self.background = background
        self.foreground = foreground
        self.accent = accent
    }
}

/// Window configuration for the overlay panel.
public struct WindowSettings: Codable, Equatable, Hashable {
    public var width: Double
    public var height: Double
    public var xPosition: Double
    public var yPosition: Double
    /// Window opacity in the inclusive range 0.5 ... 1.0.
    public var opacity: Double

    public init(width: Double = 400, height: Double = 600, xPosition: Double = 100, yPosition: Double = 100, opacity: Double = 0.95) {
        self.width = width
        self.height = height
        self.xPosition = xPosition
        self.yPosition = yPosition
        self.opacity = WindowSettings.clampOpacity(opacity)
    }

    /// Clamps opacity to the platform-supported overlay range.
    public static func clampOpacity(_ value: Double) -> Double {
        min(max(value, 0.5), 1.0)
    }
}

/// Feature flags matching the Python `features` config block.
public struct FeatureFlags: Codable, Equatable, Hashable {
    public var handbrakeIntegration: Bool
    public var autoFormat: Bool
    public var snippetSuggestions: Bool

    public init(handbrakeIntegration: Bool = true, autoFormat: Bool = true, snippetSuggestions: Bool = true) {
        self.handbrakeIntegration = handbrakeIntegration
        self.autoFormat = autoFormat
        self.snippetSuggestions = snippetSuggestions
    }
}

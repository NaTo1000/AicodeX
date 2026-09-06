import Foundation

/// Root application settings, a Swift port of `config/default_settings.json`.
public struct AppSettings: Codable, Equatable {
    public var window: WindowSettings
    public var hotkeys: [Hotkey]
    public var snippets: [Snippet]
    public var theme: AppTheme
    public var features: FeatureFlags

    public init(
        window: WindowSettings = WindowSettings(),
        hotkeys: [Hotkey] = AppSettings.defaultHotkeys,
        snippets: [Snippet] = AppSettings.defaultSnippets,
        theme: AppTheme = AppTheme(),
        features: FeatureFlags = FeatureFlags()
    ) {
        self.window = window
        self.hotkeys = hotkeys
        self.snippets = snippets
        self.theme = theme
        self.features = features
    }

    public static let defaultHotkeys: [Hotkey] = [
        Hotkey(action: .toggleOverlay, keyCombo: "ctrl+shift+o"),
        Hotkey(action: .insertSnippet, keyCombo: "ctrl+shift+s"),
        Hotkey(action: .formatCode, keyCombo: "ctrl+shift+f")
    ]

    public static let defaultSnippets: [Snippet] = [
        Snippet(
            name: "Python Function",
            code: "def function_name(param):\n    \"\"\"Docstring\"\"\"\n    pass",
            language: "python"
        ),
        Snippet(
            name: "JavaScript Function",
            code: "function functionName(param) {\n    // Comment\n    return value;\n}",
            language: "javascript"
        ),
        Snippet(
            name: "Python Class",
            code: "class ClassName:\n    \"\"\"Class docstring\"\"\"\n    \n    def __init__(self):\n        pass",
            language: "python"
        ),
        Snippet(
            name: "Try-Except Block",
            code: "try:\n    # Code that might raise an exception\n    pass\nexcept Exception as e:\n    # Handle exception\n    print(f\"Error: {e}\")",
            language: "python"
        )
    ]

    public static let `default` = AppSettings()
}

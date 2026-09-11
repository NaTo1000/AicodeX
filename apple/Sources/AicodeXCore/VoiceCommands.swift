import Foundation

/// A parsed voice command: an intent plus its free-text argument.
///
/// Pure Foundation so it compiles and tests on Linux. Speech recognition /
/// synthesis are platform concerns handled in the app layer; this type only
/// models the parsed command.
public struct VoiceCommand: Equatable {
    public enum Intent: String, CaseIterable {
        case analyze
        case format
        case insertSnippet
        case preview
        case interlude
        case stopInterlude
        case toggleOverlay
        case help
        case unknown
    }

    public let intent: Intent
    public let argument: String
    public let raw: String

    public init(intent: Intent, argument: String = "", raw: String = "") {
        self.intent = intent
        self.argument = argument.trimmingCharacters(in: .whitespaces)
        self.raw = raw.trimmingCharacters(in: .whitespaces)
    }
}

/// Parses an utterance into a ``VoiceCommand``.
public struct CommandParser {
    public var wakeWord: String
    public var commandPrefix: String

    public init(wakeWord: String = "aicodex", commandPrefix: String = "") {
        self.wakeWord = wakeWord.trimmingCharacters(in: .whitespaces).lowercased()
        self.commandPrefix = commandPrefix.trimmingCharacters(in: .whitespaces)
    }

    /// Verb/keyword → intent mapping (matched case-insensitively on prefixes).
    private static let intentKeywords: [(VoiceCommand.Intent, [String])] = [
        (.analyze, ["analyze", "analyse", "analyze this", "assess", "profile", "evaluate"]),
        (.format, ["format", "pretty", "beautify", "lint"]),
        (.insertSnippet, ["insert snippet", "insert", "snippet", "paste", "template"]),
        (.preview, ["preview", "run", "execute", "sandbox", "try"]),
        (.interlude, ["interlude", "brainstorm", "whiteboard", "think aloud", "pause code"]),
        (.stopInterlude, ["resume", "continue code", "end interlude", "back to code", "stop interlude"]),
        (.toggleOverlay, ["toggle overlay", "hide overlay", "show overlay", "toggle"]),
        (.help, ["help", "commands", "what can you do", "usage"]),
    ]

    public func parse(_ utterance: String) -> VoiceCommand {
        var text = utterance.trimmingCharacters(in: .whitespaces)
        if !commandPrefix.isEmpty, text.hasPrefix(commandPrefix) {
            text = String(text.dropFirst(commandPrefix.count)).trimmingCharacters(in: .whitespaces)
        }
        if !wakeWord.isEmpty, text.lowercased().hasPrefix(wakeWord) {
            var dropped = String(text.dropFirst(wakeWord.count))
            while let first = dropped.first, first == " " || first == "," || first == ":" {
                dropped.removeFirst()
            }
            text = dropped
        }
        guard !text.isEmpty else { return VoiceCommand(intent: .unknown, raw: utterance) }

        let lowered = text.lowercased()
        var best: (intent: VoiceCommand.Intent, keyword: String)? = nil
        for (intent, keywords) in CommandParser.intentKeywords {
            for kw in keywords where lowered.hasPrefix(kw) {
                if best == nil || kw.count > best!.keyword.count {
                    best = (intent, kw)
                }
            }
        }
        guard let match = best else {
            return VoiceCommand(intent: .unknown, argument: text, raw: utterance)
        }
        var argument = String(text.dropFirst(match.keyword.count))
        while let first = argument.first, first == " " || first == "," || first == ":" {
            argument.removeFirst()
        }
        return VoiceCommand(intent: match.intent, argument: argument, raw: utterance)
    }
}

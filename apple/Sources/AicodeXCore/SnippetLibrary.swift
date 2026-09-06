import Foundation

/// In-memory snippet collection with search and language filtering.
public struct SnippetLibrary {
    public private(set) var snippets: [Snippet]

    public init(snippets: [Snippet] = AppSettings.defaultSnippets) {
        self.snippets = snippets
    }

    /// Case-insensitive search across snippet name, code, and language.
    public func search(_ query: String) -> [Snippet] {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return snippets }
        let lowered = trimmed.lowercased()
        return snippets.filter {
            $0.name.lowercased().contains(lowered)
                || $0.code.lowercased().contains(lowered)
                || $0.language.lowercased().contains(lowered)
        }
    }

    /// Snippets for a specific language (case-insensitive).
    public func snippets(forLanguage language: String) -> [Snippet] {
        snippets.filter { $0.language.caseInsensitiveCompare(language) == .orderedSame }
    }

    /// Distinct set of languages present in the library, sorted alphabetically.
    public var languages: [String] {
        Array(Set(snippets.map { $0.language.lowercased() })).sorted()
    }

    public mutating func add(_ snippet: Snippet) {
        snippets.append(snippet)
    }

    public mutating func remove(id: UUID) {
        snippets.removeAll { $0.id == id }
    }
}

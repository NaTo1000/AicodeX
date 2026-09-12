import Foundation

/// A normalised text response from a model provider.
public struct ProviderResponse: Equatable {
    public var provider: String
    public var model: String
    public var text: String

    public init(provider: String, model: String, text: String) {
        self.provider = provider
        self.model = model
        self.text = text
    }
}

/// Errors a provider can raise.
public enum ProviderError: Error, Equatable {
    case disabled(String)
    case notConfigured(String)
    case requestFailed(String)
}

/// An AI model provider. Implementations must be offline-testable — network
/// access is injected — and must resolve API keys from the environment by name
/// without persisting them.
public protocol ModelProvider {
    var name: String { get }
    var kind: String { get }
    var isEnabled: Bool { get }

    /// Generate a text response for `prompt` on `model`.
    func generate(model: String, prompt: String) throws -> ProviderResponse
}

/// The supported provider kinds (adapters). Endpoint/key wiring is config
/// concern; only the *kind* is enumerated here so the registry can validate.
public enum ProviderKind: String, CaseIterable {
    case huggingface
    case northflank
    case bentoml
    case replicate
    case modal
    case lambdalabs
    case together
    case runpod
    case grok4
    case openrouter
    case gemini
    case chatgptcodex
    case chatgpt6luna
    case claudecoder
    case codex
    case minstrel
    case kodex
    case xcode
    case generic
    case mock
}

/// Configuration describing one provider (from the `interaction.providers`
/// config block). The API key is referenced by environment-variable *name*.
public struct ProviderConfig: Codable, Equatable {
    public var name: String
    public var kind: String
    public var endpoint: String
    public var apiKeyEnv: String?
    public var enabled: Bool

    public init(name: String, kind: String, endpoint: String, apiKeyEnv: String? = nil, enabled: Bool = true) {
        self.name = name
        self.kind = kind
        self.endpoint = endpoint
        self.apiKeyEnv = apiKeyEnv
        self.enabled = enabled
    }
}

/// A deterministic, offline provider for tests and offline use.
public struct MockProvider: ModelProvider {
    public let name: String
    public let kind: String = "mock"
    public let isEnabled: Bool = true
    private let canned: String?

    public init(name: String = "mock", response: String? = nil) {
        self.name = name
        self.canned = response
    }

    public func generate(model: String, prompt: String) throws -> ProviderResponse {
        let text = canned ?? "[mock:\(model)] \(prompt.prefix(120))"
        return ProviderResponse(provider: name, model: model, text: text)
    }
}

/// A name → provider collection with offline/mock fallback resolution.
public struct ProviderRegistry {
    private var providers: [String: ModelProvider] = [:]
    public let fallback: ModelProvider

    public init(providers: [ModelProvider] = [], fallback: ModelProvider = MockProvider()) {
        self.fallback = fallback
        for p in providers { self.providers[p.name] = p }
    }

    public func get(_ name: String) -> ModelProvider? { providers[name] }

    public var names: [String] { Array(providers.keys) }

    public var enabledProviders: [ModelProvider] { providers.values.filter { $0.isEnabled } }

    /// Pick a provider: the named one if enabled, else the first enabled, else
    /// the mock fallback — so callers always get a response.
    public func choose(name: String? = nil) -> ModelProvider {
        if let name = name, let chosen = providers[name], chosen.isEnabled {
            return chosen
        }
        return enabledProviders.first ?? fallback
    }
}

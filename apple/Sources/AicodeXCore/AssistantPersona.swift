import Foundation

/// The default graphical personality axes the engine scores against.
public let defaultTraitAxes: [String] = ["analytical", "creative", "driver", "amiable"]

/// A configurable tone/personality profile expressed over graphical trait axes.
///
/// Pure Foundation so it compiles and tests on Linux. "Fine-tuning" the
/// assistant / UI personnel style is simply loading or merging a persona.
public struct PersonaStyle: Codable, Equatable, Hashable {
    public var name: String
    public var tone: String
    /// Maps an axis name to a 0.0-1.0 intensity.
    public var traits: [String: Double]

    public init(name: String = "AicodeX Assistant", tone: String = "analytical", traits: [String: Double] = [:]) {
        self.name = name
        self.tone = tone
        self.traits = traits.mapValues { min(max($0, 0.0), 1.0) }
    }

    public static let `default` = PersonaStyle(
        name: "AicodeX Assistant",
        tone: "analytical",
        traits: ["analytical": 0.9, "creative": 0.4, "driver": 0.6, "amiable": 0.7]
    )

    public func trait(_ axis: String, default defaultValue: Double = 0.0) -> Double {
        traits[axis] ?? defaultValue
    }

    /// `(axis, value)` pairs sorted by intensity, descending.
    public func dominantTraits(axes: [String]? = nil) -> [(axis: String, value: Double)] {
        var pairs = traits.map { ($0.key, $0.value) }
        if let axes = axes {
            let wanted = Set(axes)
            pairs = pairs.filter { wanted.contains($0.0) }
        }
        return pairs.sorted { $0.1 > $1.1 }
    }

    /// Return a new persona fine-tuned by the supplied overrides.
    public func merging(name: String? = nil, tone: String? = nil, traits: [String: Double] = [:]) -> PersonaStyle {
        var merged = self.traits
        for (axis, value) in traits {
            merged[axis] = min(max(value, 0.0), 1.0)
        }
        return PersonaStyle(name: name ?? self.name, tone: tone ?? self.tone, traits: merged)
    }
}

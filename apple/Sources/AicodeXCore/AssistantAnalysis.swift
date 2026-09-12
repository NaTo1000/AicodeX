import Foundation

/// A scored personality profile for a piece of incoming data.
public struct TraitProfile: Codable, Equatable {
    public var scores: [String: Double]
    public var confidence: Double
    public var tokenCount: Int

    public init(scores: [String: Double], confidence: Double, tokenCount: Int = 0) {
        self.scores = scores
        self.confidence = min(max(confidence, 0.0), 1.0)
        self.tokenCount = tokenCount
    }

    /// The highest-scoring axis, or an empty string when the profile is empty.
    public var dominant: String {
        scores.max { $0.value < $1.value }?.key ?? ""
    }

    /// `(axis, score)` pairs sorted by score, descending.
    public var dominantTraits: [(axis: String, score: Double)] {
        scores.sorted { $0.value > $1.value }.map { ($0.key, $0.value) }
    }
}

/// Analyses incoming text/data against the graphical personality axes.
///
/// Deliberately transparent (bag-of-signals) so its scores are explainable,
/// matching the engine's "show the user why" requirement. Pure Foundation.
public struct IncomingDataAnalyzer {
    /// Keyword signals per axis.
    public static let axisSignals: [String: [String]] = [
        "analytical": ["analy", "data", "logic", "metric", "measure", "benchmark", "profile", "evidence", "statistic", "reason", "prove", "test", "debug", "root cause", "quantif", "research"],
        "creative": ["idea", "creat", "design", "imagine", "innovat", "brainstorm", "novel", "prototype", "art", "vision", "invent", "explore", "what if"],
        "driver": ["deadline", "asap", "ship", "result", "goal", "fast", "now", "urgent", "deliver", "win", "decide", "action", "cut scope", "move"],
        "amiable": ["team", "help", "together", "support", "feel", "stakeholder", "align", "pair", "collaborat", "listen", "people", "consensus", "share"],
    ]

    public let axes: [String]
    private let signals: [String: [String]]

    public init(axes: [String] = defaultTraitAxes, signals: [String: [String]] = [:]) {
        self.axes = axes
        var merged: [String: [String]] = [:]
        for axis in axes {
            merged[axis] = signals[axis] ?? IncomingDataAnalyzer.axisSignals[axis] ?? []
        }
        self.signals = merged
    }

    public func analyze(_ data: Any?) -> TraitProfile {
        let text = IncomingDataAnalyzer.toText(data).lowercased()
        let tokens = text.split { !$0.isLetter && $0 != "-" && $0 != "'" }
        let tokenCount = tokens.count

        var raw: [String: Double] = [:]
        for axis in axes {
            let sigs = signals[axis] ?? []
            let hits = sigs.reduce(0) { $0 + (text.contains($1) ? 1 : 0) }
            raw[axis] = sigs.isEmpty ? 0.0 : Double(hits) / Double(sigs.count)
        }

        guard tokenCount > 0 else {
            return TraitProfile(scores: Dictionary(uniqueKeysWithValues: axes.map { ($0, 0.0) }), confidence: 0.0, tokenCount: 0)
        }
        let total = raw.values.reduce(0, +)
        guard total > 0 else {
            return TraitProfile(scores: Dictionary(uniqueKeysWithValues: axes.map { ($0, 0.0) }), confidence: 0.0, tokenCount: tokenCount)
        }

        let scores = raw.mapValues { $0 / total }
        let hitAxes = raw.values.filter { $0 > 0 }.count
        let density = min(1.0, total)
        let lengthBonus = min(0.3, Double(tokenCount) / 100.0)
        let coverageBonus = min(0.4, Double(hitAxes) / Double(max(1, axes.count)) * 0.4)
        let confidence = min(1.0, 0.3 + density * 0.3 + lengthBonus + coverageBonus)
        return TraitProfile(scores: scores, confidence: (confidence * 10000).rounded() / 10000, tokenCount: tokenCount)
    }

    /// Flatten strings / collections / dictionaries to plain text.
    public static func toText(_ data: Any?) -> String {
        guard let data = data else { return "" }
        if let s = data as? String { return s }
        if let dict = data as? [String: Any] {
            return dict.map { toText($0.key) + " " + toText($0.value) }
                .filter { !$0.isEmpty }.joined(separator: " ")
        }
        if let arr = data as? [Any] {
            return arr.map { toText($0) }.filter { !$0.isEmpty }.joined(separator: " ")
        }
        return String(describing: data)
    }
}

/// A single performance solution keyed by the traits it serves.
public struct KnowledgeEntry: Codable, Equatable, Identifiable {
    public var id: String
    public var solution: String
    public var traits: [String: Double]
    public var minConfidence: Double

    public init(id: String, solution: String, traits: [String: Double], minConfidence: Double = 0.5) {
        self.id = id
        self.solution = solution
        self.traits = traits
        self.minConfidence = min(max(minConfidence, 0.0), 1.0)
    }

    /// How well a profile satisfies this entry's trait requirements (0..1).
    public func fitScore(_ profile: TraitProfile) -> Double {
        guard !traits.isEmpty else { return 0.0 }
        var total = 0.0
        for (axis, req) in traits {
            let have = profile.scores[axis] ?? 0.0
            total += req > 0 ? min(have, req) / req : 1.0
        }
        return total / Double(traits.count)
    }

    /// Required traits the profile falls short on, with the shortfall.
    public func unmetTraits(_ profile: TraitProfile) -> [String: (required: Double, actual: Double)] {
        var gaps: [String: (Double, Double)] = [:]
        for (axis, req) in traits {
            let have = profile.scores[axis] ?? 0.0
            if have < req { gaps[axis] = (req, (have * 10000).rounded() / 10000) }
        }
        return gaps
    }
}

/// The result of matching: either a solution or a reasoned explanation.
public struct SolutionMatch: Equatable {
    public var matched: Bool
    public var entry: KnowledgeEntry?
    public var score: Double
    public var explanation: String
    public var confidence: Double

    public var solution: String { entry?.solution ?? "" }
}

/// Matches trait profiles against a knowledge base, explaining misses.
public struct SolutionMatcher {
    public let knowledgeBase: [KnowledgeEntry]

    public init(knowledgeBase: [KnowledgeEntry] = []) {
        self.knowledgeBase = knowledgeBase
    }

    public func match(_ profile: TraitProfile) -> SolutionMatch {
        guard !knowledgeBase.isEmpty else {
            return SolutionMatch(
                matched: false, entry: nil, score: 0.0,
                explanation: "No performance solutions are configured in the knowledge base, so there is nothing to match this profile against.",
                confidence: profile.confidence
            )
        }
        let ranked = knowledgeBase
            .map { (score: $0.fitScore(profile), entry: $0) }
            .sorted { $0.score > $1.score }
        let best = ranked[0]

        if profile.confidence < best.entry.minConfidence {
            return SolutionMatch(
                matched: false, entry: best.entry, score: best.score,
                explanation: String(format: "The closest solution '%@' needs confidence >= %.2f, but the analysis only reached %.2f. Provide more specific input so the engine can justify a solution.", best.entry.id, best.entry.minConfidence, profile.confidence),
                confidence: profile.confidence
            )
        }
        let gaps = best.entry.unmetTraits(profile)
        if !gaps.isEmpty {
            let gapText = gaps.sorted { $0.key < $1.key }
                .map { String(format: "'%@' needs %.2f but profile has %.2f", $0.key, $0.value.required, $0.value.actual) }
                .joined(separator: "; ")
            return SolutionMatch(
                matched: false, entry: best.entry, score: best.score,
                explanation: String(format: "No configured solution fully fits. Closest is '%@' (fit %.2f); unmet traits: %@.", best.entry.id, best.score, gapText),
                confidence: profile.confidence
            )
        }
        return SolutionMatch(
            matched: true, entry: best.entry, score: best.score,
            explanation: String(format: "Matched '%@' (fit %.2f, confidence %.2f).", best.entry.id, best.score, profile.confidence),
            confidence: profile.confidence
        )
    }
}

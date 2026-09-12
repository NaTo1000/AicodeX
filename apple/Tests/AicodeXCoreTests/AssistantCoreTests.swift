import XCTest
@testable import AicodeXCore

final class AssistantCoreTests: XCTestCase {

    // MARK: - PersonaStyle

    func testDefaultPersona() {
        let p = PersonaStyle.default
        XCTAssertEqual(p.tone, "analytical")
        XCTAssertEqual(p.trait("analytical"), 0.9, accuracy: 0.0001)
    }

    func testTraitsClamped() {
        let p = PersonaStyle(traits: ["analytical": 5.0, "creative": -2.0])
        XCTAssertEqual(p.trait("analytical"), 1.0)
        XCTAssertEqual(p.trait("creative"), 0.0)
    }

    func testMergeFineTunesSingleAxis() {
        let base = PersonaStyle.default
        let tuned = base.merging(tone: "creative", traits: ["creative": 0.95])
        XCTAssertEqual(tuned.tone, "creative")
        XCTAssertEqual(tuned.trait("creative"), 0.95)
        // Untouched axes preserved; original unchanged.
        XCTAssertEqual(tuned.trait("analytical"), base.trait("analytical"))
        XCTAssertEqual(base.trait("creative"), 0.4)
    }

    func testDominantTraitsSorted() {
        let p = PersonaStyle(traits: ["a": 0.2, "b": 0.9, "c": 0.5])
        XCTAssertEqual(p.dominantTraits().map { $0.axis }, ["b", "c", "a"])
    }

    // MARK: - IncomingDataAnalyzer

    func testAnalyticalTextDominant() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("analyze the benchmark data and measure the root cause with evidence")
        XCTAssertEqual(profile.dominant, "analytical")
        XCTAssertGreaterThan(profile.confidence, 0.0)
    }

    func testDriverTextDominant() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("ship it asap, deliver results, decide now")
        XCTAssertEqual(profile.dominant, "driver")
    }

    func testEmptyInputZeroConfidence() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("")
        XCTAssertEqual(profile.confidence, 0.0)
        XCTAssertEqual(profile.tokenCount, 0)
    }

    func testNoiseInputZeroConfidence() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("zzqq xxww vvuu")
        XCTAssertEqual(profile.confidence, 0.0)
    }

    func testScoresNormalise() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("analyze data and create a design with the team")
        let total = profile.scores.values.reduce(0, +)
        XCTAssertEqual(total, 1.0, accuracy: 0.001)
    }

    // MARK: - SolutionMatcher

    private func makeMatcher() -> SolutionMatcher {
        SolutionMatcher(knowledgeBase: [
            KnowledgeEntry(id: "perf-analytical", solution: "Profile then optimize.", traits: ["analytical": 0.5], minConfidence: 0.5),
            KnowledgeEntry(id: "perf-driver", solution: "Cut scope and ship.", traits: ["driver": 0.5], minConfidence: 0.4),
        ])
    }

    func testMatchesFittingProfile() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("analyze the data and measure everything with benchmarks and logic")
        let match = makeMatcher().match(profile)
        XCTAssertTrue(match.matched)
        XCTAssertEqual(match.entry?.id, "perf-analytical")
        XCTAssertFalse(match.solution.isEmpty)
    }

    func testEmptyKnowledgeBaseExplains() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("analyze the data")
        let match = SolutionMatcher().match(profile)
        XCTAssertFalse(match.matched)
        XCTAssertTrue(match.explanation.contains("No performance solutions"))
    }

    func testLowConfidenceExplainsWhy() {
        let analyzer = IncomingDataAnalyzer()
        let profile = analyzer.analyze("zzqq nothing meaningful")
        let match = makeMatcher().match(profile)
        XCTAssertFalse(match.matched)
        XCTAssertTrue(match.explanation.lowercased().contains("confidence"))
    }
}

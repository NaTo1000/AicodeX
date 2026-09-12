import XCTest
@testable import AicodeXCore

final class InteractionCoreTests: XCTestCase {

    // MARK: - CommandParser

    func testWakeWordStripped() {
        let parser = CommandParser(wakeWord: "aicodex")
        let cmd = parser.parse("aicodex analyze the data")
        XCTAssertEqual(cmd.intent, .analyze)
        XCTAssertEqual(cmd.argument, "the data")
    }

    func testNoWakeWordStillParses() {
        let parser = CommandParser(wakeWord: "aicodex")
        XCTAssertEqual(parser.parse("analyze the data").intent, .analyze)
    }

    func testLongestKeywordWins() {
        let parser = CommandParser()
        let cmd = parser.parse("insert snippet for loops")
        XCTAssertEqual(cmd.intent, .insertSnippet)
        XCTAssertEqual(cmd.argument, "for loops")
    }

    func testUnknownIntent() {
        let parser = CommandParser()
        XCTAssertEqual(parser.parse("blorp the zazzle").intent, .unknown)
        XCTAssertEqual(parser.parse("").intent, .unknown)
    }

    func testPreviewInterludeStop() {
        let parser = CommandParser()
        XCTAssertEqual(parser.parse("preview print(1)").intent, .preview)
        XCTAssertEqual(parser.parse("brainstorm api design").intent, .interlude)
        XCTAssertEqual(parser.parse("resume").intent, .stopInterlude)
    }

    // MARK: - ChatSession / InterludeManager

    private func makeSession() -> ChatSession {
        let analyzer = IncomingDataAnalyzer()
        let matcher = SolutionMatcher(knowledgeBase: [
            KnowledgeEntry(id: "perf", solution: "Do the thing.", traits: ["analytical": 0.3], minConfidence: 0.3)
        ])
        return ChatSession { text in
            let match = matcher.match(analyzer.analyze(text))
            return match.matched ? "Solution: \(match.solution)" : "No solution: \(match.explanation)"
        }
    }

    func testChatSendUserAppendsAndReplies() {
        let session = makeSession()
        let reply = session.sendUser("analyze the data and measure it")
        XCTAssertFalse(reply.isEmpty)
        XCTAssertEqual(session.messages.map { $0.role }, ["user", "assistant"])
    }

    func testChatHistoryBounded() {
        let session = makeSession()
        session.applyAdjustment()  // touch to ensure session usable
        let bounded = ChatSession(maxHistory: 4) { _ in "ok" }
        for i in 0..<5 { bounded.sendUser("question \(i)") }
        XCTAssertLessThanOrEqual(bounded.messages.count, 4)
    }

    func testInterludeAppliesAdjustments() {
        let session = makeSession()
        let manager = InterludeManager(session: session)
        manager.start(topic: "design")
        XCTAssertTrue(manager.isActive)
        manager.brainstorm("creative idea")
        manager.adjustModel(traits: ["creative": 0.95], tone: "creative")
        let result = manager.end()
        XCTAssertTrue(result.contains("adjustments applied"))
        XCTAssertFalse(manager.isActive)
        XCTAssertEqual(session.traitAdjustments["creative"], 0.95)
        XCTAssertEqual(session.toneAdjustment, "creative")
    }

    func testInterludeEndWithoutActive() {
        let manager = InterludeManager(session: makeSession())
        XCTAssertEqual(manager.end(), "No interlude is currently active.")
    }

    // MARK: - ModelProviders

    func testMockProviderEchoes() throws {
        let mock = MockProvider()
        let resp = try mock.generate(model: "m", prompt: "hello world")
        XCTAssertTrue(resp.text.contains("hello"))
        XCTAssertEqual(resp.provider, "mock")
    }

    func testRegistryChoosePrefersNamedEnabled() {
        let a = MockProvider(name: "a")
        let reg = ProviderRegistry(providers: [a])
        XCTAssertEqual(reg.choose(name: "a").name, "a")
        // Unknown name → first enabled (the mock "a").
        XCTAssertEqual(reg.choose(name: "nope").name, "a")
    }

    func testRegistryFallsBackToMockWhenEmpty() {
        let reg = ProviderRegistry()
        XCTAssertEqual(reg.choose(name: "anything").name, "mock")
    }

    func testProviderKindsEnumerated() {
        let kinds = Set(ProviderKind.allCases.map { $0.rawValue })
        XCTAssertTrue(kinds.isSuperset(of: [
            "huggingface", "northflank", "bentoml", "replicate",
            "modal", "lambdalabs", "together", "runpod",
        ]))
    }
}

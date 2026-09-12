import Foundation

/// A single role-tagged chat message.
public struct ChatMessage: Codable, Equatable, Identifiable {
    public var id: UUID
    public var role: String
    public var content: String
    public var timestamp: Date

    public init(id: UUID = UUID(), role: String, content: String, timestamp: Date = Date()) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
    }
}

/// A bounded conversation bound to an analysis engine closure.
///
/// The engine is injected as a closure `(String) -> String` so the chat layer
/// stays pure Foundation and testable on Linux — the app supplies a closure
/// that routes through its assistant engine.
public final class ChatSession {
    public private(set) var messages: [ChatMessage] = []
    public let maxHistory: Int
    /// Modelling adjustments accumulated from interludes.
    public private(set) var traitAdjustments: [String: Double] = [:]
    public private(set) var toneAdjustment: String?

    private let responder: (String) -> String

    public init(maxHistory: Int = 100, responder: @escaping (String) -> String) {
        self.maxHistory = max(1, maxHistory)
        self.responder = responder
    }

    @discardableResult
    public func add(role: String, content: String) -> ChatMessage {
        let message = ChatMessage(role: role, content: content)
        messages.append(message)
        if messages.count > maxHistory {
            messages.removeFirst(messages.count - maxHistory)
        }
        return message
    }

    /// Record a user message and return the assistant's reply.
    @discardableResult
    public func sendUser(_ content: String) -> String {
        add(role: "user", content: content)
        let reply = responder(content)
        add(role: "assistant", content: reply)
        return reply
    }

    /// Merge modelling adjustments from an interlude.
    public func applyAdjustment(traits: [String: Double] = [:], tone: String? = nil) {
        for (axis, value) in traits {
            traitAdjustments[axis] = min(max(value, 0.0), 1.0)
        }
        if let tone = tone { toneAdjustment = tone }
    }
}

/// A nested brainstorming conversation captured during a coding flow.
public final class Interlude {
    public let topic: String
    public private(set) var notes: [ChatMessage] = []
    public private(set) var traitOverrides: [String: Double] = [:]
    public private(set) var toneOverride: String?
    public private(set) var isOpen = true

    public init(topic: String) {
        self.topic = topic
    }

    public func brainstorm(_ text: String) {
        notes.append(ChatMessage(role: "interlude", content: text))
    }

    public func suggestTraits(_ traits: [String: Double]) {
        for (axis, value) in traits { traitOverrides[axis] = value }
    }

    public func suggestTone(_ tone: String) { toneOverride = tone }

    fileprivate func close() { isOpen = false }
}

/// Starts/ends interlude chats and applies their modelling adjustments.
public final class InterludeManager {
    public private(set) var current: Interlude?
    public let session: ChatSession

    public init(session: ChatSession) {
        self.session = session
    }

    public var isActive: Bool { current?.isOpen == true }

    @discardableResult
    public func start(topic: String = "brainstorm") -> Interlude {
        if let active = current, active.isOpen { return active }
        session.add(role: "system", content: "[interlude started: \(topic)]")
        let interlude = Interlude(topic: topic)
        current = interlude
        return interlude
    }

    public func brainstorm(_ text: String) {
        if !isActive { start() }
        current?.brainstorm(text)
    }

    public func adjustModel(traits: [String: Double] = [:], tone: String? = nil) {
        if !isActive { start(topic: "modelling adjustment") }
        if !traits.isEmpty { current?.suggestTraits(traits) }
        if let tone = tone { current?.suggestTone(tone) }
    }

    /// Close the interlude; optionally apply captured modelling adjustments.
    @discardableResult
    public func end(apply: Bool = true) -> String {
        guard let interlude = current, interlude.isOpen else {
            return "No interlude is currently active."
        }
        interlude.close()
        var applied = ""
        if apply && (!interlude.traitOverrides.isEmpty || interlude.toneOverride != nil) {
            session.applyAdjustment(traits: interlude.traitOverrides, tone: interlude.toneOverride)
            applied = " (adjustments applied)"
        }
        current = nil
        let summary = "[interlude ended: \(interlude.topic); \(interlude.notes.count) note(s)]\(applied)"
        session.add(role: "system", content: summary)
        return summary
    }
}

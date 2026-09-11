"""Chat capabilities with mid-code "interlude" brainstorming.

The :class:`ChatSession` keeps a role-tagged conversation and routes user
messages through the :class:`~assistant.engine.AssistantEngine` so replies are
grounded in the persona/analysis pipeline.

The :class:`InterludeManager` supports *interlude chats*: pausing a coding
flow to brainstorm and capture **modelling adjustments**, then resuming with
those adjustments applied to the session (and, optionally, the engine's
persona). An interlude is just a nested, clearly-labelled conversation that can
set traits/tone overrides.
"""

from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional


class ChatMessage:
    """A single role-tagged chat message."""

    def __init__(self, role: str, content: str, ts: Optional[float] = None) -> None:
        self.role = str(role)
        self.content = str(content)
        self.ts = time.time() if ts is None else float(ts)

    def as_dict(self) -> Dict[str, object]:
        return {"role": self.role, "content": self.content, "ts": self.ts}


class ChatSession:
    """A bounded conversation bound to an assistant engine.

    ``max_history`` bounds retained messages (oldest dropped first) to keep the
    session memory predictable.
    """

    def __init__(self, engine, max_history: int = 100, clock: Callable[[], float] = time.time) -> None:
        self.engine = engine
        self.max_history = max(1, int(max_history))
        self._clock = clock
        self.messages: List[ChatMessage] = []
        # Modelling adjustments accumulated from interludes (trait/tone nudges).
        self.adjustments: Dict[str, object] = {"traits": {}, "tone": None}

    def add(self, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(role, content, ts=self._clock())
        self.messages.append(msg)
        if len(self.messages) > self.max_history:
            del self.messages[: len(self.messages) - self.max_history]
        return msg

    def send_user(self, content: str) -> str:
        """Record a user message and return the assistant's reply."""
        self.add("user", content)
        report = self.engine.process(content)
        reply = report.summary()
        self.add("assistant", reply)
        return reply

    def apply_adjustment(self, traits: Optional[Dict[str, float]] = None, tone: Optional[str] = None) -> None:
        """Merge modelling adjustments and re-tune the engine persona."""
        if traits:
            self.adjustments["traits"].update({str(k): float(v) for k, v in traits.items()})
        if tone:
            self.adjustments["tone"] = str(tone)
        overrides: Dict[str, object] = {"traits": dict(self.adjustments["traits"])}
        if self.adjustments["tone"]:
            overrides["tone"] = self.adjustments["tone"]
        self.engine = self.engine.fine_tune(overrides)

    @property
    def persona(self):
        """The session's current (possibly re-tuned) persona."""
        return self.engine.persona

    def history(self) -> List[Dict[str, object]]:
        return [m.as_dict() for m in self.messages]


class Interlude:
    """A nested brainstorming conversation captured during a coding flow."""

    def __init__(self, topic: str, clock: Callable[[], float] = time.time) -> None:
        self.topic = str(topic)
        self._clock = clock
        self.notes: List[ChatMessage] = []
        self.trait_overrides: Dict[str, float] = {}
        self.tone_override: Optional[str] = None
        self.open = True

    def brainstorm(self, text: str) -> ChatMessage:
        msg = ChatMessage("interlude", text, ts=self._clock())
        self.notes.append(msg)
        return msg

    def suggest_traits(self, traits: Dict[str, float]) -> None:
        self.trait_overrides.update({str(k): float(v) for k, v in traits.items()})

    def suggest_tone(self, tone: str) -> None:
        self.tone_override = str(tone)


class InterludeManager:
    """Starts/ends interlude chats and applies their modelling adjustments."""

    def __init__(self, session: ChatSession) -> None:
        self.session = session
        self.current: Optional[Interlude] = None
        self._clock = session._clock

    @property
    def active(self) -> bool:
        return self.current is not None and self.current.open

    def start(self, topic: str = "brainstorm") -> Interlude:
        """Pause the coding flow and open an interlude on ``topic``."""
        if self.active:
            return self.current
        self.session.add("system", f"[interlude started: {topic}]")
        self.current = Interlude(topic, clock=self._clock)
        return self.current

    def brainstorm(self, text: str) -> str:
        """Add a brainstorming note to the active interlude (starts one if needed)."""
        if not self.active:
            self.start("brainstorm")
        assert self.current is not None
        self.current.brainstorm(text)
        # Also run the thought through the engine so the user gets analysis.
        report = self.session.engine.process(text)
        return report.summary()

    def adjust_model(self, traits: Optional[Dict[str, float]] = None, tone: Optional[str] = None) -> None:
        """Record modelling adjustments on the active interlude."""
        if not self.active:
            self.start("modelling adjustment")
        assert self.current is not None
        if traits:
            self.current.suggest_traits(traits)
        if tone:
            self.current.suggest_tone(tone)

    def end(self, apply: bool = True) -> str:
        """Close the interlude; optionally apply captured modelling adjustments."""
        if not self.active or self.current is None:
            return "No interlude is currently active."
        interlude = self.current
        interlude.open = False
        applied = ""
        if apply and (interlude.trait_overrides or interlude.tone_override):
            # Pass tone only when set so trait-only adjustments aren't dropped.
            self.session.apply_adjustment(
                traits=interlude.trait_overrides or None,
                tone=interlude.tone_override if interlude.tone_override else None,
            )
            applied = " (adjustments applied)"
        self.current = None
        summary = (
            f"[interlude ended: {interlude.topic}; {len(interlude.notes)} note(s)]{applied}"
        )
        self.session.add("system", summary)
        return summary

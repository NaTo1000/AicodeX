"""Voice command framework for AicodeX.

Design goals:

* **Dependency-free / offline-capable** — speech recognition and synthesis are
  abstracted behind the :class:`SpeechEngine` protocol so a real STT/TTS engine
  (or platform APIs) can be plugged in later. The bundled
  :class:`DictSpeechEngine` is a deterministic, test-friendly implementation
  that treats already-typed text as "transcribed" speech.
* **Testable logic** — the :class:`CommandParser` turns an utterance into a
  structured :class:`VoiceCommand` intent, and :class:`VoiceCommandProcessor`
  executes it against overlay/engine hooks. Both are pure and unit-testable.

Supported intents (mapped from natural commands):
``analyze`` / ``format`` / ``insert_snippet`` / ``preview`` (sandbox) /
``interlude`` (start a brainstorming interlude) / ``stop_interlude`` /
``toggle_overlay`` / ``help`` / ``unknown``.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Protocol

# Canonical intents the parser can emit.
INTENTS = (
    "analyze",
    "format",
    "insert_snippet",
    "preview",
    "interlude",
    "stop_interlude",
    "toggle_overlay",
    "help",
    "unknown",
)

# Verb/keyword → intent mapping. Matched case-insensitively on word prefixes.
_INTENT_KEYWORDS = {
    "analyze": ("analyze", "analyse", "analyze this", "assess", "profile", "evaluate"),
    "format": ("format", "pretty", "beautify", "lint"),
    "insert_snippet": ("insert snippet", "insert", "snippet", "paste", "template"),
    "preview": ("preview", "run", "execute", "sandbox", "try"),
    "interlude": ("interlude", "brainstorm", "whiteboard", "think aloud", "pause code"),
    "stop_interlude": ("resume", "continue code", "end interlude", "back to code", "stop interlude"),
    "toggle_overlay": ("toggle overlay", "hide overlay", "show overlay", "toggle"),
    "help": ("help", "commands", "what can you do", "usage"),
}


class VoiceCommand:
    """A parsed voice command: an intent plus its free-text argument."""

    def __init__(self, intent: str, argument: str = "", raw: str = "") -> None:
        self.intent = intent if intent in INTENTS else "unknown"
        self.argument = argument.strip()
        self.raw = raw.strip()

    def as_dict(self) -> Dict[str, str]:
        return {"intent": self.intent, "argument": self.argument, "raw": self.raw}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"VoiceCommand(intent={self.intent!r}, argument={self.argument!r})"


class CommandParser:
    """Parses an utterance into a :class:`VoiceCommand`.

    ``wake_word`` (optional) must lead the utterance when set; ``command_prefix``
    (optional) is stripped before intent detection.
    """

    def __init__(self, wake_word: str = "aicodex", command_prefix: str = "") -> None:
        self.wake_word = (wake_word or "").strip().lower()
        self.command_prefix = (command_prefix or "").strip()

    def _strip_wake_and_prefix(self, text: str) -> str:
        t = text.strip()
        if self.command_prefix and t.startswith(self.command_prefix):
            t = t[len(self.command_prefix):].strip()
        if self.wake_word:
            lowered = t.lower()
            if lowered.startswith(self.wake_word):
                t = t[len(self.wake_word):].lstrip(" ,:").strip()
        return t

    def parse(self, utterance: object) -> VoiceCommand:
        raw = "" if utterance is None else str(utterance)
        text = self._strip_wake_and_prefix(raw)
        if not text:
            return VoiceCommand("unknown", "", raw)

        lowered = text.lower()
        # Longest keyword match wins so "insert snippet" beats "insert".
        best_intent = "unknown"
        best_len = -1
        best_kw = ""
        for intent, keywords in _INTENT_KEYWORDS.items():
            for kw in keywords:
                if lowered.startswith(kw) and len(kw) > best_len:
                    best_intent, best_len, best_kw = intent, len(kw), kw
        argument = text[len(best_kw):].strip(" ,:") if best_kw else text
        return VoiceCommand(best_intent, argument, raw)


class SpeechEngine(Protocol):
    """Protocol for pluggable speech engines (STT in, TTS out)."""

    def transcribe(self) -> str:  # pragma: no cover - interface
        """Return the latest transcribed utterance (may block in a real engine)."""
        ...

    def speak(self, text: str) -> None:  # pragma: no cover - interface
        """Vocalise ``text`` (no-op in headless/testing engines)."""
        ...


class DictSpeechEngine:
    """Deterministic speech engine for tests/offline use.

    "Transcription" is just pulling the next queued utterance; ``speak``
    records to ``spoken`` so tests can assert on it.
    """

    def __init__(self, utterances: Optional[list] = None) -> None:
        self._queue = list(utterances or [])
        self.spoken: list = []

    def push(self, utterance: str) -> None:
        self._queue.append(utterance)

    def transcribe(self) -> str:
        return self._queue.pop(0) if self._queue else ""

    def speak(self, text: str) -> None:
        self.spoken.append(text)


class VoiceCommandProcessor:
    """Executes parsed voice commands against application hooks.

    Hooks are callables; only the ones the host provides are wired. Unknown /
    unwired intents produce a helpful message rather than raising.
    """

    def __init__(self, parser: Optional[CommandParser] = None, speech: Optional[SpeechEngine] = None) -> None:
        self.parser = parser or CommandParser()
        self.speech = speech or DictSpeechEngine()
        self._hooks: Dict[str, Callable[[str], str]] = {}

    def on(self, intent: str, handler: Callable[[str], str]) -> None:
        """Register ``handler(argument) -> response_text`` for ``intent``."""
        self._hooks[intent] = handler

    def handle_utterance(self, utterance: object) -> str:
        """Transcribe+parse ``utterance`` and dispatch to the matching hook."""
        command = self.parser.parse(utterance)
        return self.execute(command)

    def execute(self, command: VoiceCommand) -> str:
        handler = self._hooks.get(command.intent)
        if handler is None:
            response = self._fallback(command)
        else:
            try:
                response = handler(command.argument)
            except Exception as exc:  # pragma: no cover - defensive
                response = f"Command '{command.intent}' failed: {exc}"
        self.speech.speak(response)
        return response

    def listen_once(self) -> str:
        """Pull one utterance from the speech engine and handle it."""
        return self.handle_utterance(self.speech.transcribe())

    def _fallback(self, command: VoiceCommand) -> str:
        if command.intent == "unknown":
            return (
                "Sorry, I didn't understand that command. Say 'help' to hear "
                "what I can do."
            )
        return f"The '{command.intent}' command is not available right now."

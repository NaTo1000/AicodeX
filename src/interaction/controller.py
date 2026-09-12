"""High-level controller wiring voice, chat, sandbox, and providers together.

The :class:`InteractionController` is the single object the overlay UI talks
to. It owns a :class:`ChatSession` bound to the assistant engine, an
:class:`InterludeManager`, a :class:`SnippetSandbox`, a
:class:`VoiceCommandProcessor`, and a :class:`~.providers.ProviderManager`, and
exposes small, UI-friendly methods for each capability.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from .chat import ChatSession, InterludeManager
from .prediction import CodePredictor, Prediction
from .providers import ProviderManager, ProviderRegistry, ProviderResponse
from .sandbox import ExecutionResult, SnippetSandbox
from .voice import CommandParser, DictSpeechEngine, VoiceCommandProcessor


class InteractionController:
    """Facade over voice / chat / interlude / sandbox / providers."""

    def __init__(
        self,
        engine,
        session: Optional[ChatSession] = None,
        interludes: Optional[InterludeManager] = None,
        sandbox: Optional[SnippetSandbox] = None,
        voice: Optional[VoiceCommandProcessor] = None,
        providers: Optional[ProviderManager] = None,
        predictor: Optional[CodePredictor] = None,
    ) -> None:
        self.engine = engine
        self.session = session or ChatSession(engine)
        self.session.engine = engine
        self.interludes = interludes or InterludeManager(self.session)
        self.sandbox = sandbox or SnippetSandbox()
        self.voice = voice or VoiceCommandProcessor(CommandParser(), DictSpeechEngine())
        self.providers = providers or ProviderManager()
        self.predictor = predictor or CodePredictor()
        self._wire_voice_hooks()

    @classmethod
    def from_config(
        cls,
        engine,
        config,
        transport=None,
        environ=None,
        clock: Optional[Callable[[], float]] = None,
    ) -> "InteractionController":
        """Build a controller from the ``interaction`` config block.

        ``config`` may be the full app settings (with an ``interaction`` key) or
        the interaction block itself. ``transport``/``environ``/``clock`` are
        injectable for deterministic tests.
        """
        block = config.get("interaction", config) if isinstance(config, dict) else {}
        if not isinstance(block, dict):
            block = {}
        clk = clock or time.time

        voice_cfg = block.get("voice", {}) if isinstance(block.get("voice"), dict) else {}
        parser = CommandParser(
            wake_word=voice_cfg.get("wake_word", "aicodex"),
            command_prefix=voice_cfg.get("command_prefix", ""),
        )
        voice = VoiceCommandProcessor(parser, DictSpeechEngine())

        chat_cfg = block.get("chat", {}) if isinstance(block.get("chat"), dict) else {}
        session = ChatSession(engine, max_history=chat_cfg.get("max_history", 100), clock=clk)
        interludes = InterludeManager(session)

        sandbox = SnippetSandbox.from_config(block.get("sandbox"))

        registry = ProviderRegistry.from_config(
            block.get("providers", []), transport=transport, environ=environ
        )
        providers = ProviderManager(registry)

        predictor = CodePredictor()
        return cls(engine, session, interludes, sandbox, voice, providers, predictor)

    @property
    def persona(self):
        """The controller's current persona (reflects any interlude re-tune)."""
        return self.session.engine.persona

    # -- voice -------------------------------------------------------------
    def _wire_voice_hooks(self) -> None:
        self.voice.on("analyze", lambda arg: self.chat(arg or "analyze this"))
        self.voice.on("preview", lambda arg: self.preview(arg).summary())
        self.voice.on("interlude", lambda arg: self.start_interlude(arg or "brainstorm"))
        self.voice.on("stop_interlude", lambda _arg: self.end_interlude())
        self.voice.on("help", lambda _arg: self.help_text())

    def handle_voice(self, utterance: object) -> str:
        """Handle a raw voice utterance end-to-end."""
        return self.voice.handle_utterance(utterance)

    # -- chat --------------------------------------------------------------
    def chat(self, message: str) -> str:
        """Send a chat message through the assistant engine."""
        return self.session.send_user(message)

    # -- interludes --------------------------------------------------------
    def start_interlude(self, topic: str = "brainstorm") -> str:
        self.interludes.start(topic)
        return f"Interlude started: {topic}"

    def brainstorm(self, text: str) -> str:
        return self.interludes.brainstorm(text)

    def adjust_model(self, traits=None, tone=None) -> str:
        self.interludes.adjust_model(traits=traits, tone=tone)
        return "Modelling adjustment recorded."

    def end_interlude(self, apply: bool = True) -> str:
        return self.interludes.end(apply=apply)

    # -- sandbox -----------------------------------------------------------
    def preview(self, code: str) -> ExecutionResult:
        """Run a snippet in the sandbox and return its result."""
        return self.sandbox.run(code)

    # -- providers ---------------------------------------------------------
    def generate(self, model: str, prompt: str, provider_name: Optional[str] = None) -> ProviderResponse:
        return self.providers.generate(model, prompt, provider_name)

    # -- prediction (HiAi + PECs) ------------------------------------------
    def predict_code(self, code: object, filename: Optional[str] = None) -> Prediction:
        """Predict language/variant/format/algorithm for a submitted snippet.

        Records the prediction in the assistant engine's retention store so
        future predictions/decisions are history-aware (PECs data retention).
        """
        prediction = self.predictor.predict(code, filename=filename)
        self._record_prediction(code, prediction)
        return prediction

    def _record_prediction(self, code: object, prediction: Prediction) -> None:
        retention = getattr(getattr(self.engine, "router", None), "retention", None)
        if retention is None:
            return
        text = code if isinstance(code, str) else str(code or "")
        key = f"code:{prediction.language}/{prediction.format}"
        retention.record(
            key, text, chosen=prediction.language,
            justified=prediction.language_confidence >= 0.5,
            confidence=prediction.language_confidence,
        )

    def choose_provider_for(self, code: object, filename: Optional[str] = None):
        """Predict the code's language and suggest the best enabled provider.

        Returns ``(prediction, provider_name_or_none)``. Prefers a configured
        provider whose name matches the predicted language family, else the
        first enabled provider, else the mock fallback.
        """
        prediction = self.predictor.predict(code, filename=filename)
        registry = self.providers.registry
        lang = prediction.language.lower()

        # Map a predicted language to a preferred provider when one is enabled.
        preferred = None
        lang_pref_map = {
            "swift": "xcode",
            "python": "chatgptcodex",
            "javascript": "openrouter",
            "typescript": "openrouter",
        }
        candidate = lang_pref_map.get(lang)
        if candidate is not None:
            provider = registry.get(candidate)
            if provider is not None and provider.enabled:
                preferred = candidate
        if preferred is None:
            enabled = registry.enabled()
            preferred = enabled[0].name if enabled else "mock"
        return prediction, preferred

    # -- misc --------------------------------------------------------------
    @staticmethod
    def help_text() -> str:
        return (
            "I can: analyze <text>, preview <code>, start/end an interlude for "
            "brainstorming, insert a snippet, format code, and answer questions "
            "via the assistant engine."
        )

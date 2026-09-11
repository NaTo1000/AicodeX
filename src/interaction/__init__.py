"""Interaction subsystem: voice commands, chat + interludes, sandbox preview,
and pluggable AI model providers.

Built to be dependency-free and offline-capable: speech I/O and provider HTTP
transports are injectable, so the logic is fully testable without a microphone
or network. See :class:`InteractionController` for a single entry point that
wires everything to the :class:`~assistant.engine.AssistantEngine`.
"""

from .voice import (
    CommandParser,
    DictSpeechEngine,
    INTENTS,
    SpeechEngine,
    VoiceCommand,
    VoiceCommandProcessor,
)
from .chat import ChatMessage, ChatSession, Interlude, InterludeManager
from .sandbox import ExecutionResult, SnippetSandbox
from .controller import InteractionController

__all__ = [
    "CommandParser",
    "DictSpeechEngine",
    "INTENTS",
    "SpeechEngine",
    "VoiceCommand",
    "VoiceCommandProcessor",
    "ChatMessage",
    "ChatSession",
    "Interlude",
    "InterludeManager",
    "ExecutionResult",
    "SnippetSandbox",
    "InteractionController",
]

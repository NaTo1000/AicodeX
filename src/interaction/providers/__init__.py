"""Pluggable AI model providers for AicodeX.

Adapters for Hugging Face, Northflank, BentoML, Replicate, Modal, Lambda Labs,
Together AI, and RunPod, plus an offline :class:`MockProvider`. All adapters
share an injectable transport (no real HTTP in tests) and resolve API keys from
environment variables by name — keys are never persisted.
"""

from .base import (
    HTTPJsonProvider,
    MockProvider,
    ModelProvider,
    ProviderError,
    ProviderResponse,
    Transport,
)
from .adapters import (
    ADAPTER_KINDS,
    BentoMLProvider,
    ChatGPT6LunaProvider,
    ChatGPTCodexProvider,
    ClaudeDecoderProvider,
    CodexProvider,
    GeminiProvider,
    GenericProvider,
    Grok4Provider,
    HuggingFaceProvider,
    KodexProvider,
    LambdaLabsProvider,
    MinstrelProvider,
    ModalProvider,
    NorthflankProvider,
    OpenRouterProvider,
    ReplicateProvider,
    RunPodProvider,
    TogetherProvider,
    XcodeProvider,
)
from .registry import ProviderManager, ProviderRegistry

__all__ = [
    "ModelProvider",
    "HTTPJsonProvider",
    "MockProvider",
    "ProviderError",
    "ProviderResponse",
    "Transport",
    "ADAPTER_KINDS",
    "HuggingFaceProvider",
    "NorthflankProvider",
    "BentoMLProvider",
    "ReplicateProvider",
    "ModalProvider",
    "LambdaLabsProvider",
    "TogetherProvider",
    "RunPodProvider",
    "Grok4Provider",
    "OpenRouterProvider",
    "GeminiProvider",
    "ChatGPTCodexProvider",
    "ChatGPT6LunaProvider",
    "ClaudeDecoderProvider",
    "CodexProvider",
    "MinstrelProvider",
    "KodexProvider",
    "XcodeProvider",
    "GenericProvider",
    "ProviderRegistry",
    "ProviderManager",
]

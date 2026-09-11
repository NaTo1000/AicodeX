"""Provider registry and manager.

The :class:`ProviderRegistry` builds providers from config entries (each entry
names a ``kind`` that maps to an adapter) and looks them up by name. The
:class:`ProviderManager` resolves a request (model + preferred provider) to a
provider and returns a normalised response, with a safe offline/mock fallback
so the app keeps working with no keys configured.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .adapters import ADAPTER_KINDS
from .base import MockProvider, ModelProvider, ProviderError, ProviderResponse, Transport


class ProviderRegistry:
    """A name → provider collection built from config."""

    def __init__(self, providers: Optional[List[ModelProvider]] = None) -> None:
        self._providers: Dict[str, ModelProvider] = {}
        for p in providers or []:
            self.register(p)

    def register(self, provider: ModelProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[ModelProvider]:
        return self._providers.get(name)

    def names(self) -> List[str]:
        return list(self._providers.keys())

    def enabled(self) -> List[ModelProvider]:
        return [p for p in self._providers.values() if p.enabled]

    @classmethod
    def from_config(
        cls,
        entries: object,
        transport: Optional[Transport] = None,
        environ: Optional[Dict[str, str]] = None,
    ) -> "ProviderRegistry":
        """Build a registry from the ``interaction.providers`` config list.

        Unknown ``kind`` values are skipped (logged via ``errors`` on the
        registry is overkill — we just ignore them) so a typo can't crash the
        app. ``transport``/``environ`` are injected for tests.
        """
        registry = cls()
        if not isinstance(entries, list):
            return registry
        for raw in entries:
            if not isinstance(raw, dict):
                continue
            kind = str(raw.get("kind", "")).lower()
            adapter = ADAPTER_KINDS.get(kind)
            if adapter is None:
                continue
            provider = adapter(
                name=raw.get("name", kind),
                endpoint=raw.get("endpoint", ""),
                api_key_env=raw.get("api_key_env"),
                enabled=raw.get("enabled", True),
                timeout=raw.get("timeout", 30.0),
                transport=transport,
                environ=environ,
            )
            registry.register(provider)
        return registry


class ProviderManager:
    """Resolves generation requests to providers with offline fallback."""

    def __init__(self, registry: Optional[ProviderRegistry] = None, fallback: Optional[ModelProvider] = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.fallback = fallback or MockProvider(name="mock")

    def choose(self, provider_name: Optional[str] = None) -> ModelProvider:
        """Pick a provider: the named one if enabled, else the first enabled,
        else the mock fallback."""
        if provider_name:
            chosen = self.registry.get(provider_name)
            if chosen is not None and chosen.enabled:
                return chosen
        enabled = self.registry.enabled()
        return enabled[0] if enabled else self.fallback

    def generate(self, model: str, prompt: str, provider_name: Optional[str] = None) -> ProviderResponse:
        provider = self.choose(provider_name)
        try:
            return provider.generate(model, prompt)
        except ProviderError:
            # Fall back to the mock so callers always get a response.
            if provider is self.fallback:
                raise
            return self.fallback.generate(model, prompt)

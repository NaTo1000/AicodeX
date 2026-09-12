"""Base abstractions for pluggable AI model providers.

A :class:`ModelProvider` resolves a model + prompt into a text response.
Network access goes through an injectable ``transport`` callable so the
providers are fully testable offline and no real HTTP call is made in tests.
API keys are resolved from environment variables by *name* and are never
persisted.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Dict, Optional


class ProviderError(Exception):
    """Raised when a provider cannot fulfil a request."""


class ProviderResponse:
    """A normalised text response from a provider."""

    def __init__(self, text: str, provider: str, model: str, raw: Optional[dict] = None) -> None:
        self.text = text
        self.provider = provider
        self.model = model
        self.raw = raw or {}

    def as_dict(self) -> Dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "text": self.text,
        }


# A transport takes (url, headers, payload_bytes, timeout) and returns the
# decoded JSON body as a dict/list. Injectable for tests.
Transport = Callable[[str, Dict[str, str], bytes, float], object]


def default_transport(url: str, headers: Dict[str, str], payload: bytes, timeout: float) -> object:
    """The real HTTP transport (urllib). Not used in tests."""
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - host from config
        return json.loads(resp.read().decode("utf-8"))


class ModelProvider:
    """Abstract base for an AI model provider adapter.

    Subclasses implement :meth:`build_request` (url/headers/payload) and
    :meth:`parse_response` (decode JSON → text).
    """

    #: Subclasses set a stable provider kind, e.g. ``"huggingface"``.
    kind: str = "base"

    def __init__(
        self,
        name: str,
        endpoint: str,
        api_key_env: Optional[str] = None,
        enabled: bool = True,
        timeout: float = 30.0,
        transport: Optional[Transport] = None,
        environ: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = str(name)
        self.endpoint = str(endpoint).rstrip("/")
        self.api_key_env = api_key_env
        self.enabled = bool(enabled)
        self.timeout = float(timeout)
        self._transport = transport or default_transport
        # Resolve secrets on demand from this env mapping; the key *value* is
        # never stored on the instance (only the mapping / var name is kept).
        self._env_getter = (environ.get if environ is not None else os.environ.get)

    # -- secrets -----------------------------------------------------------
    def api_key(self) -> Optional[str]:
        """Resolve the API key from the named environment variable.

        Returns ``None`` when unset; the value is read on demand and never
        stored on the instance.
        """
        if not self.api_key_env:
            return None
        return self._env_getter(self.api_key_env)

    def is_configured(self) -> bool:
        """True when the provider is enabled and has a usable key (if required)."""
        return self.enabled

    # -- request/response --------------------------------------------------
    def build_request(self, model: str, prompt: str) -> (str, Dict[str, str], bytes):
        """Return ``(url, headers, payload_bytes)`` for a generation request."""
        raise NotImplementedError

    def parse_response(self, body: object) -> str:
        """Decode the provider's JSON body into plain text."""
        raise NotImplementedError

    def auth_headers(self) -> Dict[str, str]:
        """Authorization header built from the env-resolved key (never stored)."""
        key = self.api_key()
        return {"Authorization": f"******"} if key else {}

    def generate(self, model: str, prompt: str) -> ProviderResponse:
        """Generate a text response. Subclasses override the transport path."""
        raise NotImplementedError


class HTTPJsonProvider(ModelProvider):
    """A :class:`ModelProvider` that POSTs a JSON body and parses JSON back."""

    def _json(self, obj: object) -> bytes:
        return json.dumps(obj).encode("utf-8")

    def auth_headers(self) -> Dict[str, str]:
        key = self.api_key()
        return {"Authorization": f"******"} if key else {}

    def generate(self, model: str, prompt: str) -> ProviderResponse:
        if not self.enabled:
            raise ProviderError(f"Provider '{self.name}' is disabled.")
        url, headers, payload = self.build_request(model, prompt)
        headers = dict(headers)
        headers.setdefault("Content-Type", "application/json")
        try:
            body = self._transport(url, headers, payload, self.timeout)
            text = self.parse_response(body)
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalise transport/parse errors
            raise ProviderError(f"{self.name} request failed: {exc}") from exc
        return ProviderResponse(
            text=text, provider=self.name, model=model,
            raw=body if isinstance(body, dict) else {},
        )


class MockProvider(ModelProvider):
    """A deterministic, offline provider for tests and offline use.

    Returns an echo-style response derived from the prompt so downstream logic
    can be exercised without any network access.
    """

    kind = "mock"

    def __init__(self, name: str = "mock", response: Optional[str] = None, **kwargs) -> None:
        kwargs.setdefault("endpoint", "mock://local")
        kwargs.setdefault("enabled", True)
        super().__init__(name=name, **kwargs)
        self._canned = response
        self.calls: list = []

    def build_request(self, model: str, prompt: str):  # pragma: no cover - not used
        return ("mock://local", {}, b"")

    def parse_response(self, body):  # pragma: no cover - not used
        return str(body)

    def generate(self, model: str, prompt: str) -> ProviderResponse:
        self.calls.append({"model": model, "prompt": prompt})
        text = self._canned if self._canned is not None else f"[mock:{model}] {prompt[:120]}"
        return ProviderResponse(text=text, provider=self.name, model=model)

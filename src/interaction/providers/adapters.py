"""Concrete provider adapters.

Each adapter subclasses :class:`~.base.HTTPJsonProvider` and only defines the
request shape + response decoding for its service. They share auth handling
(API key from an env var, never persisted) and the injectable transport, so all
are testable offline. Adapters are intentionally thin — they describe *how* to
talk to a service, not *what* model to run.
"""

from __future__ import annotations

from typing import Dict

from .base import HTTPJsonProvider, ProviderError


def _first_text(body) -> str:
    """Best-effort extraction of generated text from common shapes."""
    if isinstance(body, dict):
        for key in ("generated_text", "text", "output", "completion", "response"):
            if key in body and isinstance(body[key], str):
                return body[key]
        # OpenAI-style choices
        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                if isinstance(first.get("text"), str):
                    return first["text"]
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
        # Replicate-style output list
        output = body.get("output")
        if isinstance(output, list):
            return "".join(str(p) for p in output)
    if isinstance(body, list) and body and isinstance(body[0], dict):
        if isinstance(body[0].get("generated_text"), str):
            return body[0]["generated_text"]
    raise ProviderError("Could not parse provider response body.")


class HuggingFaceProvider(HTTPJsonProvider):
    kind = "huggingface"

    def build_request(self, model: str, prompt: str):
        url = f"{self.endpoint}/{model}"
        return url, self.auth_headers(), self._json({"inputs": prompt})

    def parse_response(self, body) -> str:
        return _first_text(body)


class NorthflankProvider(HTTPJsonProvider):
    kind = "northflank"

    def build_request(self, model: str, prompt: str):
        url = f"{self.endpoint}/models/{model}/generate"
        return url, self.auth_headers(), self._json({"prompt": prompt})

    def parse_response(self, body) -> str:
        return _first_text(body)


class BentoMLProvider(HTTPJsonProvider):
    kind = "bentoml"

    def build_request(self, model: str, prompt: str):
        url = f"{self.endpoint}/generate"
        headers = self.auth_headers()
        return url, headers, self._json({"model": model, "prompt": prompt})

    def parse_response(self, body) -> str:
        return _first_text(body)


class ReplicateProvider(HTTPJsonProvider):
    kind = "replicate"

    def build_request(self, model: str, prompt: str):
        headers = self.auth_headers()
        url = f"{self.endpoint}/models/{model}/predictions"
        return url, headers, self._json({"input": {"prompt": prompt}})

    def parse_response(self, body) -> str:
        return _first_text(body)


class ModalProvider(HTTPJsonProvider):
    kind = "modal"

    def build_request(self, model: str, prompt: str):
        headers = self.auth_headers()
        url = f"{self.endpoint}/generate"
        return url, headers, self._json({"model": model, "prompt": prompt})

    def parse_response(self, body) -> str:
        return _first_text(body)


class LambdaLabsProvider(HTTPJsonProvider):
    kind = "lambdalabs"

    def build_request(self, model: str, prompt: str):
        headers = self.auth_headers()
        url = f"{self.endpoint}/chat/completions"
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        return url, headers, self._json(payload)

    def parse_response(self, body) -> str:
        return _first_text(body)


class TogetherProvider(HTTPJsonProvider):
    kind = "together"

    def build_request(self, model: str, prompt: str):
        headers = self.auth_headers()
        url = f"{self.endpoint}/chat/completions"
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        return url, headers, self._json(payload)

    def parse_response(self, body) -> str:
        return _first_text(body)


class RunPodProvider(HTTPJsonProvider):
    kind = "runpod"

    def build_request(self, model: str, prompt: str):
        headers = self.auth_headers()
        url = f"{self.endpoint}/{model}/runsync"
        return url, headers, self._json({"input": {"prompt": prompt}})

    def parse_response(self, body) -> str:
        return _first_text(body)


#: kind → adapter class, used by the registry/factory.
ADAPTER_KINDS: Dict[str, type] = {
    p.kind: p
    for p in (
        HuggingFaceProvider,
        NorthflankProvider,
        BentoMLProvider,
        ReplicateProvider,
        ModalProvider,
        LambdaLabsProvider,
        TogetherProvider,
        RunPodProvider,
    )
}

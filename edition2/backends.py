"""Compute-backend links for AicodeX Edition 2 models.

Every model role gets its own **compute link** describing where its work runs.
A role either uses the *standard* model output (the provider's default), or a
user-supplied backend: a VPS, a cloud instance, or a GPU (Nvidia / Tesla).

The configuration stores only *references* — a backend's endpoint is typically
a ``$VAULT:key`` reference resolved through the local secrets vault, so no
host, URL, or credential is ever committed to version control.

Standard library only; immutable dataclasses; deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional

from .orchestrator import ConfigError, RoleRegistry
from .vault import SecretsVault

# Valid compute backend kinds.
_BACKEND_KINDS = ("standard", "vps", "cloud", "gpu")

# Valid GPU vendors for the ``gpu`` kind.
_GPU_VENDORS = ("Nvidia", "Tesla")


@dataclass(frozen=True)
class ComputeBackend:
    """An immutable description of where a single model's work runs.

    Attributes
    ----------
    kind:
        One of ``standard`` | ``vps`` | ``cloud`` | ``gpu``.
    endpoint:
        A connection reference for the backend. For non-standard kinds this is
        usually a ``$VAULT:key`` reference; ``None`` for ``standard``.
    gpu_vendor:
        For ``kind == "gpu"``, the vendor — ``Nvidia`` or ``Tesla``.
    label:
        Optional human-readable name for the backend.
    """

    kind: str = "standard"
    endpoint: Optional[str] = None
    gpu_vendor: Optional[str] = None
    label: Optional[str] = None

    def describe(self) -> str:
        """A short human-readable description of the link."""
        if self.kind == "standard":
            return "standard model output"
        if self.kind == "gpu":
            vendor = self.gpu_vendor or "GPU"
            return f"GPU ({vendor})"
        return self.kind.upper()


def parse_backend(raw: Optional[Mapping[str, object]],
                  role_name: str = "<unknown>") -> ComputeBackend:
    """Validate a raw ``compute`` config block into a :class:`ComputeBackend`.

    ``None`` (or an empty mapping) yields the default ``standard`` backend.
    Raises :class:`ConfigError` for invalid kinds, GPU vendors, or missing
    endpoints.
    """
    if not raw:
        return ComputeBackend()
    if not isinstance(raw, Mapping):
        raise ConfigError(f"Role '{role_name}': 'compute' must be a JSON object")

    kind = str(raw.get("kind", "standard")).lower()
    if kind not in _BACKEND_KINDS:
        raise ConfigError(
            f"Role '{role_name}': compute kind must be one of "
            f"{_BACKEND_KINDS}, got '{kind}'")

    endpoint = raw.get("endpoint")
    gpu_vendor = raw.get("gpu_vendor")
    label = raw.get("label")

    if kind == "gpu":
        if gpu_vendor not in _GPU_VENDORS:
            raise ConfigError(
                f"Role '{role_name}': gpu_vendor must be one of "
                f"{_GPU_VENDORS}, got '{gpu_vendor}'")
    elif gpu_vendor is not None:
        raise ConfigError(
            f"Role '{role_name}': gpu_vendor is only valid for kind 'gpu'")

    if kind != "standard" and not endpoint:
        raise ConfigError(
            f"Role '{role_name}': compute kind '{kind}' requires an endpoint "
            "(use a $VAULT:key reference)")

    return ComputeBackend(
        kind=kind,
        endpoint=str(endpoint) if endpoint is not None else None,
        gpu_vendor=str(gpu_vendor) if gpu_vendor is not None else None,
        label=str(label) if label is not None else None,
    )


class BackendRegistry:
    """Resolve the per-model compute link for every configured role."""

    def __init__(self, registry: RoleRegistry,
                 vault: Optional[SecretsVault] = None) -> None:
        self._registry = registry
        self._vault = vault

    def link_for(self, role_name: str) -> ComputeBackend:
        """Return the configured :class:`ComputeBackend` for a role."""
        return self._registry.get(role_name).compute

    def all_links(self) -> Dict[str, ComputeBackend]:
        """Return ``{role_name: backend}`` for every role, in config order."""
        return {role.name: role.compute for role in self._registry.all_roles()}

    def resolve_endpoint(self, role_name: str) -> Optional[str]:
        """Resolve a role's backend endpoint through the vault.

        Returns ``None`` for ``standard`` backends (no endpoint) and raises
        :class:`ConfigError` when a ``$VAULT:`` reference is present but no
        vault is attached.
        """
        backend = self.link_for(role_name)
        endpoint = backend.endpoint
        if endpoint is None:
            return None
        if endpoint.startswith("$VAULT:") and self._vault is None:
            raise ConfigError(
                f"Role '{role_name}': compute endpoint references the vault "
                "but no vault is attached")
        if self._vault is not None:
            return self._vault.resolve(endpoint)
        return endpoint

    def render(self) -> str:
        """Render all per-model compute links as aligned plain text."""
        lines = ["AicodeX Edition 2 — Compute Backends", "=" * 55]
        for role in self._registry.all_roles():
            backend = role.compute
            lines.append(f"  {role.name:<22} {role.model:<9} {backend.describe()}")
        return "\n".join(lines)

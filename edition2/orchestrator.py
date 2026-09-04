"""Role registry and configuration loader for AicodeX Edition 2.

A *role* binds a model to a mission and a set of declared inputs/outputs. The
:class:`RoleRegistry` validates the raw configuration and exposes the enabled
roles in a deterministic order so the CHAiMERA ConductorX orchestrator can
sequence them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from .vault import SecretsVault


class ConfigError(Exception):
    """Raised when the Edition 2 configuration is malformed."""


@dataclass(frozen=True)
class RoleSpec:
    """An immutable description of a single model role.

    Attributes
    ----------
    name:
        Unique role identifier (e.g. ``"skeleton_architect"``).
    model:
        The model bound to this role (e.g. ``"Claude"``).
    mission:
        A short human-readable statement of what the role is responsible for.
    enabled:
        Whether the role participates in orchestration. Optional roles default
        to ``True`` and can be switched off without editing the rest of the
        configuration.
    inputs / outputs:
        Declared artifacts the role consumes and produces. Used by the
        orchestrator to validate wiring and to build the execution report.
    metrics:
        Free-form metric names or targets the role reports against.
    secret_ref:
        An optional ``$VAULT:key`` reference naming the vault entry that holds
        this role's credential. Only the reference is stored in config — never
        the secret value.
    compute:
        The role's compute-backend link (standard output, or a user VPS /
        cloud / GPU). Populated by :class:`RoleRegistry`; defaults to a
        standard backend.
    """

    name: str
    model: str
    mission: str
    enabled: bool = True
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    secret_ref: Optional[str] = None
    compute: "object" = field(default=None)


class RoleRegistry:
    """Validate and expose the configured Edition 2 roles."""

    def __init__(self, roles: Mapping[str, Mapping[str, Any]],
                 vault: Optional[SecretsVault] = None) -> None:
        if not isinstance(roles, Mapping) or not roles:
            raise ConfigError("Configuration must define at least one role")
        self._vault = vault
        self._roles: Dict[str, RoleSpec] = {}
        for name, raw in roles.items():
            self._roles[name] = self._build_role(name, raw)

    # -- construction ------------------------------------------------------

    def _build_role(self, name: str, raw: Mapping[str, Any]) -> RoleSpec:
        if not isinstance(raw, Mapping):
            raise ConfigError(f"Role '{name}' must be a JSON object")
        model = raw.get("model")
        mission = raw.get("mission")
        if not model or not isinstance(model, str):
            raise ConfigError(f"Role '{name}' must define a non-empty 'model'")
        if not mission or not isinstance(mission, str):
            raise ConfigError(f"Role '{name}' must define a non-empty 'mission'")
        # Lazy import to avoid a circular dependency (backends imports this
        # module for RoleRegistry/ConfigError).
        from .backends import parse_backend
        return RoleSpec(
            name=name,
            model=model,
            mission=mission,
            enabled=bool(raw.get("enabled", True)),
            inputs=list(raw.get("inputs", [])),
            outputs=list(raw.get("outputs", [])),
            metrics=list(raw.get("metrics", [])),
            secret_ref=raw.get("secret_ref"),
            compute=parse_backend(raw.get("compute"), role_name=name),
        )

    # -- access ------------------------------------------------------------

    def all_roles(self) -> List[RoleSpec]:
        """Return every role, in configuration order."""
        return list(self._roles.values())

    def enabled_roles(self) -> List[RoleSpec]:
        """Return only the roles whose ``enabled`` flag is set."""
        return [role for role in self._roles.values() if role.enabled]

    def get(self, name: str) -> RoleSpec:
        """Look up a role by name, raising :class:`ConfigError` when unknown."""
        try:
            return self._roles[name]
        except KeyError as exc:
            raise ConfigError(f"Unknown role: '{name}'") from exc

    def resolve_secret(self, role_name: str) -> Optional[str]:
        """Resolve a role's secret reference through the vault.

        Returns ``None`` when the role has no secret reference, and raises
        :class:`ConfigError` when a reference exists but no vault is attached.
        """
        role = self.get(role_name)
        if not role.secret_ref:
            return None
        if self._vault is None:
            raise ConfigError(
                f"Role '{role_name}' references a secret but no vault is attached")
        return self._vault.resolve(role.secret_ref)

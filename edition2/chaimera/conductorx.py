"""ConductorX — the CHAiMERA orchestration conductor.

ConductorX sequences the enabled Edition 2 roles into a dependency-aware run
(a "symphony"). Each role executes as a *movement*; the conductor validates
that a movement's declared inputs are satisfied by earlier movements' outputs
before it is allowed to play, and records a structured result for each.

The output is a plain-text :class:`SymphonyReport` describing structure and
code-accuracy status for the user's desired output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from ..orchestrator import ConfigError, RoleRegistry, RoleSpec


@dataclass
class MovementResult:
    """The recorded outcome of a single orchestrated role (a movement)."""

    role: str
    model: str
    mission: str
    status: str = "pending"          # pending | ok | skipped | failed
    detail: str = ""
    consumed: List[str] = field(default_factory=list)
    produced: List[str] = field(default_factory=list)


@dataclass
class SymphonyReport:
    """An aggregate, human-readable report of a full orchestration run."""

    movements: List[MovementResult] = field(default_factory=list)

    @property
    def succeeded(self) -> int:
        return sum(1 for m in self.movements if m.status == "ok")

    @property
    def failed(self) -> int:
        return sum(1 for m in self.movements if m.status == "failed")

    @property
    def skipped(self) -> int:
        return sum(1 for m in self.movements if m.status == "skipped")

    def render(self) -> str:
        """Render the report as aligned plain text."""
        lines = [
            "CHAiMERA ConductorX — Symphony Report",
            "=" * 55,
        ]
        for index, movement in enumerate(self.movements, start=1):
            lines.append(
                f"{index:>2}. [{movement.status.upper():>7}] "
                f"{movement.role} ({movement.model}) — {movement.mission}")
            if movement.detail:
                lines.append(f"       {movement.detail}")
        lines.append("-" * 55)
        lines.append(
            f"Movements: {len(self.movements)}  "
            f"ok={self.succeeded}  failed={self.failed}  skipped={self.skipped}")
        return "\n".join(lines)


class ConductorX:
    """Sequence and validate the enabled roles into a single run."""

    def __init__(self, registry: RoleRegistry) -> None:
        self._registry = registry

    def conduct(self, only_enabled: bool = True,
                seeds: Optional[Set[str]] = None) -> SymphonyReport:
        """Run the symphony and return a :class:`SymphonyReport`.

        Parameters
        ----------
        only_enabled:
            When True (default), disabled roles are omitted entirely. When
            False, disabled roles are recorded as ``skipped`` movements so the
            report shows the full intended structure.
        seeds:
            Names of externally-supplied inputs (e.g. ``requirements_spec``)
            that are available before any movement runs.
        """
        roles = (self._registry.enabled_roles() if only_enabled
                 else self._registry.all_roles())
        report = SymphonyReport()
        available: Set[str] = set(seeds or ())
        for role in roles:
            result = self._play(role, available)
            report.movements.append(result)
            if result.status == "ok":
                available.update(result.produced)
        return report

    # -- internal ----------------------------------------------------------

    def _play(self, role: RoleSpec, available: Set[str]) -> MovementResult:
        result = MovementResult(role=role.name, model=role.model,
                                mission=role.mission)
        if not role.enabled:
            result.status = "skipped"
            result.detail = "role disabled in configuration"
            return result

        missing = [item for item in role.inputs if item not in available]
        result.consumed = list(role.inputs)
        result.produced = list(role.outputs)
        if missing:
            result.status = "failed"
            result.detail = "missing inputs: " + ", ".join(missing)
            return result

        result.status = "ok"
        produced = ", ".join(role.outputs) if role.outputs else "no artifacts"
        result.detail = f"produced: {produced}"
        return result


def build_default_registry(config: Dict,
                           vault: Optional[object] = None) -> RoleRegistry:
    """Build a :class:`RoleRegistry` from a loaded configuration mapping."""
    if not isinstance(config, dict) or "roles" not in config:
        raise ConfigError("Configuration must contain a 'roles' object")
    return RoleRegistry(config["roles"], vault=vault)  # type: ignore[arg-type]

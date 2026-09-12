"""Persona style model for the Assistant Persona & Analysis Engine.

A :class:`PersonaStyle` captures the assistant's (and the UI's) tone and
"personality" as a vector over a set of *graphical trait axes* (e.g.
``analytical`` / ``creative`` / ``driver`` / ``amiable``). "Fine-tuning" the
assistant is simply loading/merging a persona configuration — the same model
drives both the analysis pipeline and the UI's presentation style.
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping

# The default graphical personality axes the engine scores against.
DEFAULT_TRAIT_AXES = ("analytical", "creative", "driver", "amiable")


def _clamp01(value: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v))


class PersonaStyle:
    """A configurable tone/personality profile expressed over trait axes.

    ``traits`` maps an axis name to a 0.0-1.0 intensity. Unknown axes are kept
    so callers can extend the model, but every value is normalised into the
    inclusive ``[0, 1]`` range so downstream scoring is well behaved.
    """

    def __init__(
        self,
        name: str = "AicodeX Assistant",
        tone: str = "analytical",
        traits: Mapping[str, float] | None = None,
    ) -> None:
        self.name = str(name) if name else "AicodeX Assistant"
        self.tone = str(tone) if tone else "neutral"
        self.traits: Dict[str, float] = {
            str(axis): _clamp01(value) for axis, value in (traits or {}).items()
        }

    # -- construction ------------------------------------------------------
    @classmethod
    def default(cls) -> "PersonaStyle":
        """The out-of-the-box persona used when no config is supplied."""
        return cls(
            name="AicodeX Assistant",
            tone="analytical",
            traits={
                "analytical": 0.9,
                "creative": 0.4,
                "driver": 0.6,
                "amiable": 0.7,
            },
        )

    @classmethod
    def from_config(cls, data: Mapping[str, object] | None) -> "PersonaStyle":
        """Build a persona from the ``assistant.persona`` config block."""
        if not isinstance(data, Mapping):
            return cls.default()
        return cls(
            name=data.get("name", "AicodeX Assistant"),
            tone=data.get("tone", "analytical"),
            traits=data.get("traits", {}),
        )

    # -- fine-tuning -------------------------------------------------------
    def merge(self, overrides: Mapping[str, object] | None) -> "PersonaStyle":
        """Return a new persona fine-tuned by ``overrides``.

        Only the supplied keys change; trait values are merged (not replaced
        wholesale) so callers can nudge a single axis. This is the "fine tune
        the assistant / UI personnel style" operation.
        """
        if not isinstance(overrides, Mapping):
            return PersonaStyle(self.name, self.tone, dict(self.traits))
        traits = dict(self.traits)
        for axis, value in (overrides.get("traits") or {}).items():
            traits[str(axis)] = _clamp01(value)
        return PersonaStyle(
            name=overrides.get("name", self.name),
            tone=overrides.get("tone", self.tone),
            traits=traits,
        )

    # -- access ------------------------------------------------------------
    def trait(self, axis: str, default: float = 0.0) -> float:
        return self.traits.get(axis, default)

    def dominant_traits(self, axes: Iterable[str] | None = None) -> list:
        """Return ``(axis, value)`` pairs sorted by intensity, descending."""
        items = self.traits.items()
        if axes is not None:
            wanted = set(axes)
            items = [(a, v) for a, v in items if a in wanted]
        return sorted(items, key=lambda kv: kv[1], reverse=True)

    def as_dict(self) -> Dict[str, object]:
        return {"name": self.name, "tone": self.tone, "traits": dict(self.traits)}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"PersonaStyle(name={self.name!r}, tone={self.tone!r}, traits={self.traits!r})"

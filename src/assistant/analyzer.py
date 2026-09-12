"""Analyse incoming data against graphical personality types.

The :class:`IncomingDataAnalyzer` turns raw incoming text/data into a
:class:`TraitProfile` — a vector over the same graphical trait axes used by the
persona — plus a confidence score. The profile is what the solution matcher and
the TWINBRAIN + CCC.Ai reasoning layers consume.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, Mapping

from .persona import DEFAULT_TRAIT_AXES

# Keyword signals per graphical personality axis. The analyser is deliberately
# transparent (bag-of-signals) so its scores are explainable — matching the
# engine's "show the user why" requirement.
_AXIS_SIGNALS: Dict[str, tuple] = {
    "analytical": (
        "analy", "data", "logic", "metric", "measure", "benchmark", "profile",
        "evidence", "statistic", "reason", "prove", "test", "debug", "root cause",
        "quantif", "research",
    ),
    "creative": (
        "idea", "creat", "design", "imagine", "innovat", "brainstorm", "novel",
        "prototype", "art", "vision", "invent", "explore", "what if",
    ),
    "driver": (
        "deadline", "asap", "ship", "result", "goal", "fast", "now", "urgent",
        "deliver", "win", "decide", "action", "cut scope", "move",
    ),
    "amiable": (
        "team", "help", "together", "support", "feel", "stakeholder", "align",
        "pair", "collaborat", "listen", "people", "consensus", "share",
    ),
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-']+")


class TraitProfile:
    """A scored personality profile for a piece of incoming data."""

    def __init__(self, scores: Mapping[str, float], confidence: float, token_count: int = 0) -> None:
        self.scores: Dict[str, float] = {str(k): float(v) for k, v in scores.items()}
        self.confidence = max(0.0, min(1.0, float(confidence)))
        self.token_count = int(token_count)

    def dominant(self) -> str:
        """The highest-scoring axis, or ``""`` when the profile is empty."""
        if not self.scores:
            return ""
        return max(self.scores.items(), key=lambda kv: kv[1])[0]

    def dominant_traits(self) -> list:
        """Return ``(axis, score)`` pairs sorted by score, descending."""
        return sorted(self.scores.items(), key=lambda kv: kv[1], reverse=True)

    def as_dict(self) -> Dict[str, object]:
        return {
            "scores": dict(self.scores),
            "confidence": self.confidence,
            "token_count": self.token_count,
            "dominant": self.dominant(),
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"TraitProfile(dominant={self.dominant()!r}, confidence={self.confidence:.2f})"


class IncomingDataAnalyzer:
    """Scores incoming text/data against the graphical personality axes.

    ``axes`` defaults to :data:`DEFAULT_TRAIT_AXES`. Extra signal keywords can
    be supplied per-axis via ``signals`` to extend or override the built-ins.
    """

    def __init__(
        self,
        axes: Iterable[str] | None = None,
        signals: Mapping[str, Iterable[str]] | None = None,
    ) -> None:
        self.axes = list(axes) if axes else list(DEFAULT_TRAIT_AXES)
        merged: Dict[str, tuple] = {axis: tuple(_AXIS_SIGNALS.get(axis, ())) for axis in self.axes}
        for axis, words in (signals or {}).items():
            merged[str(axis)] = tuple(words)
        self._signals = merged

    def _score_axis(self, text: str, axis: str) -> float:
        signals = self._signals.get(axis, ())
        if not signals:
            return 0.0
        lowered = text.lower()
        hits = sum(1 for s in signals if s in lowered)
        # Normalise against the number of signals so each axis yields 0..1.
        return hits / float(len(signals))

    def analyze(self, data: object) -> TraitProfile:
        """Analyse ``data`` and return a :class:`TraitProfile` with confidence.

        ``data`` may be a string or any mapping/sequence that can be flattened
        to text. Confidence grows with how much signal was found relative to
        the input length, so empty / noise input yields low confidence (which
        downstream layers use to justify "we can't find a solution" answers).
        """
        text = self._to_text(data)
        tokens = _WORD_RE.findall(text)
        token_count = len(tokens)

        raw = {axis: self._score_axis(text, axis) for axis in self.axes}
        if token_count == 0:
            return TraitProfile({axis: 0.0 for axis in self.axes}, 0.0, token_count)

        total = sum(raw.values())
        if total <= 0.0:
            # No signal at all: report a flat, low-confidence profile so the
            # matcher/council can explain the miss rather than guess.
            return TraitProfile({axis: 0.0 for axis in self.axes}, 0.0, token_count)

        # Normalise to a distribution across axes (graphical profile), and set
        # confidence from signal density: more matched signal per token, plus a
        # saturating bonus for longer, richer input.
        scores = {axis: (value / total) for axis, value in raw.items()}
        hit_axes = sum(1 for v in raw.values() if v > 0.0)
        density = min(1.0, total)  # 0..1 based on fraction of signals hit
        length_bonus = min(0.3, token_count / 100.0)
        coverage_bonus = min(0.4, hit_axes / max(1, len(self.axes)) * 0.4)
        confidence = min(1.0, 0.3 + density * 0.3 + length_bonus + coverage_bonus)
        return TraitProfile(scores, round(confidence, 4), token_count)

    @staticmethod
    def _to_text(data: object) -> str:
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        if isinstance(data, Mapping):
            parts = []
            for key, value in data.items():
                parts.append(IncomingDataAnalyzer._to_text(key))
                parts.append(IncomingDataAnalyzer._to_text(value))
            return " ".join(p for p in parts if p)
        if isinstance(data, (list, tuple, set)):
            return " ".join(
                p for p in (IncomingDataAnalyzer._to_text(x) for x in data) if p
            )
        return str(data)

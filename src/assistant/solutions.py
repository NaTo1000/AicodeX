"""Map a personality profile to complete performance solutions.

The :class:`SolutionMatcher` looks up the best performance solution for a
:class:`~.analyzer.TraitProfile` from a configurable knowledge base. When no
entry matches, it does **not** fail silently — it explains *why* (which trait
requirements were unmet and how far off the profile was), satisfying the
"if can't find solutions then show the user why" requirement.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional

from .analyzer import TraitProfile


class KnowledgeEntry:
    """A single performance solution keyed by the traits it serves."""

    def __init__(
        self,
        entry_id: str,
        solution: str,
        traits: Mapping[str, float],
        min_confidence: float = 0.5,
    ) -> None:
        self.id = str(entry_id)
        self.solution = str(solution)
        self.traits: Dict[str, float] = {str(k): float(v) for k, v in (traits or {}).items()}
        self.min_confidence = max(0.0, min(1.0, float(min_confidence)))

    @classmethod
    def from_config(cls, data: Mapping[str, object]) -> "KnowledgeEntry":
        return cls(
            entry_id=data.get("id", "solution"),
            solution=data.get("solution", ""),
            traits=data.get("traits", {}),
            min_confidence=data.get("min_confidence", 0.5),
        )

    def fit_score(self, profile: TraitProfile) -> float:
        """How well ``profile`` satisfies this entry's trait requirements (0..1).

        Computed as the mean over required traits of ``min(profile, req)/req``,
        so a profile that meets every requirement scores 1.0. Confidence is a
        gate, not part of the score.
        """
        if not self.traits:
            return 0.0
        total = 0.0
        for axis, req in self.traits.items():
            have = profile.scores.get(axis, 0.0)
            total += min(have, req) / req if req > 0 else 1.0
        return total / len(self.traits)

    def unmet_traits(self, profile: TraitProfile) -> Dict[str, Dict[str, float]]:
        """Required traits the profile falls short on, with the shortfall."""
        gaps: Dict[str, Dict[str, float]] = {}
        for axis, req in self.traits.items():
            have = profile.scores.get(axis, 0.0)
            if have < req:
                gaps[axis] = {"required": req, "actual": round(have, 4)}
        return gaps


class SolutionMatch:
    """The result of matching: either a solution or a reasoned explanation."""

    def __init__(
        self,
        matched: bool,
        entry: Optional[KnowledgeEntry] = None,
        score: float = 0.0,
        explanation: str = "",
        gaps: Optional[Dict[str, Dict[str, float]]] = None,
        confidence: float = 0.0,
    ) -> None:
        self.matched = bool(matched)
        self.entry = entry
        self.score = round(float(score), 4)
        self.explanation = explanation
        self.gaps = gaps or {}
        self.confidence = float(confidence)

    @property
    def solution(self) -> str:
        return self.entry.solution if self.entry else ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "matched": self.matched,
            "solution_id": self.entry.id if self.entry else None,
            "solution": self.solution,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "gaps": self.gaps,
        }


class SolutionMatcher:
    """Matches trait profiles against the knowledge base with explanations."""

    def __init__(self, knowledge_base: Optional[List[KnowledgeEntry]] = None) -> None:
        self.knowledge_base: List[KnowledgeEntry] = list(knowledge_base or [])

    @classmethod
    def from_config(cls, entries: object) -> "SolutionMatcher":
        kb: List[KnowledgeEntry] = []
        if isinstance(entries, list):
            for raw in entries:
                if isinstance(raw, Mapping):
                    kb.append(KnowledgeEntry.from_config(raw))
        return cls(kb)

    def match(self, profile: TraitProfile) -> SolutionMatch:
        """Return the best :class:`SolutionMatch` for ``profile``.

        If nothing meets its confidence gate / trait requirements, return a
        match with ``matched=False`` and a human-readable ``explanation`` of
        the shortfall (plus the per-trait gaps for the closest entry).
        """
        if not self.knowledge_base:
            return SolutionMatch(
                matched=False,
                explanation=(
                    "No performance solutions are configured in the knowledge "
                    "base, so there is nothing to match this profile against."
                ),
                confidence=profile.confidence,
            )

        # Rank entries by fit; the closest entry drives the explanation on miss.
        scored = sorted(
            ((entry.fit_score(profile), entry) for entry in self.knowledge_base),
            key=lambda pair: pair[0],
            reverse=True,
        )
        best_score, best_entry = scored[0]

        if profile.confidence < best_entry.min_confidence:
            return SolutionMatch(
                matched=False,
                entry=best_entry,
                score=best_score,
                confidence=profile.confidence,
                explanation=(
                    f"The closest solution '{best_entry.id}' needs confidence "
                    f">= {best_entry.min_confidence:.2f}, but the analysis only "
                    f"reached {profile.confidence:.2f}. Provide more specific "
                    "input so the engine can justify a solution."
                ),
                gaps=best_entry.unmet_traits(profile),
            )

        gaps = best_entry.unmet_traits(profile)
        if gaps:
            gap_text = "; ".join(
                f"'{axis}' needs {g['required']:.2f} but profile has {g['actual']:.2f}"
                for axis, g in gaps.items()
            )
            return SolutionMatch(
                matched=False,
                entry=best_entry,
                score=best_score,
                confidence=profile.confidence,
                explanation=(
                    f"No configured solution fully fits. Closest is "
                    f"'{best_entry.id}' (fit {best_score:.2f}); unmet traits: "
                    f"{gap_text}."
                ),
                gaps=gaps,
            )

        return SolutionMatch(
            matched=True,
            entry=best_entry,
            score=best_score,
            confidence=profile.confidence,
            explanation=(
                f"Matched '{best_entry.id}' (fit {best_score:.2f}, confidence "
                f"{profile.confidence:.2f})."
            ),
        )

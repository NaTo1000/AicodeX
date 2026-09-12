"""CCC.Ai — the Corpus Callosum Council.

The council is the deliberation and truth-justification layer. It sits between
the two TWINBRAIN hemispheres (the corpus callosum connects the hemispheres),
weighs their candidate pathways, and makes a rational decision — gated by
evidence (truth-justification) so a low-evidence pathway is never passed off
as fact.
"""

from __future__ import annotations

from typing import List, Optional

from .twinbrain import Pathway


class CouncilDecision:
    """The outcome of the council's deliberation."""

    def __init__(
        self,
        chosen: Optional[Pathway],
        justified: bool,
        justification: str,
        deliberation: List[dict],
        confidence: float,
    ) -> None:
        self.chosen = chosen
        self.justified = bool(justified)
        self.justification = str(justification)
        self.deliberation = list(deliberation)
        self.confidence = float(confidence)

    def as_dict(self):
        return {
            "chosen": self.chosen.as_dict() if self.chosen else None,
            "justified": self.justified,
            "justification": self.justification,
            "deliberation": self.deliberation,
            "confidence": self.confidence,
        }


class CorpusCallosumCouncil:
    """Deliberates over candidate pathways and justifies the final decision.

    ``min_confidence`` and ``min_justification`` are the truth gates: a pathway
    must carry at least ``min_justification`` evidence for the council to adopt
    it as *justified truth*; otherwise the council still returns the best
    candidate but marks it unjustified and explains the shortfall.
    """

    def __init__(self, min_confidence: float = 0.5, min_justification: float = 0.4) -> None:
        self.min_confidence = max(0.0, min(1.0, float(min_confidence)))
        self.min_justification = max(0.0, min(1.0, float(min_justification)))

    @classmethod
    def from_config(cls, data) -> "CorpusCallosumCouncil":
        if isinstance(data, dict):
            return cls(
                min_confidence=data.get("min_confidence", 0.5),
                min_justification=data.get("min_justification", 0.4),
            )
        return cls()

    def deliberate(
        self,
        pathways: List[Pathway],
        profile_confidence: float,
        retained_prior: Optional[float] = None,
    ) -> CouncilDecision:
        """Choose a pathway and justify the decision.

        ``retained_prior`` is an optional 0..1 prior from the retention store
        (how often this kind of question has succeeded before); it nudges the
        effective confidence so rational decisions account for retained
        history/returns.
        """
        if not pathways:
            return CouncilDecision(
                chosen=None,
                justified=False,
                justification="No candidate pathways were proposed.",
                deliberation=[],
                confidence=0.0,
            )

        effective_confidence = float(profile_confidence)
        if retained_prior is not None:
            effective_confidence = min(1.0, 0.7 * profile_confidence + 0.3 * retained_prior)

        deliberation = []
        best: Optional[Pathway] = None
        best_score = -1.0
        for p in pathways:
            # Rational score blends the pathway's evidence with confidence.
            score = round(0.6 * p.evidence + 0.4 * effective_confidence, 4)
            deliberation.append(
                {
                    "hemisphere": p.hemisphere,
                    "title": p.title,
                    "evidence": p.evidence,
                    "score": score,
                }
            )
            if score > best_score:
                best_score = score
                best = p

        justified = (
            best is not None
            and best.evidence >= self.min_justification
            and effective_confidence >= self.min_confidence
        )
        if best is None:
            justification = "The council could not select any pathway."
        elif justified:
            justification = (
                f"Council selected the {best.hemisphere}-brain pathway "
                f"'{best.title}' (evidence {best.evidence:.2f}, confidence "
                f"{effective_confidence:.2f}) — both truth gates cleared."
            )
        else:
            reasons = []
            if best.evidence < self.min_justification:
                reasons.append(
                    f"evidence {best.evidence:.2f} < required {self.min_justification:.2f}"
                )
            if effective_confidence < self.min_confidence:
                reasons.append(
                    f"confidence {effective_confidence:.2f} < required {self.min_confidence:.2f}"
                )
            justification = (
                f"Council favours the {best.hemisphere}-brain pathway "
                f"'{best.title}' but cannot assert it as truth: "
                + "; ".join(reasons)
                + "."
            )

        return CouncilDecision(
            chosen=best,
            justified=justified,
            justification=justification,
            deliberation=deliberation,
            confidence=round(effective_confidence, 4),
        )

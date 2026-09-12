"""TWINBRAIN: dual-hemisphere pathway reasoning.

The twin brain produces *candidate pathways* for a question from two
complementary hemispheres:

* **left** — analytic: grounded in the measured trait profile and the matched
  solution (evidence-driven), and
* **right** — associative: a broader, persona-styled reframing that explores
  alternatives and next steps.

The candidates are handed to the CCC.Ai council for deliberation and
truth-justification.
"""

from __future__ import annotations

from typing import List

from .analyzer import TraitProfile
from .persona import PersonaStyle
from .solutions import SolutionMatch


class Pathway:
    """A single candidate decision pathway proposed by one hemisphere."""

    def __init__(
        self,
        hemisphere: str,
        title: str,
        rationale: str,
        evidence: float,
        steps: List[str] | None = None,
    ) -> None:
        self.hemisphere = str(hemisphere)
        self.title = str(title)
        self.rationale = str(rationale)
        # Evidence strength in [0, 1]; the council gates on this for truth.
        self.evidence = max(0.0, min(1.0, float(evidence)))
        self.steps = list(steps or [])

    def as_dict(self):
        return {
            "hemisphere": self.hemisphere,
            "title": self.title,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "steps": list(self.steps),
        }


class TwinBrain:
    """Generates left/right candidate pathways from an analysis + match."""

    def __init__(self, persona: PersonaStyle | None = None) -> None:
        self.persona = persona or PersonaStyle.default()

    def propose(self, question: str, profile: TraitProfile, match: SolutionMatch) -> List[Pathway]:
        """Produce the analytic (left) and associative (right) candidates."""
        dominant = profile.dominant() or "balanced"
        return [
            self._left(question, profile, match, dominant),
            self._right(question, profile, match, dominant),
        ]

    # -- hemispheres -------------------------------------------------------
    def _left(self, question: str, profile: TraitProfile, match: SolutionMatch, dominant: str) -> Pathway:
        if match.matched:
            rationale = (
                f"Analytic read: the input is '{dominant}'-dominant "
                f"(confidence {profile.confidence:.2f}) and the knowledge base "
                f"provides a fitting solution, so the evidence-backed pathway is "
                f"to apply it directly."
            )
            steps = [
                f"Confirm the '{dominant}' profile with the requester.",
                "Apply the matched performance solution.",
                "Measure the outcome against the baseline.",
            ]
            evidence = max(profile.confidence, match.score)
            title = f"Apply matched solution '{match.entry.id}'"
        else:
            rationale = (
                f"Analytic read: confidence {profile.confidence:.2f} / fit "
                f"{match.score:.2f} did not clear the gate, so the honest "
                "pathway is to gather more data before acting."
            )
            steps = [
                "Ask for more specific input to raise confidence.",
                "Re-run the analysis with the richer input.",
            ]
            evidence = min(profile.confidence, match.score if match.score else profile.confidence)
            title = "Gather more data before deciding"
        return Pathway("left", title, rationale, evidence, steps)

    def _right(self, question: str, profile: TraitProfile, match: SolutionMatch, dominant: str) -> Pathway:
        tone = self.persona.tone
        alts = [a for a, v in profile.dominant_traits() if a != dominant][:2]
        if match.matched:
            rationale = (
                f"Associative read ({tone} persona): while the profile is "
                f"'{dominant}'-dominant, reframing the question through adjacent "
                f"strengths ({', '.join(alts) or 'none'}) may surface a simpler "
                "or more creative route."
            )
            steps = [
                "Restate the goal in the requester's own terms.",
                f"Explore an adjacent '{alts[0] if alts else 'alternative'}' approach.",
                "Combine the matched solution with the reframe if it helps.",
            ]
            # The associative path is less evidence-bound by design.
            evidence = max(0.2, match.score * 0.6)
            title = "Reframe and explore an adjacent approach"
        else:
            rationale = (
                f"Associative read ({tone} persona): no stored solution fits, so "
                "explore analogies and adjacent trait strengths to seed a new, "
                "candidate solution the knowledge base lacks."
            )
            steps = [
                "List analogous problems that do have solutions.",
                "Draft a candidate solution and record it for review.",
            ]
            evidence = max(0.15, profile.confidence * 0.5)
            title = "Explore analogies to seed a new solution"
        return Pathway("right", title, rationale, evidence, steps)

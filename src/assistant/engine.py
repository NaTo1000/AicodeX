"""Top-level AssistantEngine orchestrating the full pipeline.

Wires the pieces together for a single ``process(question)`` call:

    PEC router (term control + retention prior)
      → IncomingDataAnalyzer (trait profile + confidence)
      → SolutionMatcher (solution or why-not explanation)
      → TwinBrain (left/right candidate pathways)
      → CorpusCallosumCouncil (deliberation + truth-justified decision)
      → retention records the return

The engine is built from the ``assistant`` block of the app config via
:meth:`AssistantEngine.from_config`.
"""

from __future__ import annotations

from typing import Callable, Optional

from .analyzer import IncomingDataAnalyzer, TraitProfile
from .council import CorpusCallosumCouncil, CouncilDecision
from .persona import DEFAULT_TRAIT_AXES, PersonaStyle
from .router import PECRouter, RetentionStore, RouterResult, TermControl
from .solutions import SolutionMatch, SolutionMatcher
from .twinbrain import Pathway, TwinBrain


class AssistantReport:
    """A structured, UI-ready report for one processed question."""

    def __init__(
        self,
        question: str,
        persona: PersonaStyle,
        profile: TraitProfile,
        match: SolutionMatch,
        pathways: list,
        decision: CouncilDecision,
        routing: RouterResult,
    ) -> None:
        self.question = question
        self.persona = persona
        self.profile = profile
        self.match = match
        self.pathways = list(pathways)
        self.decision = decision
        self.routing = routing

    def summary(self) -> str:
        """A short human-readable summary (used by the overlay UI)."""
        lines = [
            f"Persona: {self.persona.name} (tone: {self.persona.tone})",
            f"Profile: dominant={self.profile.dominant() or 'none'}, "
            f"confidence={self.profile.confidence:.2f}",
        ]
        if self.match.matched:
            lines.append(f"Solution: {self.match.solution}")
        else:
            lines.append(f"No solution: {self.match.explanation}")
        if self.decision.chosen is not None:
            verdict = "justified" if self.decision.justified else "not yet justified"
            lines.append(
                f"Council ({verdict}): {self.decision.chosen.title}"
            )
        lines.append(f"Why: {self.decision.justification}")
        return "\n".join(lines)

    def as_dict(self):
        return {
            "question": self.question,
            "persona": self.persona.as_dict(),
            "profile": self.profile.as_dict(),
            "match": self.match.as_dict(),
            "pathways": [p.as_dict() for p in self.pathways],
            "decision": self.decision.as_dict(),
            "routing": self.routing.as_dict(),
        }


class AssistantEngine:
    """Orchestrates persona, analysis, matching, reasoning, and routing."""

    def __init__(
        self,
        persona: Optional[PersonaStyle] = None,
        analyzer: Optional[IncomingDataAnalyzer] = None,
        matcher: Optional[SolutionMatcher] = None,
        twinbrain: Optional[TwinBrain] = None,
        council: Optional[CorpusCallosumCouncil] = None,
        router: Optional[PECRouter] = None,
    ) -> None:
        self.persona = persona or PersonaStyle.default()
        self.analyzer = analyzer or IncomingDataAnalyzer()
        self.matcher = matcher or SolutionMatcher()
        self.twinbrain = twinbrain or TwinBrain(self.persona)
        self.council = council or CorpusCallosumCouncil()
        self.router = router or PECRouter()

    @classmethod
    def from_config(cls, config, clock: Optional[Callable[[], float]] = None) -> "AssistantEngine":
        """Build an engine from the ``assistant`` config block.

        ``config`` may be a mapping containing an ``assistant`` key, or the
        assistant block itself. ``clock`` is injectable for deterministic tests.
        """
        block = config.get("assistant", config) if isinstance(config, dict) else {}
        if not isinstance(block, dict):
            block = {}

        import time

        persona = PersonaStyle.from_config(block.get("persona"))
        axes = block.get("trait_axes") or list(DEFAULT_TRAIT_AXES)
        analyzer = IncomingDataAnalyzer(axes=axes)
        matcher = SolutionMatcher.from_config(block.get("knowledge_base", []))
        council = CorpusCallosumCouncil.from_config(block.get("council"))
        retention = RetentionStore.from_config(
            block.get("retention"), clock=clock or time.time
        )
        router = PECRouter(TermControl(), retention)
        twinbrain = TwinBrain(persona)
        return cls(persona, analyzer, matcher, twinbrain, council, router)

    def fine_tune(self, overrides) -> "AssistantEngine":
        """Return a new engine with a fine-tuned persona (UI + assistant style)."""
        persona = self.persona.merge(overrides)
        return AssistantEngine(
            persona=persona,
            analyzer=self.analyzer,
            matcher=self.matcher,
            twinbrain=TwinBrain(persona),
            council=self.council,
            router=self.router,
        )

    def process(self, question: object) -> AssistantReport:
        """Run the full pipeline for ``question`` and record the return."""
        text = question if isinstance(question, str) else self.analyzer._to_text(question)

        routing = self.router.spread(text)
        profile = self.analyzer.analyze(text)
        match = self.matcher.match(profile)
        pathways = self.twinbrain.propose(text, profile, match)
        decision = self.council.deliberate(pathways, profile.confidence, retained_prior=routing.prior)

        chosen_title = decision.chosen.title if decision.chosen else None
        self.router.record_return(routing, text, chosen_title, decision.justified, decision.confidence)

        return AssistantReport(text, self.persona, profile, match, pathways, decision, routing)

"""Assistant Persona & Analysis Engine for AicodeX.

A self-contained, dependency-free engine that:

* fine-tunes the assistant + UI persona style (:mod:`persona`),
* analyses incoming data against graphical personality types (:mod:`analyzer`),
* matches a profile to complete performance solutions, explaining itself when
  no solution can be found (:mod:`solutions`),
* reasons about pathways with a dual-hemisphere TWINBRAIN (:mod:`twinbrain`),
* deliberates and justifies truth via the CCC.Ai Corpus Callosum Council
  (:mod:`council`),
* spreads a question through PEC term-control channels with data retention so
  decisions are justified by retained history (:mod:`router`).
"""

from .persona import PersonaStyle, DEFAULT_TRAIT_AXES
from .analyzer import IncomingDataAnalyzer, TraitProfile
from .solutions import SolutionMatcher, SolutionMatch, KnowledgeEntry
from .twinbrain import TwinBrain, Pathway
from .council import CorpusCallosumCouncil, CouncilDecision
from .router import (
    PECRouter,
    TermControl,
    RetentionStore,
    RouterResult,
)
from .engine import AssistantEngine, AssistantReport

__all__ = [
    "PersonaStyle",
    "DEFAULT_TRAIT_AXES",
    "IncomingDataAnalyzer",
    "TraitProfile",
    "SolutionMatcher",
    "SolutionMatch",
    "KnowledgeEntry",
    "TwinBrain",
    "Pathway",
    "CorpusCallosumCouncil",
    "CouncilDecision",
    "PECRouter",
    "TermControl",
    "RetentionStore",
    "RouterResult",
    "AssistantEngine",
    "AssistantReport",
]

"""PEC term-control routing with data retention.

The :class:`PECRouter` "spreads the question through the channels" under a
*term control system*: it normalises the question into controlled terms, routes
those terms through the engine's channels (analysis → solutions → twinbrain →
council), and records the query, decision, and return in a
:class:`RetentionStore`. Retained records give the council a rational prior
(decisions based on data retention and returns).
"""

from __future__ import annotations

import re
import time
from collections import Counter
from typing import Callable, Dict, List, Optional

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-']+")

# A small stop-word list for the term-control normaliser.
_STOP_WORDS = frozenset(
    "a an the is are was were be been being and or but if then of to in on for "
    "with as at by from it its this that these those i you we they he she do "
    "does did can could should would will just not no me my your their our".split()
)

# The channels a question is spread through, in order.
CHANNELS = ("analysis", "solutions", "twinbrain", "council")


class TermControl:
    """Normalises free text into a controlled set of significant terms."""

    def __init__(self, stop_words=frozenset(_STOP_WORDS)) -> None:
        self.stop_words = frozenset(stop_words)

    def controlled_terms(self, text: str, limit: int = 12) -> List[str]:
        """Return the significant, de-duplicated terms of ``text`` in order."""
        if not text:
            return []
        counts: Counter = Counter()
        order: List[str] = []
        for raw in _WORD_RE.findall(text.lower()):
            if raw in self.stop_words:
                continue
            if raw not in counts:
                order.append(raw)
            counts[raw] += 1
        # Prefer frequent terms but keep first-seen order as a stable tie-break.
        ranked = sorted(order, key=lambda t: (-counts[t], order.index(t)))
        return ranked[:limit]

    def key(self, text: str) -> str:
        """A stable retention key for a question (its controlled terms)."""
        return " ".join(sorted(self.controlled_terms(text)))


class RetentionStore:
    """In-memory retention of queries, decisions, and returns.

    Bounded by ``max_records`` (oldest dropped first). Each record links the
    controlled-term key, the chosen pathway, whether the council justified it,
    and the confidence, so future decisions can be justified by retained
    history/returns.
    """

    def __init__(self, enabled: bool = True, max_records: int = 200, clock: Callable[[], float] = time.time) -> None:
        self.enabled = bool(enabled)
        self.max_records = max(1, int(max_records))
        self._clock = clock
        self._records: List[Dict[str, object]] = []

    @classmethod
    def from_config(cls, data, clock: Callable[[], float] = time.time) -> "RetentionStore":
        if isinstance(data, dict):
            return cls(
                enabled=data.get("enabled", True),
                max_records=data.get("max_records", 200),
                clock=clock,
            )
        return cls(clock=clock)

    def record(
        self,
        key: str,
        question: str,
        chosen: Optional[str],
        justified: bool,
        confidence: float,
    ) -> None:
        if not self.enabled:
            return
        self._records.append(
            {
                "key": key,
                "question": question,
                "chosen": chosen,
                "justified": bool(justified),
                "confidence": float(confidence),
                "ts": self._clock(),
            }
        )
        if len(self._records) > self.max_records:
            del self._records[: len(self._records) - self.max_records]

    def prior(self, key: str) -> Optional[float]:
        """A 0..1 prior for ``key`` from retained returns.

        The fraction of past records for this key that were justified, blended
        with their average confidence. ``None`` when there is no history.
        """
        if not self.enabled:
            return None
        rows = [r for r in self._records if r["key"] == key]
        if not rows:
            return None
        justified_rate = sum(1 for r in rows if r["justified"]) / len(rows)
        avg_conf = sum(r["confidence"] for r in rows) / len(rows)
        return round(0.5 * justified_rate + 0.5 * avg_conf, 4)

    def __len__(self) -> int:
        return len(self._records)

    def records(self) -> List[Dict[str, object]]:
        return list(self._records)


class RouterResult:
    """The outcome of spreading a question through the channels."""

    def __init__(self, terms: List[str], channels: List[str], key: str, prior: Optional[float]) -> None:
        self.terms = list(terms)
        self.channels = list(channels)
        self.key = key
        self.prior = prior

    def as_dict(self):
        return {
            "terms": self.terms,
            "channels": self.channels,
            "key": self.key,
            "prior": self.prior,
        }


class PECRouter:
    """Spreads a question through the engine's channels under term control."""

    def __init__(self, term_control: Optional[TermControl] = None, retention: Optional[RetentionStore] = None) -> None:
        self.term_control = term_control or TermControl()
        self.retention = retention or RetentionStore()

    def spread(self, question: str) -> RouterResult:
        """Normalise ``question`` and prepare its channel spread + prior."""
        terms = self.term_control.controlled_terms(question)
        key = self.term_control.key(question)
        prior = self.retention.prior(key)
        return RouterResult(terms, list(CHANNELS), key, prior)

    def record_return(self, result: RouterResult, question: str, chosen: Optional[str], justified: bool, confidence: float) -> None:
        """Record the decision/return so future routing is history-aware."""
        self.retention.record(result.key, question, chosen, justified, confidence)

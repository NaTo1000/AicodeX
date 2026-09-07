"""Crossover code & emulation database for AicodeX Edition 2.

A database of *crossover* mappings: how a construct written in one language is
emulated in another with **precision accuracy**. Each entry records the source
construct, its faithful emulation in the target language, and the style notes
needed to keep the rewrite idiomatic.

Standard library only; deterministic; entries are validated on load.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

from .orchestrator import ConfigError


@dataclass(frozen=True)
class CrossoverEntry:
    """A single crossover/emulation mapping.

    Attributes
    ----------
    source_lang / target_lang:
        The languages being mapped between (e.g. ``python`` → ``swift``).
    construct:
        The construct being emulated (e.g. ``"list comprehension"``).
    source:
        The construct as written in the source language.
    emulation:
        The precision-accurate emulation in the target language.
    notes:
        Style/formatting notes to keep the rewrite faithful to the user's
        code-writing style.
    """

    source_lang: str
    target_lang: str
    construct: str
    source: str
    emulation: str
    notes: str = ""

    def key(self) -> Tuple[str, str, str]:
        return (self.source_lang, self.target_lang, self.construct)


class CrossoverDatabase:
    """A validated store of crossover/emulation entries."""

    def __init__(self, entries: Optional[Mapping[str, Mapping[str, object]]] = None) -> None:
        self._entries: Dict[Tuple[str, str, str], CrossoverEntry] = {}
        for name, raw in (entries or {}).items():
            entry = self._build(name, raw)
            self._entries[entry.key()] = entry

    # -- construction ------------------------------------------------------

    @staticmethod
    def _build(name: str, raw: Mapping[str, object]) -> CrossoverEntry:
        if not isinstance(raw, Mapping):
            raise ConfigError(f"Crossover entry '{name}' must be a JSON object")
        required = ("source_lang", "target_lang", "construct", "source", "emulation")
        missing = [k for k in required if not raw.get(k)]
        if missing:
            raise ConfigError(
                f"Crossover entry '{name}' is missing: {', '.join(missing)}")
        return CrossoverEntry(
            source_lang=str(raw["source_lang"]),
            target_lang=str(raw["target_lang"]),
            construct=str(raw["construct"]),
            source=str(raw["source"]),
            emulation=str(raw["emulation"]),
            notes=str(raw.get("notes", "")),
        )

    # -- access --------------------------------------------------------------

    def add(self, entry: CrossoverEntry) -> None:
        self._entries[entry.key()] = entry

    def all(self) -> List[CrossoverEntry]:
        return list(self._entries.values())

    def languages(self) -> List[str]:
        langs = {e.source_lang for e in self._entries.values()}
        langs |= {e.target_lang for e in self._entries.values()}
        return sorted(langs)

    def lookup(self, source_lang: str, target_lang: str,
               construct: str) -> Optional[CrossoverEntry]:
        """Return the exact entry for a (source, target, construct) triple."""
        return self._entries.get((source_lang, target_lang, construct))

    def find(self, source_lang: Optional[str] = None,
             target_lang: Optional[str] = None) -> List[CrossoverEntry]:
        """Return entries filtered by source and/or target language."""
        results = []
        for entry in self._entries.values():
            if source_lang and entry.source_lang != source_lang:
                continue
            if target_lang and entry.target_lang != target_lang:
                continue
            results.append(entry)
        return results

    def emulate(self, source_lang: str, target_lang: str,
                construct: str) -> Optional[str]:
        """Return the precise emulation text for a construct, if known."""
        entry = self.lookup(source_lang, target_lang, construct)
        return entry.emulation if entry else None

    # -- reporting -----------------------------------------------------------

    def render(self) -> str:
        lines = ["AicodeX Edition 2 — Crossover & Emulation Database", "=" * 55]
        for entry in self.all():
            lines.append(
                f"  {entry.source_lang} -> {entry.target_lang}: {entry.construct}")
        lines.append("-" * 55)
        lines.append(f"entries: {len(self._entries)}  "
                     f"languages: {', '.join(self.languages()) or 'none'}")
        return "\n".join(lines)

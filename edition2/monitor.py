"""Realtime monitor system for AicodeX Edition 2.

Every component feeds a :class:`MonitorSystem` through a per-component
**valve**. Valves batch realtime metrics and forward them to the conductor
(CHAiMERA ConductorX) for *enhancement management*, and to the database
analysis coordination hooks for *database analysis management* — keeping
innovation and future-development signals flowing.

The monitor ticks on a configurable realtime interval (default **0.5 s**) and
renders a live metrics display. Standard library only; deterministic when the
clock is injected, so it is fully testable offline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class MetricSample:
    """A single realtime metric sample from a component."""

    component: str
    name: str
    value: float
    timestamp: float = 0.0


@dataclass
class Valve:
    """A per-component valve that batches samples bound for the conductor.

    The valve stays *open* while the component is healthy; closing it stops
    forwarding (e.g. when a component is quiesced).
    """

    component: str
    open: bool = True
    pending: List[MetricSample] = field(default_factory=list)

    def send(self, sample: MetricSample) -> None:
        if self.open:
            self.pending.append(sample)

    def flush(self) -> List[MetricSample]:
        """Drain the batched samples (called on each monitor tick)."""
        batch, self.pending = self.pending, []
        return batch


class MonitorSystem:
    """Collects component metrics via valves and routes them onward.

    Parameters
    ----------
    refresh_interval:
        Realtime refresh interval in seconds (default ``0.5``).
    conductor:
        Optional callable receiving each tick's batched samples for
        enhancement management (the CHAiMERA ConductorX hook).
    db_analyzer:
        Optional callable receiving each tick's batched samples for database
        analysis management coordination.
    clock:
        Time source; injected for determinism in tests.
    """

    def __init__(self, refresh_interval: float = 0.5,
                 conductor: Optional[Callable[[List[MetricSample]], None]] = None,
                 db_analyzer: Optional[Callable[[List[MetricSample]], None]] = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if refresh_interval <= 0:
            raise ValueError("refresh_interval must be > 0")
        self.refresh_interval = float(refresh_interval)
        self._conductor = conductor
        self._db = db_analyzer
        self._clock = clock
        self._valves: Dict[str, Valve] = {}
        self._last_tick: Optional[float] = None
        self.ticks: int = 0

    # -- valve management -----------------------------------------------------

    def valve(self, component: str) -> Valve:
        """Return (creating if needed) the valve for a component."""
        return self._valves.setdefault(component, Valve(component=component))

    def components(self) -> List[str]:
        return sorted(self._valves)

    # -- realtime loop ---------------------------------------------------------

    def tick(self) -> List[MetricSample]:
        """Flush all open valves and forward the batch to conductor + DB.

        Returns the batch of samples forwarded this tick.
        """
        batch: List[MetricSample] = []
        now = self._clock()
        for component in self.components():
            for sample in self._valves[component].flush():
                sample.timestamp = now
                batch.append(sample)
        self._last_tick = now
        self.ticks += 1
        if batch:
            if self._conductor is not None:
                self._conductor(batch)
            if self._db is not None:
                self._db(batch)
        return batch

    def due(self) -> bool:
        """Whether another tick is due (>= refresh_interval since last tick)."""
        if self._last_tick is None:
            return True
        return (self._clock() - self._last_tick) >= self.refresh_interval

    def run_once(self) -> Optional[List[MetricSample]]:
        """Tick only when the realtime interval has elapsed."""
        if self.due():
            return self.tick()
        return None

    # -- display -----------------------------------------------------------------

    def render(self) -> str:
        """Render the live metrics display as plain text."""
        lines = ["AicodeX Edition 2 — Realtime Monitor", "=" * 55,
                 f"refresh interval: {self.refresh_interval:.2f}s   "
                 f"ticks: {self.ticks}",
                 f"valves: {len(self._valves)} "
                 f"({sum(1 for v in self._valves.values() if v.open)} open)"]
        for component in self.components():
            valve = self._valves[component]
            state = "open " if valve.open else "closed"
            lines.append(f"  [{state}] {component:<24} pending={len(valve.pending)}")
        return "\n".join(lines)

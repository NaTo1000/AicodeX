"""Hive cluster of model-driven VMware worker bots.

A :class:`Hive` owns a set of :class:`VMwareWorkerBot` instances — one per
enabled model role (or per configured need). The cluster runs three phases,
the first in parallel:

1. **Analyse** — every bot samples its bandwidth concurrently and reports its
   current load, the gaps it sees, and whether it sits at a peak or in a
   trough.
2. **Balance** — load is shed from peak-saturated bots into trough-idle bots
   until no bot is above the peak threshold (or no trough capacity remains).
3. **Patch** — any missing data bits detected during analysis are patched with
   updated innovation-research results (the Mistral ``research_dev`` role).

The implementation is deliberately dependency-free and deterministic when load
and bandwidth samples are injected, which keeps it fully testable offline.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

from ..orchestrator import RoleSpec


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class BotReport:
    """A single worker bot's view of its bandwidth and load."""

    bot: str
    model: str
    load: float                      # current offered load (0..capacity)
    capacity: float                  # maximum load the bot can hold
    bandwidth_mbps: float            # measured bandwidth
    gaps: List[str] = field(default_factory=list)       # bandwidth gaps seen
    state: str = "idle"              # idle | peak | trough

    @property
    def utilisation(self) -> float:
        """Fraction of capacity currently in use (0.0 – 1.0)."""
        if self.capacity <= 0:
            return 0.0
        return max(0.0, min(1.0, self.load / self.capacity))


@dataclass
class LoadBalanceResult:
    """Record of load moved between bots during balancing."""

    moves: List[Dict[str, object]] = field(default_factory=list)

    @property
    def moved_total(self) -> float:
        return float(sum(m["amount"] for m in self.moves))


@dataclass
class DataPatch:
    """A patch that fills a missing data bit with a research result."""

    bit: str
    source_model: str
    innovation: str


@dataclass
class HiveReport:
    """Aggregate result of a full hive run."""

    bots: List[BotReport] = field(default_factory=list)
    balance: LoadBalanceResult = field(default_factory=LoadBalanceResult)
    patches: List[DataPatch] = field(default_factory=list)

    def render(self) -> str:
        lines = ["AicodeX Hive — Cluster Report", "=" * 55]
        for bot in self.bots:
            lines.append(
                f"  {bot.bot:<22} {bot.model:<9} "
                f"load={bot.load:>5.1f}/{bot.capacity:<5.1f} "
                f"({bot.utilisation:>5.0%})  bw={bot.bandwidth_mbps:>7.1f}Mbps  "
                f"state={bot.state}")
        lines.append("-" * 55)
        lines.append(f"Load rebalanced: {self.balance.moved_total:.1f} units "
                     f"across {len(self.balance.moves)} move(s)")
        for move in self.balance.moves:
            lines.append(f"    {move['from']} -> {move['to']}: {move['amount']:.1f}")
        lines.append(f"Data patches applied: {len(self.patches)}")
        for patch in self.patches:
            lines.append(f"    {patch.bit} <= {patch.innovation} "
                         f"[{patch.source_model}]")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Worker bot
# ---------------------------------------------------------------------------

class VMwareWorkerBot:
    """A lightweight model-driven VMware worker bot.

    Parameters
    ----------
    role:
        The model role this bot works for.
    capacity:
        Maximum load the bot can hold before it saturates.
    sampler:
        Optional callable returning a bandwidth sample in Mbps. Injected for
        determinism in tests; defaults to a modest constant sample.
    """

    def __init__(self, role: RoleSpec, capacity: float = 100.0,
                 sampler: Optional[Callable[[], float]] = None) -> None:
        self.role = role
        self.capacity = float(capacity)
        self.load = 0.0
        self._sampler = sampler or (lambda: 100.0)

    @property
    def name(self) -> str:
        return self.role.name

    def needs(self) -> Dict[str, List[str]]:
        """The bot's declared needs — the role's required inputs."""
        return {"inputs": list(self.role.inputs)}

    def sample(self) -> BotReport:
        """Measure bandwidth and classify the bot as peak / trough / idle."""
        bandwidth = float(self._sampler())
        return BotReport(
            bot=self.name,
            model=self.role.model,
            load=self.load,
            capacity=self.capacity,
            bandwidth_mbps=bandwidth,
            gaps=self._detect_gaps(bandwidth),
        )

    def _detect_gaps(self, bandwidth: float) -> List[str]:
        """Flag bandwidth gaps (where capacity outstrips measured bandwidth)."""
        gaps: List[str] = []
        if bandwidth < self.capacity * 0.25:
            gaps.append(f"low-bandwidth:{bandwidth:.1f}Mbps")
        if self.load > bandwidth:
            gaps.append("load-exceeds-bandwidth")
        return gaps


# ---------------------------------------------------------------------------
# Hive cluster
# ---------------------------------------------------------------------------

class Hive:
    """A cluster of :class:`VMwareWorkerBot` instances working in parallel."""

    def __init__(self, bots: Sequence[VMwareWorkerBot],
                 peak_threshold: float = 0.85,
                 trough_threshold: float = 0.30,
                 research_source_model: str = "Mistral") -> None:
        if not bots:
            raise ValueError("Hive requires at least one worker bot")
        self.bots: List[VMwareWorkerBot] = list(bots)
        self.peak_threshold = float(peak_threshold)
        self.trough_threshold = float(trough_threshold)
        self.research_source_model = research_source_model

    # -- construction ------------------------------------------------------

    @classmethod
    def from_roles(cls, roles: Sequence[RoleSpec],
                   capacity: float = 100.0,
                   sampler: Optional[Callable[[], float]] = None,
                   **kwargs) -> "Hive":
        """Spawn one worker bot per role (per need)."""
        bots = [VMwareWorkerBot(role, capacity=capacity, sampler=sampler)
                for role in roles]
        return cls(bots, **kwargs)

    # -- phase 1: parallel analysis ----------------------------------------

    def analyze(self, max_workers: Optional[int] = None) -> List[BotReport]:
        """Sample every bot in parallel and classify peaks and troughs."""
        workers = max_workers or min(32, len(self.bots))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            reports = list(pool.map(lambda b: b.sample(), self.bots))
        for report in reports:
            report.state = self._classify(report)
        return reports

    def _classify(self, report: BotReport) -> str:
        if report.utilisation >= self.peak_threshold:
            return "peak"
        if report.utilisation <= self.trough_threshold:
            return "trough"
        return "idle"

    # -- phase 2: trough balancing -----------------------------------------

    def balance(self, reports: List[BotReport]) -> LoadBalanceResult:
        """Shed load from peak bots into trough bots.

        Returns a record of the moves performed. Bots are matched by their
        report name; the underlying :class:`VMwareWorkerBot` load is updated so
        the cluster state stays consistent.
        """
        by_name: Dict[str, VMwareWorkerBot] = {b.name: b for b in self.bots}
        result = LoadBalanceResult()

        peaks = [r for r in reports if r.state == "peak"]
        troughs = sorted((r for r in reports if r.state == "trough"),
                         key=lambda r: r.utilisation)

        for peak in peaks:
            bot = by_name[peak.bot]
            # amount above the peak threshold that we want to shed
            excess = bot.load - (self.peak_threshold * bot.capacity)
            for trough in troughs:
                if excess <= 0:
                    break
                target = by_name[trough.bot]
                # room before the trough bot itself reaches the peak threshold
                room = (self.peak_threshold * target.capacity) - target.load
                if room <= 0:
                    continue
                amount = min(excess, room)
                target.load += amount
                bot.load -= amount
                trough.load = target.load  # keep the report view in sync
                result.moves.append({"from": bot.name, "to": target.name,
                                     "amount": amount})
                excess -= amount
        return result

    # -- phase 3: data-gap patching -----------------------------------------

    def patch(self, reports: List[BotReport],
              research_results: Optional[Dict[str, str]] = None) -> List[DataPatch]:
        """Patch missing data bits with updated innovation-research results.

        ``research_results`` maps a missing data bit to the innovation string
        used to fill it. When a bit has no supplied result, a default
        placeholder innovation from the research model is used.
        """
        research_results = research_results or {}
        patches: List[DataPatch] = []
        seen: set = set()
        for report in reports:
            for gap in report.gaps:
                if gap in seen:
                    continue
                seen.add(gap)
                innovation = research_results.get(
                    gap, f"innovation-research[{self.research_source_model}]:{gap}")
                patches.append(DataPatch(bit=gap,
                                         source_model=self.research_source_model,
                                         innovation=innovation))
        return patches

    # -- full run ------------------------------------------------------------

    def run(self, research_results: Optional[Dict[str, str]] = None,
            max_workers: Optional[int] = None) -> HiveReport:
        """Execute analyse → balance → patch and return a :class:`HiveReport`."""
        reports = self.analyze(max_workers=max_workers)
        balance = self.balance(reports)
        patches = self.patch(reports, research_results=research_results)
        return HiveReport(bots=reports, balance=balance, patches=patches)

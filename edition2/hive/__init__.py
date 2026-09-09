"""The AicodeX Edition 2 hive — model-driven VMware worker bots.

The hive is a *cluster* of lightweight worker bots. Each bot is spawned for a
configured model role and, **in parallel**, the cluster:

- samples bandwidth to find **gaps** and **peaks & troughs**,
- **balances load** by shedding work from peak-saturated bots into
  trough-idle bots, and
- **patches missing data bits** with updated innovation-research results
  (supplied by the Mistral ``research_dev`` role).

A :class:`PerformanceController` governs the parallel operations: it bounds
the concurrent fan-in, keeps the balanced collection inside a target
utilisation band (cap/boost/hold per bot), and records per-run performance
metrics for the monitor valves.

Everything is standard-library only; parallelism uses
:class:`concurrent.futures.ThreadPoolExecutor`. Deterministic in tests by
injecting explicit load/bandwidth samples (and an injected clock for the
performance metrics).
"""

from .cluster import (
    BotReport,
    DataPatch,
    Hive,
    HiveReport,
    LoadBalanceResult,
    PerformanceController,
    RunMetrics,
    VMwareWorkerBot,
)

__all__ = [
    "BotReport",
    "DataPatch",
    "Hive",
    "HiveReport",
    "LoadBalanceResult",
    "PerformanceController",
    "RunMetrics",
    "VMwareWorkerBot",
]

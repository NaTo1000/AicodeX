"""The AicodeX Edition 2 hive — model-driven VMware worker bots.

The hive is a *cluster* of lightweight worker bots. Each bot is spawned for a
configured model role and, **in parallel**, the cluster:

- samples bandwidth to find **gaps** and **peaks & troughs**,
- **balances load** by shedding work from peak-saturated bots into
  trough-idle bots, and
- **patches missing data bits** with updated innovation-research results
  (supplied by the Mistral ``research_dev`` role).

Everything is standard-library only; parallelism uses
:class:`concurrent.futures.ThreadPoolExecutor`. Deterministic in tests by
injecting explicit load/bandwidth samples.
"""

from .cluster import (
    BotReport,
    DataPatch,
    Hive,
    HiveReport,
    LoadBalanceResult,
    VMwareWorkerBot,
)

__all__ = [
    "BotReport",
    "DataPatch",
    "Hive",
    "HiveReport",
    "LoadBalanceResult",
    "VMwareWorkerBot",
]

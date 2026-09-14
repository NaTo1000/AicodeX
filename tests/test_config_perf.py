"""Static checks that the Edition 2 config is tuned to a performance level.

The default config must not spin on sub-second intervals, must bound the
parallel worker-bot fan-in, and must keep generation budgets (LoD / token /
byte ceilings) small enough to stay fast and avoid size blowouts. Pure JSON
assertions — no I/O beyond reading the settings file.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

CONFIG_PATH = (Path(__file__).resolve().parent.parent
               / "config" / "edition2_settings.json")
CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

#: LoD token-budget multipliers (mirror edition2.prompts.LOD_GUIDANCE).
LOD_FACTOR = {"minimal": 0.4, "standard": 1.0, "detailed": 1.6, "exhaustive": 2.5}

# Performance-level ceilings for the committed generation parameters.
MAX_TOKENS_CEILING = 4096
MAX_BYTES_CEILING = 131072          # 128 KiB per output
EFFECTIVE_BUDGET_CEILING = 8192     # base tokens x LoD factor


class RefreshIntervalTests(unittest.TestCase):
    def test_monitor_tick_is_not_subsecond(self) -> None:
        interval = CFG["monitor"]["refresh_interval_seconds"]
        self.assertGreaterEqual(interval, 1.0,
                                "monitor tick should be >= 1s to avoid churn")

    def test_forum_refresh_is_not_subsecond(self) -> None:
        refresh = CFG["monitor"]["forum"]["refresh_seconds"]
        self.assertGreaterEqual(refresh, 1.0,
                                "forum live refresh should be >= 1s")


class HivePerformanceTests(unittest.TestCase):
    def test_fan_in_is_bounded(self) -> None:
        self.assertLessEqual(CFG["hive"]["max_workers"], 8)
        self.assertLessEqual(CFG["hive"]["performance"]["max_workers"], 8)

    def test_utilisation_band_keeps_headroom(self) -> None:
        perf = CFG["hive"]["performance"]
        top = perf["target_utilisation"] + perf["band"]
        self.assertLess(top, CFG["hive"]["peak_threshold"],
                        "control band must stay below the peak threshold")
        self.assertLessEqual(perf["band"], 0.20)


class PromptBudgetTests(unittest.TestCase):
    def test_no_register_is_exhaustive(self) -> None:
        for name, reg in CFG["prompts"]["registers"].items():
            lod = reg["parameters"]["lod"]
            self.assertNotEqual(lod, "exhaustive",
                                f"{name} must not run at exhaustive LoD")

    def test_token_and_byte_ceilings(self) -> None:
        for name, reg in CFG["prompts"]["registers"].items():
            params = reg["parameters"]
            self.assertLessEqual(params["max_tokens"], MAX_TOKENS_CEILING,
                                 f"{name} max_tokens too high")
            self.assertLessEqual(params["max_bytes"], MAX_BYTES_CEILING,
                                 f"{name} max_bytes too high")

    def test_effective_budget_is_capped(self) -> None:
        for name, reg in CFG["prompts"]["registers"].items():
            params = reg["parameters"]
            effective = params["max_tokens"] * LOD_FACTOR[params["lod"]]
            self.assertLessEqual(effective, EFFECTIVE_BUDGET_CEILING,
                                 f"{name} effective token budget too high")


if __name__ == "__main__":
    unittest.main()

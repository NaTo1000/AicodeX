"""Standard-library tests for the AicodeX Edition 2 hive cluster.

Runnable with ``python -m unittest discover -s tests -v`` or pytest.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from edition2.hive import Hive, VMwareWorkerBot
from edition2.orchestrator import RoleRegistry

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"


def _roles():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return RoleRegistry(config["roles"]).enabled_roles()


def _bot(name: str, model: str, load: float, capacity: float = 100.0,
         bandwidth: float = 100.0) -> VMwareWorkerBot:
    role = next(r for r in _roles() if r.name == name) if any(
        r.name == name for r in _roles()) else _make_role(name, model)
    bot = VMwareWorkerBot(role, capacity=capacity, sampler=lambda: bandwidth)
    bot.load = load
    return bot


def _make_role(name: str, model: str):
    from edition2.orchestrator import RoleSpec
    return RoleSpec(name=name, model=model, mission=f"{name} mission",
                    inputs=[], outputs=[])


class WorkerBotTests(unittest.TestCase):
    def test_spawned_for_each_enabled_role(self) -> None:
        hive = Hive.from_roles(_roles())
        self.assertEqual(len(hive.bots), 7)

    def test_needs_reflect_role_inputs(self) -> None:
        bot = _bot("base_coder", "Cursor", load=0.0)
        self.assertIn("skeleton_structure", bot.needs()["inputs"])

    def test_requires_at_least_one_bot(self) -> None:
        with self.assertRaises(ValueError):
            Hive([])

    def test_low_bandwidth_flags_gap(self) -> None:
        bot = _bot("security_netops", "Grok", load=0.0, bandwidth=10.0)
        report = bot.sample()
        self.assertTrue(any(g.startswith("low-bandwidth") for g in report.gaps))

    def test_load_exceeding_bandwidth_flags_gap(self) -> None:
        bot = _bot("base_coder", "Cursor", load=90.0, bandwidth=50.0)
        report = bot.sample()
        self.assertIn("load-exceeds-bandwidth", report.gaps)


class AnalysisTests(unittest.TestCase):
    def test_peak_and_trough_classification(self) -> None:
        bots = [
            _bot("skeleton_architect", "Claude", load=95.0),   # peak
            _bot("formation_planner", "Gemini", load=10.0),    # trough
            _bot("base_coder", "Cursor", load=50.0),           # idle
        ]
        hive = Hive(bots)
        reports = {r.bot: r for r in hive.analyze()}
        self.assertEqual(reports["skeleton_architect"].state, "peak")
        self.assertEqual(reports["formation_planner"].state, "trough")
        self.assertEqual(reports["base_coder"].state, "idle")

    def test_analysis_runs_in_parallel_for_all_bots(self) -> None:
        hive = Hive.from_roles(_roles())
        reports = hive.analyze(max_workers=4)
        self.assertEqual(len(reports), 7)
        self.assertTrue(all(r.bandwidth_mbps == 100.0 for r in reports))


class BalanceTests(unittest.TestCase):
    def test_load_shed_from_peak_into_trough(self) -> None:
        peak = _bot("skeleton_architect", "Claude", load=95.0)
        trough = _bot("formation_planner", "Gemini", load=5.0)
        hive = Hive([peak, trough])
        reports = hive.analyze()
        result = hive.balance(reports)
        self.assertGreater(result.moved_total, 0.0)
        # peak shed down to (at most) the peak threshold
        self.assertLessEqual(peak.load, hive.peak_threshold * peak.capacity + 1e-6)
        # trough absorbed the load
        self.assertGreater(trough.load, 5.0)

    def test_trough_never_overfilled(self) -> None:
        peak = _bot("skeleton_architect", "Claude", load=100.0)
        trough = _bot("formation_planner", "Gemini", load=0.0)
        hive = Hive([peak, trough])
        hive.balance(hive.analyze())
        self.assertLessEqual(trough.load, hive.peak_threshold * trough.capacity + 1e-6)

    def test_no_peaks_means_no_moves(self) -> None:
        bots = [_bot("base_coder", "Cursor", load=40.0),
                _bot("error_patcher", "Kimi 3", load=50.0)]
        hive = Hive(bots)
        result = hive.balance(hive.analyze())
        self.assertEqual(result.moved_total, 0.0)
        self.assertEqual(result.moves, [])

    def test_total_load_conserved(self) -> None:
        bots = [_bot("skeleton_architect", "Claude", load=95.0),
                _bot("formation_planner", "Gemini", load=5.0),
                _bot("base_coder", "Cursor", load=20.0)]
        hive = Hive(bots)
        before = sum(b.load for b in bots)
        hive.balance(hive.analyze())
        after = sum(b.load for b in bots)
        self.assertAlmostEqual(before, after, places=6)


class PatchTests(unittest.TestCase):
    def test_missing_bits_patched_with_research(self) -> None:
        bot = _bot("research_dev", "Mistral", load=90.0, bandwidth=50.0)
        hive = Hive([bot])
        reports = hive.analyze()
        patches = hive.patch(reports)
        self.assertTrue(patches)
        self.assertTrue(all(p.source_model == "Mistral" for p in patches))
        bits = {p.bit for p in patches}
        self.assertIn("load-exceeds-bandwidth", bits)

    def test_supplied_innovation_used(self) -> None:
        bot = _bot("research_dev", "Mistral", load=90.0, bandwidth=50.0)
        hive = Hive([bot])
        patches = hive.patch(hive.analyze(),
                             research_results={"load-exceeds-bandwidth": "adaptive-qos-v2"})
        match = [p for p in patches if p.bit == "load-exceeds-bandwidth"]
        self.assertEqual(match[0].innovation, "adaptive-qos-v2")

    def test_duplicate_gaps_patched_once(self) -> None:
        bots = [_bot("base_coder", "Cursor", load=90.0, bandwidth=50.0),
                _bot("error_patcher", "Kimi 3", load=95.0, bandwidth=50.0)]
        hive = Hive(bots)
        patches = hive.patch(hive.analyze())
        bits = [p.bit for p in patches]
        self.assertEqual(len(bits), len(set(bits)))


class HiveRunTests(unittest.TestCase):
    def test_full_run_renders_report(self) -> None:
        bots = [_bot("skeleton_architect", "Claude", load=95.0),
                _bot("formation_planner", "Gemini", load=5.0, bandwidth=10.0)]
        hive = Hive(bots)
        report = hive.run(research_results={"low-bandwidth:10.0Mbps": "qos-boost"})
        text = report.render()
        self.assertIn("AicodeX Hive — Cluster Report", text)
        self.assertIn("Load rebalanced", text)
        self.assertIn("Data patches applied", text)

    def test_deterministic_with_injected_samples(self) -> None:
        def build() -> Hive:
            return Hive([_bot("skeleton_architect", "Claude", load=95.0),
                         _bot("formation_planner", "Gemini", load=5.0)])
        first = build().run().render()
        second = build().run().render()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

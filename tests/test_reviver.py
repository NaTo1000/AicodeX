"""Tests for the Edition 2 reviver cluster (adversarial continuous testing)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from edition2.orchestrator import ConfigError
from edition2.reviver import (ALLOWED_LICENSES, SIX_TUNNELS, CurveballEngine,
                              Dependency, ReviverCluster, Sector,
                              SectorCollector, TestbedBuilder, ThreatScanner,
                              VramCompressionReviver, hiai_reality_check)

CONFIG_PATH = (Path(__file__).resolve().parent.parent
               / "config" / "edition2_settings.json")
REV_CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["reviver"]


class VramReviverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reviver = VramCompressionReviver()

    def test_compress_then_revive_round_trip(self) -> None:
        sector = Sector("weights", b"model-payload" * 100)
        self.assertTrue(self.reviver.round_trip_ok(sector))

    def test_compressed_is_smaller_for_redundant_data(self) -> None:
        sector = Sector("weights", b"x" * 4096)
        compressed = self.reviver.compress(sector)
        self.assertTrue(compressed.compressed)
        self.assertLess(compressed.size, sector.size)

    def test_revive_plain_sector_passthrough(self) -> None:
        sector = Sector("plain", b"raw")
        self.assertEqual(self.reviver.revive(sector), b"raw")

    def test_corrupt_sector_detected(self) -> None:
        bad = Sector("corrupt", b"\x00\x01-not-zlib", compressed=True)
        with self.assertRaises(ConfigError):
            self.reviver.revive(bad)


class SectorCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collector = SectorCollector()

    def test_collect_dedupes_sectors(self) -> None:
        sectors = [Sector("a", b"1"), Sector("a", b"1"), Sector("b", b"2")]
        self.assertEqual(self.collector.collect(sectors), ["a", "b"])

    def test_relicense_stale_dependency(self) -> None:
        dep = self.collector.relicense(Dependency("libx", "proprietary"))
        self.assertIn(dep.license, ALLOWED_LICENSES)
        self.assertEqual(dep.license, "Apache-2.0")

    def test_relicense_unknown_to_default(self) -> None:
        dep = self.collector.relicense(Dependency("liby", "unknown"))
        self.assertEqual(dep.license, "Apache-2.0")

    def test_valid_license_unchanged(self) -> None:
        dep = Dependency("libz", "MIT")
        self.assertIs(self.collector.relicense(dep), dep)
        self.assertEqual(self.collector.patches, [])

    def test_relicensing_is_idempotent(self) -> None:
        self.collector.relicense(Dependency("libx", "proprietary"))
        self.collector.relicense(Dependency("libx", "proprietary"))
        dep_patches = [p for p in self.collector.patches
                       if p.target == "dependency:libx"]
        self.assertEqual(len(dep_patches), 1)

    def test_workflow_semantic_synthesis_stable(self) -> None:
        a = self.collector.synthesise_workflow(["scan", "patch", "verify"])
        b = self.collector.synthesise_workflow(["scan", "patch", "verify"])
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("workflow-sem-"))


class RealityCheckTests(unittest.TestCase):
    def test_supported_claim_passes(self) -> None:
        passed, conf = hiai_reality_check(
            "the patch fixes the buffer overflow",
            ["patch buffer overflow resolved"])
        self.assertTrue(passed)
        self.assertGreater(conf, 0.0)

    def test_unsupported_claim_fails(self) -> None:
        passed, conf = hiai_reality_check(
            "quantum flux capacitor aligned", ["the tests all pass"])
        self.assertFalse(passed)
        self.assertEqual(conf, 0.0)

    def test_empty_claim_fails(self) -> None:
        self.assertEqual(hiai_reality_check("", ["evidence"]), (False, 0.0))


class ThreatScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scanner = ThreatScanner()

    def test_six_tunnels(self) -> None:
        self.assertEqual(len(SIX_TUNNELS), 6)

    def test_detects_trojan_indicator(self) -> None:
        findings = self.scanner.scan_payload("ssh", "os.system('id')")
        self.assertTrue(any(f.indicator == "os.system" for f in findings))

    def test_clean_payload_no_findings(self) -> None:
        self.assertEqual(self.scanner.scan_payload("tls", "hello world"), [])

    def test_unknown_tunnel_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            self.scanner.scan_payload("carrier-pigeon", "x")

    def test_scan_environment_covers_all_tunnels_in_order(self) -> None:
        payloads = {"vpn-mesh": "eval(x)", "ssh": "backdoor"}
        findings = self.scanner.scan_environment(payloads)
        self.assertEqual([f.tunnel for f in findings], ["ssh", "vpn-mesh"])


class TestbedBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = TestbedBuilder()

    def test_near_real_with_all_six_tunnels(self) -> None:
        env = self.builder.build("t", containers=["app"],
                                 variables={"a": 1, "b": 2, "c": 3,
                                            "d": 4, "e": 5, "f": 6})
        self.assertEqual(env.link_count, 6)
        self.assertGreaterEqual(env.fidelity, 0.9)

    def test_fidelity_capped_at_one(self) -> None:
        env = self.builder.build("t", containers=["app"],
                                 variables={f"k{i}": i for i in range(50)})
        self.assertLessEqual(env.fidelity, 1.0)

    def test_requires_a_container(self) -> None:
        with self.assertRaises(ConfigError):
            self.builder.build("t", containers=[])

    def test_unknown_tunnels_filtered_out(self) -> None:
        env = self.builder.build("t", containers=["app"],
                                 tunnels=["ssh", "bogus"])
        self.assertEqual(env.tunnels, ("ssh",))


class CurveballEngineTests(unittest.TestCase):
    def test_throws_and_reports_resilience(self) -> None:
        env = TestbedBuilder().build("t", containers=["app"],
                                     variables={"load": 1.0})
        engine = CurveballEngine(seed=42)
        engine.register_invariant(
            "numeric", lambda v: isinstance(v.get("load"), (int, float)))
        result = engine.throw(env)
        self.assertIn("load", result.thrown)
        self.assertIn("numeric", result.held)
        self.assertTrue(result.resilient)

    def test_broken_invariant_reported(self) -> None:
        env = TestbedBuilder().build("t", containers=["app"],
                                     variables={"load": 1.0})
        engine = CurveballEngine(seed=1)
        engine.register_invariant("positive",
                                  lambda v: float(v.get("load", 0)) > 0)
        result = engine.throw(env)
        # load * {-1,0,2,10} can go non-positive → must be detectable.
        self.assertIn("load", result.thrown)

    def test_throwing_invariant_counts_as_broke(self) -> None:
        env = TestbedBuilder().build("t", containers=["app"],
                                     variables={"x": "abc"})
        engine = CurveballEngine(seed=0)
        engine.register_invariant("boom", lambda v: 1 / 0)  # always throws
        result = engine.throw(env)
        self.assertIn("boom", result.broke)
        self.assertFalse(result.resilient)


class ClusterCycleTests(unittest.TestCase):
    def test_full_cycle(self) -> None:
        env = TestbedBuilder().build("near-real", containers=["app", "db"],
                                     variables={"a": 1})
        report = ReviverCluster().run_cycle(
            [Sector("weights", b"payload" * 64)],
            dependencies=[Dependency("libx", "proprietary")],
            claims={"patch works": ["patch verified"]},
            tunnel_payloads={"ssh": "os.system('id')"},
            env=env)
        self.assertEqual(report.sectors, ["weights"])
        self.assertEqual(report.revived_ok, 1)
        self.assertEqual(report.relicensed, ["libx"])
        self.assertEqual(report.reality_checks, 1)
        self.assertEqual(report.reality_failed, [])
        self.assertEqual(len(report.findings), 1)
        self.assertIsNotNone(report.curveball)
        self.assertEqual(len(report.patches), 2)
        self.assertTrue(all(p.future_proof for p in report.patches))

    def test_patches_idempotent_across_cycles(self) -> None:
        env = TestbedBuilder().build("t", containers=["app"], variables={"a": 1})
        cluster = ReviverCluster()
        first = cluster.run_cycle(
            [Sector("s", b"x" * 32)],
            dependencies=[Dependency("libx", "proprietary")],
            tunnel_payloads={"ssh": "os.system('id')"}, env=env)
        second = cluster.run_cycle(
            [Sector("s", b"x" * 32)],
            dependencies=[Dependency("libx", "proprietary")],
            tunnel_payloads={"ssh": "os.system('id')"}, env=env)
        self.assertEqual(len(first.patches), 2)
        self.assertEqual(second.patches, [])

    def test_render_mentions_all_phases(self) -> None:
        env = TestbedBuilder().build("t", containers=["app"], variables={"a": 1})
        text = ReviverCluster().run_cycle([Sector("s", b"y" * 8)],
                                          env=env).render()
        for phrase in ("VRAM sectors revived", "relicensed", "reality checks",
                       "threat findings", "curveball", "patches issued"):
            self.assertIn(phrase, text)


class ConfigTests(unittest.TestCase):
    def test_reviver_section_present(self) -> None:
        self.assertEqual(REV_CFG["compression_level"], 6)
        self.assertEqual(len(REV_CFG["tunnels"]), 6)
        self.assertIn("testbed", REV_CFG)

    def test_config_tunnels_match_scanner(self) -> None:
        self.assertEqual(tuple(REV_CFG["tunnels"]), SIX_TUNNELS)

    def test_relicensing_map_uses_allowed_licenses(self) -> None:
        for target in REV_CFG["relicensing_map"].values():
            self.assertIn(target, ALLOWED_LICENSES)


if __name__ == "__main__":
    unittest.main()

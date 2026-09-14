"""Tests for the PPT (Performance Personal Tuner) subsystem."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from edition2.orchestrator import ConfigError
from edition2.ppt import (ACCESS_TIERS, DEFAULT_TARGETS, PROFILE_BOUNDS,
                          SENSITIVE_TARGETS, TARGET_CATEGORIES, MeshPlan,
                          PersonalTuner, TargetRegistry, tier_level)
from edition2.vault import SecretsVault

CONFIG_PATH = (Path(__file__).resolve().parent.parent
               / "config" / "edition2_settings.json")
PPT_CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["ppt"]


def _vault_with_root(testcase: unittest.TestCase) -> SecretsVault:
    """A temp vault holding the PPT root key; cleaned up with the test."""
    tmp = tempfile.TemporaryDirectory()
    testcase.addCleanup(tmp.cleanup)
    path = Path(tmp.name) / "vault.json"
    path.write_text(json.dumps({"PPT_ROOT_KEY": "root-secret"}),
                    encoding="utf-8")
    return SecretsVault(path)


class TierTests(unittest.TestCase):
    def test_tier_order(self) -> None:
        self.assertEqual(ACCESS_TIERS, ("user", "professional", "admin"))
        self.assertLess(tier_level("user"), tier_level("professional"))
        self.assertLess(tier_level("professional"), tier_level("admin"))

    def test_unknown_tier_is_user_level(self) -> None:
        self.assertEqual(tier_level("nobody"), 0)


class TargetRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = TargetRegistry()

    def test_categories_present(self) -> None:
        for category in TARGET_CATEGORIES:
            self.assertTrue(self.registry.by_category(category),
                            f"category '{category}' must be non-empty")

    def test_named_platforms_present(self) -> None:
        for target in ("openwrt", "openwifi", "openlte", "openvnc", "tor",
                       "obsidian-os", "mediatek-crystal"):
            self.assertTrue(self.registry.has(target), target)

    def test_named_shells_and_terminals_present(self) -> None:
        for target in ("putty", "windows-cmd", "powershell", "realvnc",
                       "xpipe", "alacritty", "termux", "unix", "msdos",
                       "bios"):
            # termux/unix/msdos/bios are platforms; the rest are shells — all
            # must resolve regardless of category.
            self.assertTrue(self.registry.has(target), target)

    def test_named_hardware_present(self) -> None:
        for target in ("flipper-zero", "cifertech", "madhatter",
                       "talkingsasquatch", "cyd", "heltec", "esp32", "jtag",
                       "serial"):
            self.assertTrue(self.registry.has(target), target)

    def test_named_transports_present(self) -> None:
        for target in ("remote", "online", "ethernet", "proxy", "vps",
                       "home-server"):
            self.assertTrue(self.registry.has(target), target)

    def test_unknown_target_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            self.registry.get("not-a-target")

    def test_unknown_category_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            TargetRegistry({"bogus": ["x"]})

    def test_sensitive_targets_flagged(self) -> None:
        for target_id in ("bios", "jtag", "tor", "proxy"):
            self.assertTrue(self.registry.get(target_id).sensitive)
            self.assertIn(target_id, SENSITIVE_TARGETS)

    def test_user_cannot_access_sensitive_but_pro_can(self) -> None:
        user_ids = {t.id for t in self.registry.accessible("user")}
        pro_ids = {t.id for t in self.registry.accessible("professional")}
        self.assertNotIn("jtag", user_ids)
        self.assertIn("jtag", pro_ids)
        self.assertIn("esp32", user_ids)      # non-sensitive stays open


class AccessGatingTests(unittest.TestCase):
    def test_no_vault_means_no_elevation(self) -> None:
        tuner = PersonalTuner()
        self.assertFalse(tuner.can_elevate())
        self.assertEqual(tuner.effective_tier("admin"), "user")
        self.assertEqual(tuner.effective_tier("professional"), "user")

    def test_root_key_grants_elevation(self) -> None:
        tuner = PersonalTuner(vault=_vault_with_root(self))
        self.assertTrue(tuner.can_elevate())
        self.assertEqual(tuner.effective_tier("admin"), "admin")
        self.assertEqual(tuner.effective_tier("professional"), "professional")

    def test_user_tier_always_allowed(self) -> None:
        self.assertEqual(PersonalTuner().effective_tier("user"), "user")


class TuningProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tuner = PersonalTuner()

    def test_knobs_clamped_to_bounds(self) -> None:
        profile = self.tuner.build_profile(
            "p", knobs={"max_workers": 99, "opacity": 0.01})
        self.assertEqual(profile.knobs["max_workers"],
                         PROFILE_BOUNDS["max_workers"][1])
        self.assertEqual(profile.knobs["opacity"],
                         PROFILE_BOUNDS["opacity"][0])

    def test_unknown_knob_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            self.tuner.build_profile("p", knobs={"nonsense": 1})

    def test_invalid_choice_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            self.tuner.build_profile("p", knobs={"lod": "ludicrous"})

    def test_sensitive_target_requires_pro(self) -> None:
        with self.assertRaises(ConfigError):
            self.tuner.build_profile("p", tier="user", targets=["jtag"])

    def test_pro_profile_builds_with_root_key(self) -> None:
        tuner = PersonalTuner(vault=_vault_with_root(self))
        profile = tuner.build_profile("lab", tier="professional",
                                      targets=["esp32", "jtag", "heltec"])
        self.assertEqual(profile.tier, "professional")
        self.assertIn("jtag", profile.targets)

    def test_profile_tier_dropped_without_key(self) -> None:
        profile = self.tuner.build_profile("p", tier="admin", targets=["esp32"])
        self.assertEqual(profile.tier, "user")

    def test_duplicate_targets_deduped(self) -> None:
        profile = self.tuner.build_profile("p", targets=["esp32", "esp32"])
        self.assertEqual(profile.targets, ["esp32"])


class MeshPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tuner = PersonalTuner(vault=_vault_with_root(self))

    def test_mesh_requires_admin(self) -> None:
        with self.assertRaises(ConfigError):
            PersonalTuner().plan_mesh(6, tier="admin")   # no root key
        with self.assertRaises(ConfigError):
            self.tuner.plan_mesh(6, tier="user")

    def test_mesh_plan_shape(self) -> None:
        plan = self.tuner.plan_mesh(6, tier="admin", max_degree=4)
        self.assertIsInstance(plan, MeshPlan)
        self.assertEqual(plan.nodes, 6)
        self.assertGreater(plan.link_count, 0)
        for node in range(6):
            self.assertLessEqual(plan.degree(node), 4)

    def test_mesh_needs_a_node(self) -> None:
        with self.assertRaises(ConfigError):
            self.tuner.plan_mesh(0, tier="admin")

    def test_small_mesh_fully_connected(self) -> None:
        plan = self.tuner.plan_mesh(3, tier="admin", max_degree=4)
        self.assertTrue(plan.fully_connected)

    def test_render_mentions_autonomous_system(self) -> None:
        text = self.tuner.plan_mesh(4, tier="admin").render()
        self.assertIn("autonomous system", text)


class ConfigTests(unittest.TestCase):
    def test_config_ppt_section(self) -> None:
        self.assertEqual(PPT_CFG["root_key_ref"], "$VAULT:PPT_ROOT_KEY")
        self.assertIn("mesh", PPT_CFG)
        self.assertIn("profiles", PPT_CFG)

    def test_config_profiles_reference_known_targets(self) -> None:
        registry = TargetRegistry()
        for name, raw in PPT_CFG["profiles"].items():
            for target in raw.get("targets", []):
                self.assertTrue(registry.has(target),
                                f"profile '{name}' target '{target}' unknown")

    def test_root_key_not_stored_in_config(self) -> None:
        text = CONFIG_PATH.read_text(encoding="utf-8")
        self.assertNotIn("root-secret", text)
        # Only the $VAULT: reference, never a literal key value.
        self.assertIn("$VAULT:PPT_ROOT_KEY", text)


if __name__ == "__main__":
    unittest.main()

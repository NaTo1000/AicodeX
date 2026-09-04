"""Standard-library test suite for AicodeX Edition 2.

Runnable with either ``python -m unittest discover -s tests -v`` or
``python -m pytest tests/ -v``.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
import warnings
from pathlib import Path

from edition2 import __version__
from edition2.__main__ import main as cli_main
from edition2.chaimera import ConductorX
from edition2.orchestrator import ConfigError, RoleRegistry
from edition2.vault import LOCAL_ONLY_WARNING, SecretsVault, VaultError

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


class SecretsVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_path = Path(self._tmp.name) / "vault.json"
        self.vault = SecretsVault(self.vault_path)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_set_and_get_roundtrip(self) -> None:
        self.vault.set("API_KEY", "s3cr3t")
        self.assertEqual(self.vault.get("API_KEY"), "s3cr3t")

    def test_get_missing_returns_default(self) -> None:
        self.assertIsNone(self.vault.get("missing"))
        self.assertEqual(self.vault.get("missing", "fallback"), "fallback")

    def test_file_permissions_are_owner_only(self) -> None:
        self.vault.set("API_KEY", "s3cr3t")
        mode = stat.S_IMODE(self.vault_path.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_permissions_are_repaired_on_write(self) -> None:
        self.vault.set("API_KEY", "s3cr3t")
        os.chmod(self.vault_path, 0o644)
        self.vault.set("OTHER", "value")
        mode = stat.S_IMODE(self.vault_path.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_delete(self) -> None:
        self.vault.set("API_KEY", "s3cr3t")
        self.assertTrue(self.vault.delete("API_KEY"))
        self.assertFalse(self.vault.delete("API_KEY"))
        self.assertIsNone(self.vault.get("API_KEY"))

    def test_keys_lists_names_not_values(self) -> None:
        self.vault.set("B_KEY", "1")
        self.vault.set("A_KEY", "2")
        self.assertEqual(self.vault.keys(), ["A_KEY", "B_KEY"])

    def test_empty_key_rejected(self) -> None:
        with self.assertRaises(VaultError):
            self.vault.set("", "value")

    def test_resolve_vault_reference(self) -> None:
        self.vault.set("CLAUDE_API_KEY", "abc123")
        self.assertEqual(self.vault.resolve("$VAULT:CLAUDE_API_KEY"), "abc123")

    def test_resolve_passthrough_for_non_reference(self) -> None:
        self.assertEqual(self.vault.resolve("plain-value"), "plain-value")

    def test_shared_location_triggers_local_only_warning(self) -> None:
        shared = SecretsVault(Path(self._tmp.name) / "Dropbox" / "vault.json")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            shared.set("K", "V")
        self.assertTrue(any(LOCAL_ONLY_WARNING in str(w.message) for w in caught))


class RoleRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = _load_config()
        self.registry = RoleRegistry(self.config["roles"])

    def test_all_seven_roles_present(self) -> None:
        self.assertEqual(len(self.registry.all_roles()), 7)

    def test_expected_models_bound(self) -> None:
        models = {role.model for role in self.registry.all_roles()}
        self.assertEqual(
            models,
            {"Claude", "Gemini", "Cursor", "Kimi 3", "Mistral", "Grok", "ChatGPT"})

    def test_enabled_by_default(self) -> None:
        self.assertTrue(all(role.enabled for role in self.registry.all_roles()))

    def test_disabled_roles_excluded(self) -> None:
        roles = json.loads(json.dumps(self.config["roles"]))
        roles["security_netops"]["enabled"] = False
        registry = RoleRegistry(roles)
        enabled_names = {role.name for role in registry.enabled_roles()}
        self.assertNotIn("security_netops", enabled_names)
        self.assertEqual(len(registry.enabled_roles()), 6)

    def test_missing_model_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            RoleRegistry({"bad": {"mission": "no model"}})

    def test_missing_mission_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            RoleRegistry({"bad": {"model": "Claude"}})

    def test_empty_roles_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            RoleRegistry({})

    def test_unknown_role_lookup_raises(self) -> None:
        with self.assertRaises(ConfigError):
            self.registry.get("nonexistent")

    def test_resolve_secret_without_vault_raises(self) -> None:
        with self.assertRaises(ConfigError):
            self.registry.resolve_secret("skeleton_architect")


class ConductorXTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = _load_config()
        self.registry = RoleRegistry(self.config["roles"])
        self.seeds = set(self.config["orchestration"].get("seeds", []))

    def test_full_run_all_ok(self) -> None:
        report = ConductorX(self.registry).conduct(seeds=self.seeds)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.succeeded, 7)
        self.assertEqual(len(report.movements), 7)

    def test_missing_seed_fails_first_movement(self) -> None:
        report = ConductorX(self.registry).conduct(seeds=set())
        statuses = {m.role: m.status for m in report.movements}
        self.assertEqual(statuses["skeleton_architect"], "failed")

    def test_missing_dependency_fails_movement(self) -> None:
        roles = json.loads(json.dumps(self.config["roles"]))
        # base_coder depends on formation_system produced by formation_planner.
        roles["formation_planner"]["enabled"] = False
        registry = RoleRegistry(roles)
        report = ConductorX(registry).conduct(seeds=self.seeds)
        statuses = {m.role: m.status for m in report.movements}
        self.assertEqual(statuses["base_coder"], "failed")
        self.assertGreaterEqual(report.failed, 1)

    def test_include_disabled_marks_skipped(self) -> None:
        roles = json.loads(json.dumps(self.config["roles"]))
        roles["research_dev"]["enabled"] = False
        registry = RoleRegistry(roles)
        report = ConductorX(registry).conduct(only_enabled=False, seeds=self.seeds)
        statuses = {m.role: m.status for m in report.movements}
        self.assertEqual(statuses["research_dev"], "skipped")
        self.assertEqual(report.skipped, 1)

    def test_report_renders_text(self) -> None:
        report = ConductorX(self.registry).conduct(seeds=self.seeds)
        text = report.render()
        self.assertIn("CHAiMERA ConductorX", text)
        self.assertIn("skeleton_architect", text)
        self.assertIn("Movements: 7", text)


class CliTests(unittest.TestCase):
    def test_version_flag(self) -> None:
        self.assertEqual(cli_main(["--version"]), 0)

    def test_list_roles(self) -> None:
        self.assertEqual(cli_main(["--list-roles", "--config", str(CONFIG_PATH)]), 0)

    def test_full_run_via_cli(self) -> None:
        self.assertEqual(cli_main(["--config", str(CONFIG_PATH)]), 0)

    def test_missing_config_returns_error(self) -> None:
        self.assertEqual(cli_main(["--config", "does/not/exist.json"]), 2)

    def test_version_constant(self) -> None:
        self.assertEqual(__version__, "2.0.0")


if __name__ == "__main__":
    unittest.main()

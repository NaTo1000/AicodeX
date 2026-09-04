"""Standard-library tests for AicodeX Edition 2 compute backends.

Runnable with ``python -m unittest discover -s tests -v`` or pytest.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.backends import BackendRegistry, ComputeBackend, parse_backend
from edition2.orchestrator import ConfigError, RoleRegistry
from edition2.vault import SecretsVault

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _registry() -> RoleRegistry:
    return RoleRegistry(_config()["roles"])


class ParseBackendTests(unittest.TestCase):
    def test_none_defaults_to_standard(self) -> None:
        backend = parse_backend(None, role_name="r")
        self.assertEqual(backend.kind, "standard")
        self.assertIsNone(backend.endpoint)

    def test_empty_mapping_defaults_to_standard(self) -> None:
        self.assertEqual(parse_backend({}, role_name="r").kind, "standard")

    def test_each_kind_accepted(self) -> None:
        for kind in ("standard", "vps", "cloud", "gpu"):
            raw = {"kind": kind}
            if kind != "standard":
                raw["endpoint"] = "$VAULT:X"
            if kind == "gpu":
                raw["gpu_vendor"] = "Nvidia"
            self.assertEqual(parse_backend(raw, role_name="r").kind, kind)

    def test_invalid_kind_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            parse_backend({"kind": "quantum"}, role_name="r")

    def test_nonstandard_requires_endpoint(self) -> None:
        for kind in ("vps", "cloud", "gpu"):
            raw = {"kind": kind}
            if kind == "gpu":
                raw["gpu_vendor"] = "Tesla"
            with self.assertRaises(ConfigError):
                parse_backend(raw, role_name="r")

    def test_gpu_requires_valid_vendor(self) -> None:
        with self.assertRaises(ConfigError):
            parse_backend({"kind": "gpu", "endpoint": "$VAULT:X",
                           "gpu_vendor": "AMD"}, role_name="r")

    def test_gpu_vendor_rejected_for_non_gpu(self) -> None:
        with self.assertRaises(ConfigError):
            parse_backend({"kind": "vps", "endpoint": "$VAULT:X",
                           "gpu_vendor": "Nvidia"}, role_name="r")

    def test_non_object_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            parse_backend(["not", "a", "dict"], role_name="r")

    def test_describe(self) -> None:
        self.assertEqual(ComputeBackend().describe(), "standard model output")
        self.assertEqual(ComputeBackend(kind="vps", endpoint="e").describe(), "VPS")
        self.assertEqual(ComputeBackend(kind="cloud", endpoint="e").describe(), "CLOUD")
        self.assertEqual(
            ComputeBackend(kind="gpu", endpoint="e", gpu_vendor="Nvidia").describe(),
            "GPU (Nvidia)")
        self.assertEqual(
            ComputeBackend(kind="gpu", endpoint="e", gpu_vendor="Tesla").describe(),
            "GPU (Tesla)")


class ConfigIntegrationTests(unittest.TestCase):
    def test_every_role_has_a_backend(self) -> None:
        for role in _registry().all_roles():
            self.assertIsInstance(role.compute, ComputeBackend)

    def test_default_standard_roles(self) -> None:
        for name in ("skeleton_architect", "error_patcher", "spec_logger"):
            self.assertEqual(_registry().get(name).compute.kind, "standard")

    def test_distinct_backend_kinds_assigned(self) -> None:
        kinds = {role.name: role.compute.kind for role in _registry().all_roles()}
        self.assertEqual(kinds["formation_planner"], "cloud")
        self.assertEqual(kinds["base_coder"], "vps")
        self.assertEqual(kinds["research_dev"], "gpu")
        self.assertEqual(kinds["security_netops"], "gpu")

    def test_gpu_vendors(self) -> None:
        self.assertEqual(_registry().get("research_dev").compute.gpu_vendor, "Nvidia")
        self.assertEqual(_registry().get("security_netops").compute.gpu_vendor, "Tesla")

    def test_endpoints_are_vault_refs_not_secrets(self) -> None:
        for role in _registry().all_roles():
            endpoint = role.compute.endpoint
            if endpoint is not None:
                self.assertTrue(endpoint.startswith("$VAULT:"),
                                f"{role.name} endpoint must be a $VAULT: reference")


class BackendRegistryTests(unittest.TestCase):
    def test_link_for(self) -> None:
        backends = BackendRegistry(_registry())
        self.assertEqual(backends.link_for("base_coder").kind, "vps")

    def test_all_links_covers_all_roles(self) -> None:
        backends = BackendRegistry(_registry())
        self.assertEqual(len(backends.all_links()), 7)

    def test_resolve_standard_returns_none(self) -> None:
        backends = BackendRegistry(_registry())
        self.assertIsNone(backends.resolve_endpoint("skeleton_architect"))

    def test_resolve_endpoint_without_vault_raises(self) -> None:
        backends = BackendRegistry(_registry())
        with self.assertRaises(ConfigError):
            backends.resolve_endpoint("base_coder")

    def test_resolve_endpoint_through_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = SecretsVault(Path(tmp) / "vault.json")
            vault.set("CURSOR_VPS_ENDPOINT", "https://vps.example.com:8443")
            backends = BackendRegistry(_registry(), vault=vault)
            self.assertEqual(backends.resolve_endpoint("base_coder"),
                             "https://vps.example.com:8443")

    def test_render_lists_every_model(self) -> None:
        text = BackendRegistry(_registry()).render()
        for model in ("Claude", "Gemini", "Cursor", "Kimi 3", "Mistral",
                      "Grok", "ChatGPT"):
            self.assertIn(model, text)
        self.assertIn("Compute Backends", text)


class CliTests(unittest.TestCase):
    def test_backends_flag(self) -> None:
        self.assertEqual(
            cli_main(["--backends", "--config", str(CONFIG_PATH)]), 0)


if __name__ == "__main__":
    unittest.main()

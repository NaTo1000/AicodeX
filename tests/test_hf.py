"""Standard-library tests for the AicodeX Edition 2 Hugging Face catalog."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.hfcatalog import HuggingFaceCatalog
from edition2.orchestrator import ConfigError
from edition2.vault import SecretsVault

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
ENTRIES = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["hf_models"]["entries"]


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.install_dir = Path(self._tmp.name) / "models"
        self.catalog = HuggingFaceCatalog(ENTRIES, install_dir=self.install_dir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_catalog_lists_variety(self) -> None:
        self.assertEqual(len(self.catalog.list()), 6)

    def test_entry_fields(self) -> None:
        spec = self.catalog.get("meta-llama/Llama-3-8B-Instruct")
        self.assertTrue(spec.gated)
        self.assertEqual(spec.task, "text-generation")
        self.assertEqual(spec.params_b, 8.0)

    def test_unknown_model_raises(self) -> None:
        with self.assertRaises(ConfigError):
            self.catalog.get("not/a-model")

    def test_non_object_entry_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            HuggingFaceCatalog({"bad": ["not", "object"]})


class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.install_dir = Path(self._tmp.name) / "models"
        self.catalog = HuggingFaceCatalog(ENTRIES, install_dir=self.install_dir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_install_marks_model_installed(self) -> None:
        model = "mistralai/Mistral-7B-Instruct"
        self.assertFalse(self.catalog.is_installed(model))
        self.catalog.install(model)
        self.assertTrue(self.catalog.is_installed(model))

    def test_install_unknown_model_raises(self) -> None:
        with self.assertRaises(ConfigError):
            self.catalog.install("not/a-model")

    def test_custom_installer_used(self) -> None:
        calls = []
        catalog = HuggingFaceCatalog(
            ENTRIES, install_dir=self.install_dir,
            installer=lambda mid, d: calls.append(mid))
        catalog.install("google/gemma-2-9b-it")
        self.assertEqual(calls, ["google/gemma-2-9b-it"])


class ActivateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.install_dir = Path(self._tmp.name) / "models"
        self.vault = SecretsVault(Path(self._tmp.name) / "vault.json")
        self.catalog = HuggingFaceCatalog(
            ENTRIES, vault=self.vault, install_dir=self.install_dir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_open_model_activates_without_key(self) -> None:
        model = "mistralai/Mistral-7B-Instruct"
        self.catalog.install(model)
        result = self.catalog.activate(model)
        self.assertTrue(result["activated"])
        self.assertIsNone(result["api_key"])

    def test_activation_requires_install_first(self) -> None:
        with self.assertRaises(ConfigError):
            self.catalog.activate("mistralai/Mistral-7B-Instruct")

    def test_gated_model_requires_key(self) -> None:
        model = "meta-llama/Llama-3-8B-Instruct"
        self.catalog.install(model)
        with self.assertRaises(ConfigError):
            self.catalog.activate(model)

    def test_gated_model_activates_with_vault_key(self) -> None:
        model = "meta-llama/Llama-3-8B-Instruct"
        self.catalog.install(model)
        self.vault.set("HF_API_KEY", "hf_secret_token")
        result = self.catalog.activate(model, api_key_ref="$VAULT:HF_API_KEY")
        self.assertTrue(result["activated"])
        self.assertEqual(result["api_key"], "hf_secret_token")

    def test_vault_ref_without_vault_raises(self) -> None:
        catalog = HuggingFaceCatalog(ENTRIES, install_dir=self.install_dir)
        model = "meta-llama/Llama-3-8B-Instruct"
        catalog.install(model)
        with self.assertRaises(ConfigError):
            catalog.activate(model, api_key_ref="$VAULT:HF_API_KEY")

    def test_api_key_not_persisted(self) -> None:
        model = "meta-llama/Llama-3-8B-Instruct"
        self.catalog.install(model)
        self.vault.set("HF_API_KEY", "hf_secret_token")
        self.catalog.activate(model, api_key_ref="$VAULT:HF_API_KEY")
        # The install marker must not contain the key.
        marker = self.install_dir / "meta-llama__Llama-3-8B-Instruct.json"
        self.assertNotIn("hf_secret_token", marker.read_text())


class CliTests(unittest.TestCase):
    def test_hf_catalog_flag(self) -> None:
        self.assertEqual(cli_main(["--hf-catalog", "--config", str(CONFIG_PATH)]), 0)


if __name__ == "__main__":
    unittest.main()

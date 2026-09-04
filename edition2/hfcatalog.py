"""Hugging Face model-selection catalog for AicodeX Edition 2.

A click-and-install catalog of model varieties. Each entry can be *installed*
(downloaded into a local directory) and *activated* with the user's API key.
The API key is supplied via a ``$VAULT:key`` reference and resolved through the
local secrets vault at activation time — it is never written to disk by this
module.

Standard library only; the default installer writes a small local marker file
so the flow is fully testable offline with no network access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional

from .orchestrator import ConfigError
from .vault import SecretsVault


@dataclass(frozen=True)
class HFModelSpec:
    """A Hugging Face catalog entry."""

    model_id: str                  # e.g. "mistralai/Mistral-7B-Instruct"
    task: str = "text-generation"  # the model variety / task
    gated: bool = False            # whether activation needs an API key
    params_b: Optional[float] = None  # parameter count in billions (optional)


class HuggingFaceCatalog:
    """A click-and-install catalog of Hugging Face models.

    Parameters
    ----------
    entries:
        Raw catalog entries (mappings) from configuration.
    vault:
        Optional :class:`SecretsVault` used to resolve the activation API key.
    install_dir:
        Directory models are installed into.
    installer:
        Optional callable ``(model_id, install_dir) -> None`` performing the
        actual install. Defaults to a local marker-file writer (offline-safe).
    """

    def __init__(self, entries: Mapping[str, Mapping[str, object]],
                 vault: Optional[SecretsVault] = None,
                 install_dir: str | Path = ".hf_models",
                 installer: Optional[Callable[[str, Path], None]] = None) -> None:
        if not isinstance(entries, Mapping):
            raise ConfigError("hf_models catalog must be a JSON object")
        self._vault = vault
        self.install_dir = Path(install_dir)
        self._installer = installer or self._default_installer
        self._entries: Dict[str, HFModelSpec] = {}
        for model_id, raw in entries.items():
            self._entries[model_id] = self._build(model_id, raw)

    # -- construction --------------------------------------------------------

    @staticmethod
    def _build(model_id: str, raw: Mapping[str, object]) -> HFModelSpec:
        if not isinstance(raw, Mapping):
            raise ConfigError(f"HF catalog entry '{model_id}' must be an object")
        return HFModelSpec(
            model_id=model_id,
            task=str(raw.get("task", "text-generation")),
            gated=bool(raw.get("gated", False)),
            params_b=(float(raw["params_b"]) if raw.get("params_b") is not None
                      else None),
        )

    @staticmethod
    def _default_installer(model_id: str, install_dir: Path) -> None:
        """Offline-safe install: record a local marker for the model."""
        safe = model_id.replace("/", "__")
        install_dir.mkdir(parents=True, exist_ok=True)
        (install_dir / f"{safe}.json").write_text(
            json.dumps({"model_id": model_id, "installed": True}, indent=2),
            encoding="utf-8")

    # -- catalog access -------------------------------------------------------

    def list(self) -> List[HFModelSpec]:
        """Return every catalog entry (the model variety)."""
        return list(self._entries.values())

    def get(self, model_id: str) -> HFModelSpec:
        try:
            return self._entries[model_id]
        except KeyError as exc:
            raise ConfigError(f"Unknown Hugging Face model: '{model_id}'") from exc

    def is_installed(self, model_id: str) -> bool:
        safe = model_id.replace("/", "__")
        return (self.install_dir / f"{safe}.json").exists()

    # -- actions ---------------------------------------------------------------

    def install(self, model_id: str) -> Path:
        """Click-to-install a catalog model into ``install_dir``."""
        spec = self.get(model_id)  # validates the id
        self._installer(spec.model_id, self.install_dir)
        return self.install_dir

    def activate(self, model_id: str,
                 api_key_ref: Optional[str] = None) -> Dict[str, object]:
        """Activate an installed model with the user's API key.

        ``api_key_ref`` is typically a ``$VAULT:key`` reference resolved via the
        attached vault. The resolved key is returned for the caller to use but
        is never persisted by this module. Gated models require a key.
        """
        spec = self.get(model_id)
        if not self.is_installed(model_id):
            raise ConfigError(
                f"Model '{model_id}' must be installed before activation")

        key: Optional[str] = None
        if api_key_ref:
            if api_key_ref.startswith("$VAULT:"):
                if self._vault is None:
                    raise ConfigError(
                        "Activation references the vault but no vault is attached")
                key = self._vault.resolve(api_key_ref)
            else:
                key = api_key_ref

        if spec.gated and not key:
            raise ConfigError(
                f"Model '{model_id}' is gated and requires an API key")

        return {
            "model_id": spec.model_id,
            "task": spec.task,
            "gated": spec.gated,
            "activated": True,
            "api_key": key,  # returned for immediate use; never stored
        }

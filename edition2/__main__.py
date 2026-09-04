"""Command-line interface for AicodeX Edition 2.

Usage::

    python -m edition2 [--version] [--list-roles] [--config PATH]
                       [--include-disabled] [--vault PATH]

By default the CLI loads ``config/edition2_settings.json`` (relative to the
current working directory), validates the configured roles, and runs the
CHAiMERA ConductorX orchestrator, printing the resulting symphony report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .chaimera import ConductorX
from .hive import Hive
from .orchestrator import ConfigError, RoleRegistry
from .vault import SecretsVault

DEFAULT_CONFIG = Path("config") / "edition2_settings.json"
DEFAULT_VAULT = Path.home() / ".aicodex" / "edition2_vault.json"


def _load_config(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Configuration file is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration root must be a JSON object: {path}")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edition2",
        description="AicodeX Edition 2 — CHAiMERA ConductorX multi-model "
                    "orchestration.")
    parser.add_argument("--version", action="store_true",
                        help="print the Edition 2 version and exit")
    parser.add_argument("--list-roles", action="store_true",
                        help="list the configured roles and exit")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG),
                        help=f"path to the settings file (default: {DEFAULT_CONFIG})")
    parser.add_argument("--vault", default=str(DEFAULT_VAULT),
                        help="path to the local secrets vault "
                             f"(default: {DEFAULT_VAULT})")
    parser.add_argument("--include-disabled", action="store_true",
                        help="show disabled roles as skipped movements")
    parser.add_argument("--hive", action="store_true",
                        help="run the hive cluster of VMware worker bots "
                             "(parallel bandwidth analysis, trough balancing, "
                             "and research-driven data patching)")
    parser.add_argument("--backends", action="store_true",
                        help="list each model's compute-backend link "
                             "(standard / VPS / cloud / GPU) and exit")
    parser.add_argument("--metrics", action="store_true",
                        help="print the usage control-deck metrics summary")
    parser.add_argument("--metrics-html", metavar="PATH",
                        help="write the metrics web page to PATH")
    parser.add_argument("--hf-catalog", action="store_true",
                        help="list the Hugging Face model-selection catalog")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.version:
        print(f"AicodeX Edition 2 version {__version__}")
        return 0

    try:
        config = _load_config(Path(args.config))
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    vault = SecretsVault(Path(args.vault))
    try:
        registry = RoleRegistry(config.get("roles", {}), vault=vault)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list_roles:
        for role in registry.all_roles():
            state = "enabled " if role.enabled else "disabled"
            print(f"[{state}] {role.name:<22} {role.model:<10} {role.mission}")
        return 0

    if args.backends:
        from .backends import BackendRegistry
        print(BackendRegistry(registry, vault=vault).render())
        return 0

    if args.hf_catalog:
        from .hfcatalog import HuggingFaceCatalog
        hf_cfg = config.get("hf_models", {})
        entries = hf_cfg.get("entries", {}) if isinstance(hf_cfg, dict) else {}
        catalog = HuggingFaceCatalog(
            entries, vault=vault,
            install_dir=hf_cfg.get("install_dir", ".hf_models"))
        print("AicodeX Edition 2 — Hugging Face Model Catalog")
        print("=" * 60)
        for spec in catalog.list():
            gated = "gated" if spec.gated else "open "
            params = f"{spec.params_b:g}B" if spec.params_b is not None else "?"
            print(f"  [{gated}] {spec.model_id:<40} {spec.task:<18} {params}")
        return 0

    if args.metrics or args.metrics_html:
        from .metrics import MetricsPanel
        metrics_cfg = config.get("metrics", {})
        cost_map = (metrics_cfg.get("cost_per_token_usd", {})
                    if isinstance(metrics_cfg, dict) else {})
        panel = MetricsPanel(cost_per_token=cost_map)
        if args.metrics_html:
            Path(args.metrics_html).write_text(panel.render_page(),
                                               encoding="utf-8")
            print(f"metrics page written to {args.metrics_html}")
        else:
            print(panel.render_text())
        return 0

    orchestration = config.get("orchestration", {})
    seeds = set(orchestration.get("seeds", [])) if isinstance(orchestration, dict) else set()

    if args.hive:
        hive_cfg = config.get("hive", {}) if isinstance(config.get("hive"), dict) else {}
        hive = Hive.from_roles(
            registry.enabled_roles(),
            capacity=float(hive_cfg.get("worker_capacity", 100.0)),
            peak_threshold=float(hive_cfg.get("peak_threshold", 0.85)),
            trough_threshold=float(hive_cfg.get("trough_threshold", 0.30)),
            research_source_model=str(hive_cfg.get("research_source_model", "Mistral")),
        )
        report = hive.run(max_workers=int(hive_cfg.get("max_workers", 8)))
        print(report.render())
        return 0

    report = ConductorX(registry).conduct(
        only_enabled=not args.include_disabled, seeds=seeds)
    print(report.render())
    return 1 if report.failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

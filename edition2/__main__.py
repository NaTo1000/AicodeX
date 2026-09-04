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

    orchestration = config.get("orchestration", {})
    seeds = set(orchestration.get("seeds", [])) if isinstance(orchestration, dict) else set()
    report = ConductorX(registry).conduct(
        only_enabled=not args.include_disabled, seeds=seeds)
    print(report.render())
    return 1 if report.failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

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
    parser.add_argument("--monitor", action="store_true",
                        help="run the realtime monitor system and print the "
                             "live metrics display")
    parser.add_argument("--cob-report", action="store_true",
                        help="print the close-of-business daily report")
    parser.add_argument("--forum-html", metavar="PATH",
                        help="write the public community forum page to PATH")
    parser.add_argument("--crossover", action="store_true",
                        help="list the crossover code & emulation database")
    parser.add_argument("--style-fingerprint", metavar="CODE",
                        help="infer a style fingerprint from an inline code "
                             "sample and print it")
    parser.add_argument("--prompts", action="store_true",
                        help="list the six prompt registers and their "
                             "algorithmically different digests")
    parser.add_argument("--decipher-prompts", action="store_true",
                        help="decipher all six prompt registers at the same "
                             "time and reconcile by union")
    parser.add_argument("--align-prompts", action="store_true",
                        help="align committed prompt parameters against the "
                             "application's measured output and fine-tune "
                             "drifted registers")
    parser.add_argument("--ppt", action="store_true",
                        help="list the PPT (Performance Personal Tuner) "
                             "target registry — platforms, shells, hardware "
                             "and transports")
    parser.add_argument("--ppt-tier", default=None,
                        help="access tier for --ppt / --ppt-profile / "
                             "--ppt-mesh: user | professional | admin")
    parser.add_argument("--ppt-profile", metavar="NAME",
                        help="render the named PPT tuning profile from config")
    parser.add_argument("--ppt-mesh", metavar="NODES", type=int,
                        help="plan a distributed mesh cluster of NODES peers "
                             "(admin/root only)")
    parser.add_argument("--reviver", action="store_true",
                        help="run one reviver-cluster cycle (VRAM revival, "
                             "sector collection, relicensing, reality check, "
                             "threat scan, curveball, patching)")
    parser.add_argument("--reviver-scan", action="store_true",
                        help="scan the six tunnel links for 0-day trojan-door "
                             "indicators and exit")
    parser.add_argument("--reviver-testbed", action="store_true",
                        help="provision a near-real test environment and print "
                             "its fidelity")
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

    if args.monitor:
        from .monitor import MonitorSystem
        mon_cfg = config.get("monitor", {}) if isinstance(config.get("monitor"), dict) else {}
        monitor = MonitorSystem(
            refresh_interval=float(mon_cfg.get("refresh_interval_seconds", 1.0)))
        for component in mon_cfg.get("valves", []):
            monitor.valve(str(component))
        print(monitor.render())
        return 0

    if args.cob_report:
        from .cob import CobReporter
        mon_cfg = config.get("monitor", {}) if isinstance(config.get("monitor"), dict) else {}
        jobs = mon_cfg.get("cob", {}).get("jobs", []) if isinstance(mon_cfg.get("cob"), dict) else []
        reporter = CobReporter(jobs=jobs)
        print(reporter.build().render_text())
        return 0

    if args.forum_html:
        from .forum import CommunityForum
        mon_cfg = config.get("monitor", {}) if isinstance(config.get("monitor"), dict) else {}
        forum_cfg = mon_cfg.get("forum", {}) if isinstance(mon_cfg.get("forum"), dict) else {}
        forum = CommunityForum(
            refresh_seconds=float(forum_cfg.get("refresh_seconds", 2.0)))
        Path(args.forum_html).write_text(forum.render(), encoding="utf-8")
        print(f"forum page written to {args.forum_html}")
        return 0

    if args.crossover:
        from .crossover import CrossoverDatabase
        x_cfg = config.get("crossover", {}) if isinstance(config.get("crossover"), dict) else {}
        db = CrossoverDatabase(x_cfg.get("entries", {}))
        print(db.render())
        return 0

    if args.style_fingerprint is not None:
        from .style import StyleDatabase
        db = StyleDatabase()
        fp = db.learn([args.style_fingerprint])
        for key, value in fp.as_dict().items():
            print(f"{key}: {value}")
        return 0

    if args.prompts or args.decipher_prompts or args.align_prompts:
        from .prompts import PromptRegistry
        p_cfg = config.get("prompts", {}) if isinstance(config.get("prompts"), dict) else {}
        registry = PromptRegistry(p_cfg.get("registers", {}))
        registry.register()
        if args.decipher_prompts:
            print(registry.render_decipher(registry.decipher()))
        elif args.align_prompts:
            app_output = p_cfg.get("app_output", {})
            drifts = registry.align(app_output)
            guidance: list = []
            registry.fine_tune(drifts, guidance=guidance)
            print(registry.render_alignment(registry.align(app_output),
                                            guidance=guidance))
        else:
            print(registry.render())
        return 0

    if args.ppt or args.ppt_profile is not None or args.ppt_mesh is not None:
        from .ppt import PersonalTuner, TargetRegistry
        ppt_cfg = config.get("ppt", {}) if isinstance(config.get("ppt"), dict) else {}
        tuner = PersonalTuner(
            TargetRegistry(ppt_cfg.get("targets")),
            vault=vault,
            root_key_ref=str(ppt_cfg.get("root_key_ref", "$VAULT:PPT_ROOT_KEY")),
        )
        tier = str(args.ppt_tier or ppt_cfg.get("default_tier", "user"))
        try:
            if args.ppt_mesh is not None:
                mesh_cfg = (ppt_cfg.get("mesh", {})
                            if isinstance(ppt_cfg.get("mesh"), dict) else {})
                max_degree = int(mesh_cfg.get("max_degree", 4))
                print(tuner.plan_mesh(args.ppt_mesh, tier=tier,
                                      max_degree=max_degree).render())
            elif args.ppt_profile is not None:
                profiles = (ppt_cfg.get("profiles", {})
                            if isinstance(ppt_cfg.get("profiles"), dict) else {})
                raw = profiles.get(args.ppt_profile)
                if not isinstance(raw, dict):
                    print(f"error: no PPT profile named '{args.ppt_profile}'",
                          file=sys.stderr)
                    return 2
                profile = tuner.build_profile(
                    args.ppt_profile,
                    tier=str(raw.get("tier", tier)),
                    knobs=raw.get("knobs", {}),
                    targets=list(raw.get("targets", [])))
                print(tuner.render_profile(profile))
            else:
                print(tuner.registry.render(tier=tuner.effective_tier(tier)))
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    if args.reviver or args.reviver_scan or args.reviver_testbed:
        from . import reviver as rv
        r_cfg = config.get("reviver", {}) if isinstance(config.get("reviver"), dict) else {}
        tb_cfg = (r_cfg.get("testbed", {})
                  if isinstance(r_cfg.get("testbed"), dict) else {})
        cluster = rv.ReviverCluster(
            collector=rv.SectorCollector(r_cfg.get("relicensing_map")),
            curveball=rv.CurveballEngine(seed=r_cfg.get("curveball_seed", 0)),
        )
        try:
            if args.reviver_scan:
                # Scan with no payloads: report the six watched tunnels.
                tunnels = ", ".join(rv.SIX_TUNNELS)
                print("AicodeX Edition 2 — 0-day Trojan-Door Scan")
                print("=" * 60)
                print(f"watching {len(rv.SIX_TUNNELS)} tunnels: {tunnels}")
                print("signatures: "
                      + ", ".join(rv.TROJAN_SIGNATURES[:4]) + ", …")
                print("no payloads supplied on the CLI — pass them via the API")
                return 0
            if args.reviver_testbed:
                env = cluster.testbed.build(
                    "near-real",
                    containers=list(tb_cfg.get("containers", ["app"])),
                    variables=dict(tb_cfg.get("variables", {})))
                print(env.name, "fidelity:", f"{env.fidelity:.0%}",
                      f"links={env.link_count}",
                      f"containers={len(env.containers)}")
                return 0
            # Full cycle over the config's testbed + a sample sector.
            env = cluster.testbed.build(
                "near-real",
                containers=list(tb_cfg.get("containers", ["app"])),
                variables=dict(tb_cfg.get("variables", {})))
            report = cluster.run_cycle(
                [rv.Sector("weights", b"model-payload" * 64)],
                dependencies=[rv.Dependency("libx", "proprietary")],
                claims={"the patch fixes the overflow":
                        ["patch overflow resolved verified"]},
                tunnel_payloads={"ssh": "os.system('id')"},
                env=env)
            print(report.render())
        except ConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    orchestration = config.get("orchestration", {})
    seeds = set(orchestration.get("seeds", [])) if isinstance(orchestration, dict) else set()

    if args.hive:
        from .hive import PerformanceController
        hive_cfg = config.get("hive", {}) if isinstance(config.get("hive"), dict) else {}
        perf_cfg = (hive_cfg.get("performance", {})
                    if isinstance(hive_cfg.get("performance"), dict) else {})
        perf_max = perf_cfg.get("max_workers")
        performance = PerformanceController(
            max_workers=None if perf_max is None else int(perf_max),
            target_utilisation=float(perf_cfg.get("target_utilisation", 0.65)),
            band=float(perf_cfg.get("band", 0.20)),
        )
        hive = Hive.from_roles(
            registry.enabled_roles(),
            capacity=float(hive_cfg.get("worker_capacity", 100.0)),
            peak_threshold=float(hive_cfg.get("peak_threshold", 0.85)),
            trough_threshold=float(hive_cfg.get("trough_threshold", 0.30)),
            research_source_model=str(hive_cfg.get("research_source_model", "Mistral")),
            performance=performance,
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

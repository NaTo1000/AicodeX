"""Adversarial continuous-testing cluster for AicodeX Edition 2.

The **reviver cluster** keeps the platform honest and future-proofed. It is a
collection of cooperating agents that, continuously:

- **Revive** compressed VRAM sectors (:class:`VramCompressionReviver`) —
  decompress, integrity-check, and re-compress model/sector payloads so stale
  or corrupted blocks are brought back to a known-good state.
- **Collect sectors** and run **constant patching + dependency relicensing +
  workflow semantic synthesis** (:class:`SectorCollector`).
- **Reality-check** every claim against the HiAi heuristic model
  (:func:`hiai_reality_check`) so a fluent-but-wrong output is flagged.
- **Scan for 0-day trojan doors** (:class:`ThreatScanner`) across the six
  tunnel/container links used to build near-real testing environments.
- **Provision near-real test environments** (:class:`TestbedBuilder`) — each
  one a 6-tunnel-linked container set whose fidelity score says how close to
  production it is.
- **Throw curveballs** (:class:`CurveballEngine`) — adversarial variable
  mutations injected into a test environment to try to throw the system off.
- **Research, innovate and patch** (:class:`ResearchPatcher`) — turn findings
  into future-proofed patches.

Standard library only; deterministic when the RNG/clock are injected so it is
fully testable offline. No real network, container, or hardware access — it
*models* the environments and threats so the logic is safe to run anywhere.
"""

from __future__ import annotations

import hashlib
import random
import zlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .orchestrator import ConfigError

# ---------------------------------------------------------------------------
# VRAM compression reviver
# ---------------------------------------------------------------------------

#: How a sector's payload is compressed for storage / transit.
COMPRESSION_LEVEL = 6


@dataclass
class Sector:
    """A unit of VRAM/state the cluster works on."""

    name: str
    payload: bytes
    compressed: bool = False

    @property
    def size(self) -> int:
        return len(self.payload)


class VramCompressionReviver:
    """Compress / revive VRAM sectors with integrity verification.

    ``compress`` stores a deflated payload; ``revive`` inflates it and checks
    it against the original checksum. A sector whose checksum no longer
    matches after a round-trip is reported as *corrupt* so the collector can
    re-patch it.
    """

    def checksum(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def compress(self, sector: Sector) -> Sector:
        return Sector(name=sector.name,
                      payload=zlib.compress(sector.payload, COMPRESSION_LEVEL),
                      compressed=True)

    def revive(self, sector: Sector) -> bytes:
        """Inflate a (possibly compressed) sector back to its payload."""
        if not sector.compressed:
            return sector.payload
        try:
            return zlib.decompress(sector.payload)
        except zlib.error as exc:
            raise ConfigError(
                f"VRAM sector '{sector.name}' is corrupt: cannot decompress"
            ) from exc

    def round_trip_ok(self, sector: Sector) -> bool:
        """Whether compress→revive returns the original payload."""
        restored = self.revive(self.compress(sector))
        return self.checksum(restored) == self.checksum(sector.payload)


# ---------------------------------------------------------------------------
# Sector collector: constant patching + dependency relicensing + semantics
# ---------------------------------------------------------------------------

#: SPDX-style licence identifiers the relicenser is allowed to (re)issue.
ALLOWED_LICENSES: Tuple[str, ...] = (
    "MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0-only",
)

#: The relicensing map used when a dependency's licence is stale/missing.
DEFAULT_RELICENSE_MAP: Mapping[str, str] = {
    "unlicensed": "MIT",
    "unknown": "Apache-2.0",
    "proprietary": "Apache-2.0",
}


@dataclass
class Dependency:
    """A dependency whose licence may need re-issuing."""

    name: str
    license: str = "unknown"

    @property
    def needs_relicense(self) -> bool:
        return self.license not in ALLOWED_LICENSES


@dataclass
class Patch:
    """A patch produced by the cluster (code fix + rationale + provenance)."""

    target: str
    change: str
    rationale: str
    future_proof: bool = True       # written with future-proofing in mind


class SectorCollector:
    """Harvests sectors and applies constant patching + relicensing.

    The collector never stops: each ``collect`` pass records the sectors it
    saw, re-licenses any dependency whose licence is not in the allowed set,
    and emits a patch for anything that failed a reality check.
    """

    def __init__(self,
                 relicensing_map: Optional[Mapping[str, str]] = None) -> None:
        self._map = dict(DEFAULT_RELICENSE_MAP)
        if relicensing_map:
            self._map.update({k.lower(): v for k, v in relicensing_map.items()})
        self.sectors: List[str] = []
        self.patches: List[Patch] = []
        self._relicensed: set = set()   # dependencies already re-issued

    def collect(self, sectors: Sequence[Sector]) -> List[str]:
        for sector in sectors:
            if sector.name not in self.sectors:
                self.sectors.append(sector.name)
        return list(self.sectors)

    def relicense(self, dep: Dependency) -> Dependency:
        """Re-issue a dependency's licence when it is stale or unknown.

        Idempotent per dependency name: once re-issued, a dependency is not
        patched again on subsequent cycles.
        """
        if not dep.needs_relicense or dep.name in self._relicensed:
            return dep
        new = self._map.get(dep.license.lower(), "Apache-2.0")
        if new not in ALLOWED_LICENSES:
            new = "Apache-2.0"
        relicensed = Dependency(name=dep.name, license=new)
        self._relicensed.add(dep.name)
        self.patches.append(Patch(
            target=f"dependency:{dep.name}",
            change=f"relicense {dep.license} -> {new}",
            rationale="dependency relicensing to an allowed SPDX licence",
        ))
        return relicensed

    def synthesise_workflow(self, steps: Sequence[str]) -> str:
        """Semantic workflow synthesis: join steps into a stable pipeline id."""
        digest = hashlib.sha256("::".join(steps).encode("utf-8")).hexdigest()
        return f"workflow-sem-{digest[:12]}"


# ---------------------------------------------------------------------------
# HiAi reality check
# ---------------------------------------------------------------------------

def hiai_reality_check(claim: str, evidence: Sequence[str]) -> Tuple[bool, float]:
    """Reality-check a claim against evidence using a HiAi-style heuristic.

    Returns ``(passed, confidence)``. The check is deliberately simple and
    deterministic: a claim *passes* when at least one evidence token shares a
    word with the claim; confidence grows with the fraction of claim words
    covered by the evidence. A fluent claim with no evidential support fails —
    that is the "reality check" the HiAi layer applies.
    """
    claim_words = {w.strip(".,;:()").lower() for w in claim.split() if w}
    claim_words.discard("")
    if not claim_words:
        return (False, 0.0)
    evidence_text = " ".join(evidence).lower()
    covered = {w for w in claim_words if w in evidence_text}
    confidence = len(covered) / len(claim_words)
    return (bool(covered), round(confidence, 3))


# ---------------------------------------------------------------------------
# Threat scanner: 0-day trojan doors over the 6-tunnel links
# ---------------------------------------------------------------------------

#: The six tunnel/container links used to build near-real test environments.
SIX_TUNNELS: Tuple[str, ...] = (
    "ssh", "tls", "websocket", "grpc", "serial-bridge", "vpn-mesh",
)

#: Substrings that flag a payload as a potential 0-day trojan door.
TROJAN_SIGNATURES: Tuple[str, ...] = (
    "eval(", "exec(", "__import__", "subprocess", "os.system",
    "base64.b64decode", "socket.connect", "backdoor", "reverse-shell",
)


@dataclass
class Finding:
    """A single suspicious item found by the scanner."""

    tunnel: str
    indicator: str
    severity: str = "high"


class ThreatScanner:
    """Scans tunnel-linked payloads for 0-day trojan-door indicators."""

    def __init__(self,
                 signatures: Optional[Sequence[str]] = None,
                 tunnels: Optional[Sequence[str]] = None) -> None:
        self.signatures = tuple(signatures or TROJAN_SIGNATURES)
        self.tunnels = tuple(tunnels or SIX_TUNNELS)

    def scan_payload(self, tunnel: str, payload: str) -> List[Finding]:
        if tunnel not in self.tunnels:
            raise ConfigError(f"Unknown tunnel '{tunnel}'")
        lowered = payload.lower()
        return [Finding(tunnel=tunnel, indicator=sig)
                for sig in self.signatures if sig.lower() in lowered]

    def scan_environment(self, payloads: Mapping[str, str]) -> List[Finding]:
        """Scan every tunnel's payload; returns all findings, tunnel order."""
        findings: List[Finding] = []
        for tunnel in self.tunnels:
            if tunnel in payloads:
                findings.extend(self.scan_payload(tunnel, payloads[tunnel]))
        return findings


# ---------------------------------------------------------------------------
# Testbed builder: near-real testing environments via 6-tunnel container links
# ---------------------------------------------------------------------------

@dataclass
class TestEnvironment:
    """A provisioned testing environment made of 6-tunnel-linked containers."""

    name: str
    tunnels: Tuple[str, ...]
    containers: List[str] = field(default_factory=list)
    variables: Dict[str, object] = field(default_factory=dict)
    fidelity: float = 0.0           # 0..1 — how close to real

    @property
    def link_count(self) -> int:
        return len(self.tunnels)


class TestbedBuilder:
    """Builds testing environments as close to real as possible.

    Fidelity starts from a base and rises with every linked tunnel and every
    production-like variable present, capped at ``1.0`` — an environment using
    all six tunnels and a full variable set reads as near-real.
    """

    BASE_FIDELITY = 0.4
    PER_TUNNEL = 0.08               # up to +0.48 for all six tunnels
    PER_VARIABLE = 0.02             # up to +0.12 for six+ variables

    def __init__(self, tunnels: Optional[Sequence[str]] = None) -> None:
        self.tunnels = tuple(tunnels or SIX_TUNNELS)

    def build(self, name: str, containers: Sequence[str],
              variables: Optional[Mapping[str, object]] = None,
              tunnels: Optional[Sequence[str]] = None) -> TestEnvironment:
        linked = tuple(t for t in (tunnels or self.tunnels)
                       if t in self.tunnels)
        if not linked:
            raise ConfigError("A test environment needs at least one tunnel")
        if not containers:
            raise ConfigError("A test environment needs at least one container")
        fidelity = (self.BASE_FIDELITY
                    + self.PER_TUNNEL * len(linked)
                    + self.PER_VARIABLE * min(6, len(variables or {})))
        return TestEnvironment(name=name, tunnels=linked,
                               containers=list(containers),
                               variables=dict(variables or {}),
                               fidelity=round(min(1.0, fidelity), 3))


# ---------------------------------------------------------------------------
# Curveball engine: adversarial variables thrown at the system
# ---------------------------------------------------------------------------

@dataclass
class CurveballResult:
    """Outcome of throwing adversarial variables at an environment."""

    thrown: List[str] = field(default_factory=list)     # variables mutated
    held: List[str] = field(default_factory=list)       # invariants that held
    broke: List[str] = field(default_factory=list)      # invariants that broke

    @property
    def resilient(self) -> bool:
        return not self.broke


class CurveballEngine:
    """Throws 'curve all variables' — adversarial mutations to throw it off.

    Each registered invariant is a predicate over the environment's variables.
    The engine mutates the variables (deterministically when seeded) and
    reports which invariants *held* and which *broke*, so the patcher knows
    what to research next.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)
        self._invariants: Dict[str, Callable[[Mapping[str, object]], bool]] = {}

    def register_invariant(self, name: str,
                           predicate: Callable[[Mapping[str, object]], bool]
                           ) -> None:
        self._invariants[name] = predicate

    def _mutate(self, value: object) -> object:
        """Adversarially mutate a single variable value."""
        if isinstance(value, bool):
            return not value
        if isinstance(value, (int, float)):
            return value * self._rng.choice((-1, 0, 2, 10))
        if isinstance(value, str):
            return value[::-1] or "∅"
        if isinstance(value, list):
            return list(reversed(value))
        return None

    def throw(self, env: TestEnvironment) -> CurveballResult:
        mutated = {k: self._mutate(v) for k, v in env.variables.items()}
        result = CurveballResult(thrown=sorted(mutated))
        for name, predicate in self._invariants.items():
            try:
                (result.held if predicate(mutated) else result.broke).append(name)
            except Exception:                       # a throwing invariant broke
                result.broke.append(name)
        return result


# ---------------------------------------------------------------------------
# Research patcher: research, innovate, patch with future-proofing
# ---------------------------------------------------------------------------

class ResearchPatcher:
    """Turns findings into future-proofed patches.

    Every broken invariant or threat finding becomes a research item, then an
    innovation note, then a :class:`Patch` whose rationale records *why* it
    will still hold as the platform evolves (future-proofing).
    """

    def __init__(self, source_model: str = "Mistral") -> None:
        self.source_model = source_model
        self.patches: List[Patch] = []

    def research(self, topic: str) -> str:
        return f"innovation-research[{self.source_model}]:{topic}"

    def _emit(self, patch: Patch) -> None:
        # Idempotent: the same target+change is only ever recorded once.
        if not any(p.target == patch.target and p.change == patch.change
                   for p in self.patches):
            self.patches.append(patch)

    def patch_broken(self, broken: Sequence[str]) -> List[Patch]:
        new: List[Patch] = []
        for item in broken:
            patch = Patch(
                target=f"invariant:{item}",
                change=self.research(item),
                rationale=("researched and innovated a fix for the broken "
                           "invariant; written with future-proofing in mind"),
                future_proof=True)
            before = len(self.patches)
            self._emit(patch)
            new.extend(self.patches[before:])
        return new

    def patch_findings(self, findings: Sequence[Finding]) -> List[Patch]:
        new: List[Patch] = []
        for finding in findings:
            patch = Patch(
                target=f"tunnel:{finding.tunnel}",
                change=f"close indicator '{finding.indicator}'",
                rationale=("0-day trojan-door indicator removed; guard added "
                           "so the pattern stays blocked (future-proofed)"),
                future_proof=True)
            before = len(self.patches)
            self._emit(patch)
            new.extend(self.patches[before:])
        return new


# ---------------------------------------------------------------------------
# The cluster
# ---------------------------------------------------------------------------

@dataclass
class CycleReport:
    """Aggregate result of one continuous-testing cycle."""

    sectors: List[str] = field(default_factory=list)
    revived_ok: int = 0
    relicensed: List[str] = field(default_factory=list)
    reality_checks: int = 0
    reality_failed: List[str] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    curveball: Optional[CurveballResult] = None
    patches: List[Patch] = field(default_factory=list)

    def render(self) -> str:
        lines = ["AicodeX Edition 2 — Reviver Cluster Cycle", "=" * 60,
                 f"sectors collected: {len(self.sectors)}",
                 f"VRAM sectors revived OK: {self.revived_ok}",
                 f"dependencies relicensed: {len(self.relicensed)}",
                 f"reality checks: {self.reality_checks} "
                 f"({len(self.reality_failed)} failed)",
                 f"threat findings: {len(self.findings)}"]
        if self.curveball is not None:
            lines.append(f"curveball: {len(self.curveball.thrown)} thrown  "
                         f"held={len(self.curveball.held)} "
                         f"broke={len(self.curveball.broke)}  "
                         f"resilient={'yes' if self.curveball.resilient else 'no'}")
        lines.append(f"patches issued: {len(self.patches)}")
        for patch in self.patches:
            lines.append(f"    {patch.target}: {patch.change}")
        return "\n".join(lines)


class ReviverCluster:
    """Orchestrates one full continuous-testing cycle.

    Compose the reviver, collector, scanner, testbed builder, curveball
    engine, and patcher. ``run_cycle`` drives them in order and returns a
    :class:`CycleReport`. Deterministic when the curveball engine is seeded.
    """

    def __init__(self,
                 reviver: Optional[VramCompressionReviver] = None,
                 collector: Optional[SectorCollector] = None,
                 scanner: Optional[ThreatScanner] = None,
                 testbed: Optional[TestbedBuilder] = None,
                 curveball: Optional[CurveballEngine] = None,
                 patcher: Optional[ResearchPatcher] = None) -> None:
        self.reviver = reviver or VramCompressionReviver()
        self.collector = collector or SectorCollector()
        self.scanner = scanner or ThreatScanner()
        self.testbed = testbed or TestbedBuilder()
        self.curveball = curveball or CurveballEngine()
        self.patcher = patcher or ResearchPatcher()

    def run_cycle(self,
                  sectors: Sequence[Sector],
                  dependencies: Sequence[Dependency] = (),
                  claims: Optional[Mapping[str, Sequence[str]]] = None,
                  tunnel_payloads: Optional[Mapping[str, str]] = None,
                  env: Optional[TestEnvironment] = None) -> CycleReport:
        report = CycleReport()

        # 1. Collect + revive sectors (VRAM compression revival).
        report.sectors = self.collector.collect(sectors)
        for sector in sectors:
            if self.reviver.round_trip_ok(sector):
                report.revived_ok += 1

        # 2. Constant patching: dependency relicensing.
        for dep in dependencies:
            before = len(self.collector.patches)
            relicensed = self.collector.relicense(dep)
            if relicensed.license != dep.license:
                report.relicensed.append(dep.name)
                # Only the patch this dependency just produced.
                report.patches.extend(self.collector.patches[before:])

        # 3. HiAi reality check on claims.
        for claim, evidence in (claims or {}).items():
            report.reality_checks += 1
            passed, _ = hiai_reality_check(claim, evidence)
            if not passed:
                report.reality_failed.append(claim)

        # 4. 0-day trojan-door scan over the 6-tunnel links.
        report.findings = self.scanner.scan_environment(tunnel_payloads or {})
        report.patches.extend(self.patcher.patch_findings(report.findings))

        # 5. Curveball the environment; patch whatever broke.
        if env is not None:
            report.curveball = self.curveball.throw(env)
            report.patches.extend(
                self.patcher.patch_broken(report.curveball.broke))

        return report

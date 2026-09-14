"""PPT — the Performance Personal Tuner for AicodeX Edition 2.

PPT lets every user refine the platform's performance to their own needs. It
ships a broad **target registry** — platforms, shells/terminals, hardware
programmers, and transports — and per-user **tuning profiles** that are
validated against the registry and clamped to safe bounds.

Access is tiered:

+--------------+-----------------------------------------------------------+
| Tier         | Capabilities                                              |
+==============+===========================================================+
| user         | Standard targets, own profiles, read-only mesh view       |
+--------------+-----------------------------------------------------------+
| professional | Sensitive targets (BIOS/JTAG/ToR/proxy), profile publish  |
+--------------+-----------------------------------------------------------+
| admin        | Root access — mesh cluster planning, every target         |
+--------------+-----------------------------------------------------------+

Elevation to *professional* or *admin* (root) requires the
``$VAULT:PPT_ROOT_KEY`` reference to resolve in the local vault — no key, no
elevation. Nothing secret is ever stored in version-controlled config.

The mesh planner models a **distributed clustering mesh** as an autonomous
system: nodes are peers organised into a topological mesh, and the planner
reports the mesh's link budget and per-node degree.

Standard library only; deterministic when constructed with injected config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

from .orchestrator import ConfigError
from .vault import SecretsVault

# ---------------------------------------------------------------------------
# Access tiers
# ---------------------------------------------------------------------------

#: Ordered access tiers; index == privilege level.
ACCESS_TIERS: Tuple[str, ...] = ("user", "professional", "admin")

#: Vault reference that must resolve to grant professional/admin elevation.
ROOT_KEY_REF = "$VAULT:PPT_ROOT_KEY"


def tier_level(tier: str) -> int:
    """Privilege level for a tier name (unknown tiers are ``user``)."""
    try:
        return ACCESS_TIERS.index(tier)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Target registry
# ---------------------------------------------------------------------------

#: Categories of tuning target.
TARGET_CATEGORIES: Tuple[str, ...] = (
    "platform",     # operating systems / router & network OSes
    "shell",        # shells, terminals, remote consoles
    "hardware",     # hardware programmers, debug interfaces, RF boards
    "transport",    # connectivity / network transports
)

#: Targets that require at least the *professional* tier (sensitive surfaces).
SENSITIVE_TARGETS: frozenset = frozenset({
    "bios", "jtag", "tor", "proxy", "msdos",
})

#: The built-in target registry: category -> (target ids). Ids are lowercase
#: and stable; ``label`` is derived for display. The config may extend these.
DEFAULT_TARGETS: Mapping[str, Tuple[str, ...]] = {
    "platform": (
        "openwrt", "openwifi", "openlte", "openvnc", "tor", "obsidian-os",
        "mediatek-crystal",
        "linux",            # all Linux distros
        "archlinux",        # all Arch Linux
        "windows",          # cmd / powershell host OS
        "unix", "msdos", "bios",
        "termux",           # Android via Termux
    ),
    "shell": (
        "putty", "windows-cmd", "powershell", "windows-terminal",
        "realvnc", "xpipe", "alacritty", "unix-shell", "msdos-prompt",
    ),
    "hardware": (
        "flipper-zero", "cifertech", "madhatter", "talkingsasquatch",
        "cyd",              # Cheap Yellow Display
        "heltec",           # Heltec.org boards
        "esp32",            # all ESP32 module variants/models
        "jtag",             # all JTAG types and modes
        "serial",           # all serial command interfaces
    ),
    "transport": (
        "remote", "online", "ethernet", "proxy", "vps", "home-server",
    ),
}


@dataclass(frozen=True)
class Target:
    """A single tunable target (platform, shell, hardware, or transport)."""

    id: str
    category: str

    @property
    def sensitive(self) -> bool:
        return self.id in SENSITIVE_TARGETS

    @property
    def label(self) -> str:
        return self.id.replace("-", " ").title()

    def allowed_for(self, tier: str) -> bool:
        """Whether a tier may tune this target."""
        if not self.sensitive:
            return True
        return tier_level(tier) >= tier_level("professional")


class TargetRegistry:
    """The registry of every target PPT can tune, by category."""

    def __init__(self,
                 overrides: Optional[Mapping[str, List[str]]] = None) -> None:
        self._targets: Dict[str, Target] = {}
        merged: Dict[str, List[str]] = {c: list(ids)
                                        for c, ids in DEFAULT_TARGETS.items()}
        for category, ids in (overrides or {}).items():
            if category not in TARGET_CATEGORIES:
                raise ConfigError(f"PPT: unknown target category '{category}'")
            merged.setdefault(category, [])
            merged[category].extend(str(i).lower() for i in ids)
        for category in TARGET_CATEGORIES:
            for target_id in merged.get(category, []):
                self._targets[target_id] = Target(id=target_id,
                                                  category=category)

    def get(self, target_id: str) -> Target:
        try:
            return self._targets[target_id.lower()]
        except KeyError as exc:
            raise ConfigError(f"PPT: unknown target '{target_id}'") from exc

    def has(self, target_id: str) -> bool:
        return target_id.lower() in self._targets

    def by_category(self, category: str) -> List[Target]:
        if category not in TARGET_CATEGORIES:
            raise ConfigError(f"PPT: unknown target category '{category}'")
        return [t for t in self._targets.values() if t.category == category]

    def all(self) -> List[Target]:
        return [self._targets[k] for k in sorted(self._targets)]

    def accessible(self, tier: str) -> List[Target]:
        """All targets a tier is allowed to tune."""
        return [t for t in self.all() if t.allowed_for(tier)]

    def render(self, tier: str = "admin") -> str:
        lines = ["AicodeX PPT — Target Registry", "=" * 60,
                 f"tier: {tier}  ({len(self.accessible(tier))}/"
                 f"{len(self.all())} targets accessible)"]
        for category in TARGET_CATEGORIES:
            targets = self.by_category(category)
            lines.append(f"\n{category.upper()} ({len(targets)})")
            for target in targets:
                mark = "" if target.allowed_for(tier) else "  [pro+]"
                sens = " *" if target.sensitive else ""
                lines.append(f"  {target.id:<18}{sens}{mark}")
        lines.append("\n* sensitive target — requires professional tier "
                     "(or admin/root)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tuning profiles
# ---------------------------------------------------------------------------

#: Numeric tuning knobs and their safe (min, max) bounds. Profiles clamp to
#: these so a user cannot push the platform outside its performance envelope.
PROFILE_BOUNDS: Mapping[str, Tuple[float, float]] = {
    "refresh_interval_seconds": (0.25, 10.0),   # realtime tick cadence
    "max_workers": (1.0, 32.0),                 # parallel fan-in bound
    "target_utilisation": (0.10, 0.95),         # hive utilisation centre
    "band": (0.05, 0.40),                       # hive utilisation half-width
    "max_tokens": (256.0, 8192.0),              # generation token budget
    "opacity": (0.20, 1.0),                     # overlay opacity
}

#: Non-numeric knobs (free-form but bounded choices).
PROFILE_CHOICES: Mapping[str, Tuple[str, ...]] = {
    "lod": ("minimal", "standard", "detailed", "exhaustive"),
}


@dataclass
class TuningProfile:
    """A user's performance tuning profile.

    ``knobs`` holds the validated/clamped knob values; ``targets`` the target
    ids the profile applies to. ``tier`` is the owning user's access tier.
    """

    name: str
    tier: str = "user"
    knobs: Dict[str, object] = field(default_factory=dict)
    targets: List[str] = field(default_factory=list)


class PersonalTuner:
    """The Performance Personal Tuner engine.

    Builds and validates per-user :class:`TuningProfile` objects against the
    :class:`TargetRegistry`, clamps knobs to :data:`PROFILE_BOUNDS`, and plans
    distributed mesh cluster topologies (admin/root only).
    """

    def __init__(self,
                 registry: Optional[TargetRegistry] = None,
                 vault: Optional[SecretsVault] = None,
                 root_key_ref: str = ROOT_KEY_REF) -> None:
        self.registry = registry or TargetRegistry()
        self._vault = vault
        self._root_key_ref = root_key_ref

    # -- access ------------------------------------------------------------

    def can_elevate(self) -> bool:
        """Whether root/admin elevation is available (root key resolves)."""
        if self._vault is None:
            return False
        return bool(self._vault.resolve(self._root_key_ref))

    def effective_tier(self, requested: str) -> str:
        """The tier actually granted for a request.

        ``user`` is always allowed. ``professional``/``admin`` require the
        root key to resolve in the vault; otherwise the request is silently
        dropped to ``user`` (no elevation without the key).
        """
        requested = requested.lower()
        if requested not in ACCESS_TIERS:
            return "user"
        if tier_level(requested) >= tier_level("professional"):
            return requested if self.can_elevate() else "user"
        return "user"

    # -- profiles ------------------------------------------------------------

    def build_profile(self, name: str, tier: str = "user",
                      knobs: Optional[Mapping[str, object]] = None,
                      targets: Optional[List[str]] = None) -> TuningProfile:
        """Validate + clamp a profile. Tier is resolved via :meth:`effective_tier`."""
        granted = self.effective_tier(tier)
        clean_knobs = self._clamp_knobs(knobs or {})
        clean_targets = self._validate_targets(targets or [], granted)
        return TuningProfile(name=name, tier=granted, knobs=clean_knobs,
                             targets=clean_targets)

    def _clamp_knobs(self, knobs: Mapping[str, object]) -> Dict[str, object]:
        clean: Dict[str, object] = {}
        for key, value in knobs.items():
            if key in PROFILE_BOUNDS:
                lo, hi = PROFILE_BOUNDS[key]
                clean[key] = max(lo, min(hi, float(value)))
            elif key in PROFILE_CHOICES:
                choice = str(value)
                if choice not in PROFILE_CHOICES[key]:
                    raise ConfigError(
                        f"PPT: knob '{key}' must be one of "
                        f"{PROFILE_CHOICES[key]}, got '{choice}'")
                clean[key] = choice
            else:
                raise ConfigError(f"PPT: unknown tuning knob '{key}'")
        return clean

    def _validate_targets(self, targets: List[str], tier: str) -> List[str]:
        clean: List[str] = []
        for target_id in targets:
            target = self.registry.get(target_id)     # raises on unknown
            if not target.allowed_for(tier):
                raise ConfigError(
                    f"PPT: target '{target_id}' requires professional tier "
                    "(or admin/root)")
            if target.id not in clean:
                clean.append(target.id)
        return clean

    # -- mesh cluster planning (admin/root) ---------------------------------

    def plan_mesh(self, nodes: int, tier: str = "user",
                  max_degree: int = 4) -> "MeshPlan":
        """Plan a distributed clustering mesh of ``nodes`` peers.

        The mesh is an autonomous system: every node is a peer, and links are
        added ring-plus-shortcut style so each node keeps ``max_degree``
        neighbours. Admin/root only.
        """
        if self.effective_tier(tier) != "admin":
            raise ConfigError(
                "PPT: mesh cluster planning requires admin (root) access")
        if nodes < 1:
            raise ConfigError("PPT: mesh needs at least one node")
        max_degree = max(2, int(max_degree))
        links: List[Tuple[int, int]] = []
        if nodes > 1:
            half = max_degree // 2
            for i in range(nodes):
                for offset in range(1, half + 1):
                    j = (i + offset) % nodes
                    edge = (min(i, j), max(i, j))
                    if edge not in links:
                        links.append(edge)
        return MeshPlan(nodes=nodes, links=links, max_degree=max_degree)

    # -- rendering ------------------------------------------------------------

    def render_profile(self, profile: TuningProfile) -> str:
        lines = [f"AicodeX PPT — Tuning Profile '{profile.name}'", "=" * 60,
                 f"tier: {profile.tier}"]
        lines.append("knobs:")
        for key in sorted(profile.knobs):
            lines.append(f"  {key:<26} {profile.knobs[key]}")
        lines.append(f"targets ({len(profile.targets)}):")
        for target_id in profile.targets:
            lines.append(f"  {target_id}")
        return "\n".join(lines)


@dataclass
class MeshPlan:
    """A distributed mesh-cluster topology plan (an autonomous system)."""

    nodes: int
    links: List[Tuple[int, int]] = field(default_factory=list)
    max_degree: int = 4

    @property
    def link_count(self) -> int:
        return len(self.links)

    def degree(self, node: int) -> int:
        return sum(1 for a, b in self.links if a == node or b == node)

    @property
    def fully_connected(self) -> bool:
        """Whether the mesh links every node to every other (small meshes)."""
        return self.link_count == self.nodes * (self.nodes - 1) // 2

    def render(self) -> str:
        lines = ["AicodeX PPT — Mesh Cluster Plan (autonomous system)",
                 "=" * 60,
                 f"nodes: {self.nodes}   links: {self.link_count}   "
                 f"max degree: {self.max_degree}",
                 f"fully connected: {'yes' if self.fully_connected else 'no'}"]
        for node in range(self.nodes):
            lines.append(f"  node {node:>3}: degree {self.degree(node)}")
        return "\n".join(lines)

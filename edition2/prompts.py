"""Prompt registers with simultaneous decipher for AicodeX Edition 2.

Six **prompt registers** hold the per-role working prompts. Each register
*commits* its prompt under an **algorithmically different** digest — no two
registers use the same hash algorithm — so the set of commitments is
structurally diverse:

+----------+------------+
| Register | Algorithm  |
+==========+============+
| R1       | sha256     |
+----------+------------+
| R2       | sha3_256   |
+----------+------------+
| R3       | blake2s    |
+----------+------------+
| R4       | blake2b    |
+----------+------------+
| R5       | sha512     |
+----------+------------+
| R6       | md5        |
+----------+------------+

Registration commits every enabled register; **decipherment runs all six at
the same time** (:class:`concurrent.futures.ThreadPoolExecutor`) and the
results are reconciled by *set union*, so a prompt recovered by any register
is never missed, and a register whose committed digest no longer matches
(tampered) or whose prompt was dropped (lost) is detected rather than
silently skipped.

Standard library only; deterministic when constructed with injected register
definitions.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import hashlib
from typing import Dict, List, Mapping, Optional, Tuple

from .orchestrator import ConfigError

# The six prompt registers, each bound to an algorithmically different digest.
REGISTER_ALGORITHMS: Tuple[Tuple[str, str], ...] = (
    ("R1", "sha256"),
    ("R2", "sha3_256"),
    ("R3", "blake2s"),
    ("R4", "blake2b"),
    ("R5", "sha512"),
    ("R6", "md5"),
)

REGISTER_NAMES: Tuple[str, ...] = tuple(name for name, _ in REGISTER_ALGORITHMS)


#: Numeric generation parameters each commitment carries, with (min, max)
#: bounds the fine-tuner is allowed to move them within.
PARAMETER_BOUNDS: Mapping[str, Tuple[float, float]] = {
    "temperature": (0.0, 2.0),
    "top_p": (0.0, 1.0),
    "max_tokens": (1.0, 8192.0),
    "max_bytes": (256.0, 262144.0),   # application size ceiling per output
}

#: Levels of detail, most-reduced to most-extended. The committed ``lod``
#: selects the baseline; ``extend_step``/``reduce_step`` move it.
LOD_LEVELS: Tuple[str, ...] = ("minimal", "standard", "detailed", "exhaustive")

#: Per-level guidance: when to apply, and the code-size factor the level
#: multiplies the token budget by (extension > 1 grows code, reduction < 1
#: shrinks it) so application size does not blow out.
LOD_GUIDANCE: Mapping[str, Mapping[str, object]] = {
    "minimal": {
        "factor": 0.4,   # strong reduction
        "when": "scaffolding, stubs, hot paths, size-constrained targets",
        "where": "anywhere output size matters more than completeness",
    },
    "standard": {
        "factor": 1.0,   # baseline
        "when": "default generation for general-purpose code",
        "where": "most roles; balanced detail vs size",
    },
    "detailed": {
        "factor": 1.6,   # moderate extension
        "when": "public APIs, security/compliance code, tricky algorithms",
        "where": "where correctness/detail matters; watch the size ceiling",
    },
    "exhaustive": {
        "factor": 2.5,   # full extension — apply sparingly
        "when": "reference docs, audits, one-off deep dives",
        "where": "only where a full treatment is explicitly required",
    },
}

#: Default committed parameters for a register that does not seed its own.
DEFAULT_PARAMETERS: Mapping[str, object] = {
    "lod": "standard",
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 2048.0,
    "max_bytes": 65536.0,
    "extend_step": 1,   # levels to move up when extending
    "reduce_step": 1,   # levels to move down when reducing
}


def _clamp(name: str, value: float) -> float:
    lo, hi = PARAMETER_BOUNDS[name]
    return max(lo, min(hi, float(value)))


def _token_budget(params: Mapping[str, object]) -> float:
    """Effective token budget for a parameter set: base tokens × LoD factor."""
    lod = str(params.get("lod", "standard"))
    factor = float(LOD_GUIDANCE.get(lod, LOD_GUIDANCE["standard"])["factor"])
    base = float(params.get("max_tokens", DEFAULT_PARAMETERS["max_tokens"]))
    return base * factor


@dataclass(frozen=True)
class PromptCommitment:
    """A prompt committed under one register's digest algorithm.

    ``parameters`` are the generation parameters committed alongside the
    prompt (LoD level, temperature, top_p, max_tokens, max_bytes ceiling,
    extend/reduce steps). They are folded into the digest so a parameter
    change is a different commitment.
    """

    register: str
    role: str
    prompt: str
    algorithm: str
    digest: str
    parameters: Mapping[str, object] = field(default_factory=dict)


@dataclass
class AlignmentDrift:
    """One register's measured drift between committed and observed output."""

    register: str
    role: str
    # parameter -> (committed, observed-from-application-output)
    drift: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    # Set when the observed output size exceeded the committed max_bytes
    # ceiling (an application size blowout).
    size_blowout: bool = False

    @property
    def aligned(self) -> bool:
        return not self.drift and not self.size_blowout


@dataclass
class DecipherResult:
    """The outcome of deciphering all registers at the same time.

    Attributes
    ----------
    recovered:
        ``{role: prompt}`` for every prompt recovered from any register.
        Reconciled by set union across registers — nothing recovered is lost.
    prompts:
        The union of every distinct prompt string recovered.
    mismatched:
        Registers whose stored prompt no longer matches its committed digest
        (tampered).
    missing:
        Registers whose prompt was dropped before decipherment (lost).
    ok:
        True only when every register was deciphered clean and present.
    """

    recovered: Dict[str, str] = field(default_factory=dict)
    prompts: List[str] = field(default_factory=list)
    mismatched: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    ok: bool = True


class PromptRegistry:
    """Six prompt registers; commit each differently, decipher all at once."""

    def __init__(self, definitions: Optional[Mapping[str, Mapping[str, object]]] = None,
                 max_workers: int = 6) -> None:
        # definitions: {register: {"role", "prompt", "algorithm"?,
        # "parameters"?}}; a definition may override "algorithm" but the
        # default keeps the six distinct.
        self._defs: Dict[str, Tuple[str, str, str]] = {}
        self._params: Dict[str, Dict[str, object]] = {}
        for name, algorithm in REGISTER_ALGORITHMS:
            raw = (definitions or {}).get(name, {})
            if raw is None:
                raw = {}
            if not isinstance(raw, Mapping):
                raise ConfigError(f"Prompt register '{name}' must be a JSON object")
            role = str(raw.get("role", name))
            prompt = str(raw.get("prompt", ""))
            algo = str(raw.get("algorithm", algorithm))
            if algo not in hashlib.algorithms_available:
                raise ConfigError(
                    f"Prompt register '{name}': unknown digest algorithm '{algo}'")
            self._defs[name] = (role, prompt, algo)
            self._params[name] = self._build_params(name, raw.get("parameters"))
        self.max_workers = max(1, int(max_workers))
        self._committed: Dict[str, PromptCommitment] = {}
        # Post-registration mutations applied by tests/simulation:
        #   _dropped  — registers whose prompt was lost before decipherment
        #   _tampered — registers whose prompt was altered after commitment
        self._dropped: set = set()
        self._tampered: Dict[str, str] = {}

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _build_params(register: str,
                      raw: Optional[Mapping[str, object]]) -> Dict[str, object]:
        params: Dict[str, object] = dict(DEFAULT_PARAMETERS)
        if raw is not None:
            if not isinstance(raw, Mapping):
                raise ConfigError(
                    f"Prompt register '{register}': 'parameters' must be an object")
            params.update(raw)
        lod = str(params.get("lod", "standard"))
        if lod not in LOD_LEVELS:
            raise ConfigError(
                f"Prompt register '{register}': lod must be one of "
                f"{LOD_LEVELS}, got '{lod}'")
        params["lod"] = lod
        for key in PARAMETER_BOUNDS:
            params[key] = _clamp(key, float(params[key]))
        params["extend_step"] = max(1, int(params.get("extend_step", 1)))
        params["reduce_step"] = max(1, int(params.get("reduce_step", 1)))
        return params

    @staticmethod
    def _digest(algorithm: str, prompt: str,
                parameters: Optional[Mapping[str, object]] = None) -> str:
        h = hashlib.new(algorithm)
        h.update(prompt.encode("utf-8"))
        if parameters:
            # Fold parameters into the commitment digest in a canonical order.
            for key in sorted(parameters):
                h.update(f"{key}={parameters[key]}".encode("utf-8"))
        return h.hexdigest()

    # -- registration ------------------------------------------------------

    def register(self) -> List[PromptCommitment]:
        """Commit every register's prompt + parameters under its algorithm."""
        self._committed = {}
        for name in REGISTER_NAMES:
            role, prompt, algorithm = self._defs[name]
            params = dict(self._params[name])
            self._committed[name] = PromptCommitment(
                register=name, role=role, prompt=prompt,
                algorithm=algorithm, parameters=params,
                digest=self._digest(algorithm, prompt, params))
        return [self._committed[name] for name in REGISTER_NAMES]

    def commitment(self, register: str) -> PromptCommitment:
        try:
            return self._committed[register]
        except KeyError as exc:
            raise ConfigError(
                f"Register '{register}' has not been committed") from exc

    def algorithms(self) -> Dict[str, str]:
        """``{register: algorithm}`` — all six algorithmically different."""
        return {name: self._defs[name][2] for name in REGISTER_NAMES}

    # -- simultaneous decipherment ------------------------------------------

    def drop(self, register: str) -> None:
        """Simulate a register losing its prompt before decipherment."""
        self._dropped.add(register)

    def tamper(self, register: str, new_prompt: str) -> None:
        """Simulate a register's prompt being altered after commitment."""
        self._tampered[register] = new_prompt

    def _decipher_one(self, register: str) -> Tuple[str, Optional[str], str]:
        """Decipher a single register.

        Returns ``(register, prompt_or_None, status)`` where status is one of
        ``ok`` | ``tampered`` | ``missing``.
        """
        commitment = self._committed[register]
        if register in self._dropped:
            return (register, None, "missing")
        prompt = self._tampered.get(register, commitment.prompt)
        if self._digest(commitment.algorithm, prompt,
                        commitment.parameters) != commitment.digest:
            return (register, None, "tampered")
        return (register, prompt, "ok")

    def decipher(self) -> DecipherResult:
        """Decipher all six registers *at the same time* and reconcile by union.

        Every register is deciphered concurrently; results are merged so that
        any prompt recovered by any register appears in the result — the union
        never misses anything — while tampered or lost registers are reported
        rather than silently dropped.
        """
        if not self._committed:
            self.register()
        result = DecipherResult()
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            outcomes = list(pool.map(self._decipher_one, REGISTER_NAMES))
        seen_prompts: set = set()
        for register, prompt, status in outcomes:
            if status == "ok" and prompt is not None:
                commitment = self._committed[register]
                result.recovered[commitment.role] = prompt
                if prompt not in seen_prompts:
                    seen_prompts.add(prompt)
                    result.prompts.append(prompt)
            elif status == "tampered":
                result.mismatched.append(register)
                result.ok = False
            else:
                result.missing.append(register)
                result.ok = False
        return result

    # -- alignment & fine-tuning ---------------------------------------------

    def align(self, app_output: Mapping[str, Mapping[str, float]],
              tolerance: float = 0.05) -> List[AlignmentDrift]:
        """Compare committed parameters against the application's output.

        ``app_output`` maps a *role* to its measured output stats — e.g. from
        the metrics control deck — with any of ``tokens_per_output``,
        ``bytes_per_output``, ``temperature``, ``top_p``. A register drifts
        when its committed parameter differs from the observed value by more
        than ``tolerance`` (relative), or when the observed output size exceeds
        the committed ``max_bytes`` ceiling (a size blowout).

        Returns one :class:`AlignmentDrift` per register, in register order.
        """
        if not self._committed:
            self.register()
        drifts: List[AlignmentDrift] = []
        for name in REGISTER_NAMES:
            commitment = self._committed[name]
            observed = app_output.get(commitment.role, {})
            params = commitment.parameters
            drift = AlignmentDrift(register=name, role=commitment.role)

            # Token budget drift (committed budget vs observed tokens/output).
            obs_tokens = observed.get("tokens_per_output")
            if obs_tokens is not None:
                committed = _token_budget(params)
                if self._drifted(committed, float(obs_tokens), tolerance):
                    drift.drift["max_tokens"] = (committed, float(obs_tokens))

            # Size blowout: observed bytes exceed the committed ceiling.
            obs_bytes = observed.get("bytes_per_output")
            if obs_bytes is not None:
                ceiling = float(params["max_bytes"])
                if float(obs_bytes) > ceiling:
                    drift.size_blowout = True
                    drift.drift["max_bytes"] = (ceiling, float(obs_bytes))

            # Numeric generation-parameter drift.
            for key in ("temperature", "top_p"):
                if key in observed:
                    committed = float(params[key])
                    if self._drifted(committed, float(observed[key]), tolerance):
                        drift.drift[key] = (committed, float(observed[key]))

            drifts.append(drift)
        return drifts

    @staticmethod
    def _drifted(committed: float, observed: float, tolerance: float) -> bool:
        scale = max(abs(committed), 1e-9)
        return abs(observed - committed) / scale > tolerance

    def fine_tune(self, drifts: List[AlignmentDrift],
                  guidance: Optional[List[str]] = None) -> List[PromptCommitment]:
        """Nudge drifted registers' parameters back into alignment.

        - **Size blowout** → *reduce*: lower the LoD level by ``reduce_step``
          and shrink ``max_tokens`` toward the observed size (code reduction).
        - **Observed far under budget** → *extend*: raise the LoD level by
          ``extend_step`` when more detail is expected (code extension).
        - Numeric parameters (``temperature``/``top_p``/``max_tokens``) are
          moved halfway toward the observed value and clamped to their bounds.

        Returns the re-committed registers that changed. ``guidance`` (when
        given) collects human-readable where/when notes for each adjustment.
        """
        changed: List[PromptCommitment] = []
        for drift in drifts:
            if drift.aligned:
                continue
            name = drift.register
            params = dict(self._params[name])
            lod = str(params["lod"])
            idx = LOD_LEVELS.index(lod)

            if drift.size_blowout:
                # Reduce: drop LoD and pull the token budget under the ceiling.
                new_idx = max(0, idx - int(params["reduce_step"]))
                params["lod"] = LOD_LEVELS[new_idx]
                observed = drift.drift.get("max_bytes", (None, None))[1]
                if observed:
                    params["max_tokens"] = _clamp(
                        "max_tokens", min(float(params["max_tokens"]),
                                          float(observed)))
                if guidance is not None:
                    g = LOD_GUIDANCE[params["lod"]]
                    guidance.append(
                        f"{name} ({drift.role}): reduce → {params['lod']} "
                        f"(size blowout; apply when {g['when']})")
            elif "max_tokens" in drift.drift:
                committed, observed = drift.drift["max_tokens"]
                if observed < committed * 0.5:
                    # Far under budget: room to extend detail.
                    new_idx = min(len(LOD_LEVELS) - 1,
                                  idx + int(params["extend_step"]))
                    params["lod"] = LOD_LEVELS[new_idx]
                    if guidance is not None:
                        g = LOD_GUIDANCE[params["lod"]]
                        guidance.append(
                            f"{name} ({drift.role}): extend → {params['lod']} "
                            f"(headroom; apply where {g['where']})")
                params["max_tokens"] = _clamp(
                    "max_tokens", (committed + observed) / 2.0)

            for key in ("temperature", "top_p"):
                if key in drift.drift:
                    committed, observed = drift.drift[key]
                    params[key] = _clamp(key, (committed + observed) / 2.0)

            self._params[name] = params
            changed.append(self.commitment(name))
        # Re-commit every register so digests reflect the tuned parameters.
        self.register()
        return changed

    def parameters(self, register: str) -> Mapping[str, object]:
        """The register's current committed parameters."""
        return dict(self.commitment(register).parameters)

    # -- reporting ----------------------------------------------------------

    def render(self) -> str:
        lines = ["AicodeX Edition 2 — Prompt Registers", "=" * 60]
        for name in REGISTER_NAMES:
            role, prompt, algorithm = self._defs[name]
            state = "committed" if name in self._committed else "pending  "
            lines.append(f"  [{state}] {name}  {algorithm:<9} {role:<20} "
                         f"prompt={len(prompt)} chars")
        distinct = len({a for a in self.algorithms().values()})
        lines.append("-" * 60)
        lines.append(f"registers: {len(REGISTER_NAMES)}  "
                     f"distinct algorithms: {distinct}")
        return "\n".join(lines)

    def render_decipher(self, result: DecipherResult) -> str:
        lines = ["AicodeX Edition 2 — Simultaneous Decipher", "=" * 60,
                 f"recovered {len(result.recovered)} role prompt(s), "
                 f"{len(result.prompts)} distinct prompt(s)"]
        for role, prompt in result.recovered.items():
            lines.append(f"  {role:<20} {prompt}")
        if result.mismatched:
            lines.append("tampered: " + ", ".join(result.mismatched))
        if result.missing:
            lines.append("missing:  " + ", ".join(result.missing))
        lines.append("status: " + ("OK — nothing missed" if result.ok
                                   else "INCOMPLETE — see above"))
        return "\n".join(lines)

    def render_alignment(self, drifts: List[AlignmentDrift],
                         guidance: Optional[List[str]] = None) -> str:
        lines = ["AicodeX Edition 2 — Commit-Parameter Alignment", "=" * 60]
        for drift in drifts:
            state = "aligned" if drift.aligned else "DRIFT  "
            params = self._params[drift.register]
            lines.append(f"  [{state}] {drift.register} {drift.role:<20} "
                         f"lod={params['lod']:<10} "
                         f"budget={_token_budget(params):>7.0f} tok  "
                         f"ceil={float(params['max_bytes']):>7.0f} B")
            for key, (committed, observed) in sorted(drift.drift.items()):
                lines.append(f"           {key:<12} committed={committed:.1f} "
                             f"observed={observed:.1f}")
            if drift.size_blowout:
                lines.append("           ** application size blowout **")
        if guidance:
            lines.append("-" * 60)
            lines.append("fine-tune guidance (where/when):")
            lines.extend(f"  - {g}" for g in guidance)
        aligned = sum(1 for d in drifts if d.aligned)
        lines.append("-" * 60)
        lines.append(f"aligned: {aligned}/{len(drifts)} registers")
        return "\n".join(lines)

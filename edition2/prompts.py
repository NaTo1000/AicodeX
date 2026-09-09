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


@dataclass(frozen=True)
class PromptCommitment:
    """A prompt committed under one register's digest algorithm."""

    register: str
    role: str
    prompt: str
    algorithm: str
    digest: str


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
        # definitions: {register: {"role": ..., "prompt": ...}}; a definition
        # may override "algorithm" but the default keeps the six distinct.
        self._defs: Dict[str, Tuple[str, str, str]] = {}
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
        self.max_workers = max(1, int(max_workers))
        self._committed: Dict[str, PromptCommitment] = {}
        # Post-registration mutations applied by tests/simulation:
        #   _dropped  — registers whose prompt was lost before decipherment
        #   _tampered — registers whose prompt was altered after commitment
        self._dropped: set = set()
        self._tampered: Dict[str, str] = {}

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _digest(algorithm: str, prompt: str) -> str:
        h = hashlib.new(algorithm)
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()

    # -- registration ------------------------------------------------------

    def register(self) -> List[PromptCommitment]:
        """Commit every register's prompt under its own distinct algorithm."""
        self._committed = {}
        for name in REGISTER_NAMES:
            role, prompt, algorithm = self._defs[name]
            self._committed[name] = PromptCommitment(
                register=name, role=role, prompt=prompt,
                algorithm=algorithm,
                digest=self._digest(algorithm, prompt))
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
        if self._digest(commitment.algorithm, prompt) != commitment.digest:
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

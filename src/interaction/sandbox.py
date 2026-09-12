"""Sandboxed runtime snippet preview.

:class:`SnippetSandbox` executes a small Python snippet in a restricted scope
with a wall-clock timeout, capturing stdout/stderr and a ``result`` binding, and
returns a structured :class:`ExecutionResult` for UI preview.

This is a *preview* sandbox, not a hardened security boundary: it blocks a set
of obviously dangerous builtins/imports and bounds output/timeout, but it is
intended for trusted, local snippet preview rather than running untrusted code
from the network.
"""

from __future__ import annotations

import builtins
import contextlib
import io
import signal
from typing import Dict, Optional

# Builtins we remove from the sandboxed namespace for safer preview.
_BLOCKED_BUILTINS = (
    "open", "exec", "eval", "compile", "__import__", "input", "globals",
    "locals", "vars", "exit", "quit", "breakpoint", "help", "memoryview",
)

# Module names that must not be imported in a preview snippet.
_BLOCKED_IMPORTS = (
    "os", "sys", "subprocess", "socket", "shutil", "pathlib", "importlib",
    "ctypes", "signal", "threading", "multiprocessing", "pickle", "builtins",
)


class ExecutionResult:
    """The outcome of running a snippet in the sandbox."""

    def __init__(
        self,
        ok: bool,
        stdout: str = "",
        stderr: str = "",
        result: object = None,
        duration_s: float = 0.0,
        timed_out: bool = False,
        error: str = "",
        truncated: bool = False,
    ) -> None:
        self.ok = bool(ok)
        self.stdout = stdout
        self.stderr = stderr
        self.result = result
        self.duration_s = float(duration_s)
        self.timed_out = bool(timed_out)
        self.error = error
        self.truncated = bool(truncated)

    def summary(self) -> str:
        if self.timed_out:
            return "Execution timed out."
        if not self.ok:
            return f"Error: {self.error or self.stderr.strip() or 'unknown error'}"
        parts = []
        if self.stdout.strip():
            parts.append(self.stdout.rstrip())
        if self.result is not None:
            parts.append(f"result = {self.result!r}")
        return "\n".join(parts) if parts else "(no output)"

    def as_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "result": repr(self.result),
            "duration_s": self.duration_s,
            "timed_out": self.timed_out,
            "error": self.error,
            "truncated": self.truncated,
        }


class _Timeout(Exception):
    pass


class SnippetSandbox:
    """Executes Python snippets with a timeout and restricted namespace."""

    def __init__(self, enabled: bool = True, timeout_seconds: int = 5, max_output_chars: int = 4000) -> None:
        self.enabled = bool(enabled)
        self.timeout_seconds = max(1, int(timeout_seconds))
        self.max_output_chars = max(100, int(max_output_chars))

    @classmethod
    def from_config(cls, data) -> "SnippetSandbox":
        if isinstance(data, dict):
            return cls(
                enabled=data.get("enabled", True),
                timeout_seconds=data.get("timeout_seconds", 5),
                max_output_chars=data.get("max_output_chars", 4000),
            )
        return cls()

    def _build_namespace(self) -> Dict[str, object]:
        safe_builtins = {
            name: getattr(builtins, name)
            for name in dir(builtins)
            if not name.startswith("_") and name not in _BLOCKED_BUILTINS
        }

        def _guarded_import(name, *args, **kwargs):
            root = str(name).split(".")[0]
            if root in _BLOCKED_IMPORTS:
                raise ImportError(f"Import of '{root}' is not allowed in the sandbox")
            return __import__(name, *args, **kwargs)

        safe_builtins["__import__"] = _guarded_import
        return {"__builtins__": safe_builtins, "__name__": "__sandbox__"}

    def _truncate(self, text: str) -> (str, bool):
        if len(text) > self.max_output_chars:
            return text[: self.max_output_chars], True
        return text, False

    def run(self, code: str) -> ExecutionResult:
        if not self.enabled:
            return ExecutionResult(ok=False, error="Sandbox is disabled.")
        if not isinstance(code, str) or not code.strip():
            return ExecutionResult(ok=False, error="Empty snippet.")

        namespace = self._build_namespace()
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        timed_out = False
        error = ""

        def _handler(signum, frame):  # pragma: no cover - timing dependent
            raise _Timeout()

        use_signal = hasattr(signal, "SIGALRM")
        old_handler = None
        if use_signal:
            old_handler = signal.signal(signal.SIGALRM, _handler)
            signal.setitimer(signal.ITIMER_REAL, self.timeout_seconds)

        import time

        start = time.perf_counter()
        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                compiled = compile(code, "<sandbox>", "exec")
                # noqa: S102 - intentional sandboxed exec for snippet preview.
                exec(compiled, namespace)  # noqa: S102
        except _Timeout:
            timed_out = True
        except Exception as exc:  # noqa: BLE001 - surface any snippet error
            error = f"{type(exc).__name__}: {exc}"
        finally:
            if use_signal:
                signal.setitimer(signal.ITIMER_REAL, 0)
                if old_handler is not None:
                    signal.signal(signal.SIGALRM, old_handler)
        duration = time.perf_counter() - start

        stdout, t1 = self._truncate(stdout_buf.getvalue())
        stderr, t2 = self._truncate(stderr_buf.getvalue())
        result = namespace.get("result")

        if timed_out:
            return ExecutionResult(
                ok=False, stdout=stdout, stderr=stderr, duration_s=duration,
                timed_out=True, truncated=t1 or t2,
            )
        if error:
            return ExecutionResult(
                ok=False, stdout=stdout, stderr=stderr, duration_s=duration,
                error=error, truncated=t1 or t2,
            )
        return ExecutionResult(
            ok=True, stdout=stdout, stderr=stderr, result=result,
            duration_s=duration, truncated=t1 or t2,
        )

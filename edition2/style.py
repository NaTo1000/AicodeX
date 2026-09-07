"""User code-writing-style database for AicodeX Edition 2.

A small *style section* that learns a user's code-writing **fingerprint** from
samples, then **rewrites** code to match that style with precision. It supports
**regular rereads and alignment**: re-learning the fingerprint from a corpus and
reporting/applying drift so generated code stays aligned with the user's style.

Standard library only; deterministic. The fingerprint captures the most common,
safely-detectable conventions:

- indent width and whether tabs are used,
- preferred quote character for strings,
- brace placement style,
- max line length,
- trailing newline preference.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional


@dataclass(frozen=True)
class StyleFingerprint:
    """A measurable summary of a code-writing style."""

    indent_width: int = 4
    use_tabs: bool = False
    quote: str = '"'           # '"' or "'"
    brace_style: str = "same_line"  # same_line | new_line
    max_line_length: int = 100
    trailing_newline: bool = True

    def as_dict(self) -> Dict[str, object]:
        return {
            "indent_width": self.indent_width,
            "use_tabs": self.use_tabs,
            "quote": self.quote,
            "brace_style": self.brace_style,
            "max_line_length": self.max_line_length,
            "trailing_newline": self.trailing_newline,
        }


def _detect_indent(lines: List[str]) -> tuple:
    """Return (indent_width, use_tabs) inferred from indented lines."""
    widths: List[int] = []
    tabs = 0
    for line in lines:
        if not line.strip():
            continue
        leading = line[:len(line) - len(line.lstrip(" \t"))]
        if leading.startswith("\t"):
            tabs += 1
        elif leading:
            widths.append(len(leading))
    if tabs > len(widths):
        return (4, True)
    if not widths:
        return (4, False)
    # Most common small indent width (2, 4, ...).
    width = min((w for w in widths if w > 0), default=4)
    return (width, False)


def _detect_quote(code: str) -> str:
    doubles = code.count('"')
    singles = code.count("'")
    return "'" if singles > doubles else '"'


def _detect_brace_style(lines: List[str]) -> str:
    """Detect same-line vs new-line brace placement (C-style languages)."""
    new_line = sum(1 for line in lines if line.strip() == "{")
    same_line = sum(1 for line in lines
                    if line.rstrip().endswith("{") and line.strip() != "{")
    return "new_line" if new_line > same_line else "same_line"


class StyleDatabase:
    """Learns, stores, and applies a user's code-writing style."""

    def __init__(self, fingerprint: Optional[StyleFingerprint] = None) -> None:
        self.fingerprint = fingerprint or StyleFingerprint()
        self.rereads: int = 0

    # -- learning -----------------------------------------------------------

    def learn(self, code_samples: List[str]) -> StyleFingerprint:
        """Infer a fingerprint from one or more code samples.

        This is the *reread* path: call it regularly with the user's corpus to
        keep the stored fingerprint aligned with their current style.
        """
        lines: List[str] = []
        combined = ""
        for sample in code_samples:
            combined += sample + "\n"
            lines.extend(sample.splitlines())

        indent_width, use_tabs = _detect_indent(lines)
        quote = _detect_quote(combined)
        brace_style = _detect_brace_style(lines)
        max_len = max((len(line) for line in lines), default=100)
        # Detect the trailing-newline preference from the samples as given
        # (don't rely on the separator we add between them).
        trailing = bool(code_samples) and code_samples[-1].endswith("\n")

        self.fingerprint = StyleFingerprint(
            indent_width=indent_width,
            use_tabs=use_tabs,
            quote=quote,
            brace_style=brace_style,
            max_line_length=max(40, min(max_len, 200)),
            trailing_newline=trailing,
        )
        self.rereads += 1
        return self.fingerprint

    # -- alignment ------------------------------------------------------------

    def alignment_drift(self, code_samples: List[str]) -> Dict[str, object]:
        """Compare a fresh fingerprint against the stored one.

        Returns a mapping of the attributes that have drifted, with
        ``{"attribute": (stored, observed)}`` pairs. Empty means aligned.
        """
        probe = StyleDatabase(fingerprint=self.fingerprint)
        observed = probe.learn(code_samples)
        drift: Dict[str, object] = {}
        for key, stored in self.fingerprint.as_dict().items():
            seen = observed.as_dict()[key]
            if seen != stored:
                drift[key] = (stored, seen)
        return drift

    def align(self, code_samples: List[str]) -> StyleFingerprint:
        """Reread the corpus and align the stored fingerprint to it."""
        return self.learn(code_samples)

    # -- rewriting --------------------------------------------------------------

    def restyle(self, code: str,
                fingerprint: Optional[StyleFingerprint] = None) -> str:
        """Rewrite ``code`` to match the stored (or given) fingerprint.

        Applies the safely-mechanical parts of the style: indentation, quote
        character for simple string literals, and the trailing newline.
        """
        fp = fingerprint or self.fingerprint
        out_lines = []
        for line in code.splitlines():
            out_lines.append(self._restyle_line(line, fp))
        result = "\n".join(out_lines)
        if fp.trailing_newline:
            result += "\n"
        return result

    @staticmethod
    def _restyle_line(line: str, fp: StyleFingerprint) -> str:
        if not line.strip():
            return line
        # Normalise indentation.
        stripped = line.lstrip(" \t")
        original_indent = line[:len(line) - len(line.lstrip(" \t"))]
        # Estimate depth from the original indent (tabs count as indent_width).
        if original_indent.startswith("\t"):
            depth = original_indent.count("\t")
        else:
            depth = len(original_indent) // max(1, fp.indent_width)
        unit = "\t" if fp.use_tabs else " " * fp.indent_width
        new_line = unit * depth + stripped
        # Normalise simple double-quoted string literals to the preferred quote.
        if fp.quote == "'":
            new_line = StyleDatabase._swap_double_quotes(new_line)
        return new_line

    @staticmethod
    def _swap_double_quotes(line: str) -> str:
        """Swap unescaped double quotes to single quotes (best-effort)."""
        out = []
        in_string = False
        for ch in line:
            if ch == '"' and not in_string:
                out.append("'")
                in_string = True
            elif ch == '"' and in_string:
                out.append("'")
                in_string = False
            else:
                out.append(ch)
        return "".join(out)
